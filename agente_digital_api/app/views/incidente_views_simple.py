# Versión simplificada del endpoint para generar documento ANCI
from flask import Blueprint, jsonify, request, send_file
from datetime import datetime
import io
import json
from app.database import get_db_connection

incidente_simple_bp = Blueprint('incidente_simple', __name__, url_prefix='/api/incidente-simple')

@incidente_simple_bp.route('/<int:incidente_id>/generar-documento-anci', methods=['POST', 'OPTIONS'])
def generar_documento_anci_simple(incidente_id):
    """
    Genera un documento ANCI simple para un incidente
    """
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    try:
        # Obtener parámetros
        data = request.get_json() or {}
        tipo_reporte = data.get('tipo_reporte', 'preliminar')
        
        # Conexión a base de datos
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
        
        cursor = conn.cursor()
        
        # Consulta simple del incidente
        query = """
            SELECT 
                i.IncidenteID,
                i.Titulo,
                i.DescripcionInicial,
                i.FechaCreacion,
                i.Criticidad,
                i.EstadoActual,
                e.RazonSocial as NombreEmpresa,
                e.RUT as RutEmpresa,
                e.TipoEmpresa
            FROM Incidentes i
            LEFT JOIN Empresa e ON i.EmpresaID = e.EmpresaID
            WHERE i.IncidenteID = ?
        """
        
        cursor.execute(query, incidente_id)
        row = cursor.fetchone()
        
        if not row:
            return jsonify({"error": f"Incidente {incidente_id} no encontrado"}), 404
        
        # Convertir a diccionario
        columns = [column[0] for column in cursor.description]
        incidente = dict(zip(columns, row))
        
        # Crear estructura básica ANCI
        reporte_anci = {
            "version": "1.0",
            "tipo_reporte": tipo_reporte,
            "fecha_generacion": datetime.now().isoformat(),
            "referencia": {
                "numero_incidente": f"INC-{incidente_id:06d}",
                "fecha_incidente": incidente['FechaCreacion'].isoformat() if incidente['FechaCreacion'] else None,
                "tipo_empresa": incidente.get('TipoEmpresa', 'PSE')
            },
            "empresa": {
                "nombre": incidente.get('NombreEmpresa', 'No especificado'),
                "rut": incidente.get('RutEmpresa', 'No especificado')
            },
            "incidente": {
                "titulo": incidente['Titulo'],
                "descripcion": incidente['DescripcionInicial'],
                "criticidad": incidente['Criticidad'],
                "estado": incidente['EstadoActual']
            },
            "detalle_tecnico": {
                "tipo_incidente": "Ciberseguridad",
                "vector_ataque": "Por determinar",
                "sistemas_afectados": "En evaluación",
                "impacto_estimado": "Medio"
            }
        }
        
        # Si es preliminar, agregar info específica
        if tipo_reporte == 'preliminar':
            reporte_anci['alerta_temprana'] = {
                "detectado_por": "Sistema de monitoreo",
                "hora_deteccion": datetime.now().isoformat(),
                "acciones_inmediatas": "Aislamiento de sistemas afectados",
                "requiere_apoyo_csirt": "No"
            }
        
        cursor.close()
        conn.close()
        
        # Generar archivo JSON
        output = io.StringIO()
        json.dump(reporte_anci, output, indent=2, ensure_ascii=False)
        output.seek(0)
        
        # Convertir a BytesIO para envío
        byte_output = io.BytesIO()
        byte_output.write(output.getvalue().encode('utf-8'))
        byte_output.seek(0)
        
        filename = f"ANCI_{tipo_reporte}_{incidente_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return send_file(
            byte_output,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Error generando documento ANCI simple: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500
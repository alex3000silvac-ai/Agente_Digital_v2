# Endpoint de prueba ultra simple
from flask import Blueprint, jsonify, request, send_file
from datetime import datetime
import io
import json

incidente_test_bp = Blueprint('incidente_test', __name__, url_prefix='/api/incidente-test')

@incidente_test_bp.route('/<int:incidente_id>/generar-documento-anci', methods=['POST', 'OPTIONS'])
def generar_documento_test(incidente_id):
    """
    Genera un documento ANCI de prueba sin base de datos
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
        
        # Datos de prueba
        reporte_anci = {
            "version": "1.0",
            "tipo_reporte": tipo_reporte,
            "fecha_generacion": datetime.now().isoformat(),
            "referencia": {
                "numero_incidente": f"INC-{incidente_id:06d}",
                "fecha_incidente": datetime.now().isoformat(),
                "tipo_empresa": "PSE"
            },
            "empresa": {
                "nombre": "Empresa de Prueba S.A.",
                "rut": "12.345.678-9"
            },
            "incidente": {
                "titulo": f"Incidente de prueba #{incidente_id}",
                "descripcion": "Descripción del incidente de prueba",
                "criticidad": "Alta",
                "estado": "Activo"
            },
            "detalle_tecnico": {
                "tipo_incidente": "Ciberseguridad",
                "vector_ataque": "Phishing",
                "sistemas_afectados": "Sistema de correo electrónico",
                "impacto_estimado": "Medio"
            },
            "alerta_temprana": {
                "detectado_por": "Sistema de monitoreo",
                "hora_deteccion": datetime.now().isoformat(),
                "acciones_inmediatas": "Aislamiento de sistemas afectados",
                "requiere_apoyo_csirt": "No"
            }
        }
        
        # Generar archivo JSON
        json_str = json.dumps(reporte_anci, indent=2, ensure_ascii=False)
        
        # Convertir a BytesIO para envío
        byte_output = io.BytesIO()
        byte_output.write(json_str.encode('utf-8'))
        byte_output.seek(0)
        
        filename = f"ANCI_{tipo_reporte}_{incidente_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Agregar headers CORS
        response = send_file(
            byte_output,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        print(f"Error en endpoint de prueba: {e}")
        response = jsonify({"error": "Error interno", "details": str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
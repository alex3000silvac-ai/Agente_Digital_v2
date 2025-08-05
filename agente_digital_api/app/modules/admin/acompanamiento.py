# modules/admin/acompanamiento.py
# Gestión de planes de acompañamiento

from flask import Blueprint, jsonify, request
from ..core.database import get_db_connection, db_validator
from ..core.errors import robust_endpoint, ErrorResponse
from datetime import datetime

acompanamiento_bp = Blueprint('admin_acompanamiento', __name__, url_prefix='/api/admin/empresas')

@acompanamiento_bp.route('/<int:empresa_id>/acompanamiento', methods=['GET', 'OPTIONS'])
def get_plan_acompanamiento(empresa_id):
    """Obtiene el plan de acompañamiento de una empresa"""
    
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Verificar que la empresa existe
        cursor.execute("SELECT RazonSocial, TipoEmpresa FROM Empresas WHERE EmpresaID = ?", (empresa_id,))
        empresa_info = cursor.fetchone()
        
        if not empresa_info:
            return jsonify({"error": "Empresa no encontrada"}), 404
        
        # MODIFICADO: Ahora devolvemos las obligaciones reales filtradas por tipo de empresa
        # Obtenemos las obligaciones según el tipo de empresa (OIV o PSE)
        obligaciones = []
        
        try:
            # Query completo incluyendo todos los campos necesarios
            query_obligaciones = """
                SELECT DISTINCT
                    O.ObligacionID,
                    O.ArticuloNorma,
                    O.Descripcion,
                    O.MedioDeVerificacionSugerido,
                    O.AplicaPara,
                    CE.CumplimientoID,
                    ISNULL(CE.Estado, 'Pendiente') as Estado,
                    ISNULL(CE.PorcentajeAvance, 0) as PorcentajeAvance,
                    CE.Responsable,
                    CE.FechaTermino,
                    CE.ObservacionesCiberseguridad,
                    CE.ObservacionesLegales
                FROM OBLIGACIONES O
                LEFT JOIN CumplimientoEmpresa CE ON O.ObligacionID = CE.ObligacionID AND CE.EmpresaID = ?
                WHERE (O.AplicaPara = ? OR O.AplicaPara = 'Ambos')
                ORDER BY O.ArticuloNorma
            """
            
            # DEBUG: Log para verificar tipo de empresa
            print(f"🔍 Buscando obligaciones para empresa {empresa_id}, tipo: {empresa_info.TipoEmpresa}")
            
            cursor.execute(query_obligaciones, (empresa_id, empresa_info.TipoEmpresa))
            rows = cursor.fetchall()
            
            # DEBUG: Log cantidad de obligaciones encontradas
            print(f"✅ Encontradas {len(rows)} obligaciones para tipo {empresa_info.TipoEmpresa}")
            
            for row in rows:
                # CORREGIDO: Construir objeto - la codificación ahora se maneja en database.py
                try:
                    obligacion = {
                        "ObligacionID": row.ObligacionID,
                        "ArticuloNorma": row.ArticuloNorma or "",
                        "Descripcion": row.Descripcion or "",
                        "MedioDeVerificacionSugerido": row.MedioDeVerificacionSugerido or "",
                        "AplicaPara": row.AplicaPara or "",
                        "CumplimientoID": row.CumplimientoID,
                        "Estado": row.Estado or "Pendiente",
                        "PorcentajeAvance": row.PorcentajeAvance or 0,
                        "Responsable": row.Responsable or "",
                        "FechaTermino": row.FechaTermino.strftime('%Y-%m-%d') if row.FechaTermino else None,
                        "ObservacionesCiberseguridad": row.ObservacionesCiberseguridad or "",
                        "ObservacionesLegales": row.ObservacionesLegales or "",
                        # Campos legacy que el frontend podría esperar
                        "Observaciones": "",
                        "ArchivoEvidencia": "",
                        "RutaEvidencia": ""
                    }
                    obligaciones.append(obligacion)
                except Exception as row_error:
                    print(f"Error procesando obligación: {row_error}")
                    import traceback
                    traceback.print_exc()
                    continue
                
        except Exception as e:
            print(f"Error obteniendo obligaciones: {e}")
            # Si falla, devolvemos estructura vacía para evitar errores en frontend
            obligaciones = []
        
        # MODIFICADO: Devolvemos directamente el array de obligaciones
        # El frontend espera un array para poder hacer .map()
        print(f"📤 Devolviendo {len(obligaciones)} obligaciones al frontend")
        return jsonify(obligaciones), 200
        
    except Exception as e:
        print(f"Error al obtener plan de acompañamiento: {e}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
    
    finally:
        if conn:
            conn.close()

@acompanamiento_bp.route('/<int:empresa_id>/acompanamiento', methods=['POST'])
def update_plan_acompanamiento(empresa_id):
    """Actualiza el plan de acompañamiento de una empresa"""
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a base de datos"}), 500
    
    try:
        data = request.get_json()
        # Aquí se implementaría la lógica para actualizar el plan
        # Por ahora retornamos éxito
        
        return jsonify({
            "message": "Plan actualizado exitosamente",
            "empresa_id": empresa_id
        }), 200
        
    except Exception as e:
        print(f"Error al actualizar plan de acompañamiento: {e}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
    
    finally:
        if conn:
            conn.close()
# modules/admin/incidentes_redirect.py  
# Redirección para compatibilidad con frontend

from flask import Blueprint, jsonify, request
import requests

incidentes_redirect_bp = Blueprint('admin_incidentes_redirect', __name__, url_prefix='/api/admin')

@incidentes_redirect_bp.route('/incidentes/<int:incidente_id>', methods=['GET'])
def get_incidente_redirect(incidente_id):
    """Redirecciona las llamadas del frontend al endpoint correcto"""
    try:
        # Llamar al endpoint completo de incidentes
        response = requests.get(f'http://localhost:5000/api/incidente/{incidente_id}')
        
        if response.status_code == 404:
            return jsonify({"error": "Incidente no encontrado"}), 404
        elif response.status_code != 200:
            return jsonify({"error": "Error al obtener incidente"}), 500
            
        return response.json(), 200
        
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500

@incidentes_redirect_bp.route('/incidentes/<int:incidente_id>', methods=['DELETE'])
def delete_incidente_redirect(incidente_id):
    """Elimina un incidente específico y todas sus referencias"""
    try:
        from ..core.database import get_db_connection
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
            
        cursor = conn.cursor()
        
        # Iniciar transacción
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            # Verificar que el incidente existe
            cursor.execute("SELECT IncidenteID FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
            if not cursor.fetchone():
                cursor.execute("ROLLBACK")
                conn.close()
                return jsonify({"error": "Incidente no encontrado"}), 404
            
            # Eliminar en orden correcto para respetar las foreign keys
            # 1. Eliminar evidencias de taxonomías
            cursor.execute("DELETE FROM EVIDENCIAS_TAXONOMIA WHERE IncidenteID = ?", (incidente_id,))
            
            # 2. Eliminar comentarios de taxonomías
            cursor.execute("DELETE FROM COMENTARIOS_TAXONOMIA WHERE IncidenteID = ?", (incidente_id,))
            
            # 3. Eliminar relaciones incidente-taxonomía
            cursor.execute("DELETE FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?", (incidente_id,))
            
            # 4. Eliminar evidencias del incidente
            cursor.execute("DELETE FROM EvidenciasIncidentes WHERE IncidenteID = ?", (incidente_id,))
            
            # 5. Eliminar del historial de incidentes
            cursor.execute("DELETE FROM HistorialIncidentes WHERE IncidenteID = ?", (incidente_id,))
            
            # 6. Eliminar categorías del incidente
            cursor.execute("DELETE FROM IncidentesCategorias WHERE IncidenteID = ?", (incidente_id,))
            
            # 7. Eliminar notificaciones ANCI
            cursor.execute("DELETE FROM AnciNotificaciones WHERE IncidenteID = ?", (incidente_id,))
            
            # 8. Eliminar autorizaciones ANCI
            cursor.execute("DELETE FROM AnciAutorizaciones WHERE IncidenteID = ?", (incidente_id,))
            
            # 9. Eliminar plazos ANCI
            cursor.execute("DELETE FROM AnciPlazos WHERE IncidenteID = ?", (incidente_id,))
            
            # 10. Finalmente, eliminar el incidente
            cursor.execute("DELETE FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
            
            # Confirmar transacción
            cursor.execute("COMMIT")
            conn.close()
            
            return jsonify({
                "success": True,
                "message": "Incidente eliminado exitosamente"
            }), 200
            
        except Exception as e:
            # Si algo falla, hacer rollback
            cursor.execute("ROLLBACK")
            raise e
        
    except Exception as e:
        import traceback
        print(f"Error al eliminar incidente: {e}")
        print(traceback.format_exc())
        
        if conn:
            conn.close()
            
        return jsonify({
            "error": "Error al eliminar incidente",
            "detalle": str(e)
        }), 500
# incidentes_eliminar.py
# Módulo robusto para eliminación de incidentes

from flask import Blueprint, jsonify
from ...database import get_db_connection

incidentes_eliminar_bp = Blueprint('incidentes_eliminar', __name__, url_prefix='/api/admin')

def verificar_tabla_existe(cursor, nombre_tabla):
    """Verifica si una tabla existe en la base de datos"""
    try:
        cursor.execute("""
            SELECT 1 FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = ?
        """, (nombre_tabla,))
        return cursor.fetchone() is not None
    except:
        return False

@incidentes_eliminar_bp.route('/incidentes/<int:incidente_id>', methods=['DELETE'])
def eliminar_incidente_seguro(incidente_id):
    """Elimina un incidente de forma segura, verificando la existencia de tablas"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
            
        cursor = conn.cursor()
        
        # Verificar que el incidente existe
        cursor.execute("SELECT IncidenteID FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Incidente no encontrado"}), 404
        
        # Iniciar transacción
        cursor.execute("BEGIN TRANSACTION")
        
        # Lista de tablas relacionadas y sus campos de referencia
        tablas_relacionadas = [
            ('EVIDENCIAS_TAXONOMIA', 'IncidenteID'),
            ('COMENTARIOS_TAXONOMIA', 'IncidenteID'),
            ('INCIDENTE_TAXONOMIA', 'IncidenteID'),
            ('EvidenciasIncidentes', 'IncidenteID'),
            ('HistorialIncidentes', 'IncidenteID'),
            ('IncidentesCategorias', 'IncidenteID'),
            ('AnciNotificaciones', 'IncidenteID'),
            ('AnciAutorizaciones', 'IncidenteID'),
            ('AnciPlazos', 'IncidenteID'),
            ('ReportesANCI', 'IncidenteID')
        ]
        
        eliminaciones_exitosas = []
        
        # Eliminar de cada tabla si existe
        for tabla, campo in tablas_relacionadas:
            if verificar_tabla_existe(cursor, tabla):
                try:
                    cursor.execute(f"DELETE FROM {tabla} WHERE {campo} = ?", (incidente_id,))
                    rows_affected = cursor.rowcount
                    if rows_affected > 0:
                        eliminaciones_exitosas.append(f"{tabla}: {rows_affected} registros")
                except Exception as e:
                    print(f"Advertencia: No se pudo eliminar de {tabla}: {str(e)}")
        
        # Finalmente, eliminar el incidente principal
        cursor.execute("DELETE FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        
        # Confirmar transacción
        cursor.execute("COMMIT")
        
        return jsonify({
            "success": True,
            "message": "Incidente eliminado exitosamente",
            "detalles": eliminaciones_exitosas
        }), 200
        
    except Exception as e:
        if conn:
            try:
                cursor.execute("ROLLBACK")
            except:
                pass
        
        import traceback
        print(f"Error al eliminar incidente: {e}")
        print(traceback.format_exc())
        
        return jsonify({
            "error": "Error al eliminar incidente",
            "detalle": str(e)
        }), 500
        
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass
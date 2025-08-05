# incidentes_delete_directo.py
# Endpoint directo para eliminación de incidentes que coincide con el frontend

from flask import Blueprint, jsonify
from ...database import get_db_connection

incidentes_delete_bp = Blueprint('admin_incidentes_delete', __name__, url_prefix='/api/admin')

@incidentes_delete_bp.route('/incidentes/<int:incidente_id>', methods=['DELETE', 'HEAD', 'OPTIONS'])
def delete_incidente_directo(incidente_id):
    """Elimina completamente un incidente - Endpoint directo para frontend"""
    print(f"🗑️ DELETE REQUEST RECIBIDO para incidente {incidente_id}")
    
    try:
        # Intentar usar el módulo de eliminación completa
        try:
            from .incidentes_eliminar_completo import eliminar_incidente_completo
            print(f"✅ Módulo de eliminación completa importado correctamente")
            return eliminar_incidente_completo(incidente_id)
        except ImportError as e:
            print(f"⚠️ No se pudo importar módulo completo: {e}")
            # Fallback a eliminación simple
            return eliminar_simple(incidente_id)
        
    except Exception as e:
        print(f"❌ Error en eliminación directa: {e}")
        return jsonify({
            "error": f"Error eliminando incidente: {str(e)}"
        }), 500

def eliminar_simple(incidente_id):
    """Eliminación simple como fallback"""
    print(f"🔄 Ejecutando eliminación simple para incidente {incidente_id}")
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ Error de conexión a BD")
            return jsonify({"error": "Error de conexión a BD"}), 500
            
        cursor = conn.cursor()
        
        # Verificar que el incidente existe
        cursor.execute("SELECT IncidenteID, Titulo FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        incidente = cursor.fetchone()
        if not incidente:
            print(f"❌ Incidente {incidente_id} no encontrado")
            return jsonify({"error": "Incidente no encontrado"}), 404
        
        print(f"✅ Incidente encontrado: {incidente[1]}")
        
        # Eliminar evidencias primero
        cursor.execute("DELETE FROM EvidenciasIncidentes WHERE IncidenteID = ?", (incidente_id,))
        evidencias_eliminadas = cursor.rowcount
        print(f"🗂️ Eliminadas {evidencias_eliminadas} evidencias")
        
        # Eliminar el incidente principal
        cursor.execute("DELETE FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        incidentes_eliminados = cursor.rowcount
        print(f"📋 Eliminados {incidentes_eliminados} incidentes")
        
        conn.commit()
        
        print(f"✅ Incidente {incidente_id} eliminado exitosamente")
        
        return jsonify({
            "success": True,
            "message": f"Incidente {incidente_id} eliminado correctamente",
            "incidente_id": incidente_id,
            "detalles": {
                "evidencias_eliminadas": evidencias_eliminadas,
                "metodo": "eliminacion_simple"
            }
        }), 200
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error en eliminación simple: {e}")
        return jsonify({
            "error": f"Error eliminando incidente: {str(e)}"
        }), 500
        
    finally:
        if conn:
            conn.close()

# Endpoint de test para verificar que está registrado
@incidentes_delete_bp.route('/test-delete', methods=['GET'])
def test_delete_endpoint():
    """Endpoint de test para verificar que el blueprint está registrado"""
    return jsonify({
        "message": "Endpoint DELETE está registrado y funcionando",
        "blueprint": "admin_incidentes_delete",
        "ruta": "/api/admin/incidentes/<id>",
        "metodos": ["DELETE", "HEAD", "OPTIONS"]
    }), 200
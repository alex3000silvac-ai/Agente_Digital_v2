from flask import Blueprint, jsonify
from ..database import get_db_connection

test_cumplimiento_bp = Blueprint('test_cumplimiento', __name__, url_prefix='/api/test')

@test_cumplimiento_bp.route('/empresa/<int:empresa_id>/obligaciones', methods=['GET'])
def test_obligaciones(empresa_id):
    """Endpoint de prueba para verificar obligaciones"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "No DB connection"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Query simple sin encoding especial
        cursor.execute("""
            SELECT TOP 5
                ObligacionID,
                ArticuloNorma,
                Descripcion
            FROM OBLIGACIONES
            WHERE AplicaPara = 'PSE' OR AplicaPara = 'Ambos'
        """)
        
        rows = cursor.fetchall()
        obligaciones = []
        
        for row in rows:
            obligaciones.append({
                'ObligacionID': str(row[0]) if row[0] else '',
                'ArticuloNorma': str(row[1]) if row[1] else '',
                'Descripcion': str(row[2]) if row[2] else ''
            })
        
        return jsonify({
            'empresa_id': empresa_id,
            'total': len(obligaciones),
            'obligaciones': obligaciones
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()
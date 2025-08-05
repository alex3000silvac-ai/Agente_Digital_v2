# inquilinos_simple.py
# Módulo simplificado de inquilinos sin autenticación para pruebas

from flask import Blueprint, jsonify, request
from ...database import get_db_connection

inquilinos_simple_bp = Blueprint('inquilinos_simple', __name__, url_prefix='/api/admin')

@inquilinos_simple_bp.route('/inquilinos', methods=['GET', 'OPTIONS'])
def get_inquilinos():
    """Obtiene la lista de inquilinos sin autenticación"""
    
    # Si es OPTIONS, retornar respuesta vacía con headers CORS
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a base de datos'}), 500
        
        cursor = conn.cursor()
        
        # Consulta simple
        cursor.execute("""
            SELECT InquilinoID, RazonSocial, RUT, EstadoActivo 
            FROM Inquilinos 
            ORDER BY RazonSocial
        """)
        
        rows = cursor.fetchall()
        
        inquilinos = []
        for row in rows:
            inquilinos.append({
                'InquilinoID': row[0],
                'RazonSocial': row[1],
                'RUT': row[2] if row[2] else '',
                'EstadoActivo': 'Activo' if row[3] else 'Inactivo'
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'inquilinos': inquilinos
        }), 200
        
    except Exception as e:
        print(f"Error obteniendo inquilinos: {str(e)}")
        return jsonify({
            'error': 'Error al obtener inquilinos',
            'detalle': str(e)
        }), 500
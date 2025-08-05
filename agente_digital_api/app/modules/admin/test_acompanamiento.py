# Test endpoint para verificar acompañamiento
from flask import Blueprint, jsonify
from ..core.database import get_db_connection

test_acompanamiento_bp = Blueprint('test_acompanamiento', __name__, url_prefix='/api/test')

@test_acompanamiento_bp.route('/verificar-obligaciones/<int:empresa_id>', methods=['GET'])
def verificar_obligaciones(empresa_id):
    """Endpoint de prueba para verificar que las obligaciones se cargan correctamente"""
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        
        # 1. Verificar empresa y su tipo
        cursor.execute("SELECT RazonSocial, TipoEmpresa FROM Empresas WHERE EmpresaID = ?", (empresa_id,))
        empresa_info = cursor.fetchone()
        
        if not empresa_info:
            return jsonify({"error": "Empresa no encontrada"}), 404
        
        # 2. Contar obligaciones para este tipo
        cursor.execute("""
            SELECT COUNT(*) 
            FROM OBLIGACIONES 
            WHERE AplicaPara = ? OR AplicaPara = 'Ambos'
        """, (empresa_info.TipoEmpresa,))
        count = cursor.fetchone()[0]
        
        # 3. Obtener primeras 3 obligaciones como muestra
        cursor.execute("""
            SELECT TOP 3 ObligacionID, ArticuloNorma, Descripcion, AplicaPara
            FROM OBLIGACIONES 
            WHERE AplicaPara = ? OR AplicaPara = 'Ambos'
            ORDER BY ArticuloNorma
        """, (empresa_info.TipoEmpresa,))
        
        obligaciones = []
        for row in cursor.fetchall():
            obligaciones.append({
                "ObligacionID": row.ObligacionID,
                "ArticuloNorma": row.ArticuloNorma,
                "Descripcion": row.Descripcion,
                "AplicaPara": row.AplicaPara
            })
        
        # 4. Verificar columnas en CumplimientoEmpresa
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'CumplimientoEmpresa'
            ORDER BY ORDINAL_POSITION
        """)
        columns = [row[0] for row in cursor.fetchall()]
        
        return jsonify({
            "empresa": {
                "id": empresa_id,
                "razon_social": empresa_info.RazonSocial,
                "tipo": empresa_info.TipoEmpresa
            },
            "total_obligaciones": count,
            "muestra_obligaciones": obligaciones,
            "columnas_cumplimiento": columns,
            "version": "2025-07-10-fix",
            "observaciones": "Esta es la versión corregida que NO usa columnas inexistentes"
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500
    
    finally:
        if conn:
            conn.close()
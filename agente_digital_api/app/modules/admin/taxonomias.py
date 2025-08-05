# modules/admin/taxonomias.py
# Gestión de taxonomías para incidentes

from flask import Blueprint, jsonify, request
from ..core.database import get_db_connection, db_validator
from ..core.errors import robust_endpoint, ErrorResponse

taxonomias_bp = Blueprint('admin_taxonomias', __name__, url_prefix='/api/admin/taxonomias')

@taxonomias_bp.route('/jerarquica', methods=['GET', 'OPTIONS'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_taxonomias_jerarquicas():
    """Obtiene las taxonomías de forma jerárquica para el tipo de empresa"""
    
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    tipo_empresa = request.args.get('tipo_empresa', 'PSE')
    
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error()
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        # Verificar que las tablas existan (con nombres correctos)
        tables_needed = ['TAXONOMIA_INCIDENTES', 'SubcategoriaTaxonomia', 'DetalleSubcategoria']
        for table in tables_needed:
            if not db_validator.table_exists(cursor, table):
                print(f"Tabla {table} no existe")
                # Retornar estructura vacía si no existen las tablas
                return jsonify({
                    'status': 'success',
                    'tipo_empresa': tipo_empresa,
                    'categorias': []
                })
        
        # Obtener todas las categorías principales
        query_categorias = """
            SELECT DISTINCT 
                Categoria_del_Incidente as Categoria,
                999 as OrdenCategoria
            FROM TAXONOMIA_INCIDENTES
            WHERE AplicaTipoEmpresa = ? OR AplicaTipoEmpresa = 'AMBAS'
            ORDER BY Categoria_del_Incidente
        """
        cursor.execute(query_categorias, (tipo_empresa,))
        categorias_rows = cursor.fetchall()
        
        resultado = {
            'status': 'success',
            'tipo_empresa': tipo_empresa,
            'categorias': []
        }
        
        for cat_row in categorias_rows:
            categoria = cat_row.Categoria
            
            # Obtener subcategorías para esta categoría
            query_subcategorias = """
                SELECT DISTINCT 
                    S.SubcategoriaID,
                    S.NombreSubcategoria,
                    S.DescripcionSubcategoria,
                    ISNULL(S.OrdenSubcategoria, 999) as OrdenSubcategoria
                FROM SubcategoriaTaxonomia S
                INNER JOIN TaxonomiaIncidentes T ON S.TaxonomiaID = T.TaxonomiaID
                WHERE T.Categoria = ?
                ORDER BY OrdenSubcategoria, S.NombreSubcategoria
            """
            cursor.execute(query_subcategorias, (categoria,))
            subcategorias_rows = cursor.fetchall()
            
            subcategorias_list = []
            for sub_row in subcategorias_rows:
                # Obtener detalles para esta subcategoría
                query_detalles = """
                    SELECT 
                        DetalleID,
                        NombreDetalle,
                        DescripcionDetalle,
                        ISNULL(OrdenDetalle, 999) as OrdenDetalle
                    FROM DetalleSubcategoria
                    WHERE SubcategoriaID = ?
                    ORDER BY OrdenDetalle, NombreDetalle
                """
                cursor.execute(query_detalles, (sub_row.SubcategoriaID,))
                detalles_rows = cursor.fetchall()
                
                detalles_list = []
                for det_row in detalles_rows:
                    detalles_list.append({
                        'id': det_row.DetalleID,
                        'nombre': det_row.NombreDetalle,
                        'descripcion': det_row.DescripcionDetalle or ''
                    })
                
                subcategorias_list.append({
                    'id': sub_row.SubcategoriaID,
                    'nombre': sub_row.NombreSubcategoria,
                    'descripcion': sub_row.DescripcionSubcategoria or '',
                    'detalles': detalles_list
                })
            
            resultado['categorias'].append({
                'nombre': categoria,
                'subcategorias': subcategorias_list
            })
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"Error al obtener taxonomías jerárquicas: {e}")
        # En caso de error, retornar estructura de contingencia
        return jsonify({
            'status': 'error',
            'tipo_empresa': tipo_empresa,
            'categorias': [
                {
                    'nombre': 'Acceso no autorizado',
                    'subcategorias': [
                        {
                            'id': 1,
                            'nombre': 'Intento de acceso sin autenticación',
                            'descripcion': 'Acceso sin credenciales válidas',
                            'detalles': []
                        }
                    ]
                },
                {
                    'nombre': 'Malware',
                    'subcategorias': [
                        {
                            'id': 2,
                            'nombre': 'Virus',
                            'descripcion': 'Software malicioso tipo virus',
                            'detalles': []
                        }
                    ]
                }
            ],
            'error': str(e)
        })
    
    finally:
        if conn:
            conn.close()

@taxonomias_bp.route('', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def list_taxonomias():
    """Lista todas las taxonomías disponibles"""
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error()
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        if not db_validator.table_exists(cursor, 'TaxonomiaIncidentes'):
            return jsonify([])
        
        cursor.execute("""
            SELECT TaxonomiaID, Categoria, Subcategoria 
            FROM TaxonomiaIncidentes 
            ORDER BY Categoria, Subcategoria
        """)
        rows = cursor.fetchall()
        
        taxonomias = []
        for row in rows:
            taxonomias.append({
                'TaxonomiaID': row.TaxonomiaID,
                'Categoria': row.Categoria,
                'Subcategoria': row.Subcategoria
            })
        
        return jsonify(taxonomias)
        
    finally:
        if conn:
            conn.close()
# modules/admin/taxonomias_simple.py
# Gestión simplificada de taxonomías basada en la estructura real de BD

from flask import Blueprint, jsonify, request
from ..core.database import get_db_connection
from ..core.errors import robust_endpoint, ErrorResponse

taxonomias_simple_bp = Blueprint('admin_taxonomias_simple', __name__, url_prefix='/api/admin/taxonomias')

@taxonomias_simple_bp.route('/simple', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_taxonomias_simple():
    """Obtiene las taxonomías de forma simple desde TAXONOMIA_INCIDENTES"""
    
    tipo_empresa = request.args.get('tipo_empresa', 'PSE')
    
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error()
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        # Consulta simple a la tabla real
        query = """
            SELECT DISTINCT
                Id_Incidente,
                Area,
                Efecto,
                Categoria_del_Incidente,
                Subcategoria_del_Incidente,
                AplicaTipoEmpresa
            FROM TAXONOMIA_INCIDENTES
            WHERE (AplicaTipoEmpresa = ? OR AplicaTipoEmpresa = 'AMBAS' OR AplicaTipoEmpresa IS NULL)
            ORDER BY Area, Efecto, Categoria_del_Incidente
        """
        
        cursor.execute(query, (tipo_empresa,))
        rows = cursor.fetchall()
        
        # Organizar por área
        taxonomias_por_area = {}
        
        for row in rows:
            area = row.Area or 'Sin clasificar'
            
            if area not in taxonomias_por_area:
                taxonomias_por_area[area] = {
                    'area': area,
                    'efectos': {}
                }
            
            efecto = row.Efecto or 'Sin efecto'
            
            if efecto not in taxonomias_por_area[area]['efectos']:
                taxonomias_por_area[area]['efectos'][efecto] = {
                    'efecto': efecto,
                    'categorias': []
                }
            
            # Agregar categoría
            categoria_existe = False
            for cat in taxonomias_por_area[area]['efectos'][efecto]['categorias']:
                if cat['categoria'] == row.Categoria_del_Incidente:
                    # Agregar subcategoría si no existe
                    if row.Subcategoria_del_Incidente and row.Subcategoria_del_Incidente not in [s['subcategoria'] for s in cat['subcategorias']]:
                        cat['subcategorias'].append({
                            'id': row.Id_Incidente,
                            'subcategoria': row.Subcategoria_del_Incidente
                        })
                    categoria_existe = True
                    break
            
            if not categoria_existe:
                nueva_categoria = {
                    'categoria': row.Categoria_del_Incidente,
                    'subcategorias': []
                }
                
                if row.Subcategoria_del_Incidente:
                    nueva_categoria['subcategorias'].append({
                        'id': row.Id_Incidente,
                        'subcategoria': row.Subcategoria_del_Incidente
                    })
                
                taxonomias_por_area[area]['efectos'][efecto]['categorias'].append(nueva_categoria)
        
        # Convertir a lista
        resultado = []
        for area_data in taxonomias_por_area.values():
            efectos_lista = []
            for efecto_data in area_data['efectos'].values():
                efectos_lista.append({
                    'efecto': efecto_data['efecto'],
                    'categorias': efecto_data['categorias']
                })
            
            resultado.append({
                'area': area_data['area'],
                'efectos': efectos_lista
            })
        
        return jsonify({
            'status': 'success',
            'tipo_empresa': tipo_empresa,
            'total': len(rows),
            'taxonomias': resultado
        })
        
    except Exception as e:
        print(f"Error obteniendo taxonomías: {e}")
        response, status = ErrorResponse.generic_error(f"Error obteniendo taxonomías: {str(e)}")
        return jsonify(response), status
    
    finally:
        if conn:
            conn.close()

@taxonomias_simple_bp.route('/flat', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_taxonomias_flat():
    """Obtiene las taxonomías en formato plano (lista simple)"""
    
    tipo_empresa = request.args.get('tipo_empresa', 'PSE')
    
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error()
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        # Verificar si hay NULLs en subcategorías
        test_query = """
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN Subcategoria_del_Incidente IS NULL THEN 1 ELSE 0 END) as nulls,
                   SUM(CASE WHEN Subcategoria_del_Incidente = '' THEN 1 ELSE 0 END) as vacios
            FROM TAXONOMIA_INCIDENTES
        """
        cursor.execute(test_query)
        stats = cursor.fetchone()
        print(f"\n🔍 ESTADÍSTICAS DE SUBCATEGORÍAS:")
        print(f"   - Total registros: {stats.total}")
        print(f"   - Subcategorías NULL: {stats.nulls}")
        print(f"   - Subcategorías vacías: {stats.vacios}")
        
        # Ver algunos ejemplos específicos
        test_query2 = """
            SELECT TOP 5 Id_Incidente, 
                   Subcategoria_del_Incidente,
                   CASE 
                       WHEN Subcategoria_del_Incidente IS NULL THEN 'ES NULL'
                       WHEN Subcategoria_del_Incidente = '' THEN 'ES VACIO'
                       ELSE 'TIENE VALOR'
                   END as Estado
            FROM TAXONOMIA_INCIDENTES
            WHERE Id_Incidente IN ('INC_USO_PHIP_ECDP', 'INC_CONF_EXCF_FCRA', 'INC_CONF_EXCF_FSRA')
        """
        cursor.execute(test_query2)
        ejemplos = cursor.fetchall()
        print(f"\n🔍 EJEMPLOS ESPECÍFICOS:")
        for row in ejemplos:
            print(f"   - {row.Id_Incidente}: '{row.Subcategoria_del_Incidente}' ({row.Estado})")
        
        # Consulta real
        query = """
            SELECT 
                Id_Incidente,
                Area,
                Efecto,
                Categoria_del_Incidente,
                Subcategoria_del_Incidente,
                AplicaTipoEmpresa
            FROM TAXONOMIA_INCIDENTES
            WHERE (AplicaTipoEmpresa = ? OR AplicaTipoEmpresa = 'AMBAS' OR AplicaTipoEmpresa IS NULL)
            ORDER BY Area, Efecto, Categoria_del_Incidente
        """
        
        print(f"🔍 DEBUG: Ejecutando consulta para tipo_empresa='{tipo_empresa}'")
        cursor.execute(query, (tipo_empresa,))
        rows = cursor.fetchall()
        print(f"🔍 DEBUG: Consulta devolvió {len(rows)} filas")
        
        taxonomias = []
        for row in rows:
            # Debug mejorado
            if 'EXCF' in row.Id_Incidente:
                print(f"\n🔍 DEBUG Taxonomía completa:")
                print(f"   - ID: {row.Id_Incidente}")
                print(f"   - Área: {row.Area}")
                print(f"   - Efecto: {row.Efecto}")
                print(f"   - Categoría: {row.Categoria_del_Incidente}")
                print(f"   - Subcategoría: '{row.Subcategoria_del_Incidente}'")
                print(f"   - Tipo subcategoría: {type(row.Subcategoria_del_Incidente)}")
            
            taxonomias.append({
                'id': row.Id_Incidente,
                'area': row.Area or '',
                'efecto': row.Efecto or '',
                'categoria': row.Categoria_del_Incidente or '',
                'subcategoria': row.Subcategoria_del_Incidente or '',
                'aplica_para': row.AplicaTipoEmpresa or tipo_empresa
            })
        
        return jsonify({
            'status': 'success',
            'tipo_empresa': tipo_empresa,
            'total': len(taxonomias),
            'taxonomias': taxonomias
        })
        
    except Exception as e:
        print(f"Error obteniendo taxonomías flat: {e}")
        response, status = ErrorResponse.generic_error(f"Error: {str(e)}")
        return jsonify(response), status
    
    finally:
        if conn:
            conn.close()
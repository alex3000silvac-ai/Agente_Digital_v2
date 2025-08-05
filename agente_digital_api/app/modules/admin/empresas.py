# modules/admin/empresas.py
# Gestión de empresas completamente modular

from flask import Blueprint, jsonify, request
from datetime import datetime
from ..core.database import get_db_connection, db_validator
from ..core.errors import robust_endpoint, ErrorResponse

empresas_bp = Blueprint('admin_empresas', __name__, url_prefix='/api/admin/empresas')

@empresas_bp.route('/test', methods=['GET'])
def test_endpoint():
    """Endpoint de prueba para verificar que el servidor está actualizado"""
    return jsonify({"status": "ok", "message": "Endpoint actualizado correctamente", "timestamp": str(datetime.now())}), 200

def format_date_safe(fecha, formato='%Y-%m-%d %H:%M:%S'):
    """Formatea fechas de forma segura"""
    if not fecha:
        return None
    return fecha.strftime(formato) if hasattr(fecha, 'strftime') else str(fecha)

@empresas_bp.route('/<int:empresa_id>', methods=['GET'])
def get_empresa_details(empresa_id):
    """Obtiene detalles de una empresa específica"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Consulta directa sin validaciones adicionales
        cursor.execute("SELECT * FROM Empresas WHERE EmpresaID = ?", (empresa_id,))
        empresa_row = cursor.fetchone()
        
        if not empresa_row:
            return jsonify({"error": "Empresa no encontrada"}), 404
        
        # Construir el diccionario manualmente para manejar tipos de datos
        empresa_data = {}
        columns = [column[0] for column in cursor.description]
        
        for i, column_name in enumerate(columns):
            value = empresa_row[i]
            # Convertir fechas a string
            if hasattr(value, 'strftime'):
                empresa_data[column_name] = value.strftime('%Y-%m-%d %H:%M:%S')
            # Convertir bytes a string
            elif isinstance(value, bytes):
                try:
                    empresa_data[column_name] = value.decode('utf-8')
                except:
                    empresa_data[column_name] = None
            # Manejar valores booleanos
            elif isinstance(value, bool):
                empresa_data[column_name] = value
            # Manejar valores None
            elif value is None:
                empresa_data[column_name] = None
            else:
                empresa_data[column_name] = value
        
        return jsonify(empresa_data), 200
    
    except Exception as e:
        print(f"Error al obtener detalles de empresa {empresa_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
    
    finally:
        if conn:
            conn.close()

@empresas_bp.route('/<int:empresa_id>/dashboard-stats', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_dashboard_stats(empresa_id):
    """Obtiene estadísticas del dashboard para una empresa con lógica de sistema completa."""
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error()
        return jsonify(response), status

    try:
        cursor = conn.cursor()

        # 1. Info básica de la empresa
        cursor.execute("SELECT TipoEmpresa FROM Empresas WHERE EmpresaID = ?", (empresa_id,))
        empresa_info = cursor.fetchone()
        if not empresa_info:
            response, status = ErrorResponse.not_found_error("Empresa")
            return jsonify(response), status
        tipo_empresa = empresa_info.TipoEmpresa if empresa_info and hasattr(empresa_info, 'TipoEmpresa') else 'PSE'

        # 2. Estadísticas de Cumplimiento (Actual)
        try:
            # Contar obligaciones base según tipo de empresa
            if tipo_empresa == 'PSE':
                total_obligaciones_base = 14
            elif tipo_empresa == 'OIV':
                total_obligaciones_base = 21
            else:
                total_obligaciones_base = 14  # Default PSE
            
            print(f"DEBUG: Tipo empresa: {tipo_empresa}, Total obligaciones base: {total_obligaciones_base}")
            
            # Luego, contar los estados de cumplimiento
            q_cumplimiento = """
                SELECT 
                    ISNULL(SUM(CASE WHEN C.Estado = 'Implementado' THEN 1 ELSE 0 END), 0) AS Implementadas,
                    ISNULL(SUM(CASE WHEN C.Estado = 'En Proceso' THEN 1 ELSE 0 END), 0) AS EnProceso,
                    ISNULL(SUM(CASE WHEN C.Estado = 'Pendiente' THEN 1 ELSE 0 END), 0) AS Pendientes,
                    ISNULL(SUM(CASE WHEN C.Estado = 'Vencido' THEN 1 ELSE 0 END), 0) AS Vencidas,
                    ISNULL(SUM(CASE WHEN C.Estado = 'No Aplica' THEN 1 ELSE 0 END), 0) AS NoAplica
                FROM CumplimientoEmpresa AS C
                WHERE C.EmpresaID = ?
            """
            cursor.execute(q_cumplimiento, (empresa_id,))
            cumplimiento = cursor.fetchone()
            print(f"DEBUG: Empresa ID: {empresa_id}, Cumplimiento: {cumplimiento}")
            
            # Verificar los valores individuales
            if cumplimiento:
                print(f"DEBUG Valores: Impl={cumplimiento.Implementadas}, EnProc={cumplimiento.EnProceso}, Pend={cumplimiento.Pendientes}")
            
            # Si no hay registros en CumplimientoEmpresa, todas las obligaciones están pendientes
            if not cumplimiento or (cumplimiento.Implementadas + cumplimiento.EnProceso + 
                                   cumplimiento.Pendientes + cumplimiento.Vencidas + cumplimiento.NoAplica) == 0:
                cumplimiento = type('obj', (object,), {
                    'Total': total_obligaciones_base,
                    'Implementadas': 0,
                    'EnProceso': 0,
                    'Pendientes': total_obligaciones_base,
                    'Vencidas': 0,
                    'NoAplica': 0
                })
            else:
                # No podemos modificar pyodbc.Row, crear un objeto nuevo con los valores
                cumplimiento = type('obj', (object,), {
                    'Total': total_obligaciones_base,
                    'Implementadas': cumplimiento.Implementadas,
                    'EnProceso': cumplimiento.EnProceso,
                    'Pendientes': cumplimiento.Pendientes,
                    'Vencidas': cumplimiento.Vencidas,
                    'NoAplica': cumplimiento.NoAplica
                })
        except Exception as e:
            print(f"Error ejecutando query de cumplimiento: {e}")
            import traceback
            traceback.print_exc()
            # Valores por defecto si falla la consulta
            cumplimiento = type('obj', (object,), {
                'Total': 0, 'Implementadas': 0, 'EnProceso': 0, 
                'Pendientes': 0, 'Vencidas': 0, 'NoAplica': 0
            })

        # Usar el total de obligaciones base calculado anteriormente
        total_obligaciones = total_obligaciones_base
        implementadas = cumplimiento.Implementadas or 0
        en_proceso = cumplimiento.EnProceso or 0
        pendientes = cumplimiento.Pendientes or 0
        vencidas = cumplimiento.Vencidas or 0
        
        # Si hay más registros de cumplimiento que el límite, ajustar a los límites
        total_registros = implementadas + en_proceso + pendientes + vencidas
        if total_registros > total_obligaciones:
            # Ajustar proporcionalmente
            factor = total_obligaciones / total_registros
            implementadas = int(implementadas * factor)
            en_proceso = int(en_proceso * factor)
            pendientes = int(pendientes * factor)
            vencidas = int(vencidas * factor)
            # Asegurar que la suma sea exacta
            diferencia = total_obligaciones - (implementadas + en_proceso + pendientes + vencidas)
            if diferencia > 0:
                pendientes += diferencia
        
        porcentaje_cumplimiento = round((implementadas / total_obligaciones) * 100) if total_obligaciones > 0 else 0

        # 3. Estadísticas de Incidentes (TODAS las incidencias, no solo últimos 60 días)
        try:
            q_incidentes = """
                SELECT 
                    ISNULL(COUNT(*), 0) as Total,
                    ISNULL(SUM(CASE WHEN EstadoActual = 'Abierto' THEN 1 ELSE 0 END), 0) as Activos,
                    ISNULL(SUM(CASE WHEN EstadoActual = 'Cerrado' THEN 1 ELSE 0 END), 0) as Cerrados,
                    ISNULL(SUM(CASE WHEN EstadoActual = 'Pendiente' THEN 1 ELSE 0 END), 0) as Pendientes,
                    ISNULL(SUM(CASE WHEN Criticidad = 'Alta' THEN 1 ELSE 0 END), 0) as CritAlta,
                    ISNULL(SUM(CASE WHEN Criticidad = 'Media' THEN 1 ELSE 0 END), 0) as CritMedia,
                    ISNULL(SUM(CASE WHEN Criticidad = 'Baja' THEN 1 ELSE 0 END), 0) as CritBaja
                FROM Incidentes
                WHERE EmpresaID = ?
            """
            cursor.execute(q_incidentes, (empresa_id,))
            incidentes = cursor.fetchone()
        except Exception as e:
            print(f"Error ejecutando query de incidentes: {e}")
            # Valores por defecto si falla la consulta
            incidentes = type('obj', (object,), {
                'Total': 0, 'Activos': 0, 'Cerrados': 0, 
                'Pendientes': 0, 'CritAlta': 0, 'CritMedia': 0, 'CritBaja': 0
            })
        
        # 4. Lógica de Riesgo
        riesgo_nivel = 'bajo'
        if porcentaje_cumplimiento < 50 or (incidentes and incidentes.CritAlta > 0):
            riesgo_nivel = 'alto'
        elif porcentaje_cumplimiento < 80 or (incidentes and incidentes.CritMedia > 0):
            riesgo_nivel = 'medio'

        # 5. Lógica de Tendencia (comparando con 30 días antes)
        try:
            # Verificar si existe la columna FechaModificacion
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'CumplimientoEmpresa' 
                AND COLUMN_NAME = 'FechaModificacion'
            """)
            has_fecha_modificacion = cursor.fetchone()[0] > 0
            
            if has_fecha_modificacion:
                # Query con FechaModificacion
                q_cumplimiento_pasado = """
                    SELECT ISNULL(SUM(CASE WHEN Estado = 'Implementado' THEN 1 ELSE 0 END), 0)
                    FROM CumplimientoEmpresa
                    WHERE EmpresaID = ? AND FechaModificacion < DATEADD(day, -30, GETDATE())
                """
            else:
                # Query sin FechaModificacion - usa el valor actual como fallback
                q_cumplimiento_pasado = """
                    SELECT ISNULL(SUM(CASE WHEN Estado = 'Implementado' THEN 1 ELSE 0 END), 0)
                    FROM CumplimientoEmpresa
                    WHERE EmpresaID = ?
                """
            
            cursor.execute(q_cumplimiento_pasado, (empresa_id,))
            cumplimiento_pasado_result = cursor.fetchone()
            cumplimiento_pasado = cumplimiento_pasado_result[0] if cumplimiento_pasado_result else 0
        except Exception as e:
            print(f"Error ejecutando query de cumplimiento pasado: {e}")
            cumplimiento_pasado = 0
        
        tendencia = 'estable'
        if porcentaje_cumplimiento > (round((cumplimiento_pasado / total_obligaciones) * 100) if total_obligaciones > 0 else 0):
            tendencia = 'mejora'
        elif porcentaje_cumplimiento < (round((cumplimiento_pasado / total_obligaciones) * 100) if total_obligaciones > 0 else 0):
            tendencia = 'deterioro'

        # 6. Próximos Vencimientos
        try:
            q_vencimientos = """
                SELECT TOP 3 R.DescripcionRecomendacion, C.FechaTermino, DATEDIFF(day, GETDATE(), C.FechaTermino) as DiasRestantes
                FROM CumplimientoEmpresa C
                JOIN Recomendaciones R ON C.RecomendacionID = R.RecomendacionID
                WHERE C.EmpresaID = ? AND C.Estado IN ('Pendiente', 'En Proceso') AND C.FechaTermino IS NOT NULL
                ORDER BY C.FechaTermino ASC
            """
            cursor.execute(q_vencimientos, (empresa_id,))
            vencimientos_data = cursor.fetchall()
            proximas_fechas = [{"ArticuloNorma": r.DescripcionRecomendacion, "FechaTermino": format_date_safe(r.FechaTermino, '%Y-%m-%d'), "DiasRestantes": r.DiasRestantes} for r in vencimientos_data]
        except Exception as e:
            print(f"Error ejecutando query de vencimientos: {e}")
            proximas_fechas = []

        # 7. Total Evidencias - verificar si la tabla existe primero
        total_evidencias = 0
        try:
            # Verificar si existe la tabla Evidencias
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'Evidencias'
            """)
            if cursor.fetchone()[0] > 0:
                cursor.execute("SELECT COUNT(*) FROM Evidencias WHERE EmpresaID = ?", (empresa_id,))
                evidencias_result = cursor.fetchone()
                total_evidencias = evidencias_result[0] if evidencias_result else 0
            else:
                # Si no existe la tabla, intentar contar archivos subidos desde otra tabla
                try:
                    # Intentar contar desde CumplimientoEmpresa donde haya evidencias
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM CumplimientoEmpresa 
                        WHERE EmpresaID = ? 
                        AND (ArchivoEvidencia IS NOT NULL OR RutaEvidencia IS NOT NULL)
                    """, (empresa_id,))
                    evidencias_result = cursor.fetchone()
                    total_evidencias = evidencias_result[0] if evidencias_result else 0
                except:
                    total_evidencias = 0
        except Exception as e:
            print(f"Error ejecutando query de evidencias: {e}")
            total_evidencias = 0

        # 7.5 Obtener tipos frecuentes de incidentes
        def obtener_tipos_frecuentes(cursor, empresa_id):
            try:
                q_tipos = """
                    SELECT TOP 3 
                        ISNULL(TipoFlujo, 'No especificado') as Tipo,
                        COUNT(*) as Cantidad
                    FROM Incidentes
                    WHERE EmpresaID = ? 
                    GROUP BY TipoFlujo
                    ORDER BY COUNT(*) DESC
                """
                cursor.execute(q_tipos, (empresa_id,))
                tipos_data = cursor.fetchall()
                return [{"tipo": r.Tipo, "cantidad": r.Cantidad} for r in tipos_data]
            except Exception as e:
                print(f"Error obteniendo tipos frecuentes: {e}")
                return []

        # 8. Construir respuesta final
        print(f"\nDEBUG FINAL para empresa {empresa_id}:")
        print(f"  - Total obligaciones base: {total_obligaciones_base}")
        print(f"  - Total obligaciones final: {total_obligaciones}")
        print(f"  - Implementadas: {implementadas}")
        print(f"  - En proceso: {en_proceso}")
        print(f"  - Pendientes: {pendientes}")
        print(f"  - Vencidas: {vencidas}")
        print(f"  - Incidentes total: {incidentes.Total or 0}")
        
        stats = {
            'empresa_id': empresa_id,
            'tipo_empresa': tipo_empresa,
            'porcentaje_cumplimiento': porcentaje_cumplimiento,
            'total_obligaciones': total_obligaciones,
            'implementadas': implementadas,
            'en_proceso': en_proceso,
            'pendientes': pendientes,
            'vencidas': vencidas,
            'no_aplica': cumplimiento.NoAplica or 0,
            'total_evidencias': total_evidencias,
            'riesgo_nivel': riesgo_nivel,
            'tendencia_cumplimiento': tendencia,
            'incidentes': {
                'total': incidentes.Total or 0,  # Cambiado: ahora muestra TODAS las incidencias
                'activos': incidentes.Activos or 0,
                'cerrados': incidentes.Cerrados or 0,
                'pendientes': incidentes.Pendientes or 0,
                'criticidad_alta': incidentes.CritAlta or 0,
                'criticidad_media': incidentes.CritMedia or 0,
                'criticidad_baja': incidentes.CritBaja or 0,
                'tipos_frecuentes': obtener_tipos_frecuentes(cursor, empresa_id)
            },
            'proximas_fechas': proximas_fechas,
            'timestamp': format_date_safe(datetime.now())
        }

        return jsonify(stats)

    except Exception as e:
        print(f"Error crítico en get_dashboard_stats: {e}")
        response, status = ErrorResponse.generic_error(str(e))
        return jsonify(response), status
    finally:
        if conn:
            conn.close()


@empresas_bp.route('', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def list_empresas():
    """Lista todas las empresas disponibles"""
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error()
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        if not db_validator.table_exists(cursor, 'Empresas'):
            return jsonify([])
        
        cursor.execute("SELECT EmpresaID, RazonSocial, TipoEmpresa FROM Empresas ORDER BY RazonSocial")
        rows = cursor.fetchall()
        
        empresas = []
        for row in rows:
            empresas.append({
                'EmpresaID': row[0],
                'RazonSocial': row[1],
                'TipoEmpresa': row[2] if len(row) > 2 else 'PSE'
            })
        
        return jsonify(empresas)
        
    finally:
        if conn:
            conn.close()
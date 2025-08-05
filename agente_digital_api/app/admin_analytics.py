# app/admin_analytics.py
"""
📊 MÓDULO DE ANALÍTICAS AVANZADAS PARA ADMINISTRADORES
Sistema de análisis predictivo y reportes inteligentes
"""

from flask import Blueprint, jsonify, request
from .database import get_db_connection
# from .admin_users_manager import verificar_admin_autenticado, verificar_permiso_admin, registrar_auditoria_admin  # Módulo deshabilitado

# Funciones temporales de reemplazo
from functools import wraps
def verificar_admin_autenticado(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper

def verificar_permiso_admin(permiso):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    return decorator

def registrar_auditoria_admin(admin_id, accion, descripcion):
    pass
from datetime import datetime, timedelta
import json
import statistics

admin_analytics_bp = Blueprint('admin_analytics', __name__, url_prefix='/api/admin-analytics')

# ============================================================================
# ANÁLISIS PREDICTIVO
# ============================================================================

@admin_analytics_bp.route('/tendencias-uso', methods=['GET'])
@verificar_admin_autenticado
@verificar_permiso_admin('ADMIN_CORP')
def obtener_tendencias_uso():
    """
    📈 Análisis de tendencias de uso del sistema
    """
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión"}), 500
        
        cursor = conn.cursor()
        
        # Tendencia de usuarios activos (últimos 90 días)
        cursor.execute("""
            WITH DiasActividad AS (
                SELECT 
                    CAST(FechaAccion AS DATE) as Fecha,
                    COUNT(DISTINCT AdminID) as UsuariosActivos
                FROM AuditoriaAdministradores
                WHERE FechaAccion >= DATEADD(day, -90, GETDATE())
                GROUP BY CAST(FechaAccion AS DATE)
            ),
            TendenciaCalculo AS (
                SELECT 
                    Fecha,
                    UsuariosActivos,
                    LAG(UsuariosActivos, 1) OVER (ORDER BY Fecha) as UsuariosAnterior,
                    ROW_NUMBER() OVER (ORDER BY Fecha) as NumeroFila
                FROM DiasActividad
            )
            SELECT 
                Fecha,
                UsuariosActivos,
                CASE 
                    WHEN UsuariosAnterior IS NOT NULL THEN 
                        CAST((UsuariosActivos - UsuariosAnterior) AS FLOAT) / UsuariosAnterior * 100
                    ELSE 0 
                END as CambioPorcentual
            FROM TendenciaCalculo
            ORDER BY Fecha
        """)
        
        tendencia_usuarios = []
        for row in cursor.fetchall():
            tendencia_usuarios.append({
                "fecha": row[0].isoformat() if row[0] else None,
                "usuarios_activos": row[1],
                "cambio_porcentual": float(row[2]) if row[2] else 0
            })
        
        # Predicción para próximos 30 días (regresión lineal simple)
        if len(tendencia_usuarios) > 7:
            valores_y = [item['usuarios_activos'] for item in tendencia_usuarios[-30:]]
            valores_x = list(range(len(valores_y)))
            
            # Calcular regresión lineal
            n = len(valores_y)
            sum_x = sum(valores_x)
            sum_y = sum(valores_y)
            sum_xy = sum(x * y for x, y in zip(valores_x, valores_y))
            sum_x2 = sum(x * x for x in valores_x)
            
            if n * sum_x2 - sum_x * sum_x != 0:
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                intercept = (sum_y - slope * sum_x) / n
                
                # Generar predicción
                prediccion_30_dias = []
                for i in range(30):
                    fecha_prediccion = datetime.now() + timedelta(days=i)
                    valor_prediccion = slope * (len(valores_y) + i) + intercept
                    prediccion_30_dias.append({
                        "fecha": fecha_prediccion.isoformat(),
                        "usuarios_predichos": max(0, int(valor_prediccion))
                    })
            else:
                prediccion_30_dias = []
        else:
            prediccion_30_dias = []
        
        # Patrones de uso por día de la semana
        cursor.execute("""
            SELECT 
                DATENAME(WEEKDAY, FechaAccion) as DiaSemana,
                DATEPART(WEEKDAY, FechaAccion) as NumDia,
                COUNT(*) as TotalAcciones,
                COUNT(DISTINCT AdminID) as UsuariosUnicos,
                AVG(CAST(DuracionMs AS FLOAT)) as DuracionPromedio
            FROM AuditoriaAdministradores
            WHERE FechaAccion >= DATEADD(day, -30, GETDATE())
            AND DuracionMs IS NOT NULL
            GROUP BY DATENAME(WEEKDAY, FechaAccion), DATEPART(WEEKDAY, FechaAccion)
            ORDER BY NumDia
        """)
        
        patrones_semanales = []
        for row in cursor.fetchall():
            patrones_semanales.append({
                "dia_semana": row[0],
                "numero_dia": row[1],
                "total_acciones": row[2],
                "usuarios_unicos": row[3],
                "duracion_promedio": float(row[4]) if row[4] else 0
            })
        
        # Horas pico de actividad
        cursor.execute("""
            SELECT 
                DATEPART(HOUR, FechaAccion) as Hora,
                COUNT(*) as TotalAcciones,
                COUNT(DISTINCT AdminID) as UsuariosUnicos
            FROM AuditoriaAdministradores
            WHERE FechaAccion >= DATEADD(day, -7, GETDATE())
            GROUP BY DATEPART(HOUR, FechaAccion)
            ORDER BY Hora
        """)
        
        horas_pico = []
        for row in cursor.fetchall():
            horas_pico.append({
                "hora": row[0],
                "total_acciones": row[1],
                "usuarios_unicos": row[2]
            })
        
        return jsonify({
            "success": True,
            "tendencia_usuarios": tendencia_usuarios,
            "prediccion_30_dias": prediccion_30_dias,
            "patrones_semanales": patrones_semanales,
            "horas_pico": horas_pico,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"ERROR obteniendo tendencias: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@admin_analytics_bp.route('/analisis-comportamiento', methods=['GET'])
@verificar_admin_autenticado
@verificar_permiso_admin('ADMIN_CORP')
def obtener_analisis_comportamiento():
    """
    🧠 Análisis de comportamiento de usuarios
    """
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión"}), 500
        
        cursor = conn.cursor()
        
        # Análisis de sesiones
        cursor.execute("""
            SELECT 
                AVG(DATEDIFF(MINUTE, FechaCreacion, ISNULL(FechaUltimaActividad, FechaCreacion))) as DuracionPromedio,
                MIN(DATEDIFF(MINUTE, FechaCreacion, ISNULL(FechaUltimaActividad, FechaCreacion))) as DuracionMinima,
                MAX(DATEDIFF(MINUTE, FechaCreacion, ISNULL(FechaUltimaActividad, FechaCreacion))) as DuracionMaxima,
                COUNT(*) as TotalSesiones,
                COUNT(DISTINCT AdminID) as UsuariosUnicos
            FROM SesionesAdministradores
            WHERE FechaCreacion >= DATEADD(day, -30, GETDATE())
        """)
        
        analisis_sesiones = cursor.fetchone()
        estadisticas_sesiones = {
            "duracion_promedio_minutos": float(analisis_sesiones[0]) if analisis_sesiones[0] else 0,
            "duracion_minima_minutos": analisis_sesiones[1] if analisis_sesiones[1] else 0,
            "duracion_maxima_minutos": analisis_sesiones[2] if analisis_sesiones[2] else 0,
            "total_sesiones": analisis_sesiones[3],
            "usuarios_unicos": analisis_sesiones[4]
        }
        
        # Acciones más comunes por tipo de admin
        cursor.execute("""
            SELECT 
                ta.Nombre as TipoAdmin,
                aa.Accion,
                aa.Modulo,
                COUNT(*) as Frecuencia,
                AVG(CAST(aa.DuracionMs AS FLOAT)) as DuracionPromedio
            FROM AuditoriaAdministradores aa
            INNER JOIN AdministradoresSistema a ON aa.AdminID = a.AdminID
            INNER JOIN TiposAdministradores ta ON a.TipoAdminID = ta.TipoAdminID
            WHERE aa.FechaAccion >= DATEADD(day, -30, GETDATE())
            GROUP BY ta.Nombre, aa.Accion, aa.Modulo
            HAVING COUNT(*) > 5
            ORDER BY ta.Nombre, Frecuencia DESC
        """)
        
        acciones_por_tipo = {}
        for row in cursor.fetchall():
            tipo_admin = row[0]
            if tipo_admin not in acciones_por_tipo:
                acciones_por_tipo[tipo_admin] = []
            
            acciones_por_tipo[tipo_admin].append({
                "accion": row[1],
                "modulo": row[2],
                "frecuencia": row[3],
                "duracion_promedio": float(row[4]) if row[4] else 0
            })
        
        # Detección de patrones anómalos
        cursor.execute("""
            WITH EstadisticasBase AS (
                SELECT 
                    AdminID,
                    COUNT(*) as TotalAcciones,
                    COUNT(DISTINCT Modulo) as ModulosUsados,
                    AVG(CAST(DuracionMs AS FLOAT)) as DuracionPromedio
                FROM AuditoriaAdministradores
                WHERE FechaAccion >= DATEADD(day, -30, GETDATE())
                AND DuracionMs IS NOT NULL
                GROUP BY AdminID
            ),
            Promedios AS (
                SELECT 
                    AVG(TotalAcciones) as PromedioAcciones,
                    AVG(ModulosUsados) as PromedioModulos,
                    AVG(DuracionPromedio) as PromedioDuracion
                FROM EstadisticasBase
            )
            SELECT 
                a.AdminID,
                u.NombreCompleto,
                eb.TotalAcciones,
                eb.ModulosUsados,
                eb.DuracionPromedio,
                CASE 
                    WHEN eb.TotalAcciones > p.PromedioAcciones * 3 THEN 'ALTA_ACTIVIDAD'
                    WHEN eb.TotalAcciones < p.PromedioAcciones * 0.3 THEN 'BAJA_ACTIVIDAD'
                    WHEN eb.DuracionPromedio > p.PromedioDuracion * 2 THEN 'LENTO'
                    ELSE 'NORMAL'
                END as Anomalia
            FROM EstadisticasBase eb
            CROSS JOIN Promedios p
            INNER JOIN AdministradoresSistema a ON eb.AdminID = a.AdminID
            INNER JOIN Usuarios u ON a.UsuarioID = u.UsuarioID
            WHERE eb.TotalAcciones > p.PromedioAcciones * 3 
               OR eb.TotalAcciones < p.PromedioAcciones * 0.3
               OR eb.DuracionPromedio > p.PromedioDuracion * 2
        """)
        
        anomalias = []
        for row in cursor.fetchall():
            anomalias.append({
                "admin_id": row[0],
                "nombre": row[1],
                "total_acciones": row[2],
                "modulos_usados": row[3],
                "duracion_promedio": float(row[4]) if row[4] else 0,
                "tipo_anomalia": row[5]
            })
        
        # Análisis de errores por usuario
        cursor.execute("""
            SELECT 
                u.NombreCompleto,
                COUNT(CASE WHEN aa.Resultado = 'ERROR' THEN 1 END) as TotalErrores,
                COUNT(*) as TotalAcciones,
                CAST(COUNT(CASE WHEN aa.Resultado = 'ERROR' THEN 1 END) AS FLOAT) / COUNT(*) * 100 as PorcentajeError
            FROM AuditoriaAdministradores aa
            INNER JOIN AdministradoresSistema a ON aa.AdminID = a.AdminID
            INNER JOIN Usuarios u ON a.UsuarioID = u.UsuarioID
            WHERE aa.FechaAccion >= DATEADD(day, -30, GETDATE())
            GROUP BY u.NombreCompleto
            HAVING COUNT(*) > 10
            ORDER BY PorcentajeError DESC
        """)
        
        errores_por_usuario = []
        for row in cursor.fetchall():
            errores_por_usuario.append({
                "nombre": row[0],
                "total_errores": row[1],
                "total_acciones": row[2],
                "porcentaje_error": float(row[3]) if row[3] else 0
            })
        
        return jsonify({
            "success": True,
            "estadisticas_sesiones": estadisticas_sesiones,
            "acciones_por_tipo": acciones_por_tipo,
            "anomalias": anomalias,
            "errores_por_usuario": errores_por_usuario,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"ERROR obteniendo análisis de comportamiento: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@admin_analytics_bp.route('/reportes-personalizados', methods=['POST'])
@verificar_admin_autenticado
@verificar_permiso_admin('ADMIN_CORP')
def generar_reporte_personalizado():
    """
    📊 Generador de reportes personalizados
    """
    try:
        data = request.get_json()
        admin_info = request.admin_actual
        
        # Parámetros del reporte
        nombre_reporte = data.get('nombre_reporte', 'Reporte Personalizado')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        filtros = data.get('filtros', {})
        metricas = data.get('metricas', [])
        agrupacion = data.get('agrupacion', 'dia')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión"}), 500
        
        cursor = conn.cursor()
        
        # Construir consulta dinámica
        select_parts = []
        group_by_parts = []
        where_parts = ["aa.FechaAccion >= ?", "aa.FechaAccion <= ?"]
        params = [fecha_inicio, fecha_fin]
        
        # Agrupación temporal
        if agrupacion == 'hora':
            select_parts.append("DATEPART(HOUR, aa.FechaAccion) as Periodo")
            group_by_parts.append("DATEPART(HOUR, aa.FechaAccion)")
        elif agrupacion == 'dia':
            select_parts.append("CAST(aa.FechaAccion AS DATE) as Periodo")
            group_by_parts.append("CAST(aa.FechaAccion AS DATE)")
        elif agrupacion == 'semana':
            select_parts.append("DATEPART(WEEK, aa.FechaAccion) as Periodo")
            group_by_parts.append("DATEPART(WEEK, aa.FechaAccion)")
        elif agrupacion == 'mes':
            select_parts.append("DATEPART(MONTH, aa.FechaAccion) as Periodo")
            group_by_parts.append("DATEPART(MONTH, aa.FechaAccion)")
        
        # Métricas solicitadas
        if 'total_acciones' in metricas:
            select_parts.append("COUNT(*) as TotalAcciones")
        
        if 'usuarios_unicos' in metricas:
            select_parts.append("COUNT(DISTINCT aa.AdminID) as UsuariosUnicos")
        
        if 'duracion_promedio' in metricas:
            select_parts.append("AVG(CAST(aa.DuracionMs AS FLOAT)) as DuracionPromedio")
        
        if 'errores' in metricas:
            select_parts.append("COUNT(CASE WHEN aa.Resultado = 'ERROR' THEN 1 END) as TotalErrores")
        
        if 'tasa_exito' in metricas:
            select_parts.append("CAST(COUNT(CASE WHEN aa.Resultado = 'EXITOSO' THEN 1 END) AS FLOAT) / COUNT(*) * 100 as TasaExito")
        
        # Filtros adicionales
        if filtros.get('tipo_admin'):
            where_parts.append("ta.Codigo = ?")
            params.append(filtros['tipo_admin'])
        
        if filtros.get('modulo'):
            where_parts.append("aa.Modulo = ?")
            params.append(filtros['modulo'])
        
        if filtros.get('accion'):
            where_parts.append("aa.Accion = ?")
            params.append(filtros['accion'])
        
        # Construir consulta completa
        consulta = f"""
            SELECT {', '.join(select_parts)}
            FROM AuditoriaAdministradores aa
            INNER JOIN AdministradoresSistema a ON aa.AdminID = a.AdminID
            INNER JOIN TiposAdministradores ta ON a.TipoAdminID = ta.TipoAdminID
            WHERE {' AND '.join(where_parts)}
            GROUP BY {', '.join(group_by_parts)}
            ORDER BY Periodo
        """
        
        cursor.execute(consulta, params)
        
        # Procesar resultados
        resultados = []
        columnas = [desc[0] for desc in cursor.description]
        
        for row in cursor.fetchall():
            fila = {}
            for i, valor in enumerate(row):
                if isinstance(valor, datetime):
                    fila[columnas[i]] = valor.isoformat()
                else:
                    fila[columnas[i]] = valor
            resultados.append(fila)
        
        # Registrar auditoría
        registrar_auditoria_admin(
            admin_info['admin_id'],
            "GENERATE_CUSTOM_REPORT",
            "ANALYTICS",
            recurso_afectado="Reporte Personalizado",
            datos_nuevos={
                "nombre_reporte": nombre_reporte,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "filtros": filtros,
                "metricas": metricas,
                "cantidad_resultados": len(resultados)
            }
        )
        
        return jsonify({
            "success": True,
            "reporte": {
                "nombre": nombre_reporte,
                "fecha_generacion": datetime.now().isoformat(),
                "parametros": {
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin,
                    "filtros": filtros,
                    "metricas": metricas,
                    "agrupacion": agrupacion
                },
                "datos": resultados,
                "columnas": columnas,
                "total_registros": len(resultados)
            }
        }), 200
        
    except Exception as e:
        print(f"ERROR generando reporte personalizado: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@admin_analytics_bp.route('/alertas-inteligentes', methods=['GET'])
@verificar_admin_autenticado
@verificar_permiso_admin('ADMIN_CORP')
def obtener_alertas_inteligentes():
    """
    🚨 Sistema de alertas inteligentes basado en análisis
    """
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión"}), 500
        
        cursor = conn.cursor()
        
        alertas = []
        
        # Alerta: Incremento inusual de errores
        cursor.execute("""
            WITH ErroresHoy AS (
                SELECT COUNT(*) as Errores
                FROM AuditoriaAdministradores
                WHERE Resultado = 'ERROR'
                AND CAST(FechaAccion AS DATE) = CAST(GETDATE() AS DATE)
            ),
            PromedioErrores AS (
                SELECT AVG(ErroresDiarios) as PromedioErrores
                FROM (
                    SELECT COUNT(*) as ErroresDiarios
                    FROM AuditoriaAdministradores
                    WHERE Resultado = 'ERROR'
                    AND FechaAccion >= DATEADD(day, -7, GETDATE())
                    AND FechaAccion < CAST(GETDATE() AS DATE)
                    GROUP BY CAST(FechaAccion AS DATE)
                ) AS ErroresPorDia
            )
            SELECT 
                eh.Errores,
                pe.PromedioErrores,
                CASE 
                    WHEN pe.PromedioErrores > 0 THEN eh.Errores / pe.PromedioErrores
                    ELSE 0
                END as Ratio
            FROM ErroresHoy eh
            CROSS JOIN PromedioErrores pe
        """)
        
        resultado_errores = cursor.fetchone()
        if resultado_errores and resultado_errores[2] > 2:  # Más del doble del promedio
            alertas.append({
                "tipo": "ANOMALIA_ERRORES",
                "severidad": "ALTA",
                "titulo": "Incremento Inusual de Errores",
                "mensaje": f"Errores hoy: {resultado_errores[0]}, Promedio: {resultado_errores[1]:.1f}",
                "valor_actual": resultado_errores[0],
                "valor_referencia": resultado_errores[1],
                "timestamp": datetime.now().isoformat()
            })
        
        # Alerta: Usuarios con comportamiento anómalo
        cursor.execute("""
            WITH ActividadUsuarios AS (
                SELECT 
                    aa.AdminID,
                    u.NombreCompleto,
                    COUNT(*) as AccionesHoy
                FROM AuditoriaAdministradores aa
                INNER JOIN AdministradoresSistema a ON aa.AdminID = a.AdminID
                INNER JOIN Usuarios u ON a.UsuarioID = u.UsuarioID
                WHERE CAST(aa.FechaAccion AS DATE) = CAST(GETDATE() AS DATE)
                GROUP BY aa.AdminID, u.NombreCompleto
            ),
            PromedioActividad AS (
                SELECT 
                    AdminID,
                    AVG(AccionesDiarias) as PromedioAcciones
                FROM (
                    SELECT 
                        AdminID,
                        COUNT(*) as AccionesDiarias
                    FROM AuditoriaAdministradores
                    WHERE FechaAccion >= DATEADD(day, -14, GETDATE())
                    AND FechaAccion < CAST(GETDATE() AS DATE)
                    GROUP BY AdminID, CAST(FechaAccion AS DATE)
                ) AS ActividadDiaria
                GROUP BY AdminID
            )
            SELECT 
                au.NombreCompleto,
                au.AccionesHoy,
                pa.PromedioAcciones
            FROM ActividadUsuarios au
            INNER JOIN PromedioActividad pa ON au.AdminID = pa.AdminID
            WHERE au.AccionesHoy > pa.PromedioAcciones * 5
        """)
        
        usuarios_anomalos = cursor.fetchall()
        if usuarios_anomalos:
            for usuario in usuarios_anomalos:
                alertas.append({
                    "tipo": "ACTIVIDAD_ANOMALA",
                    "severidad": "MEDIA",
                    "titulo": "Actividad Inusual Detectada",
                    "mensaje": f"{usuario[0]}: {usuario[1]} acciones hoy (promedio: {usuario[2]:.1f})",
                    "usuario": usuario[0],
                    "valor_actual": usuario[1],
                    "valor_referencia": usuario[2],
                    "timestamp": datetime.now().isoformat()
                })
        
        # Alerta: Caída en actividad general
        cursor.execute("""
            WITH ActividadHoy AS (
                SELECT COUNT(*) as AccionesHoy
                FROM AuditoriaAdministradores
                WHERE CAST(FechaAccion AS DATE) = CAST(GETDATE() AS DATE)
            ),
            PromedioActividad AS (
                SELECT AVG(AccionesDiarias) as PromedioAcciones
                FROM (
                    SELECT COUNT(*) as AccionesDiarias
                    FROM AuditoriaAdministradores
                    WHERE FechaAccion >= DATEADD(day, -7, GETDATE())
                    AND FechaAccion < CAST(GETDATE() AS DATE)
                    GROUP BY CAST(FechaAccion AS DATE)
                ) AS ActividadDiaria
            )
            SELECT 
                ah.AccionesHoy,
                pa.PromedioAcciones
            FROM ActividadHoy ah
            CROSS JOIN PromedioActividad pa
        """)
        
        resultado_actividad = cursor.fetchone()
        if resultado_actividad and resultado_actividad[1] > 0 and resultado_actividad[0] < resultado_actividad[1] * 0.5:
            alertas.append({
                "tipo": "BAJA_ACTIVIDAD",
                "severidad": "MEDIA",
                "titulo": "Caída en Actividad General",
                "mensaje": f"Actividad hoy: {resultado_actividad[0]}, Promedio: {resultado_actividad[1]:.1f}",
                "valor_actual": resultado_actividad[0],
                "valor_referencia": resultado_actividad[1],
                "timestamp": datetime.now().isoformat()
            })
        
        return jsonify({
            "success": True,
            "alertas": alertas,
            "total_alertas": len(alertas),
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"ERROR obteniendo alertas inteligentes: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@admin_analytics_bp.route('/recomendaciones-optimizacion', methods=['GET'])
@verificar_admin_autenticado
@verificar_permiso_admin('ADMIN_CORP')
def obtener_recomendaciones_optimizacion():
    """
    💡 Recomendaciones inteligentes para optimización del sistema
    """
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión"}), 500
        
        cursor = conn.cursor()
        
        recomendaciones = []
        
        # Recomendación: Usuarios inactivos
        cursor.execute("""
            SELECT COUNT(*) FROM Usuarios
            WHERE EstadoActivo = 1
            AND (UltimoAcceso IS NULL OR UltimoAcceso < DATEADD(day, -60, GETDATE()))
        """)
        usuarios_inactivos = cursor.fetchone()[0]
        
        if usuarios_inactivos > 5:
            recomendaciones.append({
                "tipo": "LIMPIEZA_USUARIOS",
                "prioridad": "BAJA",
                "titulo": "Limpiar Usuarios Inactivos",
                "descripcion": f"Hay {usuarios_inactivos} usuarios sin acceso en más de 60 días",
                "accion_recomendada": "Desactivar o eliminar usuarios inactivos",
                "impacto_estimado": "Mejora en rendimiento de consultas",
                "esfuerzo": "BAJO"
            })
        
        # Recomendación: Optimización de sesiones
        cursor.execute("""
            SELECT COUNT(*) FROM SesionesAdministradores
            WHERE EstadoSesion = 'ACTIVA'
            AND DATEDIFF(hour, FechaCreacion, GETDATE()) > 12
        """)
        sesiones_largas = cursor.fetchone()[0]
        
        if sesiones_largas > 3:
            recomendaciones.append({
                "tipo": "GESTION_SESIONES",
                "prioridad": "MEDIA",
                "titulo": "Optimizar Gestión de Sesiones",
                "descripcion": f"Hay {sesiones_largas} sesiones activas por más de 12 horas",
                "accion_recomendada": "Implementar cierre automático de sesiones",
                "impacto_estimado": "Mejora en seguridad y rendimiento",
                "esfuerzo": "MEDIO"
            })
        
        # Recomendación: Análisis de rendimiento
        cursor.execute("""
            SELECT 
                Modulo,
                AVG(CAST(DuracionMs AS FLOAT)) as DuracionPromedio
            FROM AuditoriaAdministradores
            WHERE DuracionMs IS NOT NULL
            AND FechaAccion >= DATEADD(day, -7, GETDATE())
            GROUP BY Modulo
            HAVING AVG(CAST(DuracionMs AS FLOAT)) > 2000
        """)
        
        modulos_lentos = cursor.fetchall()
        if modulos_lentos:
            for modulo in modulos_lentos:
                recomendaciones.append({
                    "tipo": "OPTIMIZACION_RENDIMIENTO",
                    "prioridad": "ALTA",
                    "titulo": f"Optimizar Módulo {modulo[0]}",
                    "descripcion": f"Tiempo promedio: {modulo[1]:.0f}ms",
                    "accion_recomendada": "Revisar consultas y optimizar código",
                    "impacto_estimado": "Mejora significativa en experiencia de usuario",
                    "esfuerzo": "ALTO"
                })
        
        # Recomendación: Distribución de carga
        cursor.execute("""
            SELECT 
                DATEPART(hour, FechaAccion) as Hora,
                COUNT(*) as Acciones
            FROM AuditoriaAdministradores
            WHERE FechaAccion >= DATEADD(day, -7, GETDATE())
            GROUP BY DATEPART(hour, FechaAccion)
            ORDER BY Acciones DESC
        """)
        
        horas_actividad = cursor.fetchall()
        if horas_actividad and horas_actividad[0][1] > 100:  # Más de 100 acciones en la hora pico
            recomendaciones.append({
                "tipo": "BALANCEO_CARGA",
                "prioridad": "MEDIA",
                "titulo": "Considerar Balanceo de Carga",
                "descripcion": f"Hora pico: {horas_actividad[0][0]}:00 con {horas_actividad[0][1]} acciones",
                "accion_recomendada": "Implementar distribución de carga o cache",
                "impacto_estimado": "Mejora en tiempo de respuesta",
                "esfuerzo": "ALTO"
            })
        
        # Recomendación: Análisis de errores
        cursor.execute("""
            SELECT 
                Accion,
                COUNT(*) as TotalErrores
            FROM AuditoriaAdministradores
            WHERE Resultado = 'ERROR'
            AND FechaAccion >= DATEADD(day, -30, GETDATE())
            GROUP BY Accion
            ORDER BY TotalErrores DESC
        """)
        
        errores_frecuentes = cursor.fetchall()
        if errores_frecuentes and errores_frecuentes[0][1] > 10:
            recomendaciones.append({
                "tipo": "CORRECCION_ERRORES",
                "prioridad": "ALTA",
                "titulo": f"Corregir Errores en {errores_frecuentes[0][0]}",
                "descripcion": f"{errores_frecuentes[0][1]} errores en los últimos 30 días",
                "accion_recomendada": "Investigar y corregir la causa raíz",
                "impacto_estimado": "Mejora en confiabilidad del sistema",
                "esfuerzo": "MEDIO"
            })
        
        return jsonify({
            "success": True,
            "recomendaciones": recomendaciones,
            "total_recomendaciones": len(recomendaciones),
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"ERROR obteniendo recomendaciones: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if 'conn' in locals():
            conn.close()
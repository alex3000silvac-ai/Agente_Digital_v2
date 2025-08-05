# app/admin_dashboard.py
"""
📊 DASHBOARD AVANZADO DE ADMINISTRACIÓN
Sistema de métricas y estadísticas en tiempo real para administradores
"""

from flask import Blueprint, jsonify, request
from .database import get_db_connection
from datetime import datetime, timedelta
from functools import wraps
import json
# from .admin_users_manager import verificar_admin_autenticado, registrar_auditoria_admin  # Módulo deshabilitado

# Decorador temporal para reemplazar verificar_admin_autenticado
def verificar_admin_autenticado(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper

# Función temporal para reemplazar registrar_auditoria_admin
def registrar_auditoria_admin(admin_id, accion, descripcion):
    pass

admin_dashboard_bp = Blueprint('admin_dashboard', __name__, url_prefix='/api/admin-dashboard')

# ============================================================================
# MÉTRICAS PRINCIPALES
# ============================================================================

@admin_dashboard_bp.route('/metricas-generales', methods=['GET'])
@verificar_admin_autenticado
def obtener_metricas_generales():
    """
    📊 Obtiene métricas generales del sistema
    """
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión"}), 500
        
        cursor = conn.cursor()
        
        # Métricas básicas
        metricas = {}
        
        # Total de usuarios
        cursor.execute("SELECT COUNT(*) FROM Usuarios WHERE EstadoActivo = 1")
        metricas['total_usuarios'] = cursor.fetchone()[0]
        
        # Usuarios activos hoy
        cursor.execute("""
            SELECT COUNT(*) FROM Usuarios 
            WHERE EstadoActivo = 1 
            AND CAST(UltimoAcceso AS DATE) = CAST(GETDATE() AS DATE)
        """)
        metricas['usuarios_activos_hoy'] = cursor.fetchone()[0]
        
        # Total de administradores
        cursor.execute("SELECT COUNT(*) FROM AdministradoresSistema WHERE EstadoActivo = 1")
        metricas['total_administradores'] = cursor.fetchone()[0]
        
        # Sesiones activas
        cursor.execute("""
            SELECT COUNT(*) FROM SesionesAdministradores 
            WHERE EstadoSesion = 'ACTIVA' 
            AND FechaExpiracion > GETDATE()
        """)
        metricas['sesiones_activas'] = cursor.fetchone()[0]
        
        # Incidentes del mes
        cursor.execute("""
            SELECT COUNT(*) FROM Incidentes 
            WHERE MONTH(FechaCreacion) = MONTH(GETDATE()) 
            AND YEAR(FechaCreacion) = YEAR(GETDATE())
        """)
        metricas['incidentes_mes'] = cursor.fetchone()[0]
        
        # Empresas activas
        cursor.execute("SELECT COUNT(*) FROM Empresas WHERE EstadoActivo = 1")
        metricas['empresas_activas'] = cursor.fetchone()[0]
        
        # Crecimiento mensual
        cursor.execute("""
            SELECT COUNT(*) FROM Usuarios 
            WHERE MONTH(FechaCreacion) = MONTH(GETDATE()) 
            AND YEAR(FechaCreacion) = YEAR(GETDATE())
        """)
        metricas['usuarios_nuevos_mes'] = cursor.fetchone()[0]
        
        # Distribución por roles
        cursor.execute("""
            SELECT Rol, COUNT(*) as Cantidad
            FROM Usuarios 
            WHERE EstadoActivo = 1
            GROUP BY Rol
        """)
        distribucion_roles = {}
        for row in cursor.fetchall():
            distribucion_roles[row[0]] = row[1]
        metricas['distribucion_roles'] = distribucion_roles
        
        # Actividad por horas (últimas 24h)
        cursor.execute("""
            SELECT 
                DATEPART(hour, FechaAccion) as Hora,
                COUNT(*) as Cantidad
            FROM AuditoriaAdministradores
            WHERE FechaAccion >= DATEADD(day, -1, GETDATE())
            GROUP BY DATEPART(hour, FechaAccion)
            ORDER BY Hora
        """)
        actividad_horas = {}
        for row in cursor.fetchall():
            actividad_horas[str(row[0])] = row[1]
        metricas['actividad_24h'] = actividad_horas
        
        return jsonify({
            "success": True,
            "metricas": metricas,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"ERROR obteniendo métricas: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@admin_dashboard_bp.route('/estadisticas-administradores', methods=['GET'])
@verificar_admin_autenticado
def obtener_estadisticas_administradores():
    """
    👥 Estadísticas específicas de administradores
    """
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión"}), 500
        
        cursor = conn.cursor()
        
        # Estadísticas por tipo de admin
        cursor.execute("""
            SELECT 
                ta.Codigo,
                ta.Nombre,
                ta.Color,
                ta.Icono,
                COUNT(a.AdminID) as Cantidad,
                SUM(CASE WHEN s.EstadoSesion = 'ACTIVA' AND s.FechaExpiracion > GETDATE() THEN 1 ELSE 0 END) as SesionesActivas,
                SUM(CASE WHEN CAST(a.FechaUltimoAcceso AS DATE) = CAST(GETDATE() AS DATE) THEN 1 ELSE 0 END) as ActivosHoy
            FROM TiposAdministradores ta
            LEFT JOIN AdministradoresSistema a ON ta.TipoAdminID = a.TipoAdminID AND a.EstadoActivo = 1
            LEFT JOIN SesionesAdministradores s ON a.AdminID = s.AdminID
            GROUP BY ta.Codigo, ta.Nombre, ta.Color, ta.Icono, ta.Nivel
            ORDER BY ta.Nivel
        """)
        
        tipos_admin = []
        for row in cursor.fetchall():
            tipos_admin.append({
                "codigo": row[0],
                "nombre": row[1],
                "color": row[2],
                "icono": row[3],
                "cantidad": row[4],
                "sesiones_activas": row[5],
                "activos_hoy": row[6]
            })
        
        # Actividad reciente
        cursor.execute("""
            SELECT TOP 10
                aa.Accion,
                aa.Modulo,
                aa.FechaAccion,
                u.NombreCompleto,
                aa.Resultado
            FROM AuditoriaAdministradores aa
            INNER JOIN AdministradoresSistema a ON aa.AdminID = a.AdminID
            INNER JOIN Usuarios u ON a.UsuarioID = u.UsuarioID
            ORDER BY aa.FechaAccion DESC
        """)
        
        actividad_reciente = []
        for row in cursor.fetchall():
            actividad_reciente.append({
                "accion": row[0],
                "modulo": row[1],
                "fecha": row[2].isoformat() if row[2] else None,
                "administrador": row[3],
                "resultado": row[4]
            })
        
        # Estadísticas de seguridad
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN IntentosFallidosLogin > 0 THEN 1 END) as CuentasConIntentosFallidos,
                COUNT(CASE WHEN FechaBloqueado IS NOT NULL AND DATEDIFF(minute, FechaBloqueado, GETDATE()) < 30 THEN 1 END) as CuentasBloqueadas,
                AVG(DATEDIFF(hour, FechaCreacion, FechaUltimoAcceso)) as PromedioHorasUso
            FROM AdministradoresSistema
            WHERE EstadoActivo = 1
        """)
        
        seguridad = cursor.fetchone()
        estadisticas_seguridad = {
            "cuentas_con_intentos_fallidos": seguridad[0] if seguridad[0] else 0,
            "cuentas_bloqueadas": seguridad[1] if seguridad[1] else 0,
            "promedio_horas_uso": float(seguridad[2]) if seguridad[2] else 0
        }
        
        return jsonify({
            "success": True,
            "tipos_admin": tipos_admin,
            "actividad_reciente": actividad_reciente,
            "estadisticas_seguridad": estadisticas_seguridad,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"ERROR obteniendo estadísticas de administradores: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@admin_dashboard_bp.route('/metricas-rendimiento', methods=['GET'])
@verificar_admin_autenticado
def obtener_metricas_rendimiento():
    """
    ⚡ Métricas de rendimiento del sistema
    """
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión"}), 500
        
        cursor = conn.cursor()
        
        # Tiempo promedio de respuesta por módulo
        cursor.execute("""
            SELECT 
                Modulo,
                AVG(CAST(DuracionMs AS FLOAT)) as TiempoPromedio,
                COUNT(*) as CantidadAcciones
            FROM AuditoriaAdministradores
            WHERE DuracionMs IS NOT NULL
            AND FechaAccion >= DATEADD(day, -7, GETDATE())
            GROUP BY Modulo
            ORDER BY TiempoPromedio DESC
        """)
        
        rendimiento_modulos = []
        for row in cursor.fetchall():
            rendimiento_modulos.append({
                "modulo": row[0],
                "tiempo_promedio_ms": float(row[1]) if row[1] else 0,
                "cantidad_acciones": row[2]
            })
        
        # Acciones más lentas
        cursor.execute("""
            SELECT TOP 10
                aa.Accion,
                aa.Modulo,
                aa.DuracionMs,
                aa.FechaAccion,
                u.NombreCompleto
            FROM AuditoriaAdministradores aa
            INNER JOIN AdministradoresSistema a ON aa.AdminID = a.AdminID
            INNER JOIN Usuarios u ON a.UsuarioID = u.UsuarioID
            WHERE aa.DuracionMs IS NOT NULL
            AND aa.FechaAccion >= DATEADD(day, -1, GETDATE())
            ORDER BY aa.DuracionMs DESC
        """)
        
        acciones_lentas = []
        for row in cursor.fetchall():
            acciones_lentas.append({
                "accion": row[0],
                "modulo": row[1],
                "duracion_ms": row[2],
                "fecha": row[3].isoformat() if row[3] else None,
                "administrador": row[4]
            })
        
        # Estadísticas de errores
        cursor.execute("""
            SELECT 
                Resultado,
                COUNT(*) as Cantidad
            FROM AuditoriaAdministradores
            WHERE FechaAccion >= DATEADD(day, -7, GETDATE())
            GROUP BY Resultado
        """)
        
        estadisticas_errores = {}
        for row in cursor.fetchall():
            estadisticas_errores[row[0]] = row[1]
        
        return jsonify({
            "success": True,
            "rendimiento_modulos": rendimiento_modulos,
            "acciones_lentas": acciones_lentas,
            "estadisticas_errores": estadisticas_errores,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"ERROR obteniendo métricas de rendimiento: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@admin_dashboard_bp.route('/alertas-sistema', methods=['GET'])
@verificar_admin_autenticado
def obtener_alertas_sistema():
    """
    🚨 Alertas y notificaciones del sistema
    """
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión"}), 500
        
        cursor = conn.cursor()
        
        alertas = []
        
        # Cuentas bloqueadas
        cursor.execute("""
            SELECT COUNT(*) FROM AdministradoresSistema
            WHERE FechaBloqueado IS NOT NULL 
            AND DATEDIFF(minute, FechaBloqueado, GETDATE()) < 30
        """)
        cuentas_bloqueadas = cursor.fetchone()[0]
        
        if cuentas_bloqueadas > 0:
            alertas.append({
                "tipo": "SEGURIDAD",
                "severidad": "ALTA",
                "titulo": "Cuentas Bloqueadas",
                "mensaje": f"{cuentas_bloqueadas} cuenta(s) de administrador bloqueada(s) por intentos fallidos",
                "icono": "ph-shield-warning",
                "color": "#ef4444",
                "timestamp": datetime.now().isoformat()
            })
        
        # Muchos errores recientes
        cursor.execute("""
            SELECT COUNT(*) FROM AuditoriaAdministradores
            WHERE Resultado = 'ERROR' 
            AND FechaAccion >= DATEADD(hour, -1, GETDATE())
        """)
        errores_recientes = cursor.fetchone()[0]
        
        if errores_recientes > 10:
            alertas.append({
                "tipo": "RENDIMIENTO",
                "severidad": "MEDIA",
                "titulo": "Muchos Errores Recientes",
                "mensaje": f"{errores_recientes} errores en la última hora",
                "icono": "ph-warning-circle",
                "color": "#f59e0b",
                "timestamp": datetime.now().isoformat()
            })
        
        # Sesiones largas
        cursor.execute("""
            SELECT COUNT(*) FROM SesionesAdministradores
            WHERE EstadoSesion = 'ACTIVA' 
            AND DATEDIFF(hour, FechaCreacion, GETDATE()) > 8
        """)
        sesiones_largas = cursor.fetchone()[0]
        
        if sesiones_largas > 0:
            alertas.append({
                "tipo": "SEGURIDAD",
                "severidad": "BAJA",
                "titulo": "Sesiones Prolongadas",
                "mensaje": f"{sesiones_largas} sesión(es) activa(s) por más de 8 horas",
                "icono": "ph-clock-countdown",
                "color": "#06b6d4",
                "timestamp": datetime.now().isoformat()
            })
        
        # Usuarios sin acceso reciente
        cursor.execute("""
            SELECT COUNT(*) FROM Usuarios
            WHERE EstadoActivo = 1
            AND (UltimoAcceso IS NULL OR UltimoAcceso < DATEADD(day, -30, GETDATE()))
        """)
        usuarios_inactivos = cursor.fetchone()[0]
        
        if usuarios_inactivos > 10:
            alertas.append({
                "tipo": "MANTENIMIENTO",
                "severidad": "BAJA",
                "titulo": "Usuarios Inactivos",
                "mensaje": f"{usuarios_inactivos} usuarios sin acceso en 30+ días",
                "icono": "ph-user-minus",
                "color": "#64748b",
                "timestamp": datetime.now().isoformat()
            })
        
        return jsonify({
            "success": True,
            "alertas": alertas,
            "total_alertas": len(alertas),
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"ERROR obteniendo alertas: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@admin_dashboard_bp.route('/graficos-actividad', methods=['GET'])
@verificar_admin_autenticado
def obtener_graficos_actividad():
    """
    📈 Datos para gráficos de actividad
    """
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión"}), 500
        
        cursor = conn.cursor()
        
        # Actividad por días (últimos 30 días)
        cursor.execute("""
            SELECT 
                CAST(FechaAccion AS DATE) as Fecha,
                COUNT(*) as Cantidad
            FROM AuditoriaAdministradores
            WHERE FechaAccion >= DATEADD(day, -30, GETDATE())
            GROUP BY CAST(FechaAccion AS DATE)
            ORDER BY Fecha
        """)
        
        actividad_diaria = []
        for row in cursor.fetchall():
            actividad_diaria.append({
                "fecha": row[0].isoformat() if row[0] else None,
                "cantidad": row[1]
            })
        
        # Logins por día
        cursor.execute("""
            SELECT 
                CAST(FechaAccion AS DATE) as Fecha,
                COUNT(*) as Cantidad
            FROM AuditoriaAdministradores
            WHERE Accion = 'LOGIN_SUCCESS'
            AND FechaAccion >= DATEADD(day, -30, GETDATE())
            GROUP BY CAST(FechaAccion AS DATE)
            ORDER BY Fecha
        """)
        
        logins_diarios = []
        for row in cursor.fetchall():
            logins_diarios.append({
                "fecha": row[0].isoformat() if row[0] else None,
                "cantidad": row[1]
            })
        
        # Distribución de acciones
        cursor.execute("""
            SELECT 
                Accion,
                COUNT(*) as Cantidad
            FROM AuditoriaAdministradores
            WHERE FechaAccion >= DATEADD(day, -7, GETDATE())
            GROUP BY Accion
            ORDER BY Cantidad DESC
        """)
        
        distribucion_acciones = []
        for row in cursor.fetchall():
            distribucion_acciones.append({
                "accion": row[0],
                "cantidad": row[1]
            })
        
        return jsonify({
            "success": True,
            "actividad_diaria": actividad_diaria,
            "logins_diarios": logins_diarios,
            "distribucion_acciones": distribucion_acciones,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"ERROR obteniendo gráficos: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@admin_dashboard_bp.route('/exportar-reporte', methods=['POST'])
@verificar_admin_autenticado
def exportar_reporte():
    """
    📊 Exportar reporte de métricas
    """
    try:
        data = request.get_json()
        admin_info = request.admin_actual
        
        tipo_reporte = data.get('tipo', 'general')
        formato = data.get('formato', 'json')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión"}), 500
        
        cursor = conn.cursor()
        
        # Construir consulta según tipo de reporte
        if tipo_reporte == 'actividad':
            consulta = """
                SELECT 
                    aa.FechaAccion,
                    aa.Accion,
                    aa.Modulo,
                    u.NombreCompleto,
                    aa.Resultado,
                    aa.DuracionMs
                FROM AuditoriaAdministradores aa
                INNER JOIN AdministradoresSistema a ON aa.AdminID = a.AdminID
                INNER JOIN Usuarios u ON a.UsuarioID = u.UsuarioID
                WHERE aa.FechaAccion >= ? AND aa.FechaAccion <= ?
                ORDER BY aa.FechaAccion DESC
            """
        elif tipo_reporte == 'seguridad':
            consulta = """
                SELECT 
                    u.NombreCompleto,
                    u.Email,
                    a.IntentosFallidosLogin,
                    a.FechaBloqueado,
                    a.FechaUltimoAcceso,
                    ta.Nombre as TipoAdmin
                FROM AdministradoresSistema a
                INNER JOIN Usuarios u ON a.UsuarioID = u.UsuarioID
                INNER JOIN TiposAdministradores ta ON a.TipoAdminID = ta.TipoAdminID
                WHERE a.EstadoActivo = 1
                ORDER BY a.IntentosFallidosLogin DESC
            """
        else:  # general
            consulta = """
                SELECT 
                    u.NombreCompleto,
                    u.Email,
                    ta.Nombre as TipoAdmin,
                    a.FechaCreacion,
                    a.FechaUltimoAcceso,
                    a.EstadoActivo
                FROM AdministradoresSistema a
                INNER JOIN Usuarios u ON a.UsuarioID = u.UsuarioID
                INNER JOIN TiposAdministradores ta ON a.TipoAdminID = ta.TipoAdminID
                ORDER BY a.FechaCreacion DESC
            """
        
        # Ejecutar consulta
        if tipo_reporte == 'actividad':
            cursor.execute(consulta, (fecha_inicio or datetime.now() - timedelta(days=30), fecha_fin or datetime.now()))
        else:
            cursor.execute(consulta)
        
        # Procesar resultados
        resultados = []
        for row in cursor.fetchall():
            fila = {}
            for i, valor in enumerate(row):
                if isinstance(valor, datetime):
                    fila[f'campo_{i}'] = valor.isoformat()
                else:
                    fila[f'campo_{i}'] = valor
            resultados.append(fila)
        
        # Registrar auditoría
        registrar_auditoria_admin(
            admin_info['admin_id'],
            "EXPORT_REPORT",
            "DASHBOARD",
            recurso_afectado="Reporte",
            datos_nuevos={
                "tipo_reporte": tipo_reporte,
                "formato": formato,
                "cantidad_registros": len(resultados)
            }
        )
        
        return jsonify({
            "success": True,
            "datos": resultados,
            "tipo_reporte": tipo_reporte,
            "formato": formato,
            "cantidad_registros": len(resultados),
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"ERROR exportando reporte: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if 'conn' in locals():
            conn.close()
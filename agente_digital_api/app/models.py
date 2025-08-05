 
# app/models.py
from flask_login import UserMixin
from datetime import datetime
from typing import Optional, Dict, List
import json

class User(UserMixin):
    """Modelo de usuario básico con funcionalidades extendidas"""
    
    def __init__(self, id, email, nombre, rol, activo=True, **kwargs):
        self.id = id
        self.email = email
        self.nombre = nombre
        self.rol = rol
        self.activo = activo
        
        # Campos adicionales opcionales
        self.telefono = kwargs.get('telefono')
        self.ultimo_acceso = kwargs.get('ultimo_acceso')
        self.fecha_creacion = kwargs.get('fecha_creacion')
        self.avatar_url = kwargs.get('avatar_url')
        self.preferencias = kwargs.get('preferencias', {})
        self.intentos_fallidos = kwargs.get('intentos_fallidos', 0)
        self.bloqueado_hasta = kwargs.get('bloqueado_hasta')
        self.debe_cambiar_password = kwargs.get('debe_cambiar_password', False)
    
    def is_active(self):
        """Verifica si el usuario está activo"""
        return self.activo and not self.is_blocked()
    
    def is_blocked(self):
        """Verifica si el usuario está bloqueado"""
        if not self.bloqueado_hasta:
            return False
        return datetime.now() < self.bloqueado_hasta
    
    def to_dict(self):
        """Convierte el usuario a diccionario para JSON"""
        return {
            'id': self.id,
            'email': self.email,
            'nombre': self.nombre,
            'rol': self.rol,
            'activo': self.activo,
            'telefono': self.telefono,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'avatar_url': self.avatar_url,
            'preferencias': self.preferencias,
            'intentos_fallidos': self.intentos_fallidos,
            'bloqueado_hasta': self.bloqueado_hasta.isoformat() if self.bloqueado_hasta else None,
            'debe_cambiar_password': self.debe_cambiar_password
        }

class AdministradorSistema:
    """Modelo para administradores del sistema con permisos avanzados"""
    
    def __init__(self, admin_id, usuario_id, tipo_admin_id, tipo_codigo, nivel, **kwargs):
        self.admin_id = admin_id
        self.usuario_id = usuario_id
        self.tipo_admin_id = tipo_admin_id
        self.tipo_codigo = tipo_codigo
        self.nivel = nivel
        
        # Información adicional
        self.fecha_creacion = kwargs.get('fecha_creacion')
        self.creado_por = kwargs.get('creado_por')
        self.ultimo_acceso = kwargs.get('ultimo_acceso')
        self.intentos_fallidos = kwargs.get('intentos_fallidos', 0)
        self.fecha_bloqueado = kwargs.get('fecha_bloqueado')
        self.estado_activo = kwargs.get('estado_activo', True)
        
        # Información del usuario asociado
        self.usuario_info = kwargs.get('usuario_info', {})
        self.permisos = kwargs.get('permisos', [])
    
    def puede_administrar(self, otro_admin_nivel):
        """Verifica si puede administrar a otro administrador"""
        return self.nivel < otro_admin_nivel
    
    def tiene_permiso(self, permiso_codigo):
        """Verifica si tiene un permiso específico"""
        return any(p.get('codigo') == permiso_codigo for p in self.permisos)
    
    def to_dict(self):
        """Convierte el administrador a diccionario"""
        return {
            'admin_id': self.admin_id,
            'usuario_id': self.usuario_id,
            'tipo_admin_id': self.tipo_admin_id,
            'tipo_codigo': self.tipo_codigo,
            'nivel': self.nivel,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'creado_por': self.creado_por,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'intentos_fallidos': self.intentos_fallidos,
            'fecha_bloqueado': self.fecha_bloqueado.isoformat() if self.fecha_bloqueado else None,
            'estado_activo': self.estado_activo,
            'usuario_info': self.usuario_info,
            'permisos': self.permisos
        }

class SesionAdministrador:
    """Modelo para sesiones de administradores"""
    
    def __init__(self, sesion_id, admin_id, token, **kwargs):
        self.sesion_id = sesion_id
        self.admin_id = admin_id
        self.token = token
        
        # Información de la sesión
        self.ip_address = kwargs.get('ip_address')
        self.user_agent = kwargs.get('user_agent')
        self.fecha_creacion = kwargs.get('fecha_creacion')
        self.fecha_expiracion = kwargs.get('fecha_expiracion')
        self.fecha_ultima_actividad = kwargs.get('fecha_ultima_actividad')
        self.estado_sesion = kwargs.get('estado_sesion', 'ACTIVA')
        
        # Información del dispositivo
        self.dispositivo = kwargs.get('dispositivo')
        self.navegador = kwargs.get('navegador')
        self.sistema_operativo = kwargs.get('sistema_operativo')
        self.ubicacion = kwargs.get('ubicacion')
    
    def is_active(self):
        """Verifica si la sesión está activa"""
        return (
            self.estado_sesion == 'ACTIVA' and
            self.fecha_expiracion and
            datetime.now() < self.fecha_expiracion
        )
    
    def to_dict(self):
        """Convierte la sesión a diccionario"""
        return {
            'sesion_id': self.sesion_id,
            'admin_id': self.admin_id,
            'token': self.token[:8] + '...' if self.token else None,  # Solo mostrar parte del token
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_expiracion': self.fecha_expiracion.isoformat() if self.fecha_expiracion else None,
            'fecha_ultima_actividad': self.fecha_ultima_actividad.isoformat() if self.fecha_ultima_actividad else None,
            'estado_sesion': self.estado_sesion,
            'dispositivo': self.dispositivo,
            'navegador': self.navegador,
            'sistema_operativo': self.sistema_operativo,
            'ubicacion': self.ubicacion
        }

class PermisoSistema:
    """Modelo para permisos del sistema"""
    
    def __init__(self, permiso_id, codigo, nombre, modulo, accion, **kwargs):
        self.permiso_id = permiso_id
        self.codigo = codigo
        self.nombre = nombre
        self.modulo = modulo
        self.accion = accion
        
        # Información adicional
        self.descripcion = kwargs.get('descripcion')
        self.recursos = kwargs.get('recursos', [])
        self.activo = kwargs.get('activo', True)
        self.nivel_minimo = kwargs.get('nivel_minimo', 1)
    
    def to_dict(self):
        """Convierte el permiso a diccionario"""
        return {
            'permiso_id': self.permiso_id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'modulo': self.modulo,
            'accion': self.accion,
            'descripcion': self.descripcion,
            'recursos': self.recursos,
            'activo': self.activo,
            'nivel_minimo': self.nivel_minimo
        }

class AuditoriaAdministrador:
    """Modelo para auditoría de acciones de administradores"""
    
    def __init__(self, auditoria_id, admin_id, accion, modulo, **kwargs):
        self.auditoria_id = auditoria_id
        self.admin_id = admin_id
        self.accion = accion
        self.modulo = modulo
        
        # Información de la acción
        self.recurso_afectado = kwargs.get('recurso_afectado')
        self.recurso_id = kwargs.get('recurso_id')
        self.datos_anteriores = kwargs.get('datos_anteriores')
        self.datos_nuevos = kwargs.get('datos_nuevos')
        self.resultado = kwargs.get('resultado', 'EXITOSO')
        self.mensaje_error = kwargs.get('mensaje_error')
        
        # Información del contexto
        self.ip_address = kwargs.get('ip_address')
        self.user_agent = kwargs.get('user_agent')
        self.fecha_accion = kwargs.get('fecha_accion', datetime.now())
        self.duracion_ms = kwargs.get('duracion_ms')
    
    def to_dict(self):
        """Convierte la auditoría a diccionario"""
        return {
            'auditoria_id': self.auditoria_id,
            'admin_id': self.admin_id,
            'accion': self.accion,
            'modulo': self.modulo,
            'recurso_afectado': self.recurso_afectado,
            'recurso_id': self.recurso_id,
            'datos_anteriores': json.loads(self.datos_anteriores) if self.datos_anteriores else None,
            'datos_nuevos': json.loads(self.datos_nuevos) if self.datos_nuevos else None,
            'resultado': self.resultado,
            'mensaje_error': self.mensaje_error,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'fecha_accion': self.fecha_accion.isoformat() if self.fecha_accion else None,
            'duracion_ms': self.duracion_ms
        }
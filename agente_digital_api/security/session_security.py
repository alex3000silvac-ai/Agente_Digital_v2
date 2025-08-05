"""
session_security.py - Seguridad de sesiones y autenticación
========================================================

Este módulo implementa seguridad robusta para sesiones de usuario,
incluyendo prevención de session hijacking, fixation y gestión segura.

Características:
- Sesiones seguras con rotación de IDs
- Prevención de session hijacking
- Detección de anomalías en sesiones
- Timeout automático de sesiones
- Gestión de sesiones concurrentes
- Fingerprinting de dispositivos
"""

import os
import hmac
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from flask import session, request, g, current_app
import redis
import jwt

class SessionSecurity:
    """
    Sistema de gestión segura de sesiones
    """
    
    def __init__(self, app=None, redis_client=None):
        self.app = app
        self.redis_client = redis_client
        self.config = {
            'ENABLE_SESSION_SECURITY': os.getenv('ENABLE_SESSION_SECURITY', 'true').lower() == 'true',
            'SESSION_LIFETIME': int(os.getenv('SESSION_LIFETIME', 3600)),  # 1 hora
            'IDLE_TIMEOUT': int(os.getenv('SESSION_IDLE_TIMEOUT', 1800)),  # 30 minutos
            'REGENERATE_ID_INTERVAL': int(os.getenv('SESSION_REGENERATE_INTERVAL', 900)),  # 15 minutos
            'MAX_CONCURRENT_SESSIONS': int(os.getenv('MAX_CONCURRENT_SESSIONS', 3)),
            'FINGERPRINT_COMPONENTS': ['user-agent', 'accept-language', 'accept-encoding'],
            'BIND_SESSION_TO_IP': os.getenv('BIND_SESSION_TO_IP', 'false').lower() == 'true',
            'USE_REDIS': os.getenv('USE_REDIS_SESSIONS', 'false').lower() == 'true',
            'REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
            'SECURE_COOKIE': os.getenv('SESSION_SECURE_COOKIE', 'true').lower() == 'true',
            'HTTPONLY_COOKIE': True,
            'SAMESITE_COOKIE': 'Lax'
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa la seguridad de sesiones con la aplicación"""
        self.app = app
        
        # Configurar sesiones seguras
        app.config.update(
            SESSION_COOKIE_SECURE=self.config['SECURE_COOKIE'],
            SESSION_COOKIE_HTTPONLY=self.config['HTTPONLY_COOKIE'],
            SESSION_COOKIE_SAMESITE=self.config['SAMESITE_COOKIE'],
            PERMANENT_SESSION_LIFETIME=timedelta(seconds=self.config['SESSION_LIFETIME'])
        )
        
        # Inicializar Redis si está configurado
        if self.config['USE_REDIS'] and not self.redis_client:
            try:
                self.redis_client = redis.from_url(self.config['REDIS_URL'])
                self.redis_client.ping()
            except Exception as e:
                app.logger.warning(f"Redis no disponible para sesiones: {e}")
                self.config['USE_REDIS'] = False
        
        # Registrar handlers
        app.before_request(self._before_request)
        app.after_request(self._after_request)
    
    def _before_request(self):
        """Validaciones de seguridad antes de cada request"""
        if not self.config['ENABLE_SESSION_SECURITY']:
            return
        
        # Si hay una sesión activa
        if 'user_id' in session:
            # Validar sesión
            if not self._validate_session():
                self._destroy_session()
                return
            
            # Actualizar última actividad
            self._update_session_activity()
            
            # Verificar si necesita regeneración de ID
            if self._should_regenerate_id():
                self._regenerate_session_id()
    
    def _after_request(self, response):
        """Acciones después de cada request"""
        if not self.config['ENABLE_SESSION_SECURITY']:
            return response
        
        # Actualizar headers de seguridad para cookies
        if 'Set-Cookie' in response.headers:
            # Asegurar flags de seguridad
            cookie_header = response.headers['Set-Cookie']
            if 'Secure' not in cookie_header and self.config['SECURE_COOKIE']:
                cookie_header += '; Secure'
            if 'HttpOnly' not in cookie_header:
                cookie_header += '; HttpOnly'
            if 'SameSite' not in cookie_header:
                cookie_header += f'; SameSite={self.config["SAMESITE_COOKIE"]}'
            response.headers['Set-Cookie'] = cookie_header
        
        return response
    
    def create_session(self, user_id: Any, user_data: Dict[str, Any] = None) -> str:
        """
        Crea una nueva sesión segura
        
        Args:
            user_id: ID del usuario
            user_data: Datos adicionales del usuario
            
        Returns:
            str: ID de sesión
        """
        # Limpiar sesión existente
        session.clear()
        
        # Generar ID de sesión único
        session_id = secrets.token_urlsafe(32)
        
        # Crear fingerprint del dispositivo
        fingerprint = self._generate_device_fingerprint()
        
        # Datos de sesión
        session_data = {
            'user_id': user_id,
            'session_id': session_id,
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat(),
            'last_regeneration': datetime.utcnow().isoformat(),
            'fingerprint': fingerprint,
            'ip_address': request.remote_addr if self.config['BIND_SESSION_TO_IP'] else None,
            'user_agent': request.headers.get('User-Agent', 'unknown')
        }
        
        # Agregar datos adicionales del usuario
        if user_data:
            session_data.update(user_data)
        
        # Almacenar en Flask session
        for key, value in session_data.items():
            session[key] = value
        
        # Marcar sesión como permanente
        session.permanent = True
        
        # Si usa Redis, almacenar también ahí
        if self.config['USE_REDIS']:
            self._store_session_redis(session_id, session_data)
        
        # Gestionar sesiones concurrentes
        self._manage_concurrent_sessions(user_id, session_id)
        
        # Log de creación de sesión
        self._log_session_event('session_created', {
            'user_id': user_id,
            'session_id': session_id
        })
        
        return session_id
    
    def _validate_session(self) -> bool:
        """Valida la sesión actual"""
        # Verificar timeout de inactividad
        last_activity = session.get('last_activity')
        if last_activity:
            last_activity_time = datetime.fromisoformat(last_activity)
            idle_time = (datetime.utcnow() - last_activity_time).total_seconds()
            
            if idle_time > self.config['IDLE_TIMEOUT']:
                self._log_session_event('session_timeout', {
                    'user_id': session.get('user_id'),
                    'idle_time': idle_time
                })
                return False
        
        # Verificar fingerprint del dispositivo
        current_fingerprint = self._generate_device_fingerprint()
        stored_fingerprint = session.get('fingerprint')
        
        if stored_fingerprint and current_fingerprint != stored_fingerprint:
            # Posible session hijacking
            self._log_session_event('fingerprint_mismatch', {
                'user_id': session.get('user_id'),
                'stored': stored_fingerprint,
                'current': current_fingerprint
            })
            return False
        
        # Verificar IP si está habilitado
        if self.config['BIND_SESSION_TO_IP']:
            stored_ip = session.get('ip_address')
            current_ip = request.remote_addr
            
            if stored_ip and current_ip != stored_ip:
                self._log_session_event('ip_mismatch', {
                    'user_id': session.get('user_id'),
                    'stored_ip': stored_ip,
                    'current_ip': current_ip
                })
                return False
        
        # Verificar en Redis si está habilitado
        if self.config['USE_REDIS']:
            session_id = session.get('session_id')
            if session_id and not self._validate_session_redis(session_id):
                return False
        
        return True
    
    def _generate_device_fingerprint(self) -> str:
        """Genera un fingerprint único del dispositivo"""
        components = []
        
        for component in self.config['FINGERPRINT_COMPONENTS']:
            if component == 'user-agent':
                components.append(request.headers.get('User-Agent', ''))
            elif component == 'accept-language':
                components.append(request.headers.get('Accept-Language', ''))
            elif component == 'accept-encoding':
                components.append(request.headers.get('Accept-Encoding', ''))
            elif component == 'accept':
                components.append(request.headers.get('Accept', ''))
        
        # Crear hash del fingerprint
        fingerprint_str = '|'.join(components)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()
    
    def _update_session_activity(self):
        """Actualiza la última actividad de la sesión"""
        session['last_activity'] = datetime.utcnow().isoformat()
        
        # Actualizar en Redis si está habilitado
        if self.config['USE_REDIS']:
            session_id = session.get('session_id')
            if session_id:
                self._update_session_redis(session_id, {
                    'last_activity': session['last_activity']
                })
    
    def _should_regenerate_id(self) -> bool:
        """Determina si se debe regenerar el ID de sesión"""
        last_regeneration = session.get('last_regeneration')
        if not last_regeneration:
            return True
        
        last_regeneration_time = datetime.fromisoformat(last_regeneration)
        time_since_regeneration = (datetime.utcnow() - last_regeneration_time).total_seconds()
        
        return time_since_regeneration > self.config['REGENERATE_ID_INTERVAL']
    
    def _regenerate_session_id(self):
        """Regenera el ID de sesión para prevenir session fixation"""
        old_session_id = session.get('session_id')
        new_session_id = secrets.token_urlsafe(32)
        
        # Actualizar ID de sesión
        session['session_id'] = new_session_id
        session['last_regeneration'] = datetime.utcnow().isoformat()
        
        # Si usa Redis, migrar datos
        if self.config['USE_REDIS'] and old_session_id:
            self._migrate_session_redis(old_session_id, new_session_id)
        
        # Log de regeneración
        self._log_session_event('session_regenerated', {
            'user_id': session.get('user_id'),
            'old_id': old_session_id,
            'new_id': new_session_id
        })
    
    def _manage_concurrent_sessions(self, user_id: Any, new_session_id: str):
        """Gestiona el límite de sesiones concurrentes por usuario"""
        if self.config['USE_REDIS']:
            # Obtener sesiones activas del usuario
            user_sessions_key = f"user_sessions:{user_id}"
            active_sessions = self.redis_client.smembers(user_sessions_key)
            
            # Si excede el límite, eliminar las más antiguas
            if len(active_sessions) >= self.config['MAX_CONCURRENT_SESSIONS']:
                # Obtener timestamps de cada sesión
                session_times = []
                for sess_id in active_sessions:
                    sess_data = self.redis_client.hget(f"session:{sess_id}", 'created_at')
                    if sess_data:
                        session_times.append((sess_id, sess_data))
                
                # Ordenar por antigüedad y eliminar las más viejas
                session_times.sort(key=lambda x: x[1])
                sessions_to_remove = len(active_sessions) - self.config['MAX_CONCURRENT_SESSIONS'] + 1
                
                for i in range(sessions_to_remove):
                    old_session_id = session_times[i][0]
                    self._destroy_session_redis(old_session_id.decode())
                    self.redis_client.srem(user_sessions_key, old_session_id)
            
            # Agregar nueva sesión
            self.redis_client.sadd(user_sessions_key, new_session_id)
            self.redis_client.expire(user_sessions_key, self.config['SESSION_LIFETIME'])
    
    def destroy_session(self):
        """Destruye la sesión actual de forma segura"""
        session_id = session.get('session_id')
        user_id = session.get('user_id')
        
        # Limpiar Flask session
        session.clear()
        
        # Limpiar Redis si está habilitado
        if self.config['USE_REDIS'] and session_id:
            self._destroy_session_redis(session_id)
            
            if user_id:
                user_sessions_key = f"user_sessions:{user_id}"
                self.redis_client.srem(user_sessions_key, session_id)
        
        # Log de destrucción
        self._log_session_event('session_destroyed', {
            'user_id': user_id,
            'session_id': session_id
        })
    
    def _destroy_session(self):
        """Wrapper interno para destroy_session"""
        self.destroy_session()
    
    def get_active_sessions(self, user_id: Any) -> list:
        """Obtiene las sesiones activas de un usuario"""
        if not self.config['USE_REDIS']:
            return []
        
        user_sessions_key = f"user_sessions:{user_id}"
        session_ids = self.redis_client.smembers(user_sessions_key)
        
        sessions = []
        for session_id in session_ids:
            session_data = self._get_session_redis(session_id.decode())
            if session_data:
                sessions.append({
                    'session_id': session_id.decode(),
                    'created_at': session_data.get('created_at'),
                    'last_activity': session_data.get('last_activity'),
                    'user_agent': session_data.get('user_agent'),
                    'ip_address': session_data.get('ip_address')
                })
        
        return sessions
    
    def destroy_all_sessions(self, user_id: Any):
        """Destruye todas las sesiones de un usuario"""
        if not self.config['USE_REDIS']:
            return
        
        user_sessions_key = f"user_sessions:{user_id}"
        session_ids = self.redis_client.smembers(user_sessions_key)
        
        for session_id in session_ids:
            self._destroy_session_redis(session_id.decode())
        
        self.redis_client.delete(user_sessions_key)
        
        self._log_session_event('all_sessions_destroyed', {
            'user_id': user_id,
            'count': len(session_ids)
        })
    
    # Métodos de Redis
    def _store_session_redis(self, session_id: str, session_data: dict):
        """Almacena sesión en Redis"""
        if not self.redis_client:
            return
        
        key = f"session:{session_id}"
        self.redis_client.hmset(key, {
            k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            for k, v in session_data.items()
        })
        self.redis_client.expire(key, self.config['SESSION_LIFETIME'])
    
    def _get_session_redis(self, session_id: str) -> Optional[dict]:
        """Obtiene sesión de Redis"""
        if not self.redis_client:
            return None
        
        key = f"session:{session_id}"
        data = self.redis_client.hgetall(key)
        
        if not data:
            return None
        
        # Decodificar datos
        session_data = {}
        for k, v in data.items():
            k = k.decode() if isinstance(k, bytes) else k
            v = v.decode() if isinstance(v, bytes) else v
            
            # Intentar decodificar JSON
            try:
                session_data[k] = json.loads(v)
            except:
                session_data[k] = v
        
        return session_data
    
    def _update_session_redis(self, session_id: str, updates: dict):
        """Actualiza sesión en Redis"""
        if not self.redis_client:
            return
        
        key = f"session:{session_id}"
        if self.redis_client.exists(key):
            self.redis_client.hmset(key, {
                k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for k, v in updates.items()
            })
            self.redis_client.expire(key, self.config['SESSION_LIFETIME'])
    
    def _validate_session_redis(self, session_id: str) -> bool:
        """Valida sesión en Redis"""
        if not self.redis_client:
            return True
        
        key = f"session:{session_id}"
        return self.redis_client.exists(key)
    
    def _migrate_session_redis(self, old_id: str, new_id: str):
        """Migra sesión a nuevo ID en Redis"""
        if not self.redis_client:
            return
        
        old_key = f"session:{old_id}"
        new_key = f"session:{new_id}"
        
        # Copiar datos
        data = self.redis_client.hgetall(old_key)
        if data:
            self.redis_client.hmset(new_key, data)
            self.redis_client.expire(new_key, self.config['SESSION_LIFETIME'])
            self.redis_client.delete(old_key)
    
    def _destroy_session_redis(self, session_id: str):
        """Destruye sesión en Redis"""
        if not self.redis_client:
            return
        
        key = f"session:{session_id}"
        self.redis_client.delete(key)
    
    def _log_session_event(self, event_type: str, details: dict):
        """Registra eventos de sesión"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'details': details,
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'unknown')
        }
        
        if current_app:
            current_app.logger.info(f"SESSION_EVENT: {json.dumps(event)}")


# Instancia global
session_security = SessionSecurity()
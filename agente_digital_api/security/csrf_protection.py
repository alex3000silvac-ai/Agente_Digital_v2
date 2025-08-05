"""
csrf_protection.py - Protección contra Cross-Site Request Forgery (CSRF)
====================================================================

Este módulo implementa protección completa contra ataques CSRF mediante
tokens únicos, validación de origen y políticas de seguridad.

Características:
- Generación de tokens CSRF únicos
- Validación de tokens en requests
- Verificación de headers Referer/Origin
- Double Submit Cookie pattern
- Integración con sesiones
- Exclusión de endpoints específicos
"""

import os
import hmac
import hashlib
import secrets
import time
from functools import wraps
from datetime import datetime, timedelta
from typing import Optional, List, Callable
from flask import request, session, g, abort, current_app

class CSRFProtection:
    """
    Sistema de protección contra CSRF
    """
    
    def __init__(self, app=None):
        self.app = app
        self.config = {
            'ENABLE_CSRF': os.getenv('ENABLE_CSRF_PROTECTION', 'true').lower() == 'true',
            'TOKEN_LENGTH': int(os.getenv('CSRF_TOKEN_LENGTH', 32)),
            'TOKEN_LIFETIME': int(os.getenv('CSRF_TOKEN_LIFETIME', 3600)),  # 1 hora
            'HEADER_NAME': os.getenv('CSRF_HEADER_NAME', 'X-CSRF-Token'),
            'FORM_FIELD': os.getenv('CSRF_FORM_FIELD', 'csrf_token'),
            'COOKIE_NAME': os.getenv('CSRF_COOKIE_NAME', 'csrf_token'),
            'CHECK_REFERER': os.getenv('CSRF_CHECK_REFERER', 'true').lower() == 'true',
            'SAME_SITE': os.getenv('CSRF_SAME_SITE', 'Strict'),
            'SECURE_COOKIE': os.getenv('CSRF_SECURE_COOKIE', 'true').lower() == 'true',
            'METHODS_TO_PROTECT': ['POST', 'PUT', 'PATCH', 'DELETE'],
            'EXCLUDE_PATHS': []
        }
        
        # Cache de tokens para validación rápida
        self.token_cache = {}
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa CSRF protection con la aplicación Flask"""
        self.app = app
        
        # Configurar secret key si no existe
        if not app.secret_key:
            app.secret_key = os.urandom(32)
        
        # Registrar before_request handler
        app.before_request(self._before_request)
        
        # Registrar funciones en Jinja2
        app.jinja_env.globals['csrf_token'] = self.generate_csrf_token
        app.jinja_env.globals['csrf_input'] = self.csrf_input_tag
    
    def _before_request(self):
        """Valida CSRF token antes de cada request"""
        if not self.config['ENABLE_CSRF']:
            return
        
        # Skip para métodos seguros
        if request.method not in self.config['METHODS_TO_PROTECT']:
            return
        
        # Skip para paths excluidos
        if self._is_excluded_path(request.path):
            return
        
        # Skip para requests AJAX con token en header
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Validar token del header
            token = request.headers.get(self.config['HEADER_NAME'])
            if token and self._validate_token(token):
                return
        
        # Validar CSRF token
        if not self._validate_csrf():
            self._log_csrf_failure()
            abort(403, 'CSRF validation failed')
    
    def generate_csrf_token(self, force_new: bool = False) -> str:
        """
        Genera un nuevo token CSRF
        
        Args:
            force_new: Forzar generación de nuevo token
            
        Returns:
            str: Token CSRF
        """
        # Verificar si ya existe un token válido en la sesión
        if not force_new and 'csrf_token' in session:
            token_data = session.get('csrf_token_data', {})
            if token_data.get('expires', 0) > time.time():
                return session['csrf_token']
        
        # Generar nuevo token
        token = secrets.token_urlsafe(self.config['TOKEN_LENGTH'])
        
        # Almacenar en sesión con timestamp
        session['csrf_token'] = token
        session['csrf_token_data'] = {
            'created': time.time(),
            'expires': time.time() + self.config['TOKEN_LIFETIME'],
            'ip': request.remote_addr
        }
        
        # Almacenar en g para acceso en la request actual
        g.csrf_token = token
        
        # Cache local para validación rápida
        self.token_cache[token] = {
            'expires': time.time() + self.config['TOKEN_LIFETIME'],
            'session_id': session.get('_id', 'unknown')
        }
        
        # Limpiar tokens expirados del cache
        self._cleanup_token_cache()
        
        return token
    
    def _validate_csrf(self) -> bool:
        """Valida el token CSRF de la request actual"""
        # Obtener token de la request
        token = None
        
        # Buscar en form data
        if request.form:
            token = request.form.get(self.config['FORM_FIELD'])
        
        # Buscar en JSON body
        if not token and request.is_json:
            data = request.get_json()
            if isinstance(data, dict):
                token = data.get(self.config['FORM_FIELD'])
        
        # Buscar en headers
        if not token:
            token = request.headers.get(self.config['HEADER_NAME'])
        
        # Buscar en cookies (double submit pattern)
        if not token:
            token = request.cookies.get(self.config['COOKIE_NAME'])
        
        if not token:
            return False
        
        # Validar token
        return self._validate_token(token)
    
    def _validate_token(self, token: str) -> bool:
        """
        Valida un token CSRF específico
        
        Args:
            token: Token a validar
            
        Returns:
            bool: True si es válido
        """
        # Verificar en cache primero
        if token in self.token_cache:
            cache_data = self.token_cache[token]
            if cache_data['expires'] > time.time():
                return True
            else:
                # Token expirado, eliminar del cache
                del self.token_cache[token]
        
        # Verificar en sesión
        session_token = session.get('csrf_token')
        if not session_token or session_token != token:
            return False
        
        # Verificar expiración
        token_data = session.get('csrf_token_data', {})
        if token_data.get('expires', 0) < time.time():
            return False
        
        # Verificar IP (opcional, puede causar problemas con proxies)
        # if token_data.get('ip') != request.remote_addr:
        #     return False
        
        # Validar referer/origin si está configurado
        if self.config['CHECK_REFERER']:
            if not self._validate_referer():
                return False
        
        return True
    
    def _validate_referer(self) -> bool:
        """Valida el header Referer/Origin"""
        # Obtener origen de la request
        origin = request.headers.get('Origin')
        referer = request.headers.get('Referer')
        
        # Si no hay ninguno, rechazar (puede ser muy estricto)
        if not origin and not referer:
            return False
        
        # Obtener host esperado
        expected_host = request.host
        
        # Validar origin
        if origin:
            origin_host = origin.replace('https://', '').replace('http://', '').split('/')[0]
            if origin_host != expected_host:
                return False
        
        # Validar referer
        if referer:
            referer_host = referer.replace('https://', '').replace('http://', '').split('/')[0]
            if referer_host != expected_host:
                return False
        
        return True
    
    def csrf_input_tag(self) -> str:
        """
        Genera un tag HTML input con el token CSRF
        
        Returns:
            str: Tag HTML <input>
        """
        token = self.generate_csrf_token()
        return f'<input type="hidden" name="{self.config["FORM_FIELD"]}" value="{token}">'
    
    def exempt(self, f: Callable) -> Callable:
        """
        Decorator para eximir un endpoint de protección CSRF
        
        Uso:
            @app.route('/api/webhook', methods=['POST'])
            @csrf.exempt
            def webhook():
                return 'OK'
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Marcar como exento
            g.csrf_exempt = True
            return f(*args, **kwargs)
        
        # Registrar path como excluido
        if hasattr(f, '__name__'):
            self.config['EXCLUDE_PATHS'].append(f.__name__)
        
        return decorated_function
    
    def protect(self, f: Callable) -> Callable:
        """
        Decorator para forzar protección CSRF en un endpoint
        
        Uso:
            @app.route('/api/sensitive', methods=['GET'])
            @csrf.protect
            def sensitive():
                return 'Protected'
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Forzar validación CSRF
            if not self._validate_csrf():
                abort(403, 'CSRF validation failed')
            return f(*args, **kwargs)
        
        return decorated_function
    
    def _is_excluded_path(self, path: str) -> bool:
        """Verifica si un path está excluido de protección CSRF"""
        # Verificar marca de exención
        if hasattr(g, 'csrf_exempt') and g.csrf_exempt:
            return True
        
        # Verificar paths configurados
        for excluded in self.config['EXCLUDE_PATHS']:
            if path.startswith(excluded):
                return True
        
        # Excluir automáticamente algunos paths comunes
        excluded_prefixes = ['/api/health', '/static/', '/favicon.ico']
        for prefix in excluded_prefixes:
            if path.startswith(prefix):
                return True
        
        return False
    
    def _cleanup_token_cache(self):
        """Limpia tokens expirados del cache"""
        current_time = time.time()
        expired_tokens = [
            token for token, data in self.token_cache.items()
            if data['expires'] < current_time
        ]
        
        for token in expired_tokens:
            del self.token_cache[token]
    
    def regenerate_token(self):
        """Regenera el token CSRF (útil después de login)"""
        return self.generate_csrf_token(force_new=True)
    
    def get_token(self) -> Optional[str]:
        """Obtiene el token CSRF actual"""
        if hasattr(g, 'csrf_token'):
            return g.csrf_token
        return session.get('csrf_token')
    
    def validate_token(self, token: str) -> bool:
        """
        Valida un token CSRF manualmente
        
        Args:
            token: Token a validar
            
        Returns:
            bool: True si es válido
        """
        return self._validate_token(token)
    
    def _log_csrf_failure(self):
        """Registra un fallo de validación CSRF"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'csrf_validation_failed',
            'method': request.method,
            'path': request.path,
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'referer': request.headers.get('Referer', 'none'),
            'origin': request.headers.get('Origin', 'none')
        }
        
        if current_app:
            current_app.logger.warning(f"CSRF_FAILURE: {event}")


# Clase helper para Double Submit Cookie Pattern
class DoubleSubmitCSRF:
    """
    Implementación alternativa usando Double Submit Cookie pattern
    (útil cuando no hay sesiones del lado del servidor)
    """
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def generate_token(self, user_id: str = None) -> tuple:
        """
        Genera un par de tokens (cookie token, header token)
        
        Returns:
            tuple: (cookie_token, header_token)
        """
        # Generar valor random
        random_value = secrets.token_urlsafe(32)
        
        # Crear timestamp
        timestamp = str(int(time.time()))
        
        # Crear payload
        payload = f"{random_value}:{timestamp}"
        if user_id:
            payload += f":{user_id}"
        
        # Crear firma HMAC
        signature = hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Token completo
        token = f"{payload}:{signature}"
        
        return token, random_value
    
    def validate_tokens(self, cookie_token: str, header_token: str,
                       max_age: int = 3600) -> bool:
        """
        Valida el par de tokens
        
        Args:
            cookie_token: Token de la cookie
            header_token: Token del header
            max_age: Edad máxima en segundos
            
        Returns:
            bool: True si son válidos
        """
        try:
            # Parsear cookie token
            parts = cookie_token.split(':')
            if len(parts) < 3:
                return False
            
            random_value = parts[0]
            timestamp = parts[1]
            signature = parts[-1]
            
            # Verificar que el header token coincida con el random value
            if header_token != random_value:
                return False
            
            # Verificar edad
            token_age = int(time.time()) - int(timestamp)
            if token_age > max_age:
                return False
            
            # Reconstruir payload
            payload = ':'.join(parts[:-1])
            
            # Verificar firma
            expected_signature = hmac.new(
                self.secret_key.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception:
            return False


# Instancia global
csrf = CSRFProtection()
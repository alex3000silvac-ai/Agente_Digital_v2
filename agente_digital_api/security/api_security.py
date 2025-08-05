"""
api_security.py - Seguridad específica para APIs
============================================

Este módulo implementa controles de seguridad específicos para APIs REST,
incluyendo autenticación, autorización y validación de requests.

Características:
- Autenticación JWT mejorada
- API Keys seguras
- Firma de requests
- Versionado de API
- Throttling por endpoint
- Validación de schemas
"""

import os
import jwt
import hmac
import hashlib
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
from flask import request, jsonify, g, current_app
import jsonschema

class APISecurityManager:
    """
    Gestor de seguridad para APIs REST
    """
    
    def __init__(self, app=None):
        self.app = app
        self.config = {
            'ENABLE_API_SECURITY': os.getenv('ENABLE_API_SECURITY', 'true').lower() == 'true',
            
            # JWT Configuration
            'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY', os.urandom(32).hex()),
            'JWT_ALGORITHM': os.getenv('JWT_ALGORITHM', 'HS256'),
            'JWT_ACCESS_TOKEN_EXPIRES': int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)),  # 1 hora
            'JWT_REFRESH_TOKEN_EXPIRES': int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000)),  # 30 días
            'JWT_BLACKLIST_ENABLED': os.getenv('JWT_BLACKLIST_ENABLED', 'true').lower() == 'true',
            
            # API Key Configuration
            'API_KEY_HEADER': os.getenv('API_KEY_HEADER', 'X-API-Key'),
            'API_SECRET_HEADER': os.getenv('API_SECRET_HEADER', 'X-API-Secret'),
            'REQUIRE_API_KEY': os.getenv('REQUIRE_API_KEY', 'false').lower() == 'true',
            
            # Request Signing
            'REQUIRE_REQUEST_SIGNING': os.getenv('REQUIRE_REQUEST_SIGNING', 'false').lower() == 'true',
            'SIGNATURE_HEADER': os.getenv('SIGNATURE_HEADER', 'X-Signature'),
            'TIMESTAMP_HEADER': os.getenv('TIMESTAMP_HEADER', 'X-Timestamp'),
            'MAX_TIMESTAMP_DIFF': int(os.getenv('MAX_TIMESTAMP_DIFF', 300)),  # 5 minutos
            
            # Versioning
            'API_VERSION_HEADER': os.getenv('API_VERSION_HEADER', 'X-API-Version'),
            'DEFAULT_API_VERSION': os.getenv('DEFAULT_API_VERSION', 'v1'),
            'SUPPORTED_VERSIONS': os.getenv('SUPPORTED_API_VERSIONS', 'v1').split(','),
            
            # Schema Validation
            'VALIDATE_REQUEST_SCHEMA': os.getenv('VALIDATE_REQUEST_SCHEMA', 'true').lower() == 'true',
            'VALIDATE_RESPONSE_SCHEMA': os.getenv('VALIDATE_RESPONSE_SCHEMA', 'false').lower() == 'true'
        }
        
        # Blacklist de tokens JWT
        self.token_blacklist = set()
        
        # Registry de API keys
        self.api_keys = {}
        
        # Schemas de validación
        self.request_schemas = {}
        self.response_schemas = {}
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa la seguridad de API con la aplicación"""
        self.app = app
        
        if not self.config['ENABLE_API_SECURITY']:
            return
        
        # Configurar error handlers
        self._register_error_handlers(app)
        
        # Cargar API keys desde configuración/DB
        self._load_api_keys()
    
    def _register_error_handlers(self, app):
        """Registra manejadores de error para JWT"""
        @app.errorhandler(401)
        def unauthorized(e):
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Authentication required'
            }), 401
        
        @app.errorhandler(403)
        def forbidden(e):
            return jsonify({
                'error': 'Forbidden',
                'message': 'Insufficient permissions'
            }), 403
    
    def generate_tokens(self, user_id: str, user_data: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Genera par de tokens JWT (access y refresh)
        
        Args:
            user_id: ID del usuario
            user_data: Datos adicionales del usuario
            
        Returns:
            Dict con access_token y refresh_token
        """
        now = datetime.utcnow()
        
        # Payload base
        base_payload = {
            'user_id': user_id,
            'iat': now,
            'jti': os.urandom(16).hex()  # JWT ID único
        }
        
        # Agregar datos adicionales si existen
        if user_data:
            base_payload.update(user_data)
        
        # Access token
        access_payload = base_payload.copy()
        access_payload['exp'] = now + timedelta(seconds=self.config['JWT_ACCESS_TOKEN_EXPIRES'])
        access_payload['type'] = 'access'
        
        access_token = jwt.encode(
            access_payload,
            self.config['JWT_SECRET_KEY'],
            algorithm=self.config['JWT_ALGORITHM']
        )
        
        # Refresh token
        refresh_payload = base_payload.copy()
        refresh_payload['exp'] = now + timedelta(seconds=self.config['JWT_REFRESH_TOKEN_EXPIRES'])
        refresh_payload['type'] = 'refresh'
        
        refresh_token = jwt.encode(
            refresh_payload,
            self.config['JWT_SECRET_KEY'],
            algorithm=self.config['JWT_ALGORITHM']
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': self.config['JWT_ACCESS_TOKEN_EXPIRES']
        }
    
    def decode_token(self, token: str, token_type: str = 'access') -> Optional[Dict[str, Any]]:
        """
        Decodifica y valida un token JWT
        
        Args:
            token: Token a decodificar
            token_type: Tipo esperado del token
            
        Returns:
            Payload del token si es válido
        """
        try:
            # Decodificar token
            payload = jwt.decode(
                token,
                self.config['JWT_SECRET_KEY'],
                algorithms=[self.config['JWT_ALGORITHM']]
            )
            
            # Verificar tipo de token
            if payload.get('type') != token_type:
                return None
            
            # Verificar blacklist
            if self.config['JWT_BLACKLIST_ENABLED']:
                if payload.get('jti') in self.token_blacklist:
                    return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def revoke_token(self, token: str):
        """Revoca un token agregándolo a la blacklist"""
        if not self.config['JWT_BLACKLIST_ENABLED']:
            return
        
        try:
            # Decodificar para obtener jti
            payload = jwt.decode(
                token,
                self.config['JWT_SECRET_KEY'],
                algorithms=[self.config['JWT_ALGORITHM']],
                options={"verify_exp": False}  # Permitir tokens expirados
            )
            
            jti = payload.get('jti')
            if jti:
                self.token_blacklist.add(jti)
                
                # TODO: En producción, almacenar en Redis/DB con TTL
                
        except:
            pass
    
    def jwt_required(self, f: Callable) -> Callable:
        """
        Decorador que requiere autenticación JWT válida
        
        Uso:
            @app.route('/api/protected')
            @api_security.jwt_required
            def protected_route():
                user_id = g.current_user_id
                ...
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Obtener token del header
            auth_header = request.headers.get('Authorization', '')
            
            if not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Invalid authorization header'}), 401
            
            token = auth_header[7:]  # Remover 'Bearer '
            
            # Validar token
            payload = self.decode_token(token)
            
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            # Establecer usuario actual
            g.current_user_id = payload.get('user_id')
            g.jwt_payload = payload
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def refresh_jwt_required(self, f: Callable) -> Callable:
        """Decorador que requiere refresh token válido"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Obtener token
            data = request.get_json()
            refresh_token = data.get('refresh_token')
            
            if not refresh_token:
                return jsonify({'error': 'Refresh token required'}), 400
            
            # Validar refresh token
            payload = self.decode_token(refresh_token, token_type='refresh')
            
            if not payload:
                return jsonify({'error': 'Invalid refresh token'}), 401
            
            g.refresh_payload = payload
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def api_key_required(self, f: Callable) -> Callable:
        """
        Decorador que requiere API key válida
        
        Uso:
            @app.route('/api/webhook')
            @api_security.api_key_required
            def webhook():
                client_id = g.api_client_id
                ...
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Obtener API key y secret
            api_key = request.headers.get(self.config['API_KEY_HEADER'])
            api_secret = request.headers.get(self.config['API_SECRET_HEADER'])
            
            if not api_key or not api_secret:
                return jsonify({'error': 'API credentials required'}), 401
            
            # Validar credenciales
            if not self._validate_api_credentials(api_key, api_secret):
                return jsonify({'error': 'Invalid API credentials'}), 401
            
            # Establecer cliente
            g.api_client_id = self.api_keys[api_key]['client_id']
            g.api_client_data = self.api_keys[api_key]
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def require_signature(self, f: Callable) -> Callable:
        """
        Decorador que requiere firma válida en la request
        
        La firma se calcula como:
        HMAC-SHA256(secret, method + path + timestamp + body)
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Obtener headers necesarios
            signature = request.headers.get(self.config['SIGNATURE_HEADER'])
            timestamp = request.headers.get(self.config['TIMESTAMP_HEADER'])
            
            if not signature or not timestamp:
                return jsonify({'error': 'Request signature required'}), 401
            
            # Validar timestamp
            try:
                req_timestamp = int(timestamp)
                current_timestamp = int(time.time())
                
                if abs(current_timestamp - req_timestamp) > self.config['MAX_TIMESTAMP_DIFF']:
                    return jsonify({'error': 'Request timestamp too old'}), 401
                    
            except ValueError:
                return jsonify({'error': 'Invalid timestamp'}), 400
            
            # Obtener secret (desde JWT o API key)
            secret = self._get_signing_secret()
            if not secret:
                return jsonify({'error': 'No signing secret available'}), 401
            
            # Calcular firma esperada
            expected_signature = self._calculate_signature(
                secret,
                request.method,
                request.path,
                timestamp,
                request.get_data()
            )
            
            # Comparar firmas
            if not hmac.compare_digest(signature, expected_signature):
                return jsonify({'error': 'Invalid signature'}), 401
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def validate_request_schema(self, schema: Dict[str, Any]):
        """
        Decorador para validar schema del request body
        
        Uso:
            @app.route('/api/users', methods=['POST'])
            @api_security.validate_request_schema({
                "type": "object",
                "properties": {
                    "username": {"type": "string", "minLength": 3},
                    "email": {"type": "string", "format": "email"}
                },
                "required": ["username", "email"]
            })
            def create_user():
                ...
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not request.is_json:
                    return jsonify({'error': 'Content-Type must be application/json'}), 400
                
                try:
                    # Validar schema
                    jsonschema.validate(request.get_json(), schema)
                except jsonschema.ValidationError as e:
                    return jsonify({
                        'error': 'Invalid request data',
                        'details': str(e)
                    }), 422
                
                return f(*args, **kwargs)
            
            return decorated_function
        
        return decorator
    
    def require_api_version(self, *versions):
        """
        Decorador para requerir versión específica de API
        
        Uso:
            @app.route('/api/endpoint')
            @api_security.require_api_version('v2', 'v3')
            def new_endpoint():
                ...
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Obtener versión del header
                api_version = request.headers.get(
                    self.config['API_VERSION_HEADER'],
                    self.config['DEFAULT_API_VERSION']
                )
                
                # Verificar si es soportada
                if api_version not in versions:
                    return jsonify({
                        'error': 'API version not supported',
                        'supported_versions': list(versions),
                        'requested_version': api_version
                    }), 400
                
                g.api_version = api_version
                
                return f(*args, **kwargs)
            
            return decorated_function
        
        return decorator
    
    def _validate_api_credentials(self, api_key: str, api_secret: str) -> bool:
        """Valida credenciales de API"""
        if api_key not in self.api_keys:
            return False
        
        stored_data = self.api_keys[api_key]
        
        # Verificar secret
        if not hmac.compare_digest(stored_data['secret'], api_secret):
            return False
        
        # Verificar si está activa
        if not stored_data.get('active', True):
            return False
        
        # Verificar expiración si existe
        if 'expires_at' in stored_data:
            if datetime.utcnow() > datetime.fromisoformat(stored_data['expires_at']):
                return False
        
        return True
    
    def _get_signing_secret(self) -> Optional[str]:
        """Obtiene el secret para firmar requests"""
        # Si hay JWT, usar el user_id como base
        if hasattr(g, 'jwt_payload'):
            return hmac.new(
                self.config['JWT_SECRET_KEY'].encode(),
                str(g.jwt_payload['user_id']).encode(),
                hashlib.sha256
            ).hexdigest()
        
        # Si hay API key, usar el secret
        if hasattr(g, 'api_client_data'):
            return g.api_client_data['secret']
        
        return None
    
    def _calculate_signature(self, secret: str, method: str, path: str,
                           timestamp: str, body: bytes) -> str:
        """Calcula la firma HMAC de una request"""
        # Construir mensaje a firmar
        message = f"{method.upper()}{path}{timestamp}".encode()
        
        # Agregar body si existe
        if body:
            message += body
        
        # Calcular HMAC
        return hmac.new(
            secret.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
    
    def _load_api_keys(self):
        """Carga API keys desde configuración o base de datos"""
        # Por ahora, cargar desde variables de entorno
        # En producción, esto vendría de una base de datos
        
        # Ejemplo de API key
        demo_key = os.getenv('DEMO_API_KEY')
        demo_secret = os.getenv('DEMO_API_SECRET')
        
        if demo_key and demo_secret:
            self.api_keys[demo_key] = {
                'client_id': 'demo_client',
                'secret': demo_secret,
                'active': True,
                'created_at': datetime.utcnow().isoformat(),
                'permissions': ['read', 'write']
            }
    
    def create_api_key(self, client_id: str, permissions: List[str] = None) -> Dict[str, str]:
        """
        Crea un nuevo par de API key/secret
        
        Args:
            client_id: ID del cliente
            permissions: Lista de permisos
            
        Returns:
            Dict con api_key y api_secret
        """
        # Generar key y secret
        api_key = f"ak_{os.urandom(24).hex()}"
        api_secret = f"as_{os.urandom(32).hex()}"
        
        # Almacenar
        self.api_keys[api_key] = {
            'client_id': client_id,
            'secret': api_secret,
            'active': True,
            'created_at': datetime.utcnow().isoformat(),
            'permissions': permissions or ['read']
        }
        
        # TODO: En producción, almacenar en base de datos
        
        return {
            'api_key': api_key,
            'api_secret': api_secret,
            'client_id': client_id
        }
    
    def revoke_api_key(self, api_key: str):
        """Revoca una API key"""
        if api_key in self.api_keys:
            self.api_keys[api_key]['active'] = False
            self.api_keys[api_key]['revoked_at'] = datetime.utcnow().isoformat()


# Instancia global
api_security = APISecurityManager()


# Funciones helper para uso directo
def create_jwt_tokens(user_id: str, **kwargs):
    """Helper para crear tokens JWT"""
    return api_security.generate_tokens(user_id, kwargs)

def validate_jwt(token: str):
    """Helper para validar JWT"""
    return api_security.decode_token(token)

def require_auth(auth_type: str = 'jwt'):
    """
    Decorador flexible para requerir autenticación
    
    Uso:
        @app.route('/api/endpoint')
        @require_auth('jwt')  # o 'api_key' o 'any'
        def endpoint():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if auth_type == 'jwt':
                return api_security.jwt_required(f)(*args, **kwargs)
            elif auth_type == 'api_key':
                return api_security.api_key_required(f)(*args, **kwargs)
            elif auth_type == 'any':
                # Intentar JWT primero, luego API key
                auth_header = request.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    return api_security.jwt_required(f)(*args, **kwargs)
                else:
                    return api_security.api_key_required(f)(*args, **kwargs)
            else:
                return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator
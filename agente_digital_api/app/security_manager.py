# app/security_manager.py
# Gestor centralizado de seguridad para Agente Digital

import os
import logging
from flask import Flask, request, g, jsonify
from typing import Optional, Dict, Any
from functools import wraps

# Importar módulos de seguridad
from .encryption import init_encryption, get_encryption_manager
from .mfa import init_mfa_system, get_mfa_system
from .security_audit import init_audit_system, get_audit_manager, AuditEventType, AuditSeverity
from .password_policy import init_password_system, get_password_manager, get_lockout_manager, PasswordPolicy
from .security_validators import InputSanitizer, SecurityValidationError

logger = logging.getLogger(__name__)

class SecurityManager:
    """Gestor centralizado de seguridad"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.initialized = False
        self.components = {}
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Inicializar gestor de seguridad con la aplicación Flask"""
        self.app = app
        
        try:
            # Configurar logging de seguridad
            self._setup_security_logging()
            
            # Inicializar componentes de seguridad
            self._init_encryption()
            self._init_password_system()
            self._init_mfa_system()
            self._init_audit_system()
            self._init_input_validation()
            
            # Registrar middleware de seguridad
            self._register_security_middleware()
            
            # Registrar endpoints de seguridad
            self._register_security_endpoints()
            
            self.initialized = True
            logger.info("Security manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize security manager: {e}")
            raise
    
    def _setup_security_logging(self):
        """Configurar logging específico de seguridad"""
        security_logger = logging.getLogger('security')
        
        if not security_logger.handlers:
            # Handler para archivo de seguridad
            security_log_file = self.app.config.get('SECURITY_LOG_FILE', '/home/agentedigital/logs/security.log')
            
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(security_log_file), exist_ok=True)
            
            handler = logging.handlers.RotatingFileHandler(
                security_log_file,
                maxBytes=50*1024*1024,  # 50MB
                backupCount=10
            )
            
            formatter = logging.Formatter(
                '%(asctime)s|%(levelname)s|SECURITY|%(name)s|%(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            
            security_logger.addHandler(handler)
            security_logger.setLevel(logging.INFO)
    
    def _init_encryption(self):
        """Inicializar sistema de encriptación"""
        if self.app.config.get('ENCRYPTION_ENABLED', True):
            encryption_key = os.environ.get('ENCRYPTION_KEY')
            if encryption_key:
                if init_encryption(encryption_key):
                    self.components['encryption'] = get_encryption_manager()
                    logger.info("Encryption system initialized")
                else:
                    logger.error("Failed to initialize encryption system")
            else:
                logger.warning("ENCRYPTION_KEY not found, encryption disabled")
    
    def _init_password_system(self):
        """Inicializar sistema de contraseñas"""
        if self.app.config.get('PASSWORD_POLICY_ENABLED', True):
            # Configurar política de contraseñas
            policy = PasswordPolicy(
                min_length=self.app.config.get('PASSWORD_MIN_LENGTH', 12),
                password_expiry_days=self.app.config.get('PASSWORD_EXPIRY_DAYS', 90),
                password_history_count=self.app.config.get('PASSWORD_HISTORY_COUNT', 5),
                account_lockout_attempts=self.app.config.get('ACCOUNT_LOCKOUT_ATTEMPTS', 5),
                account_lockout_duration=self.app.config.get('ACCOUNT_LOCKOUT_DURATION', 30)
            )
            
            if init_password_system(policy):
                self.components['password_manager'] = get_password_manager()
                self.components['lockout_manager'] = get_lockout_manager()
                logger.info("Password system initialized")
            else:
                logger.error("Failed to initialize password system")
    
    def _init_mfa_system(self):
        """Inicializar sistema MFA"""
        if self.app.config.get('MFA_ENABLED', True):
            if init_mfa_system():
                self.components['mfa_system'] = get_mfa_system()
                logger.info("MFA system initialized")
            else:
                logger.error("Failed to initialize MFA system")
    
    def _init_audit_system(self):
        """Inicializar sistema de auditoría"""
        if self.app.config.get('AUDIT_LOG_ENABLED', True):
            if init_audit_system():
                self.components['audit_manager'] = get_audit_manager()
                logger.info("Audit system initialized")
            else:
                logger.error("Failed to initialize audit system")
    
    def _init_input_validation(self):
        """Inicializar validación de entrada"""
        if self.app.config.get('INPUT_VALIDATION_ENABLED', True):
            self.components['input_sanitizer'] = InputSanitizer()
            logger.info("Input validation initialized")
    
    def _register_security_middleware(self):
        """Registrar middleware de seguridad"""
        
        @self.app.before_request
        def security_before_request():
            """Middleware ejecutado antes de cada request"""
            
            # Generar ID único para el request
            import uuid
            g.request_id = str(uuid.uuid4())
            
            # Verificar headers de seguridad básicos
            self._check_security_headers()
            
            # Verificar rate limiting (ya manejado por rate_limiter.py)
            
            # Log de request para auditoría
            if 'audit_manager' in self.components:
                self._log_request_audit()
        
        @self.app.after_request
        def security_after_request(response):
            """Middleware ejecutado después de cada request"""
            
            # Agregar headers de seguridad
            self._add_security_headers(response)
            
            return response
        
        @self.app.errorhandler(SecurityValidationError)
        def handle_security_validation_error(error):
            """Manejar errores de validación de seguridad"""
            if 'audit_manager' in self.components:
                audit_manager = self.components['audit_manager']
                audit_manager.log_security_event(
                    AuditEventType.SECURITY_VIOLATION,
                    AuditSeverity.HIGH,
                    {'error': str(error), 'endpoint': request.endpoint}
                )
            
            return jsonify({
                'error': 'Security validation failed',
                'message': 'Invalid or potentially malicious input detected'
            }), 400
    
    def _check_security_headers(self):
        """Verificar headers de seguridad en requests"""
        # Verificar User-Agent
        user_agent = request.headers.get('User-Agent', '')
        if not user_agent or len(user_agent) < 10:
            logger.warning(f"Suspicious request without proper User-Agent: {request.remote_addr}")
        
        # Verificar Content-Type para requests POST/PUT
        if request.method in ['POST', 'PUT'] and request.content_length and request.content_length > 0:
            content_type = request.headers.get('Content-Type', '')
            if not content_type:
                logger.warning(f"Request without Content-Type: {request.method} {request.path}")
    
    def _add_security_headers(self, response):
        """Agregar headers de seguridad a la respuesta"""
        security_headers = self.app.config.get('SECURITY_HEADERS', {})
        
        # Headers predeterminados si no están configurados
        default_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'X-Request-ID': getattr(g, 'request_id', 'unknown')
        }
        
        # Aplicar headers de seguridad
        all_headers = {**default_headers, **security_headers}
        for header, value in all_headers.items():
            if header not in response.headers:
                response.headers[header] = value
        
        # HSTS solo en HTTPS
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    
    def _log_request_audit(self):
        """Registrar request para auditoría"""
        try:
            audit_manager = self.components['audit_manager']
            
            # Solo auditar ciertos endpoints
            audit_endpoints = ['/api/', '/auth/', '/admin/']
            should_audit = any(request.path.startswith(endpoint) for endpoint in audit_endpoints)
            
            if should_audit:
                details = {
                    'path': request.path,
                    'query_params': dict(request.args),
                    'content_length': request.content_length,
                    'content_type': request.content_type
                }
                
                # No incluir datos sensibles
                if request.method in ['POST', 'PUT'] and request.is_json:
                    try:
                        json_data = request.get_json()
                        if json_data:
                            # Sanitizar datos sensibles
                            sanitized_data = self._sanitize_request_data(json_data)
                            details['request_data'] = sanitized_data
                    except:
                        pass
                
                audit_manager.log_event(
                    event_type=AuditEventType.DATA_READ if request.method == 'GET' else AuditEventType.DATA_UPDATE,
                    severity=AuditSeverity.LOW,
                    action=f'http_{request.method.lower()}',
                    result='in_progress',
                    details=details,
                    resource_type='api_endpoint'
                )
        except Exception as e:
            logger.error(f"Error logging request audit: {e}")
    
    def _sanitize_request_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitizar datos de request para auditoría"""
        sensitive_fields = {'password', 'token', 'secret', 'key', 'auth', 'credential'}
        sanitized = {}
        
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_request_data(value)
            else:
                sanitized[key] = str(value)[:100]  # Truncar valores largos
        
        return sanitized
    
    def _register_security_endpoints(self):
        """Registrar endpoints específicos de seguridad"""
        
        @self.app.route('/security/status')
        def security_status():
            """Estado de componentes de seguridad"""
            try:
                status = {
                    'security_manager': {
                        'initialized': self.initialized,
                        'components': list(self.components.keys())
                    },
                    'components': {}
                }
                
                # Estado de cada componente
                for name, component in self.components.items():
                    try:
                        if hasattr(component, 'health_check'):
                            status['components'][name] = {
                                'status': 'healthy' if component.health_check() else 'unhealthy'
                            }
                        else:
                            status['components'][name] = {'status': 'active'}
                    except Exception as e:
                        status['components'][name] = {
                            'status': 'error',
                            'error': str(e)
                        }
                
                return jsonify(status)
                
            except Exception as e:
                return jsonify({
                    'error': 'Failed to get security status',
                    'message': str(e)
                }), 500
        
        @self.app.route('/security/audit/events')
        def audit_events():
            """Obtener eventos de auditoría recientes (solo admin)"""
            # Aquí implementar verificación de permisos de admin
            # Por ahora, endpoint básico
            return jsonify({
                'message': 'Audit events endpoint',
                'note': 'Admin authentication required'
            })
    
    def get_component(self, component_name: str):
        """Obtener componente específico de seguridad"""
        return self.components.get(component_name)
    
    def is_healthy(self) -> bool:
        """Verificar si todos los componentes de seguridad están saludables"""
        if not self.initialized:
            return False
        
        try:
            for name, component in self.components.items():
                if hasattr(component, 'health_check'):
                    if not component.health_check():
                        logger.warning(f"Security component {name} is unhealthy")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking security health: {e}")
            return False

# Instancia global del gestor de seguridad
_security_manager = None

def init_security(app: Flask):
    """Inicializar sistema de seguridad"""
    global _security_manager
    
    try:
        _security_manager = SecurityManager(app)
        logger.info("Security system initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize security system: {e}")
        return False

def get_security_manager() -> SecurityManager:
    """Obtener instancia del gestor de seguridad"""
    return _security_manager

# Decoradores de seguridad
def require_authentication(func):
    """Decorador para requerir autenticación"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Verificar token JWT o sesión
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        # Aquí implementar verificación de JWT
        # token = auth_header.split(' ')[1]
        # Verificar token...
        
        return func(*args, **kwargs)
    return wrapper

def require_admin(func):
    """Decorador para requerir permisos de administrador"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Verificar que el usuario sea admin
        if not hasattr(g, 'current_user') or not g.current_user:
            return jsonify({'error': 'Authentication required'}), 401
        
        user_role = g.current_user.get('role', '').lower()
        if user_role not in ['admin', 'administrator']:
            return jsonify({'error': 'Admin privileges required'}), 403
        
        return func(*args, **kwargs)
    return wrapper

def log_security_event(event_type: str, severity: str = 'medium'):
    """Decorador para registrar eventos de seguridad"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Registrar evento exitoso
                if _security_manager and 'audit_manager' in _security_manager.components:
                    audit_manager = _security_manager.components['audit_manager']
                    audit_manager.log_event(
                        event_type=getattr(AuditEventType, event_type.upper(), AuditEventType.SYSTEM_START),
                        severity=getattr(AuditSeverity, severity.upper(), AuditSeverity.MEDIUM),
                        action=func.__name__,
                        result='success',
                        details={'function': func.__name__}
                    )
                
                return result
                
            except Exception as e:
                # Registrar evento fallido
                if _security_manager and 'audit_manager' in _security_manager.components:
                    audit_manager = _security_manager.components['audit_manager']
                    audit_manager.log_event(
                        event_type=getattr(AuditEventType, event_type.upper(), AuditEventType.SYSTEM_START),
                        severity=AuditSeverity.HIGH,
                        action=func.__name__,
                        result='failed',
                        details={'function': func.__name__, 'error': str(e)}
                    )
                
                raise
                
        return wrapper
    return decorator
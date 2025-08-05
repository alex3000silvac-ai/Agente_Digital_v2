"""
Security Module - Sistema de seguridad completo para Flask
========================================================

Este módulo proporciona un sistema de seguridad integral para aplicaciones Flask,
incluyendo protección contra las principales vulnerabilidades web y controles
de seguridad empresariales.

Componentes principales:
- Rate Limiting y protección DDoS
- Validación y sanitización de inputs
- Protección contra SQL Injection
- Protección XSS y CSRF
- Gestión segura de sesiones
- Pool de conexiones seguro
- Headers de seguridad HTTP
- Manejo seguro de errores
- Sistema de auditoría
- Monitoreo de seguridad
- Seguridad para carga de archivos
- Seguridad específica para APIs
- Encriptación y hashing
- Configuración centralizada

Uso básico:
    from security import integrate_security
    
    app = Flask(__name__)
    integrate_security(app)

Uso avanzado:
    from security import SecurityIntegration, SecurityConfig
    
    config = SecurityConfig()
    security = SecurityIntegration(app)
"""

# Importar componentes principales
from .security_integration import SecurityIntegration, integrate_security
from .security_config import SecurityConfig
from .rate_limiter import rate_limiter, RateLimiter
from .input_validator import input_validator, InputValidator
from .sql_injection_guard import sql_guard, SQLInjectionGuard
from .xss_protection import xss_protection, XSSProtection
from .csrf_protection import csrf, CSRFProtection
from .session_security import session_security, SessionSecurity
from .connection_pool import db_pool, SecureConnectionPool, get_db_connection
from .encryption_utils import encryption_manager, EncryptionManager
from .audit_logger import audit_logger, AuditLogger, audit_action
from .error_handler import secure_error_handler, SecureErrorHandler, abort_secure
from .headers_security import security_headers, SecurityHeaders
from .file_upload_security import file_upload_security, FileUploadSecurity, secure_file_required
from .api_security import api_security, APISecurityManager, require_auth
from .monitoring import security_monitor, SecurityMonitor, monitor_endpoint

# Funciones de conveniencia
from .encryption_utils import (
    encrypt_sensitive_data,
    decrypt_sensitive_data,
    hash_user_password,
    verify_user_password
)

from .api_security import (
    create_jwt_tokens,
    validate_jwt
)

# Versión del módulo
__version__ = "1.0.0"

# Metadatos
__author__ = "Security Team"
__description__ = "Sistema de seguridad integral para Flask"

# Lista de componentes disponibles
AVAILABLE_COMPONENTS = [
    'SECURITY_MIDDLEWARE',
    'RATE_LIMITING', 
    'INPUT_VALIDATION',
    'SQL_INJECTION_GUARD',
    'XSS_PROTECTION',
    'CSRF_PROTECTION',
    'SESSION_SECURITY',
    'CONNECTION_POOL',
    'SECURITY_HEADERS',
    'SECURE_ERROR_HANDLING',
    'AUDIT_LOGGING',
    'SECURITY_MONITORING',
    'FILE_UPLOAD_SECURITY',
    'API_SECURITY',
    'ENCRYPTION'
]

# Configuración por defecto para importación rápida
DEFAULT_CONFIG = {
    'SECURITY_ENABLED': True,
    'COMPONENTS': {component: True for component in AVAILABLE_COMPONENTS}
}


def quick_setup(app, environment='production'):
    """
    Configuración rápida para casos comunes
    
    Args:
        app: Aplicación Flask
        environment: Entorno (development, staging, production)
    
    Returns:
        SecurityIntegration: Instancia del sistema de seguridad
    """
    import os
    os.environ['FLASK_ENV'] = environment
    
    return integrate_security(app)


def get_security_status():
    """
    Obtiene el estado actual del sistema de seguridad
    
    Returns:
        dict: Estado de todos los componentes
    """
    # Verificar si los componentes están inicializados
    components_status = {}
    
    components = {
        'rate_limiter': rate_limiter,
        'input_validator': input_validator,
        'sql_guard': sql_guard,
        'xss_protection': xss_protection,
        'csrf': csrf,
        'session_security': session_security,
        'db_pool': db_pool,
        'encryption_manager': encryption_manager,
        'audit_logger': audit_logger,
        'secure_error_handler': secure_error_handler,
        'security_headers': security_headers,
        'file_upload_security': file_upload_security,
        'api_security': api_security,
        'security_monitor': security_monitor
    }
    
    for name, component in components.items():
        components_status[name] = {
            'initialized': component is not None,
            'active': getattr(component, 'config', {}).get('ENABLED', False) if component else False
        }
    
    return {
        'version': __version__,
        'components': components_status,
        'total_components': len(AVAILABLE_COMPONENTS),
        'active_components': sum(1 for c in components_status.values() if c['active'])
    }


# Exportar todo lo necesario
__all__ = [
    # Classes principales
    'SecurityIntegration',
    'SecurityConfig',
    'RateLimiter',
    'InputValidator', 
    'SQLInjectionGuard',
    'XSSProtection',
    'CSRFProtection',
    'SessionSecurity',
    'SecureConnectionPool',
    'EncryptionManager',
    'AuditLogger',
    'SecureErrorHandler',
    'SecurityHeaders',
    'FileUploadSecurity',
    'APISecurityManager',
    'SecurityMonitor',
    
    # Instancias globales
    'rate_limiter',
    'input_validator',
    'sql_guard',
    'xss_protection',
    'csrf',
    'session_security',
    'db_pool',
    'encryption_manager',
    'audit_logger',
    'secure_error_handler',
    'security_headers',
    'file_upload_security',
    'api_security',
    'security_monitor',
    
    # Funciones de conveniencia
    'integrate_security',
    'get_db_connection',
    'encrypt_sensitive_data',
    'decrypt_sensitive_data',
    'hash_user_password',
    'verify_user_password',
    'create_jwt_tokens',
    'validate_jwt',
    'abort_secure',
    'quick_setup',
    'get_security_status',
    
    # Decoradores
    'audit_action',
    'secure_file_required',
    'require_auth',
    'monitor_endpoint',
    
    # Constantes
    'AVAILABLE_COMPONENTS',
    'DEFAULT_CONFIG'
]
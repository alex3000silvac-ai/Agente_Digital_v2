"""
security_integration.py - Integración completa del sistema de seguridad
===================================================================

Este módulo integra todos los componentes de seguridad en la aplicación Flask
sin modificar el código existente. Actúa como un plugin que se puede
activar/desactivar fácilmente.

Características:
- Integración automática de todos los módulos de seguridad
- Configuración centralizada
- Activación/desactivación por componente
- Compatibilidad total con código existente
- Monitoreo y métricas integradas
"""

import os
from flask import Flask, g, request
from typing import Optional

# Importar todos los módulos de seguridad
from .security_middleware import SecurityMiddleware
from .rate_limiter import rate_limiter
from .input_validator import input_validator
from .sql_injection_guard import sql_guard
from .xss_protection import xss_protection
from .csrf_protection import csrf
from .session_security import session_security
from .encryption_utils import encryption_manager
from .audit_logger import audit_logger
from .error_handler import secure_error_handler
from .headers_security import security_headers
from .file_upload_security import file_upload_security
from .api_security import api_security
from .connection_pool import db_pool
from .monitoring import security_monitor
from .security_config import SecurityConfig

class SecurityIntegration:
    """
    Clase principal que integra todos los componentes de seguridad
    """
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.config = SecurityConfig()
        self.components = {}
        
        # Estado de integración
        self.is_integrated = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        Inicializa la integración de seguridad con la aplicación Flask
        
        Args:
            app: Instancia de Flask
        """
        self.app = app
        
        # Verificar si ya está integrado
        if self.is_integrated:
            app.logger.warning("Security integration already initialized")
            return
        
        app.logger.info("🔒 Iniciando integración de seguridad...")
        
        try:
            # 1. Configurar aplicación
            self._configure_app(app)
            
            # 2. Inicializar connection pool
            if self.config.is_enabled('CONNECTION_POOL'):
                self._init_connection_pool(app)
            
            # 3. Inicializar middleware principal
            if self.config.is_enabled('SECURITY_MIDDLEWARE'):
                self._init_security_middleware(app)
            
            # 4. Inicializar rate limiting
            if self.config.is_enabled('RATE_LIMITING'):
                self._init_rate_limiting(app)
            
            # 5. Inicializar protección CSRF
            if self.config.is_enabled('CSRF_PROTECTION'):
                self._init_csrf_protection(app)
            
            # 6. Inicializar seguridad de sesiones
            if self.config.is_enabled('SESSION_SECURITY'):
                self._init_session_security(app)
            
            # 7. Inicializar headers de seguridad
            if self.config.is_enabled('SECURITY_HEADERS'):
                self._init_security_headers(app)
            
            # 8. Inicializar manejo de errores seguro
            if self.config.is_enabled('SECURE_ERROR_HANDLING'):
                self._init_error_handling(app)
            
            # 9. Inicializar auditoría
            if self.config.is_enabled('AUDIT_LOGGING'):
                self._init_audit_logging(app)
            
            # 10. Inicializar monitoreo
            if self.config.is_enabled('SECURITY_MONITORING'):
                self._init_monitoring(app)
            
            # 11. Registrar helpers en contexto
            self._register_context_processors(app)
            
            # 12. Registrar comandos CLI
            self._register_cli_commands(app)
            
            self.is_integrated = True
            app.logger.info("✅ Integración de seguridad completada")
            
            # Mostrar resumen
            self._show_security_summary(app)
            
        except Exception as e:
            app.logger.error(f"❌ Error en integración de seguridad: {e}")
            raise
    
    def _configure_app(self, app: Flask):
        """Configura la aplicación con settings de seguridad"""
        # Configuración básica de seguridad
        app.config.update(
            # Seguridad de cookies
            SESSION_COOKIE_SECURE=self.config.get('SESSION_COOKIE_SECURE', True),
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Lax',
            
            # Límites
            MAX_CONTENT_LENGTH=self.config.get('MAX_CONTENT_LENGTH', 10 * 1024 * 1024),
            
            # JSON
            JSON_SORT_KEYS=False,
            JSONIFY_PRETTYPRINT_REGULAR=False
        )
        
        # Asegurar secret key
        if not app.secret_key:
            app.secret_key = os.urandom(32)
    
    def _init_connection_pool(self, app: Flask):
        """Inicializa el pool de conexiones"""
        app.logger.info("Inicializando connection pool...")
        
        # El pool ya está creado como instancia global
        # Solo necesitamos registrar el helper
        @app.before_first_request
        def init_pool():
            stats = db_pool.get_pool_stats()
            app.logger.info(f"Connection pool inicializado: {stats}")
        
        self.components['connection_pool'] = db_pool
    
    def _init_security_middleware(self, app: Flask):
        """Inicializa el middleware de seguridad principal"""
        app.logger.info("Inicializando security middleware...")
        
        middleware = SecurityMiddleware(app)
        self.components['security_middleware'] = middleware
    
    def _init_rate_limiting(self, app: Flask):
        """Inicializa rate limiting"""
        app.logger.info("Inicializando rate limiting...")
        
        rate_limiter.init_app(app)
        self.components['rate_limiter'] = rate_limiter
        
        # Registrar decorator global
        app.jinja_env.globals['rate_limit'] = rate_limiter.limit
    
    def _init_csrf_protection(self, app: Flask):
        """Inicializa protección CSRF"""
        app.logger.info("Inicializando protección CSRF...")
        
        csrf.init_app(app)
        self.components['csrf'] = csrf
    
    def _init_session_security(self, app: Flask):
        """Inicializa seguridad de sesiones"""
        app.logger.info("Inicializando seguridad de sesiones...")
        
        session_security.init_app(app)
        self.components['session_security'] = session_security
    
    def _init_security_headers(self, app: Flask):
        """Inicializa headers de seguridad"""
        app.logger.info("Inicializando security headers...")
        
        security_headers.init_app(app)
        self.components['security_headers'] = security_headers
    
    def _init_error_handling(self, app: Flask):
        """Inicializa manejo seguro de errores"""
        app.logger.info("Inicializando error handling seguro...")
        
        secure_error_handler.init_app(app)
        self.components['error_handler'] = secure_error_handler
    
    def _init_audit_logging(self, app: Flask):
        """Inicializa sistema de auditoría"""
        app.logger.info("Inicializando audit logging...")
        
        audit_logger.init_app(app)
        self.components['audit_logger'] = audit_logger
    
    def _init_monitoring(self, app: Flask):
        """Inicializa monitoreo de seguridad"""
        app.logger.info("Inicializando security monitoring...")
        
        security_monitor.init_app(app)
        self.components['security_monitor'] = security_monitor
    
    def _register_context_processors(self, app: Flask):
        """Registra funciones helper en el contexto de templates"""
        
        @app.context_processor
        def security_context():
            return {
                'csrf_token': csrf.generate_csrf_token,
                'csrf_input': csrf.csrf_input_tag,
                'xss_escape': xss_protection.escape_html_attribute,
                'security_enabled': self.is_integrated
            }
    
    def _register_cli_commands(self, app: Flask):
        """Registra comandos CLI para gestión de seguridad"""
        
        @app.cli.command('security-status')
        def security_status():
            """Muestra el estado del sistema de seguridad"""
            print("\n🔒 ESTADO DEL SISTEMA DE SEGURIDAD")
            print("=" * 50)
            
            for name, component in self.components.items():
                status = "✅ Activo" if component else "❌ Inactivo"
                print(f"{name}: {status}")
            
            # Mostrar estadísticas
            if 'connection_pool' in self.components:
                stats = db_pool.get_pool_stats()
                print(f"\nConnection Pool:")
                print(f"  - Conexiones activas: {stats['active_connections']}")
                print(f"  - Tamaño del pool: {stats['pool_size']}")
            
            if 'rate_limiter' in self.components:
                load = rate_limiter.get_current_load()
                print(f"\nRate Limiter:")
                print(f"  - Requests/min: {load['requests_per_minute']}")
                print(f"  - IPs bloqueadas: {load['blacklisted_clients']}")
        
        @app.cli.command('security-test')
        def security_test():
            """Ejecuta tests de seguridad básicos"""
            from .attack_scenarios_test import run_security_tests
            run_security_tests(app)
    
    def _show_security_summary(self, app: Flask):
        """Muestra un resumen de la configuración de seguridad"""
        app.logger.info("\n" + "=" * 50)
        app.logger.info("🔒 RESUMEN DE SEGURIDAD")
        app.logger.info("=" * 50)
        
        # Componentes activos
        active_components = [name for name, comp in self.components.items() if comp]
        app.logger.info(f"Componentes activos: {len(active_components)}")
        for comp in active_components:
            app.logger.info(f"  ✓ {comp}")
        
        # Configuración crítica
        app.logger.info("\nConfiguración crítica:")
        app.logger.info(f"  - Max conexiones DB: {db_pool.config['MAX_CONNECTIONS']}")
        app.logger.info(f"  - Rate limit/min: {rate_limiter.config['REQUESTS_PER_MINUTE']}")
        app.logger.info(f"  - CSRF habilitado: {csrf.config['ENABLE_CSRF']}")
        app.logger.info(f"  - Secure cookies: {app.config.get('SESSION_COOKIE_SECURE')}")
        
        app.logger.info("=" * 50 + "\n")
    
    def get_component(self, name: str):
        """Obtiene un componente de seguridad específico"""
        return self.components.get(name)
    
    def disable_component(self, name: str):
        """Desactiva un componente de seguridad"""
        if name in self.components:
            self.components[name] = None
            self.app.logger.warning(f"Componente {name} desactivado")
    
    def get_security_stats(self):
        """Obtiene estadísticas consolidadas de seguridad"""
        stats = {
            'components_active': len([c for c in self.components.values() if c]),
            'total_components': len(self.components)
        }
        
        # Agregar stats específicas
        if 'connection_pool' in self.components and self.components['connection_pool']:
            stats['db_pool'] = db_pool.get_pool_stats()
        
        if 'rate_limiter' in self.components and self.components['rate_limiter']:
            stats['rate_limiter'] = rate_limiter.get_current_load()
        
        if 'security_monitor' in self.components and self.components['security_monitor']:
            stats['security_events'] = security_monitor.get_recent_events(10)
        
        return stats


# Función helper para integración fácil
def integrate_security(app: Flask, config: Optional[dict] = None):
    """
    Función helper para integrar seguridad en una aplicación Flask existente
    
    Uso:
        from security.security_integration import integrate_security
        
        app = Flask(__name__)
        integrate_security(app)
    
    Args:
        app: Instancia de Flask
        config: Configuración personalizada (opcional)
    """
    # Aplicar configuración personalizada si existe
    if config:
        for key, value in config.items():
            os.environ[key] = str(value)
    
    # Crear e inicializar integración
    security = SecurityIntegration(app)
    
    # Guardar referencia en la app
    app.security = security
    
    return security


# Decoradores de conveniencia para uso directo
def require_auth(f):
    """Decorator que requiere autenticación"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar autenticación
        if not hasattr(g, 'current_user_id') or not g.current_user_id:
            from flask import abort
            abort(401, 'Authentication required')
        return f(*args, **kwargs)
    
    return decorated_function


def validate_input(rules: dict):
    """Decorator para validar inputs automáticamente"""
    from functools import wraps
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Validar inputs
            validated_data = input_validator.validate_request(rules)
            
            # Agregar datos validados a kwargs
            kwargs['validated_data'] = validated_data
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def rate_limit(requests_per_minute: int = None):
    """Decorator para aplicar rate limiting"""
    return rate_limiter.limit(requests_per_minute=requests_per_minute)
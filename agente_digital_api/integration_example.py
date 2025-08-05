"""
integration_example.py - Ejemplo de integración del sistema de seguridad
=====================================================================

Este archivo muestra cómo integrar el sistema de seguridad completo
en una aplicación Flask existente.
"""

from flask import Flask, request, jsonify, session
import os

# Importar el sistema de seguridad
from security import integrate_security, SecurityConfig, quick_setup

def create_secure_app():
    """
    Crea una aplicación Flask con seguridad completa integrada
    """
    app = Flask(__name__)
    
    # Configuración básica de Flask
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', os.urandom(32)),
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax'
    )
    
    # ============================================================================
    # OPCIÓN 1: Integración rápida (recomendada para la mayoría de casos)
    # ============================================================================
    
    # Configuración automática según el entorno
    security = quick_setup(app, environment=os.getenv('FLASK_ENV', 'production'))
    
    # ============================================================================
    # OPCIÓN 2: Configuración personalizada
    # ============================================================================
    
    # # Crear configuración personalizada
    # config = SecurityConfig()
    # 
    # # Personalizar componentes según necesidades
    # config.set('COMPONENTS.RATE_LIMITING', True)
    # config.set('RATE_LIMITING.REQUESTS_PER_MINUTE', 120)
    # config.set('SESSION.BIND_TO_IP', False)  # Para desarrollo
    # 
    # # Integrar con configuración personalizada
    # security = integrate_security(app, config=config.config)
    
    # ============================================================================
    # OPCIÓN 3: Integración manual para control total
    # ============================================================================
    
    # from security import (
    #     SecurityIntegration, rate_limiter, csrf, session_security,
    #     api_security, audit_logger
    # )
    # 
    # # Inicializar componentes individualmente
    # security = SecurityIntegration(app)
    # rate_limiter.init_app(app)
    # csrf.init_app(app)
    # session_security.init_app(app)
    # api_security.init_app(app)
    # audit_logger.init_app(app)
    
    return app, security

def setup_example_routes(app, security):
    """
    Configura rutas de ejemplo que demuestran el uso del sistema de seguridad
    """
    from security import (
        require_auth, audit_action, monitor_endpoint,
        secure_file_required, abort_secure
    )
    
    # ============================================================================
    # Ruta pública sin protecciones especiales
    # ============================================================================
    
    @app.route('/')
    def home():
        return jsonify({
            'message': 'API Agente Digital - Sistema de Seguridad Activo',
            'security_status': 'enabled',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    # ============================================================================
    # Ruta protegida con autenticación JWT
    # ============================================================================
    
    @app.route('/api/protected')
    @require_auth('jwt')
    @monitor_endpoint('protected_access')
    def protected_route():
        from flask import g
        return jsonify({
            'message': 'Acceso autorizado',
            'user_id': g.current_user_id,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    # ============================================================================
    # Ruta para login con auditoría
    # ============================================================================
    
    @app.route('/api/auth/login', methods=['POST'])
    @audit_action('user_login')
    def login():
        from security import create_jwt_tokens, audit_logger
        
        data = request.get_json()
        
        # Validación básica (en producción usar input_validator)
        if not data or not data.get('username') or not data.get('password'):
            audit_logger.log_authentication(False, data.get('username', 'unknown'))
            abort_secure(400, "Username and password required")
        
        username = data['username']
        password = data['password']
        
        # Aquí iría la validación real de credenciales
        # Por ahora, demo con credenciales hardcoded
        if username == 'admin' and password == 'secure123':
            # Crear tokens JWT
            tokens = create_jwt_tokens(
                user_id='user123',
                username=username,
                roles=['admin']
            )
            
            # Log exitoso
            audit_logger.log_authentication(True, username)
            
            return jsonify({
                'success': True,
                'tokens': tokens,
                'user': {
                    'id': 'user123',
                    'username': username
                }
            })
        else:
            # Log fallido
            audit_logger.log_authentication(False, username)
            abort_secure(401, "Invalid credentials")
    
    # ============================================================================
    # Ruta para carga de archivos con validación
    # ============================================================================
    
    @app.route('/api/upload', methods=['POST'])
    @require_auth('jwt')
    @secure_file_required('file')
    def upload_file(validated_file):
        from security import file_upload_security
        from flask import g
        
        # El archivo ya está validado por el decorador
        success, path, message = file_upload_security.save_file(
            validated_file,
            user_id=g.current_user_id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'file_path': path
            })
        else:
            abort_secure(400, message)
    
    # ============================================================================
    # Ruta para métricas de seguridad (solo admins)
    # ============================================================================
    
    @app.route('/api/security/metrics')
    @require_auth('jwt')
    def security_metrics():
        from security import security_monitor, get_security_status
        from flask import g
        
        # Verificar permisos (en producción usar decorador de autorización)
        if not hasattr(g, 'jwt_payload') or 'admin' not in g.jwt_payload.get('roles', []):
            abort_secure(403, "Admin access required")
        
        return jsonify({
            'system_status': get_security_status(),
            'runtime_metrics': security_monitor.get_metrics_summary(),
            'recent_events': security_monitor.get_recent_events(50)
        })
    
    # ============================================================================
    # Ruta para configuración de seguridad
    # ============================================================================
    
    @app.route('/api/security/config')
    @require_auth('jwt')
    def security_config():
        from flask import g
        
        # Solo admins pueden ver configuración
        if not hasattr(g, 'jwt_payload') or 'admin' not in g.jwt_payload.get('roles', []):
            abort_secure(403, "Admin access required")
        
        return jsonify(security.get_security_stats())

def setup_error_handlers(app):
    """
    Configura manejadores de error personalizados
    """
    
    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.',
            'retry_after': 60
        }), 429
    
    @app.errorhandler(403)
    def access_forbidden(e):
        return jsonify({
            'error': 'Access forbidden',
            'message': 'You do not have permission to access this resource.'
        }), 403

def main():
    """
    Función principal para ejecutar la aplicación
    """
    # Crear aplicación con seguridad
    app, security = create_secure_app()
    
    # Configurar rutas de ejemplo
    setup_example_routes(app, security)
    
    # Configurar manejadores de error
    setup_error_handlers(app)
    
    # Configurar logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Mostrar información de inicio
    print("=" * 60)
    print("🔒 AGENTE DIGITAL - SISTEMA DE SEGURIDAD")
    print("=" * 60)
    print(f"Entorno: {os.getenv('FLASK_ENV', 'production')}")
    print(f"Puerto: {os.getenv('PORT', 5000)}")
    print("Componentes de seguridad activos:")
    
    from security import get_security_status
    status = get_security_status()
    for component, info in status['components'].items():
        status_icon = "✅" if info['active'] else "❌"
        print(f"  {status_icon} {component}")
    
    print("\nEndpoints disponibles:")
    print("  📍 GET  /                     - Home")
    print("  📍 POST /api/auth/login       - Login")
    print("  📍 GET  /api/protected        - Ruta protegida")
    print("  📍 POST /api/upload           - Carga de archivos")
    print("  📍 GET  /api/security/metrics - Métricas (admin)")
    print("  📍 GET  /api/security/config  - Configuración (admin)")
    print("=" * 60)
    
    # Ejecutar aplicación
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )

if __name__ == '__main__':
    # Importar datetime para los ejemplos
    from datetime import datetime
    
    main()

# ============================================================================
# EJEMPLO DE USO EN APLICACIÓN EXISTENTE
# ============================================================================

"""
Para integrar en tu aplicación existente:

1. Importar e integrar:
   
   from security import integrate_security
   
   app = Flask(__name__)
   security = integrate_security(app)

2. Usar decoradores en rutas:
   
   from security import require_auth, audit_action
   
   @app.route('/api/sensitive')
   @require_auth('jwt')
   @audit_action('access_sensitive_data')
   def sensitive_data():
       return {"data": "sensitive"}

3. Configurar según necesidades:
   
   # Variables de entorno
   FLASK_ENV=production
   RATE_LIMIT_PER_MINUTE=60
   JWT_SECRET_KEY=your-secret-key
   DB_POOL_MAX=100
   
   # O configuración programática
   from security import SecurityConfig
   config = SecurityConfig()
   config.set('RATE_LIMITING.REQUESTS_PER_MINUTE', 120)

4. Monitorear seguridad:
   
   from security import security_monitor
   
   # Obtener métricas
   metrics = security_monitor.get_metrics_summary()
   
   # Agregar handler de alertas
   def alert_handler(alert):
       print(f"ALERTA: {alert['data']['message']}")
   
   security_monitor.add_alert_handler(alert_handler)
"""
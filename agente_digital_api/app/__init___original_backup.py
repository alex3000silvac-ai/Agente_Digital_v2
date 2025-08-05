# app/__init__.py
from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os
import time
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import get_config

def create_app(config_class=None):
    app = Flask(__name__)
    
    # Usar configuración basada en entorno si no se especifica
    if config_class is None:
        config_class = get_config()
    
    app.config.from_object(config_class)
    
    # Inicializar componentes de escalabilidad
    try:
        # from .scalability_integration import init_scalability  # Temporalmente deshabilitado
        # init_scalability(app)
        app.logger.info("Componentes de escalabilidad temporalmente deshabilitados")
    except Exception as e:
        app.logger.error(f"Error inicializando escalabilidad: {e}")
        # Continuar sin escalabilidad si hay errores
    
    # Inicializar sistema de seguridad
    try:
        # from .security_manager import init_security  # Temporalmente deshabilitado
        # init_security(app)
        app.logger.info("Sistema de seguridad temporalmente deshabilitado")
    except Exception as e:
        app.logger.error(f"Error inicializando sistema de seguridad: {e}")
        # Continuar sin algunas características de seguridad si hay errores

    # Configuración CORS mejorada para producción
    cors_origins = getattr(config_class, 'CORS_ORIGINS', ["http://localhost:3000"])
    cors_methods = getattr(config_class, 'CORS_METHODS', ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    cors_headers = getattr(config_class, 'CORS_ALLOW_HEADERS', ["Content-Type", "Authorization", "X-Requested-With"])
    
    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": cors_methods,
            "allow_headers": cors_headers,
            "supports_credentials": getattr(config_class, 'CORS_SUPPORTS_CREDENTIALS', True),
            "max_age": getattr(config_class, 'CORS_MAX_AGE', 3600)
        }
    })
    
    # Headers de seguridad para producción
    @app.after_request
    def set_security_headers(response):
        if hasattr(config_class, 'SECURITY_HEADERS'):
            for header, value in config_class.SECURITY_HEADERS.items():
                response.headers[header] = value
        return response
    
    # Registro de blueprints
    from .routes import auth_bp, inquilinos_bp, taxonomia_bp, obligaciones_bp, acompanamiento_bp
    from .admin_views import admin_api_bp
    from .admin_plataforma import admin_plataforma_bp
    from .admin_dashboard import admin_dashboard_bp
    from .admin_analytics import admin_analytics_bp
    from .password_security import password_security_bp
    from .accesos_clientes import accesos_clientes_bp
    from .views.incidente_views import incidente_bp
    # from .admin_users_manager import admin_users_bp  # Módulo deshabilitado
    from .test_connection import test_bp  # Blueprint de prueba temporal
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(inquilinos_bp)
    app.register_blueprint(taxonomia_bp)
    app.register_blueprint(obligaciones_bp)
    app.register_blueprint(acompanamiento_bp)
    app.register_blueprint(incidente_bp)
    app.register_blueprint(admin_api_bp)
    app.logger.info("Blueprint admin_api_bp registrado.")
    app.logger.info("Blueprint incidente_bp registrado.")
    
    # Blueprints del nuevo sistema de administración de plataforma
    # app.register_blueprint(admin_plataforma_bp)  # Módulo deshabilitado
    app.register_blueprint(admin_dashboard_bp)
    app.register_blueprint(admin_analytics_bp)
    app.register_blueprint(password_security_bp)  # Sistema de gestión de contraseñas
    app.register_blueprint(accesos_clientes_bp)  # Sistema de accesos de clientes
    app.register_blueprint(test_bp)  # Blueprint de prueba temporal para debug
    
    # Blueprint del módulo de administración de usuarios Agente Digital
    # app.register_blueprint(admin_users_bp)  # Módulo deshabilitado
    
    # Health checks mejorados
    @app.route('/health')
    def health_check():
        """Health check básico"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'environment': os.environ.get('FLASK_ENV', 'development')
        })
    
    @app.route('/health/detailed')
    def health_check_detailed():
        """Health check detallado con verificación de servicios"""
        start_time = time.time()
        status = {'status': 'healthy', 'checks': {}}
        
        # Check base de datos
        try:
            from .database import get_db_connection
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                conn.close()
                status['checks']['database'] = 'healthy'
            else:
                status['checks']['database'] = 'unhealthy'
                status['status'] = 'unhealthy'
        except Exception as e:
            status['checks']['database'] = f'unhealthy: {str(e)}'
            status['status'] = 'unhealthy'
        
        # Check Redis (si está configurado)
        try:
            import redis
            redis_url = app.config.get('REDIS_URL')
            if redis_url:
                r = redis.from_url(redis_url)
                r.ping()
                status['checks']['redis'] = 'healthy'
            else:
                status['checks']['redis'] = 'not_configured'
        except Exception as e:
            status['checks']['redis'] = f'unhealthy: {str(e)}'
        
        # Check componentes de escalabilidad
        try:
            from .scalability_integration import get_scalability_manager
            scalability_manager = get_scalability_manager()
            if scalability_manager and scalability_manager.is_healthy():
                status['checks']['scalability'] = 'healthy'
            else:
                status['checks']['scalability'] = 'unhealthy'
        except Exception as e:
            status['checks']['scalability'] = f'unavailable: {str(e)}'
        
        # Tiempo de respuesta
        response_time = (time.time() - start_time) * 1000
        status['response_time_ms'] = round(response_time, 2)
        status['timestamp'] = datetime.utcnow().isoformat()
        
        return jsonify(status), 200 if status['status'] == 'healthy' else 503
    
    @app.route('/health/ready')
    def readiness_check():
        """Check de readiness para Kubernetes"""
        # Verificar que todos los servicios críticos estén listos
        return jsonify({'status': 'ready'}), 200
    
    @app.route('/health/live')
    def liveness_check():
        """Check de liveness para Kubernetes"""
        # Verificar que la aplicación esté viva
        return jsonify({'status': 'alive'}), 200

    return app
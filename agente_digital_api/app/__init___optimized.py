# app/__init___optimized.py
# Configuración simplificada y optimizada de la aplicación

import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime

def create_app(config_class=None):
    """Crear aplicación Flask optimizada y simplificada"""
    app = Flask(__name__)
    
    # Configuración básica simplificada
    app.config.update({
        'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-key-for-testing'),
        'MAX_CONTENT_LENGTH': 100 * 1024 * 1024,  # 100MB
        'JSON_SORT_KEYS': False,
        'TESTING': os.environ.get('TEST_MODE', 'false').lower() == 'true'
    })
    
    # CORS simplificado
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:5173"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Registrar sistema de errores
    try:
        from .modules.core.errors import register_error_handlers
        register_error_handlers(app)
        print("✅ Sistema de errores registrado")
    except ImportError as e:
        print(f"⚠️ Sistema de errores no disponible: {e}")
    
    # Registrar módulos principales de forma simplificada
    modules_registered = 0
    
    # Módulo de salud del sistema
    try:
        from .modules.core.health import health_bp
        app.register_blueprint(health_bp)
        modules_registered += 1
        print("✅ Módulo de salud registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de salud no disponible: {e}")
    
    # Módulo de administración de empresas
    try:
        from .modules.admin.empresas import empresas_bp
        app.register_blueprint(empresas_bp)
        modules_registered += 1
        print("✅ Módulo de empresas registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de empresas no disponible: {e}")
    
    # Módulo de administración de incidentes
    try:
        from .modules.admin.incidentes import incidentes_bp
        app.register_blueprint(incidentes_bp)
        modules_registered += 1
        print("✅ Módulo de incidentes registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de incidentes no disponible: {e}")
    
    # Módulo de administración de cumplimiento
    try:
        from .modules.admin.cumplimiento import cumplimiento_bp
        app.register_blueprint(cumplimiento_bp)
        modules_registered += 1
        print("✅ Módulo de cumplimiento registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de cumplimiento no disponible: {e}")
    
    # Módulo de autenticación (opcional)
    try:
        from .routes import auth_bp
        app.register_blueprint(auth_bp)
        modules_registered += 1
        print("✅ Módulo de autenticación registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de autenticación no disponible: {e}")
    
    # Endpoints básicos integrados
    @app.route('/')
    def index():
        """Página de inicio de la API"""
        return jsonify({
            'name': 'Agente Digital API',
            'version': '2.0.0',
            'status': 'optimized',
            'modules_loaded': modules_registered,
            'health_check': '/api/health',
            'documentation': '/api/info'
        })
    
    @app.route('/api/info')
    def api_info():
        """Información de la API"""
        return jsonify({
            'api_version': '2.0.0',
            'system': 'optimized',
            'modules_loaded': modules_registered,
            'endpoints': {
                'health': '/api/health',
                'empresas': '/api/admin/empresas',
                'incidentes': '/api/admin/empresas/{id}/incidentes',
                'cumplimiento': '/api/admin/empresas/{id}/cumplimientos'
            }
        })
    
    # Información del sistema cargado
    print(f"🎯 Sistema optimizado creado con {modules_registered} módulos")
    
    return app
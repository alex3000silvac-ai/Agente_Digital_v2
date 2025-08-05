# app_production.py
# Aplicación Flask para producción con SQL Server
# Código ejecutable sin simulaciones

from flask import Flask, jsonify
from flask_cors import CORS
import logging
import os
from datetime import datetime

# Configurar logging para producción
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_production_app():
    """
    Crea aplicación Flask para producción con SQL Server únicamente
    """
    app = Flask(__name__)
    
    # Configuración para producción
    app.config.update({
        'SECRET_KEY': os.environ.get('SECRET_KEY', os.urandom(32)),
        'MAX_CONTENT_LENGTH': 50 * 1024 * 1024,  # 50MB
        'JSON_SORT_KEYS': False,
        'ENV': 'production',
        'DEBUG': False,
        'TESTING': False
    })
    
    # CORS para producción
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5173", "http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })
    
    # Registrar blueprint de inquilinos production
    try:
        from app.inquilinos_production import inquilinos_bp
        app.register_blueprint(inquilinos_bp)
        logger.info("✅ Blueprint inquilinos_production registrado exitosamente")
    except ImportError as e:
        logger.error(f"❌ Error importando blueprint inquilinos_production: {e}")
        raise
    
    # Endpoint raíz
    @app.route('/')
    def index():
        return jsonify({
            'name': 'Agente Digital API - Production',
            'version': '1.0.0',
            'environment': 'production',
            'database': 'SQL Server',
            'server': '192.168.100.125',
            'database_name': 'AgenteDigitalDB',
            'endpoints': {
                'health': '/api/admin/inquilinos/health',
                'inquilinos': '/api/admin/inquilinos',
                'inquilino_detalle': '/api/admin/inquilinos/{id}',
                'empresas_por_inquilino': '/api/admin/inquilinos/{id}/empresas'
            },
            'timestamp': datetime.now().isoformat()
        })
    
    # Manejo global de errores
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Endpoint no encontrado',
            'message': 'La ruta solicitada no existe',
            'status_code': 404
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Error interno del servidor: {error}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': 'Ha ocurrido un error inesperado',
            'status_code': 500
        }), 500
    
    # Log de inicio
    logger.info("🏭 Aplicación Flask para producción inicializada")
    logger.info("📊 Configurada para SQL Server únicamente")
    
    return app

# Para ejecutar directamente
if __name__ == '__main__':
    app = create_production_app()
    
    # Configuración para producción
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    logger.info(f"🚀 Iniciando servidor de producción en {host}:{port}")
    
    app.run(
        host=host,
        port=port,
        debug=False,
        use_reloader=False,
        threaded=True
    )
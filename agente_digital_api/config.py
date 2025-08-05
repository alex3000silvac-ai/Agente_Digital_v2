# config.py
# Configuración para Agente Digital API

import os
from datetime import timedelta

class Config:
    """Configuración base para la aplicación"""
    
    # Configuración general
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32))
    DEBUG = False
    TESTING = False
    
    # Base de datos SQL Server
    DB_HOST = os.environ.get('DB_HOST', '192.168.100.125')
    DB_DATABASE = os.environ.get('DB_DATABASE', 'AgenteDigitalDB')
    DB_USERNAME = os.environ.get('DB_USERNAME', 'app_usuario')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_DRIVER = os.environ.get('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # Configuración de archivos
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    
    # CORS Configuration
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    ENV = 'development'

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    ENV = 'production'
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    DEBUG = True
    # Use in-memory database for testing
    DB_DATABASE = 'AgenteDigitalDB_Test'

# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
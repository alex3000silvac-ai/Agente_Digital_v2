# app/__init__.py
# Configuración para ambiente de producción con SQL Server

import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

def create_app(config_class=None):
    """Crear aplicación Flask para producción con SQL Server únicamente"""
    app = Flask(__name__)
    
    # En producción, servir archivos estáticos del frontend
    if os.getenv('FLASK_ENV') == 'production':
        from .static_files import configure_static_files
        configure_static_files(app)
    
    # Configuración para producción
    app.config.update({
        'SECRET_KEY': os.environ.get('SECRET_KEY', os.urandom(32)),
        'MAX_CONTENT_LENGTH': 100 * 1024 * 1024,  # 100MB
        'JSON_SORT_KEYS': False,
        'JSON_AS_ASCII': False,  # Importante: No convertir UTF-8 a ASCII
        'ENV': 'production',
        'DEBUG': False
    })
    
    # CORS configuración mejorada
    cors_origins = os.environ.get('CORS_ORIGINS', '*').split(',')
    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
            "allow_headers": ["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With", "X-CSRF-Token"],
            "expose_headers": ["Content-Length", "X-JSON", "Content-Disposition"],
            "supports_credentials": True,
            "max_age": 3600
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
    
    # Módulo de gestión completa de incidentes
    try:
        from .views.incidente_views import incidente_bp
        app.register_blueprint(incidente_bp)
        modules_registered += 1
        print("✅ Módulo de gestión de incidentes registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de gestión de incidentes no disponible: {e}")
    
    # Módulo simple de incidentes (para pruebas)
    try:
        from .views.incidente_views_simple import incidente_simple_bp
        app.register_blueprint(incidente_simple_bp)
        modules_registered += 1
        print("✅ Módulo simple de incidentes registrado")
    except ImportError as e:
        print(f"⚠️ Módulo simple de incidentes no disponible: {e}")
    
    # Módulo de prueba de incidentes (sin BD)
    try:
        from .views.incidente_test import incidente_test_bp
        app.register_blueprint(incidente_test_bp)
        modules_registered += 1
        print("✅ Módulo de prueba de incidentes registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de prueba de incidentes no disponible: {e}")
    
    # Módulo mejorado de carga completa de incidentes
    try:
        from .views.incidente_cargar_completo import incidente_cargar_bp
        app.register_blueprint(incidente_cargar_bp)
        modules_registered += 1
        print("✅ Módulo de carga completa de incidentes registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de carga completa no disponible: {e}")
    
    # Módulo de clonado perfecto de incidentes
    try:
        from .views.incidente_clonar import incidente_clonar_bp
        app.register_blueprint(incidente_clonar_bp)
        modules_registered += 1
        print("✅ Módulo de clonado perfecto registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de clonado no disponible: {e}")
    
    # Módulo de sistema dinámico de incidentes
    try:
        from .views.incidente_dinamico_views import incidente_dinamico_bp
        app.register_blueprint(incidente_dinamico_bp)
        modules_registered += 1
        print("✅ Módulo de sistema dinámico registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de sistema dinámico no disponible: {e}")
    
    # Módulo de evidencias de incidentes
    try:
        from .views.incidentes_evidencias_views import incidentes_evidencias_bp
        app.register_blueprint(incidentes_evidencias_bp)
        modules_registered += 1
        print("✅ Módulo de evidencias de incidentes registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de evidencias de incidentes no disponible: {e}")
    
    # Módulo de eliminación de evidencias con limpieza de archivos
    try:
        from .views.evidencias_eliminar import evidencias_eliminar_bp
        app.register_blueprint(evidencias_eliminar_bp)
        modules_registered += 1
        print("✅ Módulo de eliminación de evidencias registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de eliminación de evidencias no disponible: {e}")
    
    # Módulo de administración de cumplimiento
    try:
        from .modules.admin.cumplimiento import cumplimiento_bp
        app.register_blueprint(cumplimiento_bp)
        modules_registered += 1
        print("✅ Módulo de cumplimiento registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de cumplimiento no disponible: {e}")
    
    # Módulo de cumplimiento global (endpoints para frontend)
    try:
        from .modules.admin.cumplimiento_global import cumplimiento_global_bp
        app.register_blueprint(cumplimiento_global_bp)
        modules_registered += 1
        print("✅ Módulo de cumplimiento global registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de cumplimiento global no disponible: {e}")
    
    # Módulo de evidencias de cumplimiento
    try:
        from .modules.admin.cumplimiento_evidencias import cumplimiento_evidencias_bp
        app.register_blueprint(cumplimiento_evidencias_bp)
        modules_registered += 1
        print("✅ Módulo de evidencias de cumplimiento registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de evidencias de cumplimiento no disponible: {e}")
    
    # Módulo de administración de inquilinos
    try:
        from .modules.admin.inquilinos import inquilinos_bp
        app.register_blueprint(inquilinos_bp)
        modules_registered += 1
        print("✅ Módulo de inquilinos registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de inquilinos no disponible: {e}")
        # Intentar cargar módulo simple como fallback
        try:
            from .modules.admin.inquilinos_simple import inquilinos_simple_bp
            app.register_blueprint(inquilinos_simple_bp)
            modules_registered += 1
            print("✅ Módulo de inquilinos simple registrado (fallback)")
        except ImportError as e2:
            print(f"⚠️ Módulo de inquilinos simple tampoco disponible: {e2}")
    
    # Módulo de administración de taxonomías
    try:
        from .modules.admin.taxonomias import taxonomias_bp
        app.register_blueprint(taxonomias_bp)
        modules_registered += 1
        print("✅ Módulo de taxonomías registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de taxonomías no disponible: {e}")
    
    # Módulo de taxonomías simple (endpoint adicional)
    try:
        from .modules.admin.taxonomias_simple import taxonomias_simple_bp
        app.register_blueprint(taxonomias_simple_bp)
        modules_registered += 1
        print("✅ Módulo de taxonomías simple registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de taxonomías simple no disponible: {e}")
    
    # Módulo de acompañamiento
    try:
        from .modules.admin.acompanamiento import acompanamiento_bp
        app.register_blueprint(acompanamiento_bp)
        modules_registered += 1
        print("✅ Módulo de acompañamiento registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de acompañamiento no disponible: {e}")
    
    # Módulo de eliminación completa de incidentes (prioritario)
    try:
        from .modules.admin.incidentes_eliminar_completo import incidentes_eliminar_completo_bp
        app.register_blueprint(incidentes_eliminar_completo_bp)
        modules_registered += 1
        print("✅ Módulo de eliminación completa de incidentes registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de eliminación completa no disponible: {e}")
        # Intentar cargar módulo de redirección como fallback
        try:
            from .modules.admin.incidentes_redirect import incidentes_redirect_bp
            app.register_blueprint(incidentes_redirect_bp)
            modules_registered += 1
            print("✅ Módulo de redirección de incidentes registrado (fallback)")
        except ImportError as e2:
            print(f"⚠️ Módulo de redirección tampoco disponible: {e2}")
    
    # Módulo de autenticación (opcional)
    try:
        from .routes import auth_bp
        app.register_blueprint(auth_bp)
        modules_registered += 1
        print("✅ Módulo de autenticación registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de autenticación no disponible: {e}")
    
    # Módulos de incidentes (creación y edición)
    try:
        from .modules.admin import registrar_modulos_admin
        registrar_modulos_admin(app)
        modules_registered += 2  # Dos módulos: crear y editar
        print("✅ Módulos de incidentes (crear/editar) registrados")
    except ImportError as e:
        print(f"⚠️ Módulos de incidentes no disponibles: {e}")
    
    # Módulo de diagnóstico de incidentes
    try:
        from .modules.admin.diagnostico_incidentes import diagnostico_bp
        app.register_blueprint(diagnostico_bp)
        modules_registered += 1
        print("✅ Módulo de diagnóstico de incidentes registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de diagnóstico no disponible: {e}")
    
    # Módulo unificado de incidentes v2
    try:
        from .modules.incidentes import registrar_modulo_unificado
        registrar_modulo_unificado(app)
        modules_registered += 1
        print("✅ Módulo unificado de incidentes v2 registrado")
    except ImportError as e:
        print(f"⚠️ Módulo unificado de incidentes no disponible: {e}")
    
    # Módulo de informes ANCI
    try:
        from .modules.informes_anci_views import informes_anci_bp
        app.register_blueprint(informes_anci_bp)
        modules_registered += 1
        print("✅ Módulo de informes ANCI registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de informes ANCI no disponible: {e}")
    
    # Módulo de endpoints administrativos de incidentes con JWT
    try:
        from .modules.admin.incidentes_admin_endpoints import incidentes_admin_bp
        app.register_blueprint(incidentes_admin_bp)
        modules_registered += 1
        print("✅ Módulo de endpoints administrativos de incidentes registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de endpoints administrativos no disponible: {e}")
    
    # Módulo de informes ANCI completo
    # Comentado temporalmente - parece estar duplicado
    # try:
    #     from .modules.informes_anci_endpoints import informes_anci_completo_bp
    #     app.register_blueprint(informes_anci_completo_bp)
    #     modules_registered += 1
    #     print("✅ Módulo de informes ANCI completo registrado")
    # except ImportError as e:
    #     print(f"⚠️ Módulo de informes ANCI completo no disponible: {e}")
    
    # Módulo de actualización de incidentes con soporte para archivos
    try:
        from .modules.admin.incidentes_actualizar import incidentes_actualizar_bp
        app.register_blueprint(incidentes_actualizar_bp)
        modules_registered += 1
        print("✅ Módulo de actualización de incidentes registrado")
    except ImportError as e:
        print(f"⚠️ Módulo de actualización de incidentes no disponible: {e}")
    
    # Endpoint directo de eliminación de incidentes (para compatibilidad con frontend)
    try:
        from .modules.admin.incidentes_delete_directo import incidentes_delete_bp
        app.register_blueprint(incidentes_delete_bp)
        modules_registered += 1
        print("✅ Endpoint directo de eliminación de incidentes registrado")
    except ImportError as e:
        print(f"⚠️ Endpoint directo de eliminación no disponible: {e}")
    
    # Módulo de estadísticas de incidentes
    try:
        from .modules.admin.incidentes_estadisticas import estadisticas_bp
        app.register_blueprint(estadisticas_bp)
        modules_registered += 1
        print("✅ Módulo de estadísticas de incidentes registrado")
    except ImportError as e:
        print(f"⚠️ No se pudo cargar el módulo de estadísticas: {e}")
    
    # Módulo de actualización ANCI con campos completos
    try:
        from .views.incidente_anci_actualizar import incidente_anci_actualizar_bp
        app.register_blueprint(incidente_anci_actualizar_bp)
        modules_registered += 1
        print("✅ Módulo de actualización ANCI completo registrado")
    except ImportError as e:
        print(f"⚠️ No se pudo cargar el módulo de actualización ANCI: {e}")
    
    # Módulo de taxonomías de incidentes
    try:
        from .views.incidente_taxonomias import incidente_taxonomias_bp
        app.register_blueprint(incidente_taxonomias_bp)
        modules_registered += 1
        print("✅ Módulo de taxonomías de incidentes registrado")
    except ImportError as e:
        print(f"⚠️ No se pudo cargar el módulo de taxonomías de incidentes: {e}")
    
    # Módulo simplificado de taxonomías (sin autenticación)
    try:
        from .views.incidente_taxonomias_simple import incidente_taxonomias_simple_bp
        app.register_blueprint(incidente_taxonomias_simple_bp)
        modules_registered += 1
        print("✅ Módulo de taxonomías simplificado registrado")
    except ImportError as e:
        print(f"⚠️ No se pudo cargar el módulo de taxonomías simplificado: {e}")
    
    # Módulo de campos ANCI
    try:
        from .views.incidente_campos_anci import campos_anci_bp
        app.register_blueprint(campos_anci_bp)
        modules_registered += 1
        print("✅ Módulo de campos ANCI registrado")
    except ImportError as e:
        print(f"⚠️ No se pudo cargar el módulo de campos ANCI: {e}")
    
    # Módulo de generación de documentos ANCI
    try:
        from .views.generar_documento_anci_simple import bp as generar_documento_bp
        app.register_blueprint(generar_documento_bp)
        modules_registered += 1
        print("✅ Módulo de generación de documentos ANCI registrado")
    except ImportError as e:
        print(f"⚠️ No se pudo cargar el módulo de generación de documentos ANCI: {e}")
    
    
    # Endpoints básicos integrados
    @app.route('/')
    def index():
        """Página de inicio de la API"""
        return jsonify({
            'name': 'Agente Digital API',
            'version': '2.0.0',
            'status': 'production',
            'database': 'SQL Server',
            'modules_loaded': modules_registered,
            'health_check': '/api/health'
        })
    
    @app.route('/api/admin/inquilinos', methods=['GET', 'OPTIONS'])
    def get_inquilinos_temp():
        """Endpoint temporal de inquilinos para resolver CORS"""
        if request.method == 'OPTIONS':
            return '', 200
            
        try:
            from .database import get_db_connection
            conn = get_db_connection()
            if not conn:
                return jsonify({'error': 'Error de conexión'}), 500
                
            cursor = conn.cursor()
            cursor.execute("SELECT InquilinoID, RazonSocial, RUT, EstadoActivo FROM Inquilinos ORDER BY RazonSocial")
            rows = cursor.fetchall()
            
            inquilinos = []
            for row in rows:
                inquilinos.append({
                    'InquilinoID': row[0],
                    'RazonSocial': row[1],
                    'RUT': row[2] if row[2] else '',
                    'EstadoActivo': 'Activo' if row[3] else 'Inactivo'
                })
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'inquilinos': inquilinos
            }), 200
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/info')
    def api_info():
        """Información de la API"""
        return jsonify({
            'api_version': '2.0.0',
            'environment': 'production',
            'database': 'SQL Server',
            'modules_loaded': modules_registered,
            'endpoints': {
                'health': '/api/health',
                'empresas': '/api/admin/empresas',
                'incidentes': '/api/admin/empresas/{id}/incidentes',
                'incidentes_crear': '/api/incidentes/crear',
                'incidentes_editar': '/api/incidentes/editar/obtener',
                'incidentes_taxonomias': '/api/incidentes/taxonomias',
                'cumplimiento': '/api/admin/empresas/{id}/cumplimientos',
                'inquilinos': '/api/admin/inquilinos'
            }
        })
    
    # Manejador para solicitudes OPTIONS (preflight CORS)
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = jsonify({'status': 'ok'})
            response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin", "*"))
            response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept")
            response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH")
            response.headers.add("Access-Control-Allow-Credentials", "true")
            response.headers.add("Access-Control-Max-Age", "3600")
            return response, 200
    
    # Asegurar UTF-8 en todas las respuestas JSON
    @app.after_request
    def after_request(response):
        if response.content_type and 'application/json' in response.content_type:
            response.content_type = 'application/json; charset=utf-8'
        return response
    
    # Sistema configurado para producción
    print(f"🏭 Sistema de producción creado con {modules_registered} módulos")
    print(f"📊 Base de datos: SQL Server únicamente")
    
    return app
# admin_views_modular.py
# Archivo principal que registra todos los módulos de vistas

from flask import Flask
from .views.empresas_views import empresas_bp
from .views.incidentes_views import incidentes_bp
from .views.cumplimiento_views import cumplimiento_bp
from .views.health_views import health_bp
from .views.incidentes_evidencias_views import incidentes_evidencias_bp

def register_admin_blueprints(app: Flask):
    """
    Registra todos los blueprints de administración de forma modular
    
    Args:
        app: Instancia de la aplicación Flask
    """
    try:
        # Registrar módulos de administración
        app.register_blueprint(empresas_bp)
        app.register_blueprint(incidentes_bp)
        app.register_blueprint(cumplimiento_bp)
        app.register_blueprint(health_bp)
        app.register_blueprint(incidentes_evidencias_bp)
        
        print("✅ Todos los módulos administrativos registrados exitosamente")
        
        # Verificar rutas registradas
        admin_routes = [rule for rule in app.url_map.iter_rules() if '/api/admin/' in rule.rule]
        print(f"✅ {len(admin_routes)} rutas administrativas registradas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error registrando módulos administrativos: {e}")
        return False

# Para compatibilidad con el sistema existente, crear un blueprint combinado
from flask import Blueprint
admin_api_bp = Blueprint('admin_api_combined', __name__, url_prefix='/api/admin')

# Importar todas las funciones de los módulos para el blueprint combinado
from .views.empresas_views import get_empresa_details, get_dashboard_stats
from .views.incidentes_views import get_incidentes_empresa
from .views.cumplimiento_views import get_informe_cumplimiento, get_cumplimientos_empresa
from .views.health_views import health_check, health_check_detailed

# Registrar rutas en el blueprint combinado
admin_api_bp.add_url_rule('/<int:empresa_id>', 'get_empresa_details', get_empresa_details, methods=['GET'])
admin_api_bp.add_url_rule('/<int:empresa_id>/dashboard-stats', 'get_dashboard_stats', get_dashboard_stats, methods=['GET'])
admin_api_bp.add_url_rule('/<int:empresa_id>/incidentes', 'get_incidentes_empresa', get_incidentes_empresa, methods=['GET'])
admin_api_bp.add_url_rule('/<int:empresa_id>/informe-cumplimiento', 'get_informe_cumplimiento', get_informe_cumplimiento, methods=['GET'])
admin_api_bp.add_url_rule('/<int:empresa_id>/cumplimientos', 'get_cumplimientos_empresa', get_cumplimientos_empresa, methods=['GET'])
admin_api_bp.add_url_rule('/health', 'health_check', health_check, methods=['GET'])
admin_api_bp.add_url_rule('/health/detailed', 'health_check_detailed', health_check_detailed, methods=['GET'])
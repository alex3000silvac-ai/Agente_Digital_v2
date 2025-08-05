# modules/admin/__init__.py
# Módulos de administración

from .incidentes_crear import registrar_rutas_creacion
from .incidentes_editar import registrar_rutas_edicion

def registrar_modulos_admin(app):
    """Registra todos los módulos de administración"""
    # Registrar rutas de incidentes
    registrar_rutas_creacion(app)
    registrar_rutas_edicion(app)
    
    # Registrar rutas de informes ANCI completos
    try:
        from ..informes_anci_endpoints import registrar_rutas_informes_completos
        registrar_rutas_informes_completos(app)
        print("✅ Módulo de informes ANCI completos registrado")
    except Exception as e:
        print(f"⚠️ Módulo de informes ANCI completos no disponible: {e}")
# app/scalability_integration.py
# Integración de todos los componentes de escalabilidad

import logging
from flask import Flask, g, request
from typing import Optional

from .database_pool import init_db, db_manager
from .cache_manager import init_cache, cache_manager
from .rate_limiter import init_rate_limiter, rate_limiter
from .file_manager import init_file_manager, file_manager
from .query_optimizer import query_optimizer

logger = logging.getLogger(__name__)

class ScalabilityManager:
    """Gestor centralizado de escalabilidad"""
    
    def __init__(self):
        self.initialized = False
        self.components = {}
        
    def initialize_all(self, app: Flask):
        """Inicializar todos los componentes de escalabilidad"""
        if self.initialized:
            return True
            
        try:
            logger.info("Inicializando componentes de escalabilidad...")
            
            # 1. Inicializar base de datos con connection pooling
            logger.info("Inicializando database pool...")
            db_manager_instance = init_db(app)
            self.components['database'] = db_manager_instance
            
            # 2. Inicializar cache Redis
            logger.info("Inicializando cache Redis...")
            cache_success = init_cache(app)
            self.components['cache'] = cache_manager
            self.components['cache_enabled'] = cache_success
            
            # 3. Inicializar rate limiter
            logger.info("Inicializando rate limiter...")
            redis_client = cache_manager.redis_client if cache_success else None
            rate_limiter_instance = init_rate_limiter(redis_client)
            self.components['rate_limiter'] = rate_limiter_instance
            
            # 4. Inicializar file manager
            logger.info("Inicializando file manager...")
            file_manager_instance = init_file_manager()
            self.components['file_manager'] = file_manager_instance
            
            # 5. Registrar hooks de Flask
            self._register_flask_hooks(app)
            
            # 6. Registrar endpoints de monitoreo
            self._register_monitoring_endpoints(app)
            
            self.initialized = True
            logger.info("Todos los componentes de escalabilidad inicializados correctamente")
            
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando componentes de escalabilidad: {e}")
            raise
    
    def _register_flask_hooks(self, app: Flask):
        """Registrar hooks de Flask para escalabilidad"""
        
        @app.before_request
        def before_request():
            """Hook antes de cada request"""
            # Verificar rate limiting
            if rate_limiter and hasattr(rate_limiter, 'check_rate_limit'):
                try:
                    allowed, info = rate_limiter.check_rate_limit()
                    if not allowed:
                        from flask import jsonify
                        response = jsonify({
                            'error': 'Rate limit exceeded',
                            'message': 'Too many requests. Please try again later.',
                            'retry_after': info.get('retry_after', 60)
                        })
                        response.status_code = 429
                        response.headers['Retry-After'] = str(info.get('retry_after', 60))
                        return response
                except Exception as e:
                    logger.error(f"Error en rate limiting: {e}")
            
            # Almacenar tiempo de inicio para métricas
            g.request_start_time = time.time()
        
        @app.after_request
        def after_request(response):
            """Hook después de cada request"""
            # Agregar headers de performance
            if hasattr(g, 'request_start_time'):
                response_time = time.time() - g.request_start_time
                response.headers['X-Response-Time'] = f"{response_time:.3f}s"
            
            # Agregar headers de escalabilidad
            response.headers['X-Powered-By'] = 'Agente Digital Scalable'
            
            return response
        
        @app.teardown_appcontext
        def teardown_db(error):
            """Limpiar recursos después del request"""
            # El connection pooling maneja automáticamente las conexiones
            pass
    
    def _register_monitoring_endpoints(self, app: Flask):
        """Registrar endpoints de monitoreo y métricas"""
        
        @app.route('/metrics/scalability')
        def scalability_metrics():
            """Endpoint para métricas de escalabilidad"""
            from flask import jsonify
            
            try:
                metrics = {
                    'timestamp': time.time(),
                    'database': {},
                    'cache': {},
                    'rate_limiter': {},
                    'file_manager': {},
                    'query_optimizer': {}
                }
                
                # Métricas de base de datos
                if 'database' in self.components:
                    try:
                        metrics['database'] = db_manager.get_pool_stats()
                    except Exception as e:
                        metrics['database'] = {'error': str(e)}
                
                # Métricas de cache
                if 'cache' in self.components:
                    try:
                        metrics['cache'] = cache_manager.get_stats()
                    except Exception as e:
                        metrics['cache'] = {'error': str(e)}
                
                # Métricas de rate limiter
                if 'rate_limiter' in self.components:
                    try:
                        metrics['rate_limiter'] = rate_limiter.get_stats()
                    except Exception as e:
                        metrics['rate_limiter'] = {'error': str(e)}
                
                # Métricas de file manager
                if 'file_manager' in self.components:
                    try:
                        metrics['file_manager'] = file_manager.get_stats()
                    except Exception as e:
                        metrics['file_manager'] = {'error': str(e)}
                
                # Métricas de query optimizer
                try:
                    from .query_optimizer import get_query_stats
                    metrics['query_optimizer'] = get_query_stats()
                except Exception as e:
                    metrics['query_optimizer'] = {'error': str(e)}
                
                return jsonify(metrics)
                
            except Exception as e:
                logger.error(f"Error obteniendo métricas: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/metrics/performance')
        def performance_metrics():
            """Endpoint para métricas de performance"""
            from flask import jsonify
            import psutil
            
            try:
                # Métricas del sistema
                system_metrics = {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_usage': psutil.disk_usage('/').percent,
                    'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                }
                
                # Métricas de la aplicación
                app_metrics = {
                    'active_connections': len(threading.enumerate()),
                    'cache_hit_rate': 0,
                    'avg_response_time': 0
                }
                
                # Cache hit rate
                if 'cache' in self.components:
                    cache_stats = cache_manager.get_stats()
                    if cache_stats.get('total_requests', 0) > 0:
                        app_metrics['cache_hit_rate'] = cache_stats.get('hit_rate', 0)
                
                return jsonify({
                    'timestamp': time.time(),
                    'system': system_metrics,
                    'application': app_metrics
                })
                
            except Exception as e:
                logger.error(f"Error obteniendo métricas de performance: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/admin/scalability/status')
        def scalability_status():
            """Estado de los componentes de escalabilidad"""
            from flask import jsonify
            
            status = {
                'initialized': self.initialized,
                'components': {}
            }
            
            for component_name, component in self.components.items():
                if component_name == 'cache_enabled':
                    continue
                    
                try:
                    if component_name == 'database':
                        # Verificar salud de la base de datos
                        is_healthy = db_manager.health_check()
                        status['components']['database'] = {
                            'status': 'healthy' if is_healthy else 'unhealthy',
                            'pool_stats': db_manager.get_pool_stats()
                        }
                    
                    elif component_name == 'cache':
                        # Verificar salud del cache
                        is_healthy = cache_manager.health_check()
                        status['components']['cache'] = {
                            'status': 'healthy' if is_healthy else 'unhealthy',
                            'enabled': self.components.get('cache_enabled', False)
                        }
                    
                    elif component_name == 'rate_limiter':
                        # Rate limiter siempre funcional
                        status['components']['rate_limiter'] = {
                            'status': 'healthy',
                            'enabled': rate_limiter.config['enabled']
                        }
                    
                    elif component_name == 'file_manager':
                        # File manager siempre funcional si se inicializó
                        status['components']['file_manager'] = {
                            'status': 'healthy'
                        }
                        
                except Exception as e:
                    status['components'][component_name] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            return jsonify(status)
    
    def get_component(self, component_name: str):
        """Obtener instancia de un componente"""
        return self.components.get(component_name)
    
    def is_healthy(self) -> bool:
        """Verificar si todos los componentes están saludables"""
        if not self.initialized:
            return False
        
        try:
            # Verificar base de datos
            if not db_manager.health_check():
                return False
            
            # Verificar cache (opcional)
            if self.components.get('cache_enabled', False):
                if not cache_manager.health_check():
                    logger.warning("Cache no está saludable, pero no es crítico")
            
            return True
            
        except Exception as e:
            logger.error(f"Error verificando salud de componentes: {e}")
            return False

# Instancia global
scalability_manager = ScalabilityManager()

def init_scalability(app: Flask):
    """Inicializar todos los componentes de escalabilidad"""
    return scalability_manager.initialize_all(app)

def get_scalability_manager():
    """Obtener instancia del gestor de escalabilidad"""
    return scalability_manager

# Imports para compatibilidad
import time
import threading
try:
    import psutil
except ImportError:
    psutil = None
# app/cache_manager.py
# Sistema de caching avanzado con Redis para escalabilidad

import os
import json
import pickle
import logging
import time
import hashlib
from functools import wraps
from typing import Any, Optional, Union, Callable, Dict
from datetime import datetime, timedelta

try:
    import redis
    from redis.connection import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class CacheManager:
    """Gestor de cache avanzado con Redis para alta escalabilidad"""
    
    def __init__(self, config=None):
        self.config = config or self._get_default_config()
        self.redis_client = None
        self.connection_pool = None
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
            'total_requests': 0
        }
        self._enabled = REDIS_AVAILABLE and self.config.get('enabled', True)
        
    def _get_default_config(self):
        """Configuración por defecto desde variables de entorno"""
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        
        return {
            'enabled': os.environ.get('CACHE_ENABLED', 'true').lower() == 'true',
            'redis_url': redis_url,
            'password': os.environ.get('REDIS_PASSWORD'),
            'socket_timeout': int(os.environ.get('REDIS_SOCKET_TIMEOUT', '5')),
            'socket_connect_timeout': int(os.environ.get('REDIS_CONNECT_TIMEOUT', '5')),
            'health_check_interval': int(os.environ.get('REDIS_HEALTH_CHECK_INTERVAL', '30')),
            'retry_on_timeout': os.environ.get('REDIS_RETRY_ON_TIMEOUT', 'true').lower() == 'true',
            'max_connections': int(os.environ.get('REDIS_MAX_CONNECTIONS', '50')),
            
            # Configuración de cache
            'default_timeout': int(os.environ.get('CACHE_DEFAULT_TIMEOUT', '300')),  # 5 minutos
            'key_prefix': os.environ.get('CACHE_KEY_PREFIX', 'agentedigital:'),
            'serializer': os.environ.get('CACHE_SERIALIZER', 'json'),  # json, pickle
            
            # Configuraciones específicas por tipo de datos
            'timeouts': {
                'user_session': 3600,      # 1 hora
                'taxonomy_data': 86400,    # 24 horas
                'company_data': 1800,      # 30 minutos
                'incident_list': 300,      # 5 minutos
                'compliance_data': 1800,   # 30 minutos
                'dashboard_data': 600,     # 10 minutos
                'api_responses': 300,      # 5 minutos
            }
        }
    
    def initialize(self):
        """Inicializar conexión Redis con connection pooling"""
        if not self._enabled:
            logger.warning("Cache deshabilitado o Redis no disponible")
            return False
            
        try:
            # Crear connection pool
            self.connection_pool = ConnectionPool.from_url(
                self.config['redis_url'],
                password=self.config['password'],
                socket_timeout=self.config['socket_timeout'],
                socket_connect_timeout=self.config['socket_connect_timeout'],
                health_check_interval=self.config['health_check_interval'],
                retry_on_timeout=self.config['retry_on_timeout'],
                max_connections=self.config['max_connections'],
                decode_responses=True
            )
            
            # Crear cliente Redis
            self.redis_client = redis.Redis(
                connection_pool=self.connection_pool,
                decode_responses=True
            )
            
            # Verificar conectividad
            self.health_check()
            
            logger.info(f"Cache Redis inicializado: {self.config['redis_url']}")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando Redis: {e}")
            self._enabled = False
            return False
    
    def health_check(self):
        """Verificar salud de Redis"""
        if not self._enabled or not self.redis_client:
            return False
            
        try:
            response = self.redis_client.ping()
            return response is True
        except Exception as e:
            logger.error(f"Redis health check falló: {e}")
            return False
    
    def _generate_key(self, key: str, namespace: str = '') -> str:
        """Generar clave completa con prefijo y namespace"""
        prefix = self.config['key_prefix']
        if namespace:
            return f"{prefix}{namespace}:{key}"
        return f"{prefix}{key}"
    
    def _serialize_value(self, value: Any) -> Union[str, bytes]:
        """Serializar valor para almacenamiento"""
        if self.config['serializer'] == 'pickle':
            return pickle.dumps(value)
        else:
            # JSON por defecto
            return json.dumps(value, default=str, ensure_ascii=False)
    
    def _deserialize_value(self, value: Union[str, bytes]) -> Any:
        """Deserializar valor desde almacenamiento"""
        if not value:
            return None
            
        try:
            if self.config['serializer'] == 'pickle':
                return pickle.loads(value)
            else:
                # JSON por defecto
                return json.loads(value)
        except Exception as e:
            logger.error(f"Error deserializando valor: {e}")
            return None
    
    def get(self, key: str, namespace: str = '', default: Any = None) -> Any:
        """Obtener valor del cache"""
        if not self._enabled or not self.redis_client:
            return default
            
        self._stats['total_requests'] += 1
        full_key = self._generate_key(key, namespace)
        
        try:
            value = self.redis_client.get(full_key)
            if value is not None:
                self._stats['hits'] += 1
                return self._deserialize_value(value)
            else:
                self._stats['misses'] += 1
                return default
                
        except Exception as e:
            logger.error(f"Error obteniendo cache {full_key}: {e}")
            self._stats['errors'] += 1
            return default
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None, 
            namespace: str = '') -> bool:
        """Almacenar valor en cache"""
        if not self._enabled or not self.redis_client:
            return False
            
        full_key = self._generate_key(key, namespace)
        timeout = timeout or self.config['default_timeout']
        
        try:
            serialized_value = self._serialize_value(value)
            result = self.redis_client.setex(full_key, timeout, serialized_value)
            
            if result:
                self._stats['sets'] += 1
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error almacenando cache {full_key}: {e}")
            self._stats['errors'] += 1
            return False
    
    def delete(self, key: str, namespace: str = '') -> bool:
        """Eliminar valor del cache"""
        if not self._enabled or not self.redis_client:
            return False
            
        full_key = self._generate_key(key, namespace)
        
        try:
            result = self.redis_client.delete(full_key)
            if result:
                self._stats['deletes'] += 1
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error eliminando cache {full_key}: {e}")
            self._stats['errors'] += 1
            return False
    
    def delete_pattern(self, pattern: str, namespace: str = '') -> int:
        """Eliminar múltiples claves por patrón"""
        if not self._enabled or not self.redis_client:
            return 0
            
        full_pattern = self._generate_key(pattern, namespace)
        
        try:
            keys = self.redis_client.keys(full_pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                self._stats['deletes'] += deleted
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Error eliminando patrón {full_pattern}: {e}")
            self._stats['errors'] += 1
            return 0
    
    def clear_namespace(self, namespace: str) -> int:
        """Limpiar todo un namespace"""
        return self.delete_pattern('*', namespace)
    
    def increment(self, key: str, amount: int = 1, namespace: str = '') -> Optional[int]:
        """Incrementar contador"""
        if not self._enabled or not self.redis_client:
            return None
            
        full_key = self._generate_key(key, namespace)
        
        try:
            return self.redis_client.incr(full_key, amount)
        except Exception as e:
            logger.error(f"Error incrementando {full_key}: {e}")
            self._stats['errors'] += 1
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        stats = self._stats.copy()
        
        if self._stats['total_requests'] > 0:
            stats['hit_rate'] = (self._stats['hits'] / self._stats['total_requests']) * 100
            stats['miss_rate'] = (self._stats['misses'] / self._stats['total_requests']) * 100
        else:
            stats['hit_rate'] = 0
            stats['miss_rate'] = 0
            
        # Información de Redis si está disponible
        if self._enabled and self.redis_client:
            try:
                info = self.redis_client.info()
                stats['redis_info'] = {
                    'used_memory': info.get('used_memory_human', 'N/A'),
                    'connected_clients': info.get('connected_clients', 'N/A'),
                    'total_connections_received': info.get('total_connections_received', 'N/A'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                }
                
                if info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0) > 0:
                    total = info['keyspace_hits'] + info['keyspace_misses']
                    stats['redis_hit_rate'] = (info['keyspace_hits'] / total) * 100
                    
            except Exception as e:
                logger.error(f"Error obteniendo stats de Redis: {e}")
                
        return stats

# Decoradores para caching automático
def cached(timeout: Optional[int] = None, namespace: str = '', 
           key_func: Optional[Callable] = None):
    """Decorador para cachear resultados de funciones"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave de cache
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Generar clave basada en función y argumentos
                func_name = f"{func.__module__}.{func.__name__}"
                args_str = str(args) + str(sorted(kwargs.items()))
                cache_key = f"{func_name}:{hashlib.md5(args_str.encode()).hexdigest()}"
            
            # Intentar obtener del cache
            cached_result = cache_manager.get(cache_key, namespace)
            if cached_result is not None:
                return cached_result
            
            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, timeout, namespace)
            
            return result
        return wrapper
    return decorator

def cache_by_user(timeout: Optional[int] = None):
    """Decorador para cachear por usuario"""
    def key_func(*args, **kwargs):
        # Asumir que el primer argumento es user_id o está en kwargs
        user_id = kwargs.get('user_id') or (args[0] if args else 'anonymous')
        func_name = f"{args[0].__name__}" if hasattr(args[0], '__name__') else 'function'
        return f"user:{user_id}:{func_name}"
    
    return cached(timeout=timeout, namespace='user_cache', key_func=key_func)

def cache_by_company(timeout: Optional[int] = None):
    """Decorador para cachear por empresa"""
    def key_func(*args, **kwargs):
        company_id = kwargs.get('empresa_id') or kwargs.get('company_id')
        if not company_id and args:
            # Buscar en argumentos posicionales
            for arg in args:
                if isinstance(arg, (int, str)) and str(arg).isdigit():
                    company_id = arg
                    break
        
        func_name = f"{args[0].__name__}" if hasattr(args[0], '__name__') else 'function'
        return f"company:{company_id}:{func_name}"
    
    return cached(timeout=timeout, namespace='company_cache', key_func=key_func)

# Instancia global del cache manager
cache_manager = CacheManager()

def init_cache(app=None):
    """Inicializar cache con configuración de Flask"""
    if app:
        # Actualizar configuración desde Flask app
        config = {
            'enabled': app.config.get('CACHE_ENABLED', True),
            'redis_url': app.config.get('REDIS_URL', 'redis://localhost:6379/0'),
            'password': app.config.get('REDIS_PASSWORD'),
            'socket_timeout': app.config.get('REDIS_SOCKET_TIMEOUT', 5),
            'socket_connect_timeout': app.config.get('REDIS_CONNECT_TIMEOUT', 5),
            'health_check_interval': app.config.get('REDIS_HEALTH_CHECK_INTERVAL', 30),
            'retry_on_timeout': app.config.get('REDIS_RETRY_ON_TIMEOUT', True),
            'max_connections': app.config.get('REDIS_MAX_CONNECTIONS', 50),
            'default_timeout': app.config.get('CACHE_DEFAULT_TIMEOUT', 300),
            'key_prefix': app.config.get('CACHE_KEY_PREFIX', 'agentedigital:'),
            'serializer': app.config.get('CACHE_SERIALIZER', 'json'),
        }
        cache_manager.config.update(config)
    
    return cache_manager.initialize()

# Funciones helper
def get_cache() -> CacheManager:
    """Obtener instancia del cache manager"""
    return cache_manager

def clear_user_cache(user_id: Union[int, str]):
    """Limpiar cache de un usuario específico"""
    cache_manager.clear_namespace(f'user_cache:user:{user_id}')

def clear_company_cache(company_id: Union[int, str]):
    """Limpiar cache de una empresa específica"""
    cache_manager.clear_namespace(f'company_cache:company:{company_id}')

def warm_cache():
    """Pre-cargar datos frecuentemente usados en cache"""
    # TODO: Implementar pre-carga de taxonomías, listas de empresas, etc.
    pass
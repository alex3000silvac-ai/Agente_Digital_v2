# app/rate_limiter.py
# Sistema de rate limiting avanzado para escalabilidad y protección

import os
import time
import json
import logging
import hashlib
from functools import wraps
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timedelta
from flask import request, jsonify, g

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter avanzado con múltiples estrategias y protección DDoS"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.fallback_store = {}  # Fallback cuando Redis no está disponible
        self.config = self._get_config()
        self._stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'rate_limited_ips': set(),
            'top_ips': {},
            'suspicious_activity': []
        }
        
    def _get_config(self):
        """Configuración de rate limiting"""
        return {
            # Configuración general
            'enabled': os.environ.get('RATE_LIMITING_ENABLED', 'true').lower() == 'true',
            'key_prefix': os.environ.get('RATE_LIMIT_PREFIX', 'rl:agentedigital:'),
            'default_window': int(os.environ.get('RATE_LIMIT_WINDOW', '3600')),  # 1 hora
            
            # Límites por endpoint
            'limits': {
                # Autenticación - muy restrictivo
                'auth_login': {
                    'limit': 5,
                    'window': 300,  # 5 minutos
                    'burst': 2,
                    'block_duration': 900  # 15 minutos de bloqueo
                },
                'auth_register': {
                    'limit': 3,
                    'window': 3600,  # 1 hora
                    'burst': 1,
                    'block_duration': 3600
                },
                
                # API general
                'api_general': {
                    'limit': 100,
                    'window': 3600,  # 1 hora
                    'burst': 20,
                    'block_duration': 300
                },
                
                # Consultas de datos
                'api_read': {
                    'limit': 200,
                    'window': 3600,
                    'burst': 50,
                    'block_duration': 60
                },
                
                # Operaciones de escritura
                'api_write': {
                    'limit': 50,
                    'window': 3600,
                    'burst': 10,
                    'block_duration': 600
                },
                
                # Uploads
                'api_upload': {
                    'limit': 20,
                    'window': 3600,
                    'burst': 5,
                    'block_duration': 1800
                },
                
                # Reportes y exports
                'api_export': {
                    'limit': 10,
                    'window': 3600,
                    'burst': 2,
                    'block_duration': 3600
                },
                
                # Health checks - sin límite
                'health': {
                    'limit': 1000,
                    'window': 60,
                    'burst': 100,
                    'block_duration': 0
                }
            },
            
            # Configuración anti-DDoS
            'ddos_protection': {
                'enabled': True,
                'requests_per_second_threshold': 50,
                'burst_threshold': 100,
                'window_size': 60,
                'auto_block_duration': 3600,  # 1 hora
                'whitelist_ips': ['127.0.0.1', '::1']
            },
            
            # Configuración de user-based limiting
            'user_limits': {
                'admin': {
                    'limit': 1000,
                    'window': 3600,
                    'burst': 200
                },
                'user': {
                    'limit': 200,
                    'window': 3600,
                    'burst': 50
                },
                'anonymous': {
                    'limit': 50,
                    'window': 3600,
                    'burst': 10
                }
            }
        }
    
    def _get_client_id(self, include_user=True) -> str:
        """Obtener identificador único del cliente"""
        # IP del cliente (considerando proxies)
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', 
                               request.environ.get('HTTP_X_REAL_IP', 
                                                 request.remote_addr))
        
        if ',' in ip:
            ip = ip.split(',')[0].strip()
        
        # Incluir usuario si está autenticado
        user_id = ""
        if include_user and hasattr(g, 'current_user') and g.current_user:
            user_id = f":user:{g.current_user.get('user_id', 'unknown')}"
        
        return f"{ip}{user_id}"
    
    def _get_endpoint_category(self, endpoint: str, method: str) -> str:
        """Categorizar endpoint para aplicar límites específicos"""
        endpoint_lower = endpoint.lower()
        method_lower = method.lower()
        
        # Health checks
        if 'health' in endpoint_lower:
            return 'health'
        
        # Autenticación
        if '/auth/login' in endpoint_lower:
            return 'auth_login'
        elif '/auth/register' in endpoint_lower or '/auth/signup' in endpoint_lower:
            return 'auth_register'
        
        # API endpoints
        if endpoint_lower.startswith('/api/'):
            # Uploads
            if 'upload' in endpoint_lower or method_lower == 'post' and any(
                x in endpoint_lower for x in ['evidence', 'file', 'attachment']
            ):
                return 'api_upload'
            
            # Exports y reportes
            elif any(x in endpoint_lower for x in ['export', 'report', 'download', 'pdf']):
                return 'api_export'
            
            # Operaciones de escritura
            elif method_lower in ['post', 'put', 'delete']:
                return 'api_write'
            
            # Operaciones de lectura
            elif method_lower in ['get']:
                return 'api_read'
            
            # API general
            else:
                return 'api_general'
        
        # Por defecto
        return 'api_general'
    
    def _generate_key(self, client_id: str, category: str, window_start: int) -> str:
        """Generar clave Redis para rate limiting"""
        key_data = f"{client_id}:{category}:{window_start}"
        return f"{self.config['key_prefix']}{hashlib.md5(key_data.encode()).hexdigest()}"
    
    def _get_window_start(self, window_size: int) -> int:
        """Obtener inicio de ventana temporal"""
        return int(time.time()) // window_size * window_size
    
    def _check_redis_limit(self, key: str, limit: int, window: int, burst: int) -> Tuple[bool, Dict[str, Any]]:
        """Verificar límite usando Redis con sliding window"""
        current_time = time.time()
        window_start = current_time - window
        
        pipe = self.redis_client.pipeline()
        
        # Limpiar entradas antiguas
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Obtener cantidad actual de requests
        pipe.zcard(key)
        
        # Agregar request actual
        pipe.zadd(key, {str(current_time): current_time})
        
        # Establecer expiración
        pipe.expire(key, window + 60)
        
        results = pipe.execute()
        current_requests = results[1] + 1  # +1 por el request actual
        
        # Verificar límite de burst (requests muy rápidos)
        burst_window = 60  # 1 minuto para burst
        burst_start = current_time - burst_window
        burst_count = self.redis_client.zcount(key, burst_start, current_time)
        
        allowed = current_requests <= limit and burst_count <= burst
        
        info = {
            'current_requests': current_requests,
            'limit': limit,
            'burst_count': burst_count,
            'burst_limit': burst,
            'window_size': window,
            'reset_time': int(window_start + window),
            'retry_after': window if not allowed else 0
        }
        
        return allowed, info
    
    def _check_fallback_limit(self, key: str, limit: int, window: int, burst: int) -> Tuple[bool, Dict[str, Any]]:
        """Verificar límite usando fallback en memoria"""
        current_time = time.time()
        
        if key not in self.fallback_store:
            self.fallback_store[key] = []
        
        # Limpiar entradas antiguas
        window_start = current_time - window
        self.fallback_store[key] = [
            req_time for req_time in self.fallback_store[key] 
            if req_time > window_start
        ]
        
        # Agregar request actual
        self.fallback_store[key].append(current_time)
        
        current_requests = len(self.fallback_store[key])
        
        # Verificar burst
        burst_window = 60
        burst_start = current_time - burst_window
        burst_count = sum(1 for req_time in self.fallback_store[key] if req_time > burst_start)
        
        allowed = current_requests <= limit and burst_count <= burst
        
        info = {
            'current_requests': current_requests,
            'limit': limit,
            'burst_count': burst_count,
            'burst_limit': burst,
            'window_size': window,
            'reset_time': int(window_start + window),
            'retry_after': window if not allowed else 0
        }
        
        return allowed, info
    
    def _check_ddos_protection(self, client_id: str) -> Tuple[bool, Optional[str]]:
        """Verificar protección anti-DDoS"""
        if not self.config['ddos_protection']['enabled']:
            return True, None
        
        ip = client_id.split(':')[0]
        
        # Whitelist
        if ip in self.config['ddos_protection']['whitelist_ips']:
            return True, None
        
        ddos_config = self.config['ddos_protection']
        current_time = time.time()
        
        # Clave para tracking de DDoS
        ddos_key = f"{self.config['key_prefix']}ddos:{ip}"
        
        if self.redis_client:
            # Verificar si IP está bloqueada por DDoS
            block_key = f"{ddos_key}:blocked"
            if self.redis_client.get(block_key):
                return False, "IP temporarily blocked due to suspicious activity"
            
            # Contar requests en ventana de tiempo
            window_start = current_time - ddos_config['window_size']
            self.redis_client.zremrangebyscore(ddos_key, 0, window_start)
            self.redis_client.zadd(ddos_key, {str(current_time): current_time})
            self.redis_client.expire(ddos_key, ddos_config['window_size'] + 60)
            
            request_count = self.redis_client.zcard(ddos_key)
            
            # Verificar threshold de DDoS
            if request_count > ddos_config['requests_per_second_threshold'] * ddos_config['window_size']:
                # Bloquear IP
                self.redis_client.setex(
                    block_key, 
                    ddos_config['auto_block_duration'], 
                    json.dumps({
                        'blocked_at': current_time,
                        'reason': 'DDoS protection triggered',
                        'request_count': request_count
                    })
                )
                
                logger.warning(f"IP {ip} blocked for DDoS protection: {request_count} requests in {ddos_config['window_size']}s")
                return False, "IP blocked due to excessive requests"
        
        return True, None
    
    def _log_suspicious_activity(self, client_id: str, reason: str, details: Dict[str, Any]):
        """Registrar actividad sospechosa"""
        activity = {
            'timestamp': time.time(),
            'client_id': client_id,
            'reason': reason,
            'details': details,
            'endpoint': request.endpoint,
            'method': request.method,
            'user_agent': request.headers.get('User-Agent', '')
        }
        
        self._stats['suspicious_activity'].append(activity)
        
        # Mantener solo los últimos 1000 registros
        if len(self._stats['suspicious_activity']) > 1000:
            self._stats['suspicious_activity'] = self._stats['suspicious_activity'][-1000:]
        
        logger.warning(f"Suspicious activity: {reason} from {client_id}")
    
    def check_rate_limit(self, endpoint: str = None, method: str = None, 
                        user_type: str = None) -> Tuple[bool, Dict[str, Any]]:
        """Verificar rate limit principal"""
        if not self.config['enabled']:
            return True, {'status': 'disabled'}
        
        self._stats['total_requests'] += 1
        
        # Obtener información del request
        endpoint = endpoint or request.endpoint or request.path
        method = method or request.method
        client_id = self._get_client_id()
        
        # Verificar protección DDoS primero
        ddos_allowed, ddos_reason = self._check_ddos_protection(client_id)
        if not ddos_allowed:
            self._stats['blocked_requests'] += 1
            self._stats['rate_limited_ips'].add(client_id.split(':')[0])
            self._log_suspicious_activity(client_id, 'DDoS protection', {'reason': ddos_reason})
            
            return False, {
                'error': 'Rate limit exceeded',
                'reason': ddos_reason,
                'retry_after': self.config['ddos_protection']['auto_block_duration']
            }
        
        # Determinar categoría de endpoint
        category = self._get_endpoint_category(endpoint, method)
        limit_config = self.config['limits'].get(category, self.config['limits']['api_general'])
        
        # Ajustar límites según tipo de usuario
        if user_type and user_type in self.config['user_limits']:
            user_config = self.config['user_limits'][user_type]
            limit_config = {
                'limit': min(limit_config['limit'], user_config['limit']),
                'window': limit_config['window'],
                'burst': min(limit_config['burst'], user_config['burst']),
                'block_duration': limit_config['block_duration']
            }
        
        # Generar clave de rate limiting
        window_start = self._get_window_start(limit_config['window'])
        key = self._generate_key(client_id, category, window_start)
        
        # Verificar límite
        if self.redis_client:
            try:
                allowed, info = self._check_redis_limit(
                    key, 
                    limit_config['limit'], 
                    limit_config['window'], 
                    limit_config['burst']
                )
            except Exception as e:
                logger.error(f"Redis error in rate limiting: {e}")
                allowed, info = self._check_fallback_limit(
                    key, 
                    limit_config['limit'], 
                    limit_config['window'], 
                    limit_config['burst']
                )
        else:
            allowed, info = self._check_fallback_limit(
                key, 
                limit_config['limit'], 
                limit_config['window'], 
                limit_config['burst']
            )
        
        # Actualizar estadísticas
        if not allowed:
            self._stats['blocked_requests'] += 1
            self._stats['rate_limited_ips'].add(client_id.split(':')[0])
            self._log_suspicious_activity(
                client_id, 
                'Rate limit exceeded', 
                {
                    'category': category,
                    'limit': limit_config['limit'],
                    'current': info['current_requests']
                }
            )
        
        # Actualizar estadísticas de top IPs
        ip = client_id.split(':')[0]
        self._stats['top_ips'][ip] = self._stats['top_ips'].get(ip, 0) + 1
        
        # Agregar información adicional
        info.update({
            'category': category,
            'client_id': client_id,
            'allowed': allowed,
            'block_duration': limit_config['block_duration'] if not allowed else 0
        })
        
        return allowed, info
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del rate limiter"""
        stats = self._stats.copy()
        
        # Calcular rate de bloqueo
        if stats['total_requests'] > 0:
            stats['block_rate'] = (stats['blocked_requests'] / stats['total_requests']) * 100
        else:
            stats['block_rate'] = 0
        
        # Top 10 IPs más activas
        stats['top_ips'] = dict(
            sorted(stats['top_ips'].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        # Convertir set a list para serialización
        stats['rate_limited_ips'] = list(stats['rate_limited_ips'])
        
        # Actividad sospechosa reciente (últimas 24 horas)
        current_time = time.time()
        day_ago = current_time - 86400
        stats['recent_suspicious_activity'] = [
            activity for activity in stats['suspicious_activity']
            if activity['timestamp'] > day_ago
        ]
        
        return stats
    
    def clear_ip_blocks(self, ip: str) -> bool:
        """Limpiar bloqueos de una IP específica"""
        if not self.redis_client:
            return False
        
        try:
            # Limpiar bloqueo DDoS
            ddos_block_key = f"{self.config['key_prefix']}ddos:{ip}:blocked"
            self.redis_client.delete(ddos_block_key)
            
            # Limpiar contadores de rate limiting
            pattern = f"{self.config['key_prefix']}*{ip}*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            
            logger.info(f"Cleared blocks for IP: {ip}")
            return True
        except Exception as e:
            logger.error(f"Error clearing blocks for IP {ip}: {e}")
            return False

# Instancia global
rate_limiter = None

def init_rate_limiter(redis_client=None):
    """Inicializar rate limiter"""
    global rate_limiter
    rate_limiter = RateLimiter(redis_client)
    return rate_limiter

# Decoradores
def rate_limit(category: str = None, user_type: str = None):
    """Decorador para aplicar rate limiting a funciones"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if rate_limiter:
                allowed, info = rate_limiter.check_rate_limit(
                    endpoint=request.endpoint,
                    method=request.method,
                    user_type=user_type
                )
                
                if not allowed:
                    response = jsonify({
                        'error': 'Rate limit exceeded',
                        'message': 'Too many requests. Please try again later.',
                        'retry_after': info.get('retry_after', 60),
                        'limit': info.get('limit'),
                        'reset_time': info.get('reset_time')
                    })
                    response.status_code = 429
                    response.headers['Retry-After'] = str(info.get('retry_after', 60))
                    response.headers['X-RateLimit-Limit'] = str(info.get('limit', 0))
                    response.headers['X-RateLimit-Remaining'] = str(max(0, info.get('limit', 0) - info.get('current_requests', 0)))
                    response.headers['X-RateLimit-Reset'] = str(info.get('reset_time', 0))
                    return response
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit_by_user():
    """Decorador para rate limiting basado en usuario"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_type = 'anonymous'
            if hasattr(g, 'current_user') and g.current_user:
                user_role = g.current_user.get('role', 'user').lower()
                user_type = 'admin' if user_role in ['admin', 'administrator'] else 'user'
            
            return rate_limit(user_type=user_type)(func)(*args, **kwargs)
        return wrapper
    return decorator
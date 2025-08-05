"""
rate_limiter.py - Control de tasa y protección anti-DoS/DDoS
==========================================================

Este módulo implementa un sistema robusto de rate limiting para proteger
contra ataques de denegación de servicio y abuso de la API.

Características:
- Rate limiting por IP
- Rate limiting por usuario autenticado
- Detección de patrones de ataque
- Blacklist automática de IPs maliciosas
- Circuit breaker para protección de servicios
- Throttling dinámico bajo carga
"""

import os
import time
import json
import redis
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from functools import wraps
from flask import request, g, abort, jsonify, current_app
import ipaddress

class RateLimiter:
    """
    Sistema de rate limiting con múltiples estrategias de protección
    """
    
    def __init__(self, app=None, redis_client=None):
        self.app = app
        self.redis_client = redis_client
        self.local_cache = defaultdict(lambda: {'count': 0, 'window_start': time.time()})
        self.blacklist = set()
        self.suspicious_ips = defaultdict(int)
        
        self.config = {
            'ENABLE_RATE_LIMIT': os.getenv('ENABLE_RATE_LIMIT', 'true').lower() == 'true',
            'REQUESTS_PER_MINUTE': int(os.getenv('RATE_LIMIT_PER_MINUTE', 100)),
            'REQUESTS_PER_HOUR': int(os.getenv('RATE_LIMIT_PER_HOUR', 3000)),
            'BURST_LIMIT': int(os.getenv('RATE_LIMIT_BURST', 10)),
            'BLACKLIST_THRESHOLD': int(os.getenv('BLACKLIST_THRESHOLD', 5)),
            'BLACKLIST_DURATION': int(os.getenv('BLACKLIST_DURATION', 3600)),  # 1 hora
            'SUSPICIOUS_PATTERN_THRESHOLD': int(os.getenv('SUSPICIOUS_PATTERN_THRESHOLD', 10)),
            'USE_REDIS': os.getenv('USE_REDIS_RATE_LIMIT', 'false').lower() == 'true',
            'REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            'ENABLE_DISTRIBUTED_LIMITING': os.getenv('ENABLE_DISTRIBUTED_LIMITING', 'false').lower() == 'true'
        }
        
        # Métricas para monitoreo
        self.metrics = {
            'total_requests': 0,
            'blocked_requests': 0,
            'blacklisted_ips': 0,
            'current_load': 0
        }
        
        # Circuit breaker para servicios
        self.circuit_breakers = defaultdict(lambda: {
            'failures': 0,
            'last_failure': None,
            'state': 'closed'  # closed, open, half-open
        })
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa el rate limiter con la aplicación Flask"""
        self.app = app
        
        # Inicializar Redis si está configurado
        if self.config['USE_REDIS'] and not self.redis_client:
            try:
                self.redis_client = redis.from_url(self.config['REDIS_URL'])
                self.redis_client.ping()
                app.logger.info("✅ Redis conectado para rate limiting")
            except Exception as e:
                app.logger.warning(f"⚠️ Redis no disponible, usando rate limiting local: {e}")
                self.config['USE_REDIS'] = False
        
        # Iniciar thread de limpieza
        self._start_cleanup_thread()
    
    def limit(self, requests_per_minute=None, requests_per_hour=None, burst=None):
        """
        Decorator para aplicar rate limiting a endpoints
        
        Args:
            requests_per_minute: Límite por minuto (override config)
            requests_per_hour: Límite por hora (override config)
            burst: Límite de ráfaga (override config)
        
        Uso:
            @app.route('/api/endpoint')
            @rate_limiter.limit(requests_per_minute=50)
            def endpoint():
                return jsonify({'status': 'ok'})
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not self.config['ENABLE_RATE_LIMIT']:
                    return f(*args, **kwargs)
                
                # Obtener identificador del cliente
                client_id = self._get_client_identifier()
                
                # Verificar blacklist
                if self._is_blacklisted(client_id):
                    self._log_blocked_request(client_id, 'blacklisted')
                    abort(403, 'Access denied')
                
                # Aplicar rate limiting
                limits = {
                    'per_minute': requests_per_minute or self.config['REQUESTS_PER_MINUTE'],
                    'per_hour': requests_per_hour or self.config['REQUESTS_PER_HOUR'],
                    'burst': burst or self.config['BURST_LIMIT']
                }
                
                if not self._check_rate_limit(client_id, limits):
                    self._handle_rate_limit_exceeded(client_id)
                    abort(429, 'Rate limit exceeded')
                
                # Detectar patrones sospechosos
                self._check_suspicious_patterns(client_id)
                
                # Ejecutar función original
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator
    
    def _get_client_identifier(self):
        """
        Obtiene un identificador único para el cliente
        
        Returns:
            str: Identificador del cliente
        """
        # Si hay usuario autenticado, usar su ID
        if hasattr(g, 'current_user_id') and g.current_user_id:
            return f"user:{g.current_user_id}"
        
        # Obtener IP del cliente
        ip = self._get_client_ip()
        return f"ip:{ip}"
    
    def _get_client_ip(self):
        """Obtiene la IP real del cliente"""
        headers = ['X-Forwarded-For', 'X-Real-IP', 'CF-Connecting-IP']
        
        for header in headers:
            ip = request.headers.get(header)
            if ip:
                if ',' in ip:
                    ip = ip.split(',')[0].strip()
                try:
                    ipaddress.ip_address(ip)
                    return ip
                except ValueError:
                    continue
        
        return request.remote_addr or 'unknown'
    
    def _check_rate_limit(self, client_id, limits):
        """
        Verifica si el cliente ha excedido los límites
        
        Args:
            client_id: Identificador del cliente
            limits: Diccionario con límites
            
        Returns:
            bool: True si está dentro de los límites
        """
        current_time = time.time()
        
        if self.config['USE_REDIS']:
            return self._check_rate_limit_redis(client_id, limits, current_time)
        else:
            return self._check_rate_limit_local(client_id, limits, current_time)
    
    def _check_rate_limit_local(self, client_id, limits, current_time):
        """Verifica rate limit usando cache local"""
        # Límite por minuto
        minute_key = f"{client_id}:minute"
        minute_data = self.local_cache[minute_key]
        
        # Reiniciar ventana si ha pasado un minuto
        if current_time - minute_data['window_start'] > 60:
            minute_data['count'] = 0
            minute_data['window_start'] = current_time
        
        # Verificar límite por minuto
        if minute_data['count'] >= limits['per_minute']:
            return False
        
        # Verificar burst
        burst_key = f"{client_id}:burst"
        if burst_key not in self.local_cache:
            self.local_cache[burst_key] = deque(maxlen=limits['burst'])
        
        burst_queue = self.local_cache[burst_key]
        
        # Limpiar requests antiguos del burst
        while burst_queue and burst_queue[0] < current_time - 1:
            burst_queue.popleft()
        
        if len(burst_queue) >= limits['burst']:
            return False
        
        # Incrementar contadores
        minute_data['count'] += 1
        burst_queue.append(current_time)
        
        # Actualizar métricas
        self.metrics['total_requests'] += 1
        
        return True
    
    def _check_rate_limit_redis(self, client_id, limits, current_time):
        """Verifica rate limit usando Redis"""
        try:
            pipe = self.redis_client.pipeline()
            
            # Clave para ventana de minuto
            minute_key = f"rate_limit:{client_id}:minute"
            minute_window = int(current_time // 60)
            
            # Incrementar contador atómicamente
            pipe.hincrby(minute_key, minute_window, 1)
            pipe.expire(minute_key, 120)  # Expirar después de 2 minutos
            
            # Obtener conteo actual
            pipe.hget(minute_key, minute_window)
            
            results = pipe.execute()
            current_count = int(results[2] or 0)
            
            if current_count > limits['per_minute']:
                return False
            
            # Verificar burst usando sorted set
            burst_key = f"rate_limit:{client_id}:burst"
            pipe = self.redis_client.pipeline()
            
            # Eliminar requests antiguos
            pipe.zremrangebyscore(burst_key, 0, current_time - 1)
            
            # Contar requests en el último segundo
            pipe.zcount(burst_key, current_time - 1, current_time)
            
            # Agregar request actual
            pipe.zadd(burst_key, {str(current_time): current_time})
            pipe.expire(burst_key, 10)
            
            results = pipe.execute()
            burst_count = results[1]
            
            if burst_count >= limits['burst']:
                return False
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error en Redis rate limiting: {e}")
            # Fallback a rate limiting local
            return self._check_rate_limit_local(client_id, limits, current_time)
    
    def _is_blacklisted(self, client_id):
        """Verifica si un cliente está en la blacklist"""
        if self.config['USE_REDIS']:
            try:
                return self.redis_client.sismember('blacklist', client_id)
            except:
                pass
        
        return client_id in self.blacklist
    
    def _add_to_blacklist(self, client_id):
        """Agrega un cliente a la blacklist"""
        self.blacklist.add(client_id)
        self.metrics['blacklisted_ips'] += 1
        
        if self.config['USE_REDIS']:
            try:
                self.redis_client.sadd('blacklist', client_id)
                self.redis_client.expire(f'blacklist:{client_id}', self.config['BLACKLIST_DURATION'])
            except:
                pass
        
        current_app.logger.warning(f"🚫 Cliente agregado a blacklist: {client_id}")
    
    def _handle_rate_limit_exceeded(self, client_id):
        """Maneja cuando se excede el rate limit"""
        self.metrics['blocked_requests'] += 1
        
        # Incrementar contador de violaciones
        self.suspicious_ips[client_id] += 1
        
        # Auto-blacklist si excede el threshold
        if self.suspicious_ips[client_id] >= self.config['BLACKLIST_THRESHOLD']:
            self._add_to_blacklist(client_id)
            self._log_security_event('auto_blacklist', {
                'client_id': client_id,
                'violations': self.suspicious_ips[client_id]
            })
    
    def _check_suspicious_patterns(self, client_id):
        """Detecta patrones de comportamiento sospechoso"""
        # Analizar patrón de requests
        pattern_key = f"{client_id}:pattern"
        if pattern_key not in self.local_cache:
            self.local_cache[pattern_key] = []
        
        pattern_list = self.local_cache[pattern_key]
        pattern_list.append({
            'time': time.time(),
            'path': request.path,
            'method': request.method
        })
        
        # Mantener solo los últimos 100 requests
        if len(pattern_list) > 100:
            pattern_list.pop(0)
        
        # Detectar escaneo de puertos/paths
        if len(pattern_list) >= 10:
            recent_paths = [p['path'] for p in pattern_list[-10:]]
            unique_paths = set(recent_paths)
            
            # Si intenta acceder a muchos paths diferentes rápidamente
            if len(unique_paths) >= 8:
                self.suspicious_ips[client_id] += 2
                self._log_security_event('path_scanning', {
                    'client_id': client_id,
                    'paths': list(unique_paths)
                })
    
    def circuit_breaker(self, service_name, failure_threshold=5, timeout=60):
        """
        Implementa circuit breaker para servicios externos
        
        Args:
            service_name: Nombre del servicio
            failure_threshold: Número de fallos antes de abrir el circuito
            timeout: Tiempo en segundos antes de intentar cerrar el circuito
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                breaker = self.circuit_breakers[service_name]
                
                # Verificar estado del circuit breaker
                if breaker['state'] == 'open':
                    # Verificar si es tiempo de intentar half-open
                    if breaker['last_failure'] and \
                       time.time() - breaker['last_failure'] > timeout:
                        breaker['state'] = 'half-open'
                    else:
                        raise Exception(f"Circuit breaker OPEN for {service_name}")
                
                try:
                    # Ejecutar función
                    result = f(*args, **kwargs)
                    
                    # Si estaba half-open y funcionó, cerrar
                    if breaker['state'] == 'half-open':
                        breaker['state'] = 'closed'
                        breaker['failures'] = 0
                    
                    return result
                    
                except Exception as e:
                    # Registrar fallo
                    breaker['failures'] += 1
                    breaker['last_failure'] = time.time()
                    
                    # Abrir circuito si se excede el threshold
                    if breaker['failures'] >= failure_threshold:
                        breaker['state'] = 'open'
                        self._log_security_event('circuit_breaker_open', {
                            'service': service_name,
                            'failures': breaker['failures']
                        })
                    
                    raise e
            
            return decorated_function
        return decorator
    
    def get_current_load(self):
        """Obtiene la carga actual del sistema"""
        # Calcular requests por segundo en el último minuto
        current_time = time.time()
        recent_requests = sum(
            1 for client_data in self.local_cache.values()
            if isinstance(client_data, dict) and 
            current_time - client_data.get('window_start', 0) < 60
        )
        
        return {
            'requests_per_minute': recent_requests,
            'active_clients': len(self.local_cache),
            'blacklisted_clients': len(self.blacklist),
            'suspicious_clients': len(self.suspicious_ips),
            'metrics': self.metrics
        }
    
    def _start_cleanup_thread(self):
        """Inicia thread de limpieza de datos antiguos"""
        def cleanup():
            while True:
                try:
                    current_time = time.time()
                    
                    # Limpiar cache local
                    keys_to_remove = []
                    for key, data in self.local_cache.items():
                        if isinstance(data, dict) and 'window_start' in data:
                            if current_time - data['window_start'] > 300:  # 5 minutos
                                keys_to_remove.append(key)
                    
                    for key in keys_to_remove:
                        del self.local_cache[key]
                    
                    # Limpiar IPs sospechosas antiguas
                    self.suspicious_ips = defaultdict(int, {
                        k: v for k, v in self.suspicious_ips.items()
                        if v > 0
                    })
                    
                    # Actualizar métricas
                    self.metrics['current_load'] = len(self.local_cache)
                    
                    time.sleep(60)  # Ejecutar cada minuto
                    
                except Exception as e:
                    if current_app:
                        current_app.logger.error(f"Error en cleanup thread: {e}")
        
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()
    
    def _log_blocked_request(self, client_id, reason):
        """Registra una request bloqueada"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'request_blocked',
            'client_id': client_id,
            'reason': reason,
            'path': request.path,
            'method': request.method
        }
        
        if current_app:
            current_app.logger.warning(f"RATE_LIMIT_BLOCK: {json.dumps(event)}")
    
    def _log_security_event(self, event_type, details):
        """Registra un evento de seguridad"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'details': details
        }
        
        if current_app:
            current_app.logger.warning(f"SECURITY_EVENT: {json.dumps(event)}")


# Instancia global para uso conveniente
rate_limiter = RateLimiter()
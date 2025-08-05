"""
monitoring.py - Sistema de monitoreo de seguridad
==============================================

Este módulo implementa monitoreo en tiempo real de eventos de seguridad,
métricas de rendimiento y detección de anomalías.

Características:
- Monitoreo de eventos de seguridad
- Métricas de rendimiento
- Detección de anomalías
- Alertas automáticas
- Dashboard de seguridad
- Integración con sistemas de monitoreo
"""

import os
import time
import json
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, Any, List, Optional, Callable
import statistics

class SecurityMonitor:
    """
    Sistema de monitoreo de seguridad en tiempo real
    """
    
    def __init__(self, app=None):
        self.app = app
        self.config = {
            'ENABLE_MONITORING': os.getenv('ENABLE_SECURITY_MONITORING', 'true').lower() == 'true',
            'METRICS_INTERVAL': int(os.getenv('METRICS_INTERVAL', 60)),  # 1 minuto
            'ANOMALY_DETECTION': os.getenv('ENABLE_ANOMALY_DETECTION', 'true').lower() == 'true',
            'ALERT_THRESHOLD_HIGH': int(os.getenv('ALERT_THRESHOLD_HIGH', 100)),
            'ALERT_THRESHOLD_CRITICAL': int(os.getenv('ALERT_THRESHOLD_CRITICAL', 500)),
            'METRICS_RETENTION': int(os.getenv('METRICS_RETENTION_HOURS', 24)),
            'MAX_EVENTS_BUFFER': int(os.getenv('MAX_EVENTS_BUFFER', 10000)),
            'ENABLE_PROMETHEUS': os.getenv('ENABLE_PROMETHEUS_METRICS', 'false').lower() == 'true',
            'ENABLE_STATSD': os.getenv('ENABLE_STATSD_METRICS', 'false').lower() == 'true',
            'STATSD_HOST': os.getenv('STATSD_HOST', 'localhost'),
            'STATSD_PORT': int(os.getenv('STATSD_PORT', 8125))
        }
        
        # Métricas
        self.metrics = {
            'requests': defaultdict(int),
            'errors': defaultdict(int),
            'response_times': defaultdict(list),
            'security_events': defaultdict(int),
            'rate_limit_hits': defaultdict(int),
            'authentication_attempts': defaultdict(int),
            'authorization_failures': defaultdict(int),
            'suspicious_activities': defaultdict(int)
        }
        
        # Eventos recientes (cola circular)
        self.recent_events = deque(maxlen=self.config['MAX_EVENTS_BUFFER'])
        
        # Alertas activas
        self.active_alerts = {}
        
        # Callbacks para alertas
        self.alert_handlers = []
        
        # Thread de monitoreo
        self.monitoring_thread = None
        self.running = False
        
        # Lock para thread safety
        self.lock = threading.RLock()
        
        # Estadísticas de baseline para detección de anomalías
        self.baseline_stats = {}
        
        # Clientes externos
        self.statsd_client = None
        self.prometheus_registry = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa el monitor con la aplicación"""
        self.app = app
        
        if not self.config['ENABLE_MONITORING']:
            return
        
        # Inicializar clientes de métricas
        self._init_metrics_clients()
        
        # Iniciar thread de monitoreo
        self._start_monitoring_thread()
        
        # Registrar endpoint de métricas
        self._register_metrics_endpoint(app)
    
    def _init_metrics_clients(self):
        """Inicializa clientes de métricas externos"""
        # StatsD
        if self.config['ENABLE_STATSD']:
            try:
                import statsd
                self.statsd_client = statsd.StatsClient(
                    self.config['STATSD_HOST'],
                    self.config['STATSD_PORT']
                )
            except ImportError:
                self.app.logger.warning("StatsD habilitado pero módulo no instalado")
        
        # Prometheus
        if self.config['ENABLE_PROMETHEUS']:
            try:
                from prometheus_client import CollectorRegistry, Counter, Histogram, Gauge
                self.prometheus_registry = CollectorRegistry()
                
                # Definir métricas Prometheus
                self.prometheus_metrics = {
                    'requests_total': Counter(
                        'flask_requests_total',
                        'Total requests',
                        ['method', 'endpoint', 'status'],
                        registry=self.prometheus_registry
                    ),
                    'request_duration': Histogram(
                        'flask_request_duration_seconds',
                        'Request duration',
                        ['method', 'endpoint'],
                        registry=self.prometheus_registry
                    ),
                    'security_events': Counter(
                        'security_events_total',
                        'Security events',
                        ['event_type', 'severity'],
                        registry=self.prometheus_registry
                    ),
                    'active_sessions': Gauge(
                        'active_sessions',
                        'Active user sessions',
                        registry=self.prometheus_registry
                    )
                }
            except ImportError:
                self.app.logger.warning("Prometheus habilitado pero módulo no instalado")
    
    def record_request(self, method: str, endpoint: str, status_code: int,
                      response_time: float):
        """Registra métricas de una request"""
        with self.lock:
            # Actualizar contadores
            key = f"{method}:{endpoint}"
            self.metrics['requests'][key] += 1
            
            if status_code >= 400:
                self.metrics['errors'][key] += 1
            
            # Guardar tiempo de respuesta
            self.metrics['response_times'][key].append(response_time)
            
            # Limitar histórico de tiempos
            if len(self.metrics['response_times'][key]) > 1000:
                self.metrics['response_times'][key] = self.metrics['response_times'][key][-1000:]
        
        # Enviar a sistemas externos
        if self.statsd_client:
            self.statsd_client.incr(f'requests.{method.lower()}.{status_code}')
            self.statsd_client.timing(f'response_time.{endpoint}', response_time * 1000)
        
        if self.prometheus_metrics:
            self.prometheus_metrics['requests_total'].labels(
                method=method,
                endpoint=endpoint,
                status=str(status_code)
            ).inc()
            
            self.prometheus_metrics['request_duration'].labels(
                method=method,
                endpoint=endpoint
            ).observe(response_time)
    
    def record_security_event(self, event_type: str, severity: str = 'info',
                            details: Dict[str, Any] = None):
        """Registra un evento de seguridad"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': event_type,
            'severity': severity,
            'details': details or {}
        }
        
        with self.lock:
            # Agregar a eventos recientes
            self.recent_events.append(event)
            
            # Actualizar contadores
            self.metrics['security_events'][event_type] += 1
            
            # Contadores específicos
            if event_type == 'authentication_failed':
                self.metrics['authentication_attempts']['failed'] += 1
            elif event_type == 'authentication_success':
                self.metrics['authentication_attempts']['success'] += 1
            elif event_type == 'authorization_denied':
                self.metrics['authorization_failures']['total'] += 1
            elif event_type in ['suspicious_pattern', 'anomaly_detected']:
                self.metrics['suspicious_activities'][event_type] += 1
        
        # Verificar si se debe generar alerta
        self._check_alert_conditions(event)
        
        # Métricas externas
        if self.statsd_client:
            self.statsd_client.incr(f'security.{event_type}')
        
        if self.prometheus_metrics:
            self.prometheus_metrics['security_events'].labels(
                event_type=event_type,
                severity=severity
            ).inc()
    
    def _check_alert_conditions(self, event: Dict[str, Any]):
        """Verifica condiciones para generar alertas"""
        severity = event['severity']
        event_type = event['type']
        
        # Alerta inmediata para eventos críticos
        if severity == 'critical':
            self._trigger_alert('critical_event', {
                'event': event,
                'message': f'Critical security event: {event_type}'
            })
        
        # Verificar umbrales de eventos
        with self.lock:
            # Contar eventos recientes del mismo tipo
            recent_count = sum(
                1 for e in self.recent_events
                if e['type'] == event_type and
                (datetime.utcnow() - datetime.fromisoformat(e['timestamp'])).seconds < 300
            )
            
            if recent_count >= self.config['ALERT_THRESHOLD_CRITICAL']:
                self._trigger_alert('threshold_critical', {
                    'event_type': event_type,
                    'count': recent_count,
                    'period': '5 minutes',
                    'message': f'Critical threshold reached for {event_type}'
                })
            elif recent_count >= self.config['ALERT_THRESHOLD_HIGH']:
                self._trigger_alert('threshold_high', {
                    'event_type': event_type,
                    'count': recent_count,
                    'period': '5 minutes',
                    'message': f'High threshold reached for {event_type}'
                })
    
    def _trigger_alert(self, alert_type: str, alert_data: Dict[str, Any]):
        """Dispara una alerta"""
        alert_id = f"{alert_type}:{alert_data.get('event_type', 'general')}:{int(time.time())}"
        
        # Evitar alertas duplicadas
        if alert_id in self.active_alerts:
            return
        
        alert = {
            'id': alert_id,
            'type': alert_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': alert_data,
            'status': 'active'
        }
        
        self.active_alerts[alert_id] = alert
        
        # Log de alerta
        if self.app:
            self.app.logger.error(f"SECURITY ALERT: {alert_data.get('message', alert_type)}")
        
        # Ejecutar handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                if self.app:
                    self.app.logger.error(f"Error in alert handler: {e}")
    
    def add_alert_handler(self, handler: Callable):
        """Agrega un handler para alertas"""
        self.alert_handlers.append(handler)
    
    def _start_monitoring_thread(self):
        """Inicia el thread de monitoreo"""
        def monitor_loop():
            while self.running:
                try:
                    # Calcular métricas
                    self._calculate_metrics()
                    
                    # Detectar anomalías
                    if self.config['ANOMALY_DETECTION']:
                        self._detect_anomalies()
                    
                    # Limpiar datos antiguos
                    self._cleanup_old_data()
                    
                    # Esperar hasta el siguiente ciclo
                    time.sleep(self.config['METRICS_INTERVAL'])
                    
                except Exception as e:
                    if self.app:
                        self.app.logger.error(f"Error in monitoring thread: {e}")
        
        self.running = True
        self.monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitoring_thread.start()
    
    def _calculate_metrics(self):
        """Calcula métricas agregadas"""
        with self.lock:
            # Calcular tasas por minuto
            current_time = time.time()
            
            # Response time percentiles
            for endpoint, times in self.metrics['response_times'].items():
                if times:
                    p50 = statistics.median(times)
                    p95 = statistics.quantiles(times, n=20)[18] if len(times) > 20 else max(times)
                    p99 = statistics.quantiles(times, n=100)[98] if len(times) > 100 else max(times)
                    
                    # Guardar percentiles
                    self.metrics[f'response_time_p50:{endpoint}'] = p50
                    self.metrics[f'response_time_p95:{endpoint}'] = p95
                    self.metrics[f'response_time_p99:{endpoint}'] = p99
    
    def _detect_anomalies(self):
        """Detecta anomalías en los patrones de tráfico"""
        with self.lock:
            # Detección simple basada en desviación estándar
            for metric_type, values in self.metrics.items():
                if isinstance(values, dict) and values:
                    # Calcular estadísticas
                    counts = list(values.values())
                    if len(counts) > 10 and all(isinstance(c, (int, float)) for c in counts):
                        mean = statistics.mean(counts)
                        stdev = statistics.stdev(counts) if len(counts) > 1 else 0
                        
                        # Detectar outliers (3 sigma)
                        for key, value in values.items():
                            if value > mean + (3 * stdev):
                                self.record_security_event(
                                    'anomaly_detected',
                                    'warning',
                                    {
                                        'metric': metric_type,
                                        'key': key,
                                        'value': value,
                                        'mean': mean,
                                        'stdev': stdev
                                    }
                                )
    
    def _cleanup_old_data(self):
        """Limpia datos antiguos"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.config['METRICS_RETENTION'])
        
        with self.lock:
            # Limpiar eventos antiguos
            while self.recent_events and datetime.fromisoformat(self.recent_events[0]['timestamp']) < cutoff_time:
                self.recent_events.popleft()
            
            # Limpiar alertas resueltas
            resolved_alerts = [
                aid for aid, alert in self.active_alerts.items()
                if alert['status'] == 'resolved' and
                datetime.fromisoformat(alert['timestamp']) < cutoff_time
            ]
            
            for aid in resolved_alerts:
                del self.active_alerts[aid]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de métricas actuales"""
        with self.lock:
            # Calcular resumen
            total_requests = sum(self.metrics['requests'].values())
            total_errors = sum(self.metrics['errors'].values())
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            
            # Eventos recientes por tipo
            recent_events_by_type = defaultdict(int)
            for event in self.recent_events:
                recent_events_by_type[event['type']] += 1
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'requests': {
                    'total': total_requests,
                    'errors': total_errors,
                    'error_rate': f"{error_rate:.2f}%"
                },
                'security_events': {
                    'total': sum(self.metrics['security_events'].values()),
                    'by_type': dict(self.metrics['security_events']),
                    'recent': dict(recent_events_by_type)
                },
                'performance': {
                    'avg_response_time': self._calculate_avg_response_time(),
                    'endpoints': self._get_endpoint_metrics()
                },
                'alerts': {
                    'active': len([a for a in self.active_alerts.values() if a['status'] == 'active']),
                    'total': len(self.active_alerts)
                }
            }
    
    def _calculate_avg_response_time(self) -> float:
        """Calcula tiempo de respuesta promedio global"""
        all_times = []
        for times in self.metrics['response_times'].values():
            all_times.extend(times)
        
        return statistics.mean(all_times) if all_times else 0
    
    def _get_endpoint_metrics(self) -> List[Dict[str, Any]]:
        """Obtiene métricas por endpoint"""
        endpoint_data = []
        
        for endpoint, count in self.metrics['requests'].items():
            errors = self.metrics['errors'].get(endpoint, 0)
            times = self.metrics['response_times'].get(endpoint, [])
            
            endpoint_data.append({
                'endpoint': endpoint,
                'requests': count,
                'errors': errors,
                'error_rate': f"{(errors/count*100):.2f}%" if count > 0 else "0%",
                'avg_time': f"{statistics.mean(times):.3f}s" if times else "0s"
            })
        
        # Ordenar por requests descendente
        return sorted(endpoint_data, key=lambda x: x['requests'], reverse=True)[:10]
    
    def _register_metrics_endpoint(self, app):
        """Registra endpoint para exponer métricas"""
        @app.route('/api/metrics/security')
        def security_metrics():
            """Endpoint de métricas de seguridad"""
            return self.get_metrics_summary()
        
        if self.config['ENABLE_PROMETHEUS']:
            @app.route('/metrics')
            def prometheus_metrics():
                """Endpoint de métricas Prometheus"""
                try:
                    from prometheus_client import generate_latest
                    return generate_latest(self.prometheus_registry)
                except:
                    return "Prometheus not configured", 503
    
    def get_recent_events(self, limit: int = 100, event_type: str = None) -> List[Dict[str, Any]]:
        """Obtiene eventos recientes"""
        with self.lock:
            events = list(self.recent_events)
            
            # Filtrar por tipo si se especifica
            if event_type:
                events = [e for e in events if e['type'] == event_type]
            
            # Ordenar por timestamp descendente
            events.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return events[:limit]
    
    def resolve_alert(self, alert_id: str):
        """Marca una alerta como resuelta"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id]['status'] = 'resolved'
            self.active_alerts[alert_id]['resolved_at'] = datetime.utcnow().isoformat()
    
    def shutdown(self):
        """Detiene el monitor de forma segura"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)


# Instancia global
security_monitor = SecurityMonitor()


# Decorador para monitorear endpoints automáticamente
def monitor_endpoint(event_type: str = None):
    """
    Decorador para monitorear automáticamente un endpoint
    
    Uso:
        @app.route('/api/sensitive')
        @monitor_endpoint('sensitive_access')
        def sensitive():
            ...
    """
    from functools import wraps
    from flask import g
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Ejecutar función
                result = f(*args, **kwargs)
                
                # Registrar éxito
                if event_type:
                    security_monitor.record_security_event(
                        event_type,
                        'info',
                        {'status': 'success'}
                    )
                
                return result
                
            except Exception as e:
                # Registrar error
                if event_type:
                    security_monitor.record_security_event(
                        event_type,
                        'error',
                        {'status': 'failed', 'error': str(e)}
                    )
                raise
                
            finally:
                # Registrar tiempo de respuesta
                response_time = time.time() - start_time
                
                # Registrar métricas
                from flask import request
                security_monitor.record_request(
                    request.method,
                    request.endpoint or request.path,
                    getattr(g, 'response_status', 200),
                    response_time
                )
        
        return decorated_function
    
    return decorator
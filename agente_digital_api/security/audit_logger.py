"""
audit_logger.py - Sistema de auditoría y logging de seguridad
=========================================================

Este módulo implementa un sistema completo de auditoría para registrar
todas las acciones de seguridad y eventos importantes en la aplicación.

Características:
- Logging estructurado de eventos
- Trazabilidad completa de acciones
- Almacenamiento seguro de logs
- Análisis de patrones sospechosos
- Cumplimiento normativo (GDPR, etc)
- Integración con SIEM
"""

import os
import json
import time
import hashlib
import gzip
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import threading
import queue
from flask import request, g, current_app
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

class AuditLogger:
    """
    Sistema centralizado de auditoría y logging de seguridad
    """
    
    def __init__(self, app=None):
        self.app = app
        self.config = {
            'ENABLE_AUDIT': os.getenv('ENABLE_AUDIT_LOGGING', 'true').lower() == 'true',
            'LOG_LEVEL': os.getenv('AUDIT_LOG_LEVEL', 'INFO'),
            'LOG_DIR': os.getenv('AUDIT_LOG_DIR', 'logs/audit'),
            'LOG_FILE': os.getenv('AUDIT_LOG_FILE', 'security_audit.log'),
            'MAX_FILE_SIZE': int(os.getenv('AUDIT_MAX_FILE_SIZE', 10 * 1024 * 1024)),  # 10MB
            'BACKUP_COUNT': int(os.getenv('AUDIT_BACKUP_COUNT', 30)),
            'COMPRESS_LOGS': os.getenv('AUDIT_COMPRESS_LOGS', 'true').lower() == 'true',
            'ASYNC_LOGGING': os.getenv('AUDIT_ASYNC_LOGGING', 'true').lower() == 'true',
            'BUFFER_SIZE': int(os.getenv('AUDIT_BUFFER_SIZE', 1000)),
            'FLUSH_INTERVAL': int(os.getenv('AUDIT_FLUSH_INTERVAL', 5)),
            'INCLUDE_REQUEST_BODY': os.getenv('AUDIT_REQUEST_BODY', 'false').lower() == 'true',
            'SENSITIVE_FIELDS': os.getenv('AUDIT_SENSITIVE_FIELDS', 'password,token,secret,key,ssn,card').split(','),
            'RETENTION_DAYS': int(os.getenv('AUDIT_RETENTION_DAYS', 90))
        }
        
        # Logger específico para auditoría
        self.logger = None
        
        # Cola para logging asíncrono
        self.log_queue = queue.Queue(maxsize=self.config['BUFFER_SIZE'])
        self.worker_thread = None
        
        # Estadísticas
        self.stats = {
            'events_logged': 0,
            'events_dropped': 0,
            'last_flush': time.time()
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa el sistema de auditoría con la aplicación"""
        self.app = app
        
        if not self.config['ENABLE_AUDIT']:
            return
        
        # Crear directorio de logs
        Path(self.config['LOG_DIR']).mkdir(parents=True, exist_ok=True)
        
        # Configurar logger
        self._setup_logger()
        
        # Iniciar worker thread si es asíncrono
        if self.config['ASYNC_LOGGING']:
            self._start_worker_thread()
        
        # Registrar handlers
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        
        # Limpiar logs antiguos al inicio
        self._cleanup_old_logs()
    
    def _setup_logger(self):
        """Configura el logger de auditoría"""
        self.logger = logging.getLogger('security_audit')
        self.logger.setLevel(getattr(logging, self.config['LOG_LEVEL']))
        
        # Remover handlers existentes
        self.logger.handlers = []
        
        # Handler principal con rotación
        log_path = os.path.join(self.config['LOG_DIR'], self.config['LOG_FILE'])
        
        # Usar TimedRotatingFileHandler para rotación diaria
        handler = TimedRotatingFileHandler(
            log_path,
            when='midnight',
            interval=1,
            backupCount=self.config['BACKUP_COUNT']
        )
        
        # Formato estructurado
        formatter = logging.Formatter('%(message)s')  # Solo el mensaje JSON
        handler.setFormatter(formatter)
        
        # Comprimir logs rotados si está habilitado
        if self.config['COMPRESS_LOGS']:
            handler.rotator = self._compress_rotator
        
        self.logger.addHandler(handler)
        
        # Handler adicional para eventos críticos
        critical_handler = logging.FileHandler(
            os.path.join(self.config['LOG_DIR'], 'critical_events.log')
        )
        critical_handler.setLevel(logging.ERROR)
        critical_handler.setFormatter(formatter)
        self.logger.addHandler(critical_handler)
    
    def log_event(self, event_type: str, details: Dict[str, Any],
                  severity: str = 'INFO', user_id: Optional[str] = None):
        """
        Registra un evento de auditoría
        
        Args:
            event_type: Tipo de evento (login, access_denied, etc)
            details: Detalles del evento
            severity: Nivel de severidad
            user_id: ID del usuario (opcional)
        """
        if not self.config['ENABLE_AUDIT']:
            return
        
        # Construir evento
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'details': self._sanitize_data(details),
            'metadata': self._get_request_metadata(),
            'user_id': user_id or self._get_current_user_id(),
            'session_id': self._get_session_id(),
            'correlation_id': self._get_correlation_id(),
            'host': os.uname().nodename,
            'process_id': os.getpid()
        }
        
        # Calcular hash para integridad
        event['integrity_hash'] = self._calculate_event_hash(event)
        
        # Logging asíncrono o síncrono
        if self.config['ASYNC_LOGGING']:
            try:
                self.log_queue.put_nowait(event)
            except queue.Full:
                self.stats['events_dropped'] += 1
                # Log crítico si se pierden eventos
                self._emergency_log(event)
        else:
            self._write_event(event)
        
        self.stats['events_logged'] += 1
    
    def _before_request(self):
        """Handler antes de cada request"""
        # Establecer correlation ID para trazabilidad
        g.correlation_id = self._generate_correlation_id()
        g.request_start_time = time.time()
    
    def _after_request(self, response):
        """Handler después de cada request"""
        # Log de acceso automático
        if hasattr(g, 'skip_audit_log'):
            return response
        
        # Calcular duración
        duration = time.time() - g.get('request_start_time', time.time())
        
        # Determinar si es un evento de seguridad
        is_security_event = (
            response.status_code == 403 or  # Forbidden
            response.status_code == 401 or  # Unauthorized
            request.path.startswith('/api/auth') or
            request.path.startswith('/api/login')
        )
        
        if is_security_event:
            self.log_event(
                'http_request',
                {
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration_ms': int(duration * 1000),
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent'),
                    'referer': request.headers.get('Referer')
                },
                severity='WARNING' if response.status_code >= 400 else 'INFO'
            )
        
        return response
    
    def _sanitize_data(self, data: Any) -> Any:
        """Sanitiza datos removiendo información sensible"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if any(field in key.lower() for field in self.config['SENSITIVE_FIELDS']):
                    sanitized[key] = '[REDACTED]'
                else:
                    sanitized[key] = self._sanitize_data(value)
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        else:
            return data
    
    def _get_request_metadata(self) -> Dict[str, Any]:
        """Obtiene metadata de la request actual"""
        if not request:
            return {}
        
        metadata = {
            'ip_address': request.remote_addr,
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.args),
            'headers': {
                'User-Agent': request.headers.get('User-Agent'),
                'Accept': request.headers.get('Accept'),
                'Accept-Language': request.headers.get('Accept-Language'),
                'X-Forwarded-For': request.headers.get('X-Forwarded-For')
            }
        }
        
        # Incluir body si está configurado
        if self.config['INCLUDE_REQUEST_BODY'] and request.is_json:
            metadata['body'] = self._sanitize_data(request.get_json())
        
        return metadata
    
    def _get_current_user_id(self) -> Optional[str]:
        """Obtiene el ID del usuario actual"""
        # Intentar múltiples fuentes
        if hasattr(g, 'current_user_id'):
            return str(g.current_user_id)
        elif hasattr(g, 'user'):
            return str(getattr(g.user, 'id', None))
        elif 'user_id' in session:
            return str(session['user_id'])
        return None
    
    def _get_session_id(self) -> Optional[str]:
        """Obtiene el ID de sesión"""
        from flask import session
        return session.get('session_id') or session.get('_id')
    
    def _get_correlation_id(self) -> str:
        """Obtiene o genera correlation ID"""
        if hasattr(g, 'correlation_id'):
            return g.correlation_id
        return self._generate_correlation_id()
    
    def _generate_correlation_id(self) -> str:
        """Genera un ID único para correlación"""
        import uuid
        return str(uuid.uuid4())
    
    def _calculate_event_hash(self, event: Dict[str, Any]) -> str:
        """Calcula hash de integridad del evento"""
        # Crear copia sin el hash
        event_copy = event.copy()
        event_copy.pop('integrity_hash', None)
        
        # Serializar de forma determinística
        event_str = json.dumps(event_copy, sort_keys=True)
        
        # Calcular hash
        return hashlib.sha256(event_str.encode()).hexdigest()
    
    def _write_event(self, event: Dict[str, Any]):
        """Escribe evento al log"""
        try:
            # Determinar nivel de log
            level = getattr(logging, event['severity'])
            
            # Escribir como JSON
            self.logger.log(level, json.dumps(event))
            
        except Exception as e:
            # Fallback a stderr
            import sys
            print(f"AUDIT_ERROR: {e}", file=sys.stderr)
            print(json.dumps(event), file=sys.stderr)
    
    def _start_worker_thread(self):
        """Inicia thread para logging asíncrono"""
        def worker():
            buffer = []
            last_flush = time.time()
            
            while True:
                try:
                    # Obtener eventos con timeout
                    timeout = self.config['FLUSH_INTERVAL']
                    event = self.log_queue.get(timeout=timeout)
                    
                    if event is None:  # Señal de parada
                        break
                    
                    buffer.append(event)
                    
                    # Flush si el buffer está lleno o ha pasado tiempo
                    should_flush = (
                        len(buffer) >= 100 or
                        time.time() - last_flush >= self.config['FLUSH_INTERVAL']
                    )
                    
                    if should_flush:
                        self._flush_buffer(buffer)
                        buffer = []
                        last_flush = time.time()
                        
                except queue.Empty:
                    # Timeout - hacer flush si hay eventos
                    if buffer:
                        self._flush_buffer(buffer)
                        buffer = []
                        last_flush = time.time()
                        
                except Exception as e:
                    print(f"Audit worker error: {e}")
        
        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()
    
    def _flush_buffer(self, buffer: List[Dict[str, Any]]):
        """Escribe buffer de eventos al log"""
        for event in buffer:
            self._write_event(event)
        
        self.stats['last_flush'] = time.time()
    
    def _emergency_log(self, event: Dict[str, Any]):
        """Log de emergencia cuando falla el sistema principal"""
        emergency_path = os.path.join(self.config['LOG_DIR'], 'emergency.log')
        
        with open(emergency_path, 'a') as f:
            f.write(json.dumps(event) + '\n')
    
    def _compress_rotator(self, source, dest):
        """Comprime logs rotados"""
        with open(source, 'rb') as f_in:
            with gzip.open(f"{dest}.gz", 'wb') as f_out:
                f_out.writelines(f_in)
        os.remove(source)
    
    def _cleanup_old_logs(self):
        """Elimina logs antiguos según retención"""
        log_dir = Path(self.config['LOG_DIR'])
        cutoff_date = datetime.now() - timedelta(days=self.config['RETENTION_DAYS'])
        
        for log_file in log_dir.glob('*.log*'):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                try:
                    log_file.unlink()
                except:
                    pass
    
    # Métodos específicos para eventos comunes
    
    def log_authentication(self, success: bool, username: str, 
                          method: str = 'password', details: Dict = None):
        """Log de intento de autenticación"""
        self.log_event(
            'authentication',
            {
                'success': success,
                'username': username,
                'method': method,
                'details': details or {}
            },
            severity='INFO' if success else 'WARNING'
        )
    
    def log_authorization(self, resource: str, action: str, 
                         allowed: bool, reason: str = None):
        """Log de decisión de autorización"""
        self.log_event(
            'authorization',
            {
                'resource': resource,
                'action': action,
                'allowed': allowed,
                'reason': reason
            },
            severity='INFO' if allowed else 'WARNING'
        )
    
    def log_data_access(self, entity: str, entity_id: Any, 
                       action: str, fields: List[str] = None):
        """Log de acceso a datos"""
        self.log_event(
            'data_access',
            {
                'entity': entity,
                'entity_id': str(entity_id),
                'action': action,
                'fields': fields or []
            }
        )
    
    def log_security_event(self, event_name: str, threat_level: str,
                          details: Dict[str, Any]):
        """Log de evento de seguridad específico"""
        severity_map = {
            'low': 'INFO',
            'medium': 'WARNING',
            'high': 'ERROR',
            'critical': 'CRITICAL'
        }
        
        self.log_event(
            f'security_{event_name}',
            details,
            severity=severity_map.get(threat_level, 'WARNING')
        )
    
    def log_configuration_change(self, setting: str, old_value: Any, 
                               new_value: Any):
        """Log de cambio de configuración"""
        self.log_event(
            'configuration_change',
            {
                'setting': setting,
                'old_value': str(old_value),
                'new_value': str(new_value)
            },
            severity='WARNING'
        )
    
    def search_logs(self, filters: Dict[str, Any], 
                   limit: int = 100) -> List[Dict[str, Any]]:
        """
        Busca eventos en los logs
        
        Args:
            filters: Filtros de búsqueda
            limit: Límite de resultados
            
        Returns:
            Lista de eventos que coinciden
        """
        results = []
        
        # Por simplicidad, buscar en el log actual
        log_path = os.path.join(self.config['LOG_DIR'], self.config['LOG_FILE'])
        
        if not os.path.exists(log_path):
            return results
        
        with open(log_path, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    
                    # Aplicar filtros
                    match = True
                    for key, value in filters.items():
                        if key not in event or event[key] != value:
                            match = False
                            break
                    
                    if match:
                        results.append(event)
                        
                    if len(results) >= limit:
                        break
                        
                except:
                    continue
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de auditoría"""
        return {
            'events_logged': self.stats['events_logged'],
            'events_dropped': self.stats['events_dropped'],
            'queue_size': self.log_queue.qsize() if self.config['ASYNC_LOGGING'] else 0,
            'last_flush': datetime.fromtimestamp(self.stats['last_flush']).isoformat()
        }
    
    def shutdown(self):
        """Cierra el sistema de auditoría de forma segura"""
        if self.config['ASYNC_LOGGING'] and self.worker_thread:
            # Señal de parada
            self.log_queue.put(None)
            self.worker_thread.join(timeout=5)
        
        # Cerrar handlers
        if self.logger:
            for handler in self.logger.handlers:
                handler.close()


# Instancia global
audit_logger = AuditLogger()


# Decorador para auditar funciones
def audit_action(action: str, resource: str = None):
    """
    Decorador para auditar acciones automáticamente
    
    Uso:
        @audit_action('delete_user', 'user')
        def delete_user(user_id):
            ...
    """
    from functools import wraps
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Log antes de la acción
            audit_logger.log_event(
                f'{action}_attempt',
                {
                    'function': f.__name__,
                    'args': str(args)[:100],  # Limitar longitud
                    'resource': resource
                }
            )
            
            try:
                # Ejecutar función
                result = f(*args, **kwargs)
                
                # Log exitoso
                audit_logger.log_event(
                    f'{action}_success',
                    {
                        'function': f.__name__,
                        'resource': resource
                    }
                )
                
                return result
                
            except Exception as e:
                # Log de error
                audit_logger.log_event(
                    f'{action}_failed',
                    {
                        'function': f.__name__,
                        'resource': resource,
                        'error': str(e)
                    },
                    severity='ERROR'
                )
                raise
        
        return decorated_function
    
    return decorator
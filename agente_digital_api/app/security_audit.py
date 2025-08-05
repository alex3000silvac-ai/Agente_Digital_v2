# app/security_audit.py
# Sistema de auditoría y logging de seguridad para Agente Digital

import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from functools import wraps
from flask import request, g, current_app
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
import time

class AuditEventType(Enum):
    """Tipos de eventos de auditoría"""
    # Autenticación
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_VERIFICATION = "mfa_verification"
    
    # Autorización
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_ESCALATION = "permission_escalation"
    
    # Datos
    DATA_CREATE = "data_create"
    DATA_READ = "data_read"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    
    # Sistema
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    CONFIG_CHANGE = "config_change"
    
    # Seguridad
    SECURITY_VIOLATION = "security_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    
    # Archivos
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    FILE_DELETE = "file_delete"
    FILE_QUARANTINE = "file_quarantine"

class AuditSeverity(Enum):
    """Niveles de severidad para eventos de auditoría"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AuditEvent:
    """Estructura de un evento de auditoría"""
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    severity: AuditSeverity
    user_id: Optional[int]
    username: Optional[str]
    ip_address: str
    user_agent: str
    endpoint: str
    method: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    result: str  # success, failed, denied
    details: Dict[str, Any]
    session_id: Optional[str]
    request_id: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        return data

class SecurityLogger:
    """Logger especializado para eventos de seguridad"""
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file or os.environ.get('AUDIT_LOG_FILE', '/home/agentedigital/logs/security_audit.log')
        self.logger = self._setup_logger()
        self._ensure_log_directory()
    
    def _setup_logger(self) -> logging.Logger:
        """Configurar logger de seguridad"""
        logger = logging.getLogger('security_audit')
        logger.setLevel(logging.INFO)
        
        # Evitar duplicar handlers
        if logger.handlers:
            return logger
        
        # Handler para archivo
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10
        )
        
        # Formato específico para auditoría
        formatter = logging.Formatter(
            '%(asctime)s|%(levelname)s|AUDIT|%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        
        # Handler para consola en desarrollo
        if os.environ.get('FLASK_ENV') == 'development':
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def _ensure_log_directory(self):
        """Asegurar que el directorio de logs existe"""
        log_dir = os.path.dirname(self.log_file)
        os.makedirs(log_dir, exist_ok=True)
    
    def log_event(self, event: AuditEvent):
        """Registrar evento de auditoría"""
        try:
            # Convertir evento a JSON
            event_data = event.to_dict()
            log_message = json.dumps(event_data, ensure_ascii=False)
            
            # Determinar nivel de log según severidad
            if event.severity == AuditSeverity.CRITICAL:
                self.logger.critical(log_message)
            elif event.severity == AuditSeverity.HIGH:
                self.logger.error(log_message)
            elif event.severity == AuditSeverity.MEDIUM:
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)
                
        except Exception as e:
            # Log error but don't fail the original operation
            self.logger.error(f"Failed to log audit event: {e}")

class AsyncAuditLogger:
    """Logger de auditoría asíncrono para mejor performance"""
    
    def __init__(self, max_queue_size: int = 1000):
        self.security_logger = SecurityLogger()
        self.event_queue = queue.Queue(maxsize=max_queue_size)
        self.worker_thread = None
        self.running = False
        self.start_worker()
    
    def start_worker(self):
        """Iniciar worker thread para procesar eventos"""
        if self.worker_thread and self.worker_thread.is_alive():
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_events, daemon=True)
        self.worker_thread.start()
    
    def stop_worker(self):
        """Detener worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def _process_events(self):
        """Procesar eventos de la cola"""
        while self.running:
            try:
                # Obtener evento con timeout
                event = self.event_queue.get(timeout=1)
                self.security_logger.log_event(event)
                self.event_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error processing audit event: {e}")
    
    def log_event_async(self, event: AuditEvent):
        """Registrar evento de forma asíncrona"""
        try:
            self.event_queue.put_nowait(event)
        except queue.Full:
            # Si la cola está llena, log síncrono como fallback
            self.security_logger.log_event(event)

class AuditManager:
    """Gestor principal de auditoría"""
    
    def __init__(self):
        self.async_logger = AsyncAuditLogger()
        self.enabled = os.environ.get('AUDIT_LOG_ENABLED', 'true').lower() == 'true'
        self.sensitive_fields = {'password', 'token', 'secret', 'key', 'auth'}
    
    def _generate_event_id(self) -> str:
        """Generar ID único para evento"""
        timestamp = str(int(time.time() * 1000000))  # microseconds
        return hashlib.sha256(timestamp.encode()).hexdigest()[:16]
    
    def _get_request_info(self) -> Dict[str, str]:
        """Obtener información de la request actual"""
        return {
            'ip_address': self._get_client_ip(),
            'user_agent': request.headers.get('User-Agent', ''),
            'endpoint': request.endpoint or request.path,
            'method': request.method,
            'session_id': getattr(g, 'session_id', None),
            'request_id': getattr(g, 'request_id', None)
        }
    
    def _get_client_ip(self) -> str:
        """Obtener IP real del cliente"""
        # Considerar proxies
        if request.environ.get('HTTP_X_FORWARDED_FOR'):
            return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
        elif request.environ.get('HTTP_X_REAL_IP'):
            return request.environ['HTTP_X_REAL_IP']
        else:
            return request.environ.get('REMOTE_ADDR', 'unknown')
    
    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitizar detalles removiendo información sensible"""
        sanitized = {}
        
        for key, value in details.items():
            key_lower = key.lower()
            
            # Redactar campos sensibles
            if any(sensitive in key_lower for sensitive in self.sensitive_fields):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_details(value)
            elif isinstance(value, str) and len(value) > 1000:
                # Truncar strings muy largos
                sanitized[key] = value[:1000] + '...[TRUNCATED]'
            else:
                sanitized[key] = value
        
        return sanitized
    
    def log_event(self, 
                  event_type: AuditEventType,
                  severity: AuditSeverity,
                  action: str,
                  result: str,
                  details: Dict[str, Any] = None,
                  resource_type: str = None,
                  resource_id: str = None,
                  user_id: int = None,
                  username: str = None):
        """
        Registrar evento de auditoría
        
        Args:
            event_type: Tipo de evento
            severity: Severidad del evento
            action: Acción realizada
            result: Resultado de la acción
            details: Detalles adicionales
            resource_type: Tipo de recurso afectado
            resource_id: ID del recurso afectado
            user_id: ID del usuario (opcional)
            username: Nombre del usuario (opcional)
        """
        if not self.enabled:
            return
        
        try:
            # Obtener información del usuario actual si no se proporciona
            if user_id is None and hasattr(g, 'current_user'):
                user_data = g.current_user
                user_id = user_data.get('user_id')
                username = user_data.get('username')
            
            # Obtener información de la request
            request_info = self._get_request_info()
            
            # Sanitizar detalles
            sanitized_details = self._sanitize_details(details or {})
            
            # Crear evento
            event = AuditEvent(
                event_id=self._generate_event_id(),
                timestamp=datetime.now(),
                event_type=event_type,
                severity=severity,
                user_id=user_id,
                username=username,
                ip_address=request_info['ip_address'],
                user_agent=request_info['user_agent'],
                endpoint=request_info['endpoint'],
                method=request_info['method'],
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                result=result,
                details=sanitized_details,
                session_id=request_info['session_id'],
                request_id=request_info['request_id']
            )
            
            # Registrar evento
            self.async_logger.log_event_async(event)
            
        except Exception as e:
            logging.error(f"Error creating audit event: {e}")
    
    def log_authentication_event(self, 
                                event_type: AuditEventType,
                                username: str,
                                result: str,
                                details: Dict[str, Any] = None):
        """Registrar evento de autenticación"""
        severity = AuditSeverity.HIGH if result == 'failed' else AuditSeverity.MEDIUM
        
        self.log_event(
            event_type=event_type,
            severity=severity,
            action='authenticate',
            result=result,
            details=details,
            username=username,
            resource_type='user_session'
        )
    
    def log_data_access_event(self,
                             operation: str,
                             resource_type: str,
                             resource_id: str,
                             result: str,
                             details: Dict[str, Any] = None):
        """Registrar evento de acceso a datos"""
        event_type_map = {
            'create': AuditEventType.DATA_CREATE,
            'read': AuditEventType.DATA_READ,
            'update': AuditEventType.DATA_UPDATE,
            'delete': AuditEventType.DATA_DELETE,
            'export': AuditEventType.DATA_EXPORT
        }
        
        event_type = event_type_map.get(operation, AuditEventType.DATA_READ)
        severity = AuditSeverity.HIGH if operation in ['delete', 'export'] else AuditSeverity.MEDIUM
        
        self.log_event(
            event_type=event_type,
            severity=severity,
            action=operation,
            result=result,
            details=details,
            resource_type=resource_type,
            resource_id=resource_id
        )
    
    def log_security_event(self,
                          event_type: AuditEventType,
                          severity: AuditSeverity,
                          details: Dict[str, Any] = None):
        """Registrar evento de seguridad"""
        self.log_event(
            event_type=event_type,
            severity=severity,
            action='security_check',
            result='violation_detected',
            details=details,
            resource_type='security'
        )

# Decoradores para auditoría automática
def audit_data_access(operation: str, resource_type: str):
    """Decorador para auditar acceso a datos"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            resource_id = None
            result = 'success'
            error_details = {}
            
            try:
                # Intentar extraer resource_id de los argumentos
                if 'id' in kwargs:
                    resource_id = str(kwargs['id'])
                elif args and len(args) > 0:
                    resource_id = str(args[0])
                
                # Ejecutar función original
                response = func(*args, **kwargs)
                
                # Determinar si fue exitoso basado en la respuesta
                if hasattr(response, 'status_code') and response.status_code >= 400:
                    result = 'failed'
                
                return response
                
            except Exception as e:
                result = 'failed'
                error_details = {'error': str(e), 'error_type': type(e).__name__}
                raise
            
            finally:
                # Registrar evento de auditoría
                audit_manager = get_audit_manager()
                audit_manager.log_data_access_event(
                    operation=operation,
                    resource_type=resource_type,
                    resource_id=resource_id or 'unknown',
                    result=result,
                    details=error_details
                )
        
        return wrapper
    return decorator

def audit_authentication(event_type: AuditEventType):
    """Decorador para auditar eventos de autenticación"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            username = None
            result = 'success'
            details = {}
            
            try:
                # Intentar extraer username de request o argumentos
                if request.is_json:
                    request_data = request.get_json() or {}
                    username = request_data.get('username') or request_data.get('email')
                
                # Ejecutar función original
                response = func(*args, **kwargs)
                
                # Determinar resultado
                if hasattr(response, 'status_code') and response.status_code >= 400:
                    result = 'failed'
                    if hasattr(response, 'get_json'):
                        error_data = response.get_json()
                        details['error'] = error_data.get('error', 'Authentication failed')
                
                return response
                
            except Exception as e:
                result = 'failed'
                details = {'error': str(e)}
                raise
            
            finally:
                # Registrar evento
                audit_manager = get_audit_manager()
                audit_manager.log_authentication_event(
                    event_type=event_type,
                    username=username or 'unknown',
                    result=result,
                    details=details
                )
        
        return wrapper
    return decorator

# Instancia global del gestor de auditoría
_audit_manager = None

def init_audit_system():
    """Inicializar sistema de auditoría"""
    global _audit_manager
    try:
        _audit_manager = AuditManager()
        logging.info("Audit system initialized successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to initialize audit system: {e}")
        return False

def get_audit_manager() -> AuditManager:
    """Obtener instancia del gestor de auditoría"""
    if _audit_manager is None:
        init_audit_system()
    return _audit_manager

def cleanup_audit_system():
    """Limpiar sistema de auditoría al cerrar aplicación"""
    if _audit_manager:
        _audit_manager.async_logger.stop_worker()

# Funciones de conveniencia
def log_login_attempt(username: str, success: bool, details: Dict[str, Any] = None):
    """Registrar intento de login"""
    audit_manager = get_audit_manager()
    event_type = AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILED
    result = 'success' if success else 'failed'
    
    audit_manager.log_authentication_event(event_type, username, result, details)

def log_security_violation(violation_type: str, details: Dict[str, Any] = None):
    """Registrar violación de seguridad"""
    audit_manager = get_audit_manager()
    
    event_type_map = {
        'sql_injection': AuditEventType.SQL_INJECTION_ATTEMPT,
        'xss': AuditEventType.XSS_ATTEMPT,
        'rate_limit': AuditEventType.RATE_LIMIT_EXCEEDED,
        'suspicious': AuditEventType.SUSPICIOUS_ACTIVITY
    }
    
    event_type = event_type_map.get(violation_type, AuditEventType.SECURITY_VIOLATION)
    
    audit_manager.log_security_event(
        event_type=event_type,
        severity=AuditSeverity.HIGH,
        details=details or {'violation_type': violation_type}
    )
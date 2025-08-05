"""
error_handler.py - Manejo seguro de errores y excepciones
======================================================

Este módulo implementa un sistema de manejo de errores que previene
la exposición de información sensible y proporciona respuestas seguras.

Características:
- Respuestas de error seguras
- Ocultación de stack traces en producción
- Logging detallado de errores
- Mensajes de error personalizados
- Prevención de información leakage
- Manejo de errores específicos de seguridad
"""

import os
import sys
import traceback
import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from flask import request, jsonify, render_template, current_app
from werkzeug.exceptions import HTTPException
import logging

class SecureErrorHandler:
    """
    Sistema de manejo seguro de errores
    """
    
    def __init__(self, app=None):
        self.app = app
        self.config = {
            'DEBUG_MODE': os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
            'SHOW_ERRORS': os.getenv('SHOW_ERROR_DETAILS', 'false').lower() == 'true',
            'LOG_ERRORS': os.getenv('LOG_ERRORS', 'true').lower() == 'true',
            'ERROR_PAGE_TEMPLATE': os.getenv('ERROR_PAGE_TEMPLATE', 'error.html'),
            'API_ERROR_FORMAT': os.getenv('API_ERROR_FORMAT', 'json'),
            'INCLUDE_REQUEST_ID': os.getenv('INCLUDE_REQUEST_ID', 'true').lower() == 'true',
            'MASK_SENSITIVE_DATA': os.getenv('MASK_SENSITIVE_DATA', 'true').lower() == 'true',
            'ERROR_CONTACT_EMAIL': os.getenv('ERROR_CONTACT_EMAIL', 'support@example.com'),
            'MAX_ERROR_DETAIL_LENGTH': int(os.getenv('MAX_ERROR_DETAIL_LENGTH', 500))
        }
        
        # Mensajes de error seguros por código
        self.safe_messages = {
            400: "La solicitud no pudo ser procesada debido a datos inválidos.",
            401: "Autenticación requerida para acceder a este recurso.",
            403: "No tiene permisos para acceder a este recurso.",
            404: "El recurso solicitado no fue encontrado.",
            405: "Método no permitido para este recurso.",
            409: "Conflicto al procesar la solicitud.",
            422: "Los datos proporcionados no pudieron ser procesados.",
            429: "Demasiadas solicitudes. Por favor, intente más tarde.",
            500: "Error interno del servidor. Por favor, contacte al administrador.",
            502: "Error de puerta de enlace. El servicio no está disponible temporalmente.",
            503: "Servicio no disponible. Por favor, intente más tarde."
        }
        
        # Logger específico para errores
        self.error_logger = logging.getLogger('secure_errors')
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa el manejo de errores con la aplicación"""
        self.app = app
        
        # Registrar manejadores de error
        self._register_error_handlers(app)
        
        # Configurar logger
        self._setup_error_logger()
    
    def _register_error_handlers(self, app):
        """Registra manejadores para diferentes tipos de errores"""
        # Errores HTTP comunes
        for code in [400, 401, 403, 404, 405, 409, 422, 429, 500, 502, 503]:
            app.register_error_handler(code, self.handle_http_error)
        
        # Excepciones específicas
        app.register_error_handler(Exception, self.handle_exception)
        app.register_error_handler(HTTPException, self.handle_http_exception)
        
        # Errores de validación
        app.register_error_handler(ValueError, self.handle_validation_error)
        app.register_error_handler(TypeError, self.handle_validation_error)
        
        # Errores de base de datos
        try:
            import pyodbc
            app.register_error_handler(pyodbc.Error, self.handle_database_error)
        except ImportError:
            pass
        
        # Errores de autenticación JWT
        try:
            import jwt
            app.register_error_handler(jwt.InvalidTokenError, self.handle_jwt_error)
        except ImportError:
            pass
    
    def _setup_error_logger(self):
        """Configura logger específico para errores"""
        if not self.config['LOG_ERRORS']:
            return
        
        # Configurar formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Handler para archivo
        error_log_path = os.path.join('logs', 'errors.log')
        os.makedirs(os.path.dirname(error_log_path), exist_ok=True)
        
        file_handler = logging.FileHandler(error_log_path)
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(formatter)
        
        self.error_logger.addHandler(file_handler)
        self.error_logger.setLevel(logging.ERROR)
    
    def handle_http_error(self, error):
        """Maneja errores HTTP específicos"""
        status_code = error.code if hasattr(error, 'code') else 500
        
        # Log del error
        self._log_error(error, status_code)
        
        # Generar respuesta segura
        return self._create_error_response(
            status_code=status_code,
            message=self.safe_messages.get(status_code, "Error procesando la solicitud."),
            error_type='http_error'
        )
    
    def handle_http_exception(self, error: HTTPException):
        """Maneja excepciones HTTP de Werkzeug"""
        # Log del error
        self._log_error(error, error.code)
        
        # Usar mensaje personalizado o el seguro
        message = self.safe_messages.get(
            error.code,
            error.description if self.config['SHOW_ERRORS'] else "Error procesando la solicitud."
        )
        
        return self._create_error_response(
            status_code=error.code,
            message=message,
            error_type='http_exception'
        )
    
    def handle_exception(self, error: Exception):
        """Maneja excepciones generales no capturadas"""
        # Log completo del error
        self._log_error(error, 500, include_traceback=True)
        
        # Determinar si mostrar detalles
        if self.config['DEBUG_MODE'] and self.config['SHOW_ERRORS']:
            message = str(error)
            details = {
                'exception_type': type(error).__name__,
                'traceback': traceback.format_exc()
            }
        else:
            message = self.safe_messages.get(500)
            details = None
        
        return self._create_error_response(
            status_code=500,
            message=message,
            error_type='internal_error',
            details=details
        )
    
    def handle_validation_error(self, error: Exception):
        """Maneja errores de validación"""
        # Log del error
        self._log_error(error, 422)
        
        # Mensaje seguro
        if self.config['SHOW_ERRORS']:
            message = f"Error de validación: {str(error)}"
        else:
            message = "Los datos proporcionados no son válidos."
        
        return self._create_error_response(
            status_code=422,
            message=message,
            error_type='validation_error'
        )
    
    def handle_database_error(self, error):
        """Maneja errores de base de datos"""
        # Log completo pero respuesta genérica
        self._log_error(error, 500, include_traceback=True)
        
        # NUNCA exponer detalles de DB
        return self._create_error_response(
            status_code=500,
            message="Error al procesar la operación en la base de datos.",
            error_type='database_error'
        )
    
    def handle_jwt_error(self, error):
        """Maneja errores de JWT"""
        # Log del error
        self._log_error(error, 401)
        
        # Mensaje específico pero seguro
        jwt_messages = {
            'ExpiredSignatureError': 'El token ha expirado.',
            'InvalidTokenError': 'Token inválido.',
            'DecodeError': 'Error al decodificar el token.'
        }
        
        error_name = type(error).__name__
        message = jwt_messages.get(error_name, "Error de autenticación.")
        
        return self._create_error_response(
            status_code=401,
            message=message,
            error_type='authentication_error'
        )
    
    def _create_error_response(self, status_code: int, message: str,
                             error_type: str, details: Optional[Dict] = None):
        """Crea una respuesta de error segura"""
        # Generar ID único para el error
        error_id = self._generate_error_id()
        
        # Construir respuesta base
        error_response = {
            'error': True,
            'message': self._sanitize_message(message),
            'type': error_type,
            'status_code': status_code
        }
        
        # Agregar ID si está configurado
        if self.config['INCLUDE_REQUEST_ID']:
            error_response['error_id'] = error_id
            error_response['timestamp'] = datetime.utcnow().isoformat()
        
        # Agregar detalles si están disponibles y permitidos
        if details and self.config['SHOW_ERRORS']:
            error_response['details'] = details
        
        # Agregar información de contacto para errores 5xx
        if status_code >= 500:
            error_response['contact'] = self.config['ERROR_CONTACT_EMAIL']
            error_response['support_message'] = (
                f"Si el problema persiste, contacte al soporte con el ID: {error_id}"
            )
        
        # Determinar formato de respuesta
        if self._is_api_request():
            response = jsonify(error_response)
            response.status_code = status_code
        else:
            # Intentar renderizar template HTML
            try:
                response = render_template(
                    self.config['ERROR_PAGE_TEMPLATE'],
                    error=error_response
                ), status_code
            except:
                # Fallback a JSON si falla el template
                response = jsonify(error_response)
                response.status_code = status_code
        
        # Agregar headers de seguridad
        response = self._add_security_headers(response)
        
        return response
    
    def _log_error(self, error: Exception, status_code: int,
                  include_traceback: bool = False):
        """Registra el error de forma segura"""
        if not self.config['LOG_ERRORS']:
            return
        
        # Construir entrada de log
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'status_code': status_code,
            'message': str(error),
            'request': {
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent')
            }
        }
        
        # Agregar usuario si está disponible
        if hasattr(g, 'current_user_id'):
            log_entry['user_id'] = g.current_user_id
        
        # Agregar traceback si es necesario
        if include_traceback:
            log_entry['traceback'] = traceback.format_exc()
        
        # Agregar datos de request (sanitizados)
        if request.is_json:
            try:
                log_entry['request']['body'] = self._sanitize_request_data(
                    request.get_json()
                )
            except:
                pass
        
        # Log según severidad
        if status_code >= 500:
            self.error_logger.error(json.dumps(log_entry))
        else:
            self.error_logger.warning(json.dumps(log_entry))
        
        # También log en aplicación principal
        if current_app:
            current_app.logger.error(f"Error {status_code}: {error}")
    
    def _sanitize_message(self, message: str) -> str:
        """Sanitiza mensaje de error para evitar leaks"""
        if not self.config['MASK_SENSITIVE_DATA']:
            return message
        
        # Lista de patrones sensibles
        sensitive_patterns = [
            r'password["\']?\s*[:=]\s*["\']?[\w\-\._~]+',
            r'token["\']?\s*[:=]\s*["\']?[\w\-\._~]+',
            r'api[_-]?key["\']?\s*[:=]\s*["\']?[\w\-\._~]+',
            r'secret["\']?\s*[:=]\s*["\']?[\w\-\._~]+',
            r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b',  # Tarjetas
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Emails
            r'Server\s+.*?@[\w\.\-]+',  # Conexiones DB
            r'/(home|usr|etc|var)/[\w/\.\-]+',  # Rutas del sistema
        ]
        
        import re
        sanitized = message
        
        for pattern in sensitive_patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        # Limitar longitud
        if len(sanitized) > self.config['MAX_ERROR_DETAIL_LENGTH']:
            sanitized = sanitized[:self.config['MAX_ERROR_DETAIL_LENGTH']] + '...'
        
        return sanitized
    
    def _sanitize_request_data(self, data: Any) -> Any:
        """Sanitiza datos de request para logging"""
        if isinstance(data, dict):
            sanitized = {}
            sensitive_keys = ['password', 'token', 'secret', 'key', 'ssn', 'card']
            
            for key, value in data.items():
                if any(s in key.lower() for s in sensitive_keys):
                    sanitized[key] = '[REDACTED]'
                else:
                    sanitized[key] = self._sanitize_request_data(value)
            
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_request_data(item) for item in data]
        else:
            return data
    
    def _generate_error_id(self) -> str:
        """Genera ID único para el error"""
        import uuid
        return f"ERR-{uuid.uuid4().hex[:8].upper()}"
    
    def _is_api_request(self) -> bool:
        """Determina si es una request de API"""
        # Verificar Accept header
        if request.headers.get('Accept', '').startswith('application/json'):
            return True
        
        # Verificar Content-Type
        if request.is_json:
            return True
        
        # Verificar ruta
        if request.path.startswith('/api/'):
            return True
        
        return False
    
    def _add_security_headers(self, response):
        """Agrega headers de seguridad a la respuesta de error"""
        # Prevenir caching de errores
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        # Headers de seguridad
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        
        return response
    
    def create_custom_error(self, message: str, status_code: int = 400,
                          error_code: str = None, details: Dict = None):
        """
        Crea un error personalizado
        
        Args:
            message: Mensaje de error
            status_code: Código HTTP
            error_code: Código de error específico de la aplicación
            details: Detalles adicionales
            
        Returns:
            Response de error
        """
        error_response = {
            'error': True,
            'message': self._sanitize_message(message),
            'status_code': status_code
        }
        
        if error_code:
            error_response['error_code'] = error_code
        
        if details and self.config['SHOW_ERRORS']:
            error_response['details'] = self._sanitize_request_data(details)
        
        if self.config['INCLUDE_REQUEST_ID']:
            error_response['error_id'] = self._generate_error_id()
            error_response['timestamp'] = datetime.utcnow().isoformat()
        
        response = jsonify(error_response)
        response.status_code = status_code
        
        return response


# Instancia global
secure_error_handler = SecureErrorHandler()


# Funciones helper para uso directo
def abort_secure(status_code: int, message: str = None, **kwargs):
    """
    Aborta con un error seguro
    
    Uso:
        abort_secure(403, "Acceso denegado", reason="insufficient_permissions")
    """
    if not message:
        message = secure_error_handler.safe_messages.get(
            status_code,
            "Error procesando la solicitud"
        )
    
    response = secure_error_handler.create_custom_error(
        message=message,
        status_code=status_code,
        details=kwargs
    )
    
    # Lanzar como excepción HTTP
    from werkzeug.exceptions import HTTPException
    error = HTTPException()
    error.code = status_code
    error.description = message
    error.get_response = lambda e: response
    
    raise error


def handle_error_gracefully(func):
    """
    Decorador para manejar errores de forma segura
    
    Uso:
        @handle_error_gracefully
        def risky_operation():
            ...
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPException:
            # Re-lanzar errores HTTP
            raise
        except Exception as e:
            # Log y convertir a error 500 seguro
            secure_error_handler._log_error(e, 500, include_traceback=True)
            abort_secure(500, "Error interno del servidor")
    
    return wrapper
"""
security_middleware.py - Middleware principal de seguridad
========================================================

Este módulo implementa el middleware central de seguridad que intercepta
todas las requests y aplica validaciones de seguridad antes de procesarlas.

Características:
- Validación de headers HTTP
- Prevención de ataques comunes
- Logging de seguridad
- Gestión de sesiones seguras
- Integración con otros módulos de seguridad
"""

import os
import time
import json
import hashlib
import hmac
from functools import wraps
from datetime import datetime, timedelta
from flask import request, g, abort, jsonify, current_app
from werkzeug.exceptions import BadRequest
import re
import ipaddress

class SecurityMiddleware:
    """
    Middleware principal que coordina todas las medidas de seguridad
    """
    
    def __init__(self, app=None):
        self.app = app
        self.config = {
            'ENABLE_SECURITY': os.getenv('ENABLE_SECURITY', 'true').lower() == 'true',
            'MAX_CONTENT_LENGTH': int(os.getenv('MAX_CONTENT_LENGTH', 10485760)),  # 10MB
            'ALLOWED_HOSTS': os.getenv('ALLOWED_HOSTS', '').split(','),
            'ALLOWED_METHODS': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD'],
            'SUSPICIOUS_PATTERNS': [
                r'<script', r'javascript:', r'onerror=', r'onclick=',
                r'\.\./', r'\.\.\\', r'%2e%2e', r'%252e',
                r'union\s+select', r'drop\s+table', r'insert\s+into',
                r'exec\s*\(', r'eval\s*\(', r'system\s*\(',
                r'/etc/passwd', r'/etc/shadow', r'cmd\.exe',
                r'\x00', r'\x1a', r'\x7f'
            ],
            'BLOCKED_USER_AGENTS': [
                'sqlmap', 'nikto', 'nessus', 'masscan', 'nmap'
            ]
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa el middleware con la aplicación Flask"""
        self.app = app
        
        # Registrar before_request handler
        app.before_request(self._before_request)
        
        # Registrar after_request handler
        app.after_request(self._after_request)
        
        # Registrar error handlers
        app.errorhandler(400)(self._handle_bad_request)
        app.errorhandler(403)(self._handle_forbidden)
        app.errorhandler(429)(self._handle_too_many_requests)
        
    def _before_request(self):
        """Ejecuta validaciones de seguridad antes de cada request"""
        
        if not self.config['ENABLE_SECURITY']:
            return
        
        # Timestamp de inicio para métricas
        g.request_start_time = time.time()
        
        # Validar método HTTP
        if request.method not in self.config['ALLOWED_METHODS']:
            self._log_security_event('invalid_method', {
                'method': request.method,
                'ip': self._get_client_ip()
            })
            abort(405)
        
        # Validar host header (prevenir Host Header Injection)
        if self.config['ALLOWED_HOSTS'] and request.host not in self.config['ALLOWED_HOSTS']:
            self._log_security_event('invalid_host', {
                'host': request.host,
                'ip': self._get_client_ip()
            })
            abort(400, 'Invalid host header')
        
        # Validar Content-Length
        if request.content_length and request.content_length > self.config['MAX_CONTENT_LENGTH']:
            self._log_security_event('oversized_request', {
                'size': request.content_length,
                'ip': self._get_client_ip()
            })
            abort(413, 'Request entity too large')
        
        # Validar User-Agent sospechoso
        user_agent = request.headers.get('User-Agent', '').lower()
        for blocked_agent in self.config['BLOCKED_USER_AGENTS']:
            if blocked_agent in user_agent:
                self._log_security_event('blocked_user_agent', {
                    'user_agent': user_agent,
                    'ip': self._get_client_ip()
                })
                abort(403, 'Forbidden')
        
        # Detectar patrones sospechosos en la URL
        full_path = request.full_path
        for pattern in self.config['SUSPICIOUS_PATTERNS']:
            if re.search(pattern, full_path, re.IGNORECASE):
                self._log_security_event('suspicious_pattern_url', {
                    'pattern': pattern,
                    'url': full_path,
                    'ip': self._get_client_ip()
                })
                abort(400, 'Bad request')
        
        # Detectar patrones sospechosos en headers
        for header_name, header_value in request.headers:
            header_str = f"{header_name}: {header_value}"
            for pattern in self.config['SUSPICIOUS_PATTERNS']:
                if re.search(pattern, header_str, re.IGNORECASE):
                    self._log_security_event('suspicious_pattern_header', {
                        'pattern': pattern,
                        'header': header_name,
                        'ip': self._get_client_ip()
                    })
                    abort(400, 'Bad request')
        
        # Validar request body si existe
        if request.is_json:
            try:
                data = request.get_json()
                self._validate_json_data(data)
            except Exception as e:
                self._log_security_event('invalid_json', {
                    'error': str(e),
                    'ip': self._get_client_ip()
                })
                abort(400, 'Invalid JSON')
        
        # Establecer información de seguridad en g
        g.client_ip = self._get_client_ip()
        g.request_id = self._generate_request_id()
        
    def _after_request(self, response):
        """Aplica headers de seguridad después de cada request"""
        
        if not self.config['ENABLE_SECURITY']:
            return response
        
        # Calcular tiempo de respuesta
        if hasattr(g, 'request_start_time'):
            response_time = (time.time() - g.request_start_time) * 1000
            response.headers['X-Response-Time'] = f"{response_time:.2f}ms"
        
        # Agregar request ID para trazabilidad
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        
        # Headers de seguridad serán manejados por headers_security.py
        
        return response
    
    def _validate_json_data(self, data, depth=0):
        """
        Valida recursivamente datos JSON contra patrones maliciosos
        
        Args:
            data: Datos a validar
            depth: Profundidad actual de recursión
        """
        MAX_DEPTH = 10
        
        if depth > MAX_DEPTH:
            raise ValueError("JSON too deeply nested")
        
        if isinstance(data, dict):
            for key, value in data.items():
                # Validar key
                if isinstance(key, str):
                    for pattern in self.config['SUSPICIOUS_PATTERNS']:
                        if re.search(pattern, key, re.IGNORECASE):
                            raise ValueError(f"Suspicious pattern in key: {key}")
                
                # Validar value recursivamente
                self._validate_json_data(value, depth + 1)
                
        elif isinstance(data, list):
            for item in data:
                self._validate_json_data(item, depth + 1)
                
        elif isinstance(data, str):
            # Validar strings contra patrones maliciosos
            for pattern in self.config['SUSPICIOUS_PATTERNS']:
                if re.search(pattern, data, re.IGNORECASE):
                    raise ValueError(f"Suspicious pattern in value")
    
    def _get_client_ip(self):
        """
        Obtiene la IP real del cliente considerando proxies
        
        Returns:
            str: IP del cliente
        """
        # Headers comunes usados por proxies
        headers = [
            'X-Forwarded-For',
            'X-Real-IP',
            'CF-Connecting-IP',  # Cloudflare
            'True-Client-IP',    # Akamai
            'X-Client-IP'
        ]
        
        for header in headers:
            ip = request.headers.get(header)
            if ip:
                # X-Forwarded-For puede contener múltiples IPs
                if ',' in ip:
                    ip = ip.split(',')[0].strip()
                
                # Validar que sea una IP válida
                try:
                    ipaddress.ip_address(ip)
                    return ip
                except ValueError:
                    continue
        
        # Fallback a remote_addr
        return request.remote_addr or 'unknown'
    
    def _generate_request_id(self):
        """
        Genera un ID único para la request
        
        Returns:
            str: Request ID único
        """
        # Combinar timestamp, IP y datos random
        data = f"{time.time()}-{self._get_client_ip()}-{os.urandom(8).hex()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _log_security_event(self, event_type, details):
        """
        Registra un evento de seguridad
        
        Args:
            event_type: Tipo de evento
            details: Detalles del evento
        """
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'details': details,
            'request_id': getattr(g, 'request_id', 'unknown'),
            'method': request.method,
            'path': request.path,
            'user_agent': request.headers.get('User-Agent', 'unknown')
        }
        
        # Log al sistema de auditoría
        if current_app:
            current_app.logger.warning(f"SECURITY_EVENT: {json.dumps(event)}")
    
    def _handle_bad_request(self, error):
        """Maneja errores 400 de forma segura"""
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server',
            'request_id': getattr(g, 'request_id', 'unknown')
        }), 400
    
    def _handle_forbidden(self, error):
        """Maneja errores 403 de forma segura"""
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource',
            'request_id': getattr(g, 'request_id', 'unknown')
        }), 403
    
    def _handle_too_many_requests(self, error):
        """Maneja errores 429 de forma segura"""
        return jsonify({
            'error': 'Too Many Requests',
            'message': 'Rate limit exceeded. Please try again later',
            'request_id': getattr(g, 'request_id', 'unknown')
        }), 429


def secure_endpoint(f):
    """
    Decorator para aplicar validaciones de seguridad adicionales a endpoints específicos
    
    Uso:
        @app.route('/api/sensitive')
        @secure_endpoint
        def sensitive_endpoint():
            return jsonify({'data': 'sensitive'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Validaciones adicionales específicas del endpoint
        
        # Verificar que el request viene de HTTPS en producción
        if os.getenv('FLASK_ENV') == 'production' and not request.is_secure:
            abort(403, 'HTTPS required')
        
        # Verificar Content-Type para POST/PUT
        if request.method in ['POST', 'PUT']:
            content_type = request.headers.get('Content-Type', '')
            if not content_type.startswith(('application/json', 'multipart/form-data')):
                abort(400, 'Invalid Content-Type')
        
        return f(*args, **kwargs)
    
    return decorated_function
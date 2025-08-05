"""
headers_security.py - Headers de seguridad HTTP
===========================================

Este módulo gestiona todos los headers de seguridad HTTP para proteger
la aplicación contra diversos vectores de ataque.

Características:
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options
- Permissions Policy
- Referrer Policy
"""

import os
from typing import Dict, Optional, List
from flask import Response, request, current_app

class SecurityHeaders:
    """
    Gestor de headers de seguridad HTTP
    """
    
    def __init__(self, app=None):
        self.app = app
        self.config = {
            'ENABLE_SECURITY_HEADERS': os.getenv('ENABLE_SECURITY_HEADERS', 'true').lower() == 'true',
            
            # Content Security Policy
            'CSP_ENABLED': os.getenv('CSP_ENABLED', 'true').lower() == 'true',
            'CSP_REPORT_ONLY': os.getenv('CSP_REPORT_ONLY', 'false').lower() == 'true',
            'CSP_REPORT_URI': os.getenv('CSP_REPORT_URI', '/api/csp-report'),
            
            # HSTS
            'HSTS_ENABLED': os.getenv('HSTS_ENABLED', 'true').lower() == 'true',
            'HSTS_MAX_AGE': int(os.getenv('HSTS_MAX_AGE', 31536000)),  # 1 año
            'HSTS_INCLUDE_SUBDOMAINS': os.getenv('HSTS_INCLUDE_SUBDOMAINS', 'true').lower() == 'true',
            'HSTS_PRELOAD': os.getenv('HSTS_PRELOAD', 'false').lower() == 'true',
            
            # Frame Options
            'FRAME_OPTIONS': os.getenv('X_FRAME_OPTIONS', 'DENY'),
            
            # Content Type Options
            'CONTENT_TYPE_NOSNIFF': os.getenv('X_CONTENT_TYPE_NOSNIFF', 'true').lower() == 'true',
            
            # XSS Protection (legacy pero aún útil)
            'XSS_PROTECTION': os.getenv('X_XSS_PROTECTION', '1; mode=block'),
            
            # Referrer Policy
            'REFERRER_POLICY': os.getenv('REFERRER_POLICY', 'strict-origin-when-cross-origin'),
            
            # Permissions Policy (antes Feature Policy)
            'PERMISSIONS_POLICY_ENABLED': os.getenv('PERMISSIONS_POLICY_ENABLED', 'true').lower() == 'true',
            
            # CORS
            'CORS_ENABLED': os.getenv('CORS_ENABLED', 'true').lower() == 'true',
            'CORS_ORIGINS': os.getenv('CORS_ORIGINS', '*').split(','),
            'CORS_METHODS': os.getenv('CORS_METHODS', 'GET,POST,PUT,DELETE,OPTIONS').split(','),
            'CORS_HEADERS': os.getenv('CORS_HEADERS', 'Content-Type,Authorization').split(','),
            'CORS_CREDENTIALS': os.getenv('CORS_CREDENTIALS', 'true').lower() == 'true',
            
            # Custom headers
            'CUSTOM_HEADERS': {}
        }
        
        # CSP directives por defecto
        self.default_csp = {
            'default-src': ["'self'"],
            'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],  # Ajustar según necesidad
            'style-src': ["'self'", "'unsafe-inline'"],
            'img-src': ["'self'", "data:", "https:"],
            'font-src': ["'self'", "data:"],
            'connect-src': ["'self'"],
            'media-src': ["'self'"],
            'object-src': ["'none'"],
            'frame-src': ["'none'"],
            'worker-src': ["'self'"],
            'child-src': ["'self'"],
            'form-action': ["'self'"],
            'frame-ancestors': ["'none'"],
            'base-uri': ["'self'"],
            'manifest-src': ["'self'"],
            'upgrade-insecure-requests': []
        }
        
        # Permissions Policy por defecto
        self.default_permissions = {
            'accelerometer': '()',
            'camera': '()',
            'geolocation': '()',
            'gyroscope': '()',
            'magnetometer': '()',
            'microphone': '()',
            'payment': '()',
            'usb': '()',
            'interest-cohort': '()',  # FLoC opt-out
            'battery': '()',
            'display-capture': '()',
            'document-domain': '()'
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa headers de seguridad con la aplicación"""
        self.app = app
        
        if not self.config['ENABLE_SECURITY_HEADERS']:
            return
        
        # Registrar after_request handler
        app.after_request(self._apply_security_headers)
        
        # Registrar endpoint para reportes CSP si está habilitado
        if self.config['CSP_ENABLED'] and self.config['CSP_REPORT_URI']:
            self._register_csp_report_endpoint(app)
    
    def _apply_security_headers(self, response: Response) -> Response:
        """Aplica todos los headers de seguridad a la respuesta"""
        if not self.config['ENABLE_SECURITY_HEADERS']:
            return response
        
        # Content Security Policy
        if self.config['CSP_ENABLED']:
            self._apply_csp(response)
        
        # HTTP Strict Transport Security
        if self.config['HSTS_ENABLED']:
            self._apply_hsts(response)
        
        # X-Frame-Options
        if self.config['FRAME_OPTIONS']:
            response.headers['X-Frame-Options'] = self.config['FRAME_OPTIONS']
        
        # X-Content-Type-Options
        if self.config['CONTENT_TYPE_NOSNIFF']:
            response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # X-XSS-Protection
        if self.config['XSS_PROTECTION']:
            response.headers['X-XSS-Protection'] = self.config['XSS_PROTECTION']
        
        # Referrer Policy
        if self.config['REFERRER_POLICY']:
            response.headers['Referrer-Policy'] = self.config['REFERRER_POLICY']
        
        # Permissions Policy
        if self.config['PERMISSIONS_POLICY_ENABLED']:
            self._apply_permissions_policy(response)
        
        # CORS Headers
        if self.config['CORS_ENABLED']:
            self._apply_cors_headers(response)
        
        # Headers adicionales de seguridad
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
        response.headers['X-Download-Options'] = 'noopen'
        response.headers['X-DNS-Prefetch-Control'] = 'off'
        
        # Remover headers que exponen información
        response.headers.pop('Server', None)
        response.headers.pop('X-Powered-By', None)
        
        # Headers personalizados
        for header, value in self.config['CUSTOM_HEADERS'].items():
            response.headers[header] = value
        
        return response
    
    def _apply_csp(self, response: Response):
        """Aplica Content Security Policy"""
        # Obtener directivas CSP para esta ruta
        csp_directives = self._get_csp_for_route(request.path)
        
        # Construir header CSP
        csp_parts = []
        for directive, sources in csp_directives.items():
            if sources:
                csp_parts.append(f"{directive} {' '.join(sources)}")
            else:
                csp_parts.append(directive)
        
        # Agregar nonce si es necesario
        if hasattr(g, 'csp_nonce'):
            # Actualizar script-src con nonce
            for i, part in enumerate(csp_parts):
                if part.startswith('script-src'):
                    csp_parts[i] = part.replace("'unsafe-inline'", f"'nonce-{g.csp_nonce}'")
        
        # Agregar report-uri si está configurado
        if self.config['CSP_REPORT_URI']:
            csp_parts.append(f"report-uri {self.config['CSP_REPORT_URI']}")
        
        csp_header = '; '.join(csp_parts)
        
        # Aplicar header
        if self.config['CSP_REPORT_ONLY']:
            response.headers['Content-Security-Policy-Report-Only'] = csp_header
        else:
            response.headers['Content-Security-Policy'] = csp_header
    
    def _get_csp_for_route(self, path: str) -> Dict[str, List[str]]:
        """Obtiene directivas CSP específicas para una ruta"""
        # Copiar directivas por defecto
        csp = self.default_csp.copy()
        
        # Ajustes específicos por ruta
        if path.startswith('/api/'):
            # APIs no necesitan muchas directivas
            csp['default-src'] = ["'none'"]
            csp['connect-src'] = ["'self'"]
            csp.pop('script-src', None)
            csp.pop('style-src', None)
            csp.pop('img-src', None)
        
        elif path.startswith('/admin/'):
            # Admin puede necesitar más permisos
            csp['script-src'].extend(["'unsafe-eval'"])  # Para algunas librerías admin
            csp['style-src'].extend(["https://fonts.googleapis.com"])
            csp['font-src'].extend(["https://fonts.gstatic.com"])
        
        elif path.startswith('/static/'):
            # Archivos estáticos
            csp = {'default-src': ["'none'"]}
        
        return csp
    
    def _apply_hsts(self, response: Response):
        """Aplica HTTP Strict Transport Security"""
        hsts_value = f"max-age={self.config['HSTS_MAX_AGE']}"
        
        if self.config['HSTS_INCLUDE_SUBDOMAINS']:
            hsts_value += "; includeSubDomains"
        
        if self.config['HSTS_PRELOAD']:
            hsts_value += "; preload"
        
        response.headers['Strict-Transport-Security'] = hsts_value
    
    def _apply_permissions_policy(self, response: Response):
        """Aplica Permissions Policy (antes Feature Policy)"""
        permissions = []
        
        for feature, allowlist in self.default_permissions.items():
            permissions.append(f"{feature}={allowlist}")
        
        response.headers['Permissions-Policy'] = ', '.join(permissions)
    
    def _apply_cors_headers(self, response: Response):
        """Aplica headers CORS de forma segura"""
        origin = request.headers.get('Origin')
        
        # Verificar si el origen está permitido
        if origin and self._is_allowed_origin(origin):
            response.headers['Access-Control-Allow-Origin'] = origin
        elif '*' in self.config['CORS_ORIGINS']:
            response.headers['Access-Control-Allow-Origin'] = '*'
        
        # Otros headers CORS
        if request.method == 'OPTIONS':
            response.headers['Access-Control-Allow-Methods'] = ', '.join(self.config['CORS_METHODS'])
            response.headers['Access-Control-Allow-Headers'] = ', '.join(self.config['CORS_HEADERS'])
            response.headers['Access-Control-Max-Age'] = '86400'  # 24 horas
        
        if self.config['CORS_CREDENTIALS'] and origin != '*':
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        # Headers expuestos
        response.headers['Access-Control-Expose-Headers'] = 'Content-Length, X-Request-Id'
    
    def _is_allowed_origin(self, origin: str) -> bool:
        """Verifica si un origen está permitido"""
        # Si se permite cualquier origen
        if '*' in self.config['CORS_ORIGINS']:
            return True
        
        # Verificar lista de orígenes permitidos
        for allowed in self.config['CORS_ORIGINS']:
            if allowed == origin:
                return True
            
            # Soporte para wildcards en subdominios
            if allowed.startswith('*.'):
                domain = allowed[2:]
                if origin.endswith(domain):
                    return True
        
        return False
    
    def _register_csp_report_endpoint(self, app):
        """Registra endpoint para recibir reportes CSP"""
        @app.route(self.config['CSP_REPORT_URI'], methods=['POST'])
        def csp_report():
            """Recibe y procesa reportes de violaciones CSP"""
            try:
                # Obtener reporte
                report = request.get_json()
                
                if report and 'csp-report' in report:
                    csp_data = report['csp-report']
                    
                    # Log del reporte
                    app.logger.warning(f"CSP Violation: {csp_data}")
                    
                    # Aquí podrías almacenar en DB o enviar a servicio de monitoreo
                    self._process_csp_violation(csp_data)
                
                return '', 204  # No Content
                
            except Exception as e:
                app.logger.error(f"Error processing CSP report: {e}")
                return '', 204
    
    def _process_csp_violation(self, violation: Dict[str, Any]):
        """Procesa una violación CSP"""
        # Extraer información relevante
        blocked_uri = violation.get('blocked-uri', 'unknown')
        violated_directive = violation.get('violated-directive', 'unknown')
        document_uri = violation.get('document-uri', 'unknown')
        
        # Aquí podrías:
        # - Almacenar en base de datos
        # - Enviar alertas si hay muchas violaciones
        # - Actualizar políticas automáticamente
        # - Integrar con sistema de monitoreo
        
        if current_app:
            current_app.logger.info(
                f"CSP Violation: {violated_directive} blocked {blocked_uri} on {document_uri}"
            )
    
    def generate_nonce(self) -> str:
        """
        Genera un nonce para CSP inline scripts
        
        Returns:
            str: Nonce único
        """
        import secrets
        nonce = secrets.token_urlsafe(16)
        g.csp_nonce = nonce
        return nonce
    
    def add_csp_source(self, directive: str, source: str):
        """
        Agrega una fuente a una directiva CSP dinámicamente
        
        Args:
            directive: Directiva CSP (script-src, style-src, etc)
            source: Fuente a agregar
        """
        if directive in self.default_csp:
            if source not in self.default_csp[directive]:
                self.default_csp[directive].append(source)
    
    def set_custom_header(self, name: str, value: str):
        """
        Establece un header personalizado
        
        Args:
            name: Nombre del header
            value: Valor del header
        """
        self.config['CUSTOM_HEADERS'][name] = value
    
    def get_security_headers_report(self) -> Dict[str, Any]:
        """
        Genera un reporte del estado de los headers de seguridad
        
        Returns:
            Dict con el estado de cada header
        """
        report = {
            'enabled': self.config['ENABLE_SECURITY_HEADERS'],
            'headers': {
                'CSP': {
                    'enabled': self.config['CSP_ENABLED'],
                    'report_only': self.config['CSP_REPORT_ONLY'],
                    'directives': len(self.default_csp)
                },
                'HSTS': {
                    'enabled': self.config['HSTS_ENABLED'],
                    'max_age': self.config['HSTS_MAX_AGE'],
                    'include_subdomains': self.config['HSTS_INCLUDE_SUBDOMAINS'],
                    'preload': self.config['HSTS_PRELOAD']
                },
                'X-Frame-Options': self.config['FRAME_OPTIONS'],
                'X-Content-Type-Options': 'nosniff' if self.config['CONTENT_TYPE_NOSNIFF'] else None,
                'X-XSS-Protection': self.config['XSS_PROTECTION'],
                'Referrer-Policy': self.config['REFERRER_POLICY'],
                'Permissions-Policy': {
                    'enabled': self.config['PERMISSIONS_POLICY_ENABLED'],
                    'features_blocked': len(self.default_permissions)
                },
                'CORS': {
                    'enabled': self.config['CORS_ENABLED'],
                    'origins': self.config['CORS_ORIGINS'],
                    'credentials': self.config['CORS_CREDENTIALS']
                }
            }
        }
        
        return report


# Instancia global
security_headers = SecurityHeaders()


# Decorador para headers personalizados en rutas específicas
def custom_headers(**headers):
    """
    Decorador para agregar headers personalizados a una ruta
    
    Uso:
        @app.route('/special')
        @custom_headers(
            X_Custom_Header='value',
            Cache_Control='no-store'
        )
        def special_route():
            ...
    """
    from functools import wraps
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            # Si no es Response, convertir
            if not isinstance(response, Response):
                response = make_response(response)
            
            # Aplicar headers personalizados
            for header, value in headers.items():
                response.headers[header.replace('_', '-')] = value
            
            return response
        
        return decorated_function
    
    return decorator
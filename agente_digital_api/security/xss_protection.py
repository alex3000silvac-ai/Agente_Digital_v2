"""
xss_protection.py - Protección contra Cross-Site Scripting (XSS)
=============================================================

Este módulo implementa protección completa contra ataques XSS mediante
sanitización de contenido, políticas de seguridad y validación de outputs.

Características:
- Sanitización automática de HTML
- Content Security Policy (CSP)
- Escape contextual de outputs
- Validación de contenido rico
- Detección de payloads XSS
- Headers de seguridad XSS
"""

import os
import re
import html
import json
import bleach
from urllib.parse import urlparse, quote
from typing import Any, Dict, List, Optional, Union
from flask import Response, make_response

class XSSProtection:
    """
    Sistema completo de protección contra XSS
    """
    
    def __init__(self):
        self.config = {
            'ENABLE_XSS_PROTECTION': os.getenv('ENABLE_XSS_PROTECTION', 'true').lower() == 'true',
            'SANITIZE_HTML': os.getenv('SANITIZE_HTML', 'true').lower() == 'true',
            'ALLOWED_TAGS': os.getenv('XSS_ALLOWED_TAGS', 'p,br,strong,em,u,i,a,ul,ol,li,blockquote,code,pre').split(','),
            'ALLOWED_ATTRIBUTES': {
                'a': ['href', 'title', 'target'],
                'code': ['class'],
                'pre': ['class']
            },
            'ALLOWED_PROTOCOLS': ['http', 'https', 'mailto'],
            'STRIP_TAGS': os.getenv('XSS_STRIP_TAGS', 'true').lower() == 'true',
            'ESCAPE_ON_DEFAULT': os.getenv('XSS_ESCAPE_DEFAULT', 'true').lower() == 'true'
        }
        
        # Patrones de XSS conocidos
        self.xss_patterns = [
            # Script tags
            r'<script[^>]*>.*?</script>',
            r'<script[^>]*/>',
            
            # Event handlers
            r'on\w+\s*=',
            r'on(click|load|error|mouse\w+|key\w+|focus|blur|change|submit)',
            
            # JavaScript protocol
            r'javascript:',
            r'vbscript:',
            r'data:text/html',
            
            # Dangerous tags
            r'<iframe',
            r'<frame',
            r'<embed',
            r'<object',
            r'<applet',
            r'<meta',
            r'<link',
            r'<style',
            
            # Expression/Binding attacks
            r'expression\s*\(',
            r'binding\s*\(',
            r'@import',
            
            # SVG attacks
            r'<svg',
            r'xmlns',
            
            # Base64 encoded scripts
            r'base64,[A-Za-z0-9+/]+=*',
            
            # HTML entities abuse
            r'&(?:#x?[0-9a-f]+|[a-z]+);',
            
            # CSS expressions
            r'style\s*=.*expression',
            r'style\s*=.*javascript:',
            
            # Template injection
            r'\{\{.*\}\}',
            r'\${.*}',
            r'<%.*%>',
        ]
        
        # Configuración de bleach
        self.cleaner = bleach.Cleaner(
            tags=self.config['ALLOWED_TAGS'],
            attributes=self.config['ALLOWED_ATTRIBUTES'],
            protocols=self.config['ALLOWED_PROTOCOLS'],
            strip=self.config['STRIP_TAGS']
        )
    
    def sanitize_html(self, content: str, context: str = 'default') -> str:
        """
        Sanitiza contenido HTML eliminando elementos peligrosos
        
        Args:
            content: Contenido a sanitizar
            context: Contexto de uso ('default', 'strict', 'markdown', 'rich')
            
        Returns:
            str: Contenido sanitizado
        """
        if not self.config['ENABLE_XSS_PROTECTION']:
            return content
        
        if not isinstance(content, str):
            return str(content)
        
        # Detectar intentos de XSS
        if self._detect_xss_attempt(content):
            # Log del intento
            self._log_xss_attempt(content)
            
            # En modo estricto, rechazar completamente
            if context == 'strict':
                return '[CONTENIDO BLOQUEADO]'
        
        # Aplicar sanitización según contexto
        if context == 'strict':
            # Solo texto plano
            return html.escape(content)
        
        elif context == 'markdown':
            # Permitir markdown básico
            return self._sanitize_markdown(content)
        
        elif context == 'rich':
            # Permitir más tags para contenido rico
            return self._sanitize_rich_content(content)
        
        else:
            # Sanitización por defecto con bleach
            return self.cleaner.clean(content)
    
    def _detect_xss_attempt(self, content: str) -> bool:
        """Detecta posibles intentos de XSS"""
        content_lower = content.lower()
        
        # Verificar patrones conocidos
        for pattern in self.xss_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE | re.DOTALL):
                return True
        
        # Verificar longitud sospechosa de atributos
        attr_pattern = r'(\w+)\s*=\s*["\']([^"\']{100,})["\']'
        if re.search(attr_pattern, content):
            return True
        
        # Verificar múltiples codificaciones
        if any(enc in content_lower for enc in ['%3c', '%3e', '\\x3c', '\\x3e', '\\u003c', '\\u003e']):
            return True
        
        return False
    
    def _sanitize_markdown(self, content: str) -> str:
        """Sanitiza contenido markdown"""
        # Permitir tags básicos de markdown
        markdown_tags = self.config['ALLOWED_TAGS'] + ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr']
        
        markdown_cleaner = bleach.Cleaner(
            tags=markdown_tags,
            attributes=self.config['ALLOWED_ATTRIBUTES'],
            protocols=self.config['ALLOWED_PROTOCOLS'],
            strip=True
        )
        
        return markdown_cleaner.clean(content)
    
    def _sanitize_rich_content(self, content: str) -> str:
        """Sanitiza contenido rico (más permisivo)"""
        # Permitir más tags para editores WYSIWYG
        rich_tags = self.config['ALLOWED_TAGS'] + [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'table', 'thead', 'tbody', 'tr', 'td', 'th',
            'div', 'span', 'img', 'hr'
        ]
        
        rich_attributes = self.config['ALLOWED_ATTRIBUTES'].copy()
        rich_attributes.update({
            'img': ['src', 'alt', 'width', 'height'],
            'div': ['class', 'id'],
            'span': ['class', 'style'],
            'table': ['class'],
            'td': ['colspan', 'rowspan'],
            'th': ['colspan', 'rowspan']
        })
        
        rich_cleaner = bleach.Cleaner(
            tags=rich_tags,
            attributes=rich_attributes,
            protocols=self.config['ALLOWED_PROTOCOLS'] + ['data'],  # Para imágenes inline
            strip=True
        )
        
        return rich_cleaner.clean(content)
    
    def escape_json(self, data: Any) -> str:
        """
        Escapa datos para inclusión segura en JSON
        
        Args:
            data: Datos a escapar
            
        Returns:
            str: JSON escapado
        """
        # Serializar a JSON
        json_str = json.dumps(data, ensure_ascii=False)
        
        # Escapar caracteres peligrosos para inclusión en HTML
        json_str = json_str.replace('</', '<\\/')
        json_str = json_str.replace('<script', '<\\script')
        json_str = json_str.replace('</script', '<\\/script')
        
        return json_str
    
    def escape_javascript(self, content: str) -> str:
        """
        Escapa contenido para inclusión segura en JavaScript
        
        Args:
            content: Contenido a escapar
            
        Returns:
            str: Contenido escapado
        """
        if not isinstance(content, str):
            content = str(content)
        
        # Escapar caracteres peligrosos
        content = content.replace('\\', '\\\\')
        content = content.replace('"', '\\"')
        content = content.replace("'", "\\'")
        content = content.replace('\n', '\\n')
        content = content.replace('\r', '\\r')
        content = content.replace('\t', '\\t')
        content = content.replace('</', '<\\/')
        
        return content
    
    def escape_html_attribute(self, content: str) -> str:
        """
        Escapa contenido para uso seguro en atributos HTML
        
        Args:
            content: Contenido a escapar
            
        Returns:
            str: Contenido escapado
        """
        if not isinstance(content, str):
            content = str(content)
        
        # Escapar comillas y caracteres especiales
        content = html.escape(content, quote=True)
        
        # Escapar caracteres adicionales peligrosos en atributos
        content = content.replace('`', '&#96;')
        content = content.replace('(', '&#40;')
        content = content.replace(')', '&#41;')
        
        return content
    
    def escape_css(self, content: str) -> str:
        """
        Escapa contenido para uso seguro en CSS
        
        Args:
            content: Contenido a escapar
            
        Returns:
            str: Contenido escapado
        """
        if not isinstance(content, str):
            content = str(content)
        
        # Remover caracteres peligrosos
        content = re.sub(r'[<>\"\'`(){}]', '', content)
        
        # Escapar backslashes
        content = content.replace('\\', '\\\\')
        
        # Remover comentarios
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        return content
    
    def escape_url(self, url: str) -> str:
        """
        Escapa y valida URLs para prevenir XSS
        
        Args:
            url: URL a escapar
            
        Returns:
            str: URL escapada
        """
        if not url:
            return ''
        
        # Parsear URL
        try:
            parsed = urlparse(url)
        except:
            return ''
        
        # Validar protocolo
        if parsed.scheme and parsed.scheme not in self.config['ALLOWED_PROTOCOLS']:
            return ''
        
        # Si no tiene protocolo, asumir http
        if not parsed.scheme:
            url = 'http://' + url
            parsed = urlparse(url)
        
        # Reconstruir URL de forma segura
        return parsed.geturl()
    
    def set_content_security_policy(self, response: Response, 
                                  policy: Optional[Dict[str, str]] = None) -> Response:
        """
        Establece Content Security Policy en la respuesta
        
        Args:
            response: Respuesta Flask
            policy: Política CSP personalizada
            
        Returns:
            Response: Respuesta con CSP
        """
        if not self.config['ENABLE_XSS_PROTECTION']:
            return response
        
        # Política por defecto
        default_policy = {
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline' 'unsafe-eval'",  # Ajustar según necesidad
            'style-src': "'self' 'unsafe-inline'",
            'img-src': "'self' data: https:",
            'font-src': "'self' data:",
            'connect-src': "'self'",
            'media-src': "'self'",
            'object-src': "'none'",
            'frame-src': "'none'",
            'base-uri': "'self'",
            'form-action': "'self'",
            'frame-ancestors': "'none'",
            'upgrade-insecure-requests': ''
        }
        
        # Aplicar política personalizada si existe
        if policy:
            default_policy.update(policy)
        
        # Construir header CSP
        csp_parts = []
        for directive, value in default_policy.items():
            if value:
                csp_parts.append(f"{directive} {value}")
            else:
                csp_parts.append(directive)
        
        csp_header = '; '.join(csp_parts)
        
        # Establecer header
        response.headers['Content-Security-Policy'] = csp_header
        
        # Headers adicionales de XSS
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        return response
    
    def sanitize_response(self, data: Any, content_type: str = 'application/json') -> Any:
        """
        Sanitiza datos de respuesta según el tipo de contenido
        
        Args:
            data: Datos a sanitizar
            content_type: Tipo de contenido
            
        Returns:
            Datos sanitizados
        """
        if not self.config['ENABLE_XSS_PROTECTION']:
            return data
        
        if content_type == 'application/json':
            return self._sanitize_json_response(data)
        elif content_type.startswith('text/html'):
            return self._sanitize_html_response(data)
        else:
            return data
    
    def _sanitize_json_response(self, data: Any) -> Any:
        """Sanitiza respuesta JSON recursivamente"""
        if isinstance(data, dict):
            return {k: self._sanitize_json_response(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_json_response(item) for item in data]
        elif isinstance(data, str):
            # Escapar strings en respuestas JSON
            if self.config['ESCAPE_ON_DEFAULT']:
                return html.escape(data)
            return data
        else:
            return data
    
    def _sanitize_html_response(self, content: str) -> str:
        """Sanitiza respuesta HTML"""
        # Aplicar sanitización completa
        return self.sanitize_html(content, context='default')
    
    def create_safe_response(self, data: Any, status: int = 200,
                           content_type: str = 'application/json') -> Response:
        """
        Crea una respuesta segura con protecciones XSS
        
        Args:
            data: Datos de respuesta
            status: Código de estado
            content_type: Tipo de contenido
            
        Returns:
            Response: Respuesta Flask segura
        """
        # Sanitizar datos
        safe_data = self.sanitize_response(data, content_type)
        
        # Crear respuesta
        if content_type == 'application/json':
            response = make_response(json.dumps(safe_data), status)
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
        else:
            response = make_response(safe_data, status)
            response.headers['Content-Type'] = f'{content_type}; charset=utf-8'
        
        # Aplicar CSP y headers de seguridad
        response = self.set_content_security_policy(response)
        
        return response
    
    def _log_xss_attempt(self, content: str):
        """Registra un intento de XSS"""
        import logging
        logger = logging.getLogger(__name__)
        
        event = {
            'event': 'xss_attempt_detected',
            'content_sample': content[:200],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.warning(f"XSS_ATTEMPT: {json.dumps(event)}")


# Instancia global
xss_protection = XSSProtection()
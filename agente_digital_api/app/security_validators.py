# app/security_validators.py
# Validadores y sanitizadores de seguridad para entradas de usuario

import re
import html
import sqlparse
from functools import wraps
from flask import request, jsonify, g

try:
    import bleach
    from marshmallow import Schema, fields, ValidationError, validates, validates_schema
    VALIDATION_LIBS_AVAILABLE = True
except ImportError:
    from .fallback_imports import bleach, Schema, fields, ValidationError, validates
    validates_schema = validates
    VALIDATION_LIBS_AVAILABLE = False
# from werkzeug.security import safe_str_cmp  # Removed in newer Werkzeug versions
import hmac
import logging

logger = logging.getLogger(__name__)

class SecurityValidationError(Exception):
    """Excepción personalizada para errores de validación de seguridad"""
    pass

class InputSanitizer:
    """Clase para sanitizar diferentes tipos de entrada"""
    
    # Patrones de SQL injection
    SQL_INJECTION_PATTERNS = [
        r"(\s|^)(union|select|insert|delete|update|drop|create|alter|exec|execute)\s",
        r"(\s|^)(or|and)\s+(\d+\s*=\s*\d+|'.*'|\".*\")",
        r";\s*(select|insert|delete|update|drop|create|alter)",
        r"(\/\*.*\*\/|--.*$)",
        r"(char|nchar|varchar|nvarchar)\s*\(",
        r"(exec|execute|sp_|xp_)",
    ]
    
    # Patrones XSS
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"onmouseover\s*=",
    ]
    
    # Caracteres peligrosos para nombres de archivo
    DANGEROUS_FILE_CHARS = [
        '/', '\\', '..', '<', '>', ':', '"', '|', '?', '*',
        '\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07',
        '\x08', '\x09', '\x0a', '\x0b', '\x0c', '\x0d', '\x0e', '\x0f'
    ]
    
    @staticmethod
    def sanitize_html(text):
        """Sanitizar HTML para prevenir XSS"""
        if not text:
            return text
            
        # Lista de tags permitidos
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'h1', 'h2', 'h3']
        allowed_attributes = {}
        
        # Usar bleach para limpiar HTML
        clean_text = bleach.clean(text, tags=allowed_tags, attributes=allowed_attributes, strip=True)
        
        return clean_text
    
    @staticmethod
    def sanitize_sql_input(text):
        """Sanitizar entrada para prevenir SQL injection"""
        if not text:
            return text
            
        # Verificar patrones sospechosos
        text_lower = text.lower()
        for pattern in InputSanitizer.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE | re.MULTILINE):
                logger.warning(f"SQL injection attempt detected: {pattern}")
                raise SecurityValidationError("Invalid input detected")
        
        # Escapar caracteres especiales
        text = text.replace("'", "''")  # Escape single quotes
        text = text.replace(";", "")     # Remove semicolons
        text = text.replace("--", "")    # Remove comment indicators
        text = text.replace("/*", "")    # Remove comment start
        text = text.replace("*/", "")    # Remove comment end
        
        return text
    
    @staticmethod
    def sanitize_filename(filename):
        """Sanitizar nombres de archivo"""
        if not filename:
            return filename
            
        # Remover caracteres peligrosos
        for char in InputSanitizer.DANGEROUS_FILE_CHARS:
            filename = filename.replace(char, '')
        
        # Limitar longitud
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + ('.' + ext if ext else '')
        
        # Prevenir nombres reservados en Windows
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        name_part = filename.split('.')[0].upper()
        if name_part in reserved_names:
            filename = 'file_' + filename
        
        return filename
    
    @staticmethod
    def detect_xss(text):
        """Detectar intentos de XSS"""
        if not text:
            return False
            
        text_lower = text.lower()
        for pattern in InputSanitizer.XSS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning(f"XSS attempt detected: {pattern}")
                return True
        
        return False
    
    @staticmethod
    def sanitize_user_input(text, allow_html=False):
        """Sanitizar entrada general del usuario"""
        if not text:
            return text
            
        # Verificar XSS
        if InputSanitizer.detect_xss(text):
            raise SecurityValidationError("Potentially malicious content detected")
        
        # Sanitizar SQL
        text = InputSanitizer.sanitize_sql_input(text)
        
        # Sanitizar HTML si no está permitido
        if not allow_html:
            text = html.escape(text)
        else:
            text = InputSanitizer.sanitize_html(text)
        
        # Limitar longitud general
        if len(text) > 10000:  # 10KB limit
            raise SecurityValidationError("Input too long")
        
        return text.strip()

# Schemas de validación con Marshmallow
class SecureLoginSchema(Schema):
    """Schema seguro para login"""
    username = fields.Str(required=True, validate=[
        lambda x: len(x) >= 3,
        lambda x: len(x) <= 50,
        lambda x: re.match(r'^[a-zA-Z0-9._-]+$', x)
    ])
    password = fields.Str(required=True, validate=[
        lambda x: len(x) >= 8,
        lambda x: len(x) <= 128
    ])
    remember_me = fields.Bool(missing=False)
    
    @validates('username')
    def validate_username(self, value):
        # Sanitizar entrada
        sanitized = InputSanitizer.sanitize_user_input(value)
        if sanitized != value:
            raise ValidationError("Invalid characters in username")
    
    @validates('password')
    def validate_password(self, value):
        # Verificar complejidad de contraseña
        if not re.search(r'[A-Z]', value):
            raise ValidationError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', value):
            raise ValidationError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', value):
            raise ValidationError("Password must contain at least one digit")

class SecureUserSchema(Schema):
    """Schema seguro para datos de usuario"""
    nombre = fields.Str(required=True, validate=[
        lambda x: len(x) >= 2,
        lambda x: len(x) <= 100
    ])
    email = fields.Email(required=True)
    telefono = fields.Str(allow_none=True, validate=[
        lambda x: not x or re.match(r'^[\d\+\-\s\(\)]+$', x)
    ])
    
    @validates('nombre')
    def validate_nombre(self, value):
        sanitized = InputSanitizer.sanitize_user_input(value)
        if InputSanitizer.detect_xss(value):
            raise ValidationError("Invalid content detected")

class SecureEmpresaSchema(Schema):
    """Schema seguro para datos de empresa"""
    nombre = fields.Str(required=True, validate=[
        lambda x: len(x) >= 2,
        lambda x: len(x) <= 200
    ])
    rut = fields.Str(required=True, validate=[
        lambda x: re.match(r'^\d{7,8}-[\dkK]$', x)
    ])
    direccion = fields.Str(allow_none=True, validate=[
        lambda x: not x or len(x) <= 300
    ])
    
    @validates('nombre')
    def validate_nombre(self, value):
        sanitized = InputSanitizer.sanitize_user_input(value)
        if InputSanitizer.detect_xss(value):
            raise ValidationError("Invalid content detected")

class SecureIncidenteSchema(Schema):
    """Schema seguro para datos de incidente"""
    titulo = fields.Str(required=True, validate=[
        lambda x: len(x) >= 5,
        lambda x: len(x) <= 200
    ])
    descripcion = fields.Str(required=True, validate=[
        lambda x: len(x) >= 10,
        lambda x: len(x) <= 5000
    ])
    criticidad = fields.Str(required=True, validate=[
        lambda x: x in ['Baja', 'Media', 'Alta', 'Crítica']
    ])
    
    @validates('titulo')
    def validate_titulo(self, value):
        sanitized = InputSanitizer.sanitize_user_input(value)
        if InputSanitizer.detect_xss(value):
            raise ValidationError("Invalid content detected")
    
    @validates('descripcion')
    def validate_descripcion(self, value):
        # Permitir HTML básico en descripción pero sanitizado
        sanitized = InputSanitizer.sanitize_user_input(value, allow_html=True)
        if InputSanitizer.detect_xss(value):
            raise ValidationError("Invalid content detected")

# Decoradores de validación
def validate_json_input(schema_class):
    """Decorador para validar entrada JSON con schema"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if not request.is_json:
                    return jsonify({'error': 'Content-Type must be application/json'}), 400
                
                schema = schema_class()
                data = schema.load(request.get_json() or {})
                
                # Almacenar datos validados en g para acceso en la función
                g.validated_data = data
                
                return func(*args, **kwargs)
                
            except ValidationError as err:
                logger.warning(f"Validation error: {err.messages}")
                return jsonify({
                    'error': 'Validation failed',
                    'details': err.messages
                }), 400
            except SecurityValidationError as err:
                logger.error(f"Security validation error: {str(err)}")
                return jsonify({
                    'error': 'Security validation failed',
                    'message': 'Invalid or potentially malicious input detected'
                }), 400
            except Exception as err:
                logger.error(f"Unexpected validation error: {str(err)}")
                return jsonify({'error': 'Invalid request data'}), 400
                
        return wrapper
    return decorator

def validate_file_upload():
    """Decorador para validar uploads de archivos"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Verificar que hay archivos
                if not request.files:
                    return jsonify({'error': 'No files provided'}), 400
                
                # Validar cada archivo
                for field_name, file in request.files.items():
                    if file.filename == '':
                        return jsonify({'error': f'Empty filename for {field_name}'}), 400
                    
                    # Sanitizar nombre de archivo
                    original_filename = file.filename
                    sanitized_filename = InputSanitizer.sanitize_filename(original_filename)
                    
                    if sanitized_filename != original_filename:
                        logger.warning(f"Filename sanitized: {original_filename} -> {sanitized_filename}")
                    
                    # Verificar extensión
                    allowed_extensions = {
                        'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt',
                        'xls', 'xlsx', 'csv', 'ods',
                        'jpg', 'jpeg', 'png', 'gif', 'bmp',
                        'zip', 'rar', '7z'
                    }
                    
                    extension = sanitized_filename.rsplit('.', 1)[1].lower() if '.' in sanitized_filename else ''
                    if extension not in allowed_extensions:
                        return jsonify({
                            'error': f'File type not allowed: .{extension}',
                            'allowed_types': list(allowed_extensions)
                        }), 400
                    
                    # Actualizar filename sanitizado
                    file.filename = sanitized_filename
                
                return func(*args, **kwargs)
                
            except Exception as err:
                logger.error(f"File validation error: {str(err)}")
                return jsonify({'error': 'File validation failed'}), 400
                
        return wrapper
    return decorator

def sanitize_query_params():
    """Decorador para sanitizar parámetros de query"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Sanitizar parámetros de query
                sanitized_args = {}
                for key, value in request.args.items():
                    if isinstance(value, str):
                        sanitized_value = InputSanitizer.sanitize_user_input(value)
                        sanitized_args[key] = sanitized_value
                    else:
                        sanitized_args[key] = value
                
                # Reemplazar request.args con versión sanitizada
                g.sanitized_args = sanitized_args
                
                return func(*args, **kwargs)
                
            except SecurityValidationError as err:
                logger.error(f"Query parameter security error: {str(err)}")
                return jsonify({
                    'error': 'Invalid query parameters',
                    'message': 'Potentially malicious input detected'
                }), 400
            except Exception as err:
                logger.error(f"Query parameter sanitization error: {str(err)}")
                return jsonify({'error': 'Invalid query parameters'}), 400
                
        return wrapper
    return decorator

def require_csrf_token():
    """Decorador para verificar token CSRF"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'DELETE']:
                csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
                expected_token = g.get('csrf_token')
                
                if not csrf_token or not expected_token:
                    return jsonify({'error': 'CSRF token missing'}), 403
                
                if not hmac.compare_digest(csrf_token, expected_token):
                    return jsonify({'error': 'CSRF token invalid'}), 403
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Funciones de utilidad
def validate_email(email):
    """Validar formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_rut(rut):
    """Validar RUT chileno"""
    if not rut or not isinstance(rut, str):
        return False
    
    # Limpiar RUT
    rut = rut.replace('.', '').replace('-', '').upper()
    
    if len(rut) < 8 or len(rut) > 9:
        return False
    
    # Separar número y dígito verificador
    numero = rut[:-1]
    dv = rut[-1]
    
    if not numero.isdigit():
        return False
    
    # Calcular dígito verificador
    suma = 0
    multiplicador = 2
    
    for digit in reversed(numero):
        suma += int(digit) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 7 else 2
    
    resto = suma % 11
    dv_calculado = '0' if resto == 0 else 'K' if resto == 1 else str(11 - resto)
    
    return dv == dv_calculado

def check_password_strength(password):
    """Verificar fortaleza de contraseña"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password too long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    # Verificar patrones comunes débiles
    weak_patterns = [
        r'123456', r'password', r'qwerty', r'admin', r'root',
        r'(.)\1{3,}',  # Caracteres repetidos
    ]
    
    for pattern in weak_patterns:
        if re.search(pattern, password.lower()):
            return False, "Password contains weak patterns"
    
    return True, "Password is strong"
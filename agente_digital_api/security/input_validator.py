"""
input_validator.py - Validación y sanitización de inputs
======================================================

Este módulo implementa validación exhaustiva de todos los inputs
para prevenir ataques de inyección y datos maliciosos.

Características:
- Validación de tipos de datos
- Sanitización automática
- Límites de longitud
- Whitelist/Blacklist de caracteres
- Validación de formatos específicos
- Escape automático de caracteres peligrosos
"""

import os
import re
import html
import json
import urllib.parse
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union, Tuple
from flask import request, abort

class InputValidator:
    """
    Sistema completo de validación y sanitización de inputs
    """
    
    def __init__(self):
        self.config = {
            'MAX_STRING_LENGTH': int(os.getenv('MAX_STRING_LENGTH', 1000)),
            'MAX_INT_VALUE': int(os.getenv('MAX_INT_VALUE', 2147483647)),
            'MAX_ARRAY_LENGTH': int(os.getenv('MAX_ARRAY_LENGTH', 100)),
            'MAX_JSON_DEPTH': int(os.getenv('MAX_JSON_DEPTH', 10)),
            'ALLOW_HTML': os.getenv('ALLOW_HTML_INPUT', 'false').lower() == 'true',
            'STRICT_MODE': os.getenv('VALIDATION_STRICT_MODE', 'true').lower() == 'true'
        }
        
        # Patrones de validación comunes
        self.patterns = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{4,6}$',
            'url': r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$',
            'alphanumeric': r'^[a-zA-Z0-9]+$',
            'alpha': r'^[a-zA-Z]+$',
            'numeric': r'^[0-9]+$',
            'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            'date': r'^\d{4}-\d{2}-\d{2}$',
            'time': r'^\d{2}:\d{2}(:\d{2})?$',
            'datetime': r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?$'
        }
        
        # Caracteres peligrosos a filtrar
        self.dangerous_patterns = [
            # SQL Injection
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
            r"(--|;|\/\*|\*\/|xp_|sp_)",
            r"(\bor\b\s*\d+\s*=\s*\d+)",
            r"(\band\b\s*\d+\s*=\s*\d+)",
            
            # XSS
            r"(<script|<\/script|javascript:|onerror=|onclick=|onload=)",
            r"(<iframe|<\/iframe|<object|<\/object|<embed|<\/embed)",
            r"(document\.|window\.|eval\(|setTimeout\(|setInterval\()",
            
            # Path Traversal
            r"(\.\.\/|\.\.\\|%2e%2e|%252e%252e)",
            r"(\/etc\/|c:\\|\\windows\\)",
            
            # Command Injection
            r"([;&|`]|\$\(|\${)",
            r"(system\(|exec\(|popen\(|proc_open\()",
            
            # XXE
            r"(<!DOCTYPE|<!ENTITY|SYSTEM|PUBLIC)",
            
            # LDAP Injection
            r"(\(|\)|\||&|=|\*)",
            
            # NoSQL Injection
            r"(\$ne|\$gt|\$lt|\$gte|\$lte|\$in|\$nin|\$regex)",
        ]
        
        # Whitelist de caracteres seguros por tipo
        self.safe_chars = {
            'strict': r'^[a-zA-Z0-9\s\-_\.]+$',
            'normal': r'^[a-zA-Z0-9\s\-_\.\,\!\?\@\#]+$',
            'extended': r'^[a-zA-Z0-9\s\-_\.\,\!\?\@\#\$\%\^\&\*\(\)\[\]\{\}]+$'
        }
    
    def validate_request(self, rules: Dict[str, Any], source: str = 'json') -> Dict[str, Any]:
        """
        Valida una request completa según reglas definidas
        
        Args:
            rules: Diccionario con reglas de validación
            source: Origen de los datos ('json', 'form', 'args')
            
        Returns:
            Dict con datos validados y sanitizados
            
        Ejemplo:
            rules = {
                'username': {'type': 'string', 'required': True, 'min_length': 3, 'max_length': 20},
                'age': {'type': 'integer', 'required': True, 'min': 18, 'max': 120},
                'email': {'type': 'email', 'required': True}
            }
        """
        # Obtener datos según la fuente
        if source == 'json':
            data = request.get_json() or {}
        elif source == 'form':
            data = request.form.to_dict()
        elif source == 'args':
            data = request.args.to_dict()
        else:
            data = {}
        
        validated_data = {}
        errors = []
        
        # Validar cada campo según las reglas
        for field_name, field_rules in rules.items():
            value = data.get(field_name)
            
            # Validar requerido
            if field_rules.get('required', False) and value is None:
                errors.append(f"Field '{field_name}' is required")
                continue
            
            # Si no es requerido y no está presente, continuar
            if value is None:
                if 'default' in field_rules:
                    validated_data[field_name] = field_rules['default']
                continue
            
            # Validar y sanitizar según tipo
            try:
                validated_value = self._validate_field(field_name, value, field_rules)
                validated_data[field_name] = validated_value
            except ValueError as e:
                errors.append(f"Field '{field_name}': {str(e)}")
        
        # Si hay errores, abortar
        if errors:
            abort(400, {'errors': errors})
        
        return validated_data
    
    def _validate_field(self, name: str, value: Any, rules: Dict[str, Any]) -> Any:
        """Valida un campo individual según sus reglas"""
        field_type = rules.get('type', 'string')
        
        # Validar según tipo
        if field_type == 'string':
            return self._validate_string(value, rules)
        elif field_type == 'integer':
            return self._validate_integer(value, rules)
        elif field_type == 'float':
            return self._validate_float(value, rules)
        elif field_type == 'boolean':
            return self._validate_boolean(value)
        elif field_type == 'array':
            return self._validate_array(value, rules)
        elif field_type == 'object':
            return self._validate_object(value, rules)
        elif field_type == 'email':
            return self._validate_email(value)
        elif field_type == 'url':
            return self._validate_url(value)
        elif field_type == 'date':
            return self._validate_date(value)
        elif field_type == 'datetime':
            return self._validate_datetime(value)
        elif field_type == 'uuid':
            return self._validate_uuid(value)
        elif field_type == 'phone':
            return self._validate_phone(value)
        else:
            raise ValueError(f"Unknown field type: {field_type}")
    
    def _validate_string(self, value: Any, rules: Dict[str, Any]) -> str:
        """Valida y sanitiza un string"""
        # Convertir a string
        value = str(value)
        
        # Validar longitud
        min_length = rules.get('min_length', 0)
        max_length = rules.get('max_length', self.config['MAX_STRING_LENGTH'])
        
        if len(value) < min_length:
            raise ValueError(f"String too short (min: {min_length})")
        
        if len(value) > max_length:
            raise ValueError(f"String too long (max: {max_length})")
        
        # Validar patrón si existe
        if 'pattern' in rules:
            if not re.match(rules['pattern'], value):
                raise ValueError("String does not match required pattern")
        
        # Validar contra patrones peligrosos
        if self.config['STRICT_MODE']:
            for pattern in self.dangerous_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    raise ValueError("String contains dangerous pattern")
        
        # Sanitizar
        sanitized = self._sanitize_string(value, rules)
        
        # Validar whitelist de caracteres
        if 'allowed_chars' in rules:
            char_set = self.safe_chars.get(rules['allowed_chars'], rules['allowed_chars'])
            if not re.match(char_set, sanitized):
                raise ValueError("String contains invalid characters")
        
        return sanitized
    
    def _sanitize_string(self, value: str, rules: Dict[str, Any]) -> str:
        """Sanitiza un string según las reglas"""
        # Trim espacios
        if rules.get('trim', True):
            value = value.strip()
        
        # Escape HTML si no está permitido
        if not self.config['ALLOW_HTML'] and not rules.get('allow_html', False):
            value = html.escape(value)
        
        # Remover caracteres de control
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
        
        # Normalizar espacios múltiples
        if rules.get('normalize_spaces', True):
            value = ' '.join(value.split())
        
        # Aplicar transformaciones
        if rules.get('lowercase', False):
            value = value.lower()
        elif rules.get('uppercase', False):
            value = value.upper()
        
        return value
    
    def _validate_integer(self, value: Any, rules: Dict[str, Any]) -> int:
        """Valida un entero"""
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValueError("Invalid integer value")
        
        # Validar rango
        min_val = rules.get('min', -self.config['MAX_INT_VALUE'])
        max_val = rules.get('max', self.config['MAX_INT_VALUE'])
        
        if value < min_val:
            raise ValueError(f"Integer too small (min: {min_val})")
        
        if value > max_val:
            raise ValueError(f"Integer too large (max: {max_val})")
        
        return value
    
    def _validate_float(self, value: Any, rules: Dict[str, Any]) -> float:
        """Valida un float"""
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise ValueError("Invalid float value")
        
        # Validar rango
        min_val = rules.get('min', float('-inf'))
        max_val = rules.get('max', float('inf'))
        
        if value < min_val:
            raise ValueError(f"Float too small (min: {min_val})")
        
        if value > max_val:
            raise ValueError(f"Float too large (max: {max_val})")
        
        # Validar precisión
        if 'precision' in rules:
            value = round(value, rules['precision'])
        
        return value
    
    def _validate_boolean(self, value: Any) -> bool:
        """Valida un booleano"""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            if value.lower() in ('true', '1', 'yes', 'on'):
                return True
            elif value.lower() in ('false', '0', 'no', 'off'):
                return False
        
        raise ValueError("Invalid boolean value")
    
    def _validate_array(self, value: Any, rules: Dict[str, Any]) -> List[Any]:
        """Valida un array"""
        if not isinstance(value, list):
            raise ValueError("Value must be an array")
        
        # Validar longitud
        min_items = rules.get('min_items', 0)
        max_items = rules.get('max_items', self.config['MAX_ARRAY_LENGTH'])
        
        if len(value) < min_items:
            raise ValueError(f"Array too short (min: {min_items})")
        
        if len(value) > max_items:
            raise ValueError(f"Array too long (max: {max_items})")
        
        # Validar items si hay reglas
        if 'items' in rules:
            validated_items = []
            for i, item in enumerate(value):
                try:
                    validated_item = self._validate_field(f"[{i}]", item, rules['items'])
                    validated_items.append(validated_item)
                except ValueError as e:
                    raise ValueError(f"Array item {i}: {str(e)}")
            return validated_items
        
        return value
    
    def _validate_object(self, value: Any, rules: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
        """Valida un objeto/diccionario"""
        if not isinstance(value, dict):
            raise ValueError("Value must be an object")
        
        # Verificar profundidad máxima
        if depth > self.config['MAX_JSON_DEPTH']:
            raise ValueError(f"Object nesting too deep (max: {self.config['MAX_JSON_DEPTH']})")
        
        # Validar propiedades si hay esquema
        if 'properties' in rules:
            validated_obj = {}
            for prop_name, prop_rules in rules['properties'].items():
                if prop_name in value:
                    validated_obj[prop_name] = self._validate_field(
                        prop_name, value[prop_name], prop_rules
                    )
                elif prop_rules.get('required', False):
                    raise ValueError(f"Required property '{prop_name}' missing")
            
            # Verificar propiedades adicionales
            if not rules.get('additional_properties', True):
                extra_props = set(value.keys()) - set(rules['properties'].keys())
                if extra_props:
                    raise ValueError(f"Additional properties not allowed: {extra_props}")
            
            return validated_obj
        
        return value
    
    def _validate_email(self, value: Any) -> str:
        """Valida un email"""
        value = str(value).strip().lower()
        
        if not re.match(self.patterns['email'], value):
            raise ValueError("Invalid email format")
        
        # Validar longitud
        if len(value) > 254:  # RFC 5321
            raise ValueError("Email too long")
        
        return value
    
    def _validate_url(self, value: Any) -> str:
        """Valida una URL"""
        value = str(value).strip()
        
        if not re.match(self.patterns['url'], value):
            raise ValueError("Invalid URL format")
        
        # Parsear y validar componentes
        try:
            parsed = urllib.parse.urlparse(value)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL structure")
        except Exception:
            raise ValueError("Invalid URL")
        
        return value
    
    def _validate_date(self, value: Any) -> str:
        """Valida una fecha"""
        value = str(value).strip()
        
        if not re.match(self.patterns['date'], value):
            raise ValueError("Invalid date format (expected: YYYY-MM-DD)")
        
        # Validar que sea una fecha válida
        try:
            datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Invalid date")
        
        return value
    
    def _validate_datetime(self, value: Any) -> str:
        """Valida un datetime"""
        value = str(value).strip()
        
        if not re.match(self.patterns['datetime'], value):
            raise ValueError("Invalid datetime format")
        
        # Intentar parsear
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M']:
            try:
                datetime.strptime(value.replace('T', ' '), fmt)
                return value
            except ValueError:
                continue
        
        raise ValueError("Invalid datetime")
    
    def _validate_uuid(self, value: Any) -> str:
        """Valida un UUID"""
        value = str(value).strip().lower()
        
        if not re.match(self.patterns['uuid'], value):
            raise ValueError("Invalid UUID format")
        
        return value
    
    def _validate_phone(self, value: Any) -> str:
        """Valida un número de teléfono"""
        value = str(value).strip()
        
        # Remover caracteres comunes
        value = re.sub(r'[\s\-\(\)]', '', value)
        
        if not re.match(r'^\+?[0-9]{7,15}$', value):
            raise ValueError("Invalid phone number")
        
        return value
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitiza un nombre de archivo
        
        Args:
            filename: Nombre de archivo a sanitizar
            
        Returns:
            str: Nombre de archivo sanitizado
        """
        # Remover path traversal
        filename = os.path.basename(filename)
        
        # Remover caracteres peligrosos
        filename = re.sub(r'[^\w\s\-\.]', '', filename)
        
        # Limitar longitud
        name, ext = os.path.splitext(filename)
        name = name[:200]  # Limitar nombre
        ext = ext[:10]  # Limitar extensión
        
        # Reconstruir
        filename = f"{name}{ext}"
        
        # No permitir nombres vacíos
        if not filename or filename == '.':
            filename = 'unnamed'
        
        return filename
    
    def validate_json_payload(self, max_size: int = None) -> Dict[str, Any]:
        """
        Valida y sanitiza un payload JSON completo
        
        Args:
            max_size: Tamaño máximo del payload
            
        Returns:
            Dict: Payload validado
        """
        # Verificar Content-Type
        if not request.is_json:
            abort(400, 'Content-Type must be application/json')
        
        # Verificar tamaño
        if max_size and request.content_length and request.content_length > max_size:
            abort(413, 'Payload too large')
        
        # Obtener y validar JSON
        try:
            data = request.get_json(force=True)
        except Exception:
            abort(400, 'Invalid JSON')
        
        # Validar que sea un diccionario
        if not isinstance(data, dict):
            abort(400, 'JSON must be an object')
        
        return data


# Instancia global
input_validator = InputValidator()
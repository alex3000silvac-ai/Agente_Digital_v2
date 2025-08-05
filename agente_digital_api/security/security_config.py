"""
security_config.py - Configuración centralizada de seguridad
========================================================

Este módulo gestiona toda la configuración del sistema de seguridad,
permitiendo activar/desactivar componentes y ajustar parámetros.

Características:
- Configuración centralizada
- Validación de configuración
- Profiles de seguridad (dev, staging, prod)
- Hot-reload de configuración
- Exportación/importación de config
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

class SecurityConfig:
    """
    Gestor centralizado de configuración de seguridad
    """
    
    def __init__(self, config_file: Optional[str] = None):
        # Configuración por defecto
        self.default_config = {
            # General
            'SECURITY_ENABLED': True,
            'ENVIRONMENT': os.getenv('FLASK_ENV', 'production'),
            'DEBUG_MODE': False,
            
            # Componentes principales
            'COMPONENTS': {
                'SECURITY_MIDDLEWARE': True,
                'RATE_LIMITING': True,
                'INPUT_VALIDATION': True,
                'SQL_INJECTION_GUARD': True,
                'XSS_PROTECTION': True,
                'CSRF_PROTECTION': True,
                'SESSION_SECURITY': True,
                'CONNECTION_POOL': True,
                'SECURITY_HEADERS': True,
                'SECURE_ERROR_HANDLING': True,
                'AUDIT_LOGGING': True,
                'SECURITY_MONITORING': True,
                'FILE_UPLOAD_SECURITY': True,
                'API_SECURITY': True,
                'ENCRYPTION': True
            },
            
            # Rate Limiting
            'RATE_LIMITING': {
                'REQUESTS_PER_MINUTE': 60,
                'BURST_LIMIT': 100,
                'BLACKLIST_THRESHOLD': 1000,
                'BLACKLIST_DURATION': 3600,
                'WHITELIST_IPS': [],
                'CUSTOM_LIMITS': {}
            },
            
            # Session Security
            'SESSION': {
                'LIFETIME': 3600,
                'IDLE_TIMEOUT': 1800,
                'REGENERATE_ID_INTERVAL': 900,
                'MAX_CONCURRENT_SESSIONS': 3,
                'SECURE_COOKIE': True,
                'BIND_TO_IP': False
            },
            
            # Database
            'DATABASE': {
                'POOL_MIN_SIZE': 10,
                'POOL_MAX_SIZE': 100,
                'CONNECTION_TIMEOUT': 30,
                'IDLE_TIMEOUT': 300,
                'ENABLE_SSL': True
            },
            
            # File Upload
            'FILE_UPLOAD': {
                'MAX_SIZE': 10485760,  # 10MB
                'ALLOWED_EXTENSIONS': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg'],
                'SCAN_FOR_MALWARE': True,
                'USE_RANDOM_NAMES': True
            },
            
            # API Security
            'API': {
                'REQUIRE_AUTHENTICATION': True,
                'JWT_EXPIRATION': 3600,
                'REQUIRE_HTTPS': True,
                'ENABLE_RATE_LIMITING': True,
                'VALIDATE_REQUESTS': True
            },
            
            # Encryption
            'ENCRYPTION': {
                'ALGORITHM': 'AES-256',
                'SALT_ROUNDS': 12,
                'ROTATE_KEYS': False,
                'KEY_ROTATION_DAYS': 90
            },
            
            # Monitoring
            'MONITORING': {
                'ENABLED': True,
                'METRICS_INTERVAL': 60,
                'ALERT_EMAIL': None,
                'ALERT_WEBHOOK': None,
                'LOG_LEVEL': 'INFO'
            },
            
            # Security Headers
            'HEADERS': {
                'HSTS_MAX_AGE': 31536000,
                'CSP_ENABLED': True,
                'FRAME_OPTIONS': 'DENY',
                'CONTENT_TYPE_NOSNIFF': True,
                'XSS_PROTECTION': '1; mode=block'
            }
        }
        
        # Cargar configuración
        self.config = self.default_config.copy()
        self.config_file = config_file
        
        if config_file:
            self.load_from_file(config_file)
        else:
            self.load_from_env()
        
        # Aplicar perfil de seguridad
        self.apply_security_profile()
        
        # Validar configuración
        self.validate_config()
    
    def load_from_file(self, file_path: str):
        """Carga configuración desde archivo"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        # Determinar formato por extensión
        if path.suffix == '.json':
            with open(path, 'r') as f:
                config_data = json.load(f)
        elif path.suffix in ['.yml', '.yaml']:
            with open(path, 'r') as f:
                config_data = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")
        
        # Merge con configuración existente
        self._merge_config(self.config, config_data)
    
    def load_from_env(self):
        """Carga configuración desde variables de entorno"""
        # Mapeo de variables de entorno a configuración
        env_mapping = {
            'SECURITY_ENABLED': 'SECURITY_ENABLED',
            'FLASK_ENV': 'ENVIRONMENT',
            'FLASK_DEBUG': 'DEBUG_MODE',
            
            # Rate limiting
            'RATE_LIMIT_PER_MINUTE': 'RATE_LIMITING.REQUESTS_PER_MINUTE',
            'RATE_LIMIT_BURST': 'RATE_LIMITING.BURST_LIMIT',
            
            # Session
            'SESSION_LIFETIME': 'SESSION.LIFETIME',
            'SESSION_SECURE_COOKIE': 'SESSION.SECURE_COOKIE',
            
            # Database
            'DB_POOL_MAX': 'DATABASE.POOL_MAX_SIZE',
            'DB_POOL_MIN': 'DATABASE.POOL_MIN_SIZE',
            
            # Files
            'MAX_FILE_SIZE': 'FILE_UPLOAD.MAX_SIZE',
            
            # API
            'JWT_ACCESS_TOKEN_EXPIRES': 'API.JWT_EXPIRATION',
            
            # Monitoring
            'MONITORING_ENABLED': 'MONITORING.ENABLED',
            'ALERT_EMAIL': 'MONITORING.ALERT_EMAIL'
        }
        
        for env_var, config_path in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_value(self.config, config_path, self._parse_env_value(value))
    
    def apply_security_profile(self):
        """Aplica perfil de seguridad según el entorno"""
        environment = self.config['ENVIRONMENT'].lower()
        
        profiles = {
            'development': {
                'DEBUG_MODE': True,
                'COMPONENTS': {
                    'RATE_LIMITING': False,
                    'CSRF_PROTECTION': False
                },
                'SESSION': {
                    'SECURE_COOKIE': False
                },
                'API': {
                    'REQUIRE_HTTPS': False
                },
                'HEADERS': {
                    'CSP_ENABLED': False
                }
            },
            'staging': {
                'DEBUG_MODE': False,
                'COMPONENTS': {
                    'RATE_LIMITING': True,
                    'CSRF_PROTECTION': True
                },
                'RATE_LIMITING': {
                    'REQUESTS_PER_MINUTE': 120
                }
            },
            'production': {
                'DEBUG_MODE': False,
                'COMPONENTS': {
                    key: True for key in self.default_config['COMPONENTS']
                },
                'SESSION': {
                    'SECURE_COOKIE': True,
                    'BIND_TO_IP': True
                },
                'API': {
                    'REQUIRE_HTTPS': True
                },
                'FILE_UPLOAD': {
                    'SCAN_FOR_MALWARE': True
                }
            }
        }
        
        if environment in profiles:
            self._merge_config(self.config, profiles[environment])
    
    def validate_config(self):
        """Valida la configuración actual"""
        errors = []
        
        # Validaciones generales
        if self.config['ENVIRONMENT'] == 'production':
            # En producción, ciertas cosas son obligatorias
            if self.config['DEBUG_MODE']:
                errors.append("DEBUG_MODE must be False in production")
            
            if not self.config['SESSION']['SECURE_COOKIE']:
                errors.append("SECURE_COOKIE must be True in production")
            
            if not self.config['API']['REQUIRE_HTTPS']:
                errors.append("REQUIRE_HTTPS must be True in production")
        
        # Validar rangos
        if self.config['RATE_LIMITING']['REQUESTS_PER_MINUTE'] < 1:
            errors.append("REQUESTS_PER_MINUTE must be at least 1")
        
        if self.config['SESSION']['LIFETIME'] < 300:
            errors.append("SESSION_LIFETIME must be at least 300 seconds")
        
        if self.config['DATABASE']['POOL_MAX_SIZE'] < self.config['DATABASE']['POOL_MIN_SIZE']:
            errors.append("POOL_MAX_SIZE must be >= POOL_MIN_SIZE")
        
        # Validar dependencias
        if self.config['COMPONENTS']['API_SECURITY'] and not self.config['COMPONENTS']['SESSION_SECURITY']:
            errors.append("API_SECURITY requires SESSION_SECURITY to be enabled")
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(errors))
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración
        
        Args:
            key: Clave de configuración (soporta notación punto)
            default: Valor por defecto
            
        Returns:
            Valor de configuración
        """
        try:
            value = self.config
            for part in key.split('.'):
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        Establece un valor de configuración
        
        Args:
            key: Clave de configuración (soporta notación punto)
            value: Valor a establecer
        """
        self._set_nested_value(self.config, key, value)
        
        # Re-validar después de cambios
        self.validate_config()
    
    def is_enabled(self, component: str) -> bool:
        """
        Verifica si un componente está habilitado
        
        Args:
            component: Nombre del componente
            
        Returns:
            bool: True si está habilitado
        """
        if not self.config.get('SECURITY_ENABLED', True):
            return False
        
        return self.config.get('COMPONENTS', {}).get(component, False)
    
    def get_component_config(self, component: str) -> Dict[str, Any]:
        """
        Obtiene la configuración específica de un componente
        
        Args:
            component: Nombre del componente
            
        Returns:
            Dict con la configuración del componente
        """
        # Mapeo de componentes a secciones de config
        component_mapping = {
            'RATE_LIMITING': 'RATE_LIMITING',
            'SESSION_SECURITY': 'SESSION',
            'CONNECTION_POOL': 'DATABASE',
            'FILE_UPLOAD_SECURITY': 'FILE_UPLOAD',
            'API_SECURITY': 'API',
            'ENCRYPTION': 'ENCRYPTION',
            'SECURITY_MONITORING': 'MONITORING',
            'SECURITY_HEADERS': 'HEADERS'
        }
        
        config_section = component_mapping.get(component)
        if config_section:
            return self.config.get(config_section, {})
        
        return {}
    
    def export_config(self, format: str = 'json', include_defaults: bool = False) -> str:
        """
        Exporta la configuración actual
        
        Args:
            format: Formato de exportación ('json' o 'yaml')
            include_defaults: Incluir valores por defecto
            
        Returns:
            str: Configuración serializada
        """
        config_to_export = self.config if include_defaults else self._get_non_default_values()
        
        # Agregar metadata
        export_data = {
            'version': '1.0',
            'exported_at': datetime.utcnow().isoformat(),
            'environment': self.config['ENVIRONMENT'],
            'config': config_to_export
        }
        
        if format == 'json':
            return json.dumps(export_data, indent=2)
        elif format == 'yaml':
            return yaml.dump(export_data, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _merge_config(self, base: Dict, updates: Dict):
        """Merge recursivo de configuración"""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _set_nested_value(self, config: Dict, path: str, value: Any):
        """Establece un valor anidado usando notación punto"""
        parts = path.split('.')
        current = config
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    def _parse_env_value(self, value: str) -> Any:
        """Parsea valor de variable de entorno"""
        # Booleanos
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        
        # Números
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # Listas
        if ',' in value:
            return [v.strip() for v in value.split(',')]
        
        return value
    
    def _get_non_default_values(self) -> Dict[str, Any]:
        """Obtiene solo valores que difieren del default"""
        def diff_dict(default, current):
            result = {}
            for key, value in current.items():
                if key not in default:
                    result[key] = value
                elif isinstance(value, dict) and isinstance(default[key], dict):
                    nested_diff = diff_dict(default[key], value)
                    if nested_diff:
                        result[key] = nested_diff
                elif value != default[key]:
                    result[key] = value
            return result
        
        return diff_dict(self.default_config, self.config)
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Obtiene resumen del estado de seguridad"""
        enabled_components = [
            comp for comp, enabled in self.config['COMPONENTS'].items()
            if enabled
        ]
        
        return {
            'environment': self.config['ENVIRONMENT'],
            'security_enabled': self.config['SECURITY_ENABLED'],
            'enabled_components': enabled_components,
            'disabled_components': [
                comp for comp, enabled in self.config['COMPONENTS'].items()
                if not enabled
            ],
            'security_score': self._calculate_security_score(),
            'recommendations': self._get_security_recommendations()
        }
    
    def _calculate_security_score(self) -> int:
        """Calcula un score de seguridad del 0-100"""
        score = 0
        max_score = 0
        
        # Componentes (50 puntos)
        component_value = 50 / len(self.config['COMPONENTS'])
        for enabled in self.config['COMPONENTS'].values():
            max_score += component_value
            if enabled:
                score += component_value
        
        # Configuraciones críticas (50 puntos)
        critical_settings = [
            ('SESSION.SECURE_COOKIE', 10),
            ('API.REQUIRE_HTTPS', 10),
            ('FILE_UPLOAD.SCAN_FOR_MALWARE', 10),
            ('HEADERS.CSP_ENABLED', 10),
            ('MONITORING.ENABLED', 10)
        ]
        
        for setting, points in critical_settings:
            max_score += points
            if self.get(setting):
                score += points
        
        return int((score / max_score) * 100)
    
    def _get_security_recommendations(self) -> List[str]:
        """Obtiene recomendaciones de seguridad"""
        recommendations = []
        
        if self.config['ENVIRONMENT'] == 'production':
            if not self.config['SESSION']['BIND_TO_IP']:
                recommendations.append("Consider enabling SESSION.BIND_TO_IP for additional security")
            
            if not self.config['ENCRYPTION']['ROTATE_KEYS']:
                recommendations.append("Enable key rotation for better security")
            
            if self.config['RATE_LIMITING']['REQUESTS_PER_MINUTE'] > 120:
                recommendations.append("Consider lowering rate limits in production")
        
        if not all(self.config['COMPONENTS'].values()):
            recommendations.append("Some security components are disabled")
        
        return recommendations


# Función helper para crear configuración
def create_security_config(environment: str = None, config_file: str = None) -> SecurityConfig:
    """
    Crea una instancia de configuración de seguridad
    
    Args:
        environment: Entorno (development, staging, production)
        config_file: Archivo de configuración opcional
        
    Returns:
        SecurityConfig: Instancia configurada
    """
    if environment:
        os.environ['FLASK_ENV'] = environment
    
    return SecurityConfig(config_file)
# Sistema de Seguridad Integral para Flask

Este sistema de seguridad proporciona protección completa contra las principales vulnerabilidades web y controles de seguridad empresariales para aplicaciones Flask.

## 🛡️ Características

### Protecciones Principales
- **Rate Limiting** - Protección contra DoS/DDoS y abuso de API
- **Validación de Inputs** - Sanitización y validación de todos los datos de entrada
- **Protección SQL Injection** - Guards automáticos contra inyección SQL
- **Protección XSS** - Sanitización de contenido y Content Security Policy
- **Protección CSRF** - Tokens CSRF y validación de origen
- **Seguridad de Sesiones** - Gestión segura con rotación de IDs y detección de anomalías

### Componentes de Seguridad
- **Connection Pool Seguro** - Pool de conexiones con circuit breaker y health checks
- **Headers de Seguridad** - HSTS, CSP, X-Frame-Options, etc.
- **Manejo Seguro de Errores** - Respuestas seguras sin exposición de información
- **Sistema de Auditoría** - Logging completo de eventos de seguridad
- **Monitoreo en Tiempo Real** - Detección de anomalías y alertas automáticas
- **Seguridad de Archivos** - Validación y escaneo de uploads
- **Seguridad de APIs** - JWT, API Keys, firma de requests
- **Encriptación** - Utilidades de encriptación y hashing seguros

## 🚀 Instalación Rápida

### 1. Dependencias
```bash
pip install flask cryptography bcrypt bleach python-magic redis jsonschema pyjwt
```

### 2. Integración Básica
```python
from flask import Flask
from security import integrate_security

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Integración con una línea
security = integrate_security(app)

if __name__ == '__main__':
    app.run()
```

### 3. Variables de Entorno
```bash
# Configuración básica
FLASK_ENV=production
SECRET_KEY=your-super-secret-key

# Base de datos
DB_HOST=192.168.100.125
DB_DATABASE=AgenteDigitalDB
DB_USERNAME=your-username
DB_PASSWORD=your-password

# Rate limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=100

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_EXPIRES=3600

# Encriptación
APP_ENCRYPTION_KEY=your-encryption-key
BCRYPT_SALT_ROUNDS=12
```

## 📋 Uso Detallado

### Protección de Rutas

```python
from security import require_auth, audit_action, monitor_endpoint

@app.route('/api/protected')
@require_auth('jwt')  # Requiere JWT válido
@audit_action('access_protected')  # Audita el acceso
@monitor_endpoint('protected_access')  # Monitorea métricas
def protected_route():
    from flask import g
    return {'user_id': g.current_user_id}
```

### Validación de Archivos

```python
from security import secure_file_required

@app.route('/upload', methods=['POST'])
@secure_file_required('file')
def upload(validated_file):
    # El archivo ya está validado
    return {'status': 'uploaded'}
```

### Configuración Personalizada

```python
from security import SecurityConfig, integrate_security

# Crear configuración personalizada
config = SecurityConfig()
config.set('RATE_LIMITING.REQUESTS_PER_MINUTE', 120)
config.set('SESSION.BIND_TO_IP', True)
config.set('FILE_UPLOAD.MAX_SIZE', 50 * 1024 * 1024)  # 50MB

# Integrar con configuración
security = integrate_security(app, config=config.config)
```

## 🔧 Configuración por Componente

### Rate Limiting
```python
# Variables de entorno
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=100
RATE_LIMIT_BLACKLIST_THRESHOLD=1000

# Uso programático
from security import rate_limiter

@app.route('/api/endpoint')
@rate_limiter.limit('10 per minute')
def limited_endpoint():
    return {'data': 'limited'}
```

### Validación de Inputs
```python
from security import input_validator

schema = {
    "type": "object",
    "properties": {
        "email": {"type": "string", "format": "email"},
        "age": {"type": "integer", "minimum": 18}
    },
    "required": ["email"]
}

@app.route('/api/validate', methods=['POST'])
@input_validator.validate_json(schema)
def validate_endpoint():
    # Los datos ya están validados
    return {'status': 'valid'}
```

### Protección CSRF
```python
from security import csrf

# En templates HTML
{{ csrf_input() }}

# En APIs
@app.route('/api/form', methods=['POST'])
@csrf.protect
def form_endpoint():
    return {'status': 'protected'}
```

### Encriptación
```python
from security import encrypt_sensitive_data, decrypt_sensitive_data

# Encriptar datos sensibles
encrypted = encrypt_sensitive_data("sensitive data")

# Desencriptar
original = decrypt_sensitive_data(encrypted)
```

## 📊 Monitoreo y Métricas

### Dashboard de Seguridad
```python
from security import security_monitor, get_security_status

@app.route('/security/dashboard')
def security_dashboard():
    return {
        'status': get_security_status(),
        'metrics': security_monitor.get_metrics_summary(),
        'recent_events': security_monitor.get_recent_events(100)
    }
```

### Alertas Personalizadas
```python
from security import security_monitor

def custom_alert_handler(alert):
    print(f"ALERTA: {alert['data']['message']}")
    # Enviar email, webhook, etc.

security_monitor.add_alert_handler(custom_alert_handler)
```

## 🎯 Perfiles de Seguridad

### Desarrollo
```python
from security import quick_setup

security = quick_setup(app, environment='development')
# Automáticamente desactiva HTTPS, CSRF, etc. para desarrollo
```

### Staging
```python
security = quick_setup(app, environment='staging')
# Configuración intermedia para testing
```

### Producción
```python
security = quick_setup(app, environment='production')
# Todas las protecciones activadas
```

## 🚨 Manejo de Errores Seguros

```python
from security import abort_secure

@app.route('/api/sensitive')
def sensitive():
    if not user_has_permission():
        abort_secure(403, "Access denied", reason="insufficient_permissions")
    
    return {'data': 'sensitive'}
```

## 📝 Auditoría

```python
from security import audit_logger

# Auditoría automática con decorador
@audit_action('delete_user', 'user')
def delete_user(user_id):
    pass

# Auditoría manual
audit_logger.log_security_event(
    'suspicious_activity',
    'warning',
    {'ip': request.remote_addr, 'action': 'multiple_login_attempts'}
)
```

## 🔍 API Security

### JWT Authentication
```python
from security import create_jwt_tokens, validate_jwt

# Crear tokens
tokens = create_jwt_tokens(
    user_id='123',
    username='john',
    roles=['user', 'admin']
)

# Validar token
payload = validate_jwt(token)
```

### API Keys
```python
from security import api_security

# Crear API key
credentials = api_security.create_api_key(
    client_id='client123',
    permissions=['read', 'write']
)

# Proteger endpoint
@app.route('/api/webhook')
@api_security.api_key_required
def webhook():
    from flask import g
    client_id = g.api_client_id
    return {'received': True}
```

## 🗂️ Estructura del Sistema

```
security/
├── __init__.py                 # Módulo principal
├── security_integration.py     # Integración central
├── security_config.py         # Configuración centralizada
├── rate_limiter.py            # Rate limiting y protección DoS
├── input_validator.py         # Validación de inputs
├── sql_injection_guard.py     # Protección SQL injection
├── xss_protection.py          # Protección XSS
├── csrf_protection.py         # Protección CSRF
├── session_security.py        # Seguridad de sesiones
├── connection_pool.py          # Pool de conexiones seguro
├── encryption_utils.py        # Encriptación y hashing
├── audit_logger.py           # Sistema de auditoría
├── error_handler.py           # Manejo seguro de errores
├── headers_security.py        # Headers de seguridad HTTP
├── file_upload_security.py    # Seguridad de archivos
├── api_security.py           # Seguridad de APIs
├── monitoring.py              # Monitoreo en tiempo real
└── README.md                  # Esta documentación
```

## ⚙️ Variables de Entorno Completas

```bash
# === CONFIGURACIÓN GENERAL ===
FLASK_ENV=production
SECRET_KEY=your-super-secret-key
SECURITY_ENABLED=true

# === BASE DE DATOS ===
DB_HOST=192.168.100.125
DB_DATABASE=AgenteDigitalDB
DB_USERNAME=your-username
DB_PASSWORD=your-password
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_POOL_MIN=10
DB_POOL_MAX=100
DB_CONNECTION_TIMEOUT=30

# === RATE LIMITING ===
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=100
RATE_LIMIT_BLACKLIST_THRESHOLD=1000
RATE_LIMIT_BLACKLIST_DURATION=3600

# === SESIONES ===
SESSION_LIFETIME=3600
SESSION_IDLE_TIMEOUT=1800
SESSION_SECURE_COOKIE=true
SESSION_REGENERATE_INTERVAL=900
MAX_CONCURRENT_SESSIONS=3

# === JWT ===
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000
JWT_BLACKLIST_ENABLED=true

# === ENCRIPTACIÓN ===
APP_ENCRYPTION_KEY=your-encryption-key
BCRYPT_SALT_ROUNDS=12
ENABLE_FIELD_ENCRYPTION=true

# === ARCHIVOS ===
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=pdf,doc,docx,xls,xlsx,png,jpg,jpeg
SCAN_FOR_MALWARE=true
SECURE_UPLOAD_FOLDER=uploads

# === CSRF ===
ENABLE_CSRF_PROTECTION=true
CSRF_TOKEN_LIFETIME=3600

# === XSS ===
ENABLE_XSS_PROTECTION=true
SANITIZE_HTML=true

# === HEADERS DE SEGURIDAD ===
ENABLE_SECURITY_HEADERS=true
HSTS_ENABLED=true
HSTS_MAX_AGE=31536000
CSP_ENABLED=true
X_FRAME_OPTIONS=DENY

# === AUDITORÍA ===
ENABLE_AUDIT_LOGGING=true
AUDIT_LOG_LEVEL=INFO
AUDIT_LOG_DIR=logs/audit
AUDIT_RETENTION_DAYS=90

# === MONITOREO ===
ENABLE_SECURITY_MONITORING=true
METRICS_INTERVAL=60
ALERT_THRESHOLD_HIGH=100
ALERT_THRESHOLD_CRITICAL=500

# === REDIS (OPCIONAL) ===
USE_REDIS_SESSIONS=false
REDIS_URL=redis://localhost:6379/1

# === PROMETHEUS (OPCIONAL) ===
ENABLE_PROMETHEUS_METRICS=false

# === STATSD (OPCIONAL) ===
ENABLE_STATSD_METRICS=false
STATSD_HOST=localhost
STATSD_PORT=8125
```

## 🛠️ Troubleshooting

### Problemas Comunes

1. **Rate Limiting muy estricto**
   ```python
   # Ajustar límites
   config.set('RATE_LIMITING.REQUESTS_PER_MINUTE', 120)
   ```

2. **CSRF bloqueando requests**
   ```python
   # Deshabilitar para APIs
   config.set('COMPONENTS.CSRF_PROTECTION', False)
   ```

3. **Cookies no funcionan en desarrollo**
   ```python
   # Deshabilitar secure cookies
   config.set('SESSION.SECURE_COOKIE', False)
   ```

### Debugging
```python
# Activar modo debug para seguridad
config.set('DEBUG_MODE', True)

# Ver estado de componentes
from security import get_security_status
print(get_security_status())

# Ver métricas
from security import security_monitor
print(security_monitor.get_metrics_summary())
```

## 📚 Recursos Adicionales

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.0.x/security/)
- [JWT Security Best Practices](https://tools.ietf.org/html/rfc8725)

## 🤝 Contribución

Para contribuir al sistema de seguridad:

1. Seguir las mejores prácticas de seguridad
2. Documentar todos los cambios
3. Incluir tests de seguridad
4. Validar contra OWASP Top 10

## 📄 Licencia

Sistema desarrollado para Agente Digital - Proyecto Derecho Digital.

---

> ⚠️ **Importante**: Este sistema de seguridad es robusto pero debe ser configurado correctamente según tu entorno. Siempre realiza auditorías de seguridad antes de desplegar en producción.
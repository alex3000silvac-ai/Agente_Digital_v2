#!/usr/bin/env python3
"""
Generador de secretos seguros para Agente Digital
Genera claves criptográficamente seguras para uso en producción
"""

import secrets
import string
import base64
import os
from cryptography.fernet import Fernet


def generate_secret_key(length=64):
    """Genera una clave secreta segura"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_jwt_secret():
    """Genera una clave JWT específicamente optimizada"""
    return base64.urlsafe_b64encode(secrets.token_bytes(64)).decode('utf-8')


def generate_fernet_key():
    """Genera una clave Fernet para encriptación simétrica"""
    return Fernet.generate_key().decode('utf-8')


def generate_api_key():
    """Genera una API key segura"""
    return secrets.token_urlsafe(32)


def generate_db_password(length=20):
    """Genera una contraseña segura para base de datos"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_env_template():
    """Crea un template .env con todos los secretos necesarios"""
    
    secrets_config = {
        'SECRET_KEY': generate_secret_key(),
        'JWT_SECRET_KEY': generate_jwt_secret(),
        'ENCRYPTION_KEY': generate_fernet_key(),
        'API_KEY': generate_api_key(),
        'DB_PASSWORD': generate_db_password(),
        'REDIS_PASSWORD': generate_db_password(16),
        'SMTP_PASSWORD': 'your_smtp_password_here',
        'ADMIN_API_KEY': generate_api_key(),
    }
    
    env_content = f"""# Configuración de Seguridad - Agente Digital
# IMPORTANTE: Cambiar todos los valores en producción

# === CLAVES PRINCIPALES ===
SECRET_KEY={secrets_config['SECRET_KEY']}
JWT_SECRET_KEY={secrets_config['JWT_SECRET_KEY']}
ENCRYPTION_KEY={secrets_config['ENCRYPTION_KEY']}

# === BASE DE DATOS ===
DB_SERVER=localhost
DB_NAME=AgenteDigitalDB
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_USERNAME=agentedigital_user
DB_PASSWORD={secrets_config['DB_PASSWORD']}
DB_TRUSTED_CONNECTION=no

# Configuración de pool de conexiones
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=50
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# === REDIS ===
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD={secrets_config['REDIS_PASSWORD']}

# === EMAIL ===
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@domain.com
SMTP_PASSWORD={secrets_config['SMTP_PASSWORD']}
FROM_EMAIL=noreply@agentedigital.cl

# === API KEYS ===
API_KEY={secrets_config['API_KEY']}
ADMIN_API_KEY={secrets_config['ADMIN_API_KEY']}

# === CONFIGURACIÓN DE APLICACIÓN ===
FLASK_ENV=production
DEBUG=False
LOG_LEVEL=INFO
LOG_FILE=/home/agentedigital/logs/app.log

# === URLS ===
FRONTEND_URL=https://agentedigital.cl
BACKEND_URL=https://api.agentedigital.cl

# === SEGURIDAD ===
RATE_LIMITING_ENABLED=true
RATE_LIMIT_PREFIX=rl:agentedigital:
SCAN_FILES=true
MAX_FILE_SIZE=104857600
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true

# === ESCALABILIDAD ===
SCALABILITY_ENABLED=true
CONCURRENT_UPLOADS=10
CACHE_DEFAULT_TIMEOUT=300

# === MONITOREO ===
METRICS_ENABLED=true
HEALTH_CHECK_ENABLED=true
AUDIT_LOG_ENABLED=true
"""
    
    return env_content, secrets_config


def main():
    """Función principal"""
    print("🔐 Generador de Secretos Seguros - Agente Digital")
    print("=" * 50)
    
    # Generar secretos
    env_content, secrets = create_env_template()
    
    # Guardar archivo .env de ejemplo
    with open('.env.example', 'w') as f:
        f.write(env_content)
    
    print("✅ Archivo .env.example creado con secretos seguros")
    print("\n🔑 Secretos generados:")
    print("-" * 30)
    
    for key, value in secrets.items():
        if 'PASSWORD' in key or 'KEY' in key:
            masked_value = value[:8] + "*" * (len(value) - 8)
            print(f"{key}: {masked_value}")
        else:
            print(f"{key}: {value}")
    
    print("\n⚠️  IMPORTANTE:")
    print("1. Copiar .env.example a .env y personalizar")
    print("2. NUNCA commitear el archivo .env")
    print("3. Cambiar credenciales SMTP y DB según tu configuración")
    print("4. Usar diferentes secretos para cada ambiente")
    
    # Crear archivo de documentación de secretos
    docs_content = f"""# Documentación de Secretos - Agente Digital

## Secretos Generados

### Claves Principales
- **SECRET_KEY**: Clave principal de Flask (64 caracteres)
- **JWT_SECRET_KEY**: Clave para tokens JWT (Base64, 64 bytes)
- **ENCRYPTION_KEY**: Clave Fernet para encriptación de datos

### Base de Datos
- **DB_PASSWORD**: Contraseña para usuario de BD (20 caracteres)
- **REDIS_PASSWORD**: Contraseña para Redis (16 caracteres)

### API Keys
- **API_KEY**: Clave para API externa (32 bytes URL-safe)
- **ADMIN_API_KEY**: Clave para endpoints administrativos

## Rotación de Secretos

### Frecuencia Recomendada:
- **SECRET_KEY**: Cada 6 meses
- **JWT_SECRET_KEY**: Cada 3 meses  
- **DB_PASSWORD**: Cada 3 meses
- **API_KEYS**: Cada mes

### Proceso de Rotación:
1. Generar nuevos secretos con este script
2. Actualizar variables de entorno
3. Reiniciar aplicación
4. Verificar funcionamiento
5. Invalidar secretos antiguos

## Seguridad
- Todos los secretos usan `secrets.SystemRandom()`
- Longitudes criptográficamente seguras
- Caracteres especiales incluidos donde apropiado
- Encoding Base64 para claves JWT
"""
    
    with open('SECRETS_README.md', 'w') as f:
        f.write(docs_content)
    
    print("📚 Documentación creada en SECRETS_README.md")


if __name__ == "__main__":
    main()
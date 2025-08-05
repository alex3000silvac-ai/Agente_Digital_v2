# app/fallback_imports.py
# Fallbacks para cuando las dependencias de seguridad no están disponibles

import logging
logger = logging.getLogger(__name__)

# Fallback para magic
try:
    import magic
except ImportError:
    logger.warning("python-magic not available, using fallback")
    class FallbackMagic:
        @staticmethod
        def from_buffer(buffer, mime=True):
            return 'application/octet-stream'
        
        @staticmethod
        def from_file(filepath, mime=True):
            # Determinar MIME type básico por extensión
            ext_mime_map = {
                '.pdf': 'application/pdf',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg', 
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.txt': 'text/plain',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xls': 'application/vnd.ms-excel',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
            
            import os
            _, ext = os.path.splitext(str(filepath))
            return ext_mime_map.get(ext.lower(), 'application/octet-stream')
    
    magic = FallbackMagic()

# Fallback para cryptography
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    logger.warning("cryptography not available, encryption features disabled")
    
    class FallbackFernet:
        def __init__(self, key):
            self.key = key
        
        def encrypt(self, data):
            if isinstance(data, str):
                data = data.encode()
            return data  # Sin encriptación real
        
        def decrypt(self, data):
            if isinstance(data, bytes):
                return data.decode()
            return data
        
        @staticmethod
        def generate_key():
            return b'fallback_key_32_bytes_long_here'
    
    Fernet = FallbackFernet
    CRYPTOGRAPHY_AVAILABLE = False

# Fallback para pyotp
try:
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    logger.warning("pyotp not available, MFA features disabled")
    
    class FallbackTOTP:
        def __init__(self, secret):
            self.secret = secret
        
        def verify(self, token, valid_window=1):
            return token == "123456"  # Token de desarrollo
        
        def provisioning_uri(self, name, issuer_name):
            return f"otpauth://totp/{name}?secret={self.secret}&issuer={issuer_name}"
    
    class FallbackPyOTP:
        @staticmethod
        def random_base32():
            return "FALLBACKSECRET123"
        
        @staticmethod
        def TOTP(secret):
            return FallbackTOTP(secret)
        
        totp = type('obj', (object,), {'TOTP': lambda s: FallbackTOTP(s)})
    
    pyotp = FallbackPyOTP()
    PYOTP_AVAILABLE = False

# Fallback para qrcode
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    logger.warning("qrcode not available, QR code generation disabled")
    
    class FallbackQRCode:
        def __init__(self, *args, **kwargs):
            pass
        
        def add_data(self, data):
            pass
        
        def make(self, fit=True):
            pass
        
        def make_image(self, fill_color="black", back_color="white"):
            # Crear imagen placeholder
            from io import BytesIO
            import base64
            
            # Imagen 1x1 PNG transparente
            placeholder = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
            
            class FallbackImage:
                def save(self, buffer, format='PNG'):
                    buffer.write(placeholder)
            
            return FallbackImage()
    
    class FallbackQRCodeModule:
        QRCode = FallbackQRCode
    
    qrcode = FallbackQRCodeModule()
    QRCODE_AVAILABLE = False

# Fallback para bleach
try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    logger.warning("bleach not available, using basic HTML escaping")
    
    class FallbackBleach:
        @staticmethod
        def clean(text, tags=None, attributes=None, strip=False):
            import html
            return html.escape(text)
    
    bleach = FallbackBleach()
    BLEACH_AVAILABLE = False

# Fallback para marshmallow
try:
    import marshmallow
    from marshmallow import Schema, fields, ValidationError, validates
    MARSHMALLOW_AVAILABLE = True
except ImportError:
    logger.warning("marshmallow not available, using basic validation")
    
    class ValidationError(Exception):
        def __init__(self, messages):
            self.messages = messages
            super().__init__(str(messages))
    
    class FallbackField:
        def __init__(self, required=False, validate=None, **kwargs):
            self.required = required
            self.validate = validate or []
    
    class FallbackFields:
        Str = FallbackField
        Email = FallbackField
        Bool = FallbackField
        
        @staticmethod
        def Str(*args, **kwargs):
            return FallbackField(*args, **kwargs)
        
        @staticmethod
        def Email(*args, **kwargs):
            return FallbackField(*args, **kwargs)
            
        @staticmethod  
        def Bool(*args, **kwargs):
            return FallbackField(*args, **kwargs)
    
    class FallbackSchema:
        def __init__(self):
            pass
        
        def load(self, data):
            return data  # Sin validación real
        
        @staticmethod
        def validates(field_name):
            def decorator(func):
                return func
            return decorator
    
    marshmallow = type('obj', (object,), {
        'Schema': FallbackSchema,
        'fields': FallbackFields,
        'ValidationError': ValidationError,
        'validates': lambda field: lambda func: func
    })()
    
    Schema = FallbackSchema
    fields = FallbackFields
    validates = lambda field: lambda func: func
    MARSHMALLOW_AVAILABLE = False

# Exportar disponibilidad de módulos
__all__ = [
    'magic', 'Fernet', 'pyotp', 'qrcode', 'bleach', 'marshmallow',
    'Schema', 'fields', 'ValidationError', 'validates',
    'CRYPTOGRAPHY_AVAILABLE', 'PYOTP_AVAILABLE', 'QRCODE_AVAILABLE', 
    'BLEACH_AVAILABLE', 'MARSHMALLOW_AVAILABLE'
]
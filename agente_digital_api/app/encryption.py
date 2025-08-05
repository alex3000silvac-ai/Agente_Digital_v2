# app/encryption.py
# Módulo de encriptación para datos sensibles en Agente Digital

import os
import base64
import hashlib
import logging
from typing import Optional, Union, Dict, Any
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    from .fallback_imports import Fernet, CRYPTOGRAPHY_AVAILABLE
    # Crear objetos fallback para otros módulos
    hashes = None
    PBKDF2HMAC = None
    default_backend = None
import secrets

logger = logging.getLogger(__name__)

class EncryptionManager:
    """Gestor centralizado de encriptación para datos sensibles"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Inicializar gestor de encriptación
        
        Args:
            encryption_key: Clave base64 para Fernet, si no se proporciona usa variable de entorno
        """
        self.encryption_key = encryption_key or os.environ.get('ENCRYPTION_KEY')
        if not self.encryption_key:
            raise ValueError("ENCRYPTION_KEY must be provided or set in environment")
        
        try:
            self.fernet = Fernet(self.encryption_key.encode())
        except Exception as e:
            logger.error(f"Error initializing Fernet: {e}")
            raise ValueError("Invalid encryption key format")
    
    def encrypt_string(self, data: str) -> str:
        """
        Encriptar una cadena de texto
        
        Args:
            data: Cadena a encriptar
            
        Returns:
            Cadena encriptada en base64
        """
        if not data:
            return data
        
        try:
            encrypted_data = self.fernet.encrypt(data.encode('utf-8'))
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encrypting string: {e}")
            raise EncryptionError("Failed to encrypt data")
    
    def decrypt_string(self, encrypted_data: str) -> str:
        """
        Desencriptar una cadena de texto
        
        Args:
            encrypted_data: Cadena encriptada en base64
            
        Returns:
            Cadena desencriptada
        """
        if not encrypted_data:
            return encrypted_data
        
        try:
            decoded_data = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Error decrypting string: {e}")
            raise EncryptionError("Failed to decrypt data")
    
    def encrypt_dict(self, data: Dict[str, Any], fields_to_encrypt: list) -> Dict[str, Any]:
        """
        Encriptar campos específicos de un diccionario
        
        Args:
            data: Diccionario con datos
            fields_to_encrypt: Lista de campos a encriptar
            
        Returns:
            Diccionario con campos especificados encriptados
        """
        encrypted_data = data.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field]:
                try:
                    encrypted_data[field] = self.encrypt_string(str(encrypted_data[field]))
                    encrypted_data[f"{field}_encrypted"] = True
                except Exception as e:
                    logger.error(f"Error encrypting field {field}: {e}")
                    raise EncryptionError(f"Failed to encrypt field: {field}")
        
        return encrypted_data
    
    def decrypt_dict(self, data: Dict[str, Any], fields_to_decrypt: list) -> Dict[str, Any]:
        """
        Desencriptar campos específicos de un diccionario
        
        Args:
            data: Diccionario con datos
            fields_to_decrypt: Lista de campos a desencriptar
            
        Returns:
            Diccionario con campos especificados desencriptados
        """
        decrypted_data = data.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data[field]:
                # Solo desencriptar si está marcado como encriptado
                if decrypted_data.get(f"{field}_encrypted", False):
                    try:
                        decrypted_data[field] = self.decrypt_string(decrypted_data[field])
                        decrypted_data.pop(f"{field}_encrypted", None)
                    except Exception as e:
                        logger.error(f"Error decrypting field {field}: {e}")
                        raise EncryptionError(f"Failed to decrypt field: {field}")
        
        return decrypted_data
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> tuple:
        """
        Hashear contraseña con salt usando PBKDF2
        
        Args:
            password: Contraseña a hashear
            salt: Salt opcional, si no se proporciona se genera uno nuevo
            
        Returns:
            Tupla (hash_base64, salt_base64)
        """
        if salt is None:
            salt = secrets.token_bytes(32)
        
        if CRYPTOGRAPHY_AVAILABLE and PBKDF2HMAC:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=64,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            password_hash = kdf.derive(password.encode('utf-8'))
        else:
            # Fallback usando hashlib
            import hashlib
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        
        return (
            base64.b64encode(password_hash).decode('utf-8'),
            base64.b64encode(salt).decode('utf-8')
        )
    
    def verify_password(self, password: str, stored_hash: str, stored_salt: str) -> bool:
        """
        Verificar contraseña contra hash almacenado
        
        Args:
            password: Contraseña a verificar
            stored_hash: Hash almacenado en base64
            stored_salt: Salt almacenado en base64
            
        Returns:
            True si la contraseña es correcta
        """
        try:
            salt = base64.b64decode(stored_salt.encode('utf-8'))
            computed_hash, _ = self.hash_password(password, salt)
            return secrets.compare_digest(computed_hash, stored_hash)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generar token seguro para sesiones, reset passwords, etc.
        
        Args:
            length: Longitud del token en bytes
            
        Returns:
            Token seguro en base64 URL-safe
        """
        return secrets.token_urlsafe(length)
    
    def encrypt_file_content(self, file_content: bytes) -> bytes:
        """
        Encriptar contenido de archivo
        
        Args:
            file_content: Contenido del archivo en bytes
            
        Returns:
            Contenido encriptado
        """
        try:
            return self.fernet.encrypt(file_content)
        except Exception as e:
            logger.error(f"Error encrypting file content: {e}")
            raise EncryptionError("Failed to encrypt file content")
    
    def decrypt_file_content(self, encrypted_content: bytes) -> bytes:
        """
        Desencriptar contenido de archivo
        
        Args:
            encrypted_content: Contenido encriptado
            
        Returns:
            Contenido desencriptado
        """
        try:
            return self.fernet.decrypt(encrypted_content)
        except Exception as e:
            logger.error(f"Error decrypting file content: {e}")
            raise EncryptionError("Failed to decrypt file content")

class EncryptionError(Exception):
    """Excepción personalizada para errores de encriptación"""
    pass

class PIIEncryption:
    """Clase especializada para encriptación de PII (Información Personal Identificable)"""
    
    # Campos que se consideran PII y deben ser encriptados
    PII_FIELDS = [
        'rut', 'cedula', 'dni', 'passport',
        'telefono', 'celular', 'phone',
        'direccion', 'address',
        'fecha_nacimiento', 'birth_date',
        'numero_cuenta', 'account_number',
        'tarjeta_credito', 'credit_card'
    ]
    
    def __init__(self, encryption_manager: EncryptionManager):
        self.encryption_manager = encryption_manager
    
    def encrypt_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encriptar datos PII de usuario
        
        Args:
            user_data: Datos del usuario
            
        Returns:
            Datos con PII encriptado
        """
        fields_to_encrypt = [field for field in self.PII_FIELDS if field in user_data]
        return self.encryption_manager.encrypt_dict(user_data, fields_to_encrypt)
    
    def decrypt_user_data(self, encrypted_user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Desencriptar datos PII de usuario
        
        Args:
            encrypted_user_data: Datos encriptados
            
        Returns:
            Datos con PII desencriptado
        """
        fields_to_decrypt = [field for field in self.PII_FIELDS if field in encrypted_user_data]
        return self.encryption_manager.decrypt_dict(encrypted_user_data, fields_to_decrypt)
    
    def encrypt_empresa_data(self, empresa_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encriptar datos sensibles de empresa
        
        Args:
            empresa_data: Datos de la empresa
            
        Returns:
            Datos con información sensible encriptada
        """
        sensitive_fields = ['rut', 'direccion', 'telefono', 'contacto_emergencia']
        fields_to_encrypt = [field for field in sensitive_fields if field in empresa_data]
        return self.encryption_manager.encrypt_dict(empresa_data, fields_to_encrypt)
    
    def decrypt_empresa_data(self, encrypted_empresa_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Desencriptar datos sensibles de empresa
        """
        sensitive_fields = ['rut', 'direccion', 'telefono', 'contacto_emergencia']
        fields_to_decrypt = [field for field in sensitive_fields if field in encrypted_empresa_data]
        return self.encryption_manager.decrypt_dict(encrypted_empresa_data, fields_to_decrypt)

class AuditEncryption:
    """Clase para encriptación de logs de auditoría"""
    
    def __init__(self, encryption_manager: EncryptionManager):
        self.encryption_manager = encryption_manager
    
    def encrypt_audit_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encriptar datos sensibles en logs de auditoría
        """
        sensitive_fields = ['user_data', 'request_data', 'ip_address']
        fields_to_encrypt = [field for field in sensitive_fields if field in log_data]
        return self.encryption_manager.encrypt_dict(log_data, fields_to_encrypt)
    
    def decrypt_audit_log(self, encrypted_log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Desencriptar datos sensibles en logs de auditoría
        """
        sensitive_fields = ['user_data', 'request_data', 'ip_address']
        fields_to_decrypt = [field for field in sensitive_fields if field in encrypted_log_data]
        return self.encryption_manager.decrypt_dict(encrypted_log_data, fields_to_decrypt)

# Instancia global del gestor de encriptación
_encryption_manager = None
_pii_encryption = None
_audit_encryption = None

def init_encryption(encryption_key: Optional[str] = None):
    """Inicializar sistema de encriptación"""
    global _encryption_manager, _pii_encryption, _audit_encryption
    
    try:
        _encryption_manager = EncryptionManager(encryption_key)
        _pii_encryption = PIIEncryption(_encryption_manager)
        _audit_encryption = AuditEncryption(_encryption_manager)
        
        logger.info("Encryption system initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize encryption system: {e}")
        return False

def get_encryption_manager() -> EncryptionManager:
    """Obtener instancia del gestor de encriptación"""
    if _encryption_manager is None:
        init_encryption()
    return _encryption_manager

def get_pii_encryption() -> PIIEncryption:
    """Obtener instancia del encriptador de PII"""
    if _pii_encryption is None:
        init_encryption()
    return _pii_encryption

def get_audit_encryption() -> AuditEncryption:
    """Obtener instancia del encriptador de auditoría"""
    if _audit_encryption is None:
        init_encryption()
    return _audit_encryption

# Funciones de conveniencia
def encrypt_sensitive_data(data: Dict[str, Any], data_type: str = 'user') -> Dict[str, Any]:
    """
    Función de conveniencia para encriptar datos sensibles
    
    Args:
        data: Datos a encriptar
        data_type: Tipo de datos ('user', 'empresa', 'audit')
        
    Returns:
        Datos con campos sensibles encriptados
    """
    if data_type == 'user':
        return get_pii_encryption().encrypt_user_data(data)
    elif data_type == 'empresa':
        return get_pii_encryption().encrypt_empresa_data(data)
    elif data_type == 'audit':
        return get_audit_encryption().encrypt_audit_log(data)
    else:
        raise ValueError(f"Unknown data type: {data_type}")

def decrypt_sensitive_data(data: Dict[str, Any], data_type: str = 'user') -> Dict[str, Any]:
    """
    Función de conveniencia para desencriptar datos sensibles
    
    Args:
        data: Datos a desencriptar
        data_type: Tipo de datos ('user', 'empresa', 'audit')
        
    Returns:
        Datos con campos sensibles desencriptados
    """
    if data_type == 'user':
        return get_pii_encryption().decrypt_user_data(data)
    elif data_type == 'empresa':
        return get_pii_encryption().decrypt_empresa_data(data)
    elif data_type == 'audit':
        return get_audit_encryption().decrypt_audit_log(data)
    else:
        raise ValueError(f"Unknown data type: {data_type}")

def secure_hash_password(password: str) -> tuple:
    """Función de conveniencia para hashear contraseñas"""
    return get_encryption_manager().hash_password(password)

def verify_password_hash(password: str, stored_hash: str, stored_salt: str) -> bool:
    """Función de conveniencia para verificar contraseñas"""
    return get_encryption_manager().verify_password(password, stored_hash, stored_salt)

def generate_secure_token(length: int = 32) -> str:
    """Función de conveniencia para generar tokens seguros"""
    return get_encryption_manager().generate_secure_token(length)
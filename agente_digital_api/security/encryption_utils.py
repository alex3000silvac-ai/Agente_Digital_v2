"""
encryption_utils.py - Utilidades de encriptación y hashing
======================================================

Este módulo proporciona funciones seguras de encriptación y hashing
para proteger datos sensibles en la aplicación.

Características:
- Encriptación simétrica con AES
- Hashing seguro con bcrypt/argon2
- Generación de claves seguras
- Gestión de secretos
- Firmado y verificación de datos
- Encriptación de campos de base de datos
"""

import os
import base64
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Union, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import bcrypt

class EncryptionManager:
    """
    Gestor central de encriptación y seguridad criptográfica
    """
    
    def __init__(self):
        self.config = {
            'ENCRYPTION_KEY': os.getenv('APP_ENCRYPTION_KEY'),
            'SALT_ROUNDS': int(os.getenv('BCRYPT_SALT_ROUNDS', 12)),
            'TOKEN_LENGTH': int(os.getenv('TOKEN_LENGTH', 32)),
            'KEY_DERIVATION_ITERATIONS': int(os.getenv('KEY_ITERATIONS', 100000)),
            'ENABLE_FIELD_ENCRYPTION': os.getenv('ENABLE_FIELD_ENCRYPTION', 'true').lower() == 'true',
            'ROTATE_KEYS': os.getenv('ROTATE_ENCRYPTION_KEYS', 'false').lower() == 'true',
            'KEY_ROTATION_INTERVAL': int(os.getenv('KEY_ROTATION_DAYS', 90))
        }
        
        # Inicializar clave de encriptación
        self._init_encryption_key()
        
        # Cache de Fernet instances
        self.fernet_cache = {}
        
        # Registro de claves para rotación
        self.key_registry = []
    
    def _init_encryption_key(self):
        """Inicializa o genera la clave de encriptación principal"""
        if not self.config['ENCRYPTION_KEY']:
            # Generar nueva clave si no existe
            self.config['ENCRYPTION_KEY'] = Fernet.generate_key().decode()
            # En producción, esta clave debe almacenarse de forma segura
            print(f"⚠️  ADVERTENCIA: Nueva clave de encriptación generada.")
            print(f"   Guarde esta clave de forma segura: {self.config['ENCRYPTION_KEY']}")
        
        # Crear instancia Fernet principal
        self.fernet = Fernet(self.config['ENCRYPTION_KEY'].encode())
    
    def encrypt(self, data: Union[str, bytes], context: str = 'default') -> str:
        """
        Encripta datos usando encriptación simétrica
        
        Args:
            data: Datos a encriptar
            context: Contexto de encriptación para diferentes claves
            
        Returns:
            str: Datos encriptados en base64
        """
        if not self.config['ENABLE_FIELD_ENCRYPTION']:
            return data if isinstance(data, str) else data.decode()
        
        # Convertir a bytes si es necesario
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # Obtener Fernet para el contexto
        fernet = self._get_fernet_for_context(context)
        
        # Encriptar
        encrypted = fernet.encrypt(data)
        
        # Retornar como string base64
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str, context: str = 'default') -> str:
        """
        Desencripta datos
        
        Args:
            encrypted_data: Datos encriptados en base64
            context: Contexto de encriptación
            
        Returns:
            str: Datos desencriptados
        """
        if not self.config['ENABLE_FIELD_ENCRYPTION']:
            return encrypted_data
        
        try:
            # Decodificar base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            
            # Obtener Fernet para el contexto
            fernet = self._get_fernet_for_context(context)
            
            # Desencriptar
            decrypted = fernet.decrypt(encrypted_bytes)
            
            return decrypted.decode('utf-8')
        except Exception as e:
            # Si falla la desencriptación, puede ser datos no encriptados
            return encrypted_data
    
    def _get_fernet_for_context(self, context: str) -> Fernet:
        """Obtiene instancia Fernet para un contexto específico"""
        if context not in self.fernet_cache:
            # Derivar clave específica del contexto
            context_key = self._derive_key(
                self.config['ENCRYPTION_KEY'].encode(),
                context.encode()
            )
            self.fernet_cache[context] = Fernet(context_key)
        
        return self.fernet_cache[context]
    
    def _derive_key(self, master_key: bytes, salt: bytes) -> bytes:
        """Deriva una clave usando PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.config['KEY_DERIVATION_ITERATIONS'],
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(master_key))
    
    def hash_password(self, password: str) -> str:
        """
        Hashea una contraseña usando bcrypt
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            str: Hash de la contraseña
        """
        # Generar salt y hashear
        salt = bcrypt.gensalt(rounds=self.config['SALT_ROUNDS'])
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verifica una contraseña contra su hash
        
        Args:
            password: Contraseña en texto plano
            hashed: Hash almacenado
            
        Returns:
            bool: True si coincide
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed.encode('utf-8')
            )
        except:
            return False
    
    def generate_token(self, length: Optional[int] = None) -> str:
        """
        Genera un token aleatorio seguro
        
        Args:
            length: Longitud del token (por defecto usa config)
            
        Returns:
            str: Token seguro
        """
        length = length or self.config['TOKEN_LENGTH']
        return secrets.token_urlsafe(length)
    
    def generate_api_key(self) -> Tuple[str, str]:
        """
        Genera un par de API key/secret
        
        Returns:
            tuple: (api_key, api_secret)
        """
        api_key = f"ak_{secrets.token_urlsafe(24)}"
        api_secret = f"as_{secrets.token_urlsafe(32)}"
        
        return api_key, api_secret
    
    def sign_data(self, data: Union[str, bytes], key: Optional[str] = None) -> str:
        """
        Firma datos usando HMAC
        
        Args:
            data: Datos a firmar
            key: Clave para firmar (usa master key por defecto)
            
        Returns:
            str: Firma en hexadecimal
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        signing_key = (key or self.config['ENCRYPTION_KEY']).encode('utf-8')
        
        signature = hmac.new(
            signing_key,
            data,
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_signature(self, data: Union[str, bytes], signature: str,
                        key: Optional[str] = None) -> bool:
        """
        Verifica la firma de datos
        
        Args:
            data: Datos firmados
            signature: Firma a verificar
            key: Clave de firma
            
        Returns:
            bool: True si la firma es válida
        """
        expected_signature = self.sign_data(data, key)
        return hmac.compare_digest(signature, expected_signature)
    
    def encrypt_field(self, field_value: Any, field_name: str) -> str:
        """
        Encripta un campo específico de base de datos
        
        Args:
            field_value: Valor del campo
            field_name: Nombre del campo (usado como contexto)
            
        Returns:
            str: Valor encriptado
        """
        if field_value is None:
            return None
        
        # Convertir a string si es necesario
        str_value = str(field_value)
        
        # Encriptar con contexto del campo
        return self.encrypt(str_value, context=f"field_{field_name}")
    
    def decrypt_field(self, encrypted_value: str, field_name: str) -> Any:
        """
        Desencripta un campo de base de datos
        
        Args:
            encrypted_value: Valor encriptado
            field_name: Nombre del campo
            
        Returns:
            Valor desencriptado
        """
        if encrypted_value is None:
            return None
        
        return self.decrypt(encrypted_value, context=f"field_{field_name}")
    
    def create_time_limited_token(self, data: dict, expires_in: int = 3600) -> str:
        """
        Crea un token con tiempo de expiración
        
        Args:
            data: Datos a incluir en el token
            expires_in: Segundos hasta expiración
            
        Returns:
            str: Token encriptado
        """
        # Agregar timestamp de expiración
        token_data = data.copy()
        token_data['expires_at'] = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
        
        # Serializar y encriptar
        import json
        serialized = json.dumps(token_data)
        
        return self.encrypt(serialized, context='time_token')
    
    def verify_time_limited_token(self, token: str) -> Optional[dict]:
        """
        Verifica y decodifica un token con tiempo límite
        
        Args:
            token: Token a verificar
            
        Returns:
            dict: Datos del token si es válido, None si expiró
        """
        try:
            # Desencriptar
            decrypted = self.decrypt(token, context='time_token')
            
            # Deserializar
            import json
            token_data = json.loads(decrypted)
            
            # Verificar expiración
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            if datetime.utcnow() > expires_at:
                return None
            
            # Remover campo de expiración
            del token_data['expires_at']
            
            return token_data
            
        except:
            return None
    
    def rotate_encryption_key(self, new_key: Optional[str] = None) -> str:
        """
        Rota la clave de encriptación principal
        
        Args:
            new_key: Nueva clave (genera una si no se proporciona)
            
        Returns:
            str: Nueva clave
        """
        # Guardar clave antigua
        old_key = self.config['ENCRYPTION_KEY']
        self.key_registry.append({
            'key': old_key,
            'retired_at': datetime.utcnow().isoformat(),
            'fernet': self.fernet
        })
        
        # Establecer nueva clave
        if not new_key:
            new_key = Fernet.generate_key().decode()
        
        self.config['ENCRYPTION_KEY'] = new_key
        self.fernet = Fernet(new_key.encode())
        
        # Limpiar cache
        self.fernet_cache.clear()
        
        return new_key
    
    def re_encrypt_with_new_key(self, encrypted_data: str, 
                               old_key_index: int = -1) -> str:
        """
        Re-encripta datos con la nueva clave
        
        Args:
            encrypted_data: Datos encriptados con clave antigua
            old_key_index: Índice de la clave antigua en el registro
            
        Returns:
            str: Datos re-encriptados con nueva clave
        """
        # Obtener Fernet antiguo
        old_fernet = self.key_registry[old_key_index]['fernet']
        
        # Desencriptar con clave antigua
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = old_fernet.decrypt(encrypted_bytes)
        
        # Re-encriptar con nueva clave
        return self.encrypt(decrypted)
    
    def secure_compare(self, a: str, b: str) -> bool:
        """
        Comparación segura de strings (previene timing attacks)
        
        Args:
            a: Primera cadena
            b: Segunda cadena
            
        Returns:
            bool: True si son iguales
        """
        return hmac.compare_digest(a.encode(), b.encode())
    
    def hash_file(self, file_path: str, algorithm: str = 'sha256') -> str:
        """
        Calcula el hash de un archivo
        
        Args:
            file_path: Ruta del archivo
            algorithm: Algoritmo de hash
            
        Returns:
            str: Hash del archivo
        """
        hash_func = getattr(hashlib, algorithm)()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    def generate_otp(self, secret: str, counter: int = None) -> str:
        """
        Genera un One-Time Password (OTP)
        
        Args:
            secret: Secreto compartido
            counter: Contador para HOTP (usa tiempo para TOTP si es None)
            
        Returns:
            str: Código OTP de 6 dígitos
        """
        import time
        import struct
        
        # Usar tiempo actual si no hay contador
        if counter is None:
            counter = int(time.time() // 30)  # TOTP con ventana de 30s
        
        # Generar HMAC
        counter_bytes = struct.pack('>Q', counter)
        hmac_hash = hmac.new(
            base64.b32decode(secret),
            counter_bytes,
            hashlib.sha1
        ).digest()
        
        # Extraer código dinámico
        offset = hmac_hash[-1] & 0x0f
        code = struct.unpack('>I', hmac_hash[offset:offset + 4])[0]
        code &= 0x7fffffff
        code %= 1000000
        
        return f"{code:06d}"


# Instancia global
encryption_manager = EncryptionManager()


# Funciones helper para compatibilidad
def encrypt_sensitive_data(data: str) -> str:
    """Helper para encriptar datos sensibles"""
    return encryption_manager.encrypt(data)

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Helper para desencriptar datos sensibles"""
    return encryption_manager.decrypt(encrypted_data)

def hash_user_password(password: str) -> str:
    """Helper para hashear contraseñas"""
    return encryption_manager.hash_password(password)

def verify_user_password(password: str, hashed: str) -> bool:
    """Helper para verificar contraseñas"""
    return encryption_manager.verify_password(password, hashed)
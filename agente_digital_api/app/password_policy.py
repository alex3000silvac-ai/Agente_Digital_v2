# app/password_policy.py
# Política de contraseñas seguras para Agente Digital

import re
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import requests
import os

logger = logging.getLogger(__name__)

@dataclass
class PasswordPolicy:
    """Configuración de política de contraseñas"""
    min_length: int = 12
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special_chars: bool = True
    min_special_chars: int = 1
    disallow_common_passwords: bool = True
    disallow_user_info: bool = True
    disallow_repeated_chars: int = 3
    disallow_sequential_chars: bool = True
    password_history_count: int = 5
    password_expiry_days: int = 90
    account_lockout_attempts: int = 5
    account_lockout_duration: int = 30  # minutos

class PasswordValidator:
    """Validador de contraseñas con políticas de seguridad"""
    
    def __init__(self, policy: PasswordPolicy = None):
        self.policy = policy or PasswordPolicy()
        self.common_passwords = self._load_common_passwords()
        self.special_chars = "!@#$%^&*(),.?\":{}|<>[]\\/-_=+"
    
    def _load_common_passwords(self) -> set:
        """Cargar lista de contraseñas comunes"""
        common_passwords = {
            # Top contraseñas más comunes
            "123456", "password", "123456789", "12345678", "12345",
            "1234567", "1234567890", "qwerty", "abc123", "million2",
            "000000", "1234", "iloveyou", "aaron431", "password1",
            "qqww1122", "123", "omgpop", "123321", "654321",
            "qwertyuiop", "qwer1234", "123abc", "a123456", "1q2w3e4r",
            "admin", "administrator", "root", "user", "guest",
            "demo", "test", "123qwe", "1qaz2wsx", "welcome",
            "monkey", "dragon", "letmein", "baseball", "trustno1",
            "hello", "freedom", "whatever", "qazwsx", "ninja",
            # Contraseñas en español
            "contraseña", "clave123", "acceso", "seguridad", "admin123",
            "usuario", "sistema", "empresa", "chile123", "santiago",
            "password123", "clave", "pass123", "administrador"
        }
        
        # Intentar cargar archivo de contraseñas comunes si existe
        common_passwords_file = os.path.join(os.path.dirname(__file__), 'common_passwords.txt')
        if os.path.exists(common_passwords_file):
            try:
                with open(common_passwords_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        password = line.strip().lower()
                        if password:
                            common_passwords.add(password)
            except Exception as e:
                logger.warning(f"Could not load common passwords file: {e}")
        
        return common_passwords
    
    def validate_password(self, 
                         password: str, 
                         user_info: Dict[str, str] = None,
                         password_history: List[str] = None) -> Tuple[bool, List[str]]:
        """
        Validar contraseña contra la política
        
        Args:
            password: Contraseña a validar
            user_info: Información del usuario (nombre, email, etc.)
            password_history: Historial de contraseñas del usuario
            
        Returns:
            Tupla (es_válida, lista_errores)
        """
        errors = []
        
        # Validar longitud
        if len(password) < self.policy.min_length:
            errors.append(f"La contraseña debe tener al menos {self.policy.min_length} caracteres")
        
        if len(password) > self.policy.max_length:
            errors.append(f"La contraseña no puede exceder {self.policy.max_length} caracteres")
        
        # Validar caracteres requeridos
        if self.policy.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("La contraseña debe contener al menos una letra mayúscula")
        
        if self.policy.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("La contraseña debe contener al menos una letra minúscula")
        
        if self.policy.require_digits and not re.search(r'\d', password):
            errors.append("La contraseña debe contener al menos un número")
        
        if self.policy.require_special_chars:
            special_count = sum(1 for char in password if char in self.special_chars)
            if special_count < self.policy.min_special_chars:
                errors.append(f"La contraseña debe contener al menos {self.policy.min_special_chars} carácter(es) especial(es): {self.special_chars}")
        
        # Validar caracteres repetidos
        if self.policy.disallow_repeated_chars > 0:
            if self._has_repeated_chars(password, self.policy.disallow_repeated_chars):
                errors.append(f"La contraseña no puede tener más de {self.policy.disallow_repeated_chars} caracteres consecutivos iguales")
        
        # Validar caracteres secuenciales
        if self.policy.disallow_sequential_chars:
            if self._has_sequential_chars(password):
                errors.append("La contraseña no puede contener secuencias de caracteres (ej: 123, abc)")
        
        # Validar contra contraseñas comunes
        if self.policy.disallow_common_passwords:
            if password.lower() in self.common_passwords:
                errors.append("Esta contraseña es muy común y no está permitida")
        
        # Validar contra información del usuario
        if self.policy.disallow_user_info and user_info:
            if self._contains_user_info(password, user_info):
                errors.append("La contraseña no puede contener información personal")
        
        # Validar historial de contraseñas
        if password_history:
            if self._is_in_history(password, password_history):
                errors.append(f"No puede reutilizar las últimas {self.policy.password_history_count} contraseñas")
        
        # Verificar contra base de datos de brechas (opcional)
        if self._is_pwned_password(password):
            errors.append("Esta contraseña ha sido comprometida en brechas de seguridad conocidas")
        
        return len(errors) == 0, errors
    
    def _has_repeated_chars(self, password: str, max_repeated: int) -> bool:
        """Verificar si tiene caracteres repetidos consecutivos"""
        count = 1
        for i in range(1, len(password)):
            if password[i] == password[i-1]:
                count += 1
                if count > max_repeated:
                    return True
            else:
                count = 1
        return False
    
    def _has_sequential_chars(self, password: str) -> bool:
        """Verificar si tiene caracteres secuenciales"""
        sequences = [
            "0123456789", "abcdefghijklmnopqrstuvwxyz", "qwertyuiop",
            "asdfghjkl", "zxcvbnm", "9876543210", "zyxwvutsrqponmlkjihgfedcba"
        ]
        
        password_lower = password.lower()
        
        for seq in sequences:
            for i in range(len(seq) - 2):
                if seq[i:i+3] in password_lower:
                    return True
        
        return False
    
    def _contains_user_info(self, password: str, user_info: Dict[str, str]) -> bool:
        """Verificar si contiene información del usuario"""
        password_lower = password.lower()
        
        # Campos a verificar
        fields_to_check = ['nombre', 'apellido', 'username', 'email', 'empresa']
        
        for field in fields_to_check:
            if field in user_info and user_info[field]:
                value = user_info[field].lower()
                
                # Verificar valor completo
                if len(value) >= 3 and value in password_lower:
                    return True
                
                # Verificar partes del email
                if field == 'email' and '@' in value:
                    username_part = value.split('@')[0]
                    if len(username_part) >= 3 and username_part in password_lower:
                        return True
        
        return False
    
    def _is_in_history(self, password: str, password_history: List[str]) -> bool:
        """Verificar si la contraseña está en el historial"""
        from werkzeug.security import check_password_hash
        
        for old_password_hash in password_history[:self.policy.password_history_count]:
            if check_password_hash(old_password_hash, password):
                return True
        
        return False
    
    def _is_pwned_password(self, password: str) -> bool:
        """Verificar contra API de HaveIBeenPwned (opcional)"""
        try:
            # Calcular hash SHA-1 de la contraseña
            sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
            prefix = sha1_hash[:5]
            suffix = sha1_hash[5:]
            
            # Consultar API de HaveIBeenPwned
            url = f"https://api.pwnedpasswords.com/range/{prefix}"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                # Buscar el suffix en la respuesta
                for line in response.text.splitlines():
                    hash_suffix, count = line.split(':')
                    if hash_suffix == suffix:
                        # La contraseña está en la base de datos de brechas
                        logger.warning(f"Password found in breach database with {count} occurrences")
                        return True
            
            return False
            
        except Exception as e:
            # Si hay error en la consulta, no bloquear la validación
            logger.warning(f"Could not check pwned passwords: {e}")
            return False
    
    def generate_password_suggestions(self, user_info: Dict[str, str] = None) -> List[str]:
        """Generar sugerencias de contraseñas seguras"""
        import secrets
        import string
        
        suggestions = []
        
        # Generar diferentes tipos de contraseñas
        for _ in range(3):
            # Contraseña con palabras y números
            words = ["Secure", "Digital", "Agent", "System", "Access", "Private", "Strong", "Shield"]
            word = secrets.choice(words)
            numbers = ''.join(secrets.choice(string.digits) for _ in range(3))
            special = secrets.choice(self.special_chars)
            
            suggestion = f"{word}{numbers}{special}"
            suggestions.append(suggestion)
        
        # Contraseña completamente aleatoria
        alphabet = string.ascii_letters + string.digits + self.special_chars
        random_password = ''.join(secrets.choice(alphabet) for _ in range(16))
        suggestions.append(random_password)
        
        return suggestions

class PasswordManager:
    """Gestor de contraseñas con políticas y historial"""
    
    def __init__(self, policy: PasswordPolicy = None):
        self.policy = policy or PasswordPolicy()
        self.validator = PasswordValidator(self.policy)
    
    def validate_and_hash_password(self, 
                                  password: str,
                                  user_info: Dict[str, str] = None,
                                  password_history: List[str] = None) -> Tuple[bool, str, List[str]]:
        """
        Validar y hashear contraseña
        
        Returns:
            Tupla (es_válida, hash_contraseña, errores)
        """
        is_valid, errors = self.validator.validate_password(password, user_info, password_history)
        
        if is_valid:
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
            return True, password_hash, []
        
        return False, '', errors
    
    def is_password_expired(self, last_change_date: datetime) -> bool:
        """Verificar si la contraseña ha expirado"""
        if self.policy.password_expiry_days <= 0:
            return False
        
        expiry_date = last_change_date + timedelta(days=self.policy.password_expiry_days)
        return datetime.now() > expiry_date
    
    def days_until_expiry(self, last_change_date: datetime) -> int:
        """Calcular días hasta que expire la contraseña"""
        if self.policy.password_expiry_days <= 0:
            return -1
        
        expiry_date = last_change_date + timedelta(days=self.policy.password_expiry_days)
        days_left = (expiry_date - datetime.now()).days
        return max(0, days_left)
    
    def should_warn_about_expiry(self, last_change_date: datetime, warning_days: int = 7) -> bool:
        """Verificar si debe mostrar advertencia de expiración"""
        days_left = self.days_until_expiry(last_change_date)
        return 0 <= days_left <= warning_days

class AccountLockoutManager:
    """Gestor de bloqueo de cuentas por intentos fallidos"""
    
    def __init__(self, policy: PasswordPolicy = None):
        self.policy = policy or PasswordPolicy()
        self.failed_attempts = {}  # En producción usar Redis
    
    def record_failed_attempt(self, username: str) -> int:
        """Registrar intento fallido de login"""
        current_time = datetime.now()
        
        if username not in self.failed_attempts:
            self.failed_attempts[username] = {
                'count': 0,
                'first_attempt': current_time,
                'last_attempt': current_time,
                'locked_until': None
            }
        
        self.failed_attempts[username]['count'] += 1
        self.failed_attempts[username]['last_attempt'] = current_time
        
        # Verificar si debe bloquear la cuenta
        if self.failed_attempts[username]['count'] >= self.policy.account_lockout_attempts:
            lockout_until = current_time + timedelta(minutes=self.policy.account_lockout_duration)
            self.failed_attempts[username]['locked_until'] = lockout_until
            
            logger.warning(f"Account {username} locked due to {self.failed_attempts[username]['count']} failed attempts")
        
        return self.failed_attempts[username]['count']
    
    def is_account_locked(self, username: str) -> Tuple[bool, Optional[datetime]]:
        """Verificar si la cuenta está bloqueada"""
        if username not in self.failed_attempts:
            return False, None
        
        account_data = self.failed_attempts[username]
        locked_until = account_data.get('locked_until')
        
        if locked_until and datetime.now() < locked_until:
            return True, locked_until
        
        # Si ya pasó el tiempo de bloqueo, limpiar datos
        if locked_until and datetime.now() >= locked_until:
            self.reset_failed_attempts(username)
        
        return False, None
    
    def reset_failed_attempts(self, username: str):
        """Resetear intentos fallidos (después de login exitoso)"""
        if username in self.failed_attempts:
            del self.failed_attempts[username]
    
    def get_lockout_time_remaining(self, username: str) -> int:
        """Obtener minutos restantes de bloqueo"""
        is_locked, locked_until = self.is_account_locked(username)
        
        if is_locked and locked_until:
            remaining = (locked_until - datetime.now()).total_seconds() / 60
            return max(0, int(remaining))
        
        return 0

# Instancias globales
_password_manager = None
_lockout_manager = None

def init_password_system(policy: PasswordPolicy = None):
    """Inicializar sistema de contraseñas"""
    global _password_manager, _lockout_manager
    
    try:
        _password_manager = PasswordManager(policy)
        _lockout_manager = AccountLockoutManager(policy)
        logger.info("Password system initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize password system: {e}")
        return False

def get_password_manager() -> PasswordManager:
    """Obtener instancia del gestor de contraseñas"""
    if _password_manager is None:
        init_password_system()
    return _password_manager

def get_lockout_manager() -> AccountLockoutManager:
    """Obtener instancia del gestor de bloqueos"""
    if _lockout_manager is None:
        init_password_system()
    return _lockout_manager

# Funciones de conveniencia
def validate_password(password: str, user_info: Dict[str, str] = None) -> Tuple[bool, List[str]]:
    """Función de conveniencia para validar contraseña"""
    manager = get_password_manager()
    return manager.validator.validate_password(password, user_info)

def create_secure_password(password: str, user_info: Dict[str, str] = None) -> Tuple[bool, str, List[str]]:
    """Función de conveniencia para crear contraseña segura"""
    manager = get_password_manager()
    return manager.validate_and_hash_password(password, user_info)
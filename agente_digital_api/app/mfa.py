# app/mfa.py
# Sistema de Autenticación Multifactor (MFA) para Agente Digital

import os
try:
    import qrcode
    import pyotp
    MFA_AVAILABLE = True
except ImportError:
    from .fallback_imports import qrcode, pyotp
    MFA_AVAILABLE = False
import logging
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from flask import current_app
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

class MFAManager:
    """Gestor de autenticación multifactor"""
    
    def __init__(self):
        self.app_name = "Agente Digital"
        self.issuer_name = "AgenteDigital.cl"
        
    def generate_secret_key(self) -> str:
        """Generar clave secreta para TOTP"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, user_email: str, secret_key: str) -> str:
        """
        Generar código QR para configurar TOTP
        
        Args:
            user_email: Email del usuario
            secret_key: Clave secreta TOTP
            
        Returns:
            Código QR en formato base64
        """
        try:
            # Crear URI para TOTP
            totp_uri = pyotp.totp.TOTP(secret_key).provisioning_uri(
                name=user_email,
                issuer_name=self.issuer_name
            )
            
            # Generar código QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            # Crear imagen
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            raise MFAError("Failed to generate QR code")
    
    def verify_totp_token(self, secret_key: str, token: str, window: int = 1) -> bool:
        """
        Verificar token TOTP
        
        Args:
            secret_key: Clave secreta del usuario
            token: Token de 6 dígitos
            window: Ventana de tiempo permitida (1 = ±30 segundos)
            
        Returns:
            True si el token es válido
        """
        try:
            totp = pyotp.TOTP(secret_key)
            return totp.verify(token, valid_window=window)
        except Exception as e:
            logger.error(f"Error verifying TOTP token: {e}")
            return False
    
    def generate_backup_codes(self, count: int = 10) -> list:
        """
        Generar códigos de respaldo
        
        Args:
            count: Número de códigos a generar
            
        Returns:
            Lista de códigos de respaldo
        """
        codes = []
        for _ in range(count):
            # Generar código de 8 caracteres
            code = secrets.token_hex(4).upper()
            # Formatear como XXXX-XXXX
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        
        return codes
    
    def verify_backup_code(self, user_backup_codes: list, provided_code: str) -> Tuple[bool, list]:
        """
        Verificar código de respaldo
        
        Args:
            user_backup_codes: Lista de códigos de respaldo del usuario
            provided_code: Código proporcionado por el usuario
            
        Returns:
            Tupla (es_válido, códigos_restantes)
        """
        provided_code = provided_code.strip().upper()
        
        if provided_code in user_backup_codes:
            # Remover código usado
            remaining_codes = [code for code in user_backup_codes if code != provided_code]
            return True, remaining_codes
        
        return False, user_backup_codes

class SMSProvider:
    """Proveedor de SMS para MFA (implementación básica)"""
    
    def __init__(self):
        self.enabled = os.environ.get('SMS_ENABLED', 'false').lower() == 'true'
        self.api_key = os.environ.get('SMS_API_KEY')
        self.api_url = os.environ.get('SMS_API_URL')
    
    def send_sms(self, phone_number: str, message: str) -> bool:
        """
        Enviar SMS (implementación placeholder)
        
        Args:
            phone_number: Número de teléfono
            message: Mensaje a enviar
            
        Returns:
            True si se envió correctamente
        """
        if not self.enabled:
            logger.warning("SMS provider not enabled")
            return False
        
        try:
            # Aquí implementar integración con proveedor SMS real
            # Por ejemplo: Twilio, AWS SNS, etc.
            logger.info(f"SMS sent to {phone_number}: {message}")
            return True
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False

class EmailMFA:
    """Proveedor de MFA por email"""
    
    def __init__(self):
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        self.from_email = os.environ.get('FROM_EMAIL', 'noreply@agentedigital.cl')
    
    def generate_email_code(self, length: int = 6) -> str:
        """Generar código numérico para email"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])
    
    def send_verification_code(self, email: str, code: str) -> bool:
        """
        Enviar código de verificación por email
        
        Args:
            email: Email del usuario
            code: Código de verificación
            
        Returns:
            True si se envió correctamente
        """
        try:
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = email
            msg['Subject'] = "Código de Verificación - Agente Digital"
            
            # Cuerpo del mensaje
            body = f"""
            <html>
            <body>
                <h2>Código de Verificación</h2>
                <p>Su código de verificación para Agente Digital es:</p>
                <h1 style="color: #2E86AB; font-size: 32px; letter-spacing: 5px;">{code}</h1>
                <p>Este código expira en 10 minutos.</p>
                <p>Si no solicitó este código, ignore este email.</p>
                <br>
                <p>Saludos,<br>Equipo Agente Digital</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                text = msg.as_string()
                server.sendmail(self.from_email, email, text)
            
            logger.info(f"Verification code sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending verification email: {e}")
            return False

class MFASession:
    """Gestor de sesiones MFA"""
    
    def __init__(self):
        self.sessions = {}  # En producción usar Redis
        self.session_timeout = 300  # 5 minutos
    
    def create_mfa_session(self, user_id: int, mfa_method: str) -> str:
        """
        Crear sesión MFA temporal
        
        Args:
            user_id: ID del usuario
            mfa_method: Método MFA ('totp', 'email', 'sms')
            
        Returns:
            Token de sesión MFA
        """
        session_token = secrets.token_urlsafe(32)
        
        self.sessions[session_token] = {
            'user_id': user_id,
            'mfa_method': mfa_method,
            'created_at': datetime.now(),
            'verified': False,
            'attempts': 0
        }
        
        return session_token
    
    def verify_mfa_session(self, session_token: str, verification_code: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Verificar sesión MFA
        
        Args:
            session_token: Token de sesión
            verification_code: Código de verificación
            
        Returns:
            Tupla (es_válido, datos_sesión)
        """
        if session_token not in self.sessions:
            return False, {}
        
        session_data = self.sessions[session_token]
        
        # Verificar timeout
        if datetime.now() - session_data['created_at'] > timedelta(seconds=self.session_timeout):
            del self.sessions[session_token]
            return False, {}
        
        # Incrementar intentos
        session_data['attempts'] += 1
        
        # Verificar límite de intentos
        if session_data['attempts'] > 3:
            del self.sessions[session_token]
            return False, {}
        
        return True, session_data
    
    def complete_mfa_session(self, session_token: str) -> bool:
        """Completar sesión MFA exitosa"""
        if session_token in self.sessions:
            self.sessions[session_token]['verified'] = True
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """Limpiar sesiones expiradas"""
        current_time = datetime.now()
        expired_sessions = []
        
        for token, session_data in self.sessions.items():
            if current_time - session_data['created_at'] > timedelta(seconds=self.session_timeout):
                expired_sessions.append(token)
        
        for token in expired_sessions:
            del self.sessions[token]

class CompleteMFASystem:
    """Sistema completo de MFA"""
    
    def __init__(self):
        self.mfa_manager = MFAManager()
        self.email_mfa = EmailMFA()
        self.sms_provider = SMSProvider()
        self.session_manager = MFASession()
        self.temp_codes = {}  # Para códigos temporales (email/SMS)
    
    def setup_user_mfa(self, user_id: int, user_email: str, method: str = 'totp') -> Dict[str, Any]:
        """
        Configurar MFA para un usuario
        
        Args:
            user_id: ID del usuario
            user_email: Email del usuario
            method: Método MFA ('totp', 'email', 'sms')
            
        Returns:
            Datos de configuración MFA
        """
        try:
            if method == 'totp':
                secret_key = self.mfa_manager.generate_secret_key()
                qr_code = self.mfa_manager.generate_qr_code(user_email, secret_key)
                backup_codes = self.mfa_manager.generate_backup_codes()
                
                return {
                    'method': 'totp',
                    'secret_key': secret_key,
                    'qr_code': qr_code,
                    'backup_codes': backup_codes,
                    'setup_complete': False
                }
            
            elif method == 'email':
                return {
                    'method': 'email',
                    'email': user_email,
                    'setup_complete': True
                }
            
            elif method == 'sms':
                if not self.sms_provider.enabled:
                    raise MFAError("SMS MFA not available")
                
                return {
                    'method': 'sms',
                    'setup_complete': True
                }
            
            else:
                raise MFAError(f"Unsupported MFA method: {method}")
                
        except Exception as e:
            logger.error(f"Error setting up MFA: {e}")
            raise MFAError("Failed to setup MFA")
    
    def initiate_mfa_verification(self, user_id: int, user_data: Dict[str, Any]) -> str:
        """
        Iniciar proceso de verificación MFA
        
        Args:
            user_id: ID del usuario
            user_data: Datos del usuario con configuración MFA
            
        Returns:
            Token de sesión MFA
        """
        mfa_method = user_data.get('mfa_method')
        
        if not mfa_method:
            raise MFAError("MFA not configured for user")
        
        # Crear sesión MFA
        session_token = self.session_manager.create_mfa_session(user_id, mfa_method)
        
        try:
            if mfa_method == 'email':
                code = self.email_mfa.generate_email_code()
                self.temp_codes[session_token] = {
                    'code': code,
                    'created_at': datetime.now(),
                    'type': 'email'
                }
                
                if not self.email_mfa.send_verification_code(user_data['email'], code):
                    raise MFAError("Failed to send email verification code")
            
            elif mfa_method == 'sms':
                code = self.email_mfa.generate_email_code()  # Mismo formato
                self.temp_codes[session_token] = {
                    'code': code,
                    'created_at': datetime.now(),
                    'type': 'sms'
                }
                
                message = f"Su código de verificación Agente Digital es: {code}"
                if not self.sms_provider.send_sms(user_data.get('phone'), message):
                    raise MFAError("Failed to send SMS verification code")
            
            return session_token
            
        except Exception as e:
            logger.error(f"Error initiating MFA verification: {e}")
            raise MFAError("Failed to initiate MFA verification")
    
    def verify_mfa_token(self, session_token: str, token: str, user_data: Dict[str, Any]) -> bool:
        """
        Verificar token MFA
        
        Args:
            session_token: Token de sesión MFA
            token: Token proporcionado por el usuario
            user_data: Datos del usuario
            
        Returns:
            True si el token es válido
        """
        is_valid, session_data = self.session_manager.verify_mfa_session(session_token, token)
        if not is_valid:
            return False
        
        mfa_method = session_data['mfa_method']
        
        try:
            if mfa_method == 'totp':
                secret_key = user_data.get('mfa_secret_key')
                if not secret_key:
                    return False
                
                # Verificar TOTP
                if self.mfa_manager.verify_totp_token(secret_key, token):
                    self.session_manager.complete_mfa_session(session_token)
                    return True
                
                # Verificar código de respaldo
                backup_codes = user_data.get('mfa_backup_codes', [])
                is_backup_valid, remaining_codes = self.mfa_manager.verify_backup_code(backup_codes, token)
                if is_backup_valid:
                    # Actualizar códigos de respaldo en base de datos
                    user_data['mfa_backup_codes'] = remaining_codes
                    self.session_manager.complete_mfa_session(session_token)
                    return True
            
            elif mfa_method in ['email', 'sms']:
                if session_token in self.temp_codes:
                    temp_code_data = self.temp_codes[session_token]
                    
                    # Verificar timeout (10 minutos)
                    if datetime.now() - temp_code_data['created_at'] > timedelta(minutes=10):
                        del self.temp_codes[session_token]
                        return False
                    
                    if temp_code_data['code'] == token:
                        self.session_manager.complete_mfa_session(session_token)
                        del self.temp_codes[session_token]
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying MFA token: {e}")
            return False
    
    def disable_user_mfa(self, user_id: int) -> bool:
        """Deshabilitar MFA para un usuario"""
        try:
            # Limpiar datos MFA del usuario
            # Esto debería actualizar la base de datos
            logger.info(f"MFA disabled for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error disabling MFA: {e}")
            return False
    
    def regenerate_backup_codes(self, user_id: int) -> list:
        """Regenerar códigos de respaldo"""
        return self.mfa_manager.generate_backup_codes()

class MFAError(Exception):
    """Excepción personalizada para errores MFA"""
    pass

# Instancia global del sistema MFA
_mfa_system = None

def init_mfa_system():
    """Inicializar sistema MFA"""
    global _mfa_system
    try:
        _mfa_system = CompleteMFASystem()
        logger.info("MFA system initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize MFA system: {e}")
        return False

def get_mfa_system() -> CompleteMFASystem:
    """Obtener instancia del sistema MFA"""
    if _mfa_system is None:
        init_mfa_system()
    return _mfa_system
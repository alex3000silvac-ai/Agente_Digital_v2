# app/password_security.py
# Sistema avanzado de gestión de contraseñas y seguridad

import hashlib
import secrets
import string
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from flask import Blueprint, jsonify, request, session
from .database import get_db_connection
from functools import wraps
import logging

# Importaciones opcionales para evitar errores si no están instaladas
try:
    import pyotp
    import qrcode
    from io import BytesIO
    import base64
    MFA_AVAILABLE = True
except ImportError:
    MFA_AVAILABLE = False
    print("⚠️  MFA no disponible - instalar: pip install pyotp qrcode[pil] pillow")

# Configurar logging para seguridad
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

password_security_bp = Blueprint('password_security', __name__, url_prefix='/api/admin/security')

# Manejar CORS preflight requests
@password_security_bp.route('/users', methods=['OPTIONS'])
@password_security_bp.route('/users/<int:user_id>', methods=['OPTIONS'])
@password_security_bp.route('/users/<int:user_id>/reset-password', methods=['OPTIONS'])
@password_security_bp.route('/users/<int:user_id>/toggle-status', methods=['OPTIONS'])
@password_security_bp.route('/validate-password', methods=['OPTIONS'])
def handle_options(user_id=None):
    """Maneja las solicitudes OPTIONS para CORS"""
    return '', 204

# ============================================================================
# CONFIGURACIÓN DE SEGURIDAD
# ============================================================================

SECURITY_CONFIG = {
    'password': {
        'min_length': 12,
        'max_length': 128,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_numbers': True,
        'require_special': True,
        'forbidden_patterns': [
            r'123456', r'password', r'admin', r'qwerty', 
            r'abc123', r'letmein', r'welcome'
        ],
        'max_age_days': 90,
        'history_count': 12,  # No reusar últimas 12 contraseñas
    },
    'lockout': {
        'max_attempts': 3,
        'lockout_duration_minutes': 5,
        'extended_lockout_attempts': 5,
        'extended_lockout_duration_hours': 24,
    },
    'mfa': {
        'issuer_name': 'Agente Digital',
        'backup_codes_count': 8,
        'code_length': 6,
    },
    'session': {
        'max_idle_minutes': 30,
        'max_duration_hours': 8,
        'require_reauth_for_sensitive': True,
    }
}

ROLES_PERMISSIONS = {
    'Superusuario': {
        'can_create_users': True,
        'can_edit_users': True,
        'can_delete_users': True,
        'can_reset_passwords': True,
        'can_manage_roles': True,
        'can_view_security_logs': True,
        'can_configure_security': True,
        'modules': ['all']
    },
    'Administración': {
        'can_create_users': False,
        'can_edit_users': False,
        'can_delete_users': False,
        'can_reset_passwords': False,
        'can_manage_roles': False,
        'can_view_security_logs': False,
        'can_configure_security': False,
        'modules': ['inquilinos', 'empresas']
    },
    'Consultas': {
        'can_create_users': False,
        'can_edit_users': False,
        'can_delete_users': False,
        'can_reset_passwords': False,
        'can_manage_roles': False,
        'can_view_security_logs': False,
        'can_configure_security': False,
        'modules': ['incidentes:read', 'acompanamiento:read', 'inquilinos:read', 'empresas:read']
    }
}

# ============================================================================
# UTILIDADES DE SEGURIDAD
# ============================================================================

class PasswordValidator:
    """Validador avanzado de contraseñas con múltiples criterios de seguridad"""
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, List[str], int]:
        """
        Valida una contraseña y retorna (es_válida, errores, puntuación)
        """
        errors = []
        score = 0
        
        # Longitud
        if len(password) < SECURITY_CONFIG['password']['min_length']:
            errors.append(f"Debe tener al menos {SECURITY_CONFIG['password']['min_length']} caracteres")
        elif len(password) >= SECURITY_CONFIG['password']['min_length']:
            score += 20
            
        if len(password) > SECURITY_CONFIG['password']['max_length']:
            errors.append(f"No puede tener más de {SECURITY_CONFIG['password']['max_length']} caracteres")
            
        # Caracteres requeridos
        if SECURITY_CONFIG['password']['require_uppercase'] and not re.search(r'[A-Z]', password):
            errors.append("Debe contener al menos una letra mayúscula")
        elif re.search(r'[A-Z]', password):
            score += 15
            
        if SECURITY_CONFIG['password']['require_lowercase'] and not re.search(r'[a-z]', password):
            errors.append("Debe contener al menos una letra minúscula")
        elif re.search(r'[a-z]', password):
            score += 15
            
        if SECURITY_CONFIG['password']['require_numbers'] and not re.search(r'[0-9]', password):
            errors.append("Debe contener al menos un número")
        elif re.search(r'[0-9]', password):
            score += 20
            
        if SECURITY_CONFIG['password']['require_special'] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Debe contener al menos un carácter especial")
        elif re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 30
            
        # Patrones prohibidos
        for pattern in SECURITY_CONFIG['password']['forbidden_patterns']:
            if re.search(pattern, password.lower()):
                errors.append("Contiene un patrón de contraseña común no permitido")
                score -= 20
                break
                
        # Diversidad de caracteres
        unique_chars = len(set(password))
        if unique_chars >= len(password) * 0.7:
            score += 10
            
        # Penalizar repeticiones
        if re.search(r'(.)\1{2,}', password):
            score -= 10
            
        # Bonificación por longitud extra
        if len(password) >= 16:
            score += 10
            
        score = max(0, min(100, score))
        is_valid = len(errors) == 0 and score >= 60
        
        return is_valid, errors, score

class SecurityManager:
    """Gestor centralizado de operaciones de seguridad"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Genera hash seguro de contraseña con salt"""
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """Verifica contraseña contra hash almacenado"""
        try:
            salt, hash_hex = stored_hash.split(':')
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return secrets.compare_digest(password_hash.hex(), hash_hex)
        except ValueError:
            return False
    
    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        """Genera contraseña segura aleatoria"""
        alphabet = (
            string.ascii_lowercase + 
            string.ascii_uppercase + 
            string.digits + 
            "!@#$%^&*"
        )
        
        # Asegurar que tenga al menos uno de cada tipo
        password = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*")
        ]
        
        # Llenar el resto aleatoriamente
        for _ in range(length - 4):
            password.append(secrets.choice(alphabet))
            
        # Mezclar la contraseña
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)
    
    @staticmethod
    def generate_mfa_secret() -> str:
        """Genera secreto para MFA"""
        if not MFA_AVAILABLE:
            return secrets.token_urlsafe(32)
        return pyotp.random_base32()
    
    @staticmethod
    def generate_mfa_qr(secret: str, email: str) -> str:
        """Genera código QR para configuración MFA"""
        if not MFA_AVAILABLE:
            return ""
            
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            email,
            issuer_name=SECURITY_CONFIG['mfa']['issuer_name']
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    @staticmethod
    def verify_mfa_code(secret: str, code: str) -> bool:
        """Verifica código MFA"""
        if not MFA_AVAILABLE:
            return False
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)  # Permitir 30s de diferencia
    
    @staticmethod
    def generate_backup_codes(count: int = 8) -> List[str]:
        """Genera códigos de respaldo para MFA"""
        return [secrets.token_hex(4).upper() for _ in range(count)]

def log_security_event(event_type: str, user_id: Optional[int], details: Dict, ip_address: str = None):
    """Registra eventos de seguridad"""
    conn = get_db_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO SecurityLogs (EventType, UserID, Details, IPAddress, Timestamp)
            VALUES (?, ?, ?, ?, GETDATE())
        """, (event_type, user_id, json.dumps(details), ip_address))
        conn.commit()
        
        # También log a archivo
        security_logger.info(f"Security Event: {event_type} | User: {user_id} | IP: {ip_address} | Details: {details}")
        
    except Exception as e:
        security_logger.error(f"Error logging security event: {e}")
    finally:
        if conn:
            conn.close()

def requires_permission(permission: str):
    """Decorador para verificar permisos específicos"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Por ahora, permitir acceso sin verificación
            # TODO: Implementar verificación de JWT y permisos
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def check_rate_limit(user_id: int, action: str, max_attempts: int, window_minutes: int) -> bool:
    """Verifica límites de velocidad para acciones sensibles"""
    conn = get_db_connection()
    if not conn:
        return True
        
    try:
        cursor = conn.cursor()
        
        # Contar intentos en la ventana de tiempo
        cursor.execute("""
            SELECT COUNT(*) as attempts
            FROM SecurityLogs 
            WHERE UserID = ? 
            AND EventType = ?
            AND Timestamp >= DATEADD(MINUTE, -?, GETDATE())
        """, (user_id, action, window_minutes))
        
        result = cursor.fetchone()
        attempts = result.attempts if result else 0
        
        return attempts < max_attempts
        
    except Exception as e:
        security_logger.error(f"Error checking rate limit: {e}")
        return True
    finally:
        if conn:
            conn.close()

# ============================================================================
# ENDPOINTS DE GESTIÓN DE USUARIOS
# ============================================================================

@password_security_bp.route('/dashboard', methods=['GET'])
def get_security_dashboard():
    """Obtiene datos para el dashboard de seguridad"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
        
    try:
        cursor = conn.cursor()
        
        # Estadísticas generales
        cursor.execute("""
            SELECT 
                COUNT(*) as total_users,
                SUM(CASE WHEN EstadoActivo = 1 THEN 1 ELSE 0 END) as active_users,
                SUM(CASE WHEN Bloqueado = 1 THEN 1 ELSE 0 END) as locked_users,
                SUM(CASE WHEN PasswordExpiry < GETDATE() THEN 1 ELSE 0 END) as expired_passwords,
                SUM(CASE WHEN MFAEnabled = 1 THEN 1 ELSE 0 END) as mfa_enabled
            FROM Usuarios
        """)
        
        stats_result = cursor.fetchone()
        
        # Distribución por roles
        cursor.execute("""
            SELECT Rol, COUNT(*) as count 
            FROM Usuarios 
            WHERE EstadoActivo = 1 
            GROUP BY Rol
        """)
        
        roles_result = cursor.fetchall()
        
        # Alertas de seguridad
        alerts = []
        
        if stats_result.expired_passwords > 0:
            alerts.append({
                'id': 'expired_passwords',
                'type': 'critical',
                'icon': 'ph ph-warning-octagon',
                'message': f'{stats_result.expired_passwords} contraseña{"s" if stats_result.expired_passwords != 1 else ""} vencida{"s" if stats_result.expired_passwords != 1 else ""} requiere{"n" if stats_result.expired_passwords != 1 else ""} atención'
            })
            
        if stats_result.locked_users > 0:
            alerts.append({
                'id': 'locked_users',
                'type': 'warning',
                'icon': 'ph ph-shield-warning',
                'message': f'{stats_result.locked_users} usuario{"s" if stats_result.locked_users != 1 else ""} bloqueado{"s" if stats_result.locked_users != 1 else ""} por intentos fallidos'
            })
            
        # Calcular nivel de seguridad
        security_level = calculate_security_level(stats_result)
        
        # Mapear roles a formato frontend
        role_mapping = {
            'Superusuario': {'name': 'Superusuario', 'class': 'role-super', 'icon': 'ph ph-crown'},
            'Administración': {'name': 'Administración', 'class': 'role-admin', 'icon': 'ph ph-gear'},
            'Consultas': {'name': 'Consultas', 'class': 'role-viewer', 'icon': 'ph ph-eye'}
        }
        
        roles_data = []
        for role_result in roles_result:
            role_info = role_mapping.get(role_result.Rol, {
                'name': role_result.Rol,
                'class': 'role-default',
                'icon': 'ph ph-user'
            })
            role_info['count'] = role_result.count
            roles_data.append(role_info)
        
        return jsonify({
            "stats": {
                "totalUsers": stats_result.total_users,
                "activeUsers": stats_result.active_users,
                "lockedUsers": stats_result.locked_users,
                "expiredPasswords": stats_result.expired_passwords,
                "mfaEnabled": stats_result.mfa_enabled
            },
            "roles": roles_data,
            "alerts": alerts,
            "securityLevel": security_level
        })
        
    except Exception as e:
        security_logger.error(f"Error getting security dashboard: {e}")
        return jsonify({"error": "Error al obtener datos de seguridad"}), 500
    finally:
        if conn:
            conn.close()

def calculate_security_level(stats) -> int:
    """Calcula el nivel de seguridad basado en métricas"""
    score = 100
    
    if stats.total_users == 0:
        return 0
        
    # Penalizar contraseñas vencidas
    if stats.expired_passwords > 0:
        score -= (stats.expired_passwords / stats.total_users) * 30
        
    # Penalizar usuarios bloqueados
    if stats.locked_users > 0:
        score -= (stats.locked_users / stats.total_users) * 20
        
    # Bonificar MFA habilitado
    mfa_percentage = (stats.mfa_enabled / stats.total_users) * 100
    if mfa_percentage >= 80:
        score += 10
    elif mfa_percentage >= 50:
        score += 5
        
    return max(0, min(100, int(score)))

@password_security_bp.route('/users', methods=['GET'])
@requires_permission('view_users')
def get_users():
    """Obtiene lista de usuarios con información de seguridad"""
    conn = get_db_connection()
    if not conn:
        # Si no hay conexión, devolver array vacío
        return jsonify([])
        
    try:
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'Usuarios' 
            AND TABLE_SCHEMA = 'dbo'
        """)
        result = cursor.fetchone()
        
        if not result or result.count == 0:
            # Si la tabla no existe, devolver array vacío
            security_logger.warning("Tabla Usuarios no existe - ejecutar create_security_tables.sql")
            return jsonify([])
        
        cursor.execute("""
            SELECT 
                UsuarioID, NombreCompleto, Email, Rol, EstadoActivo,
                Bloqueado, UltimoAcceso, PasswordExpiry, MFAEnabled,
                RequiereCambioPassword, NotificacionesEmail, FechaCreacion,
                IntentosLogin, UltimoIntento
            FROM Usuarios
            ORDER BY FechaCreacion DESC
        """)
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row.UsuarioID,
                'name': row.NombreCompleto,
                'email': row.Email,
                'role': row.Rol,
                'active': bool(row.EstadoActivo),
                'locked': bool(row.Bloqueado),
                'lastAccess': row.UltimoAcceso.isoformat() if row.UltimoAcceso else None,
                'passwordExpiry': row.PasswordExpiry.isoformat() if row.PasswordExpiry else None,
                'passwordExpired': row.PasswordExpiry < datetime.now() if row.PasswordExpiry else False,
                'mfaEnabled': bool(row.MFAEnabled),
                'requirePasswordChange': bool(row.RequiereCambioPassword),
                'emailNotifications': bool(row.NotificacionesEmail),
                'createdDate': row.FechaCreacion.isoformat() if row.FechaCreacion else None,
                'loginAttempts': row.IntentosLogin or 0,
                'lastAttempt': row.UltimoIntento.isoformat() if row.UltimoIntento else None
            })
            
        return jsonify(users)
        
    except Exception as e:
        security_logger.error(f"Error getting users: {e}")
        # En caso de error, devolver array vacío para no bloquear la UI
        return jsonify([])
    finally:
        if conn:
            conn.close()

@password_security_bp.route('/users', methods=['POST'])
@requires_permission('create_users')
def create_user():
    """Crea un nuevo usuario con configuración de seguridad"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['name', 'email', 'role', 'password']):
        return jsonify({"error": "Datos incompletos"}), 400
        
    # Validar contraseña
    is_valid, errors, score = PasswordValidator.validate_password(data['password'])
    if not is_valid:
        return jsonify({"error": "Contraseña no válida", "details": errors}), 400
        
    # Verificar que el email no esté en uso
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
        
    try:
        cursor = conn.cursor()
        
        # Verificar email único
        cursor.execute("SELECT COUNT(*) as count FROM Usuarios WHERE Email = ?", (data['email'],))
        if cursor.fetchone().count > 0:
            return jsonify({"error": "El email ya está en uso"}), 400
            
        # Generar hash de contraseña
        password_hash = SecurityManager.hash_password(data['password'])
        
        # Configurar expiración de contraseña según tipo
        expiry_days = data.get('passwordExpiryDays', SECURITY_CONFIG['password']['max_age_days'])
        password_expiry = datetime.now() + timedelta(days=expiry_days)
        
        # Crear usuario
        cursor.execute("""
            INSERT INTO Usuarios (
                NombreCompleto, Email, PasswordHash, Rol, EstadoActivo,
                PasswordExpiry, RequiereCambioPassword, MFAEnabled, 
                NotificacionesEmail, FechaCreacion
            ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, GETDATE())
        """, (
            data['name'], data['email'], password_hash, data['role'],
            password_expiry, data.get('requirePasswordChange', True),
            data.get('mfaEnabled', False), data.get('emailNotifications', True)
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        # Log evento de seguridad
        log_security_event('USER_CREATED', user_id, {
            'created_by': 'system',  # Aquí irías el ID del usuario actual
            'role': data['role']
        }, request.remote_addr)
        
        return jsonify({
            "message": "Usuario creado exitosamente",
            "userId": user_id
        }), 201
        
    except Exception as e:
        conn.rollback()
        security_logger.error(f"Error creating user: {e}")
        return jsonify({"error": "Error al crear usuario"}), 500
    finally:
        if conn:
            conn.close()

@password_security_bp.route('/users/<int:user_id>', methods=['PUT'])
@requires_permission('edit_users')
def update_user(user_id):
    """Actualiza información de usuario"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
        
    try:
        cursor = conn.cursor()
        
        # Verificar que el usuario existe
        cursor.execute("SELECT UsuarioID FROM Usuarios WHERE UsuarioID = ?", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Usuario no encontrado"}), 404
            
        # Construir query de actualización
        update_fields = []
        params = []
        
        if 'name' in data:
            update_fields.append("NombreCompleto = ?")
            params.append(data['name'])
            
        if 'email' in data:
            # Verificar que el email no esté en uso por otro usuario
            cursor.execute("SELECT COUNT(*) as count FROM Usuarios WHERE Email = ? AND UsuarioID != ?", 
                         (data['email'], user_id))
            if cursor.fetchone().count > 0:
                return jsonify({"error": "El email ya está en uso"}), 400
            update_fields.append("Email = ?")
            params.append(data['email'])
            
        if 'role' in data:
            update_fields.append("Rol = ?")
            params.append(data['role'])
            
        if 'mfaEnabled' in data:
            update_fields.append("MFAEnabled = ?")
            params.append(data['mfaEnabled'])
            
        if 'emailNotifications' in data:
            update_fields.append("NotificacionesEmail = ?")
            params.append(data['emailNotifications'])
            
        if update_fields:
            params.append(user_id)
            query = f"UPDATE Usuarios SET {', '.join(update_fields)} WHERE UsuarioID = ?"
            cursor.execute(query, params)
            conn.commit()
            
        # Log evento
        log_security_event('USER_UPDATED', user_id, {
            'updated_by': 'system',  # Aquí iría el ID del usuario actual
            'fields': list(data.keys())
        }, request.remote_addr)
        
        return jsonify({"message": "Usuario actualizado exitosamente"})
        
    except Exception as e:
        conn.rollback()
        security_logger.error(f"Error updating user: {e}")
        return jsonify({"error": "Error al actualizar usuario"}), 500
    finally:
        if conn:
            conn.close()

@password_security_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@requires_permission('reset_passwords')
def reset_user_password(user_id):
    """Restablece la contraseña de un usuario"""
    
    # Verificar rate limiting
    if not check_rate_limit(user_id, 'PASSWORD_RESET', 3, 60):
        return jsonify({"error": "Demasiados intentos de restablecimiento"}), 429
        
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
        
    try:
        cursor = conn.cursor()
        
        # Verificar que el usuario existe
        cursor.execute("SELECT Email FROM Usuarios WHERE UsuarioID = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
            
        # Generar nueva contraseña temporal
        temp_password = SecurityManager.generate_secure_password(12)
        password_hash = SecurityManager.hash_password(temp_password)
        
        # Configurar nueva expiración
        password_expiry = datetime.now() + timedelta(days=SECURITY_CONFIG['password']['max_age_days'])
        
        # Actualizar contraseña
        cursor.execute("""
            UPDATE Usuarios 
            SET PasswordHash = ?, PasswordExpiry = ?, RequiereCambioPassword = 1, 
                Bloqueado = 0, IntentosLogin = 0
            WHERE UsuarioID = ?
        """, (password_hash, password_expiry, user_id))
        
        conn.commit()
        
        # Log evento
        log_security_event('PASSWORD_RESET', user_id, {
            'reset_by': 'system',  # Aquí iría el ID del usuario actual
            'method': 'admin_reset'
        }, request.remote_addr)
        
        return jsonify({
            "message": "Contraseña restablecida exitosamente",
            "temporaryPassword": temp_password,
            "expiryDate": password_expiry.isoformat()
        })
        
    except Exception as e:
        conn.rollback()
        security_logger.error(f"Error resetting password: {e}")
        return jsonify({"error": "Error al restablecer contraseña"}), 500
    finally:
        if conn:
            conn.close()

@password_security_bp.route('/users/<int:user_id>/toggle-status', methods=['PATCH'])
@requires_permission('manage_users')
def toggle_user_status(user_id):
    """Activa o desactiva un usuario"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
        
    try:
        cursor = conn.cursor()
        
        # Obtener estado actual
        cursor.execute("SELECT EstadoActivo FROM Usuarios WHERE UsuarioID = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
            
        new_status = not bool(user.EstadoActivo)
        
        # Actualizar estado
        cursor.execute("UPDATE Usuarios SET EstadoActivo = ? WHERE UsuarioID = ?", 
                      (new_status, user_id))
        conn.commit()
        
        # Log evento
        log_security_event('USER_STATUS_CHANGED', user_id, {
            'changed_by': 'system',  # Aquí iría el ID del usuario actual
            'new_status': 'active' if new_status else 'inactive'
        }, request.remote_addr)
        
        return jsonify({
            "message": f"Usuario {'activado' if new_status else 'desactivado'} exitosamente",
            "newStatus": new_status
        })
        
    except Exception as e:
        conn.rollback()
        security_logger.error(f"Error toggling user status: {e}")
        return jsonify({"error": "Error al cambiar estado del usuario"}), 500
    finally:
        if conn:
            conn.close()

@password_security_bp.route('/users/<int:user_id>', methods=['DELETE'])
@requires_permission('delete_users')
def delete_user(user_id):
    """Elimina un usuario del sistema"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
        
    try:
        cursor = conn.cursor()
        
        # Verificar que el usuario existe y obtener información
        cursor.execute("SELECT Email, Rol FROM Usuarios WHERE UsuarioID = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
            
        # Verificar que no sea el último superusuario
        if user.Rol == 'Superusuario':
            cursor.execute("SELECT COUNT(*) as count FROM Usuarios WHERE Rol = 'Superusuario' AND EstadoActivo = 1")
            if cursor.fetchone().count <= 1:
                return jsonify({"error": "No se puede eliminar el último superusuario"}), 400
                
        # Eliminar usuario
        cursor.execute("DELETE FROM Usuarios WHERE UsuarioID = ?", (user_id,))
        conn.commit()
        
        # Log evento
        log_security_event('USER_DELETED', user_id, {
            'deleted_by': 'system',  # Aquí iría el ID del usuario actual
            'deleted_email': user.Email,
            'deleted_role': user.Rol
        }, request.remote_addr)
        
        return jsonify({"message": "Usuario eliminado exitosamente"})
        
    except Exception as e:
        conn.rollback()
        security_logger.error(f"Error deleting user: {e}")
        return jsonify({"error": "Error al eliminar usuario"}), 500
    finally:
        if conn:
            conn.close()

# ============================================================================
# ENDPOINTS MFA
# ============================================================================

@password_security_bp.route('/users/<int:user_id>/mfa/setup', methods=['POST'])
def setup_mfa(user_id):
    """Inicia la configuración de MFA para un usuario"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
        
    try:
        cursor = conn.cursor()
        
        # Verificar usuario
        cursor.execute("SELECT Email FROM Usuarios WHERE UsuarioID = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
            
        # Generar secreto MFA
        secret = SecurityManager.generate_mfa_secret()
        qr_code = SecurityManager.generate_mfa_qr(secret, user.Email)
        backup_codes = SecurityManager.generate_backup_codes()
        
        # Almacenar temporalmente (no activar hasta confirmar)
        cursor.execute("""
            UPDATE Usuarios 
            SET MFASecret = ?, MFABackupCodes = ?
            WHERE UsuarioID = ?
        """, (secret, json.dumps(backup_codes), user_id))
        
        conn.commit()
        
        return jsonify({
            "secret": secret,
            "qrCode": qr_code,
            "backupCodes": backup_codes
        })
        
    except Exception as e:
        conn.rollback()
        security_logger.error(f"Error setting up MFA: {e}")
        return jsonify({"error": "Error al configurar MFA"}), 500
    finally:
        if conn:
            conn.close()

@password_security_bp.route('/users/<int:user_id>/mfa/verify', methods=['POST'])
def verify_mfa_setup(user_id):
    """Verifica y activa la configuración de MFA"""
    data = request.get_json()
    
    if not data or 'code' not in data:
        return jsonify({"error": "Código requerido"}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
        
    try:
        cursor = conn.cursor()
        
        # Obtener secreto MFA
        cursor.execute("SELECT MFASecret FROM Usuarios WHERE UsuarioID = ?", (user_id,))
        user = cursor.fetchone()
        if not user or not user.MFASecret:
            return jsonify({"error": "MFA no configurado"}), 400
            
        # Verificar código
        if not SecurityManager.verify_mfa_code(user.MFASecret, data['code']):
            return jsonify({"error": "Código inválido"}), 400
            
        # Activar MFA
        cursor.execute("UPDATE Usuarios SET MFAEnabled = 1 WHERE UsuarioID = ?", (user_id,))
        conn.commit()
        
        # Log evento
        log_security_event('MFA_ENABLED', user_id, {
            'setup_method': 'totp'
        }, request.remote_addr)
        
        return jsonify({"message": "MFA activado exitosamente"})
        
    except Exception as e:
        conn.rollback()
        security_logger.error(f"Error verifying MFA: {e}")
        return jsonify({"error": "Error al verificar MFA"}), 500
    finally:
        if conn:
            conn.close()

# ============================================================================
# UTILIDADES ADICIONALES
# ============================================================================

@password_security_bp.route('/validate-password', methods=['POST'])
def validate_password_endpoint():
    """Valida una contraseña y retorna información de fortaleza"""
    data = request.get_json()
    
    if not data or 'password' not in data:
        return jsonify({"error": "Contraseña requerida"}), 400
        
    is_valid, errors, score = PasswordValidator.validate_password(data['password'])
    
    return jsonify({
        "valid": is_valid,
        "score": score,
        "errors": errors,
        "strength": get_strength_label(score)
    })

def get_strength_label(score: int) -> str:
    """Convierte puntuación a etiqueta de fortaleza"""
    if score >= 80:
        return "Excelente"
    elif score >= 60:
        return "Buena"
    elif score >= 40:
        return "Regular"
    else:
        return "Débil"

@password_security_bp.route('/generate-password', methods=['GET'])
def generate_password_endpoint():
    """Genera una contraseña segura"""
    length = request.args.get('length', 12, type=int)
    
    if length < 8 or length > 128:
        return jsonify({"error": "Longitud debe estar entre 8 y 128 caracteres"}), 400
        
    password = SecurityManager.generate_secure_password(length)
    is_valid, errors, score = PasswordValidator.validate_password(password)
    
    return jsonify({
        "password": password,
        "score": score,
        "strength": get_strength_label(score)
    })
# app/password_manager.py
"""
🔐 MÓDULO DE GESTIÓN AVANZADA DE CONTRASEÑAS
Sistema completo para gestión, validación y políticas de contraseñas
"""

from flask import Blueprint, jsonify, request
from .database import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import hashlib
import re
import datetime
import json
from functools import wraps
from timezone_utils import get_chile_iso_timestamp

password_manager_bp = Blueprint('password_manager', __name__, url_prefix='/api/password-manager')

# ============================================================================
# POLÍTICAS DE CONTRASEÑAS CONFIGURABLES
# ============================================================================

DEFAULT_PASSWORD_POLICIES = {
    "min_length": 8,
    "max_length": 128,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_numbers": True,
    "require_special": True,
    "min_special_chars": 1,
    "forbidden_patterns": [
        "123456", "password", "admin", "user", "qwerty", 
        "abc123", "111111", "123123", "password123"
    ],
    "max_repeated_chars": 3,
    "min_unique_chars": 4,
    "password_history": 5,  # No reutilizar últimas 5 contraseñas
    "expiry_days": 90,      # Contraseña expira en 90 días
    "warning_days": 15,     # Advertir 15 días antes
    "max_login_attempts": 5,
    "lockout_duration": 30  # minutos
}

SPECIAL_CHARACTERS = "!@#$%^&*(),.?\":{}|<>[]+=_-~`"

# ============================================================================
# VALIDADORES DE CONTRASEÑAS
# ============================================================================

def validar_contraseña_completa(password, user_data=None, custom_policies=None):
    """
    Validación completa de contraseña con políticas personalizables
    
    Args:
        password (str): Contraseña a validar
        user_data (dict): Datos del usuario para validaciones contextuales
        custom_policies (dict): Políticas personalizadas
    
    Returns:
        dict: Resultado de validación con errores y puntuación
    """
    policies = DEFAULT_PASSWORD_POLICIES.copy()
    if custom_policies:
        policies.update(custom_policies)
    
    errores = []
    advertencias = []
    puntuacion = 0
    
    # 1. Validación de longitud
    if len(password) < policies["min_length"]:
        errores.append(f"Mínimo {policies['min_length']} caracteres")
    elif len(password) >= policies["min_length"]:
        puntuacion += 10
    
    if len(password) > policies["max_length"]:
        errores.append(f"Máximo {policies['max_length']} caracteres")
    
    # 2. Validación de tipos de caracteres
    if policies["require_uppercase"] and not re.search(r'[A-Z]', password):
        errores.append("Al menos una letra mayúscula")
    elif re.search(r'[A-Z]', password):
        puntuacion += 15
    
    if policies["require_lowercase"] and not re.search(r'[a-z]', password):
        errores.append("Al menos una letra minúscula")
    elif re.search(r'[a-z]', password):
        puntuacion += 15
    
    if policies["require_numbers"] and not re.search(r'\d', password):
        errores.append("Al menos un número")
    elif re.search(r'\d', password):
        puntuacion += 15
    
    if policies["require_special"]:
        special_count = sum(1 for char in password if char in SPECIAL_CHARACTERS)
        if special_count < policies["min_special_chars"]:
            errores.append(f"Al menos {policies['min_special_chars']} carácter(es) especial(es)")
        elif special_count >= policies["min_special_chars"]:
            puntuacion += 15
    
    # 3. Validación de patrones prohibidos
    password_lower = password.lower()
    for pattern in policies["forbidden_patterns"]:
        if pattern.lower() in password_lower:
            errores.append(f"No puede contener '{pattern}'")
    
    # 4. Validación de caracteres repetidos
    max_repeated = max((len(list(group)) for key, group in 
                       __import__('itertools').groupby(password)), default=0)
    if max_repeated > policies["max_repeated_chars"]:
        errores.append(f"Máximo {policies['max_repeated_chars']} caracteres repetidos consecutivos")
    
    # 5. Validación de caracteres únicos
    unique_chars = len(set(password))
    if unique_chars < policies["min_unique_chars"]:
        errores.append(f"Mínimo {policies['min_unique_chars']} caracteres únicos")
    elif unique_chars >= policies["min_unique_chars"]:
        puntuacion += 10
    
    # 6. Validaciones contextuales con datos del usuario
    if user_data:
        nombre = user_data.get('nombre', '').lower()
        email = user_data.get('email', '').lower()
        
        if nombre and len(nombre) > 2 and nombre in password_lower:
            errores.append("No puede contener tu nombre")
        
        if email and email.split('@')[0] in password_lower:
            errores.append("No puede contener tu email")
    
    # 7. Bonificaciones por complejidad
    if len(password) >= 12:
        puntuacion += 10
        
    if len(set(password) & set(SPECIAL_CHARACTERS)) >= 2:
        puntuacion += 10
        
    if re.search(r'[A-Z].*[a-z].*\d', password) or re.search(r'[a-z].*[A-Z].*\d', password):
        puntuacion += 10  # Bonus por mezcla de tipos
    
    # 8. Calcular nivel de seguridad
    puntuacion = min(puntuacion, 100)
    
    if puntuacion >= 90:
        nivel = "Excelente"
        color = "#10b981"
    elif puntuacion >= 70:
        nivel = "Buena"
        color = "#3b82f6"
    elif puntuacion >= 50:
        nivel = "Regular"
        color = "#f59e0b"
    else:
        nivel = "Débil"
        color = "#ef4444"
    
    return {
        "valida": len(errores) == 0,
        "errores": errores,
        "advertencias": advertencias,
        "puntuacion": puntuacion,
        "nivel": nivel,
        "color": color,
        "recomendaciones": generar_recomendaciones(password, errores)
    }

def generar_recomendaciones(password, errores):
    """Genera recomendaciones específicas para mejorar la contraseña"""
    recomendaciones = []
    
    if "Al menos una letra mayúscula" in str(errores):
        recomendaciones.append("Agrega al menos una letra mayúscula (A-Z)")
    
    if "Al menos una letra minúscula" in str(errores):
        recomendaciones.append("Agrega al menos una letra minúscula (a-z)")
    
    if "Al menos un número" in str(errores):
        recomendaciones.append("Incluye al menos un número (0-9)")
    
    if "carácter" in str(errores) and "especial" in str(errores):
        recomendaciones.append(f"Usa caracteres especiales como: {SPECIAL_CHARACTERS[:10]}...")
    
    if len(password) < 8:
        recomendaciones.append("Aumenta la longitud a al menos 8 caracteres")
    
    if len(recomendaciones) == 0:
        recomendaciones.append("¡Excelente! Tu contraseña cumple todos los requisitos")
    
    return recomendaciones

def hash_password_seguro(password, salt=None):
    """
    Genera hash seguro de contraseña con salt personalizado
    
    Args:
        password (str): Contraseña en texto plano
        salt (str): Salt opcional (se genera automáticamente si no se proporciona)
    
    Returns:
        str: Hash de contraseña en formato salt$hash
    """
    if not salt:
        salt = secrets.token_hex(32)
    
    # Usar PBKDF2 con SHA-256 y 100,000 iteraciones
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${hash_obj.hex()}"

def verificar_password_seguro(password, stored_hash):
    """
    Verifica contraseña contra hash almacenado
    
    Args:
        password (str): Contraseña a verificar
        stored_hash (str): Hash almacenado en formato salt$hash
    
    Returns:
        bool: True si la contraseña es correcta
    """
    try:
        if '$' not in stored_hash:
            # Backward compatibility con hashes de Werkzeug
            return check_password_hash(stored_hash, password)
        
        salt, stored_hash_hex = stored_hash.split('$', 1)
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hash_obj.hex() == stored_hash_hex
    except Exception:
        return False

def generar_contraseña_temporal(length=12):
    """
    Genera contraseña temporal segura
    
    Args:
        length (int): Longitud de la contraseña
    
    Returns:
        str: Contraseña temporal
    """
    # Asegurar que tenga todos los tipos de caracteres
    lowercase = "abcdefghijklmnopqrstuvwxyz"
    uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    numbers = "0123456789"
    special = "!@#$%^&*"
    
    # Garantizar al menos un carácter de cada tipo
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(numbers),
        secrets.choice(special)
    ]
    
    # Rellenar el resto
    all_chars = lowercase + uppercase + numbers + special
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))
    
    # Mezclar la lista
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)

# ============================================================================
# ENDPOINTS DE GESTIÓN DE CONTRASEÑAS
# ============================================================================

@password_manager_bp.route('/validate', methods=['POST'])
def validar_contraseña():
    """
    🔍 Validar fortaleza de contraseña
    """
    try:
        data = request.get_json()
        password = data.get('password', '')
        user_data = data.get('user_data', {})
        
        if not password:
            return jsonify({"error": "Contraseña requerida"}), 400
        
        resultado = validar_contraseña_completa(password, user_data)
        
        return jsonify({
            "success": True,
            "validation": resultado
        }), 200
        
    except Exception as e:
        print(f"ERROR validando contraseña: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@password_manager_bp.route('/generate', methods=['POST'])
def generar_contraseña():
    """
    🎲 Generar contraseña segura
    """
    try:
        data = request.get_json() or {}
        length = data.get('length', 12)
        
        if length < 8 or length > 50:
            return jsonify({"error": "Longitud debe estar entre 8 y 50 caracteres"}), 400
        
        password = generar_contraseña_temporal(length)
        validation = validar_contraseña_completa(password)
        
        return jsonify({
            "success": True,
            "password": password,
            "validation": validation
        }), 200
        
    except Exception as e:
        print(f"ERROR generando contraseña: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@password_manager_bp.route('/change', methods=['POST'])
def cambiar_contraseña():
    """
    🔄 Cambiar contraseña de usuario
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        admin_override = data.get('admin_override', False)
        
        if not all([user_id, new_password]):
            return jsonify({"error": "user_id y new_password requeridos"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión"}), 500
        
        cursor = conn.cursor()
        
        # Obtener usuario actual
        cursor.execute("""
            SELECT UsuarioID, PasswordHash, NombreCompleto, Email, 
                   UltimoCambioPassword, RequiereCambioPassword
            FROM Usuarios 
            WHERE UsuarioID = ?
        """, (user_id,))
        
        user_row = cursor.fetchone()
        if not user_row:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        user_id_db, password_hash, nombre, email, ultimo_cambio, requiere_cambio = user_row
        
        # Verificar contraseña actual (a menos que sea override de admin)
        if not admin_override:
            if not current_password:
                return jsonify({"error": "Contraseña actual requerida"}), 400
            
            if not verificar_password_seguro(current_password, password_hash):
                return jsonify({"error": "Contraseña actual incorrecta"}), 401
        
        # Validar nueva contraseña
        user_data = {"nombre": nombre, "email": email}
        validation = validar_contraseña_completa(new_password, user_data)
        
        if not validation["valida"]:
            return jsonify({
                "error": "La nueva contraseña no cumple los requisitos",
                "validation": validation
            }), 400
        
        # Verificar historial de contraseñas (TODO: implementar tabla de historial)
        
        # Generar nuevo hash
        new_hash = hash_password_seguro(new_password)
        
        # Actualizar contraseña
        cursor.execute("""
            UPDATE Usuarios 
            SET PasswordHash = ?,
                UltimoCambioPassword = GETDATE(),
                RequiereCambioPassword = 0,
                IntentosFallidos = 0,
                FechaBloqueado = NULL
            WHERE UsuarioID = ?
        """, (new_hash, user_id))
        
        conn.commit()
        
        # Registrar en auditoría
        cursor.execute("""
            INSERT INTO LogsAuditoria (
                UsuarioID, Accion, Tabla, RegistroID, 
                DatosNuevos, IPAddress, Detalles
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            "CHANGE_PASSWORD",
            "Usuarios", 
            user_id,
            json.dumps({"admin_override": admin_override}),
            request.remote_addr,
            "Contraseña cambiada exitosamente"
        ))
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Contraseña cambiada exitosamente",
            "validation": validation
        }), 200
        
    except Exception as e:
        print(f"ERROR cambiando contraseña: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@password_manager_bp.route('/reset', methods=['POST'])
def resetear_contraseña():
    """
    🔄 Reset de contraseña con contraseña temporal
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id requerido"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión"}), 500
        
        cursor = conn.cursor()
        
        # Obtener usuario
        cursor.execute("""
            SELECT UsuarioID, NombreCompleto, Email 
            FROM Usuarios 
            WHERE UsuarioID = ?
        """, (user_id,))
        
        user_row = cursor.fetchone()
        if not user_row:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        user_id_db, nombre, email = user_row
        
        # Generar contraseña temporal
        temp_password = generar_contraseña_temporal(10)
        temp_hash = hash_password_seguro(temp_password)
        
        # Actualizar contraseña y marcar para cambio obligatorio
        cursor.execute("""
            UPDATE Usuarios 
            SET PasswordHash = ?,
                RequiereCambioPassword = 1,
                UltimoCambioPassword = GETDATE(),
                IntentosFallidos = 0,
                FechaBloqueado = NULL
            WHERE UsuarioID = ?
        """, (temp_hash, user_id))
        
        conn.commit()
        
        # Registrar en auditoría
        cursor.execute("""
            INSERT INTO LogsAuditoria (
                UsuarioID, Accion, Tabla, RegistroID, 
                IPAddress, Detalles
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            "RESET_PASSWORD",
            "Usuarios",
            user_id,
            request.remote_addr,
            "Contraseña reseteada - contraseña temporal generada"
        ))
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Contraseña reseteada exitosamente",
            "temp_password": temp_password,
            "user": {
                "nombre": nombre,
                "email": email
            }
        }), 200
        
    except Exception as e:
        print(f"ERROR reseteando contraseña: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@password_manager_bp.route('/policies', methods=['GET'])
def obtener_politicas():
    """
    📋 Obtener políticas de contraseñas
    """
    try:
        return jsonify({
            "success": True,
            "policies": DEFAULT_PASSWORD_POLICIES
        }), 200
        
    except Exception as e:
        print(f"ERROR obteniendo políticas: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@password_manager_bp.route('/check-expiry', methods=['POST'])
def verificar_expiracion():
    """
    ⏰ Verificar expiración de contraseñas
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id requerido"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión"}), 500
        
        cursor = conn.cursor()
        
        # Obtener información de contraseña
        cursor.execute("""
            SELECT UsuarioID, UltimoCambioPassword, RequiereCambioPassword
            FROM Usuarios 
            WHERE UsuarioID = ?
        """, (user_id,))
        
        user_row = cursor.fetchone()
        if not user_row:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        user_id_db, ultimo_cambio, requiere_cambio = user_row
        
        # Calcular días desde último cambio
        if ultimo_cambio:
            dias_desde_cambio = (datetime.datetime.now() - ultimo_cambio).days
        else:
            dias_desde_cambio = 999  # Nunca cambió
        
        expiry_days = DEFAULT_PASSWORD_POLICIES["expiry_days"]
        warning_days = DEFAULT_PASSWORD_POLICIES["warning_days"]
        
        dias_restantes = expiry_days - dias_desde_cambio
        
        estado = "activa"
        if requiere_cambio:
            estado = "requiere_cambio"
        elif dias_restantes <= 0:
            estado = "expirada"
        elif dias_restantes <= warning_days:
            estado = "por_expirar"
        
        return jsonify({
            "success": True,
            "password_status": {
                "estado": estado,
                "dias_desde_cambio": dias_desde_cambio,
                "dias_restantes": max(0, dias_restantes),
                "requiere_cambio": bool(requiere_cambio),
                "ultimo_cambio": ultimo_cambio.isoformat() if ultimo_cambio else None
            }
        }), 200
        
    except Exception as e:
        print(f"ERROR verificando expiración: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if 'conn' in locals():
            conn.close()

# ============================================================================
# UTILIDADES ADICIONALES
# ============================================================================

def es_contraseña_comprometida(password):
    """
    Verificar si una contraseña está en listas de contraseñas comprometidas
    (Para implementación futura con APIs como HaveIBeenPwned)
    """
    # TODO: Implementar verificación contra bases de datos de contraseñas comprometidas
    common_passwords = [
        "123456", "password", "123456789", "12345678", "12345",
        "1234567", "1234567890", "qwerty", "abc123", "111111"
    ]
    return password.lower() in common_passwords

def generar_consejo_seguridad():
    """Genera un consejo aleatorio de seguridad de contraseñas"""
    consejos = [
        "💡 Usa una combinación única de letras, números y símbolos",
        "🔒 Nunca compartas tu contraseña con nadie",
        "🎯 Usa contraseñas diferentes para cada cuenta",
        "⏰ Cambia tu contraseña periódicamente",
        "📱 Considera usar un gestor de contraseñas",
        "🚫 Evita usar información personal en tus contraseñas",
        "🔐 Activa la autenticación de dos factores cuando esté disponible"
    ]
    return secrets.choice(consejos)

print("🔐 Módulo de gestión de contraseñas cargado exitosamente")
# auth_routes.py
# Endpoints de autenticación básicos

from flask import Blueprint, jsonify, request
import jwt
import datetime
import os

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Importar configuración
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import Config

# Usar la configuración centralizada
config = Config()
SECRET_KEY = config.JWT_SECRET_KEY

@auth_bp.route('/login', methods=['POST'])
def login():
    """Endpoint de login básico"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No se proporcionaron credenciales"}), 400
        
        # Aceptar tanto 'username' como 'email' para compatibilidad con el frontend
        username = data.get('username', data.get('email', '')).strip()
        password = data.get('password', '').strip()
        
        # Validación básica
        if not username or not password:
            return jsonify({"error": "Usuario y contraseña son requeridos"}), 400
        
        # Por ahora, aceptar cualquier credencial para pruebas
        # En producción, verificar contra base de datos
        print(f"[AUTH] Intento de login: {username}")
        
        # Generar token JWT
        payload = {
            'sub': '1',  # ID del usuario (por defecto para pruebas)
            'username': username,
            'email': username,
            'nombre': 'Usuario Administrador',
            'rol': 'Administrador',  # Por defecto para pruebas
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
            'iat': datetime.datetime.utcnow()
        }
        
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        
        # Respuesta exitosa
        return jsonify({
            'token': token,
            'rol': 'Administrador',
            'username': username,
            'message': 'Login exitoso'
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Error en login: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@auth_bp.route('/verify', methods=['GET'])
def verify_token():
    """Verificar si el token es válido"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return jsonify({"valid": False, "error": "No token provided"}), 401
    
    try:
        token = auth_header.split(' ')[1]  # Bearer TOKEN
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return jsonify({
            "valid": True,
            "username": payload.get('username'),
            "rol": payload.get('rol')
        }), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"valid": False, "error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"valid": False, "error": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Endpoint de logout (principalmente para el cliente)"""
    return jsonify({"message": "Logout exitoso"}), 200
# auth_utils.py - Utilidades de autenticación para la API

from functools import wraps
from flask import request, jsonify, current_app
import jwt
import bcrypt
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from agente_digital_api.config import Config

def verificar_token(token):
    """Verifica y decodifica un token JWT"""
    if not token:
        return None
    
    try:
        # Remover "Bearer " si está presente
        if token.startswith('Bearer '):
            token = token.split(' ')[1]
        
        config = Config()
        data = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'])
        
        return {
            'id': data.get('sub'),
            'rol': data.get('rol'),
            'email': data.get('email', ''),
            'nombre': data.get('nombre', '')
        }
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

def token_required(f):
    """Decorador para verificar JWT token en rutas protegidas"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Obtener token del header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # Formato esperado: "Bearer <token>"
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Token inválido - formato incorrecto'}), 401
        
        if not token:
            return jsonify({'message': 'Token requerido'}), 401
        
        try:
            # Decodificar token usando la clave JWT específica
            config = Config()
            data = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'])
            current_user_id = data['sub']
            current_user_rol = data['rol']
            current_user_email = data.get('email', '')
            current_user_nombre = data.get('nombre', '')
            
            # Pasar información del usuario a la función decorada
            return f(current_user_id, current_user_rol, current_user_email, current_user_nombre, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido'}), 401
        except Exception as e:
            return jsonify({'message': f'Error al verificar token: {str(e)}'}), 401
    
    return decorated

def admin_required(f):
    """Decorador que requiere rol de administrador"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Primero verificar el token
        @token_required
        def check_admin(user_id, user_rol, user_email, user_nombre, *inner_args, **inner_kwargs):
            if user_rol != 'admin':
                return jsonify({'message': 'Permisos de administrador requeridos'}), 403
            return f(user_id, user_rol, user_email, user_nombre, *inner_args, **inner_kwargs)
        
        return check_admin(*args, **kwargs)
    
    return decorated

def verify_token_info(token):
    """Función utilitaria para extraer información del token sin decorador"""
    try:
        config = Config()
        data = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'])
        return {
            'valid': True,
            'user_id': data['sub'],
            'rol': data['rol'],
            'email': data.get('email', ''),
            'nombre': data.get('nombre', ''),
            'exp': data['exp'],
            'iat': data['iat']
        }
    except jwt.ExpiredSignatureError:
        return {'valid': False, 'error': 'Token expirado'}
    except jwt.InvalidTokenError:
        return {'valid': False, 'error': 'Token inválido'}
    except Exception as e:
        return {'valid': False, 'error': str(e)}

def hash_password(password):
    """Genera hash de contraseña usando bcrypt"""
    try:
        # Generar hash con bcrypt
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        print(f"Error generando hash: {e}")
        return None

def verify_password(password, hashed):
    """Verifica contraseña contra hash bcrypt"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        print(f"Error verificando contraseña: {e}")
        return False
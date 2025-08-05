# app/accesos_clientes.py
# API para gestión de accesos de clientes

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
import pyodbc
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# Configurar logging
logger = logging.getLogger(__name__)

accesos_clientes_bp = Blueprint('accesos_clientes', __name__, url_prefix='/api/admin/accesos-clientes')

# ============================================================================
# DECORADORES Y UTILIDADES
# ============================================================================

def requires_admin_access(f):
    """Decorador para verificar acceso de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar si el usuario es administrador o superusuario
        if not session.get('user_id'):
            return jsonify({'error': 'No autorizado'}), 401
        
        user_role = session.get('user_role')
        if user_role not in ['Administrador', 'SuperUsuario']:
            return jsonify({'error': 'Acceso denegado'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def generate_password(length=12):
    """Genera una contraseña segura"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password

def hash_password(password: str) -> Tuple[str, str]:
    """Hash de contraseña con salt"""
    salt = secrets.token_hex(32)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return password_hash.hex(), salt

def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verifica contraseña"""
    test_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return test_hash.hex() == password_hash

def validate_password_strength(password: str) -> List[str]:
    """Valida fuerza de contraseña"""
    errors = []
    
    if len(password) < 8:
        errors.append("La contraseña debe tener al menos 8 caracteres")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Debe contener al menos una mayúscula")
    
    if not re.search(r'[a-z]', password):
        errors.append("Debe contener al menos una minúscula")
    
    if not re.search(r'\d', password):
        errors.append("Debe contener al menos un número")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Debe contener al menos un carácter especial")
    
    return errors

def send_authorization_email(email: str, codigo: str, tipo_solicitud: str):
    """Envía email con código de autorización"""
    # Implementar envío de email según configuración del sistema
    pass

# ============================================================================
# GESTIÓN DE INQUILINOS Y CONFIGURACIÓN
# ============================================================================

@accesos_clientes_bp.route('/inquilinos', methods=['GET'])
@requires_admin_access
def get_inquilinos():
    """Obtiene lista de inquilinos con su configuración"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
        SELECT 
            i.InquilinoID,
            i.NombreInquilino,
            i.RUT,
            i.Email,
            i.Estado as EstadoInquilino,
            ic.TipoAcceso,
            ic.PermiteCrearUsuarios,
            ic.FechaCreacion as FechaConfiguracion,
            COUNT(uc.UsuarioClienteID) as TotalUsuarios
        FROM Inquilinos i
        LEFT JOIN InquilinosConfig ic ON i.InquilinoID = ic.InquilinoID
        LEFT JOIN UsuariosCliente uc ON i.InquilinoID = uc.InquilinoID
        WHERE i.Estado = 'Activo'
        GROUP BY i.InquilinoID, i.NombreInquilino, i.RUT, i.Email, i.Estado, 
                 ic.TipoAcceso, ic.PermiteCrearUsuarios, ic.FechaCreacion
        ORDER BY i.NombreInquilino
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        inquilinos = []
        for row in rows:
            inquilinos.append({
                'InquilinoID': row[0],
                'NombreInquilino': row[1],
                'RUT': row[2],
                'Email': row[3],
                'EstadoInquilino': row[4],
                'TipoAcceso': row[5] if row[5] else 1,
                'PermiteCrearUsuarios': bool(row[6]) if row[6] else True,
                'FechaConfiguracion': row[7].isoformat() if row[7] else None,
                'TotalUsuarios': row[8]
            })
        
        connection.close()
        return jsonify(inquilinos)
        
    except Exception as e:
        logger.error(f"Error al obtener inquilinos: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@accesos_clientes_bp.route('/inquilinos/<int:inquilino_id>/config', methods=['POST'])
@requires_admin_access
def configurar_inquilino(inquilino_id):
    """Configura tipo de acceso para inquilino"""
    try:
        data = request.get_json()
        tipo_acceso = data.get('tipo_acceso')
        permite_crear_usuarios = data.get('permite_crear_usuarios', True)
        
        if tipo_acceso not in [1, 2]:
            return jsonify({'error': 'Tipo de acceso inválido'}), 400
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Verificar si ya existe configuración
        cursor.execute("SELECT InquilinoID FROM InquilinosConfig WHERE InquilinoID = ?", (inquilino_id,))
        if cursor.fetchone():
            # Actualizar configuración existente
            cursor.execute("""
                UPDATE InquilinosConfig 
                SET TipoAcceso = ?, PermiteCrearUsuarios = ?, FechaModificacion = GETDATE()
                WHERE InquilinoID = ?
            """, (tipo_acceso, permite_crear_usuarios, inquilino_id))
        else:
            # Crear nueva configuración
            cursor.execute("""
                INSERT INTO InquilinosConfig (InquilinoID, TipoAcceso, PermiteCrearUsuarios, UsuarioCreador)
                VALUES (?, ?, ?, ?)
            """, (inquilino_id, tipo_acceso, permite_crear_usuarios, session.get('user_id')))
        
        connection.commit()
        connection.close()
        
        return jsonify({'success': True, 'message': 'Configuración actualizada correctamente'})
        
    except Exception as e:
        logger.error(f"Error al configurar inquilino: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

# ============================================================================
# GESTIÓN DE USUARIOS CLIENTE
# ============================================================================

@accesos_clientes_bp.route('/usuarios', methods=['GET'])
@requires_admin_access
def get_usuarios_cliente():
    """Obtiene lista de usuarios cliente"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
        SELECT 
            uc.UsuarioClienteID,
            uc.NombreUsuario,
            uc.Email,
            uc.NombreCompleto,
            uc.Telefono,
            uc.Cargo,
            uc.TipoUsuario,
            uc.UltimoAcceso,
            uc.Estado,
            uc.FechaCreacion,
            i.NombreInquilino,
            i.InquilinoID,
            e.NombreEmpresa,
            e.EmpresaID,
            rc.NombreRol
        FROM UsuariosCliente uc
        INNER JOIN Inquilinos i ON uc.InquilinoID = i.InquilinoID
        LEFT JOIN Empresas e ON uc.EmpresaID = e.EmpresaID
        INNER JOIN RolesCliente rc ON uc.RolID = rc.RolID
        ORDER BY uc.FechaCreacion DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        usuarios = []
        for row in rows:
            usuarios.append({
                'UsuarioClienteID': row[0],
                'NombreUsuario': row[1],
                'Email': row[2],
                'NombreCompleto': row[3],
                'Telefono': row[4],
                'Cargo': row[5],
                'TipoUsuario': row[6],
                'UltimoAcceso': row[7].isoformat() if row[7] else None,
                'Estado': row[8],
                'FechaCreacion': row[9].isoformat() if row[9] else None,
                'NombreInquilino': row[10],
                'InquilinoID': row[11],
                'NombreEmpresa': row[12],
                'EmpresaID': row[13],
                'NombreRol': row[14]
            })
        
        connection.close()
        return jsonify(usuarios)
        
    except Exception as e:
        logger.error(f"Error al obtener usuarios cliente: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@accesos_clientes_bp.route('/usuarios', methods=['POST'])
@requires_admin_access
def crear_usuario_cliente():
    """Crea nuevo usuario cliente"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['nombre_usuario', 'email', 'nombre_completo', 'inquilino_id', 'rol_id', 'tipo_usuario']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        
        # Validar email
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data['email']):
            return jsonify({'error': 'Email inválido'}), 400
        
        # Generar contraseña temporal
        password_temporal = generate_password(12)
        password_hash, salt = hash_password(password_temporal)
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Verificar que no exista el usuario
        cursor.execute("SELECT UsuarioClienteID FROM UsuariosCliente WHERE NombreUsuario = ? OR Email = ?", 
                      (data['nombre_usuario'], data['email']))
        if cursor.fetchone():
            return jsonify({'error': 'El usuario o email ya existe'}), 400
        
        # Crear usuario
        cursor.execute("""
            INSERT INTO UsuariosCliente (
                InquilinoID, EmpresaID, NombreUsuario, Email, PasswordHash, Salt,
                NombreCompleto, Telefono, Cargo, RolID, TipoUsuario,
                CambiarPasswordProximoLogin, FechaVencimientoPassword, UsuarioCreador
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['inquilino_id'],
            data.get('empresa_id'),
            data['nombre_usuario'],
            data['email'],
            password_hash,
            salt,
            data['nombre_completo'],
            data.get('telefono'),
            data.get('cargo'),
            data['rol_id'],
            data['tipo_usuario'],
            1,  # Cambiar contraseña en próximo login
            datetime.now() + timedelta(days=30),  # Vencimiento en 30 días
            session.get('user_id')
        ))
        
        connection.commit()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Usuario creado correctamente',
            'password_temporal': password_temporal,
            'usuario_id': cursor.lastrowid
        })
        
    except Exception as e:
        logger.error(f"Error al crear usuario cliente: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@accesos_clientes_bp.route('/usuarios/<int:usuario_id>', methods=['PUT'])
@requires_admin_access
def actualizar_usuario_cliente(usuario_id):
    """Actualiza usuario cliente"""
    try:
        data = request.get_json()
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Construir query de actualización dinámicamente
        campos_actualizables = ['email', 'nombre_completo', 'telefono', 'cargo', 'rol_id', 'estado']
        campos_sql = []
        valores = []
        
        for campo in campos_actualizables:
            if campo in data:
                if campo == 'email':
                    campos_sql.append("Email = ?")
                elif campo == 'nombre_completo':
                    campos_sql.append("NombreCompleto = ?")
                elif campo == 'telefono':
                    campos_sql.append("Telefono = ?")
                elif campo == 'cargo':
                    campos_sql.append("Cargo = ?")
                elif campo == 'rol_id':
                    campos_sql.append("RolID = ?")
                elif campo == 'estado':
                    campos_sql.append("Estado = ?")
                
                valores.append(data[campo])
        
        if not campos_sql:
            return jsonify({'error': 'No hay campos para actualizar'}), 400
        
        campos_sql.append("FechaModificacion = GETDATE()")
        valores.append(usuario_id)
        
        query = f"UPDATE UsuariosCliente SET {', '.join(campos_sql)} WHERE UsuarioClienteID = ?"
        cursor.execute(query, valores)
        
        connection.commit()
        connection.close()
        
        return jsonify({'success': True, 'message': 'Usuario actualizado correctamente'})
        
    except Exception as e:
        logger.error(f"Error al actualizar usuario cliente: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

# ============================================================================
# GESTIÓN DE ROLES
# ============================================================================

@accesos_clientes_bp.route('/roles', methods=['GET'])
@requires_admin_access
def get_roles_cliente():
    """Obtiene lista de roles disponibles"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT RolID, NombreRol, Descripcion, AccesoAcompanamiento, AccesoIncidentes,
                   AccesoInformesANCI, AccesoReportes, AccesoTodosModulos, PuedeCrearUsuarios
            FROM RolesCliente
            WHERE Estado = 'Activo'
            ORDER BY NombreRol
        """)
        
        rows = cursor.fetchall()
        roles = []
        
        for row in rows:
            roles.append({
                'RolID': row[0],
                'NombreRol': row[1],
                'Descripcion': row[2],
                'AccesoAcompanamiento': bool(row[3]),
                'AccesoIncidentes': bool(row[4]),
                'AccesoInformesANCI': bool(row[5]),
                'AccesoReportes': bool(row[6]),
                'AccesoTodosModulos': bool(row[7]),
                'PuedeCrearUsuarios': bool(row[8])
            })
        
        connection.close()
        return jsonify(roles)
        
    except Exception as e:
        logger.error(f"Error al obtener roles: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

# ============================================================================
# SISTEMA DE AUTORIZACIÓN
# ============================================================================

@accesos_clientes_bp.route('/usuarios/<int:usuario_id>/solicitar-reset', methods=['POST'])
@requires_admin_access
def solicitar_reset_password(usuario_id):
    """Solicita autorización para resetear contraseña"""
    try:
        data = request.get_json()
        motivo = data.get('motivo', 'Reseteo de contraseña solicitado por administrador')
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Obtener datos del usuario cliente
        cursor.execute("""
            SELECT uc.InquilinoID, i.Email, i.NombreInquilino, uc.NombreCompleto
            FROM UsuariosCliente uc
            INNER JOIN Inquilinos i ON uc.InquilinoID = i.InquilinoID
            WHERE uc.UsuarioClienteID = ?
        """, (usuario_id,))
        
        usuario_data = cursor.fetchone()
        if not usuario_data:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Generar código de autorización
        codigo_autorizacion = ''.join(secrets.choice(string.digits) for _ in range(6))
        fecha_expiracion = datetime.now() + timedelta(hours=24)
        
        # Crear solicitud de autorización
        cursor.execute("""
            INSERT INTO SolicitudesAutorizacion (
                UsuarioClienteID, TipoSolicitud, UsuarioSolicitante, Motivo,
                CodigoAutorizacion, FechaExpiracionCodigo
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (usuario_id, 'ResetPassword', session.get('user_id'), motivo, codigo_autorizacion, fecha_expiracion))
        
        solicitud_id = cursor.lastrowid
        
        # Enviar email con código de autorización
        try:
            send_authorization_email(usuario_data[1], codigo_autorizacion, 'reseteo de contraseña')
        except Exception as e:
            logger.warning(f"Error al enviar email de autorización: {str(e)}")
        
        connection.commit()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Solicitud de autorización enviada',
            'solicitud_id': solicitud_id,
            'codigo_demo': codigo_autorizacion  # Solo para demo, remover en producción
        })
        
    except Exception as e:
        logger.error(f"Error al solicitar reset: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@accesos_clientes_bp.route('/autorizar/<int:solicitud_id>', methods=['POST'])
@requires_admin_access
def autorizar_solicitud(solicitud_id):
    """Autoriza una solicitud con código"""
    try:
        data = request.get_json()
        codigo_ingresado = data.get('codigo')
        
        if not codigo_ingresado:
            return jsonify({'error': 'Código de autorización requerido'}), 400
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Verificar solicitud y código
        cursor.execute("""
            SELECT SolicitudID, UsuarioClienteID, CodigoAutorizacion, FechaExpiracionCodigo, TipoSolicitud
            FROM SolicitudesAutorizacion
            WHERE SolicitudID = ? AND Estado = 'Pendiente'
        """, (solicitud_id,))
        
        solicitud = cursor.fetchone()
        if not solicitud:
            return jsonify({'error': 'Solicitud no encontrada o ya procesada'}), 404
        
        # Verificar código y expiración
        if solicitud[2] != codigo_ingresado:
            return jsonify({'error': 'Código de autorización incorrecto'}), 400
        
        if datetime.now() > solicitud[3]:
            cursor.execute("UPDATE SolicitudesAutorizacion SET Estado = 'Expirada' WHERE SolicitudID = ?", (solicitud_id,))
            connection.commit()
            return jsonify({'error': 'Código de autorización expirado'}), 400
        
        # Aprobar solicitud
        cursor.execute("""
            UPDATE SolicitudesAutorizacion 
            SET Estado = 'Aprobada', FechaRespuesta = GETDATE()
            WHERE SolicitudID = ?
        """, (solicitud_id,))
        
        # Ejecutar acción según tipo de solicitud
        if solicitud[4] == 'ResetPassword':
            # Generar nueva contraseña
            nueva_password = generate_password(12)
            password_hash, salt = hash_password(nueva_password)
            
            cursor.execute("""
                UPDATE UsuariosCliente 
                SET PasswordHash = ?, Salt = ?, CambiarPasswordProximoLogin = 1, FechaVencimientoPassword = ?
                WHERE UsuarioClienteID = ?
            """, (password_hash, salt, datetime.now() + timedelta(days=30), solicitud[1]))
        
        connection.commit()
        connection.close()
        
        response = {
            'success': True,
            'message': 'Solicitud autorizada correctamente'
        }
        
        if solicitud[4] == 'ResetPassword':
            response['nueva_password'] = nueva_password
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error al autorizar solicitud: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

# ============================================================================
# ENDPOINTS ADICIONALES
# ============================================================================

@accesos_clientes_bp.route('/inquilinos/<int:inquilino_id>/empresas', methods=['GET'])
@requires_admin_access
def get_empresas_inquilino(inquilino_id):
    """Obtiene empresas de un inquilino"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT EmpresaID, NombreEmpresa, RUT, Estado
            FROM Empresas
            WHERE InquilinoID = ? AND Estado = 'Activo'
            ORDER BY NombreEmpresa
        """, (inquilino_id,))
        
        rows = cursor.fetchall()
        empresas = []
        
        for row in rows:
            empresas.append({
                'EmpresaID': row[0],
                'NombreEmpresa': row[1],
                'RUT': row[2],
                'Estado': row[3]
            })
        
        connection.close()
        return jsonify(empresas)
        
    except Exception as e:
        logger.error(f"Error al obtener empresas: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@accesos_clientes_bp.route('/estadisticas', methods=['GET'])
@requires_admin_access
def get_estadisticas():
    """Obtiene estadísticas del módulo"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Total de usuarios cliente
        cursor.execute("SELECT COUNT(*) FROM UsuariosCliente WHERE Estado = 'Activo'")
        total_usuarios = cursor.fetchone()[0]
        
        # Usuarios por rol
        cursor.execute("""
            SELECT rc.NombreRol, COUNT(uc.UsuarioClienteID) as Total
            FROM RolesCliente rc
            LEFT JOIN UsuariosCliente uc ON rc.RolID = uc.RolID AND uc.Estado = 'Activo'
            GROUP BY rc.NombreRol
            ORDER BY Total DESC
        """)
        usuarios_por_rol = [{'rol': row[0], 'total': row[1]} for row in cursor.fetchall()]
        
        # Inquilinos configurados
        cursor.execute("SELECT COUNT(*) FROM InquilinosConfig")
        inquilinos_configurados = cursor.fetchone()[0]
        
        # Solicitudes pendientes
        cursor.execute("SELECT COUNT(*) FROM SolicitudesAutorizacion WHERE Estado = 'Pendiente'")
        solicitudes_pendientes = cursor.fetchone()[0]
        
        connection.close()
        
        return jsonify({
            'total_usuarios': total_usuarios,
            'usuarios_por_rol': usuarios_por_rol,
            'inquilinos_configurados': inquilinos_configurados,
            'solicitudes_pendientes': solicitudes_pendientes
        })
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

# Manejar CORS
@accesos_clientes_bp.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response
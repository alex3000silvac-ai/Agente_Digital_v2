# modules/admin/inquilinos.py
# Gestión de inquilinos completamente modular

from flask import Blueprint, jsonify, request
from datetime import datetime
from ..core.database import get_db_connection, db_validator
from ..core.errors import robust_endpoint, ErrorResponse

inquilinos_bp = Blueprint('admin_inquilinos', __name__, url_prefix='/api/admin/inquilinos')

def format_date_safe(fecha, formato='%Y-%m-%d %H:%M:%S'):
    """Formatea fechas de forma segura"""
    if not fecha:
        return None
    return fecha.strftime(formato) if hasattr(fecha, 'strftime') else str(fecha)

@inquilinos_bp.route('', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_inquilinos():
    """Obtiene la lista de todos los inquilinos"""
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error()
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        # Usar tabla Inquilinos de SQL Server únicamente
        if not db_validator.table_exists(cursor, 'Inquilinos'):
            return jsonify({
                'error': 'Tabla Inquilinos no encontrada',
                'message': 'La tabla Inquilinos no existe en la base de datos SQL Server'
            }), 503
        
        try:
            # Consulta directa a tabla Inquilinos en SQL Server
            cursor.execute("SELECT InquilinoID, RazonSocial, RUT, FechaCreacion, EstadoActivo FROM Inquilinos ORDER BY RazonSocial")
            rows = cursor.fetchall()
            
            inquilinos = []
            for row in rows:
                inquilino = {
                    'InquilinoID': row[0],
                    'RazonSocial': row[1],
                    'RUT': row[2] if len(row) > 2 else None,
                    'FechaCreacion': format_date_safe(row[3]) if len(row) > 3 else None,
                    'EstadoActivo': 'Activo' if (len(row) > 4 and row[4]) else 'Inactivo'
                }
                inquilinos.append(inquilino)
            
            return jsonify(inquilinos)
            
        except Exception as e:
            print(f"Error consultando tabla Inquilinos: {e}")
            return jsonify({
                'error': 'Error de base de datos',
                'message': f'Error consultando inquilinos: {str(e)}'
            }), 500
    
    finally:
        if conn:
            conn.close()

@inquilinos_bp.route('/<int:inquilino_id>', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_inquilino_detalle(inquilino_id):
    """Obtiene detalles de un inquilino específico"""
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error()
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        # Intentar buscar en tabla Empresas (como inquilinos)
        if db_validator.table_exists(cursor, 'Empresas'):
            cursor.execute("SELECT * FROM Empresas WHERE EmpresaID = ?", (inquilino_id,))
            empresa_row = cursor.fetchone()
            
            if empresa_row:
                columns = [column[0] for column in cursor.description]
                empresa_data = dict(zip(columns, empresa_row))
                
                # Mapear a formato de inquilino
                inquilino = {
                    'id': empresa_data.get('EmpresaID'),
                    'nombre': empresa_data.get('RazonSocial'),
                    'tipo': empresa_data.get('TipoEmpresa', 'Empresa'),
                    'fecha_creacion': format_date_safe(empresa_data.get('FechaCreacion')),
                    'estado': 'Activo',
                    'detalles_completos': empresa_data
                }
                
                return jsonify(inquilino)
        
        response, status = ErrorResponse.not_found_error("Inquilino")
        return jsonify(response), status
    
    finally:
        if conn:
            conn.close()

@inquilinos_bp.route('', methods=['POST'])
@robust_endpoint(require_authentication=False, validate_payload=['nombre'], log_perf=True)
def create_inquilino():
    """Crea un nuevo inquilino"""
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error()
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        data = request.get_json()
        
        # Crear en tabla Empresas (como inquilino)
        if db_validator.table_exists(cursor, 'Empresas'):
            cursor.execute("""
                INSERT INTO Empresas (RazonSocial, TipoEmpresa, FechaCreacion)
                VALUES (?, 'Inquilino', GETDATE())
            """, (data['nombre'],))
            
            conn.commit()
            
            # Obtener ID del inquilino creado
            cursor.execute("SELECT @@IDENTITY")
            inquilino_id = cursor.fetchone()[0]
            
            return jsonify({
                'success': True,
                'inquilino_id': inquilino_id,
                'message': 'Inquilino creado exitosamente'
            }), 201
        else:
            response, status = ErrorResponse.generic_error("Sistema de inquilinos no disponible")
            return jsonify(response), status
        
    except Exception as e:
        if conn:
            conn.rollback()
        response, status = ErrorResponse.generic_error(f"Error creando inquilino: {str(e)}")
        return jsonify(response), status
    
    finally:
        if conn:
            conn.close()

@inquilinos_bp.route('/<inquilino_id>/empresas', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_empresas_inquilino(inquilino_id):
    """Obtiene las empresas asociadas a un inquilino específico"""
    
    # Validar que inquilino_id sea válido para producción
    if inquilino_id == 'undefined' or inquilino_id == 'null':
        return jsonify({
            'error': 'ID de inquilino no válido',
            'message': 'El parámetro inquilino_id es requerido'
        }), 400
    
    try:
        inquilino_id = int(inquilino_id)
    except ValueError:
        return jsonify({
            'error': 'ID de inquilino debe ser un número',
            'message': f'El valor "{inquilino_id}" no es un ID válido',
            'inquilino_id_recibido': inquilino_id
        }), 400
    
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error()
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        # Verificar que la tabla Inquilinos existe en SQL Server
        if not db_validator.table_exists(cursor, 'Inquilinos'):
            return jsonify({
                'error': 'Sistema no disponible',
                'message': 'La tabla Inquilinos no existe en SQL Server'
            }), 503
        
        # Verificar que el inquilino existe
        cursor.execute("SELECT InquilinoID FROM Inquilinos WHERE InquilinoID = ?", (inquilino_id,))
        if not cursor.fetchone():
            response, status = ErrorResponse.not_found_error("Inquilino")
            return jsonify(response), status
        
        # Verificar que existe tabla Empresas en SQL Server
        if not db_validator.table_exists(cursor, 'Empresas'):
            return jsonify({
                'error': 'Sistema no disponible',
                'message': 'La tabla Empresas no existe en SQL Server'
            }), 503
        
        # Buscar empresas asociadas al inquilino en SQL Server
        try:
            cursor.execute("""
                SELECT EmpresaID, RazonSocial, TipoEmpresa, FechaCreacion
                FROM Empresas 
                WHERE InquilinoID = ?
                ORDER BY RazonSocial
            """, (inquilino_id,))
            
            rows = cursor.fetchall()
            empresas = []
            for row in rows:
                empresa = {
                    'EmpresaID': row[0],
                    'RazonSocial': row[1],
                    'TipoEmpresa': row[2] if len(row) > 2 else 'PSE',
                    'FechaCreacion': format_date_safe(row[3]) if len(row) > 3 else None
                }
                empresas.append(empresa)
                
        except Exception as e:
            print(f"Error consultando empresas en SQL Server: {e}")
            return jsonify({
                'error': 'Error de base de datos',
                'message': f'Error consultando empresas: {str(e)}'
            }), 500
        
        return jsonify(empresas)
        
    finally:
        if conn:
            conn.close()

@inquilinos_bp.route('/<int:inquilino_id>/empresas', methods=['POST'])
@robust_endpoint(require_authentication=False, validate_payload=['razon_social'], log_perf=True)
def create_empresa_inquilino(inquilino_id):
    """Crea una nueva empresa para un inquilino específico"""
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error()
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        data = request.get_json()
        
        # Verificar que el inquilino existe
        cursor.execute("SELECT InquilinoID FROM Inquilinos WHERE InquilinoID = ?", (inquilino_id,))
        if not cursor.fetchone():
            response, status = ErrorResponse.not_found_error("Inquilino")
            return jsonify(response), status
        
        # Crear empresa asociada al inquilino
        cursor.execute("""
            INSERT INTO Empresas (RazonSocial, TipoEmpresa, InquilinoID, FechaCreacion)
            VALUES (?, ?, ?, GETDATE())
        """, (data['razon_social'], data.get('tipo_empresa', 'PSE'), inquilino_id))
        
        conn.commit()
        
        # Obtener ID de la empresa creada
        cursor.execute("SELECT @@IDENTITY")
        empresa_id = cursor.fetchone()[0]
        
        return jsonify({
            'success': True,
            'empresa_id': empresa_id,
            'message': 'Empresa creada exitosamente para el inquilino'
        }), 201
        
    except Exception as e:
        if conn:
            conn.rollback()
        response, status = ErrorResponse.generic_error(f"Error creando empresa: {str(e)}")
        return jsonify(response), status
    
    finally:
        if conn:
            conn.close()


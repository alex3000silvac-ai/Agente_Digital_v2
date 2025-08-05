# app/inquilinos_production.py
# Sistema de gestión de inquilinos para producción con SQL Server
# Código ejecutable y profesional sin simulaciones

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
import pyodbc
from .database import get_db_connection

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear Blueprint
inquilinos_bp = Blueprint('inquilinos_production', __name__, url_prefix='/api/admin')

def format_date_for_json(date_obj):
    """Convierte datetime a string para JSON de forma segura"""
    if date_obj is None:
        return None
    if isinstance(date_obj, datetime):
        return date_obj.strftime('%Y-%m-%d %H:%M:%S')
    return str(date_obj)

@inquilinos_bp.route('/inquilinos', methods=['GET'])
def get_inquilinos():
    """
    Obtiene lista de inquilinos desde SQL Server tabla Inquilinos
    Estructura real: InquilinoID, RazonSocial, RUT, EstadoActivo, FechaCreacion
    """
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("No se pudo establecer conexión con SQL Server")
            return jsonify({
                'error': 'Error de conexión',
                'message': 'No se pudo conectar a la base de datos'
            }), 500

        cursor = conn.cursor()
        
        # Consulta SQL real a tabla Inquilinos
        query = """
            SELECT InquilinoID, RazonSocial, RUT, EstadoActivo, FechaCreacion
            FROM Inquilinos 
            WHERE EstadoActivo = 1
            ORDER BY RazonSocial ASC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        inquilinos = []
        for row in rows:
            inquilino = {
                'id': row[0],                                    # InquilinoID
                'razon_social': row[1],                         # RazonSocial
                'rut': row[2] if row[2] is not None else '',   # RUT
                'estado_activo': bool(row[3]),                  # EstadoActivo
                'fecha_creacion': format_date_for_json(row[4])  # FechaCreacion
            }
            inquilinos.append(inquilino)
        
        logger.info(f"Consulta exitosa: {len(inquilinos)} inquilinos encontrados")
        
        return jsonify({
            'success': True,
            'data': inquilinos,
            'total': len(inquilinos)
        }), 200

    except pyodbc.Error as e:
        logger.error(f"Error de SQL Server: {str(e)}")
        return jsonify({
            'error': 'Error de base de datos',
            'message': f'Error en consulta SQL: {str(e)}'
        }), 500
    
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return jsonify({
            'error': 'Error interno',
            'message': 'Error inesperado en el servidor'
        }), 500
    
    finally:
        if conn:
            conn.close()

@inquilinos_bp.route('/inquilinos/<int:inquilino_id>', methods=['GET'])
def get_inquilino_detalle(inquilino_id):
    """
    Obtiene detalles de un inquilino específico desde SQL Server
    """
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("No se pudo establecer conexión con SQL Server")
            return jsonify({
                'error': 'Error de conexión',
                'message': 'No se pudo conectar a la base de datos'
            }), 500

        cursor = conn.cursor()
        
        # Consulta SQL real con parámetro
        query = """
            SELECT InquilinoID, RazonSocial, RUT, EstadoActivo, FechaCreacion
            FROM Inquilinos 
            WHERE InquilinoID = ?
        """
        
        cursor.execute(query, (inquilino_id,))
        row = cursor.fetchone()
        
        if not row:
            logger.warning(f"Inquilino con ID {inquilino_id} no encontrado")
            return jsonify({
                'error': 'No encontrado',
                'message': f'Inquilino con ID {inquilino_id} no existe'
            }), 404
        
        inquilino = {
            'id': row[0],
            'razon_social': row[1],
            'rut': row[2] if row[2] is not None else '',
            'estado_activo': bool(row[3]),
            'fecha_creacion': format_date_for_json(row[4])
        }
        
        logger.info(f"Inquilino {inquilino_id} encontrado: {row[1]}")
        
        return jsonify({
            'success': True,
            'data': inquilino
        }), 200

    except pyodbc.Error as e:
        logger.error(f"Error de SQL Server: {str(e)}")
        return jsonify({
            'error': 'Error de base de datos',
            'message': f'Error en consulta SQL: {str(e)}'
        }), 500
    
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return jsonify({
            'error': 'Error interno',
            'message': 'Error inesperado en el servidor'
        }), 500
    
    finally:
        if conn:
            conn.close()

@inquilinos_bp.route('/inquilinos/<int:inquilino_id>/empresas', methods=['GET'])
def get_empresas_por_inquilino(inquilino_id):
    """
    Obtiene empresas asociadas a un inquilino desde SQL Server tabla Empresas
    Relación: Empresas.InquilinoID -> Inquilinos.InquilinoID
    """
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("No se pudo establecer conexión con SQL Server")
            return jsonify({
                'error': 'Error de conexión',
                'message': 'No se pudo conectar a la base de datos'
            }), 500

        cursor = conn.cursor()
        
        # Primero verificar que el inquilino existe
        cursor.execute("SELECT InquilinoID FROM Inquilinos WHERE InquilinoID = ?", (inquilino_id,))
        if not cursor.fetchone():
            return jsonify({
                'error': 'No encontrado',
                'message': f'Inquilino con ID {inquilino_id} no existe'
            }), 404
        
        # Consulta SQL real a tabla Empresas con JOIN
        query = """
            SELECT 
                e.EmpresaID,
                e.RazonSocial,
                e.RUT,
                e.TipoEmpresa,
                e.NombreFantasia,
                e.GiroDelNegocio,
                e.Ciudad,
                e.RepresentanteLegal,
                e.EmailContacto,
                e.Telefono,
                e.NumeroEmpleados,
                e.FechaCreacion,
                e.EstadoActivo
            FROM Empresas e
            WHERE e.InquilinoID = ? AND e.EstadoActivo = 1
            ORDER BY e.RazonSocial ASC
        """
        
        cursor.execute(query, (inquilino_id,))
        rows = cursor.fetchall()
        
        empresas = []
        for row in rows:
            empresa = {
                'id': row[0],                                      # EmpresaID
                'razon_social': row[1],                           # RazonSocial
                'rut': row[2] if row[2] is not None else '',     # RUT
                'tipo_empresa': row[3] if row[3] is not None else '', # TipoEmpresa
                'nombre_fantasia': row[4] if row[4] is not None else '', # NombreFantasia
                'giro_negocio': row[5] if row[5] is not None else '', # GiroDelNegocio
                'ciudad': row[6] if row[6] is not None else '',   # Ciudad
                'representante_legal': row[7] if row[7] is not None else '', # RepresentanteLegal
                'email_contacto': row[8] if row[8] is not None else '', # EmailContacto
                'telefono': row[9] if row[9] is not None else '', # Telefono
                'numero_empleados': row[10] if row[10] is not None else 0, # NumeroEmpleados
                'fecha_creacion': format_date_for_json(row[11]),  # FechaCreacion
                'estado_activo': bool(row[12])                    # EstadoActivo
            }
            empresas.append(empresa)
        
        logger.info(f"Consulta exitosa: {len(empresas)} empresas encontradas para inquilino {inquilino_id}")
        
        return jsonify({
            'success': True,
            'inquilino_id': inquilino_id,
            'data': empresas,
            'total': len(empresas)
        }), 200

    except pyodbc.Error as e:
        logger.error(f"Error de SQL Server: {str(e)}")
        return jsonify({
            'error': 'Error de base de datos',
            'message': f'Error en consulta SQL: {str(e)}'
        }), 500
    
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return jsonify({
            'error': 'Error interno',
            'message': 'Error inesperado en el servidor'
        }), 500
    
    finally:
        if conn:
            conn.close()

@inquilinos_bp.route('/inquilinos', methods=['POST'])
def crear_inquilino():
    """
    Crea un nuevo inquilino en SQL Server tabla Inquilinos
    Campos requeridos: RazonSocial
    Campos opcionales: RUT
    """
    conn = None
    try:
        # Validar datos de entrada
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Datos inválidos',
                'message': 'Se requiere JSON válido'
            }), 400
        
        razon_social = data.get('razon_social', '').strip()
        if not razon_social:
            return jsonify({
                'error': 'Datos incompletos',
                'message': 'El campo razon_social es requerido'
            }), 400
        
        rut = data.get('rut', '').strip() if data.get('rut') else None
        
        conn = get_db_connection()
        if not conn:
            logger.error("No se pudo establecer conexión con SQL Server")
            return jsonify({
                'error': 'Error de conexión',
                'message': 'No se pudo conectar a la base de datos'
            }), 500

        cursor = conn.cursor()
        
        # Inserción SQL real
        query = """
            INSERT INTO Inquilinos (RazonSocial, RUT, EstadoActivo, FechaCreacion)
            VALUES (?, ?, 1, GETDATE())
        """
        
        cursor.execute(query, (razon_social, rut))
        
        # Obtener ID del inquilino creado
        cursor.execute("SELECT @@IDENTITY")
        nuevo_id = cursor.fetchone()[0]
        
        conn.commit()
        
        logger.info(f"Inquilino creado exitosamente: ID {nuevo_id}, Razón Social: {razon_social}")
        
        return jsonify({
            'success': True,
            'message': 'Inquilino creado exitosamente',
            'data': {
                'id': int(nuevo_id),
                'razon_social': razon_social,
                'rut': rut
            }
        }), 201

    except pyodbc.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Error de SQL Server: {str(e)}")
        return jsonify({
            'error': 'Error de base de datos',
            'message': f'Error en inserción SQL: {str(e)}'
        }), 500
    
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error inesperado: {str(e)}")
        return jsonify({
            'error': 'Error interno',
            'message': 'Error inesperado en el servidor'
        }), 500
    
    finally:
        if conn:
            conn.close()

# Endpoint de salud para verificar conectividad SQL Server
@inquilinos_bp.route('/inquilinos/health', methods=['GET'])
def health_check():
    """
    Verifica conectividad con SQL Server y acceso a tablas
    """
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'status': 'unhealthy',
                'message': 'Sin conexión a SQL Server'
            }), 503

        cursor = conn.cursor()
        
        # Verificar acceso a tablas reales
        cursor.execute("SELECT COUNT(*) FROM Inquilinos")
        count_inquilinos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Empresas")
        count_empresas = cursor.fetchone()[0]
        
        return jsonify({
            'status': 'healthy',
            'database': 'SQL Server',
            'server': '192.168.100.125',
            'database_name': 'AgenteDigitalDB',
            'inquilinos_count': count_inquilinos,
            'empresas_count': count_empresas,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503
    
    finally:
        if conn:
            conn.close()
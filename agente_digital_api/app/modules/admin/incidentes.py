# modules/admin/incidentes.py
# Gestión de incidentes completamente modular

from flask import Blueprint, jsonify, request
from ..core.database import get_db_connection, db_validator
from ..core.errors import robust_endpoint, ErrorResponse

incidentes_bp = Blueprint('admin_incidentes', __name__, url_prefix='/api/admin/empresas')

@incidentes_bp.route('/<int:empresa_id>/incidentes', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_incidentes_empresa(empresa_id):
    """Obtiene incidentes de una empresa específica"""
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error()
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        # Verificar que las tablas existan
        if not db_validator.table_exists(cursor, 'Incidentes'):
            return jsonify([])
        
        if not db_validator.table_exists(cursor, 'Empresas'):
            return jsonify([])
        
        # Verificar que la empresa existe
        cursor.execute("SELECT EmpresaID FROM Empresas WHERE EmpresaID = ?", (empresa_id,))
        if not cursor.fetchone():
            response, status = ErrorResponse.not_found_error("Empresa")
            return jsonify(response), status
        
        # Obtener incidentes usando validación segura
        try:
            query, columns = db_validator.build_safe_select_query(
                cursor, 'Incidentes', 
                desired_columns=['IncidenteID', 'Titulo', 'EstadoActual', 'Criticidad', 'FechaCreacion'],
                where_clause=f"EmpresaID = {empresa_id}"
            )
            
            cursor.execute(query)
            rows = cursor.fetchall()
            incidentes = [dict(zip(columns, row)) for row in rows]
            
            return jsonify(incidentes)
            
        except Exception as e:
            print(f"Error en consulta de incidentes: {e}")
            return jsonify([])
    
    finally:
        if conn:
            conn.close()

@incidentes_bp.route('/<int:empresa_id>/incidentes', methods=['POST'])
@robust_endpoint(require_authentication=False, validate_payload=['titulo'], log_perf=True)
def create_incidente(empresa_id):
    """Crea un nuevo incidente para una empresa"""
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error()
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        data = request.get_json()
        
        # Verificar que la empresa existe
        cursor.execute("SELECT EmpresaID FROM Empresas WHERE EmpresaID = ?", (empresa_id,))
        if not cursor.fetchone():
            response, status = ErrorResponse.not_found_error("Empresa")
            return jsonify(response), status
        
        # Crear incidente básico
        cursor.execute("""
            INSERT INTO Incidentes (EmpresaID, Titulo, EstadoActual, FechaCreacion)
            VALUES (?, ?, 'Abierto', GETDATE())
        """, (empresa_id, data['titulo']))
        
        conn.commit()
        
        # Obtener ID del incidente creado
        cursor.execute("SELECT @@IDENTITY")
        incidente_id = cursor.fetchone()[0]
        
        return jsonify({
            'success': True,
            'incidente_id': incidente_id,
            'message': 'Incidente creado exitosamente'
        }), 201
        
    except Exception as e:
        if conn:
            conn.rollback()
        response, status = ErrorResponse.generic_error(f"Error creando incidente: {str(e)}")
        return jsonify(response), status
    
    finally:
        if conn:
            conn.close()

@incidentes_bp.route('/incidentes/<int:incidente_id>', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_incidente_detalle(incidente_id):
    """Obtiene detalles de un incidente específico"""
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error()
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        if not db_validator.table_exists(cursor, 'Incidentes'):
            response, status = ErrorResponse.not_found_error("Sistema de incidentes")
            return jsonify(response), status
        
        cursor.execute("SELECT * FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        incidente_row = cursor.fetchone()
        
        if not incidente_row:
            response, status = ErrorResponse.not_found_error("Incidente")
            return jsonify(response), status
        
        columns = [column[0] for column in cursor.description]
        incidente_data = dict(zip(columns, incidente_row))
        
        # Agregar tipo de empresa desde la tabla EMPRESAS
        if incidente_data.get('EmpresaID'):
            cursor.execute("""
                SELECT TipoEmpresa, RazonSocial 
                FROM EMPRESAS 
                WHERE EmpresaID = ?
            """, (incidente_data['EmpresaID'],))
            empresa_row = cursor.fetchone()
            if empresa_row:
                incidente_data['TipoEmpresa'] = empresa_row[0]
                incidente_data['RazonSocial'] = empresa_row[1]
                print(f"Tipo de empresa para incidente {incidente_id}: {empresa_row[0]}")
        
        return jsonify(incidente_data)
    
    finally:
        if conn:
            conn.close()

@incidentes_bp.route('/incidentes/<int:incidente_id>', methods=['DELETE'])
@robust_endpoint(require_authentication=False, log_perf=True)
def delete_incidente(incidente_id):
    """Elimina completamente un incidente sin dejar rastro"""
    try:
        # Importar el módulo de eliminación completa
        from .incidentes_eliminar_completo import eliminar_incidente_completo
        
        # Llamar a la función de eliminación completa
        return eliminar_incidente_completo(incidente_id)
        
    except ImportError:
        # Si el módulo no está disponible, usar eliminación básica
        conn = get_db_connection()
        if not conn:
            response, status = ErrorResponse.database_error()
            return jsonify(response), status
        
        try:
            cursor = conn.cursor()
            
            # Verificar que el incidente existe
            cursor.execute("SELECT IncidenteID FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
            if not cursor.fetchone():
                response, status = ErrorResponse.not_found_error("Incidente")
                return jsonify(response), status
            
            # Eliminación básica
            cursor.execute("DELETE FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
            conn.commit()
            
            return jsonify({
                "success": True,
                "message": "Incidente eliminado exitosamente"
            }), 200
            
        except Exception as e:
            if conn:
                conn.rollback()
            response, status = ErrorResponse.generic_error(f"Error eliminando incidente: {str(e)}")
            return jsonify(response), status
        
        finally:
            if conn:
                conn.close()
    
    except Exception as e:
        response, status = ErrorResponse.generic_error(f"Error en eliminación: {str(e)}")
        return jsonify(response), status
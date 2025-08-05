# views/incidentes_views.py
# Módulo especializado para endpoints de incidentes

from flask import Blueprint, jsonify, request
from ..db_validator import db_validator
from ..error_handlers import robust_endpoint, ErrorResponse
from ..database import get_db_connection

incidentes_bp = Blueprint('incidentes_api', __name__, url_prefix='/api/admin/empresas')

@incidentes_bp.route('/<int:empresa_id>/incidentes', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_incidentes_empresa(empresa_id):
    """Obtiene los incidentes de una empresa específica"""
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error("No se pudo conectar a la base de datos")
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        # Verificar que la tabla Incidentes existe
        if not db_validator.table_exists(cursor, 'Incidentes'):
            return jsonify([])  # Retornar lista vacía si la tabla no existe
        
        # Verificar que la empresa existe
        if not db_validator.table_exists(cursor, 'Empresas'):
            return jsonify([])
        
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
            # Si hay error en la consulta, retornar array vacío en lugar de fallar
            print(f"Error en consulta de incidentes: {e}")
            return jsonify([])
    
    finally:
        if conn:
            conn.close()
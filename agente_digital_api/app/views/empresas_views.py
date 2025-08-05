# views/empresas_views.py
# Módulo especializado para endpoints de empresas

from flask import Blueprint, jsonify, request
from ..db_validator import db_validator
from ..error_handlers import robust_endpoint, ErrorResponse
from ..database import get_db_connection
from datetime import datetime

empresas_bp = Blueprint('empresas_api', __name__, url_prefix='/api/admin/empresas')

def format_date_safe(fecha, formato='%Y-%m-%d %H:%M:%S'):
    """Formatea una fecha de forma segura"""
    if not fecha:
        return None
    
    if hasattr(fecha, 'strftime'):
        return fecha.strftime(formato)
    else:
        return str(fecha)

@empresas_bp.route('/<int:empresa_id>', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_empresa_details(empresa_id):
    """Obtiene los detalles de una empresa específica"""
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error("No se pudo conectar a la base de datos")
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        # Verificar que la tabla Empresas existe
        if not db_validator.table_exists(cursor, 'Empresas'):
            response, status = ErrorResponse.not_found_error("Sistema de empresas")
            return jsonify(response), status
        
        # Obtener empresa usando validación segura
        cursor.execute("SELECT * FROM Empresas WHERE EmpresaID = ?", (empresa_id,))
        empresa_row = cursor.fetchone()
        
        if not empresa_row:
            response, status = ErrorResponse.not_found_error("Empresa")
            return jsonify(response), status
        
        # Convertir a diccionario manejando tipos de datos
        empresa_data = {}
        columns = [column[0] for column in cursor.description]
        
        for i, column_name in enumerate(columns):
            value = empresa_row[i]
            # Convertir fechas a string
            if hasattr(value, 'strftime'):
                empresa_data[column_name] = value.strftime('%Y-%m-%d %H:%M:%S')
            # Convertir bytes a string
            elif isinstance(value, bytes):
                try:
                    empresa_data[column_name] = value.decode('utf-8')
                except:
                    empresa_data[column_name] = None
            # Manejar valores booleanos
            elif isinstance(value, bool):
                empresa_data[column_name] = value
            # Manejar valores None
            elif value is None:
                empresa_data[column_name] = None
            else:
                empresa_data[column_name] = value
        
        return jsonify(empresa_data)
    
    finally:
        if conn:
            conn.close()

@empresas_bp.route('/<int:empresa_id>/dashboard-stats', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_dashboard_stats(empresa_id):
    """Obtiene estadísticas del dashboard para una empresa específica"""
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error("No se pudo conectar a la base de datos")
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        # Estadísticas básicas
        stats = {
            'empresa_id': empresa_id,
            'total_incidentes': 0,
            'incidentes_abiertos': 0,
            'cumplimiento_general': 0,
            'timestamp': format_date_safe(datetime.now())
        }
        
        # Solo obtener datos si las tablas existen
        if db_validator.table_exists(cursor, 'Incidentes'):
            try:
                cursor.execute("SELECT COUNT(*) FROM Incidentes WHERE EmpresaID = ?", (empresa_id,))
                stats['total_incidentes'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM Incidentes WHERE EmpresaID = ? AND EstadoActual = 'Abierto'", (empresa_id,))
                stats['incidentes_abiertos'] = cursor.fetchone()[0]
            except:
                pass  # Mantener valores por defecto
        
        return jsonify(stats)
        
    finally:
        if conn:
            conn.close()
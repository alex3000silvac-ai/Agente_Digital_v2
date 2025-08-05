# modules/core/health.py
# Sistema de health checks centralizado

from flask import Blueprint, jsonify
from datetime import datetime
from .database import get_db_connection, db_validator
from .errors import safe_endpoint, robust_endpoint, ErrorResponse, DatabaseHealthChecker

health_bp = Blueprint('health', __name__, url_prefix='/api')

@health_bp.route('/health', methods=['GET'])
@safe_endpoint()
def health_check():
    """Health check básico del sistema"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'environment': 'production',
        'database': 'SQL Server'
    })

@health_bp.route('/health/detailed', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def health_check_detailed():
    """Health check detallado del sistema"""
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error()
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        # Verificar conexión de BD
        health_status = DatabaseHealthChecker.check_connection(cursor)
        
        # Verificar tablas críticas
        critical_tables = ['Empresas', 'Incidentes', 'CumplimientoEmpresa']
        tables_status = DatabaseHealthChecker.check_critical_tables(cursor, critical_tables)
        
        # Información del sistema
        system_info = {
            "cache_stats": {
                "tables_cached": len(db_validator._table_cache),
                "columns_cached": len(db_validator._column_cache)
            },
            "database_type": "SQL Server",
            "environment": "production",
            "modules_loaded": ["core", "admin", "empresas", "incidentes", "cumplimiento", "inquilinos"]
        }
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "database": health_status,
                "tables": tables_status
            },
            "system_info": system_info
        })
    
    finally:
        if conn:
            conn.close()

@health_bp.route('/ping', methods=['GET'])
def ping():
    """Ping básico para verificación rápida"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})
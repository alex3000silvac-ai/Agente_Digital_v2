# views/health_views.py
# Módulo especializado para health checks y monitoreo

from flask import Blueprint, jsonify
from ..db_validator import db_validator
from ..error_handlers import robust_endpoint, safe_endpoint, ErrorResponse, DatabaseHealthChecker
from ..database import get_db_connection
from datetime import datetime

health_bp = Blueprint('health_api', __name__, url_prefix='/api/admin')

@health_bp.route('/health', methods=['GET'])
@safe_endpoint()
def health_check():
    """Health check básico del sistema"""
    conn = get_db_connection()
    if not conn:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "database": "disconnected"
        }), 503
    
    try:
        cursor = conn.cursor()
        health_status = DatabaseHealthChecker.check_connection(cursor)
        
        # Verificar tablas críticas
        critical_tables = ['Empresas', 'Incidentes', 'CumplimientoEmpresa']
        tables_status = DatabaseHealthChecker.check_critical_tables(cursor, critical_tables)
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "database": health_status,
                "tables": tables_status
            }
        })
    
    finally:
        if conn:
            conn.close()

@health_bp.route('/health/detailed', methods=['GET'])
@robust_endpoint(require_authentication=True, log_perf=True)
def health_check_detailed():
    """Health check detallado del sistema"""
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error()
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        # Información de tablas disponibles
        cursor.execute("""
            SELECT TABLE_NAME, 
                   (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = t.TABLE_NAME) as COLUMN_COUNT
            FROM INFORMATION_SCHEMA.TABLES t
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        
        tables_info = []
        for row in cursor.fetchall():
            tables_info.append({
                "name": row[0],
                "columns": row[1],
                "cached": db_validator._table_cache.get(row[0], False)
            })
        
        # Estadísticas de incidentes por empresa
        incident_stats = []
        if db_validator.table_exists(cursor, 'Empresas') and db_validator.table_exists(cursor, 'Incidentes'):
            try:
                cursor.execute("""
                    SELECT e.RazonSocial, COUNT(i.IncidenteID) as TotalIncidentes
                    FROM Empresas e
                    LEFT JOIN Incidentes i ON e.EmpresaID = i.EmpresaID
                    GROUP BY e.EmpresaID, e.RazonSocial
                    ORDER BY TotalIncidentes DESC
                """)
                
                for row in cursor.fetchall():
                    incident_stats.append({
                        "empresa": row[0],
                        "incidentes": row[1]
                    })
            except:
                pass  # Si hay error, mantener lista vacía
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database_info": {
                "tables": tables_info,
                "cache_stats": {
                    "tables_cached": len(db_validator._table_cache),
                    "columns_cached": len(db_validator._column_cache)
                },
                "incident_statistics": incident_stats
            }
        })
    
    finally:
        if conn:
            conn.close()
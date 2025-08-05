# app/admin_views_clean.py
# Versión limpia con funciones corregidas y sistema de validación

from flask import Blueprint, jsonify, request, send_from_directory, Response, session
from .db_validator import db_validator, safe_db_operation, validate_table_access, safe_select_all, get_standard_fields
from .error_handlers import robust_endpoint, safe_endpoint, ErrorResponse, DatabaseHealthChecker
from .database import get_db_connection, TEST_MODE
from werkzeug.utils import secure_filename
import os
import time
import datetime
from datetime import datetime
import json
from collections import defaultdict
from io import BytesIO
from functools import wraps
from timezone_utils import get_chile_iso_timestamp, get_chile_timestamp, get_chile_time, calculate_deadline_chile, get_chile_time_str

# Funciones temporales mientras se instala flask_jwt_extended
def jwt_required(optional=False):
    def decorator(f):
        return f
    return decorator

def get_jwt_identity():
    return None

def requires_organization(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

def get_user_organization():
    return {'inquilino_id': 1}

def format_date_safe(fecha, formato='%Y-%m-%d %H:%M:%S'):
    """
    Formatea una fecha de forma segura para ambos motores de BD
    """
    if not fecha:
        return None
    
    if hasattr(fecha, 'strftime'):
        return fecha.strftime(formato)
    else:
        return str(fecha)

admin_api_bp = Blueprint('admin_api', __name__, url_prefix='/api/admin')

# ============================================================================
# ENDPOINTS PRINCIPALES CORREGIDOS
# ============================================================================

@admin_api_bp.route('/health', methods=['GET'])
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

@admin_api_bp.route('/health/detailed', methods=['GET'])
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

@admin_api_bp.route('/empresas/<int:empresa_id>/incidentes', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_incidentes_empresa(empresa_id):
    """
    Obtiene los incidentes de una empresa específica - VERSIÓN ROBUSTA
    """
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

@admin_api_bp.route('/empresas/<int:empresa_id>/informe-cumplimiento', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_informe_cumplimiento(empresa_id):
    """
    Genera el informe de cumplimiento para una empresa - VERSIÓN ROBUSTA
    """
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error("No se pudo conectar a la base de datos")
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        # Verificar que las tablas existen
        if not db_validator.table_exists(cursor, 'Empresas'):
            return jsonify({"error": "Sistema no disponible - tablas faltantes"}), 503
        
        # Verificar que la empresa existe
        cursor.execute("SELECT EmpresaID, RazonSocial, TipoEmpresa FROM Empresas WHERE EmpresaID = ?", (empresa_id,))
        empresa = cursor.fetchone()
        
        if not empresa:
            response, status = ErrorResponse.not_found_error("Empresa")
            return jsonify(response), status
        
        # Crear informe básico por defecto
        informe_basico = {
            'empresa': {
                'EmpresaID': empresa[0],
                'RazonSocial': empresa[1],
                'TipoEmpresa': empresa[2] if len(empresa) > 2 else 'PSE'
            },
            'estadisticas_generales': {
                'total_obligaciones': 0,
                'implementadas': 0,
                'en_proceso': 0,
                'pendientes': 0,
                'porcentaje_cumplimiento': 0
            },
            'fecha_generacion': format_date_safe(datetime.now())
        }
        
        # Intentar obtener estadísticas de cumplimiento si la tabla existe
        if db_validator.table_exists(cursor, 'CumplimientoEmpresa'):
            try:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as Total,
                        SUM(CASE WHEN Estado = 'Implementado' THEN 1 ELSE 0 END) as Impl,
                        SUM(CASE WHEN Estado = 'En Proceso' THEN 1 ELSE 0 END) as Proc,
                        SUM(CASE WHEN Estado = 'Pendiente' THEN 1 ELSE 0 END) as Pend
                    FROM CumplimientoEmpresa 
                    WHERE EmpresaID = ?
                """, (empresa_id,))
                
                stats = cursor.fetchone()
                if stats and stats[0] > 0:
                    informe_basico['estadisticas_generales'] = {
                        'total_obligaciones': stats[0],
                        'implementadas': stats[1] or 0,
                        'en_proceso': stats[2] or 0,
                        'pendientes': stats[3] or 0,
                        'porcentaje_cumplimiento': round((stats[1] or 0) / stats[0] * 100, 2) if stats[0] > 0 else 0
                    }
            except Exception as e:
                print(f"Error obteniendo estadísticas de cumplimiento: {e}")
                # Mantener valores por defecto
        
        return jsonify(informe_basico)
        
    finally:
        if conn:
            conn.close()

@admin_api_bp.route('/empresas/<int:empresa_id>', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_empresa_details(empresa_id):
    """
    Obtiene los detalles de una empresa específica - VERSIÓN ROBUSTA
    """
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
        
        # Convertir a diccionario
        columns = [column[0] for column in cursor.description]
        empresa_data = dict(zip(columns, empresa_row))
        
        return jsonify(empresa_data)
    
    finally:
        if conn:
            conn.close()

@admin_api_bp.route('/empresas/<int:empresa_id>/dashboard-stats', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_dashboard_stats(empresa_id):
    """
    Obtiene estadísticas del dashboard para una empresa específica - VERSIÓN ROBUSTA
    """
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error("No se pudo conectar a la base de datos")
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        # Estadísticas básicas de ejemplo (se puede expandir según necesidad)
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

@admin_api_bp.route('/empresas/<int:empresa_id>/cumplimientos', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_cumplimientos_empresa(empresa_id):
    """
    Obtiene todos los cumplimientos de una empresa - VERSIÓN ROBUSTA
    """
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error("No se pudo conectar a la base de datos")
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        # Verificar que la empresa existe
        if not db_validator.table_exists(cursor, 'Empresas'):
            return jsonify([])
        
        cursor.execute("SELECT EmpresaID FROM Empresas WHERE EmpresaID = ?", (empresa_id,))
        if not cursor.fetchone():
            response, status = ErrorResponse.not_found_error("Empresa")
            return jsonify(response), status
        
        # Retornar datos de cumplimiento solo si la tabla existe
        if not db_validator.table_exists(cursor, 'CumplimientoEmpresa'):
            return jsonify([])  # Sin tabla de cumplimiento, retornar vacío
        
        # Obtener cumplimientos básicos
        try:
            cursor.execute("""
                SELECT 
                    CumplimientoID,
                    EmpresaID,
                    ObligacionID,
                    Estado,
                    PorcentajeAvance,
                    Responsable,
                    FechaTermino
                FROM CumplimientoEmpresa
                WHERE EmpresaID = ?
                ORDER BY ObligacionID
            """, (empresa_id,))
            
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            cumplimientos = [dict(zip(columns, row)) for row in rows]
            
            return jsonify(cumplimientos)
            
        except Exception as e:
            print(f"Error obteniendo cumplimientos: {e}")
            return jsonify([])
    
    finally:
        if conn:
            conn.close()
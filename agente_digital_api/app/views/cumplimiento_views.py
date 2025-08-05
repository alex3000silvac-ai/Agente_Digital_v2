# views/cumplimiento_views.py
# Módulo especializado para endpoints de cumplimiento

from flask import Blueprint, jsonify, request
from ..db_validator import db_validator
from ..error_handlers import robust_endpoint, ErrorResponse
from ..database import get_db_connection
from datetime import datetime

cumplimiento_bp = Blueprint('cumplimiento_api', __name__, url_prefix='/api/admin/empresas')

def format_date_safe(fecha, formato='%Y-%m-%d %H:%M:%S'):
    """Formatea una fecha de forma segura"""
    if not fecha:
        return None
    
    if hasattr(fecha, 'strftime'):
        return fecha.strftime(formato)
    else:
        return str(fecha)

@cumplimiento_bp.route('/<int:empresa_id>/informe-cumplimiento', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_informe_cumplimiento(empresa_id):
    """Genera el informe de cumplimiento para una empresa"""
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

@cumplimiento_bp.route('/<int:empresa_id>/cumplimientos', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_cumplimientos_empresa(empresa_id):
    """Obtiene todos los cumplimientos de una empresa"""
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
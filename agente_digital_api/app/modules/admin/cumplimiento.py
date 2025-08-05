# modules/admin/cumplimiento.py
# Gestión de cumplimiento completamente modular

from flask import Blueprint, jsonify, request
from datetime import datetime
from ..core.database import get_db_connection, db_validator
from ..core.errors import robust_endpoint, ErrorResponse

cumplimiento_bp = Blueprint('admin_cumplimiento', __name__, url_prefix='/api/admin/empresas')

def format_date_safe(fecha, formato='%Y-%m-%d %H:%M:%S'):
    """Formatea fechas de forma segura"""
    if not fecha:
        return None
    return fecha.strftime(formato) if hasattr(fecha, 'strftime') else str(fecha)

@cumplimiento_bp.route('/<int:empresa_id>/informe-cumplimiento', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_informe_cumplimiento(empresa_id):
    """Genera informe de cumplimiento para una empresa"""
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error()
        return jsonify(response), status
    
    try:
        cursor = conn.cursor()
        
        # Verificar que las tablas existen
        if not db_validator.table_exists(cursor, 'Empresas'):
            return jsonify({"error": "Sistema no disponible"}), 503
        
        # Verificar que la empresa existe
        cursor.execute("SELECT EmpresaID, RazonSocial, TipoEmpresa FROM Empresas WHERE EmpresaID = ?", (empresa_id,))
        empresa = cursor.fetchone()
        
        if not empresa:
            response, status = ErrorResponse.not_found_error("Empresa")
            return jsonify(response), status
        
        # Crear informe básico
        informe = {
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
        
        # Obtener estadísticas de cumplimiento si la tabla existe
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
                    informe['estadisticas_generales'] = {
                        'total_obligaciones': stats[0],
                        'implementadas': stats[1] or 0,
                        'en_proceso': stats[2] or 0,
                        'pendientes': stats[3] or 0,
                        'porcentaje_cumplimiento': round((stats[1] or 0) / stats[0] * 100, 2) if stats[0] > 0 else 0
                    }
            except Exception as e:
                print(f"Error obteniendo estadísticas: {e}")
        
        # Obtener detalle de obligaciones
        obligaciones_detalle = []
        if db_validator.table_exists(cursor, 'OBLIGACIONES') and db_validator.table_exists(cursor, 'CumplimientoEmpresa'):
            try:
                # Obtener tipo de empresa
                tipo_empresa = empresa[2] if len(empresa) > 2 else 'PSE'
                
                cursor.execute("""
                    SELECT 
                        O.ObligacionID,
                        O.ArticuloNorma,
                        O.Descripcion,
                        O.MedioDeVerificacionSugerido,
                        ISNULL(CE.Estado, 'Pendiente') as Estado,
                        ISNULL(CE.PorcentajeAvance, 0) as PorcentajeAvance,
                        CE.Responsable,
                        CE.FechaTermino,
                        CE.ObservacionesCiberseguridad,
                        CE.ObservacionesLegales,
                        CE.CumplimientoID,
                        O.ContactoTecnicoComercial
                    FROM OBLIGACIONES O
                    LEFT JOIN CumplimientoEmpresa CE ON O.ObligacionID = CE.ObligacionID AND CE.EmpresaID = ?
                    WHERE (O.AplicaPara = ? OR O.AplicaPara = 'Ambos')
                    ORDER BY O.ArticuloNorma
                """, (empresa_id, tipo_empresa))
                
                rows = cursor.fetchall()
                for row in rows:
                    obligaciones_detalle.append({
                        'ObligacionID': row[0],
                        'ArticuloNorma': row[1],
                        'Descripcion': row[2],
                        'MedioDeVerificacionSugerido': row[3],
                        'Estado': row[4],
                        'PorcentajeAvance': row[5],
                        'Responsable': row[6],
                        'FechaTermino': format_date_safe(row[7], '%Y-%m-%d') if row[7] else None,
                        'ObservacionesCiberseguridad': row[8],
                        'ObservacionesLegales': row[9],
                        'CumplimientoID': row[10],
                        'ContactoTecnicoComercial': row[11]  # Campo directo de OBLIGACIONES
                    })
                    
            except Exception as e:
                print(f"Error obteniendo detalle de obligaciones: {e}")
        
        informe['obligaciones_detalle'] = obligaciones_detalle
        
        return jsonify(informe)
        
    finally:
        if conn:
            conn.close()

@cumplimiento_bp.route('/<int:empresa_id>/cumplimientos', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_cumplimientos_empresa(empresa_id):
    """Obtiene todos los cumplimientos de una empresa"""
    conn = get_db_connection()
    if not conn:
        response, status = ErrorResponse.database_error()
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
        
        # Retornar cumplimientos si la tabla existe
        if not db_validator.table_exists(cursor, 'CumplimientoEmpresa'):
            return jsonify([])
        
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

@cumplimiento_bp.route('/<int:empresa_id>/cumplimientos', methods=['POST'])
@robust_endpoint(require_authentication=False, validate_payload=['obligacion_id'], log_perf=True)
def create_cumplimiento(empresa_id):
    """Crea un nuevo registro de cumplimiento"""
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
        
        # Crear registro de cumplimiento
        cursor.execute("""
            INSERT INTO CumplimientoEmpresa (EmpresaID, ObligacionID, Estado, PorcentajeAvance)
            VALUES (?, ?, 'Pendiente', 0)
        """, (empresa_id, data['obligacion_id']))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cumplimiento creado exitosamente'
        }), 201
        
    except Exception as e:
        if conn:
            conn.rollback()
        response, status = ErrorResponse.generic_error(f"Error creando cumplimiento: {str(e)}")
        return jsonify(response), status
    
    finally:
        if conn:
            conn.close()
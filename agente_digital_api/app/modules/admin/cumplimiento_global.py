# modules/admin/cumplimiento_global.py
# Endpoints globales de cumplimiento para el frontend

from flask import Blueprint, jsonify, request
from ..core.database import get_db_connection
from datetime import datetime

cumplimiento_global_bp = Blueprint('admin_cumplimiento_global', __name__, url_prefix='/api/admin')

@cumplimiento_global_bp.route('/cumplimiento', methods=['POST', 'OPTIONS'])
def create_cumplimiento_global():
    """Crea un nuevo registro de cumplimiento"""
    
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    print("📨 POST /api/admin/cumplimiento - Iniciando procesamiento...")
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        data = request.get_json()
        
        # Validar datos requeridos
        empresa_id = data.get('EmpresaID')
        obligacion_id = data.get('ObligacionID')
        
        if not empresa_id or not obligacion_id:
            return jsonify({"error": "EmpresaID y ObligacionID son requeridos"}), 400
        
        # Verificar si ya existe un cumplimiento para esta combinación
        print(f"🔍 Verificando duplicados para Empresa={empresa_id}, Obligacion={obligacion_id}")
        cursor.execute("""
            SELECT CumplimientoID 
            FROM CumplimientoEmpresa 
            WHERE EmpresaID = ? AND ObligacionID = ?
        """, (empresa_id, obligacion_id))
        
        existing = cursor.fetchone()
        if existing:
            print(f"✏️ Registro existente encontrado con ID={existing.CumplimientoID}, actualizando...")
            # Si ya existe, actualizamos en lugar de crear uno nuevo
            cumplimiento_id = existing.CumplimientoID
            
            # Actualizar el registro existente
            cursor.execute("""
                UPDATE CumplimientoEmpresa 
                SET Estado = ?, 
                    PorcentajeAvance = ?,
                    Responsable = ?,
                    FechaTermino = ?
                WHERE CumplimientoID = ?
            """, (
                data.get('Estado', 'Pendiente'),
                data.get('PorcentajeAvance', 0),
                data.get('Responsable', ''),
                data.get('FechaTermino'),
                cumplimiento_id
            ))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Cumplimiento actualizado exitosamente',
                'CumplimientoID': cumplimiento_id,
                'updated': True
            }), 200
        
        # Insertar nuevo cumplimiento
        cursor.execute("""
            INSERT INTO CumplimientoEmpresa (
                EmpresaID, 
                ObligacionID, 
                Estado, 
                PorcentajeAvance,
                Responsable,
                FechaTermino
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            empresa_id,
            obligacion_id,
            data.get('Estado', 'Pendiente'),
            data.get('PorcentajeAvance', 0),
            data.get('Responsable', ''),
            data.get('FechaTermino')
        ))
        
        # Obtener el ID del registro insertado
        cursor.execute("SELECT SCOPE_IDENTITY()")
        cumplimiento_id = cursor.fetchone()[0]
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cumplimiento creado exitosamente',
            'CumplimientoID': cumplimiento_id
        }), 201
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error creando cumplimiento: {e}")
        return jsonify({"error": f"Error creando cumplimiento: {str(e)}"}), 500
    
    finally:
        if conn:
            conn.close()

@cumplimiento_global_bp.route('/cumplimiento/<int:cumplimiento_id>', methods=['PUT', 'OPTIONS'])
def update_cumplimiento_global(cumplimiento_id):
    """Actualiza un registro de cumplimiento existente"""
    
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        data = request.get_json()
        
        # Verificar que el cumplimiento existe
        cursor.execute("SELECT CumplimientoID FROM CumplimientoEmpresa WHERE CumplimientoID = ?", (cumplimiento_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Cumplimiento no encontrado"}), 404
        
        # Construir query de actualización dinámicamente
        update_fields = []
        params = []
        
        if 'Estado' in data:
            update_fields.append("Estado = ?")
            params.append(data['Estado'])
        
        if 'PorcentajeAvance' in data:
            update_fields.append("PorcentajeAvance = ?")
            params.append(data['PorcentajeAvance'])
        
        if 'Responsable' in data:
            update_fields.append("Responsable = ?")
            params.append(data['Responsable'])
        
        if 'FechaTermino' in data:
            update_fields.append("FechaTermino = ?")
            params.append(data['FechaTermino'])
        
        # Campos de observaciones si existen en la tabla
        if 'ObservacionesCiberseguridad' in data:
            # Verificar si la columna existe
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'CumplimientoEmpresa' 
                AND COLUMN_NAME = 'ObservacionesCiberseguridad'
            """)
            if cursor.fetchone():
                update_fields.append("ObservacionesCiberseguridad = ?")
                params.append(data['ObservacionesCiberseguridad'])
        
        if 'ObservacionesLegales' in data:
            # Verificar si la columna existe
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'CumplimientoEmpresa' 
                AND COLUMN_NAME = 'ObservacionesLegales'
            """)
            if cursor.fetchone():
                update_fields.append("ObservacionesLegales = ?")
                params.append(data['ObservacionesLegales'])
        
        if not update_fields:
            return jsonify({"error": "No hay campos para actualizar"}), 400
        
        # Agregar el ID al final de los parámetros
        params.append(cumplimiento_id)
        
        # Ejecutar actualización
        query = f"UPDATE CumplimientoEmpresa SET {', '.join(update_fields)} WHERE CumplimientoID = ?"
        cursor.execute(query, params)
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cumplimiento actualizado exitosamente'
        }), 200
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error actualizando cumplimiento: {e}")
        return jsonify({"error": f"Error actualizando cumplimiento: {str(e)}"}), 500
    
    finally:
        if conn:
            conn.close()

# Endpoints temporales (alias de los principales)
@cumplimiento_global_bp.route('/cumplimiento-temp', methods=['POST', 'OPTIONS'])
def create_cumplimiento_temp():
    """Endpoint temporal - redirige al principal"""
    return create_cumplimiento_global()

@cumplimiento_global_bp.route('/cumplimiento-temp/<int:cumplimiento_id>', methods=['PUT', 'OPTIONS'])
def update_cumplimiento_temp(cumplimiento_id):
    """Endpoint temporal - redirige al principal"""
    return update_cumplimiento_global(cumplimiento_id)

# Endpoint para obtener historial de cambios
@cumplimiento_global_bp.route('/cumplimiento/<int:cumplimiento_id>/historial', methods=['GET', 'OPTIONS'])
def get_historial_cumplimiento(cumplimiento_id):
    """Obtiene el historial de cambios de un cumplimiento"""
    
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Verificar si existe tabla de historial
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'HistorialCumplimiento'
        """)
        
        if not cursor.fetchone():
            # Si no existe la tabla, devolver array vacío
            return jsonify([]), 200
        
        # Obtener historial
        cursor.execute("""
            SELECT 
                HistorialID,
                CumplimientoID,
                CampoModificado,
                ValorAnterior,
                ValorNuevo,
                FechaCambio,
                UsuarioCambio
            FROM HistorialCumplimiento
            WHERE CumplimientoID = ?
            ORDER BY FechaCambio DESC
        """, (cumplimiento_id,))
        
        rows = cursor.fetchall()
        historial = []
        
        for row in rows:
            historial.append({
                "HistorialID": row.HistorialID,
                "CumplimientoID": row.CumplimientoID,
                "CampoModificado": row.CampoModificado,
                "ValorAnterior": row.ValorAnterior,
                "ValorNuevo": row.ValorNuevo,
                "FechaCambio": row.FechaCambio.strftime('%Y-%m-%d %H:%M:%S') if row.FechaCambio else None,
                "UsuarioCambio": row.UsuarioCambio or "Sistema"
            })
        
        return jsonify(historial), 200
        
    except Exception as e:
        print(f"Error obteniendo historial: {e}")
        # Si hay error, devolver array vacío en lugar de error
        return jsonify([]), 200
    
    finally:
        if conn:
            conn.close()

# Endpoint para obtener evidencias
@cumplimiento_global_bp.route('/cumplimiento/<int:cumplimiento_id>/evidencias', methods=['GET', 'OPTIONS'])
def get_evidencias_cumplimiento(cumplimiento_id):
    """Obtiene las evidencias de un cumplimiento"""
    
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Verificar si existe tabla de evidencias
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'EvidenciasCumplimiento'
        """)
        
        if not cursor.fetchone():
            # Si no existe la tabla, devolver array vacío
            return jsonify([]), 200
        
        # Obtener evidencias
        cursor.execute("""
            SELECT 
                EvidenciaID,
                CumplimientoID,
                NombreArchivoOriginal,
                TipoArchivo,
                TamanoArchivoKB,
                FechaSubida,
                UsuarioQueSubio,
                Descripcion,
                Version
            FROM EvidenciasCumplimiento
            WHERE CumplimientoID = ?
            ORDER BY FechaSubida DESC
        """, (cumplimiento_id,))
        
        rows = cursor.fetchall()
        evidencias = []
        
        for row in rows:
            evidencias.append({
                "EvidenciaID": row.EvidenciaID,
                "CumplimientoID": row.CumplimientoID,
                "NombreArchivoOriginal": row.NombreArchivoOriginal,
                "TipoArchivo": row.TipoArchivo or "",
                "TamanoArchivoKB": row.TamanoArchivoKB or 0,
                "FechaSubida": row.FechaSubida.strftime('%Y-%m-%d %H:%M:%S') if row.FechaSubida else None,
                "UsuarioQueSubio": row.UsuarioQueSubio or "Sistema",
                "Descripcion": row.Descripcion or "",
                "Version": getattr(row, 'Version', 1)
            })
        
        return jsonify(evidencias), 200
        
    except Exception as e:
        print(f"Error obteniendo evidencias: {e}")
        # Si hay error, devolver array vacío en lugar de error
        return jsonify([]), 200
    
    finally:
        if conn:
            conn.close()

# Endpoint para obtener resumen de evidencias con verificación de columna FechaVigencia
@cumplimiento_global_bp.route('/cumplimiento/<int:cumplimiento_id>/evidencias/resumen', methods=['GET', 'OPTIONS'])
def get_evidencias_resumen(cumplimiento_id):
    """Obtiene un resumen de las evidencias de un cumplimiento"""
    
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Verificar si existe tabla de evidencias
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'EvidenciasCumplimiento'
        """)
        
        if not cursor.fetchone():
            # Si no existe la tabla, devolver estructura vacía
            return jsonify({
                "evidencias": [],
                "estadisticas": {"total": 0, "vigentes": 0, "por_vencer": 0, "vencidos": 0}
            }), 200
        
        # Verificar si existe columna FechaVigencia
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'EvidenciasCumplimiento' 
            AND COLUMN_NAME = 'FechaVigencia'
        """)
        has_fecha_vigencia = cursor.fetchone() is not None
        
        if has_fecha_vigencia:
            # Query con FechaVigencia
            cursor.execute("""
                SELECT 
                    EvidenciaID as id,
                    NombreArchivoOriginal as nombre,
                    FechaSubida as fecha_subida,
                    Descripcion as descripcion,
                    ISNULL(Version, 1) as version,
                    CASE 
                        WHEN FechaVigencia IS NULL THEN 'vigente'
                        WHEN FechaVigencia > GETDATE() THEN 'vigente'
                        WHEN DATEDIFF(day, GETDATE(), FechaVigencia) <= 30 THEN 'por_vencer'
                        ELSE 'vencido'
                    END as estado,
                    CASE 
                        WHEN FechaVigencia IS NULL THEN 'Vigente'
                        WHEN FechaVigencia > GETDATE() THEN 'Vigente'
                        WHEN DATEDIFF(day, GETDATE(), FechaVigencia) <= 30 THEN 'Por vencer'
                        ELSE 'Vencido'
                    END as vigencia,
                    CASE 
                        WHEN LOWER(NombreArchivoOriginal) LIKE '%.pdf' THEN 'pdf'
                        WHEN LOWER(NombreArchivoOriginal) LIKE '%.doc%' THEN 'word'
                        WHEN LOWER(NombreArchivoOriginal) LIKE '%.xls%' THEN 'excel'
                        WHEN LOWER(NombreArchivoOriginal) LIKE '%.jpg' OR LOWER(NombreArchivoOriginal) LIKE '%.jpeg' OR LOWER(NombreArchivoOriginal) LIKE '%.png' THEN 'imagen'
                        ELSE 'archivo'
                    END as tipo_icono
                FROM EvidenciasCumplimiento
                WHERE CumplimientoID = ?
                ORDER BY FechaSubida DESC
            """, (cumplimiento_id,))
        else:
            # Query sin FechaVigencia
            cursor.execute("""
                SELECT 
                    EvidenciaID as id,
                    NombreArchivoOriginal as nombre,
                    FechaSubida as fecha_subida,
                    Descripcion as descripcion,
                    ISNULL(Version, 1) as version,
                    'vigente' as estado,
                    'Vigente' as vigencia,
                    CASE 
                        WHEN LOWER(NombreArchivoOriginal) LIKE '%.pdf' THEN 'pdf'
                        WHEN LOWER(NombreArchivoOriginal) LIKE '%.doc%' THEN 'word'
                        WHEN LOWER(NombreArchivoOriginal) LIKE '%.xls%' THEN 'excel'
                        WHEN LOWER(NombreArchivoOriginal) LIKE '%.jpg' OR LOWER(NombreArchivoOriginal) LIKE '%.jpeg' OR LOWER(NombreArchivoOriginal) LIKE '%.png' THEN 'imagen'
                        ELSE 'archivo'
                    END as tipo_icono
                FROM EvidenciasCumplimiento
                WHERE CumplimientoID = ?
                ORDER BY FechaSubida DESC
            """, (cumplimiento_id,))
        
        rows = cursor.fetchall()
        evidencias = []
        estadisticas = {"total": 0, "vigentes": 0, "por_vencer": 0, "vencidos": 0}
        
        for row in rows:
            evidencias.append({
                "id": row.id,
                "nombre": row.nombre,
                "fecha_subida": row.fecha_subida,
                "fecha_formateada": row.fecha_subida.strftime('%d/%m/%Y %H:%M') if row.fecha_subida else None,
                "descripcion": row.descripcion or "",
                "version": row.version,
                "estado": row.estado,
                "vigencia": row.vigencia,
                "tipo_icono": row.tipo_icono
            })
            estadisticas["total"] += 1
            if row.estado == "vigente":
                estadisticas["vigentes"] += 1
            elif row.estado == "por_vencer":
                estadisticas["por_vencer"] += 1
            elif row.estado == "vencido":
                estadisticas["vencidos"] += 1
        
        return jsonify({
            "evidencias": evidencias,
            "estadisticas": estadisticas
        }), 200
        
    except Exception as e:
        print(f"Error obteniendo resumen de evidencias: {e}")
        return jsonify({
            "evidencias": [],
            "estadisticas": {"total": 0, "vigentes": 0, "por_vencer": 0, "vencidos": 0}
        }), 200
    
    finally:
        if conn:
            conn.close()
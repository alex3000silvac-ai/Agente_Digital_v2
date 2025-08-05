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

# Endpoint para obtener resumen de evidencias
@cumplimiento_global_bp.route('/cumplimiento/<int:cumplimiento_id>/evidencias/resumen', methods=['GET', 'OPTIONS'])
def get_evidencias_resumen(cumplimiento_id):
    """Obtiene un resumen de las evidencias de un cumplimiento"""
    
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        # Simular datos de evidencias
        # En producción, esto vendría de la base de datos
        evidencias = [
            {
                "id": 1,
                "nombre": "Política_Ciberseguridad_2025.pdf",
                "fecha": "2025-01-15",
                "estado": "vigente",
                "icono": "ph-file-pdf"
            },
            {
                "id": 2,
                "nombre": "Certificado_ISO27001.pdf",
                "fecha": "2024-12-01",
                "estado": "por_vencer",
                "icono": "ph-file-pdf"
            }
        ]
        
        # Calcular estadísticas
        estadisticas = {
            "total": len(evidencias),
            "vigentes": sum(1 for e in evidencias if e["estado"] == "vigente"),
            "por_vencer": sum(1 for e in evidencias if e["estado"] == "por_vencer"),
            "vencidos": sum(1 for e in evidencias if e["estado"] == "vencido")
        }
        
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

# Endpoint para obtener resumen de evidencias
@cumplimiento_global_bp.route('/cumplimiento/<int:cumplimiento_id>/evidencias/resumen', methods=['GET', 'OPTIONS'])
def get_evidencias_resumen(cumplimiento_id):
    """Obtiene un resumen de las evidencias de un cumplimiento"""
    
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        # Simular datos de evidencias
        # En producción, esto vendría de la base de datos
        evidencias = [
            {
                "id": 1,
                "nombre": "Política_Ciberseguridad_2025.pdf",
                "fecha": "2025-01-15",
                "estado": "vigente",
                "icono": "ph-file-pdf"
            },
            {
                "id": 2,
                "nombre": "Certificado_ISO27001.pdf",
                "fecha": "2024-12-01",
                "estado": "por_vencer",
                "icono": "ph-file-pdf"
            }
        ]
        
        # Calcular estadísticas
        estadisticas = {
            "total": len(evidencias),
            "vigentes": sum(1 for e in evidencias if e["estado"] == "vigente"),
            "por_vencer": sum(1 for e in evidencias if e["estado"] == "por_vencer"),
            "vencidos": sum(1 for e in evidencias if e["estado"] == "vencido")
        }
        
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

# Endpoint para obtener resumen de evidencias
@cumplimiento_global_bp.route('/cumplimiento/<int:cumplimiento_id>/evidencias/resumen', methods=['GET', 'OPTIONS'])
def get_evidencias_resumen(cumplimiento_id):
    """Obtiene un resumen de las evidencias de un cumplimiento"""
    
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        # Simular datos de evidencias
        # En producción, esto vendría de la base de datos
        evidencias = [
            {
                "id": 1,
                "nombre": "Política_Ciberseguridad_2025.pdf",
                "fecha": "2025-01-15",
                "estado": "vigente",
                "icono": "ph-file-pdf"
            },
            {
                "id": 2,
                "nombre": "Certificado_ISO27001.pdf",
                "fecha": "2024-12-01",
                "estado": "por_vencer",
                "icono": "ph-file-pdf"
            }
        ]
        
        # Calcular estadísticas
        estadisticas = {
            "total": len(evidencias),
            "vigentes": sum(1 for e in evidencias if e["estado"] == "vigente"),
            "por_vencer": sum(1 for e in evidencias if e["estado"] == "por_vencer"),
            "vencidos": sum(1 for e in evidencias if e["estado"] == "vencido")
        }
        
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
                NombreArchivo,
                TipoArchivo,
                Tamaño,
                FechaCarga,
                UsuarioCarga,
                Descripcion
            FROM EvidenciasCumplimiento
            WHERE CumplimientoID = ?
            ORDER BY FechaCarga DESC
        """, (cumplimiento_id,))
        
        rows = cursor.fetchall()
        evidencias = []
        
        for row in rows:
            evidencias.append({
                "EvidenciaID": row.EvidenciaID,
                "CumplimientoID": row.CumplimientoID,
                "NombreArchivo": row.NombreArchivo,
                "TipoArchivo": row.TipoArchivo,
                "Tamaño": row.Tamaño,
                "FechaCarga": row.FechaCarga.strftime('%Y-%m-%d %H:%M:%S') if row.FechaCarga else None,
                "UsuarioCarga": row.UsuarioCarga or "Sistema",
                "Descripcion": row.Descripcion or ""
            })
        
        return jsonify(evidencias), 200
        
    except Exception as e:
        print(f"Error obteniendo evidencias: {e}")
        # Si hay error, devolver array vacío en lugar de error
        return jsonify([]), 200
    
    finally:
        if conn:
            conn.close()

# Endpoint para obtener resumen de evidencias
@cumplimiento_global_bp.route('/cumplimiento/<int:cumplimiento_id>/evidencias/resumen', methods=['GET', 'OPTIONS'])
def get_evidencias_resumen(cumplimiento_id):
    """Obtiene un resumen de las evidencias de un cumplimiento"""
    
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        # Simular datos de evidencias
        # En producción, esto vendría de la base de datos
        evidencias = [
            {
                "id": 1,
                "nombre": "Política_Ciberseguridad_2025.pdf",
                "fecha": "2025-01-15",
                "estado": "vigente",
                "icono": "ph-file-pdf"
            },
            {
                "id": 2,
                "nombre": "Certificado_ISO27001.pdf",
                "fecha": "2024-12-01",
                "estado": "por_vencer",
                "icono": "ph-file-pdf"
            }
        ]
        
        # Calcular estadísticas
        estadisticas = {
            "total": len(evidencias),
            "vigentes": sum(1 for e in evidencias if e["estado"] == "vigente"),
            "por_vencer": sum(1 for e in evidencias if e["estado"] == "por_vencer"),
            "vencidos": sum(1 for e in evidencias if e["estado"] == "vencido")
        }
        
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
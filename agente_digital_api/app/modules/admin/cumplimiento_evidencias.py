# modules/admin/cumplimiento_evidencias.py
# Endpoints para gestión de evidencias

from flask import Blueprint, jsonify, request, send_file
from ..core.database import get_db_connection
import io
import os
from datetime import datetime
import hashlib
from werkzeug.utils import secure_filename

cumplimiento_evidencias_bp = Blueprint('admin_cumplimiento_evidencias', __name__, url_prefix='/api/admin')

@cumplimiento_evidencias_bp.route('/cumplimiento/<int:cumplimiento_id>/evidencias', methods=['GET', 'OPTIONS'])
def list_evidencias_cumplimiento(cumplimiento_id):
    """Lista todas las evidencias de un cumplimiento específico"""
    
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Verificar que el cumplimiento existe
        cursor.execute("SELECT CumplimientoID FROM CumplimientoEmpresa WHERE CumplimientoID = ?", (cumplimiento_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Cumplimiento no encontrado"}), 404
        
        # Obtener todas las evidencias del cumplimiento
        query = """
            SELECT 
                EvidenciaID,
                NombreArchivoOriginal,
                NombreArchivoAlmacenado,
                RutaArchivo,
                TipoArchivo,
                TamanoArchivoKB,
                FechaSubida,
                ISNULL(Version, 1) as Version,
                ISNULL(UsuarioQueSubio, 'admin') as UsuarioQueSubio,
                ISNULL(Descripcion, '') as Descripcion,
                FechaVigencia,
                ISNULL(IPAddress, '') as IPAddress,
                ISNULL(UserAgent, '') as UserAgent
            FROM EvidenciasCumplimiento
            WHERE CumplimientoID = ?
            ORDER BY FechaSubida DESC
        """
        
        cursor.execute(query, (cumplimiento_id,))
        rows = cursor.fetchall()
        
        evidencias = []
        for row in rows:
            # Calcular estado de vigencia
            estado_vigencia = 'vigente'
            if row.FechaVigencia:
                fecha_vigencia = row.FechaVigencia
                if hasattr(fecha_vigencia, 'date'):
                    fecha_vigencia = fecha_vigencia.date()
                else:
                    fecha_vigencia = datetime.strptime(str(fecha_vigencia), '%Y-%m-%d').date()
                
                hoy = datetime.now().date()
                if fecha_vigencia < hoy:
                    estado_vigencia = 'vencido'
                elif (fecha_vigencia - hoy).days <= 30:
                    estado_vigencia = 'por_vencer'
            
            evidencia = {
                'EvidenciaID': row.EvidenciaID,
                'NombreArchivoOriginal': row.NombreArchivoOriginal,
                'NombreArchivoAlmacenado': row.NombreArchivoAlmacenado,
                'RutaArchivo': row.RutaArchivo,
                'TipoArchivo': row.TipoArchivo,
                'TamanoArchivoKB': row.TamanoArchivoKB,
                'FechaSubida': row.FechaSubida.isoformat() if row.FechaSubida else None,
                'Version': row.Version,
                'UsuarioQueSubio': row.UsuarioQueSubio,
                'Descripcion': row.Descripcion,
                'FechaVigencia': row.FechaVigencia.isoformat() if row.FechaVigencia else None,
                'IPAddress': row.IPAddress,
                'UserAgent': row.UserAgent,
                'EstadoVigencia': estado_vigencia
            }
            evidencias.append(evidencia)
        
        print(f"✅ Listadas {len(evidencias)} evidencias para cumplimiento {cumplimiento_id}")
        return jsonify(evidencias), 200
        
    except Exception as e:
        print(f"Error listando evidencias: {e}")
        return jsonify({"error": f"Error al listar evidencias: {str(e)}"}), 500
    
    finally:
        if conn:
            conn.close()

@cumplimiento_evidencias_bp.route('/cumplimiento/<int:cumplimiento_id>/evidencia', methods=['POST', 'OPTIONS'])
def upload_evidencia_cumplimiento(cumplimiento_id):
    """Sube una nueva evidencia para un cumplimiento"""
    
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Obtener datos del formulario
        file = request.files.get('file')
        descripcion = request.form.get('descripcion', '')
        fecha_vigencia = request.form.get('fecha_vigencia')
        
        if not file:
            return jsonify({"error": "No se proporcionó archivo"}), 400
        
        # Obtener información del cumplimiento para extraer InquilinoID y EmpresaID
        cursor.execute("""
            SELECT ce.EmpresaID, e.InquilinoID
            FROM CumplimientoEmpresa ce
            INNER JOIN EMPRESAS e ON ce.EmpresaID = e.EmpresaID
            WHERE ce.CumplimientoID = ?
        """, (cumplimiento_id,))
        
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Cumplimiento no encontrado"}), 404
        
        empresa_id = result.EmpresaID
        inquilino_id = result.InquilinoID or 1  # Default a 1 si no hay inquilino
        
        # Preparar información del archivo
        filename = secure_filename(file.filename)
        file_content = file.read()
        file_size_kb = len(file_content) / 1024
        file_type = file.content_type or 'application/octet-stream'
        
        # Generar nombre único para almacenar
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_hash = hashlib.md5(file_content).hexdigest()[:8]
        stored_filename = f"{timestamp}_{file_hash}_{filename}"
        
        # Crear estructura de directorios
        base_upload_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'uploads')
        inquilino_path = f"inquilino_{inquilino_id}"
        empresa_path = f"empresa_{empresa_id}"
        full_dir_path = os.path.join(base_upload_path, inquilino_path, empresa_path)
        
        # Crear directorios si no existen
        os.makedirs(full_dir_path, exist_ok=True)
        
        # Guardar archivo físicamente
        file_path = os.path.join(full_dir_path, stored_filename)
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Ruta relativa para guardar en la base de datos
        relative_path = os.path.join(inquilino_path, empresa_path, stored_filename)
        
        # Verificar qué columnas existen en la tabla
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'EvidenciasCumplimiento'
        """)
        existing_columns = [row.COLUMN_NAME for row in cursor.fetchall()]
        
        # Construir INSERT dinámicamente basado en columnas existentes
        insert_columns = ['CumplimientoID', 'NombreArchivoOriginal', 'NombreArchivoAlmacenado', 
                         'RutaArchivo', 'TipoArchivo', 'TamanoArchivoKB', 'FechaSubida']
        insert_values = [cumplimiento_id, filename, stored_filename, relative_path, 
                        file_type, file_size_kb, datetime.now()]
        
        # Agregar columnas opcionales si existen
        if 'Version' in existing_columns:
            insert_columns.append('Version')
            insert_values.append(1)
            
        if 'UsuarioQueSubio' in existing_columns:
            insert_columns.append('UsuarioQueSubio')
            insert_values.append('admin')  # TODO: Obtener del contexto de sesión
            
        if 'InquilinoID' in existing_columns:
            insert_columns.append('InquilinoID')
            insert_values.append(inquilino_id)
            
        if 'EmpresaID' in existing_columns:
            insert_columns.append('EmpresaID')
            insert_values.append(empresa_id)
            
        if 'IPAddress' in existing_columns:
            insert_columns.append('IPAddress')
            insert_values.append(request.remote_addr)
            
        if 'UserAgent' in existing_columns:
            insert_columns.append('UserAgent')
            insert_values.append(request.headers.get('User-Agent', '')[:255])
            
        if 'Descripcion' in existing_columns:
            insert_columns.append('Descripcion')
            insert_values.append(descripcion)
            
        if 'FechaVigencia' in existing_columns and fecha_vigencia:
            insert_columns.append('FechaVigencia')
            insert_values.append(fecha_vigencia)
        
        # Construir y ejecutar query
        placeholders = ', '.join(['?' for _ in insert_values])
        columns_str = ', '.join(insert_columns)
        
        query = f"""
            INSERT INTO EvidenciasCumplimiento ({columns_str})
            VALUES ({placeholders})
        """
        
        cursor.execute(query, insert_values)
        
        # Obtener el ID del registro insertado
        cursor.execute("SELECT SCOPE_IDENTITY()")
        evidencia_id = cursor.fetchone()[0]
        
        conn.commit()
        
        print(f"✅ Archivo guardado: {relative_path} ({file_size_kb:.2f} KB) - ID: {evidencia_id}")
        
        return jsonify({
            "success": True,
            "message": "Archivo subido exitosamente",
            "filename": filename,
            "size_kb": round(file_size_kb, 2)
        }), 201
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error subiendo evidencia: {e}")
        return jsonify({"error": f"Error al subir archivo: {str(e)}"}), 500
    
    finally:
        if conn:
            conn.close()

# Endpoint para eliminar evidencias
@cumplimiento_evidencias_bp.route('/evidencia/<int:evidencia_id>', methods=['DELETE', 'OPTIONS'])
def delete_evidencia(evidencia_id):
    """Elimina una evidencia"""
    
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Obtener información del archivo antes de eliminar
        cursor.execute("""
            SELECT RutaArchivo 
            FROM EvidenciasCumplimiento 
            WHERE EvidenciaID = ?
        """, (evidencia_id,))
        
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Evidencia no encontrada"}), 404
        
        ruta_archivo = result.RutaArchivo
        
        # Eliminar archivo físico si existe
        if ruta_archivo:
            base_upload_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'uploads')
            file_path = os.path.join(base_upload_path, ruta_archivo)
            
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"✅ Archivo físico eliminado: {file_path}")
                except Exception as e:
                    print(f"⚠️ No se pudo eliminar archivo físico: {e}")
        
        # Eliminar registro de la base de datos
        cursor.execute("DELETE FROM EvidenciasCumplimiento WHERE EvidenciaID = ?", (evidencia_id,))
        
        conn.commit()
        
        print(f"✅ Evidencia ID {evidencia_id} eliminada")
        
        return jsonify({
            "success": True,
            "message": "Evidencia eliminada exitosamente"
        }), 200
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error eliminando evidencia: {e}")
        return jsonify({"error": f"Error al eliminar evidencia: {str(e)}"}), 500
    
    finally:
        if conn:
            conn.close()

# Endpoint para visualizar/descargar evidencias
@cumplimiento_evidencias_bp.route('/evidencia/<int:evidencia_id>', methods=['GET', 'OPTIONS'])
def get_evidencia(evidencia_id):
    """Obtiene una evidencia para visualización/descarga"""
    
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Obtener información del archivo
        cursor.execute("""
            SELECT 
                NombreArchivoOriginal,
                RutaArchivo,
                TipoArchivo
            FROM EvidenciasCumplimiento
            WHERE EvidenciaID = ?
        """, (evidencia_id,))
        
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Evidencia no encontrada"}), 404
        
        nombre_original = result.NombreArchivoOriginal
        ruta_archivo = result.RutaArchivo
        tipo_archivo = result.TipoArchivo or 'application/octet-stream'
        
        # Construir ruta completa del archivo
        base_upload_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'uploads')
        file_path = os.path.join(base_upload_path, ruta_archivo)
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            print(f"❌ Archivo no encontrado: {file_path}")
            return jsonify({"error": "Archivo no encontrado en el servidor"}), 404
        
        print(f"✅ Enviando archivo: {nombre_original} ({tipo_archivo})")
        
        # Determinar si se debe descargar o visualizar
        as_attachment = request.args.get('download', 'false').lower() == 'true'
        
        return send_file(
            file_path,
            mimetype=tipo_archivo,
            as_attachment=as_attachment,
            download_name=nombre_original
        )
        
    except Exception as e:
        print(f"Error obteniendo evidencia: {e}")
        return jsonify({"error": f"Error al obtener evidencia: {str(e)}"}), 500
    
    finally:
        if conn:
            conn.close()

# Endpoint para actualizar evidencias
@cumplimiento_evidencias_bp.route('/evidencia/<int:evidencia_id>', methods=['PUT', 'OPTIONS'])
def update_evidencia(evidencia_id):
    """Actualiza los metadatos de una evidencia"""
    
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        data = request.get_json()
        
        # Verificar que la evidencia existe
        cursor.execute("SELECT EvidenciaID FROM EvidenciasCumplimiento WHERE EvidenciaID = ?", (evidencia_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Evidencia no encontrada"}), 404
        
        # Actualizar campos que vengan en el request
        update_fields = []
        params = []
        
        if 'descripcion' in data:
            update_fields.append("Descripcion = ?")
            params.append(data['descripcion'])
        
        if 'fecha_vigencia' in data:
            # Verificar si la columna FechaVigencia existe
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'EvidenciasCumplimiento' 
                AND COLUMN_NAME = 'FechaVigencia'
            """)
            if cursor.fetchone():
                update_fields.append("FechaVigencia = ?")
                params.append(data['fecha_vigencia'])
        
        if not update_fields:
            return jsonify({"error": "No hay campos para actualizar"}), 400
        
        # Agregar el ID al final de los parámetros
        params.append(evidencia_id)
        
        # Ejecutar actualización
        query = f"UPDATE EvidenciasCumplimiento SET {', '.join(update_fields)} WHERE EvidenciaID = ?"
        cursor.execute(query, params)
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Evidencia actualizada exitosamente'
        }), 200
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error actualizando evidencia: {e}")
        return jsonify({"error": f"Error actualizando evidencia: {str(e)}"}), 500
    
    finally:
        if conn:
            conn.close()

# Endpoint para actualizar solo el comentario de una evidencia
@cumplimiento_evidencias_bp.route('/evidencia/<int:evidencia_id>/comentario', methods=['PUT', 'OPTIONS'])
def update_evidencia_comentario(evidencia_id):
    """Actualiza solo el comentario (descripción) de una evidencia"""
    
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        data = request.get_json()
        
        # Verificar que la evidencia existe
        cursor.execute("SELECT EvidenciaID FROM EvidenciasCumplimiento WHERE EvidenciaID = ?", (evidencia_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Evidencia no encontrada"}), 404
        
        # Obtener el comentario del request
        descripcion = data.get('descripcion', '')
        
        # Actualizar el comentario
        cursor.execute("""
            UPDATE EvidenciasCumplimiento 
            SET Descripcion = ? 
            WHERE EvidenciaID = ?
        """, (descripcion, evidencia_id))
        
        conn.commit()
        
        print(f"✅ Comentario actualizado para evidencia ID {evidencia_id}")
        
        return jsonify({
            'success': True,
            'message': 'Comentario actualizado exitosamente'
        }), 200
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error actualizando comentario: {e}")
        return jsonify({"error": f"Error actualizando comentario: {str(e)}"}), 500
    
    finally:
        if conn:
            conn.close()

# Endpoint temporal sin autenticación (fallback)
@cumplimiento_evidencias_bp.route('/evidencia-temp/<int:evidencia_id>', methods=['GET', 'OPTIONS'])
def get_evidencia_temp(evidencia_id):
    """Obtiene una evidencia sin autenticación (temporal)"""
    return get_evidencia(evidencia_id)
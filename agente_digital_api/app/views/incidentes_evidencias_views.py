# incidentes_evidencias_views.py
# Endpoints para gestión de evidencias de incidentes

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import pyodbc
from datetime import datetime
import uuid
from ..modules.core.database import get_db_connection
from ..modules.core.errors import robust_endpoint

incidentes_evidencias_bp = Blueprint('incidentes_evidencias', __name__, url_prefix='/api/admin')

# Configuración
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'xlsx', 'doc', 'xls', 'csv', 'log', 'xml', 'json'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@incidentes_evidencias_bp.route('/incidentes/<int:incidente_id>/evidencias', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def get_evidencias_incidente(incidente_id):
    """Obtiene todas las evidencias de un incidente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT 
                ei.EvidenciaIncidenteID,
                ei.NombreArchivoOriginal,
                ei.NombreArchivoAlmacenado,
                ei.RutaArchivo,
                ei.TamanoArchivoKB,
                ei.TipoArchivo,
                ei.Descripcion,
                ei.Version,
                ei.FechaSubida,
                ei.SubidoPor,
                ei.UsuarioQueSubio,
                ei.FechaVigencia,
                ei.EsUltimaVersion,
                ei.HashArchivo
            FROM dbo.EvidenciasIncidentes ei
            WHERE ei.IncidenteID = ?
            ORDER BY ei.FechaSubida DESC
        """
        
        cursor.execute(query, (incidente_id,))
        evidencias = []
        
        for row in cursor.fetchall():
            evidencia = {
                'EvidenciaIncidenteID': row.EvidenciaIncidenteID,
                'NombreArchivoOriginal': row.NombreArchivoOriginal,
                'NombreArchivoAlmacenado': row.NombreArchivoAlmacenado,
                'RutaArchivo': row.RutaArchivo,
                'TamanoKB': row.TamanoArchivoKB,
                'TipoArchivo': row.TipoArchivo,
                'Descripcion': row.Descripcion,
                'Version': row.Version or 1,
                'FechaSubida': row.FechaSubida.isoformat() if row.FechaSubida else None,
                'SubidoPor': row.SubidoPor,
                'UsuarioQueSubio': row.UsuarioQueSubio or row.SubidoPor or 'Sistema',
                'FechaVigencia': row.FechaVigencia.isoformat() if row.FechaVigencia else None,
                'EsUltimaVersion': row.EsUltimaVersion if hasattr(row, 'EsUltimaVersion') else True
            }
            evidencias.append(evidencia)
        
        return jsonify(evidencias), 200
        
    except Exception as e:
        print(f"Error obteniendo evidencias: {str(e)}")
        return jsonify({'error': 'Error al obtener evidencias'}), 500
    finally:
        cursor.close()
        conn.close()

@incidentes_evidencias_bp.route('/incidentes/<int:incidente_id>/evidencia', methods=['POST'])
@robust_endpoint(require_authentication=False, log_perf=True)
def upload_evidencia_incidente(incidente_id):
    """Sube una nueva evidencia para un incidente"""
    
    # Verificar que hay archivo
    if 'file' not in request.files:
        return jsonify({'error': 'No se proporcionó ningún archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Tipo de archivo no permitido'}), 400
    
    # Verificar tamaño
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': f'El archivo excede el tamaño máximo permitido de {MAX_FILE_SIZE/1024/1024}MB'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar que el incidente existe
        cursor.execute("SELECT EmpresaID FROM dbo.Incidentes WHERE IncidenteID = ?", (incidente_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'Incidente no encontrado'}), 404
        
        empresa_id = result.EmpresaID
        
        # Obtener inquilino_id
        cursor.execute("SELECT InquilinoID FROM dbo.Empresas WHERE EmpresaID = ?", (empresa_id,))
        inquilino_result = cursor.fetchone()
        inquilino_id = inquilino_result.InquilinoID if inquilino_result else 1
        
        # Generar nombre único para el archivo
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Crear directorio si no existe
        year = datetime.now().year
        month = datetime.now().month
        upload_base = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'uploads')
        upload_path = os.path.join(upload_base, 'incidentes', str(incidente_id), str(year), str(month).zfill(2))
        
        os.makedirs(upload_path, exist_ok=True)
        # La ruta completa del archivo
        full_file_path = os.path.join(upload_path, unique_filename)
        
        # Guardar archivo
        file.save(full_file_path)
        
        # Ruta relativa para la BD
        relative_path = os.path.join('uploads', 'incidentes', str(incidente_id), str(year), str(month).zfill(2), unique_filename).replace('\\', '/')
        
        # Obtener la última versión
        cursor.execute("""
            SELECT COALESCE(MAX(Version), 0) + 1 as NextVersion
            FROM dbo.EvidenciasIncidentes 
            WHERE IncidenteID = ? AND NombreArchivoOriginal = ?
        """, (incidente_id, filename))
        next_version = cursor.fetchone().NextVersion
        
        # Obtener información del usuario (por ahora hardcoded)
        usuario_id = request.headers.get('X-User-Id', 'admin')
        
        # Obtener metadata del formulario
        descripcion = request.form.get('descripcion', '')
        fecha_vigencia = request.form.get('fechaVigencia', None)
        
        # Insertar registro
        query = """
            INSERT INTO dbo.EvidenciasIncidentes (
                IncidenteID, 
                NombreArchivoOriginal, 
                NombreArchivoAlmacenado,
                RutaArchivo, 
                TamanoArchivoKB, 
                TipoArchivo,
                Descripcion, 
                Version, 
                FechaSubida, 
                SubidoPor,
                UsuarioQueSubio,
                FechaVigencia,
                InquilinoID,
                EmpresaID,
                EsUltimaVersion
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, ?, ?, ?, ?, 1)
        """
        
        cursor.execute(query, (
            incidente_id,
            filename,
            unique_filename,
            relative_path,
            file_size / 1024,  # Convertir a KB
            file_extension,
            descripcion,
            next_version,
            usuario_id,
            usuario_id,
            fecha_vigencia,
            inquilino_id,
            empresa_id
        ))
        
        # Marcar versiones anteriores como no última versión
        if next_version > 1:
            cursor.execute("""
                UPDATE dbo.EvidenciasIncidentes 
                SET EsUltimaVersion = 0 
                WHERE IncidenteID = ? 
                AND NombreArchivoOriginal = ? 
                AND Version < ?
            """, (incidente_id, filename, next_version))
        
        conn.commit()
        
        return jsonify({
            'message': 'Archivo subido exitosamente',
            'filename': filename,
            'version': next_version
        }), 200
        
    except Exception as e:
        print(f"Error subiendo evidencia: {str(e)}")
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': 'Error al subir el archivo'}), 500
    finally:
        cursor.close()
        conn.close()

@incidentes_evidencias_bp.route('/evidencia-incidente/<int:evidencia_id>', methods=['GET'])
@robust_endpoint(require_authentication=False, log_perf=True)
def download_evidencia_incidente(evidencia_id):
    """Descarga una evidencia específica"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Obtener información del archivo
        cursor.execute("""
            SELECT RutaArchivo, NombreArchivoOriginal, TipoArchivo
            FROM dbo.EvidenciasIncidentes
            WHERE EvidenciaIncidenteID = ?
        """, (evidencia_id,))
        
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'Evidencia no encontrada'}), 404
        
        # Construir ruta completa
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        file_path = os.path.join(base_path, result.RutaArchivo)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Archivo no encontrado en el sistema'}), 404
        
        # Determinar mimetype
        mimetype = 'application/octet-stream'
        if result.TipoArchivo:
            ext_to_mime = {
                'pdf': 'application/pdf',
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'gif': 'image/gif',
                'txt': 'text/plain',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'doc': 'application/msword',
                'xls': 'application/vnd.ms-excel'
            }
            mimetype = ext_to_mime.get(result.TipoArchivo.lower(), 'application/octet-stream')
        
        return send_file(
            file_path,
            mimetype=mimetype,
            as_attachment=True,
            download_name=result.NombreArchivoOriginal
        )
        
    except Exception as e:
        print(f"Error descargando evidencia: {str(e)}")
        return jsonify({'error': 'Error al descargar el archivo'}), 500
    finally:
        cursor.close()
        conn.close()

@incidentes_evidencias_bp.route('/evidencia-incidente/<int:evidencia_id>', methods=['DELETE'])
@robust_endpoint(require_authentication=False, log_perf=True)
def delete_evidencia_incidente(evidencia_id):
    """Elimina una evidencia específica"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Obtener información del archivo
        cursor.execute("""
            SELECT RutaArchivo, IncidenteID
            FROM dbo.EvidenciasIncidentes
            WHERE EvidenciaIncidenteID = ?
        """, (evidencia_id,))
        
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'Evidencia no encontrada'}), 404
        
        # Eliminar archivo físico si existe
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        file_path = os.path.join(base_path, result.RutaArchivo)
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error eliminando archivo físico: {str(e)}")
        
        # Eliminar registro de la BD
        cursor.execute("DELETE FROM dbo.EvidenciasIncidentes WHERE EvidenciaIncidenteID = ?", (evidencia_id,))
        conn.commit()
        
        return jsonify({'message': 'Evidencia eliminada exitosamente'}), 200
        
    except Exception as e:
        print(f"Error eliminando evidencia: {str(e)}")
        return jsonify({'error': 'Error al eliminar la evidencia'}), 500
    finally:
        cursor.close()
        conn.close()

@incidentes_evidencias_bp.route('/evidencia-incidente/<int:evidencia_id>', methods=['PUT'])
@robust_endpoint(require_authentication=False, log_perf=True)
def update_evidencia_incidente(evidencia_id):
    """Actualiza la metadata de una evidencia"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        data = request.get_json()
        
        # Verificar que la evidencia existe
        cursor.execute("SELECT 1 FROM dbo.EvidenciasIncidentes WHERE EvidenciaIncidenteID = ?", (evidencia_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Evidencia no encontrada'}), 404
        
        # Actualizar campos permitidos
        update_fields = []
        params = []
        
        if 'descripcion' in data:
            update_fields.append("Descripcion = ?")
            params.append(data['descripcion'])
        
        if 'fechaVigencia' in data:
            update_fields.append("FechaVigencia = ?")
            params.append(data['fechaVigencia'])
        
        if update_fields:
            query = f"UPDATE dbo.EvidenciasIncidentes SET {', '.join(update_fields)} WHERE EvidenciaIncidenteID = ?"
            params.append(evidencia_id)
            cursor.execute(query, params)
            conn.commit()
        
        return jsonify({'message': 'Evidencia actualizada exitosamente'}), 200
        
    except Exception as e:
        print(f"Error actualizando evidencia: {str(e)}")
        return jsonify({'error': 'Error al actualizar la evidencia'}), 500
    finally:
        cursor.close()
        conn.close()
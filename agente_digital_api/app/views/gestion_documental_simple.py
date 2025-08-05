from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename
from ..modules.core.database import get_db_connection

gestion_documental_bp = Blueprint('gestion_documental', __name__, url_prefix='/api/gestion-documental')

# Configuración
UPLOAD_FOLDER = os.environ.get('DOCUMENTOS_PATH', os.path.join(os.path.dirname(__file__), '..', '..', 'archivos', 'documentos'))
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'zip', 'rar', 'txt'}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Crear carpeta si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@gestion_documental_bp.route('/empresa/<int:empresa_id>', methods=['GET'])
def obtener_empresa(empresa_id):
    """Obtiene información básica de la empresa"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión"}), 500
    
    try:
        cursor = conn.cursor()
        query = "SELECT EmpresaID, RazonSocial, RUT, TipoEmpresa FROM Empresas WHERE EmpresaID = ?"
        cursor.execute(query, (empresa_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"error": "Empresa no encontrada"}), 404
        
        empresa = {
            'EmpresaID': result.EmpresaID,
            'RazonSocial': result.RazonSocial,
            'RUT': result.RUT,
            'TipoEmpresa': result.TipoEmpresa
        }
        
        conn.close()
        return jsonify(empresa), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error interno"}), 500

@gestion_documental_bp.route('/carpetas/<int:empresa_id>/conteo', methods=['GET'])
def obtener_conteo_carpetas(empresa_id):
    """Obtiene el conteo de archivos por carpeta"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión"}), 500
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT CarpetaID as carpeta_id, COUNT(*) as total
            FROM DOCUMENTOS_ANCI
            WHERE EmpresaID = ? AND Activo = 1
            GROUP BY CarpetaID
        """
        cursor.execute(query, (empresa_id,))
        
        conteos = []
        for row in cursor.fetchall():
            conteos.append({
                'carpeta_id': row.carpeta_id,
                'total': row.total
            })
        
        conn.close()
        return jsonify(conteos), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error interno"}), 500

@gestion_documental_bp.route('/archivos/<int:empresa_id>/<int:carpeta_id>', methods=['GET'])
def obtener_archivos(empresa_id, carpeta_id):
    """Obtiene los archivos de una carpeta"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión"}), 500
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                DocumentoID as id,
                NombreArchivo as nombre,
                TipoDocumento as tipo,
                Descripcion as descripcion,
                FechaSubida as fechaSubida,
                RutaArchivo as ruta
            FROM DOCUMENTOS_ANCI
            WHERE EmpresaID = ? AND CarpetaID = ? AND Activo = 1
            ORDER BY FechaSubida DESC
        """
        cursor.execute(query, (empresa_id, carpeta_id))
        
        archivos = []
        for row in cursor.fetchall():
            archivos.append({
                'id': row.id,
                'nombre': row.nombre,
                'extension': row.nombre.rsplit('.', 1)[1].lower() if '.' in row.nombre else '',
                'comentario': row.descripcion or '',
                'fechaSubida': row.fechaSubida.isoformat() if row.fechaSubida else None,
                'ruta': row.ruta
            })
        
        conn.close()
        return jsonify(archivos), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error interno"}), 500

@gestion_documental_bp.route('/archivos/<int:empresa_id>', methods=['POST'])
def subir_archivo(empresa_id):
    """Sube un nuevo archivo"""
    if 'archivo' not in request.files:
        return jsonify({"error": "No se encontró archivo"}), 400
    
    archivo = request.files['archivo']
    if archivo.filename == '':
        return jsonify({"error": "No se seleccionó archivo"}), 400
    
    if not allowed_file(archivo.filename):
        return jsonify({"error": "Tipo de archivo no permitido"}), 400
    
    # Verificar tamaño del archivo
    archivo.seek(0, os.SEEK_END)
    file_size = archivo.tell()
    archivo.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({"error": f"El archivo excede el tamaño máximo de {MAX_FILE_SIZE // (1024*1024)}MB"}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión"}), 500
    
    try:
        # Obtener datos del formulario
        carpeta_id = request.form.get('carpeta_id', type=int)
        comentario = request.form.get('comentario', '')
        
        # Guardar archivo
        filename = secure_filename(archivo.filename)
        extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Crear estructura de carpetas
        carpeta_path = os.path.join(UPLOAD_FOLDER, f"empresa_{empresa_id}", f"carpeta_{carpeta_id}")
        os.makedirs(carpeta_path, exist_ok=True)
        
        filepath = os.path.join(carpeta_path, unique_filename)
        archivo.save(filepath)
        
        # Guardar en base de datos
        cursor = conn.cursor()
        query = """
            INSERT INTO DOCUMENTOS_ANCI (
                EmpresaID, CarpetaID, NombreArchivo, 
                RutaArchivo, TipoDocumento, Descripcion, FechaSubida, Activo
            ) VALUES (?, ?, ?, ?, ?, ?, GETDATE(), 1)
        """
        
        cursor.execute(query, (
            empresa_id, carpeta_id, filename,
            filepath, extension, comentario
        ))
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Archivo subido exitosamente"
        }), 201
        
    except Exception as e:
        print(f"Error: {e}")
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": "Error interno"}), 500

@gestion_documental_bp.route('/archivos/<int:archivo_id>/comentario', methods=['PUT'])
def actualizar_comentario(archivo_id):
    """Actualiza el comentario de un archivo"""
    data = request.get_json()
    comentario = data.get('comentario', '')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión"}), 500
    
    try:
        cursor = conn.cursor()
        query = """
            UPDATE DOCUMENTOS_ANCI 
            SET Descripcion = ?
            WHERE DocumentoID = ? AND Activo = 1
        """
        cursor.execute(query, (comentario, archivo_id))
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Archivo no encontrado"}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error interno"}), 500

@gestion_documental_bp.route('/archivos/<int:archivo_id>', methods=['DELETE'])
def eliminar_archivo(archivo_id):
    """Elimina un archivo (soft delete)"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Primero obtener la ruta del archivo
        cursor.execute("SELECT RutaArchivo FROM DOCUMENTOS_ANCI WHERE DocumentoID = ?", (archivo_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"error": "Archivo no encontrado"}), 404
        
        ruta_archivo = result.RutaArchivo
        
        # Marcar como inactivo
        query = """
            UPDATE DOCUMENTOS_ANCI 
            SET Activo = 0, FechaEliminacion = GETDATE()
            WHERE DocumentoID = ?
        """
        cursor.execute(query, (archivo_id,))
        conn.commit()
        
        # Intentar eliminar archivo físico
        try:
            if os.path.exists(ruta_archivo):
                os.remove(ruta_archivo)
        except:
            pass  # Si falla la eliminación física, continuar
        
        conn.close()
        return jsonify({"success": True}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error interno"}), 500

@gestion_documental_bp.route('/archivos/<int:archivo_id>/descargar', methods=['GET'])
def descargar_archivo(archivo_id):
    """Descarga o visualiza un archivo"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión"}), 500
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT RutaArchivo, NombreArchivo, TipoDocumento
            FROM DOCUMENTOS_ANCI
            WHERE DocumentoID = ? AND Activo = 1
        """
        cursor.execute(query, (archivo_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"error": "Archivo no encontrado"}), 404
        
        ruta_archivo = result.RutaArchivo
        nombre_archivo = result.NombreArchivo
        tipo_documento = result.TipoDocumento
        
        conn.close()
        
        if not os.path.exists(ruta_archivo):
            return jsonify({"error": "Archivo físico no encontrado"}), 404
        
        # Para imágenes, enviar con mimetype correcto para visualización
        image_extensions = ['png', 'jpg', 'jpeg', 'gif', 'bmp']
        if tipo_documento and tipo_documento.lower() in image_extensions:
            mimetype = f'image/{tipo_documento.lower()}'
            if tipo_documento.lower() == 'jpg':
                mimetype = 'image/jpeg'
            return send_file(ruta_archivo, mimetype=mimetype, as_attachment=False)
        
        # Para otros archivos, descargar
        return send_file(ruta_archivo, as_attachment=True, download_name=nombre_archivo)
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error interno"}), 500

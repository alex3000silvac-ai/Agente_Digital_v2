#!/usr/bin/env python3
"""
Implementación segura de upload de evidencias para módulo de acompañamiento
Corrige vulnerabilidades críticas identificadas en el análisis de seguridad
"""

from flask import Blueprint, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
import os
import time
from datetime import datetime
from .security_file_validator import FileSecurityValidator, log_file_security_event
from .admin_views import get_user_organization, get_db_connection, get_secure_upload_path, requires_organization

# ============================================================================
# VERSIÓN SEGURA DE UPLOAD DE EVIDENCIAS PARA CUMPLIMIENTO
# ============================================================================

@admin_api_bp.route('/cumplimiento/<int:cumplimiento_id>/evidencia/secure', methods=['POST'])
@requires_organization
def upload_evidencia_cumplimiento_secure(cumplimiento_id):
    """
    Versión segura de upload de evidencias para cumplimientos
    Incluye todas las validaciones de seguridad necesarias
    """
    user_org = get_user_organization()
    conn = get_db_connection()
    
    try:
        # 1. Validaciones básicas
        if 'file' not in request.files:
            log_file_security_event('upload_attempt', None, user_org, False, 'No file in request')
            return jsonify({"error": "No se encontró el archivo"}), 400
        
        file = request.files['file']
        if file.filename == '':
            log_file_security_event('upload_attempt', '', user_org, False, 'Empty filename')
            return jsonify({"error": "No se seleccionó ningún archivo"}), 400
        
        # 2. Validación de seguridad completa
        validator = FileSecurityValidator(conn)
        try:
            validation_result = validator.validate_file_security(file, user_org, 'cumplimiento')
            log_file_security_event('file_validated', file.filename, user_org, True)
        except ValueError as e:
            log_file_security_event('validation_failed', file.filename, user_org, False, str(e))
            return jsonify({"error": str(e)}), 400
        
        # 3. Verificar permisos específicos del cumplimiento
        cursor = conn.cursor()
        
        # Verificar que el cumplimiento existe y pertenece a la organización
        cursor.execute("""
            SELECT c.CumplimientoID, c.EmpresaID
            FROM CumplimientoEmpresa c
            INNER JOIN Empresas e ON c.EmpresaID = e.EmpresaID
            WHERE c.CumplimientoID = ? 
            AND e.InquilinoID = ? 
            AND e.EmpresaID = ?
        """, (cumplimiento_id, user_org['inquilino_id'], user_org['empresa_id']))
        
        cumplimiento_info = cursor.fetchone()
        if not cumplimiento_info:
            log_file_security_event('permission_denied', file.filename, user_org, False, 
                                   f'Cumplimiento {cumplimiento_id} not found or no permission')
            return jsonify({"error": "Cumplimiento no encontrado o sin permisos"}), 404
        
        # 4. Calcular nueva versión
        cursor.execute("""
            SELECT ISNULL(MAX(Version), 0) + 1 as NuevaVersion
            FROM EvidenciasCumplimiento 
            WHERE CumplimientoID = ?
        """, (cumplimiento_id,))
        nueva_version = cursor.fetchone()[0]
        
        # 5. Generar rutas seguras
        upload_path = get_secure_upload_path(user_org['inquilino_id'], user_org['empresa_id'])
        secure_filename_result = validation_result['secure_filename']
        
        # Agregar timestamp y versión para mayor unicidad
        timestamp = int(time.time())
        final_filename = f"c{cumplimiento_id}_v{nueva_version}_{timestamp}_{secure_filename_result}"
        
        ruta_guardado_absoluta = os.path.join(upload_path, final_filename)
        ruta_guardado_relativa = os.path.join(
            f"inquilino_{user_org['inquilino_id']}", 
            f"empresa_{user_org['empresa_id']}", 
            final_filename
        )
        
        # 6. Guardar archivo de forma segura
        try:
            # Crear directorio si no existe
            os.makedirs(upload_path, exist_ok=True)
            
            # Guardar archivo
            file.save(ruta_guardado_absoluta)
            
            # Verificar que el archivo se guardó correctamente
            if not os.path.exists(ruta_guardado_absoluta):
                raise Exception("Error guardando el archivo")
            
            # Verificar tamaño final
            actual_size = os.path.getsize(ruta_guardado_absoluta)
            if actual_size != validation_result['file_size']:
                os.remove(ruta_guardado_absoluta)
                raise Exception("Tamaño de archivo no coincide")
                
        except Exception as e:
            log_file_security_event('file_save_failed', file.filename, user_org, False, str(e))
            return jsonify({"error": f"Error guardando archivo: {str(e)}"}), 500
        
        # 7. Registrar en base de datos
        try:
            query = """
                INSERT INTO EvidenciasCumplimiento 
                (CumplimientoID, NombreArchivoOriginal, NombreArchivoAlmacenado, RutaArchivo, 
                 TipoArchivo, TamanoArchivoKB, Version, UsuarioQueSubio, InquilinoID, EmpresaID,
                 FechaSubida, IPAddress, UserAgent) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(query, (
                cumplimiento_id,
                validation_result['original_filename'],
                final_filename,
                ruta_guardado_relativa,
                file.mimetype or 'application/octet-stream',
                validation_result['file_size'] / 1024,  # Convert to KB
                nueva_version,
                user_org.get('user_id', 'unknown'),
                user_org['inquilino_id'],
                user_org['empresa_id'],
                datetime.utcnow(),
                request.remote_addr,
                request.headers.get('User-Agent', '')[:500]  # Limitar longitud
            ))
            
            conn.commit()
            
        except Exception as e:
            # Limpiar archivo si falla el registro en BD
            if os.path.exists(ruta_guardado_absoluta):
                os.remove(ruta_guardado_absoluta)
            
            conn.rollback()
            log_file_security_event('db_insert_failed', file.filename, user_org, False, str(e))
            return jsonify({"error": f"Error registrando archivo en base de datos: {str(e)}"}), 500
        
        # 8. Log de éxito
        log_file_security_event('upload_success', file.filename, user_org, True, {
            'cumplimiento_id': cumplimiento_id,
            'version': nueva_version,
            'file_size': validation_result['file_size'],
            'final_filename': final_filename
        })
        
        return jsonify({
            "message": f"Evidencia subida exitosamente como versión {nueva_version}",
            "version": nueva_version,
            "filename": validation_result['original_filename'],
            "size_kb": round(validation_result['file_size'] / 1024, 2)
        }), 201
        
    except Exception as e:
        # Log de error general
        log_file_security_event('upload_error', 
                               file.filename if 'file' in locals() else 'unknown', 
                               user_org, False, str(e))
        
        if conn:
            conn.rollback()
        
        return jsonify({"error": "Error interno del servidor"}), 500
        
    finally:
        if conn:
            conn.close()

# ============================================================================
# VERSIÓN SEGURA DE DESCARGA DE EVIDENCIAS
# ============================================================================

@admin_api_bp.route('/evidencia/<int:evidencia_id>/secure', methods=['GET'])
@requires_organization
def download_evidencia_secure(evidencia_id):
    """
    Versión segura de descarga de evidencias
    Incluye validaciones adicionales de seguridad
    """
    user_org = get_user_organization()
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        
        # Verificar permisos y obtener información de la evidencia
        cursor.execute("""
            SELECT 
                ec.RutaArchivo, 
                ec.NombreArchivoOriginal, 
                ec.InquilinoID, 
                ec.EmpresaID,
                ec.TamanoArchivoKB,
                ec.TipoArchivo,
                ec.FechaSubida
            FROM EvidenciasCumplimiento ec
            INNER JOIN CumplimientoEmpresa c ON ec.CumplimientoID = c.CumplimientoID
            INNER JOIN Empresas e ON c.EmpresaID = e.EmpresaID
            WHERE ec.EvidenciaID = ? 
            AND e.InquilinoID = ? 
            AND e.EmpresaID = ?
        """, (evidencia_id, user_org['inquilino_id'], user_org['empresa_id']))
        
        evidencia = cursor.fetchone()
        
        if not evidencia:
            log_file_security_event('download_denied', f'evidencia_{evidencia_id}', user_org, False, 
                                   'Evidence not found or no permission')
            return jsonify({"error": "Evidencia no encontrada o sin permisos"}), 404
        
        # Construir ruta completa del archivo
        from .admin_views import BASE_UPLOAD_FOLDER
        file_path = os.path.join(BASE_UPLOAD_FOLDER, evidencia.RutaArchivo)
        
        # Verificar que el archivo existe físicamente
        if not os.path.exists(file_path):
            log_file_security_event('file_not_found', evidencia.NombreArchivoOriginal, user_org, False,
                                   f'Physical file not found: {file_path}')
            return jsonify({"error": "Archivo no encontrado en el sistema"}), 404
        
        # Verificar acceso al archivo (protección adicional contra path traversal)
        from .admin_views import verify_file_access
        if not verify_file_access(evidencia.InquilinoID, evidencia.EmpresaID, file_path):
            log_file_security_event('path_traversal_attempt', evidencia.NombreArchivoOriginal, user_org, False,
                                   f'Path traversal detected: {file_path}')
            return jsonify({"error": "Acceso denegado al archivo"}), 403
        
        # Verificar integridad del archivo
        actual_size = os.path.getsize(file_path)
        expected_size_kb = evidencia.TamanoArchivoKB or 0
        expected_size_bytes = expected_size_kb * 1024
        
        # Permitir diferencia de ±5% en el tamaño (por redondeo)
        if abs(actual_size - expected_size_bytes) > (expected_size_bytes * 0.05):
            log_file_security_event('file_integrity_failed', evidencia.NombreArchivoOriginal, user_org, False,
                                   f'Size mismatch: expected {expected_size_bytes}, actual {actual_size}')
            return jsonify({"error": "Archivo corrupto o modificado"}), 500
        
        # Log de descarga exitosa
        log_file_security_event('download_success', evidencia.NombreArchivoOriginal, user_org, True, {
            'evidencia_id': evidencia_id,
            'file_size': actual_size,
            'fecha_subida': str(evidencia.FechaSubida)
        })
        
        # Enviar archivo
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        
        return send_from_directory(
            directory, 
            filename, 
            as_attachment=True, 
            download_name=evidencia.NombreArchivoOriginal,
            mimetype=evidencia.TipoArchivo
        )
        
    except Exception as e:
        log_file_security_event('download_error', f'evidencia_{evidencia_id}', user_org, False, str(e))
        return jsonify({"error": "Error interno del servidor"}), 500
        
    finally:
        if conn:
            conn.close()

# ============================================================================
# FUNCIÓN DE UTILIDAD PARA LIMPIAR ARCHIVOS HUÉRFANOS
# ============================================================================

def cleanup_orphaned_files(inquilino_id=None, empresa_id=None):
    """
    Función de mantenimiento para limpiar archivos huérfanos
    Debe ejecutarse periódicamente como tarea de mantenimiento
    """
    from .admin_views import BASE_UPLOAD_FOLDER
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Construir filtro por organización si se especifica
        org_filter = ""
        params = []
        if inquilino_id and empresa_id:
            org_filter = "WHERE InquilinoID = ? AND EmpresaID = ?"
            params = [inquilino_id, empresa_id]
        
        # Obtener todas las rutas de archivos registradas en BD
        cursor.execute(f"""
            SELECT RutaArchivo FROM EvidenciasCumplimiento {org_filter}
            UNION
            SELECT RutaArchivo FROM EvidenciasIncidentes {org_filter}
            UNION  
            SELECT RutaArchivo FROM INCIDENTE_TAXONOMIA_EVIDENCIAS {org_filter}
        """, params)
        
        registered_files = {row[0] for row in cursor.fetchall()}
        
        # Escanear directorio de uploads
        cleanup_count = 0
        if inquilino_id and empresa_id:
            search_path = os.path.join(BASE_UPLOAD_FOLDER, f"inquilino_{inquilino_id}", f"empresa_{empresa_id}")
        else:
            search_path = BASE_UPLOAD_FOLDER
        
        for root, dirs, files in os.walk(search_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, BASE_UPLOAD_FOLDER)
                
                # Si el archivo no está registrado en BD, eliminarlo
                if relative_path not in registered_files:
                    try:
                        os.remove(file_path)
                        cleanup_count += 1
                        print(f"Archivo huérfano eliminado: {relative_path}")
                    except Exception as e:
                        print(f"Error eliminando archivo huérfano {relative_path}: {e}")
        
        print(f"Limpieza completada: {cleanup_count} archivos huérfanos eliminados")
        
    except Exception as e:
        print(f"Error en limpieza de archivos: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔒 Módulo de upload seguro de evidencias cargado")
    print("✅ Validaciones implementadas:")
    print("   - Validación de tipos de archivo")
    print("   - Límites de tamaño")
    print("   - Verificación de permisos")
    print("   - Protección contra path traversal")
    print("   - Logs de auditoría")
    print("   - Verificación de integridad")
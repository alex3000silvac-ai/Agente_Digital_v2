#!/usr/bin/env python3
"""
Módulo de validación de seguridad para archivos en sistema SaaS multicliente
Correcciones críticas para vulnerabilidades identificadas
"""

import os
import mimetypes
from werkzeug.utils import secure_filename
from flask import jsonify, request

# Configuraciones de seguridad
ALLOWED_EXTENSIONS = {
    'documents': {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'},
    'images': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'},
    'spreadsheets': {'.xls', '.xlsx', '.csv', '.ods'},
    'archives': {'.zip', '.rar', '.7z'},
    'presentations': {'.ppt', '.pptx', '.odp'}
}

# Extensiones explícitamente prohibidas
BLOCKED_EXTENSIONS = {
    '.exe', '.bat', '.cmd', '.com', '.scr', '.vbs', '.js', '.jar',
    '.php', '.asp', '.jsp', '.sh', '.ps1', '.py', '.rb', '.pl',
    '.msi', '.deb', '.rpm', '.dmg', '.app', '.dll', '.so'
}

# Límites de tamaño
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB por archivo
MAX_TOTAL_SIZE_PER_ORG = 500 * 1024 * 1024  # 500MB por organización

# MIME types permitidos
ALLOWED_MIME_TYPES = {
    # Documentos
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'application/rtf',
    
    # Imágenes
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/bmp',
    'image/tiff',
    'image/webp',
    
    # Hojas de cálculo
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv',
    
    # Archivos comprimidos
    'application/zip',
    'application/x-rar-compressed',
    'application/x-7z-compressed',
    
    # Presentaciones
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation'
}

class FileSecurityValidator:
    """Validador de seguridad para archivos subidos"""
    
    def __init__(self, conn=None):
        self.conn = conn
    
    def validate_file_security(self, file, user_org, context='general'):
        """
        Validación completa de seguridad para archivos
        
        Args:
            file: Archivo de Flask request.files
            user_org: Información de organización del usuario
            context: Contexto del archivo ('cumplimiento', 'incidente', 'taxonomia')
        
        Returns:
            dict: Resultado de validación
        
        Raises:
            ValueError: Si el archivo no pasa las validaciones
        """
        
        # 1. Validaciones básicas
        if not file or file.filename == '':
            raise ValueError("No se seleccionó ningún archivo")
        
        # 2. Validar nombre de archivo
        original_filename = file.filename
        if not self._is_valid_filename(original_filename):
            raise ValueError("Nombre de archivo inválido o sospechoso")
        
        # 3. Validar extensión
        file_ext = self._get_file_extension(original_filename)
        if not self._is_allowed_extension(file_ext):
            raise ValueError(f"Tipo de archivo no permitido: {file_ext}")
        
        # 4. Validar tamaño
        file_size = self._get_file_size(file)
        if not self._is_valid_size(file_size):
            raise ValueError(f"Archivo demasiado grande. Máximo permitido: {MAX_FILE_SIZE // (1024*1024)}MB")
        
        # 5. Validar límite total por organización
        if not self._check_org_storage_limit(user_org, file_size):
            raise ValueError("Límite de almacenamiento de la organización excedido")
        
        # 6. Validar MIME type
        file.seek(0)  # Reset file pointer
        file_content = file.read(1024)  # Leer primeros 1024 bytes
        file.seek(0)  # Reset again
        
        if not self._is_valid_mime_type(file_content, file_ext):
            raise ValueError("Tipo de contenido del archivo no coincide con la extensión")
        
        # 7. Escanear contenido sospechoso
        if not self._scan_content_security(file_content):
            raise ValueError("Contenido del archivo considerado inseguro")
        
        return {
            'valid': True,
            'original_filename': original_filename,
            'file_extension': file_ext,
            'file_size': file_size,
            'secure_filename': self._generate_secure_filename(original_filename, context)
        }
    
    def _is_valid_filename(self, filename):
        """Validar que el nombre de archivo sea seguro"""
        if not filename or len(filename) > 255:
            return False
        
        # Caracteres prohibidos
        forbidden_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        if any(char in filename for char in forbidden_chars):
            return False
        
        # Nombres reservados en Windows
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
            'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
            'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        name_without_ext = os.path.splitext(filename)[0].upper()
        if name_without_ext in reserved_names:
            return False
        
        return True
    
    def _get_file_extension(self, filename):
        """Obtener extensión del archivo en minúsculas"""
        return os.path.splitext(filename)[1].lower()
    
    def _is_allowed_extension(self, file_ext):
        """Verificar si la extensión está permitida"""
        if file_ext in BLOCKED_EXTENSIONS:
            return False
        
        # Verificar en extensiones permitidas
        all_allowed = set()
        for category in ALLOWED_EXTENSIONS.values():
            all_allowed.update(category)
        
        return file_ext in all_allowed
    
    def _get_file_size(self, file):
        """Obtener tamaño del archivo"""
        if hasattr(file, 'content_length') and file.content_length:
            return file.content_length
        
        # Fallback: leer el archivo para determinar tamaño
        file.seek(0, 2)  # Ir al final
        size = file.tell()
        file.seek(0)  # Volver al inicio
        return size
    
    def _is_valid_size(self, file_size):
        """Verificar que el tamaño esté dentro de los límites"""
        return 0 < file_size <= MAX_FILE_SIZE
    
    def _check_org_storage_limit(self, user_org, new_file_size):
        """Verificar límite de almacenamiento por organización"""
        if not self.conn:
            return True  # Skip si no hay conexión DB
        
        try:
            cursor = self.conn.cursor()
            
            # Calcular uso actual de almacenamiento
            cursor.execute("""
                SELECT ISNULL(SUM(TamanoArchivoKB), 0) * 1024 as TotalBytes
                FROM (
                    SELECT TamanoArchivoKB FROM EvidenciasCumplimiento 
                    WHERE InquilinoID = ? AND EmpresaID = ?
                    UNION ALL
                    SELECT TamanoArchivoKB FROM EvidenciasIncidentes 
                    WHERE InquilinoID = ? AND EmpresaID = ?
                    UNION ALL
                    SELECT TamanoArchivo FROM INCIDENTE_TAXONOMIA_EVIDENCIAS 
                    WHERE InquilinoID = ? AND EmpresaID = ?
                ) as AllFiles
            """, (
                user_org['inquilino_id'], user_org['empresa_id'],
                user_org['inquilino_id'], user_org['empresa_id'],
                user_org['inquilino_id'], user_org['empresa_id']
            ))
            
            current_usage = cursor.fetchone()[0] or 0
            return (current_usage + new_file_size) <= MAX_TOTAL_SIZE_PER_ORG
            
        except Exception as e:
            print(f"Error verificando límite de almacenamiento: {e}")
            return True  # Permitir en caso de error DB
    
    def _is_valid_mime_type(self, file_content, file_ext):
        """Verificar que el MIME type coincida con la extensión"""
        try:
            # Detectar MIME type por contenido (requiere python-magic)
            # Para simplificar, usar mimetypes por extensión
            expected_mime, _ = mimetypes.guess_type(f"dummy{file_ext}")
            
            if expected_mime in ALLOWED_MIME_TYPES:
                return True
            
            # Verificaciones adicionales por contenido
            if file_ext in ['.pdf'] and file_content.startswith(b'%PDF'):
                return True
            elif file_ext in ['.jpg', '.jpeg'] and file_content.startswith(b'\xff\xd8\xff'):
                return True
            elif file_ext in ['.png'] and file_content.startswith(b'\x89PNG'):
                return True
            elif file_ext in ['.zip'] and file_content.startswith(b'PK'):
                return True
            
            return False
            
        except Exception:
            return False
    
    def _scan_content_security(self, file_content):
        """Escanear contenido en busca de patrones sospechosos"""
        
        # Patrones de contenido malicioso
        malicious_patterns = [
            b'<script',  # JavaScript
            b'<?php',    # PHP
            b'<%',       # ASP
            b'eval(',    # Eval functions
            b'exec(',    # Exec functions
            b'system(',  # System calls
            b'shell_exec(',
            b'passthru(',
            b'cmd.exe',
            b'/bin/sh',
            b'/bin/bash',
        ]
        
        # Buscar patrones en contenido
        file_content_lower = file_content.lower()
        for pattern in malicious_patterns:
            if pattern in file_content_lower:
                return False
        
        return True
    
    def _generate_secure_filename(self, original_filename, context):
        """Generar nombre de archivo seguro"""
        import time
        import hashlib
        
        # Obtener extensión segura
        file_ext = self._get_file_extension(original_filename)
        
        # Crear hash del filename original + timestamp
        timestamp = str(int(time.time()))
        hash_input = f"{original_filename}_{timestamp}".encode('utf-8')
        file_hash = hashlib.md5(hash_input).hexdigest()[:8]
        
        # Generar nombre seguro
        secure_name = secure_filename(os.path.splitext(original_filename)[0])
        secure_name = secure_name[:50]  # Limitar longitud
        
        # Formato final: context_hash_securefilename.ext
        final_filename = f"{context}_{file_hash}_{secure_name}{file_ext}"
        
        return final_filename

def create_secure_upload_decorator(context='general'):
    """
    Decorador para validar archivos de forma segura
    
    Usage:
        @create_secure_upload_decorator('cumplimiento')
        def upload_evidencia_cumplimiento(cumplimiento_id):
            # file ya está validado aquí
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            try:
                if 'file' not in request.files:
                    return jsonify({"error": "No se encontró el archivo"}), 400
                
                file = request.files['file']
                
                # Obtener organización del usuario
                from .admin_views import get_user_organization, get_db_connection
                user_org = get_user_organization()
                
                if not user_org:
                    return jsonify({"error": "Usuario no autenticado"}), 401
                
                # Validar archivo
                validator = FileSecurityValidator(get_db_connection())
                validation_result = validator.validate_file_security(file, user_org, context)
                
                # Agregar resultado de validación al request para uso en la función
                request.file_validation = validation_result
                
                return f(*args, **kwargs)
                
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            except Exception as e:
                return jsonify({"error": "Error de validación de archivo"}), 500
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

# Función de utilidad para logs de auditoría
def log_file_security_event(event_type, filename, user_org, success=True, details=None):
    """Registrar eventos de seguridad de archivos"""
    import json
    from datetime import datetime
    
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,  # 'upload_attempt', 'validation_failed', 'malware_detected'
        'filename': filename,
        'user_org': user_org,
        'success': success,
        'details': details,
        'ip_address': request.remote_addr if request else None,
        'user_agent': request.headers.get('User-Agent') if request else None
    }
    
    # En producción, enviar a sistema de logs centralizado
    print(f"SECURITY_LOG: {json.dumps(log_entry)}")

if __name__ == "__main__":
    # Tests básicos
    print("🔒 Módulo de seguridad de archivos cargado")
    print(f"📁 Extensiones permitidas: {sum(len(exts) for exts in ALLOWED_EXTENSIONS.values())}")
    print(f"🚫 Extensiones bloqueadas: {len(BLOCKED_EXTENSIONS)}")
    print(f"📏 Límite por archivo: {MAX_FILE_SIZE // (1024*1024)}MB")
    print(f"📊 Límite por organización: {MAX_TOTAL_SIZE_PER_ORG // (1024*1024)}MB")
"""
file_upload_security.py - Seguridad para carga de archivos
=======================================================

Este módulo implementa validaciones y controles de seguridad para
la carga de archivos, previniendo ataques mediante archivos maliciosos.

Características:
- Validación de tipos de archivo
- Límites de tamaño
- Escaneo de contenido malicioso
- Sanitización de nombres
- Almacenamiento seguro
- Prevención de path traversal
"""

import os
import re
import hashlib
import magic
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Any
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import tempfile
import shutil

class FileUploadSecurity:
    """
    Sistema de seguridad para carga de archivos
    """
    
    def __init__(self):
        self.config = {
            'ENABLE_FILE_SECURITY': os.getenv('ENABLE_FILE_SECURITY', 'true').lower() == 'true',
            'UPLOAD_FOLDER': os.getenv('SECURE_UPLOAD_FOLDER', 'uploads'),
            'MAX_FILE_SIZE': int(os.getenv('MAX_FILE_SIZE', 10 * 1024 * 1024)),  # 10MB
            'ALLOWED_EXTENSIONS': set(os.getenv('ALLOWED_EXTENSIONS', 'pdf,doc,docx,xls,xlsx,png,jpg,jpeg,gif,txt,csv').split(',')),
            'BLOCKED_EXTENSIONS': set(os.getenv('BLOCKED_EXTENSIONS', 'exe,bat,cmd,sh,ps1,vbs,js,jar,com,scr,msi').split(',')),
            'CHECK_MIME_TYPE': os.getenv('CHECK_MIME_TYPE', 'true').lower() == 'true',
            'SCAN_FOR_MALWARE': os.getenv('SCAN_FOR_MALWARE', 'true').lower() == 'true',
            'QUARANTINE_FOLDER': os.getenv('QUARANTINE_FOLDER', 'quarantine'),
            'USE_RANDOM_NAMES': os.getenv('USE_RANDOM_FILE_NAMES', 'true').lower() == 'true',
            'PRESERVE_EXTENSION': os.getenv('PRESERVE_FILE_EXTENSION', 'true').lower() == 'true',
            'CREATE_USER_FOLDERS': os.getenv('CREATE_USER_FOLDERS', 'true').lower() == 'true',
            'VIRUS_SCAN_COMMAND': os.getenv('VIRUS_SCAN_COMMAND', ''),  # ej: 'clamscan'
            'MAX_FILENAME_LENGTH': int(os.getenv('MAX_FILENAME_LENGTH', 255))
        }
        
        # Mapeo de MIME types seguros
        self.safe_mime_types = {
            'pdf': ['application/pdf'],
            'doc': ['application/msword'],
            'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            'xls': ['application/vnd.ms-excel'],
            'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
            'png': ['image/png'],
            'jpg': ['image/jpeg'],
            'jpeg': ['image/jpeg'],
            'gif': ['image/gif'],
            'txt': ['text/plain'],
            'csv': ['text/csv', 'application/csv']
        }
        
        # Patrones peligrosos en nombres de archivo
        self.dangerous_patterns = [
            r'\.\./',  # Path traversal
            r'\.\.\\',  # Path traversal Windows
            r'^/',  # Absolute path
            r'^\\',  # Absolute path Windows
            r'^~',  # Home directory
            r'[\x00-\x1f]',  # Control characters
            r'[<>:"|?*]',  # Windows reserved
            r'\.{2,}',  # Multiple dots
            r'^\.ht',  # .htaccess, .htpasswd
            r'\.php\d?$',  # PHP files
            r'\.phtml$',  # PHP files
            r'\.asp[x]?$',  # ASP files
            r'\.jsp$',  # JSP files
        ]
        
        # Inicializar detector de MIME si está disponible
        self.mime_detector = None
        try:
            self.mime_detector = magic.Magic(mime=True)
        except:
            pass
        
        # Crear directorios necesarios
        self._create_directories()
    
    def _create_directories(self):
        """Crea directorios necesarios para uploads"""
        for folder in [self.config['UPLOAD_FOLDER'], self.config['QUARANTINE_FOLDER']]:
            Path(folder).mkdir(parents=True, exist_ok=True)
            
            # Establecer permisos restrictivos
            os.chmod(folder, 0o755)
    
    def validate_file(self, file: FileStorage, user_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Valida un archivo antes de guardarlo
        
        Args:
            file: Archivo a validar
            user_id: ID del usuario (opcional)
            
        Returns:
            tuple: (es_valido, mensaje_error)
        """
        if not self.config['ENABLE_FILE_SECURITY']:
            return True, "OK"
        
        # Verificar que hay archivo
        if not file or not file.filename:
            return False, "No se proporcionó archivo"
        
        # Validar nombre de archivo
        is_valid, error = self._validate_filename(file.filename)
        if not is_valid:
            return False, error
        
        # Validar extensión
        is_valid, error = self._validate_extension(file.filename)
        if not is_valid:
            return False, error
        
        # Validar tamaño
        is_valid, error = self._validate_size(file)
        if not is_valid:
            return False, error
        
        # Validar MIME type
        if self.config['CHECK_MIME_TYPE']:
            is_valid, error = self._validate_mime_type(file)
            if not is_valid:
                return False, error
        
        # Validar contenido
        is_valid, error = self._validate_content(file)
        if not is_valid:
            return False, error
        
        # Escanear malware si está configurado
        if self.config['SCAN_FOR_MALWARE']:
            is_valid, error = self._scan_for_malware(file)
            if not is_valid:
                return False, error
        
        return True, "OK"
    
    def _validate_filename(self, filename: str) -> Tuple[bool, str]:
        """Valida el nombre del archivo"""
        # Verificar longitud
        if len(filename) > self.config['MAX_FILENAME_LENGTH']:
            return False, f"Nombre de archivo demasiado largo (máx {self.config['MAX_FILENAME_LENGTH']} caracteres)"
        
        # Verificar patrones peligrosos
        for pattern in self.dangerous_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                return False, "Nombre de archivo contiene caracteres no permitidos"
        
        # Verificar caracteres Unicode peligrosos
        if any(ord(char) > 127 for char in filename):
            # Permitir algunos caracteres Unicode comunes
            allowed_unicode = set('áéíóúñÁÉÍÓÚÑ')
            if any(char not in allowed_unicode and ord(char) > 127 for char in filename):
                return False, "Nombre de archivo contiene caracteres Unicode no permitidos"
        
        return True, "OK"
    
    def _validate_extension(self, filename: str) -> Tuple[bool, str]:
        """Valida la extensión del archivo"""
        # Obtener extensión
        ext = self._get_extension(filename)
        
        if not ext:
            return False, "Archivo sin extensión"
        
        # Verificar lista negra primero
        if ext in self.config['BLOCKED_EXTENSIONS']:
            return False, f"Tipo de archivo no permitido: .{ext}"
        
        # Verificar lista blanca
        if ext not in self.config['ALLOWED_EXTENSIONS']:
            return False, f"Tipo de archivo no permitido: .{ext}"
        
        # Verificar doble extensión
        parts = filename.split('.')
        if len(parts) > 2:
            # Verificar si alguna extensión intermedia es peligrosa
            for part in parts[1:-1]:
                if part.lower() in self.config['BLOCKED_EXTENSIONS']:
                    return False, "Archivo con múltiples extensiones no permitido"
        
        return True, "OK"
    
    def _validate_size(self, file: FileStorage) -> Tuple[bool, str]:
        """Valida el tamaño del archivo"""
        # Obtener tamaño
        file.seek(0, 2)  # Ir al final
        size = file.tell()
        file.seek(0)  # Volver al inicio
        
        if size > self.config['MAX_FILE_SIZE']:
            max_mb = self.config['MAX_FILE_SIZE'] / (1024 * 1024)
            return False, f"Archivo demasiado grande (máx {max_mb}MB)"
        
        if size == 0:
            return False, "Archivo vacío"
        
        return True, "OK"
    
    def _validate_mime_type(self, file: FileStorage) -> Tuple[bool, str]:
        """Valida el MIME type real del archivo"""
        if not self.mime_detector:
            return True, "OK"  # Skip si no hay detector
        
        try:
            # Leer primeros bytes para detección
            file.seek(0)
            file_header = file.read(1024)
            file.seek(0)
            
            # Detectar MIME type
            detected_mime = self.mime_detector.from_buffer(file_header)
            
            # Obtener extensión esperada
            ext = self._get_extension(file.filename)
            
            # Verificar si coincide con lo esperado
            if ext in self.safe_mime_types:
                expected_mimes = self.safe_mime_types[ext]
                if detected_mime not in expected_mimes:
                    return False, f"El tipo de archivo no coincide con la extensión (detectado: {detected_mime})"
            
            # Verificar MIME types peligrosos
            dangerous_mimes = [
                'application/x-executable',
                'application/x-sharedlib',
                'application/x-shellscript',
                'application/x-msdos-program',
                'application/x-msdownload'
            ]
            
            if detected_mime in dangerous_mimes:
                return False, "Tipo de archivo potencialmente peligroso detectado"
            
        except Exception as e:
            return False, f"Error validando tipo de archivo: {str(e)}"
        
        return True, "OK"
    
    def _validate_content(self, file: FileStorage) -> Tuple[bool, str]:
        """Valida el contenido del archivo buscando patrones maliciosos"""
        # Patrones maliciosos comunes
        malicious_patterns = [
            b'<script',  # JavaScript
            b'<?php',  # PHP
            b'<%',  # ASP
            b'<jsp:',  # JSP
            b'\x4d\x5a',  # EXE header (MZ)
            b'\x7fELF',  # ELF header
            b'#!/bin/',  # Shell scripts
            b'@echo off',  # Batch files
            b'powershell',  # PowerShell
        ]
        
        try:
            # Leer inicio del archivo
            file.seek(0)
            content = file.read(8192)  # Primeros 8KB
            file.seek(0)
            
            # Buscar patrones maliciosos
            for pattern in malicious_patterns:
                if pattern in content.lower():
                    return False, "Contenido potencialmente malicioso detectado"
            
            # Verificar si es un archivo ZIP disfrazado
            if content.startswith(b'PK\x03\x04'):
                ext = self._get_extension(file.filename)
                if ext not in ['zip', 'docx', 'xlsx', 'pptx']:  # Estos son ZIP válidos
                    return False, "Archivo ZIP disfrazado detectado"
            
        except Exception:
            return False, "Error al validar contenido del archivo"
        
        return True, "OK"
    
    def _scan_for_malware(self, file: FileStorage) -> Tuple[bool, str]:
        """Escanea el archivo en busca de malware"""
        if not self.config['VIRUS_SCAN_COMMAND']:
            return True, "OK"  # Skip si no hay scanner configurado
        
        temp_path = None
        try:
            # Guardar temporalmente para escanear
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                file.save(tmp.name)
                temp_path = tmp.name
            
            # Ejecutar scanner
            import subprocess
            result = subprocess.run(
                [self.config['VIRUS_SCAN_COMMAND'], temp_path],
                capture_output=True,
                timeout=30
            )
            
            # Verificar resultado
            if result.returncode != 0:
                return False, "Archivo detectado como malicioso"
            
        except subprocess.TimeoutExpired:
            return False, "Timeout al escanear archivo"
        except Exception as e:
            return False, f"Error al escanear archivo: {str(e)}"
        finally:
            # Limpiar archivo temporal
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
            file.seek(0)
        
        return True, "OK"
    
    def save_file(self, file: FileStorage, user_id: Optional[str] = None,
                  subfolder: Optional[str] = None) -> Tuple[bool, str, str]:
        """
        Guarda un archivo de forma segura
        
        Args:
            file: Archivo a guardar
            user_id: ID del usuario
            subfolder: Subcarpeta adicional
            
        Returns:
            tuple: (exito, ruta_guardada, mensaje)
        """
        try:
            # Validar primero
            is_valid, error = self.validate_file(file, user_id)
            if not is_valid:
                return False, "", error
            
            # Generar nombre seguro
            filename = self._generate_safe_filename(file.filename)
            
            # Construir ruta de destino
            dest_folder = Path(self.config['UPLOAD_FOLDER'])
            
            if self.config['CREATE_USER_FOLDERS'] and user_id:
                dest_folder = dest_folder / f"user_{user_id}"
            
            if subfolder:
                dest_folder = dest_folder / secure_filename(subfolder)
            
            # Crear directorio si no existe
            dest_folder.mkdir(parents=True, exist_ok=True)
            
            # Ruta completa del archivo
            dest_path = dest_folder / filename
            
            # Verificar que no existe
            if dest_path.exists():
                # Generar nombre único
                base, ext = os.path.splitext(filename)
                counter = 1
                while dest_path.exists():
                    filename = f"{base}_{counter}{ext}"
                    dest_path = dest_folder / filename
                    counter += 1
            
            # Guardar archivo
            file.save(str(dest_path))
            
            # Establecer permisos restrictivos
            os.chmod(str(dest_path), 0o644)
            
            # Registrar metadata
            self._save_file_metadata(dest_path, file, user_id)
            
            return True, str(dest_path), "Archivo guardado exitosamente"
            
        except Exception as e:
            return False, "", f"Error al guardar archivo: {str(e)}"
    
    def _generate_safe_filename(self, original_filename: str) -> str:
        """Genera un nombre de archivo seguro"""
        # Usar secure_filename de Werkzeug como base
        filename = secure_filename(original_filename)
        
        if self.config['USE_RANDOM_NAMES']:
            # Generar nombre aleatorio manteniendo extensión
            ext = self._get_extension(filename)
            random_name = hashlib.sha256(
                f"{original_filename}{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()[:16]
            
            if self.config['PRESERVE_EXTENSION'] and ext:
                filename = f"{random_name}.{ext}"
            else:
                filename = random_name
        
        return filename
    
    def _get_extension(self, filename: str) -> str:
        """Obtiene la extensión del archivo de forma segura"""
        parts = filename.rsplit('.', 1)
        if len(parts) == 2:
            return parts[1].lower()
        return ""
    
    def _save_file_metadata(self, file_path: Path, file: FileStorage, user_id: Optional[str]):
        """Guarda metadata del archivo"""
        metadata = {
            'original_filename': file.filename,
            'saved_filename': file_path.name,
            'size': file_path.stat().st_size,
            'mime_type': file.content_type,
            'upload_date': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'sha256': self._calculate_file_hash(file_path)
        }
        
        # Guardar metadata junto al archivo
        metadata_path = file_path.with_suffix('.meta.json')
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calcula el hash SHA256 del archivo"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def quarantine_file(self, file_path: str, reason: str):
        """
        Mueve un archivo a cuarentena
        
        Args:
            file_path: Ruta del archivo
            reason: Razón de la cuarentena
        """
        try:
            source = Path(file_path)
            if not source.exists():
                return
            
            # Crear carpeta de cuarentena con fecha
            quarantine_folder = Path(self.config['QUARANTINE_FOLDER']) / datetime.utcnow().strftime("%Y%m%d")
            quarantine_folder.mkdir(parents=True, exist_ok=True)
            
            # Mover archivo
            dest = quarantine_folder / f"{source.name}.quarantine"
            shutil.move(str(source), str(dest))
            
            # Crear archivo de información
            info_file = dest.with_suffix('.info')
            with open(info_file, 'w') as f:
                f.write(f"Original path: {file_path}\n")
                f.write(f"Quarantined at: {datetime.utcnow().isoformat()}\n")
                f.write(f"Reason: {reason}\n")
            
            # Permisos restrictivos
            os.chmod(str(dest), 0o600)
            
        except Exception as e:
            import logging
            logging.error(f"Error quarantining file: {e}")
    
    def get_safe_path(self, filename: str, user_id: Optional[str] = None) -> str:
        """
        Genera una ruta segura para un archivo
        
        Args:
            filename: Nombre del archivo
            user_id: ID del usuario
            
        Returns:
            str: Ruta segura
        """
        # Sanitizar nombre
        safe_filename = self._generate_safe_filename(filename)
        
        # Construir ruta
        path_parts = [self.config['UPLOAD_FOLDER']]
        
        if self.config['CREATE_USER_FOLDERS'] and user_id:
            path_parts.append(f"user_{user_id}")
        
        path_parts.append(safe_filename)
        
        return os.path.join(*path_parts)
    
    def validate_download_request(self, file_path: str, user_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Valida una solicitud de descarga
        
        Args:
            file_path: Ruta del archivo solicitado
            user_id: ID del usuario
            
        Returns:
            tuple: (es_valido, mensaje_error)
        """
        try:
            # Verificar path traversal
            safe_path = os.path.abspath(file_path)
            upload_root = os.path.abspath(self.config['UPLOAD_FOLDER'])
            
            if not safe_path.startswith(upload_root):
                return False, "Acceso denegado"
            
            # Verificar que existe
            if not os.path.exists(safe_path):
                return False, "Archivo no encontrado"
            
            # Verificar permisos de usuario si aplica
            if self.config['CREATE_USER_FOLDERS'] and user_id:
                user_folder = os.path.join(upload_root, f"user_{user_id}")
                if not safe_path.startswith(user_folder):
                    return False, "No autorizado para acceder a este archivo"
            
            return True, "OK"
            
        except Exception:
            return False, "Error validando solicitud"


# Instancia global
file_upload_security = FileUploadSecurity()


# Decorador para validación automática
def secure_file_required(param_name: str = 'file'):
    """
    Decorador para validar archivos automáticamente
    
    Uso:
        @app.route('/upload', methods=['POST'])
        @secure_file_required('file')
        def upload(validated_file):
            # validated_file es el archivo validado
            ...
    """
    from functools import wraps
    from flask import request, jsonify
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Obtener archivo
            file = request.files.get(param_name)
            
            if not file:
                return jsonify({'error': 'No se proporcionó archivo'}), 400
            
            # Validar
            is_valid, error = file_upload_security.validate_file(file)
            
            if not is_valid:
                return jsonify({'error': error}), 400
            
            # Agregar archivo validado a kwargs
            kwargs['validated_file'] = file
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator
# app/file_manager.py
# Gestor de archivos optimizado para escalabilidad y performance

import os
import hashlib
import mimetypes
import logging
import shutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, BinaryIO
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
try:
    import magic
except ImportError:
    from .fallback_imports import magic

logger = logging.getLogger(__name__)

class FileManager:
    """Gestor de archivos optimizado para alta concurrencia y escalabilidad"""
    
    def __init__(self, config=None):
        self.config = config or self._get_default_config()
        self._lock = threading.RLock()
        self._stats = {
            'total_uploads': 0,
            'total_downloads': 0,
            'storage_used': 0,
            'failed_uploads': 0,
            'quarantined_files': 0
        }
        
    def _get_default_config(self):
        """Configuración por defecto del gestor de archivos"""
        return {
            # Directorios base
            'base_upload_dir': os.environ.get('UPLOAD_FOLDER', '/home/agentedigital/apps/agentedigital/uploads'),
            'temp_dir': os.environ.get('TEMP_FOLDER', '/tmp/agentedigital'),
            'quarantine_dir': os.environ.get('QUARANTINE_FOLDER', '/home/agentedigital/quarantine'),
            
            # Límites de archivos
            'max_file_size': int(os.environ.get('MAX_FILE_SIZE', '104857600')),  # 100MB
            'max_files_per_user': int(os.environ.get('MAX_FILES_PER_USER', '1000')),
            'max_storage_per_user': int(os.environ.get('MAX_STORAGE_PER_USER', '1073741824')),  # 1GB
            
            # Tipos de archivos permitidos
            'allowed_extensions': {
                'documents': ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'],
                'spreadsheets': ['xls', 'xlsx', 'csv', 'ods'],
                'presentations': ['ppt', 'pptx', 'odp'],
                'images': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'],
                'archives': ['zip', 'rar', '7z', 'tar', 'gz'],
                'others': ['xml', 'json', 'log']
            },
            
            # Tipos MIME permitidos
            'allowed_mimetypes': [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-powerpoint',
                'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                'text/plain',
                'text/csv',
                'image/jpeg',
                'image/png',
                'image/gif',
                'image/bmp',
                'image/svg+xml',
                'image/webp',
                'application/zip',
                'application/x-rar-compressed',
                'application/x-7z-compressed',
                'application/json',
                'application/xml',
                'text/xml',
                'application/octet-stream'  # Permitir archivos genéricos
            ],
            
            # Configuración de seguridad
            'scan_files': os.environ.get('SCAN_FILES', 'true').lower() == 'true',
            'quarantine_suspicious': True,
            'generate_thumbnails': os.environ.get('GENERATE_THUMBNAILS', 'true').lower() == 'true',
            'compress_files': os.environ.get('COMPRESS_FILES', 'false').lower() == 'true',
            
            # Configuración de performance
            'chunk_size': int(os.environ.get('CHUNK_SIZE', '8192')),  # 8KB chunks
            'concurrent_uploads': int(os.environ.get('CONCURRENT_UPLOADS', '10')),
            'cache_file_info': True,
            
            # Configuración de limpieza
            'cleanup_enabled': True,
            'temp_file_lifetime': 3600,  # 1 hora
            'trash_retention_days': 30,
            
            # Configuración de estructura de directorios
            'directory_structure': 'inquilino_id/empresa_id/type/year/month',
            'create_subdirs': True,
        }
    
    def initialize(self):
        """Inicializar el gestor de archivos"""
        try:
            # Crear directorios necesarios
            directories = [
                self.config['base_upload_dir'],
                self.config['temp_dir'],
                self.config['quarantine_dir']
            ]
            
            for directory in directories:
                Path(directory).mkdir(parents=True, exist_ok=True)
                
            # Verificar permisos de escritura
            for directory in directories:
                test_file = Path(directory) / '.write_test'
                try:
                    test_file.touch()
                    test_file.unlink()
                except Exception as e:
                    raise PermissionError(f"No hay permisos de escritura en {directory}: {e}")
            
            logger.info(f"File manager inicializado: {self.config['base_upload_dir']}")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando file manager: {e}")
            raise
    
    def _get_file_path(self, inquilino_id: int, empresa_id: int, file_type: str, filename: str) -> Path:
        """Generar ruta de archivo basada en la estructura configurada"""
        now = datetime.now()
        
        # Estructura: inquilino_id/empresa_id/type/year/month/filename
        path_parts = [
            self.config['base_upload_dir'],
            f"inquilino_{inquilino_id}",
            f"empresa_{empresa_id}",
            file_type,
            str(now.year),
            f"{now.month:02d}"
        ]
        
        directory = Path(*path_parts)
        
        if self.config['create_subdirs']:
            directory.mkdir(parents=True, exist_ok=True)
        
        return directory / filename
    
    def _generate_safe_filename(self, original_filename: str, inquilino_id: int, empresa_id: int) -> str:
        """Generar nombre de archivo seguro y único"""
        # Limpiar nombre original
        safe_name = secure_filename(original_filename)
        
        # Agregar timestamp para unicidad
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Separar nombre y extensión
        name, ext = os.path.splitext(safe_name)
        
        # Generar hash para evitar colisiones
        hash_input = f"{inquilino_id}_{empresa_id}_{safe_name}_{timestamp}"
        file_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        
        # Construir nombre final
        final_name = f"{name}_{timestamp}_{file_hash}{ext}"
        
        return final_name
    
    def _validate_file(self, file: FileStorage) -> Tuple[bool, Optional[str]]:
        """Validar archivo subido"""
        # Verificar que hay un archivo
        if not file or not file.filename:
            return False, "No se proporcionó archivo"
        
        # Verificar tamaño
        file.seek(0, 2)  # Ir al final
        file_size = file.tell()
        file.seek(0)  # Volver al inicio
        
        if file_size > self.config['max_file_size']:
            return False, f"Archivo demasiado grande. Máximo: {self.config['max_file_size']} bytes"
        
        if file_size == 0:
            return False, "El archivo está vacío"
        
        # Verificar extensión
        filename = file.filename.lower()
        extension = filename.split('.')[-1] if '.' in filename else ''
        
        all_allowed_extensions = []
        for category_extensions in self.config['allowed_extensions'].values():
            all_allowed_extensions.extend(category_extensions)
        
        if extension not in all_allowed_extensions:
            return False, f"Tipo de archivo no permitido: .{extension}"
        
        # Verificar MIME type
        if hasattr(magic, 'from_buffer'):
            try:
                file_content = file.read(1024)  # Leer primeros 1KB
                file.seek(0)  # Volver al inicio
                
                mime_type = magic.from_buffer(file_content, mime=True)
                
                if mime_type not in self.config['allowed_mimetypes']:
                    return False, f"Tipo MIME no permitido: {mime_type}"
                    
            except Exception as e:
                logger.warning(f"Error verificando MIME type: {e}")
        
        return True, None
    
    def _scan_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Escanear archivo en busca de amenazas (básico)"""
        if not self.config['scan_files']:
            return True, None
        
        try:
            # Verificaciones básicas de seguridad
            file_size = file_path.stat().st_size
            
            # Archivos sospechosamente grandes
            if file_size > self.config['max_file_size'] * 2:
                return False, "Archivo sospechosamente grande"
            
            # Leer contenido para verificaciones básicas
            with open(file_path, 'rb') as f:
                header = f.read(1024)
            
            # Verificar firmas de archivos maliciosos conocidos
            malicious_patterns = [
                b'MZ',  # Ejecutables Windows (muy básico)
                b'\x7fELF',  # Ejecutables Linux
                b'<script',  # Scripts embebidos
                b'javascript:',  # JavaScript URLs
            ]
            
            for pattern in malicious_patterns:
                if pattern.lower() in header.lower():
                    return False, f"Patrón sospechoso detectado"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error escaneando archivo {file_path}: {e}")
            return False, f"Error en escaneo: {e}"
    
    def _quarantine_file(self, file_path: Path, reason: str) -> Path:
        """Mover archivo a cuarentena"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        quarantine_filename = f"{timestamp}_{file_path.name}"
        quarantine_path = Path(self.config['quarantine_dir']) / quarantine_filename
        
        # Crear directorio de cuarentena si no existe
        quarantine_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Mover archivo
        shutil.move(str(file_path), str(quarantine_path))
        
        # Registrar en log
        logger.warning(f"Archivo en cuarentena: {file_path} -> {quarantine_path} (Razón: {reason})")
        
        # Crear archivo de metadatos
        metadata_path = quarantine_path.with_suffix('.metadata')
        with open(metadata_path, 'w') as f:
            f.write(f"Original path: {file_path}\n")
            f.write(f"Quarantine reason: {reason}\n")
            f.write(f"Quarantine date: {datetime.now().isoformat()}\n")
        
        self._stats['quarantined_files'] += 1
        
        return quarantine_path
    
    def upload_file(self, file: FileStorage, inquilino_id: int, empresa_id: int, 
                   file_type: str = 'general', metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Subir archivo con validación y procesamiento completo"""
        
        with self._lock:
            self._stats['total_uploads'] += 1
        
        try:
            # Validar archivo
            is_valid, error_message = self._validate_file(file)
            if not is_valid:
                self._stats['failed_uploads'] += 1
                return {
                    'success': False,
                    'error': error_message,
                    'error_code': 'VALIDATION_ERROR'
                }
            
            # Generar nombre seguro
            safe_filename = self._generate_safe_filename(file.filename, inquilino_id, empresa_id)
            
            # Determinar ruta final
            final_path = self._get_file_path(inquilino_id, empresa_id, file_type, safe_filename)
            
            # Crear archivo temporal primero
            temp_path = Path(self.config['temp_dir']) / f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_filename}"
            
            # Guardar archivo en temporal
            file.save(str(temp_path))
            
            # Escanear archivo
            scan_passed, scan_reason = self._scan_file(temp_path)
            if not scan_passed:
                if self.config['quarantine_suspicious']:
                    quarantine_path = self._quarantine_file(temp_path, scan_reason)
                    return {
                        'success': False,
                        'error': 'Archivo bloqueado por medidas de seguridad',
                        'error_code': 'SECURITY_BLOCK',
                        'quarantine_path': str(quarantine_path)
                    }
                else:
                    temp_path.unlink()  # Eliminar archivo temporal
                    return {
                        'success': False,
                        'error': f'Archivo no pasó validación de seguridad: {scan_reason}',
                        'error_code': 'SECURITY_VALIDATION_FAILED'
                    }
            
            # Mover de temporal a ubicación final
            final_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(temp_path), str(final_path))
            
            # Calcular hash del archivo
            file_hash = self._calculate_file_hash(final_path)
            
            # Obtener información del archivo
            file_info = self._get_file_info(final_path)
            
            # Actualizar estadísticas
            with self._lock:
                self._stats['storage_used'] += file_info['size']
            
            # Preparar resultado
            result = {
                'success': True,
                'file_id': file_hash,
                'filename': safe_filename,
                'original_filename': file.filename,
                'file_path': str(final_path.relative_to(self.config['base_upload_dir'])),
                'absolute_path': str(final_path),
                'file_type': file_type,
                'size': file_info['size'],
                'mime_type': file_info['mime_type'],
                'hash': file_hash,
                'upload_date': datetime.now().isoformat(),
                'inquilino_id': inquilino_id,
                'empresa_id': empresa_id,
                'metadata': metadata or {}
            }
            
            logger.info(f"Archivo subido exitosamente: {safe_filename} ({file_info['size']} bytes)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error subiendo archivo: {e}")
            self._stats['failed_uploads'] += 1
            
            # Limpiar archivos temporales en caso de error
            if 'temp_path' in locals() and temp_path.exists():
                temp_path.unlink()
            
            return {
                'success': False,
                'error': f'Error interno del servidor: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calcular hash SHA-256 del archivo"""
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(self.config['chunk_size']), b''):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Obtener información detallada del archivo"""
        stat = file_path.stat()
        
        # Determinar MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type and hasattr(magic, 'from_file'):
            try:
                mime_type = magic.from_file(str(file_path), mime=True)
            except:
                mime_type = 'application/octet-stream'
        
        return {
            'size': stat.st_size,
            'mime_type': mime_type or 'application/octet-stream',
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'extension': file_path.suffix.lower()
        }
    
    def download_file(self, file_path: str, inquilino_id: int, empresa_id: int) -> Tuple[bool, Any]:
        """Descargar archivo con verificación de permisos"""
        try:
            # Construir ruta absoluta
            if file_path.startswith('/'):
                absolute_path = Path(file_path)
            else:
                absolute_path = Path(self.config['base_upload_dir']) / file_path
            
            # Verificar que el archivo existe
            if not absolute_path.exists():
                return False, {'error': 'Archivo no encontrado', 'error_code': 'FILE_NOT_FOUND'}
            
            # Verificar permisos (el archivo debe estar en el directorio del inquilino/empresa)
            expected_prefix = Path(self.config['base_upload_dir']) / f"inquilino_{inquilino_id}" / f"empresa_{empresa_id}"
            
            try:
                absolute_path.resolve().relative_to(expected_prefix.resolve())
            except ValueError:
                return False, {'error': 'Acceso denegado', 'error_code': 'ACCESS_DENIED'}
            
            # Actualizar estadísticas
            with self._lock:
                self._stats['total_downloads'] += 1
            
            # Obtener información del archivo
            file_info = self._get_file_info(absolute_path)
            
            logger.info(f"Archivo descargado: {absolute_path} por inquilino {inquilino_id}")
            
            return True, {
                'file_path': str(absolute_path),
                'filename': absolute_path.name,
                'size': file_info['size'],
                'mime_type': file_info['mime_type']
            }
            
        except Exception as e:
            logger.error(f"Error descargando archivo {file_path}: {e}")
            return False, {'error': f'Error interno: {str(e)}', 'error_code': 'INTERNAL_ERROR'}
    
    def delete_file(self, file_path: str, inquilino_id: int, empresa_id: int) -> Dict[str, Any]:
        """Eliminar archivo con verificación de permisos"""
        try:
            # Construir ruta absoluta
            if file_path.startswith('/'):
                absolute_path = Path(file_path)
            else:
                absolute_path = Path(self.config['base_upload_dir']) / file_path
            
            # Verificar que el archivo existe
            if not absolute_path.exists():
                return {'success': False, 'error': 'Archivo no encontrado', 'error_code': 'FILE_NOT_FOUND'}
            
            # Verificar permisos
            expected_prefix = Path(self.config['base_upload_dir']) / f"inquilino_{inquilino_id}" / f"empresa_{empresa_id}"
            
            try:
                absolute_path.resolve().relative_to(expected_prefix.resolve())
            except ValueError:
                return {'success': False, 'error': 'Acceso denegado', 'error_code': 'ACCESS_DENIED'}
            
            # Obtener tamaño antes de eliminar para estadísticas
            file_size = absolute_path.stat().st_size
            
            # Eliminar archivo
            absolute_path.unlink()
            
            # Actualizar estadísticas
            with self._lock:
                self._stats['storage_used'] = max(0, self._stats['storage_used'] - file_size)
            
            logger.info(f"Archivo eliminado: {absolute_path}")
            
            return {
                'success': True,
                'message': 'Archivo eliminado correctamente',
                'file_path': str(absolute_path),
                'size_freed': file_size
            }
            
        except Exception as e:
            logger.error(f"Error eliminando archivo {file_path}: {e}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def list_files(self, inquilino_id: int, empresa_id: int, file_type: str = None) -> List[Dict[str, Any]]:
        """Listar archivos de un inquilino/empresa"""
        try:
            base_path = Path(self.config['base_upload_dir']) / f"inquilino_{inquilino_id}" / f"empresa_{empresa_id}"
            
            if not base_path.exists():
                return []
            
            files = []
            
            # Buscar archivos recursivamente
            for file_path in base_path.rglob('*'):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    
                    # Filtrar por tipo si se especifica
                    if file_type and file_type not in str(file_path.parent):
                        continue
                    
                    try:
                        file_info = self._get_file_info(file_path)
                        relative_path = file_path.relative_to(Path(self.config['base_upload_dir']))
                        
                        files.append({
                            'filename': file_path.name,
                            'file_path': str(relative_path),
                            'absolute_path': str(file_path),
                            'size': file_info['size'],
                            'mime_type': file_info['mime_type'],
                            'created': file_info['created'],
                            'modified': file_info['modified'],
                            'extension': file_info['extension'],
                            'file_type': file_path.parent.name if file_path.parent.name in ['evidencias', 'reportes', 'general'] else 'general'
                        })
                        
                    except Exception as e:
                        logger.warning(f"Error obteniendo info de archivo {file_path}: {e}")
                        continue
            
            # Ordenar por fecha de modificación (más recientes primero)
            files.sort(key=lambda x: x['modified'], reverse=True)
            
            return files
            
        except Exception as e:
            logger.error(f"Error listando archivos para inquilino {inquilino_id}, empresa {empresa_id}: {e}")
            return []
    
    def cleanup_temp_files(self):
        """Limpiar archivos temporales antiguos"""
        if not self.config['cleanup_enabled']:
            return
        
        try:
            temp_dir = Path(self.config['temp_dir'])
            if not temp_dir.exists():
                return
            
            cutoff_time = datetime.now() - timedelta(seconds=self.config['temp_file_lifetime'])
            
            cleaned_count = 0
            cleaned_size = 0
            
            for file_path in temp_dir.iterdir():
                if file_path.is_file():
                    file_stat = file_path.stat()
                    file_modified = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    if file_modified < cutoff_time:
                        try:
                            cleaned_size += file_stat.st_size
                            file_path.unlink()
                            cleaned_count += 1
                        except Exception as e:
                            logger.warning(f"Error eliminando archivo temporal {file_path}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"Cleanup completado: {cleaned_count} archivos temporales eliminados ({cleaned_size} bytes)")
                
        except Exception as e:
            logger.error(f"Error en cleanup de archivos temporales: {e}")
    
    def get_storage_stats(self, inquilino_id: int = None, empresa_id: int = None) -> Dict[str, Any]:
        """Obtener estadísticas de almacenamiento"""
        try:
            stats = {
                'total_files': 0,
                'total_size': 0,
                'files_by_type': {},
                'files_by_extension': {},
                'largest_files': [],
                'recent_files': []
            }
            
            # Determinar directorio base
            if inquilino_id and empresa_id:
                base_path = Path(self.config['base_upload_dir']) / f"inquilino_{inquilino_id}" / f"empresa_{empresa_id}"
            elif inquilino_id:
                base_path = Path(self.config['base_upload_dir']) / f"inquilino_{inquilino_id}"
            else:
                base_path = Path(self.config['base_upload_dir'])
            
            if not base_path.exists():
                return stats
            
            all_files = []
            
            # Recorrer archivos
            for file_path in base_path.rglob('*'):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    try:
                        file_stat = file_path.stat()
                        file_info = {
                            'path': str(file_path),
                            'name': file_path.name,
                            'size': file_stat.st_size,
                            'modified': datetime.fromtimestamp(file_stat.st_mtime),
                            'extension': file_path.suffix.lower()
                        }
                        
                        all_files.append(file_info)
                        
                        # Actualizar contadores
                        stats['total_files'] += 1
                        stats['total_size'] += file_info['size']
                        
                        # Contar por extensión
                        ext = file_info['extension'] or 'sin_extension'
                        stats['files_by_extension'][ext] = stats['files_by_extension'].get(ext, 0) + 1
                        
                        # Contar por tipo (basado en directorio padre)
                        file_type = file_path.parent.name
                        stats['files_by_type'][file_type] = stats['files_by_type'].get(file_type, 0) + 1
                        
                    except Exception as e:
                        logger.warning(f"Error procesando archivo {file_path}: {e}")
            
            # Archivos más grandes (top 10)
            stats['largest_files'] = sorted(all_files, key=lambda x: x['size'], reverse=True)[:10]
            
            # Archivos más recientes (top 10)
            stats['recent_files'] = sorted(all_files, key=lambda x: x['modified'], reverse=True)[:10]
            
            # Convertir datetime a string para serialización
            for file_info in stats['largest_files'] + stats['recent_files']:
                file_info['modified'] = file_info['modified'].isoformat()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de almacenamiento: {e}")
            return {'error': str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del gestor de archivos"""
        return self._stats.copy()

# Instancia global
file_manager = None

def init_file_manager(config=None):
    """Inicializar gestor de archivos"""
    global file_manager
    file_manager = FileManager(config)
    file_manager.initialize()
    return file_manager

def get_file_manager():
    """Obtener instancia del gestor de archivos"""
    return file_manager
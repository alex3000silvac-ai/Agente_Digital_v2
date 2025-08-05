# error_handlers.py - Sistema de Manejo de Errores para Endpoints
"""
Decoradores y manejadores de errores robustos para prevenir caídas del sistema.
Garantiza que nunca se retorne un error 500 sin manejo.
"""

import traceback
import logging
from functools import wraps
from flask import jsonify, request
from datetime import datetime
import pyodbc
import json

# Configurar logging para errores
error_logger = logging.getLogger('error_handler')
error_logger.setLevel(logging.ERROR)

# Crear handler para archivo de errores (con ruta segura)
import os
log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, 'error_log.txt')

try:
    handler = logging.FileHandler(log_file, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    error_logger.addHandler(handler)
except (PermissionError, FileNotFoundError):
    # Fallback a consola si no se puede escribir archivo
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    error_logger.addHandler(console_handler)

class ErrorResponse:
    """Generador de respuestas de error estandarizadas"""
    
    @staticmethod
    def database_error(message: str = "Error de base de datos", details: str = None):
        """Error de base de datos"""
        return {
            "error": "DATABASE_ERROR",
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "recoverable": True
        }, 500
    
    @staticmethod
    def validation_error(message: str = "Error de validación", field: str = None):
        """Error de validación"""
        return {
            "error": "VALIDATION_ERROR", 
            "message": message,
            "field": field,
            "timestamp": datetime.now().isoformat(),
            "recoverable": True
        }, 400
    
    @staticmethod
    def authentication_error(message: str = "Error de autenticación"):
        """Error de autenticación"""
        return {
            "error": "AUTH_ERROR",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "recoverable": True
        }, 401
    
    @staticmethod
    def not_found_error(resource: str = "Recurso"):
        """Error de recurso no encontrado"""
        return {
            "error": "NOT_FOUND",
            "message": f"{resource} no encontrado",
            "timestamp": datetime.now().isoformat(),
            "recoverable": True
        }, 404
    
    @staticmethod
    def generic_error(message: str = "Error interno del servidor"):
        """Error genérico controlado"""
        return {
            "error": "INTERNAL_ERROR",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "recoverable": False
        }, 500

def safe_endpoint(default_response=None, log_level=logging.ERROR):
    """
    Decorador principal para endpoints seguros.
    Captura TODOS los errores y retorna respuestas JSON válidas.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Log de inicio de endpoint
                endpoint_name = func.__name__
                method = request.method if request else "UNKNOWN"
                error_logger.info(f"🚀 Iniciando {method} {endpoint_name}")
                
                # Ejecutar función
                result = func(*args, **kwargs)
                
                # Log de éxito
                error_logger.info(f"✅ {method} {endpoint_name} completado exitosamente")
                return result
                
            except pyodbc.Error as e:
                # Errores específicos de base de datos
                error_msg = f"Error de BD en {func.__name__}: {str(e)}"
                error_logger.error(error_msg, exc_info=True)
                
                response, status = ErrorResponse.database_error(
                    "Error de conexión o consulta a la base de datos",
                    str(e)
                )
                return jsonify(response), status
                
            except ValueError as e:
                # Errores de validación
                error_msg = f"Error de validación en {func.__name__}: {str(e)}"
                error_logger.warning(error_msg)
                
                response, status = ErrorResponse.validation_error(str(e))
                return jsonify(response), status
                
            except KeyError as e:
                # Errores de datos faltantes
                error_msg = f"Datos faltantes en {func.__name__}: {str(e)}"
                error_logger.warning(error_msg)
                
                response, status = ErrorResponse.validation_error(
                    f"Campo requerido faltante: {str(e)}", 
                    str(e)
                )
                return jsonify(response), status
                
            except PermissionError as e:
                # Errores de permisos
                error_msg = f"Error de permisos en {func.__name__}: {str(e)}"
                error_logger.warning(error_msg)
                
                response, status = ErrorResponse.authentication_error(
                    "No tiene permisos para realizar esta acción"
                )
                return jsonify(response), status
                
            except FileNotFoundError as e:
                # Errores de archivo no encontrado
                error_msg = f"Archivo no encontrado en {func.__name__}: {str(e)}"
                error_logger.warning(error_msg)
                
                response, status = ErrorResponse.not_found_error("Archivo")
                return jsonify(response), status
                
            except Exception as e:
                # Cualquier otro error no capturado
                error_msg = f"Error inesperado en {func.__name__}: {str(e)}"
                error_logger.error(error_msg, exc_info=True)
                
                # Log detallado para debugging
                error_logger.error(f"Traceback completo:\n{traceback.format_exc()}")
                
                response, status = ErrorResponse.generic_error(
                    "Error interno del servidor. El equipo técnico ha sido notificado."
                )
                
                # En desarrollo, incluir más detalles
                import os
                if os.environ.get('FLASK_ENV') == 'development':
                    response['debug_info'] = str(e)
                    response['traceback'] = traceback.format_exc()
                
                return jsonify(response), status
                
        return wrapper
    return decorator

def require_auth(func):
    """Decorador que requiere autenticación válida"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Importar aquí para evitar imports circulares
            from .admin_views import get_user_organization
            
            user_org = get_user_organization()
            if not user_org:
                response, status = ErrorResponse.authentication_error(
                    "Token de autenticación inválido o expirado"
                )
                return jsonify(response), status
            
            return func(*args, **kwargs)
        except Exception as e:
            error_logger.error(f"Error en autenticación: {str(e)}")
            response, status = ErrorResponse.authentication_error()
            return jsonify(response), status
            
    return wrapper

def validate_json_payload(required_fields: list = None):
    """Decorador que valida payload JSON"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if not request.is_json:
                    response, status = ErrorResponse.validation_error(
                        "Content-Type debe ser application/json"
                    )
                    return jsonify(response), status
                
                data = request.get_json()
                if not data:
                    response, status = ErrorResponse.validation_error(
                        "Body JSON es requerido"
                    )
                    return jsonify(response), status
                
                if required_fields:
                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        response, status = ErrorResponse.validation_error(
                            f"Campos requeridos faltantes: {', '.join(missing_fields)}"
                        )
                        return jsonify(response), status
                
                return func(*args, **kwargs)
                
            except json.JSONDecodeError as e:
                response, status = ErrorResponse.validation_error(
                    "JSON inválido en el body de la petición"
                )
                return jsonify(response), status
                
        return wrapper
    return decorator

def log_performance(func):
    """Decorador para medir y loggear performance"""
    @wraps(func) 
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if duration > 2.0:  # Log operaciones lentas
            error_logger.warning(f"⚠️ Operación lenta: {func.__name__} tomó {duration:.2f}s")
        else:
            error_logger.info(f"⏱️ {func.__name__} completado en {duration:.2f}s")
            
        return result
    return wrapper

class DatabaseHealthChecker:
    """Verificador de salud de la base de datos"""
    
    @staticmethod
    def check_connection(cursor) -> dict:
        """Verifica estado de conexión a BD"""
        try:
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return {
                "status": "healthy",
                "message": "Conexión a base de datos OK",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "message": f"Error de conexión: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    @staticmethod
    def check_critical_tables(cursor, tables: list) -> dict:
        """Verifica que tablas críticas existan"""
        missing_tables = []
        
        for table in tables:
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = '{table}'
                """)
                exists = cursor.fetchone()[0] > 0
                if not exists:
                    missing_tables.append(table)
            except:
                missing_tables.append(table)
        
        if missing_tables:
            return {
                "status": "degraded",
                "message": f"Tablas faltantes: {', '.join(missing_tables)}",
                "missing_tables": missing_tables,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "healthy",
                "message": "Todas las tablas críticas están disponibles",
                "timestamp": datetime.now().isoformat()
            }

# Función para registrar errores críticos
def log_critical_error(error: Exception, context: str = ""):
    """Registra errores críticos para análisis posterior"""
    critical_logger = logging.getLogger('critical_errors')
    
    error_data = {
        "timestamp": datetime.now().isoformat(),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "traceback": traceback.format_exc(),
        "request_url": request.url if request else "N/A",
        "request_method": request.method if request else "N/A"
    }
    
    critical_logger.error(f"CRITICAL ERROR: {json.dumps(error_data, indent=2)}")
    
    # Aquí podrías agregar notificaciones (email, Slack, etc.)
    # send_critical_alert(error_data)

# Manejadores globales de errores para Flask
def register_error_handlers(app):
    """Registra manejadores de errores globales en la aplicación Flask"""
    
    @app.errorhandler(404)
    def handle_404(e):
        response, status = ErrorResponse.not_found_error("Endpoint")
        return jsonify(response), status
    
    @app.errorhandler(405)
    def handle_405(e):
        response, status = ErrorResponse.validation_error(
            "Método HTTP no permitido para este endpoint"
        )
        return jsonify(response), status
    
    @app.errorhandler(500)
    def handle_500(e):
        log_critical_error(e, "Error 500 no capturado")
        response, status = ErrorResponse.generic_error()
        return jsonify(response), status
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        log_critical_error(e, "Excepción no capturada")
        response, status = ErrorResponse.generic_error()
        return jsonify(response), status

# Decorador combinado para endpoints de alto nivel
def robust_endpoint(require_authentication=True, validate_payload=None, log_perf=True):
    """
    Decorador combinado que aplica todas las protecciones:
    - Manejo seguro de errores
    - Autenticación (opcional)
    - Validación de payload (opcional)
    - Logging de performance (opcional)
    """
    def decorator(func):
        # Aplicar decoradores en orden
        wrapped_func = func
        
        if log_perf:
            wrapped_func = log_performance(wrapped_func)
        
        if validate_payload:
            wrapped_func = validate_json_payload(validate_payload)(wrapped_func)
        
        if require_authentication:
            wrapped_func = require_auth(wrapped_func)
        
        wrapped_func = safe_endpoint()(wrapped_func)
        
        return wrapped_func
    return decorator
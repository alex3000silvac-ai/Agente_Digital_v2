# db_validator.py - Sistema de Validación de Base de Datos
"""
Sistema robusto de validación de base de datos para prevenir errores 500.
Valida existencia de tablas, columnas y construye consultas seguras.
"""

import pyodbc
from functools import wraps
from typing import List, Dict, Optional, Tuple, Any
import logging

# Configurar logging específico para validación
logging.basicConfig(level=logging.INFO)
validator_logger = logging.getLogger('db_validator')

class DatabaseValidator:
    """Validador robusto de base de datos con cache de metadatos"""
    
    def __init__(self):
        self._table_cache = {}
        self._column_cache = {}
        self._cache_initialized = False
    
    def validate_connection(self, cursor) -> bool:
        """Valida que la conexión a base de datos esté activa"""
        try:
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True
        except Exception as e:
            validator_logger.error(f"❌ Conexión a BD inválida: {str(e)}")
            return False
    
    def table_exists(self, cursor, table_name: str) -> bool:
        """Verifica si una tabla existe en la base de datos"""
        if not self.validate_connection(cursor):
            return False
            
        # Usar cache si disponible
        if table_name in self._table_cache:
            return self._table_cache[table_name]
        
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = ?
            """, (table_name,))
            exists = cursor.fetchone()[0] > 0
            
            # Guardar en cache
            self._table_cache[table_name] = exists
            validator_logger.info(f"🔍 Tabla '{table_name}': {'EXISTE' if exists else 'NO EXISTE'}")
            return exists
            
        except Exception as e:
            validator_logger.error(f"❌ Error verificando tabla '{table_name}': {str(e)}")
            self._table_cache[table_name] = False
            return False
    
    def get_table_columns(self, cursor, table_name: str) -> List[str]:
        """Obtiene lista de columnas de una tabla"""
        if not self.validate_connection(cursor):
            return []
            
        # Usar cache si disponible
        cache_key = table_name
        if cache_key in self._column_cache:
            return self._column_cache[cache_key]
        
        if not self.table_exists(cursor, table_name):
            self._column_cache[cache_key] = []
            return []
        
        try:
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """, (table_name,))
            
            columns = [row[0] for row in cursor.fetchall()]
            
            # Guardar en cache
            self._column_cache[cache_key] = columns
            validator_logger.info(f"🔍 Columnas de '{table_name}': {len(columns)} columnas encontradas")
            return columns
            
        except Exception as e:
            validator_logger.error(f"❌ Error obteniendo columnas de '{table_name}': {str(e)}")
            self._column_cache[cache_key] = []
            return []
    
    def validate_columns_exist(self, cursor, table_name: str, required_columns: List[str]) -> Tuple[List[str], List[str]]:
        """Valida qué columnas existen y cuáles faltan"""
        available_columns = self.get_table_columns(cursor, table_name)
        
        existing = [col for col in required_columns if col in available_columns]
        missing = [col for col in required_columns if col not in available_columns]
        
        if missing:
            validator_logger.warning(f"⚠️ Columnas faltantes en '{table_name}': {missing}")
        
        return existing, missing
    
    def build_safe_select_query(self, cursor, table_name: str, desired_columns: List[str], 
                               where_clause: str = "", joins: str = "", 
                               order_by: str = "") -> Tuple[str, List[str]]:
        """Construye una consulta SELECT segura con columnas validadas"""
        
        if not self.table_exists(cursor, table_name):
            validator_logger.error(f"❌ Tabla '{table_name}' no existe")
            return "", []
        
        available_columns = self.get_table_columns(cursor, table_name)
        
        if not available_columns:
            validator_logger.error(f"❌ Tabla '{table_name}' no tiene columnas")
            return "", []
        
        # Filtrar columnas que realmente existen
        safe_columns = []
        table_alias = table_name[0].lower()  # Usar primera letra como alias
        
        for col in desired_columns:
            if col in available_columns:
                safe_columns.append(f"{table_alias}.{col}")
            else:
                validator_logger.warning(f"⚠️ Columna '{col}' no existe en '{table_name}', omitiendo")
        
        # Si no hay columnas válidas, usar todas las disponibles (máximo 10)
        if not safe_columns:
            validator_logger.warning(f"⚠️ Ninguna columna deseada existe, usando columnas disponibles")
            safe_columns = [f"{table_alias}.{col}" for col in available_columns[:10]]
        
        # Construir consulta
        query_parts = [
            "SELECT",
            ", ".join(safe_columns),
            f"FROM {table_name} {table_alias}"
        ]
        
        if joins:
            query_parts.append(joins)
        
        if where_clause:
            query_parts.append(f"WHERE {where_clause}")
        
        if order_by:
            query_parts.append(f"ORDER BY {order_by}")
        
        final_query = " ".join(query_parts)
        actual_columns = [col.split('.')[-1] for col in safe_columns]  # Quitar alias de tabla
        
        validator_logger.info(f"✅ Consulta segura construida para '{table_name}' con {len(actual_columns)} columnas")
        return final_query, actual_columns
    
    def clear_cache(self):
        """Limpia el cache de metadatos"""
        self._table_cache.clear()
        self._column_cache.clear()
        validator_logger.info("🧹 Cache de validación limpiado")

# Instancia global del validador
db_validator = DatabaseValidator()

def safe_db_operation(default_return=None, log_errors=True):
    """Decorador para operaciones de base de datos seguras"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except pyodbc.Error as e:
                if log_errors:
                    validator_logger.error(f"❌ Error de BD en {func.__name__}: {str(e)}")
                return default_return
            except Exception as e:
                if log_errors:
                    validator_logger.error(f"❌ Error general en {func.__name__}: {str(e)}")
                return default_return
        return wrapper
    return decorator

def validate_table_access(table_name: str):
    """Decorador para validar acceso a tabla antes de ejecutar función"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Buscar cursor en argumentos
            cursor = None
            if 'cursor' in kwargs:
                cursor = kwargs['cursor']
            elif len(args) > 0 and hasattr(args[0], 'execute'):
                cursor = args[0]
            
            if cursor and not db_validator.table_exists(cursor, table_name):
                validator_logger.warning(f"⚠️ Tabla '{table_name}' no existe, retornando valor por defecto")
                return []
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Funciones de utilidad para consultas comunes
@safe_db_operation(default_return=[])
def safe_count_records(cursor, table_name: str, where_clause: str = "") -> int:
    """Cuenta registros de manera segura"""
    if not db_validator.table_exists(cursor, table_name):
        return 0
    
    query = f"SELECT COUNT(*) FROM {table_name}"
    if where_clause:
        query += f" WHERE {where_clause}"
    
    cursor.execute(query)
    return cursor.fetchone()[0]

@safe_db_operation(default_return=[])
def safe_select_all(cursor, table_name: str, columns: List[str] = None, 
                   where_clause: str = "", limit: int = None) -> List[Dict]:
    """Selecciona registros de manera segura"""
    
    if not columns:
        columns = db_validator.get_table_columns(cursor, table_name)[:10]  # Máximo 10 columnas
    
    query, actual_columns = db_validator.build_safe_select_query(
        cursor, table_name, columns, where_clause
    )
    
    if not query:
        return []
    
    if limit:
        query += f" TOP {limit}" if "TOP" not in query else ""
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    return [dict(zip(actual_columns, row)) for row in rows]

# Mapeo de campos estándar para consistencia
STANDARD_FIELD_MAPPINGS = {
    'Incidentes': {
        'ID_PRIMARY': 'IncidenteID',
        'TITLE': 'Titulo',
        'DESCRIPTION': 'DescripcionInicial', 
        'STATUS': 'EstadoActual',
        'SEVERITY': 'Criticidad',
        'CREATED': 'FechaCreacion',
        'DETECTED': 'FechaDeteccion',
        'COMPANY_ID': 'EmpresaID'
    },
    'Empresas': {
        'ID_PRIMARY': 'EmpresaID',
        'NAME': 'RazonSocial',
        'RUT': 'RUT',
        'TYPE': 'TipoEmpresa',
        'TENANT_ID': 'InquilinoID',
        'ACTIVE': 'EstadoActivo'
    },
    'Usuarios': {
        'ID_PRIMARY': 'UsuarioID',
        'EMAIL': 'Email',
        'ROLE': 'Rol',
        'TENANT_ID': 'InquilinoID',
        'COMPANY_ID': 'EmpresaID'
    }
}

def get_standard_fields(table_name: str) -> Dict[str, str]:
    """Obtiene mapeo de campos estándar para una tabla"""
    return STANDARD_FIELD_MAPPINGS.get(table_name, {})

def validate_and_map_fields(cursor, table_name: str, desired_fields: Dict[str, str]) -> Dict[str, str]:
    """Valida y mapea campos deseados con campos reales de la tabla"""
    available_columns = db_validator.get_table_columns(cursor, table_name)
    validated_mapping = {}
    
    for standard_name, db_column in desired_fields.items():
        if db_column in available_columns:
            validated_mapping[standard_name] = db_column
        else:
            validator_logger.warning(f"⚠️ Campo '{db_column}' no existe en '{table_name}'")
    
    return validated_mapping
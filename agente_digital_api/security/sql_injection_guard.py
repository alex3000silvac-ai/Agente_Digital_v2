"""
sql_injection_guard.py - Protección contra SQL Injection
======================================================

Este módulo implementa protección completa contra ataques de SQL Injection
usando prepared statements, validación de queries y análisis de patrones.

Características:
- Wrapper seguro para todas las queries
- Prepared statements obligatorios
- Validación de parámetros
- Detección de patrones maliciosos
- Query builder seguro
- Logging de intentos de inyección
"""

import os
import re
import hashlib
import pyodbc
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
import logging

class SQLInjectionGuard:
    """
    Sistema de protección contra SQL Injection
    """
    
    def __init__(self):
        self.config = {
            'ENABLE_GUARD': os.getenv('ENABLE_SQL_GUARD', 'true').lower() == 'true',
            'LOG_QUERIES': os.getenv('LOG_SQL_QUERIES', 'false').lower() == 'true',
            'MAX_QUERY_LENGTH': int(os.getenv('MAX_QUERY_LENGTH', 10000)),
            'MAX_PARAM_LENGTH': int(os.getenv('MAX_SQL_PARAM_LENGTH', 1000)),
            'STRICT_MODE': os.getenv('SQL_GUARD_STRICT', 'true').lower() == 'true'
        }
        
        # Patrones peligrosos de SQL Injection
        self.dangerous_patterns = [
            # Comentarios SQL
            r'(--|#|\/\*|\*\/)',
            
            # Operadores de unión y subconsultas
            r'\b(union|intersect|except)\b',
            
            # Comandos DDL
            r'\b(create|alter|drop|truncate)\b',
            
            # Comandos peligrosos
            r'\b(exec|execute|xp_|sp_|dbcc|declare|cursor|trigger)\b',
            
            # Funciones peligrosas
            r'\b(char|nchar|varchar|nvarchar|cast|convert|substring)\b\s*\(',
            
            # Inyección de tiempo
            r'\b(waitfor|delay|sleep|benchmark)\b',
            
            # Acceso a objetos del sistema
            r'\b(sysobjects|syscolumns|information_schema|master\.\.)\b',
            
            # Caracteres de escape peligrosos
            r"(\x00|\x1a|\\x)",
            
            # Inyección booleana
            r"(\bor\b.*=.*\bor\b|\band\b.*=.*\band\b)",
            
            # Stacked queries
            r';\s*(select|insert|update|delete|drop|create)',
        ]
        
        # Whitelist de tablas permitidas
        self.allowed_tables = {
            'Incidentes', 'Empresas', 'Inquilinos', 'Usuarios',
            'INCIDENTE_TAXONOMIA', 'Taxonomia_incidentes',
            'EvidenciasIncidentes', 'EVIDENCIAS_TAXONOMIA',
            'CumplimientoEmpresas', 'EvidenciasCumplimiento',
            'UsuariosInquilino', 'Normativas', 'Obligaciones'
        }
        
        # Cache de queries validadas
        self.validated_queries_cache = {}
        
        self.logger = logging.getLogger(__name__)
    
    def safe_query(self, cursor: pyodbc.Cursor, query: str, 
                   params: Optional[Union[Tuple, List]] = None) -> pyodbc.Cursor:
        """
        Ejecuta una query de forma segura con validación completa
        
        Args:
            cursor: Cursor de pyodbc
            query: Query SQL
            params: Parámetros para la query
            
        Returns:
            Cursor con resultados
            
        Raises:
            ValueError: Si se detecta intento de SQL Injection
        """
        if not self.config['ENABLE_GUARD']:
            return cursor.execute(query, params or ())
        
        # Validar query
        self._validate_query(query)
        
        # Validar parámetros
        if params:
            self._validate_params(params)
        
        # Log si está habilitado
        if self.config['LOG_QUERIES']:
            self._log_query(query, params)
        
        # Ejecutar query segura
        try:
            if params:
                return cursor.execute(query, params)
            else:
                return cursor.execute(query)
        except Exception as e:
            # Detectar errores que podrían indicar SQL Injection
            error_msg = str(e).lower()
            if any(word in error_msg for word in ['syntax', 'inject', 'hack']):
                self._log_injection_attempt(query, params, str(e))
            raise
    
    def _validate_query(self, query: str):
        """Valida que la query sea segura"""
        # Validar longitud
        if len(query) > self.config['MAX_QUERY_LENGTH']:
            raise ValueError("Query too long")
        
        # Normalizar query para análisis
        normalized_query = query.lower()
        
        # Verificar patrones peligrosos
        for pattern in self.dangerous_patterns:
            if re.search(pattern, normalized_query, re.IGNORECASE):
                self._log_injection_attempt(query, None, f"Dangerous pattern: {pattern}")
                raise ValueError("Potentially dangerous SQL pattern detected")
        
        # En modo estricto, validar tablas
        if self.config['STRICT_MODE']:
            self._validate_tables(query)
        
        # Verificar estructura básica
        self._validate_query_structure(query)
    
    def _validate_tables(self, query: str):
        """Valida que solo se acceda a tablas permitidas"""
        # Extraer nombres de tablas
        table_pattern = r'\b(?:from|join|into|update)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        tables = re.findall(table_pattern, query, re.IGNORECASE)
        
        for table in tables:
            if table.upper() not in (t.upper() for t in self.allowed_tables):
                self._log_injection_attempt(query, None, f"Unauthorized table: {table}")
                raise ValueError(f"Access to table '{table}' not allowed")
    
    def _validate_query_structure(self, query: str):
        """Valida la estructura básica de la query"""
        # Verificar balance de paréntesis
        if query.count('(') != query.count(')'):
            raise ValueError("Unbalanced parentheses in query")
        
        # Verificar balance de comillas
        single_quotes = query.count("'") - query.count("\\'")
        if single_quotes % 2 != 0:
            raise ValueError("Unbalanced quotes in query")
        
        # Verificar que no haya múltiples statements
        if ';' in query and not query.strip().endswith(';'):
            raise ValueError("Multiple statements not allowed")
    
    def _validate_params(self, params: Union[Tuple, List]):
        """Valida los parámetros de la query"""
        for i, param in enumerate(params):
            # Validar longitud de strings
            if isinstance(param, str):
                if len(param) > self.config['MAX_PARAM_LENGTH']:
                    raise ValueError(f"Parameter {i} too long")
                
                # Verificar patrones peligrosos en parámetros
                for pattern in self.dangerous_patterns:
                    if re.search(pattern, param, re.IGNORECASE):
                        self._log_injection_attempt(None, params, f"Dangerous pattern in param {i}")
                        raise ValueError(f"Dangerous pattern in parameter {i}")
            
            # Validar tipos numéricos
            elif isinstance(param, (int, float)):
                # Verificar rangos razonables
                if isinstance(param, int) and abs(param) > 2147483647:
                    raise ValueError(f"Parameter {i} out of range")
            
            # No permitir tipos de datos peligrosos
            elif param is not None and not isinstance(param, (str, int, float, bool, datetime)):
                raise ValueError(f"Parameter {i} has invalid type: {type(param)}")
    
    def build_safe_select(self, table: str, columns: List[str] = None,
                         where: Dict[str, Any] = None, order_by: str = None,
                         limit: int = None) -> Tuple[str, List[Any]]:
        """
        Construye una query SELECT segura
        
        Args:
            table: Nombre de la tabla
            columns: Lista de columnas (None = *)
            where: Condiciones WHERE como diccionario
            order_by: Columna para ORDER BY
            limit: Límite de resultados
            
        Returns:
            Tuple de (query, params)
        """
        # Validar tabla
        if table not in self.allowed_tables:
            raise ValueError(f"Table '{table}' not allowed")
        
        # Construir SELECT
        if columns:
            # Validar nombres de columnas
            for col in columns:
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                    raise ValueError(f"Invalid column name: {col}")
            columns_str = ', '.join(columns)
        else:
            columns_str = '*'
        
        query = f"SELECT {columns_str} FROM {table}"
        params = []
        
        # Agregar WHERE
        if where:
            conditions = []
            for col, value in where.items():
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                    raise ValueError(f"Invalid column name in WHERE: {col}")
                
                if value is None:
                    conditions.append(f"{col} IS NULL")
                elif isinstance(value, list):
                    # WHERE IN
                    placeholders = ', '.join(['?' for _ in value])
                    conditions.append(f"{col} IN ({placeholders})")
                    params.extend(value)
                else:
                    conditions.append(f"{col} = ?")
                    params.append(value)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        # Agregar ORDER BY
        if order_by:
            # Validar formato columna [ASC|DESC]
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(\s+(ASC|DESC))?$', order_by, re.IGNORECASE):
                raise ValueError(f"Invalid ORDER BY: {order_by}")
            query += f" ORDER BY {order_by}"
        
        # Agregar LIMIT (SQL Server style)
        if limit:
            if not isinstance(limit, int) or limit < 1 or limit > 10000:
                raise ValueError(f"Invalid LIMIT: {limit}")
            
            if not order_by:
                # SQL Server requiere ORDER BY para OFFSET/FETCH
                query += " ORDER BY (SELECT NULL)"
            
            query += f" OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY"
        
        return query, params
    
    def build_safe_insert(self, table: str, data: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """
        Construye una query INSERT segura
        
        Args:
            table: Nombre de la tabla
            data: Diccionario con columnas y valores
            
        Returns:
            Tuple de (query, params)
        """
        # Validar tabla
        if table not in self.allowed_tables:
            raise ValueError(f"Table '{table}' not allowed")
        
        if not data:
            raise ValueError("No data to insert")
        
        columns = []
        values = []
        params = []
        
        for col, value in data.items():
            # Validar nombre de columna
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                raise ValueError(f"Invalid column name: {col}")
            
            columns.append(col)
            values.append('?')
            params.append(value)
        
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)})"
        
        return query, params
    
    def build_safe_update(self, table: str, data: Dict[str, Any],
                         where: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """
        Construye una query UPDATE segura
        
        Args:
            table: Nombre de la tabla
            data: Diccionario con columnas y valores a actualizar
            where: Condiciones WHERE
            
        Returns:
            Tuple de (query, params)
        """
        # Validar tabla
        if table not in self.allowed_tables:
            raise ValueError(f"Table '{table}' not allowed")
        
        if not data:
            raise ValueError("No data to update")
        
        if not where:
            raise ValueError("WHERE clause required for UPDATE")
        
        set_clauses = []
        params = []
        
        # Construir SET
        for col, value in data.items():
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                raise ValueError(f"Invalid column name: {col}")
            
            set_clauses.append(f"{col} = ?")
            params.append(value)
        
        query = f"UPDATE {table} SET {', '.join(set_clauses)}"
        
        # Agregar WHERE
        where_clauses = []
        for col, value in where.items():
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                raise ValueError(f"Invalid column name in WHERE: {col}")
            
            if value is None:
                where_clauses.append(f"{col} IS NULL")
            else:
                where_clauses.append(f"{col} = ?")
                params.append(value)
        
        query += " WHERE " + " AND ".join(where_clauses)
        
        return query, params
    
    def build_safe_delete(self, table: str, where: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """
        Construye una query DELETE segura
        
        Args:
            table: Nombre de la tabla
            where: Condiciones WHERE
            
        Returns:
            Tuple de (query, params)
        """
        # Validar tabla
        if table not in self.allowed_tables:
            raise ValueError(f"Table '{table}' not allowed")
        
        if not where:
            raise ValueError("WHERE clause required for DELETE")
        
        query = f"DELETE FROM {table}"
        params = []
        
        # Agregar WHERE
        where_clauses = []
        for col, value in where.items():
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                raise ValueError(f"Invalid column name in WHERE: {col}")
            
            if value is None:
                where_clauses.append(f"{col} IS NULL")
            else:
                where_clauses.append(f"{col} = ?")
                params.append(value)
        
        query += " WHERE " + " AND ".join(where_clauses)
        
        return query, params
    
    def escape_like_pattern(self, pattern: str) -> str:
        """
        Escapa caracteres especiales en patrones LIKE
        
        Args:
            pattern: Patrón a escapar
            
        Returns:
            str: Patrón escapado
        """
        # Escapar caracteres especiales de LIKE
        pattern = pattern.replace('\\', '\\\\')
        pattern = pattern.replace('%', '\\%')
        pattern = pattern.replace('_', '\\_')
        pattern = pattern.replace('[', '\\[')
        
        return pattern
    
    def _log_query(self, query: str, params: Optional[Union[Tuple, List]]):
        """Log de queries para debugging"""
        if self.config['LOG_QUERIES']:
            # Hash de la query para agrupación
            query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
            
            self.logger.debug(f"SQL Query [{query_hash}]: {query[:200]}...")
            if params:
                self.logger.debug(f"SQL Params [{query_hash}]: {params[:5]}...")
    
    def _log_injection_attempt(self, query: Optional[str], params: Optional[Union[Tuple, List]], 
                              reason: str):
        """Log de intentos de SQL Injection"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'sql_injection_attempt',
            'reason': reason,
            'query': query[:500] if query else None,
            'params': str(params)[:200] if params else None
        }
        
        self.logger.warning(f"SQL_INJECTION_ATTEMPT: {event}")


# Instancia global
sql_guard = SQLInjectionGuard()
# database_adapter.py
# Adaptador para soportar SQL Server, PostgreSQL y Supabase

import os
import urllib.parse
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import psycopg2
import pyodbc

class DatabaseAdapter:
    """Adaptador de base de datos que soporta SQL Server, PostgreSQL y Supabase"""
    
    def __init__(self):
        self.db_type = None
        self.engine = None
        self._init_database()
    
    def _init_database(self):
        """Inicializa la conexión según la configuración"""
        # Verificar si es Supabase
        supabase_url = os.getenv('SUPABASE_DB_URL')
        database_url = os.getenv('DATABASE_URL')
        
        if supabase_url:
            # Supabase
            self.db_type = 'supabase'
            self.engine = create_engine(
                supabase_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={
                    "sslmode": "require",
                    "connect_timeout": 30
                }
            )
        elif database_url and database_url.startswith('postgresql://'):
            # Railway/PostgreSQL genérico
            self.db_type = 'postgresql'
            self.engine = create_engine(
                database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=300
            )
        else:
            # SQL Server local
            self.db_type = 'sqlserver'
            self._init_sqlserver()
    
    def _init_sqlserver(self):
        """Inicializa conexión SQL Server"""
        server = os.getenv('DB_SERVER', 'PASC')
        database = os.getenv('DB_DATABASE', 'AgenteDigitalDB')
        username = os.getenv('DB_USERNAME', 'app_usuario')
        password = os.getenv('DB_PASSWORD', 'ClaveSegura123!')
        
        connection_string = (
            f"mssql+pyodbc://{username}:{urllib.parse.quote_plus(password)}@"
            f"{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
            "&TrustServerCertificate=yes&Encrypt=no"
        )
        
        self.engine = create_engine(
            connection_string,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )
    
    def get_connection(self):
        """Obtiene una conexión de la base de datos"""
        return self.engine.connect()
    
    def execute_query(self, query, params=None):
        """Ejecuta una consulta adaptada al tipo de BD"""
        with self.engine.connect() as conn:
            if self.db_type == 'postgresql':
                # Adaptar sintaxis SQL Server a PostgreSQL
                query = self._adapt_query_to_postgres(query)
            
            result = conn.execute(text(query), params or {})
            conn.commit()
            return result
    
    def _adapt_query_to_postgres(self, query):
        """Adapta consultas de SQL Server a PostgreSQL"""
        # Reemplazos básicos
        replacements = {
            'GETDATE()': 'CURRENT_TIMESTAMP',
            'ISNULL': 'COALESCE',
            '[': '"',
            ']': '"',
            'TOP': 'LIMIT',
            'LEN': 'LENGTH',
            'DATEADD': 'INTERVAL',
            'bit': 'boolean',
            'nvarchar': 'varchar',
            'datetime2': 'timestamp'
        }
        
        for old, new in replacements.items():
            query = query.replace(old, new)
        
        # Manejo especial de TOP
        if 'TOP' in query.upper():
            import re
            query = re.sub(r'SELECT\s+TOP\s+(\d+)', r'SELECT', query)
            query += f' LIMIT {re.search(r"TOP\s+(\d+)", query, re.IGNORECASE).group(1)}'
        
        return query
    
    def table_exists(self, table_name):
        """Verifica si una tabla existe"""
        if self.db_type == 'postgresql':
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = :table_name
                )
            """
        else:
            query = """
                SELECT CASE WHEN EXISTS (
                    SELECT * FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = :table_name
                ) THEN 1 ELSE 0 END
            """
        
        result = self.execute_query(query, {'table_name': table_name.lower()})
        return bool(result.scalar())

# Instancia global
db_adapter = DatabaseAdapter()
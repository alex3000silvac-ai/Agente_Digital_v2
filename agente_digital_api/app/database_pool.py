# app/database_pool.py
# Sistema de base de datos mejorado con connection pooling para escalabilidad

import os
import logging
import time
from contextlib import contextmanager
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text, event
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.exc import DisconnectionError, TimeoutError as SQLTimeoutError
from sqlalchemy.engine import Engine
import pyodbc

# Configurar logging
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestor de base de datos con connection pooling optimizado para escalabilidad"""
    
    def __init__(self, config=None):
        self.config = config or self._get_default_config()
        self.engine = None
        self._connection_string = None
        self._pool_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'idle_connections': 0,
            'failed_connections': 0,
            'pool_hits': 0,
            'pool_misses': 0
        }
        
    def _get_default_config(self):
        """Configuración por defecto desde variables de entorno"""
        return {
            'server': os.environ.get('DB_SERVER', 'localhost'),
            'database': os.environ.get('DB_NAME', 'AgenteDigitalDB'),
            'driver': os.environ.get('DB_DRIVER', 'ODBC Driver 17 for SQL Server'),
            'username': os.environ.get('DB_USERNAME'),
            'password': os.environ.get('DB_PASSWORD'),
            'trusted_connection': os.environ.get('DB_TRUSTED_CONNECTION', 'yes').lower() == 'yes',
            
            # Configuración de pooling
            'pool_size': int(os.environ.get('DB_POOL_SIZE', '20')),
            'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', '50')),
            'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', '30')),
            'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', '3600')),
            'pool_pre_ping': os.environ.get('DB_POOL_PRE_PING', 'true').lower() == 'true',
            
            # Configuración de conexión
            'connect_timeout': int(os.environ.get('DB_CONNECT_TIMEOUT', '30')),
            'command_timeout': int(os.environ.get('DB_COMMAND_TIMEOUT', '30')),
            'autocommit': False,
            'encrypt': os.environ.get('DB_ENCRYPT', 'yes').lower() == 'yes',
            'trust_server_certificate': os.environ.get('DB_TRUST_CERT', 'no').lower() == 'yes',
        }
    
    def _build_connection_string(self):
        """Construir string de conexión optimizado"""
        if self._connection_string:
            return self._connection_string
            
        config = self.config
        
        # Parámetros de conexión ODBC
        params = [
            f"DRIVER={{{config['driver']}}}",
            f"SERVER={config['server']}",
            f"DATABASE={config['database']}",
        ]
        
        # Autenticación
        if config['trusted_connection']:
            params.append("Trusted_Connection=yes")
        else:
            if not config['username'] or not config['password']:
                raise ValueError("Username y password requeridos cuando Trusted_Connection=no")
            params.append(f"UID={config['username']}")
            params.append(f"PWD={config['password']}")
        
        # Configuración de seguridad
        if config['encrypt']:
            params.append("Encrypt=yes")
        if config['trust_server_certificate']:
            params.append("TrustServerCertificate=yes")
            
        # Configuración de timeouts
        params.append(f"Connection Timeout={config['connect_timeout']}")
        params.append(f"Command Timeout={config['command_timeout']}")
        
        # Configuraciones adicionales para performance
        params.append("MARS_Connection=yes")  # Multiple Active Result Sets
        params.append("MultipleActiveResultSets=True")
        params.append("Pooling=false")  # Deshabilitar pooling de ODBC (usamos SQLAlchemy)
        
        odbc_string = ";".join(params)
        
        # URL de SQLAlchemy con parámetros escapados
        self._connection_string = f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_string)}"
        
        return self._connection_string
    
    def _create_engine(self):
        """Crear engine de SQLAlchemy con configuración optimizada"""
        connection_string = self._build_connection_string()
        config = self.config
        
        # Determinar clase de pool basada en entorno
        flask_env = os.environ.get('FLASK_ENV', 'development').lower()
        
        if flask_env == 'testing':
            # Para testing, usar StaticPool para conexiones en memoria
            poolclass = StaticPool
            pool_size = 1
            max_overflow = 0
        else:
            # Para desarrollo y producción, usar QueuePool
            poolclass = QueuePool
            pool_size = config['pool_size']
            max_overflow = config['max_overflow']
        
        # Crear engine con configuración de pooling
        engine = create_engine(
            connection_string,
            poolclass=poolclass,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=config['pool_timeout'],
            pool_recycle=config['pool_recycle'],
            pool_pre_ping=config['pool_pre_ping'],
            echo=flask_env == 'development' and logger.level <= logging.DEBUG,
            echo_pool=flask_env == 'development' and logger.level <= logging.DEBUG,
            connect_args={
                'timeout': config['connect_timeout'],
                'autocommit': config['autocommit']
            }
        )
        
        # Registrar event listeners para monitoreo
        self._register_event_listeners(engine)
        
        return engine
    
    def _register_event_listeners(self, engine):
        """Registrar listeners para monitoreo y logging"""
        
        @event.listens_for(engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Evento al establecer conexión"""
            self._pool_stats['total_connections'] += 1
            logger.debug(f"Nueva conexión establecida. Total: {self._pool_stats['total_connections']}")
            
            # Configurar la conexión
            dbapi_connection.autocommit = self.config['autocommit']
            
        @event.listens_for(engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            """Evento al obtener conexión del pool"""
            self._pool_stats['active_connections'] += 1
            self._pool_stats['pool_hits'] += 1
            logger.debug(f"Conexión checkout. Activas: {self._pool_stats['active_connections']}")
            
        @event.listens_for(engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            """Evento al devolver conexión al pool"""
            self._pool_stats['active_connections'] -= 1
            self._pool_stats['idle_connections'] += 1
            logger.debug(f"Conexión checkin. Activas: {self._pool_stats['active_connections']}")
            
        @event.listens_for(engine, "invalidate")
        def on_invalidate(dbapi_connection, connection_record, exception):
            """Evento al invalidar conexión"""
            self._pool_stats['failed_connections'] += 1
            logger.warning(f"Conexión invalidada: {exception}")
    
    def initialize(self):
        """Inicializar el engine de base de datos"""
        if self.engine is None:
            try:
                logger.info("Inicializando conexión pool de base de datos...")
                self.engine = self._create_engine()
                
                # Verificar conectividad
                self.health_check()
                
                logger.info(f"Connection pool inicializado: pool_size={self.config['pool_size']}, "
                           f"max_overflow={self.config['max_overflow']}")
                
            except Exception as e:
                logger.error(f"Error inicializando base de datos: {e}")
                raise
    
    def health_check(self):
        """Verificar salud de la conexión"""
        if not self.engine:
            raise RuntimeError("Engine no inicializado")
            
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as health_check"))
                return result.fetchone()[0] == 1
        except Exception as e:
            logger.error(f"Health check falló: {e}")
            raise
    
    @contextmanager
    def get_connection(self, timeout=None):
        """Context manager para obtener conexión del pool"""
        if not self.engine:
            self.initialize()
            
        connection = None
        start_time = time.time()
        
        try:
            # Obtener conexión del pool
            connection = self.engine.connect()
            
            connection_time = time.time() - start_time
            if connection_time > 1.0:  # Log si toma más de 1 segundo
                logger.warning(f"Conexión tardó {connection_time:.2f}s en obtenerse")
            
            yield connection
            
        except (DisconnectionError, SQLTimeoutError) as e:
            logger.error(f"Error de conexión: {e}")
            if connection:
                connection.invalidate()
            raise
        except Exception as e:
            logger.error(f"Error en conexión: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                connection.close()
    
    @contextmanager 
    def get_transaction(self):
        """Context manager para transacciones"""
        with self.get_connection() as conn:
            trans = conn.begin()
            try:
                yield conn
                trans.commit()
            except Exception:
                trans.rollback()
                raise
    
    def execute_query(self, query, params=None, fetch_one=False, fetch_all=True):
        """Ejecutar query con manejo de errores y retry"""
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                with self.get_connection() as conn:
                    if isinstance(query, str):
                        query = text(query)
                    
                    result = conn.execute(query, params or {})
                    
                    if fetch_one:
                        return result.fetchone()
                    elif fetch_all:
                        return result.fetchall()
                    else:
                        return result
                        
            except (DisconnectionError, SQLTimeoutError) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Reintentando query, intento {attempt + 1}: {e}")
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    logger.error(f"Query falló después de {max_retries} intentos: {e}")
                    raise
            except Exception as e:
                logger.error(f"Error ejecutando query: {e}")
                raise
    
    def get_pool_stats(self):
        """Obtener estadísticas del pool"""
        stats = self._pool_stats.copy()
        
        if self.engine and hasattr(self.engine.pool, 'size'):
            stats.update({
                'pool_size': self.engine.pool.size(),
                'checked_in': self.engine.pool.checkedin(),
                'checked_out': self.engine.pool.checkedout(),
                'overflow': self.engine.pool.overflow(),
                'invalid': self.engine.pool.invalid(),
            })
        
        return stats
    
    def close(self):
        """Cerrar todas las conexiones del pool"""
        if self.engine:
            logger.info("Cerrando connection pool...")
            self.engine.dispose()
            self.engine = None

# Instancia global del database manager
db_manager = DatabaseManager()

def init_db(app=None):
    """Inicializar base de datos con configuración de Flask"""
    if app:
        # Actualizar configuración desde Flask app
        config = {
            'server': app.config.get('DB_SERVER', 'localhost'),
            'database': app.config.get('DB_NAME', 'AgenteDigitalDB'),
            'driver': app.config.get('DB_DRIVER', 'ODBC Driver 17 for SQL Server'),
            'username': app.config.get('DB_USERNAME'),
            'password': app.config.get('DB_PASSWORD'),
            'trusted_connection': app.config.get('DB_TRUSTED_CONNECTION', True),
            'pool_size': app.config.get('DB_POOL_SIZE', 20),
            'max_overflow': app.config.get('DB_MAX_OVERFLOW', 50),
            'pool_timeout': app.config.get('DB_POOL_TIMEOUT', 30),
            'pool_recycle': app.config.get('DB_POOL_RECYCLE', 3600),
            'pool_pre_ping': app.config.get('DB_POOL_PRE_PING', True),
            'connect_timeout': app.config.get('DB_CONNECT_TIMEOUT', 30),
            'command_timeout': app.config.get('DB_COMMAND_TIMEOUT', 30),
            'autocommit': app.config.get('DB_AUTOCOMMIT', False),
            'encrypt': app.config.get('DB_ENCRYPT', True),
            'trust_server_certificate': app.config.get('DB_TRUST_CERT', False),
        }
        db_manager.config = config
    
    db_manager.initialize()
    return db_manager

def get_db_connection():
    """Función compatible con el código existente"""
    return db_manager.get_connection()

def get_db_transaction():
    """Context manager para transacciones"""
    return db_manager.get_transaction()

def execute_query(query, params=None, fetch_one=False, fetch_all=True):
    """Función helper para ejecutar queries"""
    return db_manager.execute_query(query, params, fetch_one, fetch_all)

def get_pool_status():
    """Obtener estado del pool para monitoreo"""
    return db_manager.get_pool_stats()
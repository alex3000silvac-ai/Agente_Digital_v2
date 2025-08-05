"""
connection_pool.py - Pool de conexiones seguro y escalable
======================================================

Este módulo implementa un pool de conexiones robusto para manejar
500+ usuarios concurrentes de forma eficiente y segura.

Características:
- Connection pooling con límites configurables
- Retry logic para reconexión automática
- Circuit breaker para fallos de DB
- Métricas de performance
- Prevención de connection leaks
- Thread safety
"""

import os
import time
import threading
import queue
import pyodbc
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

class SecureConnectionPool:
    """
    Pool de conexiones seguro y escalable para SQL Server
    """
    
    def __init__(self):
        self.config = {
            'MIN_CONNECTIONS': int(os.getenv('DB_POOL_MIN', 10)),
            'MAX_CONNECTIONS': int(os.getenv('DB_POOL_MAX', 100)),
            'CONNECTION_TIMEOUT': int(os.getenv('DB_CONNECTION_TIMEOUT', 30)),
            'IDLE_TIMEOUT': int(os.getenv('DB_IDLE_TIMEOUT', 300)),  # 5 minutos
            'MAX_RETRIES': int(os.getenv('DB_MAX_RETRIES', 3)),
            'RETRY_DELAY': int(os.getenv('DB_RETRY_DELAY', 1)),
            'HEALTH_CHECK_INTERVAL': int(os.getenv('DB_HEALTH_CHECK_INTERVAL', 60)),
            'ENABLE_METRICS': os.getenv('DB_ENABLE_METRICS', 'true').lower() == 'true',
            'CIRCUIT_BREAKER_THRESHOLD': int(os.getenv('DB_CIRCUIT_BREAKER_THRESHOLD', 5)),
            'CIRCUIT_BREAKER_TIMEOUT': int(os.getenv('DB_CIRCUIT_BREAKER_TIMEOUT', 60))
        }
        
        # Configuración de base de datos
        self.db_config = {
            'server': os.getenv('DB_HOST', '192.168.100.125'),
            'database': os.getenv('DB_DATABASE', 'AgenteDigitalDB'),
            'username': os.getenv('DB_USERNAME', ''),
            'password': os.getenv('DB_PASSWORD', ''),
            'driver': os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
        }
        
        # Pool de conexiones
        self.pool = queue.Queue(maxsize=self.config['MAX_CONNECTIONS'])
        self.active_connections = 0
        self.total_connections_created = 0
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Circuit breaker
        self.circuit_breaker = {
            'failures': 0,
            'last_failure': None,
            'state': 'closed'  # closed, open, half-open
        }
        
        # Métricas
        self.metrics = {
            'connections_created': 0,
            'connections_reused': 0,
            'connections_failed': 0,
            'connections_timeout': 0,
            'current_pool_size': 0,
            'peak_connections': 0,
            'total_wait_time': 0,
            'total_requests': 0
        }
        
        # Tracking de conexiones para prevenir leaks
        self.connection_tracking = {}
        
        self.logger = logging.getLogger(__name__)
        
        # Inicializar pool
        self._initialize_pool()
        
        # Iniciar health check thread
        self._start_health_check_thread()
    
    def _initialize_pool(self):
        """Inicializa el pool con conexiones mínimas"""
        self.logger.info(f"Inicializando pool con {self.config['MIN_CONNECTIONS']} conexiones")
        
        for i in range(self.config['MIN_CONNECTIONS']):
            try:
                conn = self._create_connection()
                if conn:
                    self.pool.put({
                        'connection': conn,
                        'created_at': time.time(),
                        'last_used': time.time(),
                        'usage_count': 0
                    })
            except Exception as e:
                self.logger.error(f"Error creando conexión inicial {i}: {e}")
    
    def _create_connection(self) -> Optional[pyodbc.Connection]:
        """Crea una nueva conexión a la base de datos"""
        # Verificar circuit breaker
        if self.circuit_breaker['state'] == 'open':
            if self.circuit_breaker['last_failure']:
                time_since_failure = time.time() - self.circuit_breaker['last_failure']
                if time_since_failure < self.config['CIRCUIT_BREAKER_TIMEOUT']:
                    raise Exception("Circuit breaker is OPEN")
                else:
                    # Intentar half-open
                    self.circuit_breaker['state'] = 'half-open'
        
        # Validar credenciales
        if not self.db_config['username'] or not self.db_config['password']:
            raise ValueError("Database credentials not configured")
        
        # Construir connection string
        conn_str = (
            f"DRIVER={{{self.db_config['driver']}}};"
            f"SERVER={self.db_config['server']};"
            f"DATABASE={self.db_config['database']};"
            f"UID={self.db_config['username']};"
            f"PWD={self.db_config['password']};"
            f"Encrypt=no;"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout={self.config['CONNECTION_TIMEOUT']};"
            f"LoginTimeout={self.config['CONNECTION_TIMEOUT']};"
            f"MultipleActiveResultSets=true;"
            f"Pooling=false;"  # Desactivar pooling de ODBC, usamos el nuestro
        )
        
        try:
            # Crear conexión
            conn = pyodbc.connect(conn_str)
            
            # Configurar conexión
            conn.timeout = self.config['CONNECTION_TIMEOUT']
            conn.autocommit = False  # Transacciones explícitas
            
            # Test de conectividad
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            
            # Actualizar métricas
            with self.lock:
                self.total_connections_created += 1
                self.metrics['connections_created'] += 1
                
                # Si estaba en half-open y funcionó, cerrar circuit breaker
                if self.circuit_breaker['state'] == 'half-open':
                    self.circuit_breaker['state'] = 'closed'
                    self.circuit_breaker['failures'] = 0
                    self.logger.info("Circuit breaker CLOSED")
            
            return conn
            
        except Exception as e:
            # Registrar fallo
            with self.lock:
                self.metrics['connections_failed'] += 1
                self.circuit_breaker['failures'] += 1
                self.circuit_breaker['last_failure'] = time.time()
                
                # Abrir circuit breaker si hay muchos fallos
                if self.circuit_breaker['failures'] >= self.config['CIRCUIT_BREAKER_THRESHOLD']:
                    self.circuit_breaker['state'] = 'open'
                    self.logger.error(f"Circuit breaker OPEN after {self.circuit_breaker['failures']} failures")
            
            raise e
    
    @contextmanager
    def get_connection(self):
        """
        Context manager para obtener una conexión del pool
        
        Uso:
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tabla")
        """
        connection_wrapper = None
        start_time = time.time()
        thread_id = threading.current_thread().ident
        
        try:
            # Obtener conexión del pool
            connection_wrapper = self._acquire_connection()
            
            if not connection_wrapper:
                raise Exception("No connection available")
            
            # Tracking para prevenir leaks
            with self.lock:
                self.connection_tracking[thread_id] = {
                    'connection_id': id(connection_wrapper['connection']),
                    'acquired_at': time.time(),
                    'stack_trace': self._get_stack_trace()
                }
            
            # Actualizar métricas
            wait_time = time.time() - start_time
            with self.lock:
                self.metrics['total_wait_time'] += wait_time
                self.metrics['total_requests'] += 1
            
            # Yield la conexión
            yield connection_wrapper['connection']
            
            # Marcar como exitoso
            connection_wrapper['success'] = True
            
        except Exception as e:
            # Marcar conexión como problemática
            if connection_wrapper:
                connection_wrapper['success'] = False
            raise e
            
        finally:
            # Devolver conexión al pool
            if connection_wrapper:
                self._release_connection(connection_wrapper)
            
            # Limpiar tracking
            with self.lock:
                if thread_id in self.connection_tracking:
                    del self.connection_tracking[thread_id]
    
    def _acquire_connection(self) -> Optional[Dict[str, Any]]:
        """Adquiere una conexión del pool"""
        timeout = self.config['CONNECTION_TIMEOUT']
        deadline = time.time() + timeout
        
        while time.time() < deadline:
            try:
                # Intentar obtener del pool (no bloquear)
                connection_wrapper = self.pool.get_nowait()
                
                # Verificar si la conexión sigue válida
                if self._is_connection_valid(connection_wrapper):
                    # Actualizar última vez usada
                    connection_wrapper['last_used'] = time.time()
                    connection_wrapper['usage_count'] += 1
                    
                    with self.lock:
                        self.active_connections += 1
                        self.metrics['connections_reused'] += 1
                        
                        # Actualizar peak
                        if self.active_connections > self.metrics['peak_connections']:
                            self.metrics['peak_connections'] = self.active_connections
                    
                    return connection_wrapper
                else:
                    # Conexión inválida, cerrarla
                    self._close_connection(connection_wrapper)
                    
            except queue.Empty:
                # Pool vacío, crear nueva conexión si es posible
                with self.lock:
                    current_total = self.active_connections + self.pool.qsize()
                    
                    if current_total < self.config['MAX_CONNECTIONS']:
                        try:
                            conn = self._create_connection()
                            if conn:
                                connection_wrapper = {
                                    'connection': conn,
                                    'created_at': time.time(),
                                    'last_used': time.time(),
                                    'usage_count': 1
                                }
                                self.active_connections += 1
                                return connection_wrapper
                        except Exception as e:
                            self.logger.error(f"Error creando nueva conexión: {e}")
            
            # Esperar un poco antes de reintentar
            time.sleep(0.1)
        
        # Timeout alcanzado
        with self.lock:
            self.metrics['connections_timeout'] += 1
        
        raise TimeoutError(f"Connection pool timeout after {timeout} seconds")
    
    def _release_connection(self, connection_wrapper: Dict[str, Any]):
        """Devuelve una conexión al pool"""
        with self.lock:
            self.active_connections = max(0, self.active_connections - 1)
        
        # Si la conexión falló o es muy vieja, cerrarla
        if not connection_wrapper.get('success', True) or \
           self._is_connection_expired(connection_wrapper):
            self._close_connection(connection_wrapper)
            return
        
        # Rollback cualquier transacción pendiente
        try:
            connection_wrapper['connection'].rollback()
        except:
            # Si falla el rollback, cerrar la conexión
            self._close_connection(connection_wrapper)
            return
        
        # Devolver al pool si hay espacio
        try:
            self.pool.put_nowait(connection_wrapper)
            with self.lock:
                self.metrics['current_pool_size'] = self.pool.qsize()
        except queue.Full:
            # Pool lleno, cerrar conexión
            self._close_connection(connection_wrapper)
    
    def _is_connection_valid(self, connection_wrapper: Dict[str, Any]) -> bool:
        """Verifica si una conexión sigue siendo válida"""
        conn = connection_wrapper['connection']
        
        # Verificar si no ha expirado
        if self._is_connection_expired(connection_wrapper):
            return False
        
        # Test rápido de conectividad
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except:
            return False
    
    def _is_connection_expired(self, connection_wrapper: Dict[str, Any]) -> bool:
        """Verifica si una conexión ha expirado"""
        age = time.time() - connection_wrapper['created_at']
        idle_time = time.time() - connection_wrapper['last_used']
        
        # Expirar por edad o tiempo idle
        return age > 3600 or idle_time > self.config['IDLE_TIMEOUT']
    
    def _close_connection(self, connection_wrapper: Dict[str, Any]):
        """Cierra una conexión de forma segura"""
        try:
            connection_wrapper['connection'].close()
        except:
            pass
    
    def _start_health_check_thread(self):
        """Inicia thread de health check"""
        def health_check():
            while True:
                try:
                    time.sleep(self.config['HEALTH_CHECK_INTERVAL'])
                    
                    # Limpiar conexiones expiradas
                    expired_count = 0
                    temp_connections = []
                    
                    # Vaciar pool temporalmente
                    while not self.pool.empty():
                        try:
                            conn_wrapper = self.pool.get_nowait()
                            if self._is_connection_valid(conn_wrapper):
                                temp_connections.append(conn_wrapper)
                            else:
                                self._close_connection(conn_wrapper)
                                expired_count += 1
                        except queue.Empty:
                            break
                    
                    # Devolver conexiones válidas
                    for conn in temp_connections:
                        try:
                            self.pool.put_nowait(conn)
                        except queue.Full:
                            self._close_connection(conn)
                    
                    # Rellenar pool si es necesario
                    current_size = self.pool.qsize()
                    if current_size < self.config['MIN_CONNECTIONS']:
                        for i in range(self.config['MIN_CONNECTIONS'] - current_size):
                            try:
                                conn = self._create_connection()
                                if conn:
                                    self.pool.put_nowait({
                                        'connection': conn,
                                        'created_at': time.time(),
                                        'last_used': time.time(),
                                        'usage_count': 0
                                    })
                            except:
                                break
                    
                    # Detectar connection leaks
                    with self.lock:
                        current_time = time.time()
                        for thread_id, info in list(self.connection_tracking.items()):
                            if current_time - info['acquired_at'] > 300:  # 5 minutos
                                self.logger.warning(
                                    f"Possible connection leak detected: "
                                    f"Thread {thread_id}, held for {current_time - info['acquired_at']:.1f}s"
                                )
                    
                    if expired_count > 0:
                        self.logger.info(f"Health check: cleaned {expired_count} expired connections")
                    
                except Exception as e:
                    self.logger.error(f"Error in health check: {e}")
        
        thread = threading.Thread(target=health_check, daemon=True)
        thread.start()
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del pool"""
        with self.lock:
            return {
                'pool_size': self.pool.qsize(),
                'active_connections': self.active_connections,
                'total_connections': self.pool.qsize() + self.active_connections,
                'max_connections': self.config['MAX_CONNECTIONS'],
                'metrics': self.metrics.copy(),
                'circuit_breaker_state': self.circuit_breaker['state'],
                'average_wait_time': (
                    self.metrics['total_wait_time'] / self.metrics['total_requests']
                    if self.metrics['total_requests'] > 0 else 0
                )
            }
    
    def close_all_connections(self):
        """Cierra todas las conexiones del pool"""
        self.logger.info("Cerrando todas las conexiones del pool")
        
        # Cerrar conexiones en el pool
        while not self.pool.empty():
            try:
                conn_wrapper = self.pool.get_nowait()
                self._close_connection(conn_wrapper)
            except queue.Empty:
                break
        
        with self.lock:
            self.active_connections = 0
            self.metrics['current_pool_size'] = 0
    
    def _get_stack_trace(self) -> str:
        """Obtiene stack trace para debugging"""
        import traceback
        return ''.join(traceback.format_stack()[:-1])


# Instancia global del pool
db_pool = SecureConnectionPool()


# Función helper para compatibilidad
@contextmanager
def get_db_connection():
    """
    Función helper para obtener conexión del pool
    Compatible con el código existente
    """
    with db_pool.get_connection() as conn:
        yield conn
# app/database.py
import os
import time
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(dotenv_path='/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/.env')

# Detectar si estamos en modo de prueba
test_mode_value = os.getenv('TEST_MODE', 'false')
print(f"🔧 DEBUG: TEST_MODE value = '{test_mode_value}'")
TEST_MODE = test_mode_value.lower() == 'true'
print(f"🔧 DEBUG: TEST_MODE boolean = {TEST_MODE}")

# REGLA GENERAL: SIEMPRE usar SQL Server, NUNCA cambiar
print("🏢 FORZANDO uso de SQL Server - REGLA GENERAL")
if False:  # TEST_MODE desactivado permanentemente
    print("Modo de prueba activado - usando SQLite")
    from .database_test import get_db_connection
else:
    print("Modo produccion - usando SQL Server")
    import pyodbc
    
    # Configuración desde variables de entorno
    DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'local')
    
    if DATABASE_TYPE == 'local':
        SERVER = os.getenv('LOCAL_DB_SERVER', 'PASC')
        DATABASE = os.getenv('LOCAL_DB_DATABASE', 'AgenteDigitalDB')
        USERNAME = os.getenv('LOCAL_DB_USERNAME', 'app_usuario')
        PASSWORD = os.getenv('LOCAL_DB_PASSWORD', 'ClaveSegura123!')
    else:
        SERVER = os.getenv('DB_SERVER', 'PASC')
        DATABASE = os.getenv('DB_DATABASE', 'AgenteDigitalDB')
        USERNAME = os.getenv('DB_USERNAME', 'app_usuario')
        PASSWORD = os.getenv('DB_PASSWORD', 'ClaveSegura123!')
    
    # DEBUG: Mostrar configuración leída
    print(f"🔧 DEBUG CONFIGURACIÓN:")
    print(f"   SERVER: {SERVER}")
    print(f"   DATABASE: {DATABASE}")
    print(f"   USERNAME: {USERNAME}")
    print(f"   PASSWORD: {'***' if PASSWORD else 'None'}")

    def get_db_connection():
        """
        Crea y retorna una conexión a la base de datos SQL Server.
        TODAS las funciones necesarias para que NO FALLE la comunicación.
        """
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                print(f"🔧 DEBUG: Intento {attempt + 1}/{max_retries} - Conectando a {SERVER}:{DATABASE}")
                print(f"🔧 DEBUG: Usuario: {USERNAME}")
                
                # Lista de drivers disponibles para intentar
                drivers = [
                    "ODBC Driver 17 for SQL Server",
                    "ODBC Driver 18 for SQL Server", 
                    "ODBC Driver 13 for SQL Server",
                    "SQL Server Native Client 11.0",
                    "SQL Server"
                ]
                
                # Buscar driver disponible
                available_drivers = pyodbc.drivers()
                print(f"🔧 DEBUG: Drivers disponibles: {available_drivers}")
                
                selected_driver = None
                for driver in drivers:
                    if driver in available_drivers:
                        selected_driver = driver
                        print(f"✅ DEBUG: Usando driver: {selected_driver}")
                        break
                
                if not selected_driver:
                    selected_driver = drivers[0]  # Fallback
                    print(f"⚠️ DEBUG: Usando driver fallback: {selected_driver}")
                
                if USERNAME and PASSWORD:
                    # SQL Server Authentication con TODAS las opciones de compatibilidad
                    conn_str = (
                        f'DRIVER={{{selected_driver}}};'
                        f'SERVER={SERVER};'
                        f'DATABASE={DATABASE};'
                        f'UID={USERNAME};'
                        f'PWD={PASSWORD};'
                        f'Encrypt=no;'
                        f'TrustServerCertificate=yes;'
                        f'Connection Timeout=30;'
                        f'Command Timeout=60;'
                        f'LoginTimeout=30;'
                        f'MultipleActiveResultSets=true;'
                        f'Pooling=true;'
                    )
                    print(f"🔧 DEBUG: Usando SQL Server Authentication")
                else:
                    # Windows Authentication con opciones de compatibilidad
                    conn_str = (
                        f'DRIVER={{{selected_driver}}};'
                        f'SERVER={SERVER};'
                        f'DATABASE={DATABASE};'
                        f'Trusted_Connection=yes;'
                        f'Encrypt=no;'
                        f'TrustServerCertificate=yes;'
                        f'Connection Timeout=30;'
                        f'Command Timeout=60;'
                        f'LoginTimeout=30;'
                        f'MultipleActiveResultSets=true;'
                        f'Pooling=true;'
                    )
                    print(f"🔧 DEBUG: Usando Windows Authentication")
                
                # Mostrar string de conexión (ocultar password)
                safe_conn_str = conn_str.replace(PASSWORD, '***') if PASSWORD else conn_str
                print(f"🔧 DEBUG: String de conexión: {safe_conn_str}")
                
                # Intentar conexión con configuración robusta
                conn = pyodbc.connect(
                    conn_str,
                    autocommit=False,  # Control manual de transacciones
                    timeout=30
                )
                
                # Configurar la conexión para máxima compatibilidad
                # IMPORTANTE: SQL Server puede enviar caracteres en Latin-1/Windows-1252
                conn.setdecoding(pyodbc.SQL_CHAR, encoding='latin-1')
                conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16le')
                conn.setencoding(encoding='utf-8')
                
                # Test de conectividad básico
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as test")
                test_result = cursor.fetchone()
                cursor.close()
                
                if test_result and test_result[0] == 1:
                    print(f"✅ DEBUG: Conexión exitosa y test de conectividad OK!")
                    return conn
                else:
                    print(f"❌ DEBUG: Test de conectividad falló")
                    conn.close()
                    raise Exception("Test de conectividad falló")
                    
            except pyodbc.InterfaceError as e:
                print(f"❌ Error de interfaz ODBC (intento {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                    continue
                    
            except pyodbc.DatabaseError as e:
                print(f"❌ Error de base de datos (intento {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                    continue
                    
            except pyodbc.OperationalError as e:
                print(f"❌ Error operacional (intento {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                    continue
                    
            except pyodbc.Error as e:
                print(f"❌ Error ODBC general (intento {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                    continue
                    
            except Exception as e:
                print(f"❌ Error inesperado (intento {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                    continue
        
        print(f"❌ FALLO TOTAL: No se pudo conectar después de {max_retries} intentos")
        return None
    
    def execute_query_safe(query, params=None, fetch_one=False, fetch_all=True):
        """
        Ejecuta una consulta de forma segura con manejo de errores completo.
        """
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn:
                print("❌ No se pudo obtener conexión para execute_query_safe")
                return None
            
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                result = cursor.rowcount
            
            conn.commit()
            print(f"✅ Consulta ejecutada exitosamente")
            return result
            
        except pyodbc.Error as e:
            print(f"❌ Error ejecutando consulta: {e}")
            if conn:
                conn.rollback()
            return None
        except Exception as e:
            print(f"❌ Error inesperado en consulta: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def test_table_exists(table_name):
        """
        Verifica si una tabla existe en la base de datos.
        """
        try:
            query = """
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = ?
            """
            result = execute_query_safe(query, (table_name,), fetch_one=True)
            exists = result and result[0] > 0
            print(f"🔍 Tabla '{table_name}' {'existe' if exists else 'NO existe'}")
            return exists
        except Exception as e:
            print(f"❌ Error verificando tabla {table_name}: {e}")
            return False
    
    def get_table_columns(table_name):
        """
        Obtiene las columnas de una tabla para verificación.
        """
        try:
            query = """
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """
            result = execute_query_safe(query, (table_name,), fetch_all=True)
            if result:
                columns = [{"name": row[0], "type": row[1], "nullable": row[2], "default": row[3]} for row in result]
                print(f"📋 Tabla '{table_name}' tiene {len(columns)} columnas")
                return columns
            return []
        except Exception as e:
            print(f"❌ Error obteniendo columnas de {table_name}: {e}")
            return []

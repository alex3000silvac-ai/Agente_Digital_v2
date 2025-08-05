 # app/database.py
import pyodbc

# Tus datos de conexión validados
SERVER = 'localhost'
DATABASE = 'AgenteDigitalDB'

def get_db_connection():
    """Crea y retorna una conexión a la base de datos SQL Server usando Autenticación de Windows."""
    try:
        conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={SERVER};'
            f'DATABASE={DATABASE};'
            f'Trusted_Connection=yes;'
            f'Encrypt=yes;'
            f'TrustServerCertificate=yes;'
        )
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

import pyodbc
from werkzeug.security import check_password_hash

# --- PARÁMETROS DE PRUEBA ---
# Asegúrate de que esta sea la contraseña en texto plano correcta
PASSWORD_A_VERIFICAR = 'admin123' 
EMAIL_A_BUSCAR = 'admin@demo.cl'

# --- LÓGICA DE CONEXIÓN (Copiada de tu database.py) ---
SERVER = 'localhost'
DATABASE = 'AgenteDigitalDB'

def get_db_connection_for_test():
    """Crea una conexión usando la misma configuración que tu app."""
    try:
        conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={SERVER};'
            f'DATABASE={DATABASE};'
            f'Trusted_Connection=yes;'
            f'Encrypt=yes;'
            f'TrustServerCertificate=yes;'
        )
        # autocommit=True para que las lecturas no queden en una transacción abierta
        return pyodbc.connect(conn_str, autocommit=True)
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

# --- SCRIPT DE DIAGNÓSTICO ---
print("--- Iniciando diagnóstico final ---")
conn = get_db_connection_for_test()

if conn:
    try:
        cursor = conn.cursor()
        print(f"\n[Paso 1] Buscando usuario: '{EMAIL_A_BUSCAR}'...")

        # Usamos la consulta correcta con el parámetro como tupla
        cursor.execute("SELECT PasswordHash FROM Usuarios WHERE Email = ?", (EMAIL_A_BUSCAR,))
        user_row = cursor.fetchone()

        if not user_row:
            print("   -> ❌ RESULTADO: Usuario NO ENCONTRADO en la base de datos.")
        else:
            stored_hash = user_row.PasswordHash
            print("   -> ✅ Usuario encontrado.")
            print(f"   -> Hash en BD: {stored_hash}")

            print(f"\n[Paso 2] Comparando con la contraseña: '{PASSWORD_A_VERIFICAR}'...")
            es_valido = check_password_hash(stored_hash, PASSWORD_A_VERIFICAR)

            if es_valido:
                print("\n   -> ✅✅✅ RESULTADO FINAL: ¡LA CONTRASEÑA Y EL HASH COINCIDEN!")
            else:
                print("\n   -> ❌❌❌ RESULTADO FINAL: LA CONTRASEÑA Y EL HASH NO COINCIDEN.")

    except Exception as e:
        print(f"Ocurrió un error durante la consulta: {e}")
    finally:
        conn.close()
        print("\n--- Diagnóstico finalizado. ---")
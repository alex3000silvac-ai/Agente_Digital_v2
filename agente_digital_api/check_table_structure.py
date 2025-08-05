#!/usr/bin/env python3
"""
Script para verificar la estructura de la tabla TAXONOMIA_INCIDENTES
"""

import pyodbc
import sys

# Configuración de la base de datos
DB_CONFIG = {
    'driver': 'ODBC Driver 17 for SQL Server',
    'server': 'localhost',
    'database': 'AgenteDigitalDB',
    'trusted_connection': 'yes'
}

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        conn_str = f"DRIVER={{{DB_CONFIG['driver']}}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};TRUSTED_CONNECTION={DB_CONFIG['trusted_connection']}"
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

def main():
    conn = get_db_connection()
    if not conn:
        print("ERROR: No se pudo conectar a la base de datos")
        sys.exit(1)
    
    try:
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sys.tables WHERE name = 'TAXONOMIA_INCIDENTES'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("Tabla TAXONOMIA_INCIDENTES existe")
            
            # Obtener estructura de la tabla
            cursor.execute("""
                SELECT 
                    COLUMN_NAME, 
                    DATA_TYPE, 
                    IS_NULLABLE,
                    CHARACTER_MAXIMUM_LENGTH
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'TAXONOMIA_INCIDENTES'
                ORDER BY ORDINAL_POSITION
            """)
            
            columns = cursor.fetchall()
            print("Estructura de la tabla:")
            for col in columns:
                print(f"  - {col[0]} ({col[1]}) - Nullable: {col[2]} - Max Length: {col[3]}")
            
            # Verificar cantidad de datos
            cursor.execute("SELECT COUNT(*) FROM TAXONOMIA_INCIDENTES")
            count = cursor.fetchone()[0]
            print(f"Cantidad de registros: {count}")
            
            if count > 0:
                # Mostrar algunos ejemplos
                cursor.execute("SELECT TOP 3 * FROM TAXONOMIA_INCIDENTES")
                rows = cursor.fetchall()
                columns = [column[0] for column in cursor.description]
                print("Ejemplos de datos:")
                for row in rows:
                    print("  " + str(dict(zip(columns, row))))
        else:
            print("La tabla TAXONOMIA_INCIDENTES NO existe")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
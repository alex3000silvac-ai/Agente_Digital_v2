#!/usr/bin/env python3
"""
Script para verificar el nombre correcto de la columna de tamaño
"""

import pyodbc

# Configuración de la base de datos
DB_CONFIG = {
    'driver': 'ODBC Driver 17 for SQL Server',
    'server': '192.168.100.125',
    'database': 'AgenteDigitalDB',
    'username': 'app_usuario',
    'password': 'ClaveSegura123!'
}

def verificar_columna():
    """Verificar columnas de EvidenciasCumplimiento"""
    try:
        conn_str = f"DRIVER={{{DB_CONFIG['driver']}}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']};Encrypt=no;TrustServerCertificate=yes"
        conn = pyodbc.connect(conn_str)
        conn.setdecoding(pyodbc.SQL_CHAR, encoding='latin-1')
        conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16le')
        conn.setencoding(encoding='utf-8')
        
        cursor = conn.cursor()
        
        # Verificar si existe la tabla
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'EvidenciasCumplimiento'
        """)
        
        if not cursor.fetchone():
            print("La tabla EvidenciasCumplimiento NO existe")
            return
            
        print("Columnas de la tabla EvidenciasCumplimiento:")
        print("=" * 60)
        
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'EvidenciasCumplimiento'
            ORDER BY ORDINAL_POSITION
        """)
        
        for row in cursor.fetchall():
            col_name = row.COLUMN_NAME
            data_type = row.DATA_TYPE
            max_len = row.CHARACTER_MAXIMUM_LENGTH
            nullable = row.IS_NULLABLE
            
            type_info = data_type
            if max_len:
                type_info += f"({max_len})"
                
            print(f"{col_name:<30} {type_info:<20} {nullable}")
            
            # Verificar específicamente columnas con "tam" o "size"
            if 'tam' in col_name.lower() or 'size' in col_name.lower():
                print(f"   ⚠️ COLUMNA DE TAMAÑO ENCONTRADA: {col_name}")
            
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    verificar_columna()
#!/usr/bin/env python3
"""
Script para verificar la estructura de la tabla EvidenciasCumplimiento
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

def verificar_estructura():
    """Verificar columnas de la tabla EvidenciasCumplimiento"""
    try:
        conn_str = f"DRIVER={{{DB_CONFIG['driver']}}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']};Encrypt=no;TrustServerCertificate=yes"
        conn = pyodbc.connect(conn_str)
        conn.setdecoding(pyodbc.SQL_CHAR, encoding='latin-1')
        conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16le')
        conn.setencoding(encoding='utf-8')
        
        cursor = conn.cursor()
        
        print("=" * 80)
        print("ESTRUCTURA DE LA TABLA EvidenciasCumplimiento")
        print("=" * 80)
        
        # Obtener todas las columnas
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'EvidenciasCumplimiento'
            ORDER BY ORDINAL_POSITION
        """)
        
        columns = cursor.fetchall()
        if columns:
            print(f"\nTotal de columnas: {len(columns)}\n")
            print(f"{'Columna':<30} {'Tipo':<15} {'Tamaño':<10} {'Nullable':<10} {'Default':<20}")
            print("-" * 85)
            
            for col in columns:
                col_name = col.COLUMN_NAME
                data_type = col.DATA_TYPE
                max_length = col.CHARACTER_MAXIMUM_LENGTH or ''
                is_nullable = col.IS_NULLABLE
                default = col.COLUMN_DEFAULT or ''
                
                # Marcar columnas importantes
                marker = ""
                if col_name in ['IPAddress', 'UserAgent']:
                    marker = " ⚠️"
                elif col_name in ['CumplimientoID', 'NombreArchivoOriginal', 'RutaArchivo']:
                    marker = " ✅"
                
                print(f"{col_name:<30} {data_type:<15} {str(max_length):<10} {is_nullable:<10} {str(default):<20}{marker}")
                
            # Verificar columnas específicas
            print("\n" + "=" * 80)
            print("VERIFICACIÓN DE COLUMNAS PROBLEMÁTICAS")
            print("=" * 80)
            
            column_names = [col.COLUMN_NAME for col in columns]
            
            problematic_columns = ['IPAddress', 'UserAgent']
            for col in problematic_columns:
                if col in column_names:
                    print(f"✅ Columna '{col}' EXISTE")
                else:
                    print(f"❌ Columna '{col}' NO EXISTE")
                    
            # Mostrar columnas requeridas mínimas
            print("\n" + "=" * 80)
            print("COLUMNAS MÍNIMAS REQUERIDAS")
            print("=" * 80)
            
            required_columns = [
                'CumplimientoID',
                'NombreArchivoOriginal', 
                'NombreArchivoAlmacenado',
                'RutaArchivo',
                'TipoArchivo',
                'TamanoArchivoKB',
                'FechaSubida'
            ]
            
            for col in required_columns:
                if col in column_names:
                    print(f"✅ {col}")
                else:
                    print(f"❌ {col} - FALTA!")
                    
        else:
            print("❌ La tabla EvidenciasCumplimiento no existe o no tiene columnas")
            
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    verificar_estructura()
#!/usr/bin/env python3
"""
Script para probar la corrección de codificación
"""

import pyodbc
from datetime import datetime

# Configuración de la base de datos
DB_CONFIG = {
    'driver': 'ODBC Driver 17 for SQL Server',
    'server': '192.168.100.125',
    'database': 'AgenteDigitalDB',
    'username': 'app_usuario',
    'password': 'ClaveSegura123!'
}

def test_conexion_con_codificacion():
    """Probar conexión con configuración de codificación corregida"""
    
    print("=" * 80)
    print("PRUEBA DE CONEXIÓN CON CODIFICACIÓN CORREGIDA")
    print("=" * 80)
    
    try:
        # Crear conexión
        conn_str = f"DRIVER={{{DB_CONFIG['driver']}}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']};Encrypt=no;TrustServerCertificate=yes"
        conn = pyodbc.connect(conn_str)
        
        # Configurar codificación (como en el fix)
        conn.setdecoding(pyodbc.SQL_CHAR, encoding='latin-1')
        conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16le')
        conn.setencoding(encoding='utf-8')
        
        cursor = conn.cursor()
        
        # Probar query problemática
        cursor.execute("""
            SELECT TOP 5 ObligacionID, ArticuloNorma, Descripcion
            FROM OBLIGACIONES 
            WHERE AplicaPara = 'PSE' OR AplicaPara = 'Ambos'
            ORDER BY ArticuloNorma
        """)
        
        print("\nResultados con codificación corregida:")
        print("-" * 80)
        
        for row in cursor.fetchall():
            print(f"\nID: {row.ObligacionID}")
            print(f"Artículo: {row.ArticuloNorma}")
            print(f"Descripción: {row.Descripcion[:50]}...")
            
            # Verificar el símbolo de grado
            if '°' in row.ArticuloNorma:
                print(f"  ✓ Símbolo ° detectado correctamente")
        
        cursor.close()
        conn.close()
        
        print("\n✅ ÉXITO: La codificación funciona correctamente")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_conexion_con_codificacion()
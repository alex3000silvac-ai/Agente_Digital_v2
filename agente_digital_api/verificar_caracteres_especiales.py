#!/usr/bin/env python3
"""
Script para verificar caracteres especiales en las obligaciones
"""

import pyodbc
import sys
from datetime import datetime

# Configuración de la base de datos
DB_CONFIG = {
    'driver': 'ODBC Driver 17 for SQL Server',
    'server': '192.168.100.125',
    'database': 'AgenteDigitalDB',
    'username': 'app_usuario',
    'password': 'ClaveSegura123!'
}

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        conn_str = f"DRIVER={{{DB_CONFIG['driver']}}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']};Encrypt=no;TrustServerCertificate=yes"
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

def verificar_caracteres():
    """Verificar caracteres especiales en obligaciones"""
    conn = get_db_connection()
    if not conn:
        print("ERROR: No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor()
        
        print("=" * 80)
        print("VERIFICANDO CARACTERES ESPECIALES EN OBLIGACIONES PSE")
        print("=" * 80)
        
        # Obtener obligaciones para PSE
        cursor.execute("""
            SELECT ObligacionID, ArticuloNorma, Descripcion, MedioDeVerificacionSugerido
            FROM OBLIGACIONES 
            WHERE AplicaPara = 'PSE' OR AplicaPara = 'Ambos'
            ORDER BY ArticuloNorma
        """)
        
        problematic_count = 0
        for row in cursor.fetchall():
            problematic_fields = []
            
            # Verificar cada campo
            for field_name, value in [
                ('ObligacionID', row.ObligacionID),
                ('ArticuloNorma', row.ArticuloNorma),
                ('Descripcion', row.Descripcion),
                ('MedioDeVerificacionSugerido', row.MedioDeVerificacionSugerido)
            ]:
                if value:
                    try:
                        # Intentar decodificar si es bytes
                        if isinstance(value, bytes):
                            value.decode('utf-8')
                        else:
                            # Si es string, verificar que no tenga caracteres problemáticos
                            str(value).encode('utf-8')
                    except Exception as e:
                        problematic_fields.append((field_name, value, str(e)))
            
            if problematic_fields:
                problematic_count += 1
                print(f"\n⚠️ Obligación {row.ObligacionID} tiene caracteres problemáticos:")
                for field_name, value, error in problematic_fields:
                    print(f"   Campo: {field_name}")
                    print(f"   Valor: {repr(value)}")
                    print(f"   Error: {error}")
                    
                    # Mostrar bytes si es posible
                    if isinstance(value, str):
                        print(f"   Bytes: {value.encode('latin-1', errors='ignore')}")
        
        if problematic_count == 0:
            print("\n✅ No se encontraron caracteres problemáticos en las obligaciones PSE")
        else:
            print(f"\n❌ Se encontraron {problematic_count} obligaciones con caracteres problemáticos")
        
        # Verificar específicamente ArticuloNorma
        print("\n" + "-" * 80)
        print("ANALIZANDO CAMPO ArticuloNorma:")
        cursor.execute("""
            SELECT DISTINCT ArticuloNorma
            FROM OBLIGACIONES 
            WHERE AplicaPara = 'PSE' OR AplicaPara = 'Ambos'
            ORDER BY ArticuloNorma
        """)
        
        for row in cursor.fetchall():
            articulo = row.ArticuloNorma
            print(f"\nArtículo: {repr(articulo)}")
            if articulo:
                # Mostrar cada carácter
                for i, char in enumerate(str(articulo)):
                    try:
                        print(f"  Pos {i}: '{char}' (Unicode: U+{ord(char):04X})")
                    except:
                        print(f"  Pos {i}: Carácter problemático")
                        
    except Exception as e:
        print(f"Error durante verificación: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == '__main__':
    verificar_caracteres()
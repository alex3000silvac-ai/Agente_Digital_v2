#!/usr/bin/env python3
"""
Script para verificar la codificación de los datos en la tabla Obligaciones
"""
import pyodbc
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import get_db_connection

def verificar_encoding():
    """Verifica los datos de obligaciones y su codificación"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("VERIFICANDO CODIFICACIÓN EN TABLA OBLIGACIONES")
        print("="*70 + "\n")
        
        # Buscar registros que contengan caracteres especiales
        cursor.execute("""
            SELECT TOP 10
                ObligacionID,
                ArticuloNorma,
                Descripcion,
                MedioDeVerificacionSugerido
            FROM Obligaciones
            WHERE Descripcion LIKE '%ción%' 
               OR Descripcion LIKE '%ñ%'
               OR MedioDeVerificacionSugerido LIKE '%ción%'
               OR MedioDeVerificacionSugerido LIKE '%ñ%'
            ORDER BY ObligacionID
        """)
        
        registros = cursor.fetchall()
        
        if registros:
            print(f"✅ Se encontraron {len(registros)} registros con caracteres especiales:\n")
            
            for idx, row in enumerate(registros, 1):
                print(f"{idx}. ObligacionID: {row[0]}")
                print(f"   Artículo: {row[1]}")
                print(f"   Descripción: {row[2][:100]}...")
                if row[3]:
                    print(f"   Medio Verificación: {row[3][:80]}...")
                print()
                
                # Verificar bytes
                desc_bytes = row[2].encode('utf-8')
                print(f"   [DEBUG] Primeros bytes de descripción: {desc_bytes[:50]}")
                print()
        else:
            print("❌ No se encontraron registros con 'ción' o 'ñ'")
            
        # Verificar un registro específico
        print("\n" + "="*70)
        print("VERIFICANDO REGISTRO ESPECÍFICO")
        print("="*70 + "\n")
        
        cursor.execute("""
            SELECT TOP 1
                ObligacionID,
                Descripcion
            FROM Obligaciones
            WHERE ObligacionID > 0
            ORDER BY ObligacionID
        """)
        
        row = cursor.fetchone()
        if row:
            print(f"ObligacionID: {row[0]}")
            print(f"Descripción: {row[1]}")
            print(f"Longitud: {len(row[1])} caracteres")
            
            # Analizar caracteres
            for i, char in enumerate(row[1][:50]):
                if ord(char) > 127:
                    print(f"  - Posición {i}: '{char}' (Unicode: U+{ord(char):04X})")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verificar_encoding()
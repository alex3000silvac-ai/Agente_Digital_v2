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
        
        # Primero ver algunos registros
        cursor.execute("""
            SELECT TOP 5
                ObligacionID,
                ArticuloNorma,
                Descripcion,
                MedioDeVerificacionSugerido
            FROM Obligaciones
            ORDER BY ObligacionID
        """)
        
        registros = cursor.fetchall()
        
        print(f"✅ Primeros {len(registros)} registros:\n")
        
        for idx, row in enumerate(registros, 1):
            print(f"{idx}. ObligacionID: {row[0]}")
            print(f"   Artículo: {row[1]}")
            desc = row[2] if row[2] else "Sin descripción"
            print(f"   Descripción: {desc[:80]}...")
            
            # Buscar caracteres problemáticos
            problemas = []
            for i, char in enumerate(desc):
                if char == 'Ã':
                    if i+1 < len(desc):
                        next_char = desc[i+1]
                        problemas.append(f"Posición {i}: 'Ã{next_char}' (probablemente UTF-8 mal interpretado)")
            
            if problemas:
                print("   ⚠️  PROBLEMAS DE CODIFICACIÓN DETECTADOS:")
                for p in problemas:
                    print(f"      - {p}")
            
            if row[3]:
                medio = row[3]
                print(f"   Medio Verificación: {medio[:60]}...")
                
                # Buscar problemas en medio de verificación
                for i, char in enumerate(medio):
                    if char == 'Ã':
                        if i+1 < len(medio):
                            next_char = medio[i+1]
                            print(f"      ⚠️  Problema en posición {i}: 'Ã{next_char}'")
            print()
        
        # Buscar específicamente registros con problemas de codificación
        print("\n" + "="*70)
        print("BUSCANDO REGISTROS CON PROBLEMAS DE CODIFICACIÓN")
        print("="*70 + "\n")
        
        cursor.execute("""
            SELECT TOP 10
                ObligacionID,
                Descripcion
            FROM Obligaciones
            WHERE Descripcion LIKE '%Ã%'
               OR MedioDeVerificacionSugerido LIKE '%Ã%'
        """)
        
        problematicos = cursor.fetchall()
        
        if problematicos:
            print(f"⚠️  Se encontraron {len(problematicos)} registros con posibles problemas:\n")
            
            for row in problematicos:
                print(f"ObligacionID: {row[0]}")
                desc = row[1]
                print(f"Descripción con problema: {desc[:100]}...")
                
                # Intentar decodificar
                try:
                    # Si el texto fue guardado como UTF-8 pero interpretado como Latin-1
                    desc_bytes = desc.encode('latin-1')
                    desc_corregido = desc_bytes.decode('utf-8')
                    print(f"✅ Descripción corregida: {desc_corregido[:100]}...")
                except:
                    print("❌ No se pudo corregir automáticamente")
                print()
        else:
            print("✅ No se encontraron registros con el patrón 'Ã' (típico de problemas UTF-8)")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verificar_encoding()
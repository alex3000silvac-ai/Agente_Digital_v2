#!/usr/bin/env python3
"""
Script para buscar el registro específico con problemas de codificación
"""
import pyodbc
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import get_db_connection

def buscar_registro_corrupto():
    """Busca el registro específico DS 295, ART.10"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("BUSCANDO REGISTRO DS 295, ART.10")
        print("="*70 + "\n")
        
        # Buscar por ArticuloNorma que contenga "295" y "10"
        cursor.execute("""
            SELECT 
                ObligacionID,
                ArticuloNorma,
                Descripcion,
                MedioDeVerificacionSugerido,
                AplicaPara
            FROM Obligaciones
            WHERE ArticuloNorma LIKE '%295%' 
               OR ArticuloNorma LIKE '%ART.10%'
               OR ArticuloNorma LIKE '%Art. 10%'
            ORDER BY ObligacionID
        """)
        
        registros = cursor.fetchall()
        
        if registros:
            print(f"✅ Se encontraron {len(registros)} registros relacionados:\n")
            
            for idx, row in enumerate(registros, 1):
                print(f"{idx}. ObligacionID: {row[0]}")
                print(f"   Artículo: {row[1]}")
                print(f"   Descripción: {row[2][:100]}...")
                
                # Buscar "ejecuciÃ³n" específicamente
                desc = row[2] if row[2] else ""
                if "ejecuciÃ³n" in desc:
                    print(f"   🎯 ENCONTRADO PROBLEMA: contiene 'ejecuciÃ³n'")
                    
                    # Mostrar contexto alrededor del problema
                    pos = desc.find("ejecuciÃ³n")
                    if pos >= 0:
                        inicio = max(0, pos - 30)
                        fin = min(len(desc), pos + 40)
                        contexto = desc[inicio:fin]
                        print(f"   📍 Contexto: ...{contexto}...")
                        
                        # Intentar corregir
                        desc_corregido = desc.replace("ejecuciÃ³n", "ejecución")
                        contexto_corregido = desc_corregido[inicio:fin]
                        print(f"   ✅ Corregido: ...{contexto_corregido}...")
                
                if row[3]:  # MedioDeVerificacionSugerido
                    medio = row[3]
                    if "ejecuciÃ³n" in medio:
                        print(f"   🎯 PROBLEMA EN MEDIO DE VERIFICACIÓN: contiene 'ejecuciÃ³n'")
                
                print(f"   Aplica para: {row[4]}")
                print()
        else:
            print("❌ No se encontraron registros con DS 295 o ART.10")
            
        # Buscar todos los registros con problemas de codificación
        print("\n" + "="*70)
        print("BUSCANDO TODOS LOS REGISTROS CON PROBLEMAS DE CODIFICACIÓN")
        print("="*70 + "\n")
        
        # Patrones comunes de codificación incorrecta
        patrones = ["ciÃ³n", "aciÃ³n", "siÃ³n", "Ã¡", "Ã©", "Ã­", "Ã³", "Ãº", "Ã±"]
        
        for patron in patrones:
            cursor.execute("""
                SELECT 
                    ObligacionID,
                    ArticuloNorma,
                    Descripcion
                FROM Obligaciones
                WHERE Descripcion LIKE ? OR MedioDeVerificacionSugerido LIKE ?
            """, (f'%{patron}%', f'%{patron}%'))
            
            resultados = cursor.fetchall()
            
            if resultados:
                print(f"🔍 Patrón '{patron}' encontrado en {len(resultados)} registros:")
                for row in resultados:
                    print(f"   - {row[0]}: {row[1]}")
                    # Mostrar fragmento con el problema
                    desc = row[2]
                    pos = desc.find(patron)
                    if pos >= 0:
                        inicio = max(0, pos - 20)
                        fin = min(len(desc), pos + 30)
                        fragmento = desc[inicio:fin]
                        print(f"     Fragmento: ...{fragmento}...")
                print()
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    buscar_registro_corrupto()
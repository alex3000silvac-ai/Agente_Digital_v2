#!/usr/bin/env python3
"""
Script para verificar específicamente la evidencia ID 31
"""
import pyodbc
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import get_db_connection

def verificar_evidencia_31():
    """Verifica específicamente la evidencia ID 31"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("VERIFICANDO EVIDENCIA ID 31 ESPECÍFICAMENTE")
        print("="*70 + "\n")
        
        # Consultar la evidencia específica
        cursor.execute("""
            SELECT 
                EvidenciaID,
                CumplimientoID,
                NombreArchivoOriginal,
                Descripcion,
                FechaSubida,
                UsuarioQueSubio
            FROM EvidenciasCumplimiento
            WHERE EvidenciaID = 31
        """)
        
        evidencia = cursor.fetchone()
        
        if evidencia:
            print(f"✅ Evidencia encontrada:")
            print(f"   EvidenciaID: {evidencia[0]}")
            print(f"   CumplimientoID: {evidencia[1]}")
            print(f"   NombreArchivo: {evidencia[2]}")
            print(f"   Descripcion: '{evidencia[3]}'")
            print(f"   FechaSubida: {evidencia[4]}")
            print(f"   Usuario: {evidencia[5]}")
            
            # Analizar la descripción byte por byte
            descripcion = evidencia[3] or ""
            print(f"\n🔍 ANÁLISIS DETALLADO DE LA DESCRIPCIÓN:")
            print(f"   Longitud: {len(descripcion)} caracteres")
            
            # Mostrar caracteres especiales
            caracteres_especiales = []
            for i, char in enumerate(descripcion):
                if ord(char) > 127:
                    caracteres_especiales.append((i, char, ord(char)))
            
            if caracteres_especiales:
                print(f"   Caracteres especiales encontrados:")
                for pos, char, code in caracteres_especiales:
                    print(f"     Posición {pos}: '{char}' (Unicode: U+{code:04X})")
            else:
                print(f"   ✅ No se encontraron caracteres especiales (>127)")
            
            # Buscar patrones problemáticos
            patrones = ['Ã³', 'Ã¡', 'Ã©', 'Ã­', 'Ãº', 'Ã±', 'ejecuciÃ³n']
            for patron in patrones:
                if patron in descripcion:
                    print(f"   🎯 PATRÓN PROBLEMÁTICO ENCONTRADO: '{patron}'")
                    pos = descripcion.find(patron)
                    print(f"      Posición: {pos}")
                    contexto_inicio = max(0, pos - 10)
                    contexto_fin = min(len(descripcion), pos + 20)
                    contexto = descripcion[contexto_inicio:contexto_fin]
                    print(f"      Contexto: '{contexto}'")
            
            # Intentar diferentes correcciones
            if 'ejecuciÃ³n' in descripcion:
                descripcion_corregida = descripcion.replace('ejecuciÃ³n', 'ejecución')
                print(f"\n✅ CORRECCIÓN PROPUESTA:")
                print(f"   Antes: {descripcion}")
                print(f"   Después: {descripcion_corregida}")
                
                print(f"\n📝 SQL para corregir:")
                print(f"   UPDATE EvidenciasCumplimiento SET Descripcion = '{descripcion_corregida}' WHERE EvidenciaID = 31;")
                
                # Aplicar corrección
                print(f"\n❓ ¿Aplicar corrección? (y/N): ", end="")
                respuesta = input().strip().lower()
                
                if respuesta == 'y':
                    cursor.execute("UPDATE EvidenciasCumplimiento SET Descripcion = ? WHERE EvidenciaID = 31", 
                                 (descripcion_corregida,))
                    conn.commit()
                    print(f"✅ Corrección aplicada exitosamente")
                else:
                    print(f"💾 Corrección NO aplicada")
            
        else:
            print("❌ No se encontró la evidencia ID 31")
            
        # Buscar todas las evidencias que contengan texto similar
        print(f"\n" + "="*70)
        print("BUSCANDO OTRAS EVIDENCIAS CON PROBLEMAS SIMILARES")
        print("="*70 + "\n")
        
        cursor.execute("""
            SELECT 
                EvidenciaID,
                Descripcion
            FROM EvidenciasCumplimiento
            WHERE Descripcion LIKE '%Desarrollo%'
               OR Descripcion LIKE '%ejecuci%'
               OR Descripcion LIKE '%proceso%'
            ORDER BY FechaSubida DESC
        """)
        
        evidencias_similares = cursor.fetchall()
        
        if evidencias_similares:
            print(f"✅ Encontradas {len(evidencias_similares)} evidencias con texto similar:")
            for ev in evidencias_similares:
                print(f"   EvidenciaID {ev[0]}: {ev[1]}")
        else:
            print("❌ No se encontraron evidencias con texto similar")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verificar_evidencia_31()
#!/usr/bin/env python3
"""
Script para buscar archivos con problemas de codificación en evidencias
"""
import pyodbc
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import get_db_connection

def buscar_archivos_corruptos():
    """Busca archivos con nombres corruptos en las tablas de evidencias"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("BUSCANDO ARCHIVOS CON PROBLEMAS DE CODIFICACIÓN")
        print("="*70 + "\n")
        
        # Buscar en tabla CumplimientoEvidencias
        print("1. TABLA CumplimientoEvidencias:")
        print("-" * 40)
        
        try:
            cursor.execute("""
                SELECT 
                    EvidenciaID,
                    CumplimientoID,
                    NombreArchivo,
                    Descripcion
                FROM CumplimientoEvidencias
                WHERE NombreArchivo LIKE '%ejecuci%'
                   OR NombreArchivo LIKE '%Ã%'
                   OR Descripcion LIKE '%Ã%'
                ORDER BY EvidenciaID DESC
            """)
            
            evidencias = cursor.fetchall()
            
            if evidencias:
                print(f"✅ Encontrados {len(evidencias)} archivos con problemas:\n")
                
                for row in evidencias:
                    print(f"EvidenciaID: {row[0]}")
                    print(f"CumplimientoID: {row[1]}")
                    print(f"❌ Nombre corrupto: {row[2]}")
                    
                    # Intentar corregir el nombre
                    nombre_original = row[2]
                    nombre_corregido = nombre_original
                    
                    # Correcciones comunes
                    correcciones = {
                        'ejecuciÃ³n': 'ejecución',
                        'aplicaciÃ³n': 'aplicación',
                        'soluciÃ³n': 'solución',
                        'informaciÃ³n': 'información',
                        'verificaciÃ³n': 'verificación',
                        'implementaciÃ³n': 'implementación',
                        'Ã¡': 'á',
                        'Ã©': 'é',
                        'Ã­': 'í',
                        'Ã³': 'ó',
                        'Ãº': 'ú',
                        'Ã±': 'ñ'
                    }
                    
                    for corrupto, correcto in correcciones.items():
                        nombre_corregido = nombre_corregido.replace(corrupto, correcto)
                    
                    if nombre_corregido != nombre_original:
                        print(f"✅ Nombre corregido: {nombre_corregido}")
                        
                        # Preparar query de actualización
                        print(f"📝 SQL para corregir:")
                        print(f"UPDATE CumplimientoEvidencias SET NombreArchivo = '{nombre_corregido}' WHERE EvidenciaID = {row[0]};")
                    
                    if row[3] and 'Ã' in row[3]:
                        desc_corregida = row[3]
                        for corrupto, correcto in correcciones.items():
                            desc_corregida = desc_corregida.replace(corrupto, correcto)
                        
                        if desc_corregida != row[3]:
                            print(f"✅ Descripción corregida: {desc_corregida}")
                            print(f"📝 SQL para descripción:")
                            print(f"UPDATE CumplimientoEvidencias SET Descripcion = '{desc_corregida}' WHERE EvidenciaID = {row[0]};")
                    
                    print("-" * 60)
            else:
                print("✅ No se encontraron archivos con problemas en CumplimientoEvidencias")
                
        except Exception as e:
            print(f"❌ Error consultando CumplimientoEvidencias: {e}")
        
        # Buscar en EvidenciasIncidentes
        print("\n2. TABLA EvidenciasIncidentes:")
        print("-" * 40)
        
        try:
            cursor.execute("""
                SELECT 
                    EvidenciaID,
                    IncidenteID,
                    NombreArchivo,
                    Descripcion
                FROM EvidenciasIncidentes
                WHERE NombreArchivo LIKE '%ejecuci%'
                   OR NombreArchivo LIKE '%Ã%'
                   OR Descripcion LIKE '%Ã%'
                ORDER BY EvidenciaID DESC
            """)
            
            evidencias_inc = cursor.fetchall()
            
            if evidencias_inc:
                print(f"✅ Encontrados {len(evidencias_inc)} archivos con problemas:\n")
                
                for row in evidencias_inc:
                    print(f"EvidenciaID: {row[0]}")
                    print(f"IncidenteID: {row[1]}")
                    print(f"❌ Nombre corrupto: {row[2]}")
                    # Similar procesamiento que arriba...
            else:
                print("✅ No se encontraron archivos con problemas en EvidenciasIncidentes")
                
        except Exception as e:
            print(f"❌ Error consultando EvidenciasIncidentes: {e}")
        
        # Buscar específicamente el texto "Desarrollo ejecución"
        print("\n3. BÚSQUEDA ESPECÍFICA 'Desarrollo ejecución':")
        print("-" * 50)
        
        for tabla in ['CumplimientoEvidencias', 'EvidenciasIncidentes']:
            try:
                cursor.execute(f"""
                    SELECT 
                        *
                    FROM {tabla}
                    WHERE NombreArchivo LIKE '%Desarrollo%'
                       OR NombreArchivo LIKE '%proceso%'
                       OR Descripcion LIKE '%Desarrollo%'
                """)
                
                resultados = cursor.fetchall()
                columnas = [desc[0] for desc in cursor.description]
                
                if resultados:
                    print(f"\n📁 {tabla} - {len(resultados)} registros:")
                    for row in resultados:
                        row_dict = dict(zip(columnas, row))
                        print(f"   ID: {row_dict.get('EvidenciaID')}")
                        print(f"   Archivo: {row_dict.get('NombreArchivo')}")
                        if 'Ã' in str(row_dict.get('NombreArchivo', '')):
                            print(f"   🎯 ARCHIVO CORRUPTO ENCONTRADO!")
                        print()
                
            except Exception as e:
                print(f"❌ Error en {tabla}: {e}")
            
    except Exception as e:
        print(f"\n❌ Error general: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    buscar_archivos_corruptos()
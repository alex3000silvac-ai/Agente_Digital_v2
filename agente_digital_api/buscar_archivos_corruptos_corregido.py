#!/usr/bin/env python3
"""
Script para buscar archivos con problemas de codificación en evidencias (nombres correctos de tabla)
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
        
        # Buscar en tabla EvidenciasCumplimiento
        print("1. TABLA EvidenciasCumplimiento:")
        print("-" * 40)
        
        try:
            # Primero verificar estructura de la tabla
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'EvidenciasCumplimiento'
                ORDER BY ORDINAL_POSITION
            """)
            
            columnas = cursor.fetchall()
            print("Columnas disponibles:")
            for col in columnas:
                print(f"  - {col[0]} ({col[1]})")
            print()
            
            # Buscar registros con problemas
            cursor.execute("""
                SELECT TOP 20 *
                FROM EvidenciasCumplimiento
                WHERE NombreArchivo LIKE '%ejecuci%'
                   OR NombreArchivo LIKE '%Ã%'
                   OR Descripcion LIKE '%Ã%'
                   OR NombreArchivo LIKE '%Desarrollo%'
                ORDER BY FechaSubida DESC
            """)
            
            evidencias = cursor.fetchall()
            columnas_datos = [desc[0] for desc in cursor.description]
            
            if evidencias:
                print(f"🎯 ENCONTRADOS {len(evidencias)} archivos con posibles problemas:\n")
                
                for idx, row in enumerate(evidencias, 1):
                    row_dict = dict(zip(columnas_datos, row))
                    
                    print(f"{idx}. EvidenciaID: {row_dict.get('EvidenciaID')}")
                    print(f"   CumplimientoID: {row_dict.get('CumplimientoID')}")
                    
                    nombre_archivo = row_dict.get('NombreArchivo', '')
                    print(f"   Nombre archivo: {nombre_archivo}")
                    
                    # Verificar si contiene caracteres problemáticos
                    if 'Ã' in nombre_archivo:
                        print(f"   🎯 PROBLEMA DETECTADO: contiene 'Ã'")
                        
                        # Generar corrección
                        nombre_corregido = nombre_archivo
                        
                        # Correcciones comunes
                        correcciones = {
                            'ejecuciÃ³n': 'ejecución',
                            'aplicaciÃ³n': 'aplicación',
                            'soluciÃ³n': 'solución',
                            'informaciÃ³n': 'información',
                            'verificaciÃ³n': 'verificación',
                            'implementaciÃ³n': 'implementación',
                            'operaciÃ³n': 'operación',
                            'creaciÃ³n': 'creación',
                            'Ã¡': 'á',
                            'Ã©': 'é',
                            'Ã­': 'í',
                            'Ã³': 'ó',
                            'Ãº': 'ú',
                            'Ã±': 'ñ'
                        }
                        
                        for corrupto, correcto in correcciones.items():
                            nombre_corregido = nombre_corregido.replace(corrupto, correcto)
                        
                        print(f"   ✅ Corrección propuesta: {nombre_corregido}")
                        
                        if nombre_corregido != nombre_archivo:
                            print(f"   📝 SQL para corregir:")
                            print(f"   UPDATE EvidenciasCumplimiento SET NombreArchivo = '{nombre_corregido}' WHERE EvidenciaID = {row_dict.get('EvidenciaID')};")
                    
                    # Verificar descripción
                    descripcion = row_dict.get('Descripcion', '')
                    if descripcion and 'Ã' in descripcion:
                        print(f"   🎯 PROBLEMA EN DESCRIPCIÓN: {descripcion}")
                    
                    print(f"   Fecha: {row_dict.get('FechaSubida')}")
                    print("-" * 60)
            else:
                print("✅ No se encontraron archivos con problemas en EvidenciasCumplimiento")
                
        except Exception as e:
            print(f"❌ Error consultando EvidenciasCumplimiento: {e}")
        
        # Buscar en EvidenciasIncidentes también
        print("\n2. TABLA EvidenciasIncidentes:")
        print("-" * 40)
        
        try:
            cursor.execute("""
                SELECT TOP 10 *
                FROM EvidenciasIncidentes
                WHERE NombreArchivo LIKE '%Desarrollo%'
                   OR NombreArchivo LIKE '%ejecuci%'
                   OR NombreArchivo LIKE '%Ã%'
                ORDER BY FechaSubida DESC
            """)
            
            evidencias_inc = cursor.fetchall()
            columnas_inc = [desc[0] for desc in cursor.description]
            
            if evidencias_inc:
                print(f"🎯 ENCONTRADOS {len(evidencias_inc)} archivos en incidentes:\n")
                
                for row in evidencias_inc:
                    row_dict = dict(zip(columnas_inc, row))
                    print(f"EvidenciaID: {row_dict.get('EvidenciaID')}")
                    print(f"Archivo: {row_dict.get('NombreArchivo')}")
                    if 'Ã' in str(row_dict.get('NombreArchivo', '')):
                        print(f"🎯 PROBLEMA DETECTADO!")
                    print()
            else:
                print("✅ No se encontraron archivos con problemas en EvidenciasIncidentes")
                
        except Exception as e:
            print(f"❌ Error consultando EvidenciasIncidentes: {e}")
            
    except Exception as e:
        print(f"\n❌ Error general: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    buscar_archivos_corruptos()
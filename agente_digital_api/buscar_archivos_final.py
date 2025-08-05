#!/usr/bin/env python3
"""
Script para buscar y corregir archivos con problemas de codificación (versión final)
"""
import pyodbc
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import get_db_connection

def buscar_y_corregir_archivos():
    """Busca y corrige archivos con nombres corruptos"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("BUSCANDO Y CORRIGIENDO ARCHIVOS CON PROBLEMAS DE CODIFICACIÓN")
        print("="*70 + "\n")
        
        # Buscar en tabla EvidenciasCumplimiento
        print("1. TABLA EvidenciasCumplimiento:")
        print("-" * 40)
        
        try:
            # Buscar registros con problemas usando los nombres correctos de columna
            cursor.execute("""
                SELECT 
                    EvidenciaID,
                    CumplimientoID,
                    NombreArchivoOriginal,
                    Descripcion,
                    FechaSubida
                FROM EvidenciasCumplimiento
                WHERE NombreArchivoOriginal LIKE '%ejecuci%'
                   OR NombreArchivoOriginal LIKE '%Ã%'
                   OR Descripcion LIKE '%Ã%'
                   OR NombreArchivoOriginal LIKE '%Desarrollo%'
                ORDER BY FechaSubida DESC
            """)
            
            evidencias = cursor.fetchall()
            
            if evidencias:
                print(f"🎯 ENCONTRADOS {len(evidencias)} archivos con posibles problemas:\n")
                
                correcciones_sql = []
                
                for idx, row in enumerate(evidencias, 1):
                    evidencia_id = row[0]
                    cumplimiento_id = row[1]
                    nombre_original = row[2] or ""
                    descripcion = row[3] or ""
                    fecha = row[4]
                    
                    print(f"{idx}. EvidenciaID: {evidencia_id}")
                    print(f"   CumplimientoID: {cumplimiento_id}")
                    print(f"   Nombre original: {nombre_original}")
                    
                    # Verificar si contiene caracteres problemáticos
                    tiene_problema = False
                    
                    if 'Ã' in nombre_original:
                        print(f"   🎯 PROBLEMA DETECTADO en nombre: contiene 'Ã'")
                        tiene_problema = True
                        
                        # Generar corrección
                        nombre_corregido = nombre_original
                        
                        # Correcciones comunes UTF-8 mal interpretado
                        correcciones = {
                            'ejecuciÃ³n': 'ejecución',
                            'aplicaciÃ³n': 'aplicación',
                            'soluciÃ³n': 'solución',
                            'informaciÃ³n': 'información',
                            'verificaciÃ³n': 'verificación',
                            'implementaciÃ³n': 'implementación',
                            'operaciÃ³n': 'operación',
                            'creaciÃ³n': 'creación',
                            'administraciÃ³n': 'administración',
                            'documentaciÃ³n': 'documentación',
                            'autenticaciÃ³n': 'autenticación',
                            'configuraciÃ³n': 'configuración',
                            'Ã¡': 'á',
                            'Ã©': 'é',
                            'Ã­': 'í',
                            'Ã³': 'ó',
                            'Ãº': 'ú',
                            'Ã±': 'ñ',
                            'Ã¤': 'ä',
                            'Ã¼': 'ü'
                        }
                        
                        for corrupto, correcto in correcciones.items():
                            nombre_corregido = nombre_corregido.replace(corrupto, correcto)
                        
                        print(f"   ✅ Corrección propuesta: {nombre_corregido}")
                        
                        if nombre_corregido != nombre_original:
                            sql_correccion = f"UPDATE EvidenciasCumplimiento SET NombreArchivoOriginal = '{nombre_corregido}' WHERE EvidenciaID = {evidencia_id};"
                            correcciones_sql.append(sql_correccion)
                            print(f"   📝 SQL preparado para corrección")
                    
                    # Verificar descripción
                    if descripcion and 'Ã' in descripcion:
                        print(f"   🎯 PROBLEMA EN DESCRIPCIÓN: {descripcion[:50]}...")
                        tiene_problema = True
                        
                        desc_corregida = descripcion
                        for corrupto, correcto in correcciones.items():
                            desc_corregida = desc_corregida.replace(corrupto, correcto)
                        
                        if desc_corregida != descripcion:
                            desc_escaped = desc_corregida.replace("'", "''")
                            sql_desc = f"UPDATE EvidenciasCumplimiento SET Descripcion = '{desc_escaped}' WHERE EvidenciaID = {evidencia_id};"
                            correcciones_sql.append(sql_desc)
                            print(f"   📝 SQL preparado para descripción")
                    
                    if not tiene_problema:
                        print(f"   ✅ Archivo OK (no contiene caracteres problemáticos)")
                    
                    print(f"   Fecha: {fecha}")
                    print("-" * 60)
                
                # Mostrar resumen de correcciones
                if correcciones_sql:
                    print(f"\n📝 RESUMEN DE CORRECCIONES:")
                    print(f"Total de registros a corregir: {len(correcciones_sql)}")
                    
                    print(f"\n💾 SCRIPT SQL DE CORRECCIÓN:")
                    print("-- Script generado automáticamente para corregir caracteres UTF-8")
                    print("-- Ejecutar en SQL Server Management Studio")
                    print("BEGIN TRANSACTION;")
                    print()
                    
                    for sql in correcciones_sql:
                        print(sql)
                    
                    print()
                    print("-- Verificar cambios antes de confirmar")
                    print("-- COMMIT; -- Descomentar para aplicar cambios")
                    print("-- ROLLBACK; -- Usar para deshacer si algo sale mal")
                    
                    # Guardar en archivo
                    with open('correccion_caracteres.sql', 'w', encoding='utf-8') as f:
                        f.write("-- Script para corregir caracteres UTF-8 mal codificados\n")
                        f.write("-- Generado automáticamente\n\n")
                        f.write("BEGIN TRANSACTION;\n\n")
                        
                        for sql in correcciones_sql:
                            f.write(sql + "\n")
                        
                        f.write("\n-- Verificar cambios antes de confirmar\n")
                        f.write("-- COMMIT; -- Descomentar para aplicar cambios\n")
                        f.write("-- ROLLBACK; -- Usar para deshacer si algo sale mal\n")
                    
                    print(f"\n💾 Script guardado en: correccion_caracteres.sql")
                else:
                    print(f"\n✅ No se requieren correcciones")
                    
            else:
                print("✅ No se encontraron archivos con problemas en EvidenciasCumplimiento")
                
        except Exception as e:
            print(f"❌ Error consultando EvidenciasCumplimiento: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"\n❌ Error general: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    buscar_y_corregir_archivos()
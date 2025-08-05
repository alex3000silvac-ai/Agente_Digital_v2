#!/usr/bin/env python3
"""
Script para corregir la descripción corrupta específica y buscar otros casos similares
"""
import pyodbc
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import get_db_connection

def corregir_descripciones_corruptas():
    """Corrige descripciones con caracteres mal codificados"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("CORRIGIENDO DESCRIPCIONES CORRUPTAS EN EVIDENCIASCUMPLIMIENTO")
        print("="*70 + "\n")
        
        # Buscar todas las descripciones con problemas
        cursor.execute("""
            SELECT 
                EvidenciaID,
                CumplimientoID,
                NombreArchivoOriginal,
                Descripcion,
                FechaSubida
            FROM EvidenciasCumplimiento
            WHERE Descripcion LIKE '%Ã%'
            ORDER BY FechaSubida DESC
        """)
        
        evidencias_problematicas = cursor.fetchall()
        
        if evidencias_problematicas:
            print(f"🎯 ENCONTRADAS {len(evidencias_problematicas)} evidencias con descripciones corruptas:")
            print()
            
            correcciones = []
            
            for idx, row in enumerate(evidencias_problematicas, 1):
                evidencia_id = row[0]
                cumplimiento_id = row[1]
                nombre = row[2]
                descripcion_corrupta = row[3]
                fecha = row[4]
                
                print(f"{idx}. EvidenciaID: {evidencia_id}")
                print(f"   Archivo: {nombre}")
                print(f"   ❌ Descripción corrupta: {descripcion_corrupta}")
                
                # Aplicar correcciones
                descripcion_corregida = descripcion_corrupta
                
                # Correcciones específicas para UTF-8 mal interpretado
                correcciones_utf8 = {
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
                    'autorizaciÃ³n': 'autorización',
                    'comunicaciÃ³n': 'comunicación',
                    'coordinaciÃ³n': 'coordinación',
                    'evaluaciÃ³n': 'evaluación',
                    'planificaciÃ³n': 'planificación',
                    'organizaciÃ³n': 'organización',
                    'Ã¡': 'á',
                    'Ã©': 'é', 
                    'Ã­': 'í',
                    'Ã³': 'ó',
                    'Ãº': 'ú',
                    'Ã±': 'ñ',
                    'Ã¿': 'ÿ',
                    'Ã¢': 'â',
                    'Ã¤': 'ä',
                    'Ã¼': 'ü',
                    'Ã§': 'ç'
                }
                
                for corrupto, correcto in correcciones_utf8.items():
                    descripcion_corregida = descripcion_corregida.replace(corrupto, correcto)
                
                print(f"   ✅ Descripción corregida: {descripcion_corregida}")
                
                if descripcion_corregida != descripcion_corrupta:
                    # Escapar comillas para SQL
                    desc_escaped = descripcion_corregida.replace("'", "''")
                    sql_update = f"UPDATE EvidenciasCumplimiento SET Descripcion = '{desc_escaped}' WHERE EvidenciaID = {evidencia_id};"
                    correcciones.append({
                        'evidencia_id': evidencia_id,
                        'descripcion_original': descripcion_corrupta,
                        'descripcion_corregida': descripcion_corregida,
                        'sql': sql_update
                    })
                    print(f"   📝 Preparada corrección SQL")
                else:
                    print(f"   ⚠️  No se detectaron cambios necesarios")
                
                print(f"   Fecha: {fecha}")
                print("-" * 60)
            
            # Mostrar resumen y generar script SQL
            if correcciones:
                print(f"\n📋 RESUMEN DE CORRECCIONES:")
                print(f"Total de registros a corregir: {len(correcciones)}")
                
                # Generar script SQL
                sql_script = """-- Script para corregir descripciones de evidencias con caracteres UTF-8 mal codificados
-- Generado automáticamente
-- Ejecutar en SQL Server Management Studio

BEGIN TRANSACTION;

-- Mostrar registros antes de la corrección
SELECT EvidenciaID, Descripcion FROM EvidenciasCumplimiento 
WHERE EvidenciaID IN (""" + ", ".join(str(c['evidencia_id']) for c in correcciones) + """);

-- Aplicar correcciones
"""
                
                for correccion in correcciones:
                    sql_script += f"\n-- EvidenciaID {correccion['evidencia_id']}\n"
                    sql_script += f"-- Antes: {correccion['descripcion_original']}\n"
                    sql_script += f"-- Después: {correccion['descripcion_corregida']}\n"
                    sql_script += correccion['sql'] + "\n"
                
                sql_script += """
-- Mostrar registros después de la corrección
SELECT EvidenciaID, Descripcion FROM EvidenciasCumplimiento 
WHERE EvidenciaID IN (""" + ", ".join(str(c['evidencia_id']) for c in correcciones) + """);

-- ¡IMPORTANTE! Verificar los cambios antes de confirmar
-- Si todo está bien, descomentar la siguiente línea:
-- COMMIT;

-- Si algo está mal, descomentar la siguiente línea:
-- ROLLBACK;
"""
                
                # Guardar script en archivo
                with open('corregir_descripciones_evidencias.sql', 'w', encoding='utf-8') as f:
                    f.write(sql_script)
                
                print(f"\n💾 Script SQL guardado en: corregir_descripciones_evidencias.sql")
                
                # Opción de aplicar correcciones directamente
                print(f"\n❓ ¿Deseas aplicar las correcciones ahora? (y/N): ", end="")
                respuesta = input().strip().lower()
                
                if respuesta == 'y':
                    print(f"\n🔄 Aplicando correcciones...")
                    
                    try:
                        for correccion in correcciones:
                            cursor.execute(f"UPDATE EvidenciasCumplimiento SET Descripcion = ? WHERE EvidenciaID = ?", 
                                         (correccion['descripcion_corregida'], correccion['evidencia_id']))
                            print(f"   ✅ Corregida evidencia {correccion['evidencia_id']}")
                        
                        conn.commit()
                        print(f"\n✅ Todas las correcciones aplicadas exitosamente")
                        print(f"🎉 El problema 'ejecuciÃ³n' ya debería estar resuelto en el frontend")
                        
                    except Exception as e:
                        conn.rollback()
                        print(f"\n❌ Error aplicando correcciones: {e}")
                        print(f"🔄 Cambios revertidos")
                else:
                    print(f"\n💾 Correcciones NO aplicadas. Usa el archivo SQL para aplicarlas manualmente.")
            else:
                print(f"\n✅ No se requieren correcciones")
                
        else:
            print("✅ No se encontraron descripciones con caracteres corruptos")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    corregir_descripciones_corruptas()
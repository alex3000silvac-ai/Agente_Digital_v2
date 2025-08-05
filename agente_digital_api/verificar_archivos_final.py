#!/usr/bin/env python3
"""
Verificación final de archivos asociados
"""

def verificar_archivos_completo():
    """Verificar todos los archivos del incidente 25"""
    try:
        print("🔍 VERIFICACIÓN COMPLETA DE ARCHIVOS - INCIDENTE 25")
        print("=" * 80)
        
        from app.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Archivos en INCIDENTES_ARCHIVOS
        print("\n1️⃣ ARCHIVOS EN INCIDENTES_ARCHIVOS:")
        cursor.execute("""
            SELECT 
                ArchivoID,
                SeccionID,
                NombreOriginal,
                NombreServidor,
                RutaArchivo,
                TamanoKB,
                FechaSubida
            FROM INCIDENTES_ARCHIVOS
            WHERE IncidenteID = 25 AND Activo = 1
            ORDER BY FechaSubida DESC
        """)
        
        archivos_incidente = cursor.fetchall()
        
        if archivos_incidente:
            print(f"\n   ✅ Encontrados {len(archivos_incidente)} archivos:")
            for archivo in archivos_incidente:
                print(f"\n   📄 ARCHIVO ID: {archivo[0]}")
                print(f"      Sección: {archivo[1]}")
                print(f"      Nombre Original: {archivo[2]}")
                print(f"      Nombre Servidor: {archivo[3]}")
                print(f"      Ruta: {archivo[4]}")
                print(f"      Tamaño: {archivo[5]} KB")
                print(f"      Fecha: {archivo[6]}")
        else:
            print("\n   ❌ NO HAY ARCHIVOS en INCIDENTES_ARCHIVOS")
        
        # 2. Archivos en EVIDENCIAS_TAXONOMIA
        print("\n2️⃣ ARCHIVOS EN EVIDENCIAS_TAXONOMIA:")
        cursor.execute("""
            SELECT 
                TaxonomiaID,
                NombreArchivo,
                RutaArchivo,
                TamanoArchivo,
                FechaSubida
            FROM EVIDENCIAS_TAXONOMIA
            WHERE IncidenteID = 25
        """)
        
        archivos_taxonomia = cursor.fetchall()
        
        if archivos_taxonomia:
            print(f"\n   ✅ Encontrados {len(archivos_taxonomia)} archivos:")
            for archivo in archivos_taxonomia:
                print(f"\n   📄 ARCHIVO:")
                print(f"      Taxonomía: {archivo[0]}")
                print(f"      Nombre: {archivo[1]}")
                print(f"      Ruta: {archivo[2]}")
                print(f"      Tamaño: {archivo[3]} bytes")
                print(f"      Fecha: {archivo[4]}")
        else:
            print("\n   ❌ NO HAY ARCHIVOS en EVIDENCIAS_TAXONOMIA")
        
        # 3. Resumen
        print("\n📊 RESUMEN:")
        print(f"   - Archivos generales del incidente: {len(archivos_incidente)}")
        print(f"   - Archivos de taxonomías: {len(archivos_taxonomia)}")
        print(f"   - Total archivos: {len(archivos_incidente) + len(archivos_taxonomia)}")
        
        if len(archivos_incidente) + len(archivos_taxonomia) == 0:
            print("\n⚠️ NO HAY NINGÚN ARCHIVO GUARDADO para el incidente 25")
            print("   Esto es normal si:")
            print("   - No se adjuntaron archivos al crear/editar")
            print("   - Los archivos se eliminaron")
            print("   - Hubo un error al subir archivos")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_archivos_completo()
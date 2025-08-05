#!/usr/bin/env python3
"""
Verificar archivos asociados a las taxonomías del incidente 25
"""

def verificar_archivos_taxonomias():
    """Buscar archivos guardados en las taxonomías"""
    try:
        print("🔍 VERIFICANDO ARCHIVOS DE TAXONOMÍAS - INCIDENTE 25")
        print("=" * 80)
        
        from app.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Verificar taxonomías del incidente 25
        print("\n1️⃣ TAXONOMÍAS DEL INCIDENTE 25:")
        cursor.execute("""
            SELECT 
                IT.Id_Taxonomia,
                IT.Comentarios,
                IT.FechaAsignacion
            FROM INCIDENTE_TAXONOMIA IT
            WHERE IT.IncidenteID = 25
        """)
        
        taxonomias = cursor.fetchall()
        print(f"   Encontradas: {len(taxonomias)} taxonomías")
        
        for tax in taxonomias:
            print(f"\n   📋 Taxonomía: {tax[0]}")
            print(f"      Fecha: {tax[2]}")
        
        # 2. Buscar archivos en EVIDENCIAS_TAXONOMIA
        print("\n2️⃣ ARCHIVOS EN EVIDENCIAS_TAXONOMIA:")
        cursor.execute("""
            SELECT 
                ET.TaxonomiaID,
                ET.NombreArchivo,
                ET.NombreArchivoOriginal,
                ET.RutaArchivo,
                ET.TamanoArchivo,
                ET.FechaSubida,
                ET.Comentario
            FROM EVIDENCIAS_TAXONOMIA ET
            WHERE ET.IncidenteID = 25
            ORDER BY ET.TaxonomiaID, ET.FechaSubida
        """)
        
        archivos = cursor.fetchall()
        
        if archivos:
            print(f"\n   ✅ Encontrados {len(archivos)} archivos:")
            for archivo in archivos:
                print(f"\n   📄 ARCHIVO:")
                print(f"      Taxonomía: {archivo[0]}")
                print(f"      Nombre: {archivo[1]}")
                print(f"      Nombre Original: {archivo[2]}")
                print(f"      Ruta: {archivo[3]}")
                print(f"      Tamaño: {archivo[4]} bytes")
                print(f"      Fecha: {archivo[5]}")
                print(f"      Comentario: {archivo[6]}")
        else:
            print("\n   ❌ NO HAY ARCHIVOS guardados para las taxonomías")
        
        # 3. Buscar archivos generales del incidente
        print("\n3️⃣ ARCHIVOS GENERALES DEL INCIDENTE:")
        cursor.execute("""
            SELECT 
                NombreArchivo,
                RutaArchivo,
                SeccionID,
                FechaCarga
            FROM INCIDENTES_ARCHIVOS
            WHERE IncidenteID = 25 AND Activo = 1
            ORDER BY FechaCarga DESC
        """)
        
        archivos_generales = cursor.fetchall()
        
        if archivos_generales:
            print(f"\n   ✅ Encontrados {len(archivos_generales)} archivos generales:")
            for archivo in archivos_generales:
                print(f"\n   📄 Archivo: {archivo[0]}")
                print(f"      Sección: {archivo[2]}")
                print(f"      Ruta: {archivo[1]}")
                print(f"      Fecha: {archivo[3]}")
        else:
            print("\n   ❌ NO HAY ARCHIVOS generales del incidente")
        
        # 4. Verificar estructura de la respuesta
        print("\n4️⃣ ESTRUCTURA ESPERADA EN EL FRONTEND:")
        print("   taxonomias_seleccionadas: [")
        print("     {")
        print("       id: 'INC_USO_PHIP_ECDP',")
        print("       justificacion: '...',")
        print("       descripcionProblema: '...',")
        print("       archivos: [")
        print("         {")
        print("           nombre: 'archivo.pdf',")
        print("           ruta: '/uploads/...'")
        print("         }")
        print("       ]")
        print("     }")
        print("   ]")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_archivos_taxonomias()
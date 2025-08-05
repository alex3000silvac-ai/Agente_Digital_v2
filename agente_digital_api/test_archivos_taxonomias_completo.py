#!/usr/bin/env python3
"""
Test completo del flujo de archivos de taxonomías
"""

def test_archivos_taxonomias():
    """Verificar y agregar archivos de prueba para las taxonomías"""
    try:
        print("🔍 TEST COMPLETO DE ARCHIVOS DE TAXONOMÍAS")
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
                TI.Subcategoria_del_Incidente as Nombre
            FROM INCIDENTE_TAXONOMIA IT
            INNER JOIN Taxonomia_incidentes TI ON IT.Id_Taxonomia = TI.Id_Incidente
            WHERE IT.IncidenteID = 25
        """)
        
        taxonomias = cursor.fetchall()
        print(f"   Encontradas: {len(taxonomias)} taxonomías")
        
        if not taxonomias:
            print("   ❌ No hay taxonomías para el incidente 25")
            return
        
        # 2. Verificar archivos existentes
        print("\n2️⃣ ARCHIVOS EXISTENTES EN EVIDENCIAS_TAXONOMIA:")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM EVIDENCIAS_TAXONOMIA 
            WHERE IncidenteID = 25
        """)
        
        count = cursor.fetchone()[0]
        print(f"   Archivos actuales: {count}")
        
        # 3. Agregar archivos de prueba a cada taxonomía
        print("\n3️⃣ AGREGANDO ARCHIVOS DE PRUEBA:")
        
        import os
        from datetime import datetime
        
        for tax in taxonomias:
            tax_id = tax[0]
            tax_nombre = tax[2]
            
            print(f"\n   📋 Taxonomía: {tax_id} - {tax_nombre}")
            
            # Crear archivo de prueba
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f"{timestamp}_evidencia_{tax_id}.pdf"
            ruta_archivo = f"/uploads/incidentes/25/taxonomias/{nombre_archivo}"
            
            # Insertar en la base de datos
            cursor.execute("""
                INSERT INTO EVIDENCIAS_TAXONOMIA 
                (IncidenteID, TaxonomiaID, NombreArchivo, NombreArchivoOriginal,
                 RutaArchivo, TamanoArchivo, TipoArchivo, FechaSubida, SubidoPor, Activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, 1)
            """, (
                25,
                tax_id,
                nombre_archivo,
                f"evidencia_{tax_nombre.replace(' ', '_')}.pdf",
                ruta_archivo,
                1024 * 50,  # 50KB
                'application/pdf',
                1  # Usuario de prueba
            ))
            
            print(f"      ✅ Archivo agregado: {nombre_archivo}")
        
        conn.commit()
        print("\n✅ Archivos de prueba agregados exitosamente")
        
        # 4. Verificar resultado final
        print("\n4️⃣ VERIFICACIÓN FINAL:")
        cursor.execute("""
            SELECT 
                ET.TaxonomiaID,
                ET.NombreArchivo,
                ET.NombreArchivoOriginal,
                ET.TamanoArchivo,
                TI.Subcategoria_del_Incidente as NombreTaxonomia
            FROM EVIDENCIAS_TAXONOMIA ET
            INNER JOIN Taxonomia_incidentes TI ON ET.TaxonomiaID = TI.Id_Incidente
            WHERE ET.IncidenteID = 25
            ORDER BY ET.TaxonomiaID, ET.FechaSubida DESC
        """)
        
        archivos_finales = cursor.fetchall()
        
        print(f"\n   Total archivos: {len(archivos_finales)}")
        for archivo in archivos_finales:
            print(f"\n   📄 Taxonomía: {archivo[0]} - {archivo[4]}")
            print(f"      Archivo: {archivo[2]}")
            print(f"      Tamaño: {archivo[3]} bytes")
        
        cursor.close()
        conn.close()
        
        # 5. Probar el endpoint
        print("\n5️⃣ PROBANDO ENDPOINT cargar_completo:")
        print("\n   Para verificar en el navegador:")
        print("   1. Abre la consola del navegador (F12)")
        print("   2. Ve a http://localhost:5173/incidente-detalle/25")
        print("   3. En la consola ejecuta:")
        print("\n   // Verificar archivos de taxonomías")
        print("   const response = await fetch('http://localhost:5002/api/incidente/25/cargar_completo', {")
        print("     headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }")
        print("   });")
        print("   const data = await response.json();")
        print("   console.log('Taxonomías:', data.incidente.taxonomias_seleccionadas);")
        print("   data.incidente.taxonomias_seleccionadas.forEach(tax => {")
        print("     console.log(`Taxonomía ${tax.id}:`, tax.archivos);")
        print("   });")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_archivos_taxonomias()
#!/usr/bin/env python3
"""
Verificación completa del flujo de taxonomías
"""

def verificar_taxonomias_completas():
    """Verificar todo sobre las taxonomías del incidente 25"""
    try:
        print("🔍 VERIFICACIÓN COMPLETA DE TAXONOMÍAS - INCIDENTE 25")
        print("=" * 80)
        
        from app.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Verificar estructura de la tabla INCIDENTE_TAXONOMIA
        print("\n1️⃣ ESTRUCTURA DE INCIDENTE_TAXONOMIA:")
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'INCIDENTE_TAXONOMIA'
            ORDER BY ORDINAL_POSITION
        """)
        
        columnas = cursor.fetchall()
        for col in columnas:
            print(f"   - {col[0]}: {col[1]}")
        
        # 2. Datos guardados para incidente 25
        print("\n2️⃣ TAXONOMÍAS GUARDADAS PARA INCIDENTE 25:")
        cursor.execute("""
            SELECT 
                IT.*,
                TI.Subcategoria_del_Incidente as Nombre,
                TI.Categoria_del_Incidente as Categoria
            FROM INCIDENTE_TAXONOMIA IT
            INNER JOIN Taxonomia_incidentes TI ON IT.Id_Taxonomia = TI.Id_Incidente
            WHERE IT.IncidenteID = 25
        """)
        
        # Obtener nombres de columnas
        columns = [column[0] for column in cursor.description]
        taxonomias = []
        
        for row in cursor.fetchall():
            tax_dict = dict(zip(columns, row))
            taxonomias.append(tax_dict)
            
            print(f"\n   📋 Taxonomía guardada:")
            for key, value in tax_dict.items():
                if value is not None:
                    print(f"      {key}: {value}")
        
        # 3. Verificar qué devuelve el endpoint (simulación)
        print("\n3️⃣ SIMULACIÓN DE CARGA (como lo haría el endpoint):")
        
        # Esta es la consulta del endpoint
        cursor.execute("""
            SELECT 
                IT.Id_Taxonomia,
                TI.Subcategoria_del_Incidente as Categoria_del_Incidente,
                TI.Descripcion,
                TI.AplicaTipoEmpresa,
                IT.Comentarios,
                IT.FechaAsignacion,
                IT.CreadoPor,
                TI.Categoria_del_Incidente as Categoria
            FROM INCIDENTE_TAXONOMIA IT
            INNER JOIN Taxonomia_incidentes TI ON IT.Id_Taxonomia = TI.Id_Incidente
            WHERE IT.IncidenteID = 25
        """)
        
        taxonomias_endpoint = cursor.fetchall()
        
        print(f"\n   Total taxonomías que devolvería el endpoint: {len(taxonomias_endpoint)}")
        
        for tax in taxonomias_endpoint:
            print(f"\n   📌 Datos que se enviarían al frontend:")
            print(f"      Id_Taxonomia: {tax[0]}")
            print(f"      Categoria_del_Incidente: {tax[1]}")
            print(f"      Comentarios: {tax[4][:100] if tax[4] else 'NO HAY COMENTARIOS'}...")
            
            # Verificar si los comentarios tienen el formato esperado
            if tax[4] and 'Justificación:' in tax[4]:
                print("      ✅ Comentarios tienen formato de justificación")
            else:
                print("      ❌ Comentarios NO tienen formato de justificación")
        
        # 4. Verificar archivos
        print("\n4️⃣ ARCHIVOS DE TAXONOMÍAS:")
        cursor.execute("""
            SELECT 
                TaxonomiaID,
                COUNT(*) as TotalArchivos
            FROM EVIDENCIAS_TAXONOMIA
            WHERE IncidenteID = 25
            GROUP BY TaxonomiaID
        """)
        
        archivos = cursor.fetchall()
        if archivos:
            for arch in archivos:
                print(f"   📂 Taxonomía {arch[0]}: {arch[1]} archivos")
        else:
            print("   ❌ No hay archivos de taxonomías")
        
        # 5. Verificar qué espera el frontend
        print("\n5️⃣ LO QUE ESPERA EL FRONTEND:")
        print("   taxonomias_seleccionadas: [")
        print("     {")
        print("       id: 'INC_USO_PHIP_ECDP',  // CAMPO CRÍTICO")
        print("       nombre: '...',            // CAMPO CRÍTICO")
        print("       justificacion: '...',")
        print("       descripcionProblema: '...',")
        print("       archivos: []")
        print("     }")
        print("   ]")
        
        print("\n6️⃣ PROBLEMAS IDENTIFICADOS:")
        problemas = []
        
        if len(taxonomias_endpoint) == 0:
            problemas.append("No hay taxonomías guardadas para el incidente 25")
        else:
            tax = taxonomias_endpoint[0]
            if not tax[4] or 'Justificación:' not in tax[4]:
                problemas.append("Los comentarios no tienen el formato de justificación")
        
        if len(problemas) > 0:
            for p in problemas:
                print(f"   ❌ {p}")
        else:
            print("   ✅ No se identificaron problemas en la base de datos")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_taxonomias_completas()
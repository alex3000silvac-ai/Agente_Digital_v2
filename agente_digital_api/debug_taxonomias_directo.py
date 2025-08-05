#!/usr/bin/env python3
"""
Debug directo de taxonomías - sin servidor Flask
"""

def test_taxonomias_directo():
    """Test directo sin servidor"""
    try:
        from app.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("🧪 PRUEBA DIRECTA DE TAXONOMÍAS")
        print("=" * 50)
        
        # 1. Verificar incidente 22
        print(f"📋 1. Verificando incidente 22...")
        cursor.execute("SELECT IncidenteID, Titulo FROM Incidentes WHERE IncidenteID = 22")
        incidente = cursor.fetchone()
        
        if incidente:
            print(f"   ✅ Incidente encontrado: {incidente[1]}")
        else:
            print(f"   ❌ Incidente 22 no encontrado")
            return
            
        # 2. Verificar taxonomías del incidente
        print(f"🏷️  2. Verificando taxonomías del incidente...")
        cursor.execute("""
            SELECT 
                IT.ID,
                IT.Id_Taxonomia,
                IT.Comentarios,
                IT.FechaAsignacion
            FROM INCIDENTE_TAXONOMIA IT
            WHERE IT.IncidenteID = 22
        """)
        
        taxonomias_bd = cursor.fetchall()
        print(f"   📊 Taxonomías en BD: {len(taxonomias_bd)}")
        
        for tax in taxonomias_bd:
            print(f"      ID: {tax[0]}")
            print(f"      Taxonomía: {tax[1]}")
            print(f"      Comentarios: {tax[2][:100] if tax[2] else 'Sin comentarios'}...")
            print(f"      Fecha: {tax[3]}")
            print()
        
        # 3. Simular query del endpoint
        print(f"🔍 3. Simulando query del endpoint de carga...")
        cursor.execute("""
            SELECT 
                it.Id_Taxonomia,
                COALESCE(ti.Categoria_del_Incidente + ' - ' + ti.Subcategoria_del_Incidente, ti.Categoria_del_Incidente) as Nombre,
                ti.Area,
                ti.Efecto,
                ti.Categoria_del_Incidente as Categoria,
                ti.Subcategoria_del_Incidente as Subcategoria,
                ti.AplicaTipoEmpresa as Tipo,
                ti.Descripcion,
                it.Comentarios as Justificacion,
                '' as DescripcionProblema,
                it.FechaAsignacion
            FROM INCIDENTE_TAXONOMIA it
            INNER JOIN Taxonomia_incidentes ti ON it.Id_Taxonomia = ti.Id_Incidente
            WHERE it.IncidenteID = 22
        """)
        
        taxonomias_endpoint = cursor.fetchall()
        print(f"   📊 Taxonomías por endpoint: {len(taxonomias_endpoint)}")
        
        for row in taxonomias_endpoint:
            print(f"      ID: {row[0]}")
            print(f"      Nombre: {row[1]}")
            print(f"      Área: {row[2]}")
            print(f"      Justificación: {row[8][:100] if row[8] else 'Sin justificación'}...")
            print()
            
        # 4. Verificar si la taxonomía existe en la tabla principal
        print(f"🔍 4. Verificando existencia de taxonomías en tabla principal...")
        
        for tax_bd in taxonomias_bd:
            tax_id = tax_bd[1]
            cursor.execute("""
                SELECT 
                    Id_Incidente,
                    Categoria_del_Incidente,
                    Subcategoria_del_Incidente,
                    Area,
                    Efecto
                FROM Taxonomia_incidentes 
                WHERE Id_Incidente = ?
            """, (tax_id,))
            
            resultado = cursor.fetchone()
            if resultado:
                print(f"   ✅ {tax_id}: {resultado[1]} - {resultado[2]}")
            else:
                print(f"   ❌ {tax_id}: NO ENCONTRADA en Taxonomia_incidentes")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Prueba completada")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_taxonomias_directo()
#!/usr/bin/env python3
"""
Verificar taxonomías del incidente 24
"""

def verificar_incidente_24():
    """Verificar qué taxonomías tiene el incidente 24"""
    try:
        print("🔍 VERIFICANDO INCIDENTE 24")
        print("=" * 70)
        
        from app.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        incidente_id = 24
        
        # 1. Verificar si existe el incidente
        cursor.execute("SELECT IncidenteID, Titulo, FechaCreacion FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        incidente = cursor.fetchone()
        
        if incidente:
            print(f"\n✅ Incidente encontrado:")
            print(f"   ID: {incidente[0]}")
            print(f"   Título: {incidente[1]}")
            print(f"   Fecha: {incidente[2]}")
        else:
            print(f"\n❌ Incidente {incidente_id} NO existe")
            return
        
        # 2. Verificar taxonomías
        print(f"\n📊 TAXONOMÍAS DEL INCIDENTE {incidente_id}:")
        
        cursor.execute("""
            SELECT 
                IT.Id_Taxonomia,
                IT.Comentarios,
                IT.FechaAsignacion,
                IT.CreadoPor
            FROM INCIDENTE_TAXONOMIA IT
            WHERE IT.IncidenteID = ?
            ORDER BY IT.FechaAsignacion DESC
        """, (incidente_id,))
        
        taxonomias = cursor.fetchall()
        
        if taxonomias:
            print(f"\n✅ Se encontraron {len(taxonomias)} taxonomías:")
            for i, tax in enumerate(taxonomias, 1):
                print(f"\n{i}. Taxonomía: {tax[0]}")
                print(f"   Comentarios: {tax[1][:100] if tax[1] else 'NULL'}...")
                print(f"   Fecha: {tax[2]}")
                print(f"   Creado por: {tax[3]}")
        else:
            print(f"\n❌ NO HAY TAXONOMÍAS para el incidente {incidente_id}")
            print("   Esto es normal si:")
            print("   - Es un incidente nuevo")
            print("   - No se han seleccionado taxonomías en la Sección 4")
            print("   - Hubo un error al guardar")
        
        # 3. Verificar otros incidentes con taxonomías
        print(f"\n📋 OTROS INCIDENTES CON TAXONOMÍAS:")
        
        cursor.execute("""
            SELECT DISTINCT TOP 10
                I.IncidenteID,
                I.Titulo,
                COUNT(IT.Id_Taxonomia) as NumTaxonomias
            FROM Incidentes I
            INNER JOIN INCIDENTE_TAXONOMIA IT ON I.IncidenteID = IT.IncidenteID
            GROUP BY I.IncidenteID, I.Titulo
            ORDER BY I.IncidenteID DESC
        """)
        
        otros = cursor.fetchall()
        for inc in otros:
            print(f"   - Incidente {inc[0]}: {inc[1][:50]}... ({inc[2]} taxonomías)")
        
        # 4. Sugerir acciones
        print(f"\n💡 ACCIONES SUGERIDAS:")
        if not taxonomias:
            print("   1. Edita el incidente 24")
            print("   2. Ve a la Sección 4 - Acciones Iniciales")
            print("   3. Selecciona al menos una taxonomía")
            print("   4. Completa los campos de justificación y descripción")
            print("   5. Guarda el incidente")
        else:
            print("   1. Recarga la página (F5)")
            print("   2. Verifica en DevTools la respuesta de 'cargar-completo'")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_incidente_24()
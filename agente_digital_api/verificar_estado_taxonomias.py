#!/usr/bin/env python3
"""
Verificar estado actual de taxonomías en el incidente 22
"""

def verificar_estado_completo():
    """Verificar estado completo de taxonomías"""
    try:
        from app.database import get_db_connection
        from app.utils.encoding_fixer import EncodingFixer
        
        print("🔍 VERIFICACIÓN COMPLETA DE TAXONOMÍAS")
        print("=" * 60)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        incidente_id = 22
        
        # 1. Verificar incidente
        print(f"📋 1. VERIFICANDO INCIDENTE {incidente_id}")
        cursor.execute("SELECT IncidenteID, Titulo, EstadoActual FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        incidente = cursor.fetchone()
        
        if incidente:
            print(f"   ✅ Incidente: {incidente[1]}")
            print(f"   Estado: {incidente[2]}")
        else:
            print(f"   ❌ Incidente no encontrado")
            return
        
        # 2. Verificar taxonomías en INCIDENTE_TAXONOMIA
        print(f"\n🗃️  2. TAXONOMÍAS EN INCIDENTE_TAXONOMIA")
        cursor.execute("""
            SELECT 
                ID,
                IncidenteID,
                Id_Taxonomia,
                Comentarios,
                FechaAsignacion,
                CreadoPor
            FROM INCIDENTE_TAXONOMIA
            WHERE IncidenteID = ?
            ORDER BY FechaAsignacion DESC
        """, (incidente_id,))
        
        taxonomias_bd = cursor.fetchall()
        print(f"   📊 Total registros: {len(taxonomias_bd)}")
        
        for i, tax in enumerate(taxonomias_bd):
            print(f"   {i+1}. ID_BD: {tax[0]}")
            print(f"      Taxonomía: {tax[2]}")
            print(f"      Comentarios: {tax[3][:100] if tax[3] else 'Sin comentarios'}...")
            print(f"      Fecha: {tax[4]}")
            print(f"      Usuario: {tax[5]}")
            print()
        
        # 3. Verificar con JOIN como en el endpoint
        print(f"🔍 3. VERIFICACIÓN CON JOIN (como endpoint)")
        cursor.execute("""
            SELECT 
                it.Id_Taxonomia,
                COALESCE(ti.Categoria_del_Incidente + ' - ' + ti.Subcategoria_del_Incidente, ti.Categoria_del_Incidente) as Nombre,
                ti.Area,
                ti.Efecto,
                it.Comentarios as Justificacion,
                it.FechaAsignacion
            FROM INCIDENTE_TAXONOMIA it
            INNER JOIN Taxonomia_incidentes ti ON it.Id_Taxonomia = ti.Id_Incidente
            WHERE it.IncidenteID = ?
        """, (incidente_id,))
        
        taxonomias_endpoint = cursor.fetchall()
        print(f"   📊 Con JOIN: {len(taxonomias_endpoint)} registros")
        
        for i, row in enumerate(taxonomias_endpoint):
            # Aplicar fix de encoding
            justificacion_original = row[4] or ''
            justificacion_corregida = EncodingFixer.fix_text(justificacion_original) if justificacion_original else ''
            
            print(f"   {i+1}. ID: {row[0]}")
            print(f"      Nombre: {row[1][:50]}...")
            print(f"      Área: {row[2]}")
            print(f"      Justificación (original): {justificacion_original[:50]}...")
            print(f"      Justificación (corregida): {justificacion_corregida[:50]}...")
            print(f"      Fecha: {row[5]}")
            print()
        
        # 4. Verificar qué taxonomías están disponibles
        print(f"🏷️  4. TAXONOMÍAS DISPONIBLES EN SISTEMA")
        cursor.execute("""
            SELECT COUNT(*) as Total
            FROM Taxonomia_incidentes
        """)
        
        total_taxonomias = cursor.fetchone()[0]
        print(f"   📊 Total taxonomías en sistema: {total_taxonomias}")
        
        # 5. Verificar taxonomías específicas que podrían estar seleccionadas
        taxonomias_test = ['INC_USO_PHIP_ECDP', 'INC_CONF_EXCF_FCRA', 'INC_CONF_EXCF_FSRA']
        
        print(f"\n🎯 5. VERIFICACIÓN DE TAXONOMÍAS ESPECÍFICAS")
        for tax_id in taxonomias_test:
            # Verificar si existe en el sistema
            cursor.execute("""
                SELECT 
                    Id_Incidente,
                    Categoria_del_Incidente,
                    Subcategoria_del_Incidente
                FROM Taxonomia_incidentes 
                WHERE Id_Incidente = ?
            """, (tax_id,))
            
            existe = cursor.fetchone()
            
            if existe:
                print(f"   ✅ {tax_id}: {existe[1]} - {existe[2]}")
                
                # Verificar si está seleccionada en el incidente
                cursor.execute("""
                    SELECT ID, Comentarios 
                    FROM INCIDENTE_TAXONOMIA 
                    WHERE IncidenteID = ? AND Id_Taxonomia = ?
                """, (incidente_id, tax_id))
                
                seleccionada = cursor.fetchone()
                
                if seleccionada:
                    print(f"      🔗 SELECCIONADA: ID_BD={seleccionada[0]}")
                    print(f"         Comentarios: {seleccionada[1][:50] if seleccionada[1] else 'Sin comentarios'}...")
                else:
                    print(f"      ❌ NO seleccionada en incidente")
            else:
                print(f"   ❌ {tax_id}: NO EXISTE en sistema")
            print()
        
        cursor.close()
        conn.close()
        
        print("✅ Verificación completada")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_estado_completo()
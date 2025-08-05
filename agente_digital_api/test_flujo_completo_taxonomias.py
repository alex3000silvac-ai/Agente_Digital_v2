#!/usr/bin/env python3
"""
Test del flujo completo de taxonomías: seleccionar → guardar → recargar
"""

def test_flujo_completo():
    """Test del flujo completo como lo hace el usuario"""
    try:
        from app.database import get_db_connection
        from app.utils.encoding_fixer import EncodingFixer
        import json
        
        print("🧪 TEST FLUJO COMPLETO DE TAXONOMÍAS")
        print("=" * 60)
        
        incidente_id = 22
        
        # PASO 1: Verificar estado inicial
        print("🔍 PASO 1: Estado inicial")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as Total
            FROM INCIDENTE_TAXONOMIA
            WHERE IncidenteID = ?
        """, (incidente_id,))
        
        inicial = cursor.fetchone()[0]
        print(f"   Taxonomías iniciales: {inicial}")
        
        # PASO 2: Simular que el usuario AGREGA una nueva taxonomía
        print("\n💾 PASO 2: Usuario agrega nueva taxonomía")
        
        nueva_taxonomia = {
            'id': 'INC_CONF_EXCF_FCRA',
            'justificacion': 'Nueva justificación de prueba',
            'descripcionProblema': 'Nuevo problema de prueba'
        }
        
        # Simular guardado (como hace incidentes_actualizar.py líneas 138-148)
        cursor.execute("""
            INSERT INTO INCIDENTE_TAXONOMIA 
            (IncidenteID, Id_Taxonomia, Comentarios, FechaAsignacion, CreadoPor)
            VALUES (?, ?, ?, GETDATE(), ?)
        """, (
            incidente_id,
            nueva_taxonomia['id'],
            nueva_taxonomia['justificacion'],
            'test_user'
        ))
        
        conn.commit()
        print(f"   ✅ Taxonomía {nueva_taxonomia['id']} agregada")
        
        # PASO 3: Verificar que se guardó
        print("\n🔍 PASO 3: Verificar guardado")
        cursor.execute("""
            SELECT COUNT(*) as Total
            FROM INCIDENTE_TAXONOMIA
            WHERE IncidenteID = ?
        """, (incidente_id,))
        
        despues_agregar = cursor.fetchone()[0]
        print(f"   Taxonomías después de agregar: {despues_agregar}")
        print(f"   Diferencia: +{despues_agregar - inicial}")
        
        # PASO 4: Simular carga como hace el endpoint
        print("\n📥 PASO 4: Simular carga del endpoint")
        
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
            WHERE it.IncidenteID = ?
            ORDER BY it.FechaAsignacion DESC
        """, (incidente_id,))
        
        taxonomias_cargadas = []
        for row in cursor.fetchall():
            tax_data = {
                'id': row[0],
                'nombre': row[1],
                'area': row[2],
                'efecto': row[3],
                'categoria': row[4],
                'subcategoria': row[5],
                'tipo': row[6],
                'descripcion': row[7],
                'justificacion': row[8] or '',
                'descripcionProblema': row[9] or '',
                'fechaSeleccion': row[10].isoformat() if row[10] else None
            }
            # Aplicar fix de encoding
            tax_data = EncodingFixer.fix_dict(tax_data)
            taxonomias_cargadas.append(tax_data)
        
        print(f"   📊 Taxonomías cargadas por endpoint: {len(taxonomias_cargadas)}")
        for i, tax in enumerate(taxonomias_cargadas):
            print(f"   {i+1}. {tax['id']}")
            print(f"      Nombre: {tax['nombre'][:50]}...")
            print(f"      Justificación: {tax['justificacion'][:50]}...")
            print()
        
        # PASO 5: Simular que el usuario MODIFICA una taxonomía existente
        print("\n✏️  PASO 5: Usuario modifica taxonomía existente")
        
        if taxonomias_cargadas:
            tax_a_modificar = taxonomias_cargadas[0]
            nueva_justificacion = "Justificación MODIFICADA por el usuario"
            
            print(f"   Modificando: {tax_a_modificar['id']}")
            print(f"   Justificación anterior: {tax_a_modificar['justificacion'][:50]}...")
            print(f"   Nueva justificación: {nueva_justificacion}")
            
            # Simular update (como hace incidentes_actualizar.py)
            # Primero elimina todas las taxonomías
            cursor.execute("DELETE FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?", (incidente_id,))
            
            # Luego re-inserta todas (incluyendo la modificada)
            for tax in taxonomias_cargadas:
                justificacion_a_usar = nueva_justificacion if tax['id'] == tax_a_modificar['id'] else tax['justificacion']
                
                cursor.execute("""
                    INSERT INTO INCIDENTE_TAXONOMIA 
                    (IncidenteID, Id_Taxonomia, Comentarios, FechaAsignacion, CreadoPor)
                    VALUES (?, ?, ?, GETDATE(), ?)
                """, (
                    incidente_id,
                    tax['id'],
                    justificacion_a_usar,
                    'test_user'
                ))
            
            conn.commit()
            print(f"   ✅ Taxonomía modificada")
        
        # PASO 6: Verificar la modificación cargando nuevamente
        print("\n🔍 PASO 6: Verificar modificación")
        
        cursor.execute("""
            SELECT 
                it.Id_Taxonomia,
                it.Comentarios,
                it.FechaAsignacion
            FROM INCIDENTE_TAXONOMIA it
            WHERE it.IncidenteID = ?
            ORDER BY it.FechaAsignacion DESC
        """, (incidente_id,))
        
        taxonomias_finales = cursor.fetchall()
        print(f"   📊 Taxonomías después de modificación: {len(taxonomias_finales)}")
        
        for i, tax in enumerate(taxonomias_finales):
            comentarios_corregidos = EncodingFixer.fix_text(tax[1]) if tax[1] else ''
            print(f"   {i+1}. {tax[0]}")
            print(f"      Comentarios: {comentarios_corregidos[:50]}...")
            print(f"      Fecha: {tax[2]}")
            print()
        
        # PASO 7: Simular el problema reportado - "desaparece al editar"
        print("\n🚨 PASO 7: Simular problema - taxonomía 'desaparece'")
        
        print("   Posibles causas:")
        print("   1. ¿Se está perdiendo en el mapeo frontend?")
        print("   2. ¿Se está eliminando accidentalmente?")
        print("   3. ¿Hay problemas de timing en la carga?")
        print("   4. ¿El frontend no está enviando los datos correctamente?")
        
        # Verificar si alguna taxonomía no se está mostrando visualmente
        print("\n   🔍 Verificando visibilidad:")
        
        for tax in taxonomias_finales:
            tax_id = tax[0]
            comentarios = tax[1] or ''
            
            # Simular función taxonomiaSeleccionada del frontend
            print(f"   - {tax_id}: ¿Debería aparecer seleccionada? SÍ")
            print(f"     Comentarios: {comentarios[:30]}...")
            
            # Verificar si tiene datos suficientes para mostrarse
            if not comentarios.strip():
                print(f"     ⚠️  WARNING: Sin comentarios - podría no mostrarse completa")
            else:
                print(f"     ✅ Tiene comentarios - debería mostrarse")
        
        cursor.close()
        conn.close()
        
        return {
            'inicial': inicial,
            'despues_agregar': despues_agregar,
            'final': len(taxonomias_finales),
            'agregadas': despues_agregar - inicial,
            'conservadas': len(taxonomias_finales)
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {}

if __name__ == "__main__":
    resultado = test_flujo_completo()
    
    print("\n📊 RESUMEN DEL FLUJO:")
    print("=" * 50)
    print(f"Taxonomías iniciales: {resultado.get('inicial', 0)}")
    print(f"Después de agregar: {resultado.get('despues_agregar', 0)}")
    print(f"Taxonomías finales: {resultado.get('final', 0)}")
    print(f"Agregadas en test: +{resultado.get('agregadas', 0)}")
    print(f"Conservadas después de modificar: {resultado.get('conservadas', 0)}")
    
    if resultado.get('conservadas', 0) > 0:
        print("\n✅ LAS TAXONOMÍAS SÍ SE CONSERVAN EN LA BD")
        print("❓ El problema debe ser en el FRONTEND - lógica de visualización")
    else:
        print("\n❌ PROBLEMA EN EL BACKEND - las taxonomías se pierden")
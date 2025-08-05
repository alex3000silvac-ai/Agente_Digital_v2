#!/usr/bin/env python3
"""
Test simple para verificar que las taxonomías se muestran correctamente
"""

def test_query_directa():
    """Probar la query corregida directamente"""
    try:
        print("🧪 TEST DIRECTO DE QUERY CORREGIDA")
        print("=" * 70)
        
        from app.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        incidente_id = 22
        
        # Query CORREGIDA con Comentarios
        query_taxonomias = """
            SELECT DISTINCT
                IT.Id_Taxonomia,
                IT.Comentarios,
                IT.FechaAsignacion,
                IT.CreadoPor,
                TI.Area,
                TI.Efecto,
                TI.Categoria_del_Incidente,
                TI.Subcategoria_del_Incidente,
                TI.Tipo_Empresa
            FROM INCIDENTE_TAXONOMIA IT
            INNER JOIN TAXONOMIA_INCIDENTES TI ON IT.Id_Taxonomia = TI.Id_Incidente
            WHERE IT.IncidenteID = ?
        """
        
        cursor.execute(query_taxonomias, (incidente_id,))
        
        print(f"\n📊 RESULTADOS DE LA QUERY:")
        
        for row in cursor.fetchall():
            tax = dict(zip([column[0] for column in cursor.description], row))
            
            print(f"\n🏷️ Taxonomía: {tax['Id_Taxonomia']}")
            print(f"   - Comentarios raw: {tax.get('Comentarios', 'NULL')[:100]}...")
            
            # Simular el parseo
            if tax.get('Comentarios'):
                comentarios = tax['Comentarios']
                if 'Justificación:' in comentarios:
                    parts = comentarios.split('Justificación:', 1)
                    if len(parts) > 1:
                        justif_parts = parts[1].split('\n', 1)
                        justificacion = justif_parts[0].strip()
                        
                        descripcion = ''
                        if len(justif_parts) > 1 and 'Descripción del problema:' in justif_parts[1]:
                            desc_parts = justif_parts[1].split('Descripción del problema:', 1)
                            if len(desc_parts) > 1:
                                descripcion = desc_parts[1].strip()
                        
                        print(f"   ✅ Justificación parseada: {justificacion}")
                        print(f"   ✅ Descripción parseada: {descripcion}")
                else:
                    print(f"   ⚠️ Formato antiguo - usando comentario completo")
            else:
                print(f"   ❌ Sin comentarios")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def verificar_que_muestra_frontend():
    """Explicar qué debería mostrar el frontend"""
    print(f"\n🎨 QUÉ DEBERÍA MOSTRAR EL FRONTEND")
    print("=" * 70)
    
    print("\n📋 Con los cambios implementados:")
    print("\n1. Al CARGAR un incidente:")
    print("   - El backend ahora incluye IT.Comentarios en la query")
    print("   - El backend parsea y agrega campos 'justificacion' y 'descripcionProblema'")
    print("   - El frontend recibe estos campos y los muestra en los textareas")
    
    print("\n2. Al GUARDAR un incidente:")
    print("   - El frontend envía: {id: 'XXX', justificacion: 'YYY', descripcionProblema: 'ZZZ'}")
    print("   - El backend combina: 'Justificación: YYY\\nDescripción del problema: ZZZ'")
    print("   - Se guarda en IT.Comentarios")
    
    print("\n3. En la UI deberías ver:")
    print("   - ☑️ INC_USO_PHIP_ECDP - [nombre de la taxonomía]")
    print("   - Campo 4.2.1: [textarea con la justificación]")
    print("   - Campo 4.2.2: [textarea con la descripción del problema]")

if __name__ == "__main__":
    print("🔍 TEST SIMPLE DE TAXONOMÍAS")
    print("=" * 80)
    
    # Test directo
    test_query_directa()
    
    # Explicación
    verificar_que_muestra_frontend()
    
    print("\n" + "=" * 80)
    print("✅ CAMBIOS IMPLEMENTADOS:")
    print("   1. incidente_cargar_completo.py - Query incluye IT.Comentarios")
    print("   2. incidente_cargar_completo.py - Parsea justificacion y descripcionProblema")
    print("   3. Frontend ya está listo para mostrar estos campos")
    print("\n⚠️ IMPORTANTE:")
    print("   Necesitas RECARGAR la página del incidente para ver los cambios")
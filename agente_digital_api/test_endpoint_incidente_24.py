#!/usr/bin/env python3
"""
Test del endpoint cargar-completo para incidente 24
"""

def simular_endpoint_incidente_24():
    """Simular lo que devuelve el endpoint para incidente 24"""
    try:
        print("🔍 SIMULANDO ENDPOINT CARGAR-COMPLETO PARA INCIDENTE 24")
        print("=" * 70)
        
        from app.database import get_db_connection
        from app.utils.encoding_fixer import EncodingFixer
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        incidente_id = 24
        
        # Ejecutar la query ACTUAL del endpoint
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
                TI.TipoEmpresa
            FROM INCIDENTE_TAXONOMIA IT
            INNER JOIN TAXONOMIA_INCIDENTES TI ON IT.Id_Taxonomia = TI.Id_Incidente
            WHERE IT.IncidenteID = ?
        """
        
        cursor.execute(query_taxonomias, (incidente_id,))
        
        print("\n📊 RESULTADO DE LA QUERY:")
        
        taxonomias_seleccionadas = []
        
        for row in cursor.fetchall():
            tax = dict(zip([column[0] for column in cursor.description], row))
            
            print(f"\n🏷️ Taxonomía ANTES de fix encoding:")
            print(f"   ID: {tax['Id_Taxonomia']}")
            print(f"   Comentarios: {tax.get('Comentarios', '')[:100]}...")
            
            # Aplicar fix de encoding
            tax = EncodingFixer.fix_dict(tax)
            
            print(f"\n✅ Taxonomía DESPUÉS de fix encoding:")
            print(f"   Comentarios: {tax.get('Comentarios', '')[:100]}...")
            
            # Parsear comentarios
            if tax.get('Comentarios'):
                comentarios = tax['Comentarios']
                
                # Buscar justificación
                if 'Justificación:' in comentarios:
                    parts = comentarios.split('Justificación:', 1)
                    if len(parts) > 1:
                        justif_parts = parts[1].split('\n', 1)
                        tax['justificacion'] = justif_parts[0].strip()
                        
                        # Buscar descripción del problema
                        if len(justif_parts) > 1 and 'Descripción del problema:' in justif_parts[1]:
                            desc_parts = justif_parts[1].split('Descripción del problema:', 1)
                            if len(desc_parts) > 1:
                                tax['descripcionProblema'] = desc_parts[1].strip()
                else:
                    # Formato antiguo
                    tax['justificacion'] = comentarios
                    tax['descripcionProblema'] = ''
            else:
                tax['justificacion'] = ''
                tax['descripcionProblema'] = ''
            
            print(f"\n📋 Campos parseados:")
            print(f"   justificacion: {tax.get('justificacion', 'NO PARSEADA')}")
            print(f"   descripcionProblema: {tax.get('descripcionProblema', 'NO PARSEADA')}")
            
            taxonomias_seleccionadas.append(tax)
        
        print(f"\n📊 RESULTADO FINAL:")
        print(f"   Total taxonomías: {len(taxonomias_seleccionadas)}")
        
        if taxonomias_seleccionadas:
            print(f"\n🎯 Lo que debería mostrar el frontend:")
            for tax in taxonomias_seleccionadas:
                print(f"\n   ☑️ {tax['Id_Taxonomia']}")
                print(f"   Campo 4.2.1: {tax.get('justificacion', '')}")
                print(f"   Campo 4.2.2: {tax.get('descripcionProblema', '')}")
        
        cursor.close()
        conn.close()
        
        return taxonomias_seleccionadas
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

def verificar_que_hacer():
    """Qué hacer si no se ven las taxonomías"""
    print(f"\n📋 SI NO VES LAS TAXONOMÍAS EN LA UI:")
    print("=" * 70)
    
    print("\n1. Abre las DevTools (F12)")
    print("2. Ve a la pestaña Network")
    print("3. Recarga la página")
    print("4. Busca la llamada a 'cargar-completo'")
    print("5. En la respuesta, busca 'taxonomias_seleccionadas'")
    print("6. Verifica que contenga:")
    print("   - Id_Taxonomia")
    print("   - justificacion")
    print("   - descripcionProblema")
    
    print("\n7. Si los campos están pero no se muestran:")
    print("   - Verifica la consola por errores")
    print("   - Busca errores como 'Cannot read property of undefined'")

if __name__ == "__main__":
    # Simular endpoint
    taxonomias = simular_endpoint_incidente_24()
    
    # Instrucciones
    verificar_que_hacer()
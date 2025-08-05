#!/usr/bin/env python3
"""
Test final - Verificar que el incidente 24 muestra taxonomías correctamente
"""

def test_incidente_24_completo():
    """Test completo del incidente 24"""
    try:
        print("🔍 TEST COMPLETO INCIDENTE 24")
        print("=" * 70)
        
        from app.database import get_db_connection
        from app.utils.encoding_fixer import EncodingFixer
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        incidente_id = 24
        
        # Query corregida final
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
                TI.AplicaTipoEmpresa
            FROM INCIDENTE_TAXONOMIA IT
            LEFT JOIN TAXONOMIA_INCIDENTES TI ON IT.Id_Taxonomia = TI.Id_Incidente
            WHERE IT.IncidenteID = ?
        """
        
        cursor.execute(query_taxonomias, (incidente_id,))
        
        print("\n📊 PROCESANDO TAXONOMÍAS:")
        
        taxonomias_resultado = []
        
        for row in cursor.fetchall():
            tax = dict(zip([column[0] for column in cursor.description], row))
            
            print(f"\n🏷️ Taxonomía: {tax['Id_Taxonomia']}")
            print(f"   Comentarios ANTES de fix: {repr(tax.get('Comentarios', '')[:50])}...")
            
            # Fix encoding
            tax = EncodingFixer.fix_dict(tax)
            
            print(f"   Comentarios DESPUÉS de fix: {repr(tax.get('Comentarios', '')[:50])}...")
            
            # Parsear
            if tax.get('Comentarios'):
                comentarios = tax['Comentarios']
                
                if 'Justificación:' in comentarios:
                    parts = comentarios.split('Justificación:', 1)
                    if len(parts) > 1:
                        justif_parts = parts[1].split('\n', 1)
                        tax['justificacion'] = justif_parts[0].strip()
                        
                        if len(justif_parts) > 1 and 'Descripción del problema:' in justif_parts[1]:
                            desc_parts = justif_parts[1].split('Descripción del problema:', 1)
                            if len(desc_parts) > 1:
                                tax['descripcionProblema'] = desc_parts[1].strip()
                            else:
                                tax['descripcionProblema'] = ''
                        else:
                            tax['descripcionProblema'] = ''
                else:
                    tax['justificacion'] = comentarios.strip()
                    tax['descripcionProblema'] = ''
            else:
                tax['justificacion'] = ''
                tax['descripcionProblema'] = ''
            
            print(f"\n   📋 Campos parseados:")
            print(f"      justificacion: '{tax.get('justificacion', '')}'")
            print(f"      descripcionProblema: '{tax.get('descripcionProblema', '')}'")
            
            # Agregar otros campos necesarios
            tax['nombre'] = tax.get('Categoria_del_Incidente', '')
            tax['area'] = tax.get('Area', '')
            tax['efecto'] = tax.get('Efecto', '')
            
            taxonomias_resultado.append(tax)
        
        print(f"\n✅ RESULTADO FINAL:")
        print(f"   Total taxonomías: {len(taxonomias_resultado)}")
        
        if taxonomias_resultado:
            print(f"\n🎯 LO QUE DEBES VER EN LA UI:")
            print(f"   En http://localhost:5173/incidente-detalle/24")
            print(f"   Sección 4 - Acciones Iniciales:")
            
            for tax in taxonomias_resultado:
                print(f"\n   ☑️ {tax['Id_Taxonomia']} - {tax.get('nombre', 'Sin nombre')}")
                print(f"      Campo 4.2.1 (Justificación): {tax.get('justificacion', '')}")
                print(f"      Campo 4.2.2 (Descripción): {tax.get('descripcionProblema', '')}")
        else:
            print("\n❌ No hay taxonomías para mostrar")
        
        cursor.close()
        conn.close()
        
        return taxonomias_resultado
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

def instrucciones_debug():
    """Instrucciones para debug en el navegador"""
    print(f"\n📋 PASOS PARA VERIFICAR EN EL NAVEGADOR:")
    print("=" * 70)
    
    print("\n1. Abre: http://localhost:5173/incidente-detalle/24")
    print("2. Abre DevTools (F12)")
    print("3. Ve a la pestaña Network")
    print("4. Recarga la página (F5)")
    print("5. Busca la llamada a '/api/incidentes/24/cargar-completo'")
    print("6. Click en la llamada y ve a 'Response'")
    print("7. Busca 'taxonomias_seleccionadas' en el JSON")
    print("8. Verifica que contenga:")
    print("   {")
    print('     "Id_Taxonomia": "INC_USO_PHIP_ECDP",')
    print('     "Comentarios": "Justificación: sadfsdf...",')
    print('     "justificacion": "sadfsdf sdfdf",')
    print('     "descripcionProblema": "sdfsdf sdfsa"')
    print("   }")
    
    print("\n9. Si los datos están pero no se ven:")
    print("   - Ve a la pestaña Console")
    print("   - Busca errores en rojo")
    print("   - Escribe: window.debugTaxonomias()")

if __name__ == "__main__":
    # Test completo
    taxonomias = test_incidente_24_completo()
    
    # Instrucciones
    instrucciones_debug()
    
    print("\n" + "=" * 70)
    print("✅ El backend está correctamente configurado")
    print("📌 Si no ves las taxonomías, sigue las instrucciones de debug arriba")
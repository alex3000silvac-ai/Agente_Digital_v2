#!/usr/bin/env python3
"""
Test final - Verificar formato correcto para el frontend
"""

def test_formato_frontend():
    """Verificar que el formato sea exactamente el que espera el frontend"""
    try:
        print("🔍 TEST FINAL - FORMATO PARA FRONTEND")
        print("=" * 80)
        
        from app.database import get_db_connection
        from app.utils.encoding_fixer import EncodingFixer
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query actualizada con campo 'id'
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
            WHERE IT.IncidenteID = 25
        """
        
        cursor.execute(query_taxonomias)
        rows = cursor.fetchall()
        
        print(f"\n📊 Procesando {len(rows)} taxonomías...")
        
        taxonomias_resultado = []
        
        for row in rows:
            tax = dict(zip([column[0] for column in cursor.description], row))
            tax = EncodingFixer.fix_dict(tax)
            
            # Parsear comentarios
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
                    tax['justificacion'] = comentarios
                    tax['descripcionProblema'] = ''
            else:
                tax['justificacion'] = ''
                tax['descripcionProblema'] = ''
            
            # CRÍTICO: Agregar campo 'id' que espera el frontend
            tax['id'] = tax['Id_Taxonomia']
            tax['nombre'] = tax.get('Categoria_del_Incidente', '')
            tax['area'] = tax.get('Area', '')
            tax['efecto'] = tax.get('Efecto', '')
            
            taxonomias_resultado.append(tax)
        
        # Mostrar resultado final
        print(f"\n📋 FORMATO FINAL PARA EL FRONTEND:")
        print("taxonomias_seleccionadas: [")
        for tax in taxonomias_resultado:
            print("  {")
            print(f'    "id": "{tax.get("id", "")}",  // CRÍTICO: Frontend busca este campo')
            print(f'    "Id_Taxonomia": "{tax.get("Id_Taxonomia", "")}",')
            print(f'    "nombre": "{tax.get("nombre", "")}",')
            print(f'    "justificacion": "{tax.get("justificacion", "")}",')
            print(f'    "descripcionProblema": "{tax.get("descripcionProblema", "")}",')
            print(f'    "area": "{tax.get("area", "")}",')
            print(f'    "efecto": "{tax.get("efecto", "")}"')
            print("  }")
        print("]")
        
        print(f"\n✅ VERIFICACIÓN DE CAMPOS CRÍTICOS:")
        for tax in taxonomias_resultado:
            print(f"\n🏷️ Taxonomía: {tax['id']}")
            if tax.get('id'):
                print("   ✅ Campo 'id' presente")
            else:
                print("   ❌ FALTA campo 'id'")
            
            if tax.get('justificacion'):
                print(f"   ✅ justificacion: '{tax['justificacion']}'")
            else:
                print("   ❌ FALTA justificacion")
                
            if tax.get('descripcionProblema'):
                print(f"   ✅ descripcionProblema: '{tax['descripcionProblema']}'")
            else:
                print("   ⚠️ descripcionProblema vacío")
        
        print(f"\n🎯 INSTRUCCIONES PARA VERIFICAR EN UI:")
        print("1. Abre: http://localhost:5173/incidente-detalle/25")
        print("2. Recarga la página (F5)")
        print("3. Ve a Sección 4")
        print("4. Deberías ver:")
        print("   - Taxonomía con fondo verde")
        print("   - Checkbox marcado ☑️")
        print("   - Campo 4.2.1 con justificación")
        print("   - Campo 4.2.2 con descripción")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_formato_frontend()
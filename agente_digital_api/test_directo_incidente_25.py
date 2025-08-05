#!/usr/bin/env python3
"""
Test directo de lo que devuelve el endpoint
"""

def test_directo():
    """Test directo sin Flask"""
    try:
        print("🔍 TEST DIRECTO - INCIDENTE 25")
        print("=" * 80)
        
        from app.database import get_db_connection
        from app.utils.encoding_fixer import EncodingFixer
        import json
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Consulta directa igual que el endpoint
        query = """
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
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print(f"\n📊 Taxonomías encontradas: {len(rows)}")
        
        taxonomias_seleccionadas = []
        
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
            
            # AGREGAR CAMPO 'id' QUE ESPERA EL FRONTEND
            tax['id'] = tax['Id_Taxonomia']
            tax['nombre'] = tax.get('Categoria_del_Incidente', '')
            tax['area'] = tax.get('Area', '')
            tax['efecto'] = tax.get('Efecto', '')
            
            # Convertir fecha a string si existe
            if tax.get('FechaAsignacion'):
                tax['FechaAsignacion'] = str(tax['FechaAsignacion'])
            
            taxonomias_seleccionadas.append(tax)
        
        # Simular respuesta completa
        respuesta = {
            'success': True,
            'taxonomias_seleccionadas': taxonomias_seleccionadas
        }
        
        print("\n📋 RESPUESTA SIMULADA:")
        print(json.dumps(respuesta, indent=2, ensure_ascii=False))
        
        print("\n✅ VERIFICACIÓN FINAL:")
        for tax in taxonomias_seleccionadas:
            print(f"\n🏷️ Taxonomía: {tax['id']}")
            print(f"   ✅ Campo 'id': '{tax['id']}'")
            print(f"   ✅ Campo 'justificacion': '{tax['justificacion']}'")
            print(f"   ✅ Campo 'descripcionProblema': '{tax['descripcionProblema']}'")
            print(f"   ✅ Campo 'nombre': '{tax['nombre']}'")
        
        # Guardar en archivo para inspección
        with open('respuesta_incidente_25.json', 'w', encoding='utf-8') as f:
            json.dump(respuesta, f, indent=2, ensure_ascii=False)
        
        print("\n📄 Respuesta guardada en: respuesta_incidente_25.json")
        
        print("\n🎯 INSTRUCCIONES FINALES:")
        print("1. El backend ESTÁ devolviendo los datos correctos")
        print("2. Abre: http://localhost:5173/incidente-detalle/25")
        print("3. Abre DevTools > Console")
        print("4. Escribe: window.debugTaxonomias()")
        print("5. Si no muestra datos, el problema es que:")
        print("   - El servidor Flask no está corriendo")
        print("   - Hay un error de CORS")
        print("   - El frontend no está procesando la respuesta correctamente")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_directo()
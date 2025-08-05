#!/usr/bin/env python3
"""
Verificar qué devuelve el endpoint para el incidente 25
"""

def verificar_endpoint_incidente_25():
    """Simular exactamente lo que devuelve el endpoint cargar-completo"""
    try:
        print("🔍 VERIFICANDO QUÉ RECIBE EL FRONTEND - INCIDENTE 25")
        print("=" * 80)
        
        from app.database import get_db_connection
        from app.utils.encoding_fixer import EncodingFixer
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Verificar si existe el incidente 25
        cursor.execute("SELECT IncidenteID, Titulo, EmpresaID FROM Incidentes WHERE IncidenteID = 25")
        inc = cursor.fetchone()
        
        if not inc:
            print("❌ Incidente 25 NO existe")
            return
        
        print(f"✅ Incidente encontrado: ID={inc[0]}, Título={inc[1]}, EmpresaID={inc[2]}")
        
        # 2. Ejecutar EXACTAMENTE la misma query del endpoint
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
        
        cursor.execute(query_taxonomias, (25,))
        rows = cursor.fetchall()
        
        print(f"\n📊 TAXONOMÍAS ENCONTRADAS: {len(rows)}")
        
        if len(rows) == 0:
            print("❌ NO HAY TAXONOMÍAS para el incidente 25")
            print("   - Verifica que hayas guardado el incidente con taxonomías seleccionadas")
            print("   - En la Sección 4, debe haber al menos una taxonomía marcada")
            return
        
        # 3. Procesar igual que el endpoint
        taxonomias_resultado = []
        for row in rows:
            tax = dict(zip([column[0] for column in cursor.description], row))
            tax = EncodingFixer.fix_dict(tax)
            
            print(f"\n🏷️ Procesando taxonomía: {tax['Id_Taxonomia']}")
            print(f"   Comentarios RAW: {tax.get('Comentarios', 'NULL')[:100]}...")
            
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
                    tax['justificacion'] = comentarios.strip()
                    tax['descripcionProblema'] = ''
            else:
                tax['justificacion'] = ''
                tax['descripcionProblema'] = ''
            
            print(f"   ✅ justificacion: '{tax.get('justificacion', '')}'")
            print(f"   ✅ descripcionProblema: '{tax.get('descripcionProblema', '')}'")
            
            taxonomias_resultado.append(tax)
        
        # 4. Mostrar resultado final
        print(f"\n📋 RESULTADO QUE RECIBE EL FRONTEND:")
        print(f"taxonomias_seleccionadas: [")
        for tax in taxonomias_resultado:
            print(f"  {{")
            print(f'    "Id_Taxonomia": "{tax.get("Id_Taxonomia", "")}",')
            print(f'    "Comentarios": "{tax.get("Comentarios", "")[:50]}...",')
            print(f'    "justificacion": "{tax.get("justificacion", "")}",')
            print(f'    "descripcionProblema": "{tax.get("descripcionProblema", "")}",')
            print(f'    "Area": "{tax.get("Area", "")}",')
            print(f'    "Efecto": "{tax.get("Efecto", "")}",')
            print(f'    "Categoria_del_Incidente": "{tax.get("Categoria_del_Incidente", "")}"')
            print(f"  }}")
        print(f"]")
        
        # 5. Verificar qué espera el frontend
        print(f"\n🎯 LO QUE ESPERA EL FRONTEND (AcordeonIncidenteMejorado.vue):")
        print("   - Campo 'id' o 'Id_Taxonomia' ✅")
        print("   - Campo 'justificacion' ✅") 
        print("   - Campo 'descripcionProblema' ✅")
        print("   - Que se muestre con fondo verde cuando está seleccionada")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_endpoint_incidente_25()
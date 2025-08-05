#!/usr/bin/env python3
"""
Probar el endpoint de taxonomías directamente
"""

def test_endpoint_directo():
    """Probar el endpoint ejecutando el código directamente"""
    
    print("🔍 PROBANDO ENDPOINT DE TAXONOMÍAS DIRECTAMENTE")
    print("=" * 80)
    
    try:
        from app.database import get_db_connection
        import json
        
        incidente_id = 25
        print(f"\n📡 Obteniendo taxonomías del incidente {incidente_id}...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Verificar que el incidente existe
        cursor.execute("SELECT IncidenteID FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        if not cursor.fetchone():
            print(f"❌ Incidente {incidente_id} no encontrado")
            return
        
        print(f"✅ Incidente {incidente_id} existe")
        
        # 2. Obtener taxonomías seleccionadas
        print("\n🔍 Consultando taxonomías...")
        cursor.execute("""
            SELECT 
                IT.Id_Taxonomia,
                TI.Subcategoria_del_Incidente as nombre,
                TI.Descripcion,
                TI.AplicaTipoEmpresa,
                IT.Comentarios,
                IT.FechaAsignacion,
                IT.CreadoPor,
                TI.Categoria_del_Incidente as categoria
            FROM INCIDENTE_TAXONOMIA IT
            INNER JOIN Taxonomia_incidentes TI ON IT.Id_Taxonomia = TI.Id_Incidente
            WHERE IT.IncidenteID = ?
        """, (incidente_id,))
        
        taxonomias = []
        columns = [column[0] for column in cursor.description]
        
        for row in cursor.fetchall():
            tax = dict(zip(columns, row))
            
            # Parsear justificación y descripción
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
            
            # Agregar campos esperados
            tax['id'] = tax['Id_Taxonomia']
            
            # Convertir fecha
            if tax.get('FechaAsignacion'):
                tax['FechaAsignacion'] = tax['FechaAsignacion'].isoformat()
            
            taxonomias.append(tax)
            
            print(f"\n✅ Taxonomía encontrada: {tax['id']}")
            print(f"   Nombre: {tax['nombre']}")
            print(f"   Justificación: {tax['justificacion']}")
        
        print(f"\n📊 Total taxonomías encontradas: {len(taxonomias)}")
        
        # 3. Obtener archivos de cada taxonomía
        print("\n🔍 Consultando archivos de taxonomías...")
        cursor.execute("""
            SELECT 
                ET.TaxonomiaID,
                ET.EvidenciaID,
                ET.NombreArchivo,
                ET.NombreArchivoOriginal,
                ET.RutaArchivo,
                ET.TamanoArchivo,
                ET.FechaSubida
            FROM EVIDENCIAS_TAXONOMIA ET
            WHERE ET.IncidenteID = ?
            ORDER BY ET.TaxonomiaID, ET.FechaSubida DESC
        """, (incidente_id,))
        
        # Agrupar archivos por taxonomía
        archivos_por_taxonomia = {}
        for row in cursor.fetchall():
            tax_id = row[0]
            if tax_id not in archivos_por_taxonomia:
                archivos_por_taxonomia[tax_id] = []
            
            archivos_por_taxonomia[tax_id].append({
                'id': row[1],
                'nombre': row[2],
                'nombreOriginal': row[3],
                'ruta': row[4],
                'tamaño': row[5],
                'fechaSubida': row[6].isoformat() if row[6] else None
            })
            
            print(f"   📎 Archivo para {tax_id}: {row[3]}")
        
        # 4. Agregar archivos a cada taxonomía
        for tax in taxonomias:
            tax_id = tax['id']
            tax['archivos'] = archivos_por_taxonomia.get(tax_id, [])
            print(f"\n   Taxonomía {tax_id}: {len(tax['archivos'])} archivos")
        
        cursor.close()
        conn.close()
        
        # 5. Crear respuesta JSON
        resultado = {
            "success": True,
            "taxonomias": taxonomias,
            "total": len(taxonomias)
        }
        
        # Guardar en archivo
        with open('taxonomias_endpoint_test.json', 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        
        print("\n✅ Resultado guardado en taxonomias_endpoint_test.json")
        print(f"\n📋 RESUMEN FINAL:")
        print(f"   - Taxonomías: {len(taxonomias)}")
        print(f"   - Total archivos: {sum(len(t['archivos']) for t in taxonomias)}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_endpoint_directo()
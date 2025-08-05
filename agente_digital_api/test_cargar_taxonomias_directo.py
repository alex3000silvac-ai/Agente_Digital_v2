#!/usr/bin/env python3
"""
Probar la carga directa de taxonomías del incidente 25
"""

def test_cargar_taxonomias():
    """Cargar y mostrar las taxonomías del incidente 25"""
    try:
        print("🔍 CARGANDO TAXONOMÍAS DEL INCIDENTE 25")
        print("=" * 80)
        
        from app.database import get_db_connection
        import json
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Cargar taxonomías con la misma consulta del endpoint
        print("\n1️⃣ TAXONOMÍAS SELECCIONADAS:")
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
            WHERE IT.IncidenteID = 25
        """)
        
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
            
            print(f"\n   📋 Taxonomía: {tax['id']}")
            print(f"      Nombre: {tax['nombre']}")
            print(f"      Justificación: {tax['justificacion']}")
            print(f"      Descripción: {tax['descripcionProblema'][:50]}...")
        
        # 2. Cargar archivos de taxonomías
        print("\n2️⃣ ARCHIVOS DE TAXONOMÍAS:")
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
            WHERE ET.IncidenteID = 25
            ORDER BY ET.TaxonomiaID
        """)
        
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
            
            print(f"\n   📄 Archivo para {tax_id}:")
            print(f"      Nombre: {row[3]}")
            print(f"      Tamaño: {row[5]} bytes")
            print(f"      Fecha: {row[6]}")
        
        # 3. Fusionar archivos con taxonomías
        print("\n3️⃣ ESTRUCTURA FINAL:")
        for tax in taxonomias:
            tax_id = tax['id']
            tax['archivos'] = archivos_por_taxonomia.get(tax_id, [])
            print(f"\n   Taxonomía {tax_id}: {len(tax['archivos'])} archivos")
        
        # 4. Crear estructura JSON completa
        resultado = {
            "success": True,
            "taxonomias": taxonomias,
            "total": len(taxonomias)
        }
        
        # Guardar en archivo para inspección
        with open('taxonomias_incidente_25.json', 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        
        print("\n✅ Datos guardados en taxonomias_incidente_25.json")
        
        # 5. Generar código JavaScript para cargar manualmente
        print("\n4️⃣ CÓDIGO PARA CARGAR EN EL NAVEGADOR:")
        print("""
// Copiar y pegar en la consola del navegador:
(function() {
  const taxonomiasData = """ + json.dumps(taxonomias, ensure_ascii=False) + """;
  
  // Buscar el componente Vue
  const app = document.querySelector('#app').__vue_app__;
  const buscarComponente = (instance) => {
    if (instance?.proxy?.taxonomiasSeleccionadas !== undefined) return instance.proxy;
    if (instance?.subTree?.component) {
      const result = buscarComponente(instance.subTree.component);
      if (result) return result;
    }
    if (instance?.children) {
      for (let child of instance.children) {
        const result = buscarComponente(child);
        if (result) return result;
      }
    }
    return null;
  };
  
  const vm = buscarComponente(app._instance);
  if (vm) {
    vm.taxonomiasSeleccionadas = taxonomiasData;
    console.log('✅ Taxonomías cargadas:', vm.taxonomiasSeleccionadas);
    if (vm.$forceUpdate) vm.$forceUpdate();
  } else {
    console.error('❌ No se encontró el componente');
  }
})();
""")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cargar_taxonomias()
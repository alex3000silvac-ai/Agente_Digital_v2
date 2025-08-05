#!/usr/bin/env python3
"""
Test para verificar race condition en la carga de taxonomías
"""

def simular_carga_taxonomias_frontend():
    """Simular lo que hace el frontend al cargar taxonomías"""
    try:
        from app.database import get_db_connection
        from app.utils.encoding_fixer import EncodingFixer
        import json
        
        print("🧪 SIMULANDO CARGA DE TAXONOMÍAS DEL FRONTEND")
        print("=" * 60)
        
        incidente_id = 22
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Simular llamada al endpoint de taxonomías disponibles
        print("1. 📋 Obteniendo taxonomías disponibles...")
        cursor.execute("""
            SELECT 
                Id_Incidente as id,
                Categoria_del_Incidente as categoria,
                Subcategoria_del_Incidente as subcategoria,
                Area as area,
                Efecto as efecto,
                AplicaTipoEmpresa as tipo,
                Descripcion as descripcion
            FROM Taxonomia_incidentes
            WHERE AplicaTipoEmpresa IN ('PSE', 'AMBAS')
        """)
        
        taxonomias_disponibles = []
        for row in cursor.fetchall():
            tax = dict(zip([column[0] for column in cursor.description], row))
            taxonomias_disponibles.append(tax)
        
        print(f"   ✅ {len(taxonomias_disponibles)} taxonomías disponibles")
        
        # 2. Simular llamada al endpoint del incidente 
        print("2. 📄 Obteniendo datos del incidente...")
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
        """, (incidente_id,))
        
        taxonomias_seleccionadas_bd = []
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
            taxonomias_seleccionadas_bd.append(tax_data)
        
        print(f"   ✅ {len(taxonomias_seleccionadas_bd)} taxonomías seleccionadas en BD")
        
        # 3. Simular el mapeo que hace el frontend
        print("3. 🔄 Simulando mapeo del frontend...")
        
        taxonomias_seleccionadas_frontend = []
        
        for tax_seleccionada in taxonomias_seleccionadas_bd:
            print(f"   🔍 Buscando taxonomía: {tax_seleccionada['id']}")
            
            # Buscar en taxonomías disponibles (como hace el frontend)
            tax_completa = None
            for tax_disp in taxonomias_disponibles:
                if tax_disp['id'] == tax_seleccionada['id']:
                    tax_completa = tax_disp
                    break
            
            if tax_completa:
                print(f"      ✅ Encontrada en disponibles")
                # Combinar datos como hace el frontend
                taxonomia_final = {
                    **tax_completa,  # Datos de la taxonomía disponible
                    'justificacion': tax_seleccionada['justificacion'],
                    'descripcionProblema': tax_seleccionada['descripcionProblema'],
                    'archivos': [],
                    'fechaSeleccion': tax_seleccionada['fechaSeleccion']
                }
                taxonomias_seleccionadas_frontend.append(taxonomia_final)
            else:
                print(f"      ❌ NO encontrada en disponibles - usando datos del servidor")
                taxonomias_seleccionadas_frontend.append(tax_seleccionada)
        
        print(f"\n📊 RESULTADO DEL MAPEO:")
        print(f"   Taxonomías seleccionadas finales: {len(taxonomias_seleccionadas_frontend)}")
        
        for i, tax in enumerate(taxonomias_seleccionadas_frontend):
            print(f"   {i+1}. ID: {tax['id']}")
            print(f"      Nombre: {tax.get('nombre', 'Sin nombre')[:50]}...")
            print(f"      Justificación: {tax.get('justificacion', 'Sin justificación')[:50]}...")
            print(f"      Tiene descripcionProblema: {'Sí' if tax.get('descripcionProblema') else 'No'}")
            print()
        
        # 4. Verificar si la función taxonomiaSeleccionada funcionaría
        print("4. 🎯 Verificando función taxonomiaSeleccionada...")
        
        for tax_disp in taxonomias_disponibles[:5]:  # Solo primeras 5 para no saturar
            es_seleccionada = any(t['id'] == tax_disp['id'] for t in taxonomias_seleccionadas_frontend)
            print(f"   {tax_disp['id']}: {'✅ SELECCIONADA' if es_seleccionada else '❌ No seleccionada'}")
        
        cursor.close()
        conn.close()
        
        return {
            'disponibles': len(taxonomias_disponibles),
            'seleccionadas_bd': len(taxonomias_seleccionadas_bd),
            'seleccionadas_frontend': len(taxonomias_seleccionadas_frontend),
            'mapeo_exitoso': len(taxonomias_seleccionadas_bd) == len(taxonomias_seleccionadas_frontend)
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {}

def verificar_timing():
    """Verificar si hay problemas de timing"""
    print("\n⏱️  VERIFICANDO PROBLEMAS DE TIMING")
    print("=" * 50)
    
    # Simular que las taxonomías disponibles demoran en cargar
    import time
    
    print("🔄 Simulando carga lenta de taxonomías disponibles...")
    print("   (Como podría pasar en un servidor lento)")
    
    time.sleep(1)  # Simular 1 segundo de demora
    
    print("✅ Taxonomías disponibles 'cargadas'")
    print("🔄 Intentando mapear taxonomías seleccionadas...")
    
    # Aquí es donde podría fallar el frontend si el timeout es muy corto
    resultado = simular_carga_taxonomias_frontend()
    
    return resultado

if __name__ == "__main__":
    print("🧪 TEST DE RACE CONDITION EN TAXONOMÍAS")
    print("=" * 70)
    
    # Test principal
    resultado = simular_carga_taxonomias_frontend()
    
    # Test de timing
    resultado_timing = verificar_timing()
    
    print("\n📊 RESUMEN:")
    print("=" * 50)
    print(f"Taxonomías disponibles: {resultado.get('disponibles', 0)}")
    print(f"Taxonomías en BD: {resultado.get('seleccionadas_bd', 0)}")
    print(f"Taxonomías mapeadas: {resultado.get('seleccionadas_frontend', 0)}")
    print(f"Mapeo exitoso: {'✅ SÍ' if resultado.get('mapeo_exitoso') else '❌ NO'}")
    
    if resultado.get('mapeo_exitoso'):
        print("\n🎉 NO hay problemas de mapeo - buscar otra causa")
    else:
        print("\n❌ PROBLEMA DE MAPEO ENCONTRADO")
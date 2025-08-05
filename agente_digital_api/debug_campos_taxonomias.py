#!/usr/bin/env python3
"""
Debug de campos de taxonomías para entender el problema del nombre
"""

def debug_campos_taxonomias():
    """Debuggear exactamente qué campos tienen las taxonomías"""
    try:
        from app.database import get_db_connection
        
        print("🔍 DEBUGGING CAMPOS DE TAXONOMÍAS")
        print("=" * 60)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Ver estructura de la tabla Taxonomia_incidentes
        print("1. 📋 ESTRUCTURA DE LA TABLA Taxonomia_incidentes")
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'Taxonomia_incidentes'
            ORDER BY ORDINAL_POSITION
        """)
        
        columnas = cursor.fetchall()
        print(f"   📊 Total columnas: {len(columnas)}")
        for col in columnas:
            print(f"   - {col[0]}: {col[1]} ({'NULL' if col[3] == 'YES' else 'NOT NULL'})")
        
        # 2. Ver datos de ejemplo
        print(f"\n2. 🎯 DATOS DE EJEMPLO (INC_USO_PHIP_ECDP)")
        cursor.execute("""
            SELECT *
            FROM Taxonomia_incidentes
            WHERE Id_Incidente = 'INC_USO_PHIP_ECDP'
        """)
        
        resultado = cursor.fetchone()
        if resultado:
            columns = [column[0] for column in cursor.description]
            datos = dict(zip(columns, resultado))
            
            print("   📝 Datos completos:")
            for campo, valor in datos.items():
                print(f"   {campo}: {valor}")
        
        # 3. Simular query del endpoint de taxonomías disponibles
        print(f"\n3. 🔍 SIMULANDO ENDPOINT DE TAXONOMÍAS DISPONIBLES")
        cursor.execute("""
            SELECT 
                Id_Incidente,
                Categoria_del_Incidente,
                Subcategoria_del_Incidente,
                Area,
                Efecto,
                AplicaTipoEmpresa,
                Descripcion
            FROM Taxonomia_incidentes
            WHERE Id_Incidente = 'INC_USO_PHIP_ECDP'
        """)
        
        resultado_endpoint = cursor.fetchone()
        if resultado_endpoint:
            columns_endpoint = [column[0] for column in cursor.description]
            datos_endpoint = dict(zip(columns_endpoint, resultado_endpoint))
            
            print("   📝 Como lo ve el endpoint de taxonomías disponibles:")
            for campo, valor in datos_endpoint.items():
                print(f"   {campo}: {valor}")
            
            # 4. Simular mapeo del frontend
            print(f"\n4. 🔄 SIMULANDO MAPEO DEL FRONTEND")
            
            # Como viene del endpoint /api/admin/taxonomias/flat
            tax_from_endpoint = {
                'id': datos_endpoint['Id_Incidente'],
                'categoria': datos_endpoint['Categoria_del_Incidente'],
                'subcategoria': datos_endpoint['Subcategoria_del_Incidente'],
                'area': datos_endpoint['Area'],
                'efecto': datos_endpoint['Efecto'],
                'aplica_para': datos_endpoint['AplicaTipoEmpresa'],
                'descripcion': datos_endpoint['Descripcion']
            }
            
            print("   📝 Objeto como viene del endpoint:")
            for campo, valor in tax_from_endpoint.items():
                print(f"   {campo}: {valor}")
            
            # Como lo mapea el frontend (líneas 1176-1185)
            tax_frontend = {
                'id': tax_from_endpoint['id'],
                'nombre': f"{tax_from_endpoint.get('categoria', '')} - {tax_from_endpoint.get('subcategoria', '')}".strip() or 'Sin nombre',
                'area': tax_from_endpoint.get('area', ''),
                'efecto': tax_from_endpoint.get('efecto', ''),
                'categoria': tax_from_endpoint.get('categoria', ''),
                'subcategoria': tax_from_endpoint.get('subcategoria', ''),
                'descripcion': f"{tax_from_endpoint.get('area', '')} - {tax_from_endpoint.get('efecto', '')} - {tax_from_endpoint.get('subcategoria', '')}".replace(' - ', ' - ').strip(),
                'tipo': (tax_from_endpoint.get('aplica_para', 'PSE')).upper()
            }
            
            print("\n   📝 Objeto después del mapeo del frontend:")
            for campo, valor in tax_frontend.items():
                print(f"   {campo}: {valor}")
            
            # 5. Verificar qué pasa en el momento de selección
            print(f"\n5. 🎯 VERIFICANDO LÓGICA DE SELECCIÓN")
            
            # Cuando se selecciona (toggleTaxonomia líneas 1296-1308)
            tax_seleccionada = {
                'id': tax_frontend['id'],
                'nombre': tax_frontend['nombre'],
                'area': tax_frontend['area'],
                'efecto': tax_frontend['efecto'],
                'categoria': tax_frontend['categoria'],
                'subcategoria': tax_frontend['subcategoria'],
                'descripcion': tax_frontend['descripcion'],
                'tipo': tax_frontend['tipo'],
                'justificacion': '',
                'descripcionProblema': '',
                'archivos': []
            }
            
            print("   📝 Taxonomía cuando se selecciona:")
            for campo, valor in tax_seleccionada.items():
                print(f"   {campo}: {valor}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_campos_taxonomias()
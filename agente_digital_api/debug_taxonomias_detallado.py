#!/usr/bin/env python3
"""
Script detallado para debug de taxonomías - muestra exactamente lo que el endpoint vería
"""

import pyodbc
from app.modules.core.database import get_db_connection

def debug_taxonomias_detallado():
    """Debug detallado para simular exactamente lo que hace el endpoint"""
    
    print("="*80)
    print("DEBUG DETALLADO DE TAXONOMÍAS - SIMULANDO ENDPOINT")
    print("="*80)
    
    conn = get_db_connection()
    if not conn:
        print("❌ No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor()
        tipo_empresa = 'PSE'
        
        # Primera consulta de prueba - para ver estructura
        print("\n1. CONSULTA DE PRUEBA - Estructura de la tabla:")
        test_query = "SELECT TOP 1 * FROM TAXONOMIA_INCIDENTES"
        cursor.execute(test_query)
        test_rows = cursor.fetchall()
        
        if test_rows:
            print(f"\n🔍 DEBUG: Columnas en la tabla: {[col[0] for col in cursor.description]}")
            print(f"🔍 Ejemplo de fila: ")
            for i, val in enumerate(test_rows[0]):
                print(f"   - {cursor.description[i][0]}: '{val}'")
        
        # Consulta real del endpoint
        print(f"\n2. CONSULTA REAL - Para tipo_empresa='{tipo_empresa}':")
        query = """
            SELECT 
                Id_Incidente,
                Area,
                Efecto,
                Categoria_del_Incidente,
                Subcategoria_del_Incidente,
                AplicaTipoEmpresa
            FROM TAXONOMIA_INCIDENTES
            WHERE (AplicaTipoEmpresa = ? OR AplicaTipoEmpresa = 'AMBAS' OR AplicaTipoEmpresa IS NULL)
            ORDER BY Area, Efecto, Categoria_del_Incidente
        """
        
        print(f"🔍 DEBUG: Ejecutando consulta para tipo_empresa='{tipo_empresa}'")
        cursor.execute(query, (tipo_empresa,))
        rows = cursor.fetchall()
        print(f"🔍 DEBUG: Consulta devolvió {len(rows)} filas")
        
        # Mostrar las primeras 5 filas
        print("\n3. PRIMERAS 5 FILAS DE RESULTADOS:")
        for idx, row in enumerate(rows[:5], 1):
            print(f"\n   Fila {idx}:")
            print(f"   - ID: {row.Id_Incidente}")
            print(f"   - Área: {row.Area}")
            print(f"   - Efecto: {row.Efecto}")
            print(f"   - Categoría: {row.Categoria_del_Incidente}")
            print(f"   - Subcategoría: '{row.Subcategoria_del_Incidente}'")
            print(f"   - Tipo subcategoría: {type(row.Subcategoria_del_Incidente)}")
            print(f"   - AplicaTipoEmpresa: {row.AplicaTipoEmpresa}")
            
            # Debug especial para registros problemáticos
            if 'EXCF' in row.Id_Incidente:
                print(f"\n🔍 DEBUG Taxonomía EXCF completa:")
                print(f"   - ID: {row.Id_Incidente}")
                print(f"   - Área: {row.Area}")
                print(f"   - Efecto: {row.Efecto}")
                print(f"   - Categoría: {row.Categoria_del_Incidente}")
                print(f"   - Subcategoría: '{row.Subcategoria_del_Incidente}'")
                print(f"   - Tipo subcategoría: {type(row.Subcategoria_del_Incidente)}")
        
        # Verificar caracteres especiales
        print("\n4. ANÁLISIS DE CARACTERES ESPECIALES:")
        for row in rows:
            if row.Subcategoria_del_Incidente:
                # Verificar si hay caracteres no ASCII
                non_ascii = [c for c in row.Subcategoria_del_Incidente if ord(c) > 127]
                if non_ascii:
                    print(f"\n   ID: {row.Id_Incidente}")
                    print(f"   Subcategoría: '{row.Subcategoria_del_Incidente}'")
                    print(f"   Caracteres no ASCII encontrados: {non_ascii}")
                    print(f"   Códigos Unicode: {[ord(c) for c in non_ascii]}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if conn:
            conn.close()
    
    print("\n" + "="*80)

if __name__ == "__main__":
    debug_taxonomias_detallado()
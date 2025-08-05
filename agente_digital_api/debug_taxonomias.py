#!/usr/bin/env python3
"""
Script de debug para verificar las taxonomías en la base de datos
"""

import pyodbc
from app.modules.core.database import get_db_connection

def debug_taxonomias():
    """Debug directo de la tabla TAXONOMIA_INCIDENTES"""
    
    print("="*80)
    print("DEBUG DE TAXONOMÍAS EN BASE DE DATOS")
    print("="*80)
    
    conn = get_db_connection()
    if not conn:
        print("❌ No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor()
        
        # 1. Verificar que la tabla existe
        print("\n1. Verificando tabla TAXONOMIA_INCIDENTES...")
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'TAXONOMIA_INCIDENTES'
        """)
        result = cursor.fetchone()
        if result and result.total > 0:
            print("✅ Tabla TAXONOMIA_INCIDENTES existe")
        else:
            print("❌ Tabla TAXONOMIA_INCIDENTES NO existe")
            return
        
        # 2. Contar registros totales
        print("\n2. Contando registros...")
        cursor.execute("SELECT COUNT(*) as total FROM TAXONOMIA_INCIDENTES")
        total = cursor.fetchone().total
        print(f"✅ Total de registros: {total}")
        
        # 3. Ver distribución por tipo de empresa
        print("\n3. Distribución por AplicaTipoEmpresa:")
        cursor.execute("""
            SELECT AplicaTipoEmpresa, COUNT(*) as cantidad
            FROM TAXONOMIA_INCIDENTES
            GROUP BY AplicaTipoEmpresa
            ORDER BY cantidad DESC
        """)
        for row in cursor.fetchall():
            tipo = row.AplicaTipoEmpresa or 'NULL'
            print(f"   - {tipo}: {row.cantidad} registros")
        
        # 4. Mostrar primeros 5 registros para PSE
        print("\n4. Primeros 5 registros para PSE:")
        cursor.execute("""
            SELECT TOP 5
                Id_Incidente,
                Area,
                Efecto,
                Categoria_del_Incidente,
                Subcategoria_del_Incidente,
                AplicaTipoEmpresa
            FROM TAXONOMIA_INCIDENTES
            WHERE AplicaTipoEmpresa = 'PSE' OR AplicaTipoEmpresa = 'Ambos' OR AplicaTipoEmpresa IS NULL
            ORDER BY Area, Efecto
        """)
        
        for i, row in enumerate(cursor.fetchall(), 1):
            print(f"\n   Registro {i}:")
            print(f"   - ID: {row.Id_Incidente}")
            print(f"   - Área: {row.Area}")
            print(f"   - Efecto: {row.Efecto}")
            print(f"   - Categoría: {row.Categoria_del_Incidente}")
            print(f"   - Subcategoría: {row.Subcategoria_del_Incidente}")
            print(f"   - Aplica para: {row.AplicaTipoEmpresa}")
        
        # 5. Buscar registros específicos que aparecen en el log
        print("\n5. Buscando registros con 'servicios de pago'...")
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM TAXONOMIA_INCIDENTES
            WHERE Area LIKE '%pago%' OR Efecto LIKE '%pago%'
        """)
        result = cursor.fetchone()
        print(f"   - Registros con 'pago': {result.total}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if conn:
            conn.close()
    
    print("\n" + "="*80)

if __name__ == "__main__":
    debug_taxonomias()
#!/usr/bin/env python3
"""
Verificación rápida del problema de taxonomías
"""

from app.modules.core.database import get_db_connection

def verificar_valores_aplicatipoempresa():
    """Verificar los valores únicos en AplicaTipoEmpresa"""
    
    conn = get_db_connection()
    if not conn:
        print("❌ No se pudo conectar a la BD")
        return
    
    try:
        cursor = conn.cursor()
        
        # 1. Valores únicos
        print("1. Valores únicos en AplicaTipoEmpresa:")
        cursor.execute("""
            SELECT DISTINCT AplicaTipoEmpresa, COUNT(*) as cantidad
            FROM TAXONOMIA_INCIDENTES
            GROUP BY AplicaTipoEmpresa
            ORDER BY cantidad DESC
        """)
        
        for row in cursor.fetchall():
            valor = row.AplicaTipoEmpresa or 'NULL'
            print(f"   - '{valor}': {row.cantidad} registros")
        
        # 2. Probar consulta con 'Ambos'
        print("\n2. Registros con 'Ambos' (minúsculas):")
        cursor.execute("SELECT COUNT(*) as total FROM TAXONOMIA_INCIDENTES WHERE AplicaTipoEmpresa = 'Ambos'")
        print(f"   Total: {cursor.fetchone().total}")
        
        # 3. Probar consulta con 'AMBAS'
        print("\n3. Registros con 'AMBAS' (mayúsculas):")
        cursor.execute("SELECT COUNT(*) as total FROM TAXONOMIA_INCIDENTES WHERE AplicaTipoEmpresa = 'AMBAS'")
        print(f"   Total: {cursor.fetchone().total}")
        
        # 4. Consulta corregida para PSE
        print("\n4. Total para PSE con consulta corregida:")
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM TAXONOMIA_INCIDENTES 
            WHERE AplicaTipoEmpresa = 'PSE' OR AplicaTipoEmpresa = 'AMBAS' OR AplicaTipoEmpresa IS NULL
        """)
        print(f"   Total: {cursor.fetchone().total} registros")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verificar_valores_aplicatipoempresa()
"""
Script para verificar las columnas de INCIDENTE_TAXONOMIA
"""
import pyodbc
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import get_db_connection

def verificar_columnas():
    """Verifica las columnas de la tabla INCIDENTE_TAXONOMIA"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("VERIFICANDO COLUMNAS DE INCIDENTE_TAXONOMIA")
        print("="*70 + "\n")
        
        # Obtener columnas
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'INCIDENTE_TAXONOMIA'
            ORDER BY ORDINAL_POSITION
        """)
        
        columnas = cursor.fetchall()
        
        print("Columnas encontradas:")
        print("-" * 70)
        for col in columnas:
            print(f"- {col[0]:<30} {col[1]:<15} {col[2] or 'N/A':<10} {col[3]}")
        
        # Verificar si hay registros para el incidente 5
        print("\n" + "="*70)
        print("REGISTROS PARA INCIDENTE 5:")
        print("="*70 + "\n")
        
        cursor.execute("SELECT * FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = 5")
        rows = cursor.fetchall()
        
        if not rows:
            print("❌ No hay taxonomías guardadas para el incidente 5")
        else:
            # Obtener nombres de columnas
            column_names = [desc[0] for desc in cursor.description]
            
            print(f"✅ Se encontraron {len(rows)} taxonomías:")
            for idx, row in enumerate(rows, 1):
                print(f"\nTaxonomía {idx}:")
                for i, col_name in enumerate(column_names):
                    value = row[i]
                    if value and len(str(value)) > 50:
                        value = str(value)[:50] + "..."
                    print(f"  {col_name}: {value}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verificar_columnas()
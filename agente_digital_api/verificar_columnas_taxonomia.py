"""
Script para verificar las columnas exactas de la tabla Taxonomia_incidentes
"""
import pyodbc
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import get_db_connection

def verificar_columnas():
    """Verifica las columnas de la tabla Taxonomia_incidentes"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("VERIFICANDO COLUMNAS DE Taxonomia_incidentes")
        print("="*70 + "\n")
        
        # Obtener columnas
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'Taxonomia_incidentes'
            ORDER BY ORDINAL_POSITION
        """)
        
        columnas = cursor.fetchall()
        
        print("Columnas encontradas:")
        print("-" * 70)
        for col in columnas:
            print(f"- {col[0]:<30} {col[1]:<15} {col[2] or 'N/A':<10} {col[3]}")
        
        # Obtener algunos registros de ejemplo
        print("\n" + "="*70)
        print("REGISTROS DE EJEMPLO (primeros 3):")
        print("="*70 + "\n")
        
        cursor.execute("SELECT TOP 3 * FROM Taxonomia_incidentes")
        rows = cursor.fetchall()
        
        # Obtener nombres de columnas
        column_names = [desc[0] for desc in cursor.description]
        
        for idx, row in enumerate(rows, 1):
            print(f"\nRegistro {idx}:")
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
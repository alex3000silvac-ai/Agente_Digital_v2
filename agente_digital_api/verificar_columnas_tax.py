#!/usr/bin/env python3
"""
Verificar nombres correctos de columnas
"""

def verificar_columnas():
    """Verificar columnas de la tabla TAXONOMIA_INCIDENTES"""
    try:
        print("🔍 VERIFICANDO COLUMNAS DE TAXONOMIA_INCIDENTES")
        print("=" * 70)
        
        from app.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ver columnas de TAXONOMIA_INCIDENTES
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'TAXONOMIA_INCIDENTES'
            ORDER BY ORDINAL_POSITION
        """)
        
        print("\n📊 Columnas en TAXONOMIA_INCIDENTES:")
        columnas = [row[0] for row in cursor.fetchall()]
        for col in columnas:
            print(f"   - {col}")
        
        # Buscar columna que contenga "tipo"
        columnas_tipo = [col for col in columnas if 'tipo' in col.lower()]
        if columnas_tipo:
            print(f"\n✅ Columnas con 'tipo': {columnas_tipo}")
        else:
            print("\n❌ No hay columnas con 'tipo'")
        
        cursor.close()
        conn.close()
        
        return columnas
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    columnas = verificar_columnas()
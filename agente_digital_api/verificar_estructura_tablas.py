#!/usr/bin/env python3
"""
Verificar estructura de tablas para estadísticas
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db_connection

def verificar_estructura():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("=== ESTRUCTURA DE TABLAS PARA ESTADÍSTICAS ===\n")
        
        # 1. INCIDENTES_ARCHIVOS
        print("1. INCIDENTES_ARCHIVOS:")
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'INCIDENTES_ARCHIVOS'
            ORDER BY ORDINAL_POSITION
        """)
        columnas = cursor.fetchall()
        for col in columnas:
            print(f"   - {col[0]} ({col[1]})")
        
        # Contar archivos para incidente 5
        cursor.execute("SELECT COUNT(*) FROM INCIDENTES_ARCHIVOS WHERE IncidenteID = 5")
        count = cursor.fetchone()[0]
        print(f"   Total archivos para incidente 5: {count}")
        
        # 2. INCIDENTES_COMENTARIOS
        print("\n2. INCIDENTES_COMENTARIOS:")
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'INCIDENTES_COMENTARIOS'
        """)
        if cursor.fetchone()[0] > 0:
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'INCIDENTES_COMENTARIOS'
                ORDER BY ORDINAL_POSITION
            """)
            columnas = cursor.fetchall()
            for col in columnas:
                print(f"   - {col[0]} ({col[1]})")
            
            cursor.execute("SELECT COUNT(*) FROM INCIDENTES_COMENTARIOS WHERE IncidenteID = 5")
            count = cursor.fetchone()[0]
            print(f"   Total comentarios para incidente 5: {count}")
        else:
            print("   Tabla no existe")
        
        # 3. INCIDENTES_TAXONOMIAS
        print("\n3. INCIDENTES_TAXONOMIAS:")
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'INCIDENTES_TAXONOMIAS'
        """)
        if cursor.fetchone()[0] > 0:
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'INCIDENTES_TAXONOMIAS'
                ORDER BY ORDINAL_POSITION
            """)
            columnas = cursor.fetchall()
            for col in columnas:
                print(f"   - {col[0]} ({col[1]})")
                
            # Intentar con diferentes nombres de columna
            try:
                cursor.execute("SELECT COUNT(*) FROM INCIDENTES_TAXONOMIAS WHERE Id_Incidente = 5")
                count = cursor.fetchone()[0]
                print(f"   Total taxonomías para incidente 5: {count}")
            except:
                try:
                    cursor.execute("SELECT COUNT(*) FROM INCIDENTES_TAXONOMIAS WHERE IncidenteID = 5")
                    count = cursor.fetchone()[0]
                    print(f"   Total taxonomías para incidente 5: {count}")
                except:
                    print("   No se pudo contar taxonomías")
        else:
            print("   Tabla no existe")
        
        # 4. Buscar otras tablas relevantes
        print("\n4. OTRAS TABLAS RELEVANTES:")
        
        # COMENTARIOS_TAXONOMIA
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'COMENTARIOS_TAXONOMIA'
        """)
        if cursor.fetchone()[0] > 0:
            cursor.execute("""
                SELECT TOP 5 * FROM COMENTARIOS_TAXONOMIA 
                WHERE Id_Incidente = 5
            """)
            comentarios_tax = cursor.fetchall()
            print(f"   COMENTARIOS_TAXONOMIA: {len(comentarios_tax)} registros para incidente 5")
        
        # EVIDENCIAS_TAXONOMIA  
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'EVIDENCIAS_TAXONOMIA'
        """)
        if cursor.fetchone()[0] > 0:
            cursor.execute("""
                SELECT TOP 5 * FROM EVIDENCIAS_TAXONOMIA 
                WHERE Id_Incidente = 5
            """)
            evidencias_tax = cursor.fetchall()
            print(f"   EVIDENCIAS_TAXONOMIA: {len(evidencias_tax)} registros para incidente 5")
        
        print("\n=== RESUMEN DE ESTADÍSTICAS POSIBLES ===")
        print("Para calcular las estadísticas del incidente 5:")
        print("- Archivos: Usar INCIDENTES_ARCHIVOS")
        print("- Comentarios: Usar COMENTARIOS_TAXONOMIA")
        print("- Evidencias: Usar EVIDENCIAS_TAXONOMIA")
        print("- Taxonomías: Usar INCIDENTES_TAXONOMIAS")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verificar_estructura()
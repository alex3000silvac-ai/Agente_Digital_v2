#!/usr/bin/env python3
"""
Verificar nombres correctos de tablas para estadísticas
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db_connection

def verificar_tablas():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("=== VERIFICANDO TABLAS RELACIONADAS CON INCIDENTES ===\n")
        
        # Buscar todas las tablas que contengan 'incident' en su nombre
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE' 
            AND (LOWER(TABLE_NAME) LIKE '%incident%' 
                 OR LOWER(TABLE_NAME) LIKE '%evidenc%' 
                 OR LOWER(TABLE_NAME) LIKE '%comentar%'
                 OR LOWER(TABLE_NAME) LIKE '%taxonom%'
                 OR LOWER(TABLE_NAME) LIKE '%archivo%')
            ORDER BY TABLE_NAME
        """)
        
        tablas = cursor.fetchall()
        print("Tablas encontradas:")
        for tabla in tablas:
            print(f"  - {tabla[0]}")
        
        # Verificar específicamente para incidente 5
        print("\n=== DATOS DEL INCIDENTE 5 ===")
        
        # 1. Verificar si existe tabla EVIDENCIAS
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'EVIDENCIAS'
        """)
        if cursor.fetchone()[0] > 0:
            cursor.execute("""
                SELECT COUNT(*) FROM EVIDENCIAS 
                WHERE IncidenteID = 5
            """)
            count = cursor.fetchone()[0]
            print(f"Evidencias en tabla EVIDENCIAS: {count}")
        
        # 2. Verificar tabla INCIDENTES_ARCHIVOS
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'INCIDENTES_ARCHIVOS'
        """)
        if cursor.fetchone()[0] > 0:
            cursor.execute("""
                SELECT COUNT(*) FROM INCIDENTES_ARCHIVOS 
                WHERE IncidenteID = 5
            """)
            count = cursor.fetchone()[0]
            print(f"Archivos en INCIDENTES_ARCHIVOS: {count}")
            
            # Mostrar algunos archivos
            cursor.execute("""
                SELECT TOP 3 Id_Archivo, Nombre_Archivo, Fecha_Subida
                FROM INCIDENTES_ARCHIVOS 
                WHERE IncidenteID = 5
                ORDER BY Fecha_Subida DESC
            """)
            archivos = cursor.fetchall()
            if archivos:
                print("  Últimos archivos:")
                for arch in archivos:
                    print(f"    - ID: {arch[0]}, Nombre: {arch[1]}, Fecha: {arch[2]}")
        
        # 3. Verificar tabla INCIDENTES_COMENTARIOS
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'INCIDENTES_COMENTARIOS'
        """)
        if cursor.fetchone()[0] > 0:
            cursor.execute("""
                SELECT COUNT(*) FROM INCIDENTES_COMENTARIOS 
                WHERE IncidenteID = 5
            """)
            count = cursor.fetchone()[0]
            print(f"Comentarios en INCIDENTES_COMENTARIOS: {count}")
            
            # Mostrar algunos comentarios
            cursor.execute("""
                SELECT TOP 3 Id_Comentario, Comentario, Fecha_Comentario
                FROM INCIDENTES_COMENTARIOS 
                WHERE IncidenteID = 5
                ORDER BY Fecha_Comentario DESC
            """)
            comentarios = cursor.fetchall()
            if comentarios:
                print("  Últimos comentarios:")
                for com in comentarios:
                    print(f"    - ID: {com[0]}, Texto: {com[1][:50]}..., Fecha: {com[2]}")
        
        # 4. Verificar tabla INCIDENTES_TAXONOMIAS
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'INCIDENTES_TAXONOMIAS'
        """)
        if cursor.fetchone()[0] > 0:
            cursor.execute("""
                SELECT COUNT(*) FROM INCIDENTES_TAXONOMIAS 
                WHERE Id_Incidente = 5
            """)
            count = cursor.fetchone()[0]
            print(f"Taxonomías seleccionadas: {count}")
            
            # Mostrar taxonomías
            cursor.execute("""
                SELECT it.Id_Taxonomia, ti.Categoria_del_Incidente, ti.Subcategoria_del_Incidente
                FROM INCIDENTES_TAXONOMIAS it
                LEFT JOIN TaxonomiaIncidentes ti ON it.Id_Taxonomia = ti.Id_Taxonomia
                WHERE it.Id_Incidente = 5
            """)
            taxonomias = cursor.fetchall()
            if taxonomias:
                print("  Taxonomías:")
                for tax in taxonomias:
                    print(f"    - ID: {tax[0]}, Categoría: {tax[1]}, Subcategoría: {tax[2]}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verificar_tablas()
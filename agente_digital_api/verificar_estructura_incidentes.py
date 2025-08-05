#!/usr/bin/env python3
"""
Script para verificar la estructura completa de las tablas relacionadas con incidentes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db_connection

def verificar_tablas():
    """Verifica que existan todas las tablas necesarias para el módulo de incidentes"""
    print("="*60)
    print("VERIFICACIÓN DE ESTRUCTURA DE TABLAS DE INCIDENTES")
    print("="*60)
    
    conn = get_db_connection()
    if not conn:
        print("❌ Error: No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor()
        
        # Lista de tablas a verificar
        tablas_requeridas = [
            'Incidentes',
            'EvidenciasIncidentes', 
            'HistorialIncidentes',
            'INCIDENTE_TAXONOMIA',
            'COMENTARIOS_TAXONOMIA',
            'TAXONOMIA_INCIDENTES'
        ]
        
        for tabla in tablas_requeridas:
            cursor.execute("""
                SELECT COUNT(*) as existe
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = ?
            """, (tabla,))
            
            existe = cursor.fetchone().existe
            
            if existe:
                print(f"✅ Tabla {tabla} existe")
                
                # Mostrar estructura de la tabla
                cursor.execute("""
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        IS_NULLABLE,
                        CHARACTER_MAXIMUM_LENGTH
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = ?
                    ORDER BY ORDINAL_POSITION
                """, (tabla,))
                
                print(f"   Estructura de {tabla}:")
                for col in cursor.fetchall():
                    nullable = "NULL" if col.IS_NULLABLE == "YES" else "NOT NULL"
                    longitud = f"({col.CHARACTER_MAXIMUM_LENGTH})" if col.CHARACTER_MAXIMUM_LENGTH and col.CHARACTER_MAXIMUM_LENGTH != -1 else ""
                    print(f"     - {col.COLUMN_NAME}: {col.DATA_TYPE}{longitud} {nullable}")
                print()
            else:
                print(f"❌ Tabla {tabla} NO existe")
        
        # Verificar relaciones
        print("\n" + "="*60)
        print("VERIFICACIÓN DE RELACIONES")
        print("="*60)
        
        # Verificar foreign keys
        cursor.execute("""
            SELECT 
                fk.name AS FK_Name,
                tp.name AS Parent_Table,
                cp.name AS Parent_Column,
                tr.name AS Referenced_Table,
                cr.name AS Referenced_Column
            FROM sys.foreign_keys AS fk
            INNER JOIN sys.tables AS tp ON fk.parent_object_id = tp.object_id
            INNER JOIN sys.tables AS tr ON fk.referenced_object_id = tr.object_id
            INNER JOIN sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
            INNER JOIN sys.columns AS cp ON fkc.parent_column_id = cp.column_id AND fkc.parent_object_id = cp.object_id
            INNER JOIN sys.columns AS cr ON fkc.referenced_column_id = cr.column_id AND fkc.referenced_object_id = cr.object_id
            WHERE tp.name IN ('Incidentes', 'EvidenciasIncidentes', 'HistorialIncidentes', 'INCIDENTE_TAXONOMIA', 'COMENTARIOS_TAXONOMIA')
        """)
        
        relaciones = cursor.fetchall()
        if relaciones:
            print("Relaciones encontradas:")
            for rel in relaciones:
                print(f"  - {rel.Parent_Table}.{rel.Parent_Column} → {rel.Referenced_Table}.{rel.Referenced_Column}")
        else:
            print("⚠️ No se encontraron relaciones de foreign key")
        
        # Verificar datos de ejemplo
        print("\n" + "="*60)
        print("VERIFICACIÓN DE DATOS")
        print("="*60)
        
        # Contar registros en cada tabla
        for tabla in tablas_requeridas:
            try:
                cursor.execute(f"SELECT COUNT(*) as total FROM {tabla}")
                total = cursor.fetchone().total
                print(f"  {tabla}: {total} registros")
            except:
                print(f"  {tabla}: Error al contar registros")
        
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
    finally:
        conn.close()

def verificar_integridad_datos():
    """Verifica la integridad de los datos entre tablas"""
    print("\n" + "="*60)
    print("VERIFICACIÓN DE INTEGRIDAD DE DATOS")
    print("="*60)
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Verificar incidentes sin archivos adjuntos
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM Incidentes i
            WHERE NOT EXISTS (
                SELECT 1 FROM EvidenciasIncidentes e 
                WHERE e.IncidenteID = i.IncidenteID
            )
        """)
        sin_archivos = cursor.fetchone().total
        print(f"  Incidentes sin archivos adjuntos: {sin_archivos}")
        
        # Verificar incidentes sin taxonomías
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM Incidentes i
            WHERE NOT EXISTS (
                SELECT 1 FROM INCIDENTE_TAXONOMIA it 
                WHERE it.IncidenteID = i.IncidenteID
            )
        """)
        sin_taxonomias = cursor.fetchone().total
        print(f"  Incidentes sin taxonomías asociadas: {sin_taxonomias}")
        
        # Verificar incidentes sin historial
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM Incidentes i
            WHERE NOT EXISTS (
                SELECT 1 FROM HistorialIncidentes h 
                WHERE h.IncidenteID = i.IncidenteID
            )
        """)
        sin_historial = cursor.fetchone().total
        print(f"  Incidentes sin historial de cambios: {sin_historial}")
        
        # Verificar archivos huérfanos
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM EvidenciasIncidentes e
            WHERE NOT EXISTS (
                SELECT 1 FROM Incidentes i 
                WHERE i.IncidenteID = e.IncidenteID
            )
        """)
        archivos_huerfanos = cursor.fetchone().total
        if archivos_huerfanos > 0:
            print(f"  ⚠️ Archivos huérfanos sin incidente: {archivos_huerfanos}")
        else:
            print(f"  ✅ No hay archivos huérfanos")
        
    except Exception as e:
        print(f"❌ Error verificando integridad: {e}")
    finally:
        conn.close()

def main():
    """Función principal"""
    verificar_tablas()
    verificar_integridad_datos()
    
    print("\n" + "="*60)
    print("VERIFICACIÓN COMPLETADA")
    print("="*60)

if __name__ == "__main__":
    main()
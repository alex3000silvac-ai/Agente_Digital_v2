#!/usr/bin/env python3
"""
Script para verificar y poblar datos de origen en incidentes existentes
"""

import sys
import os
sys.path.append('.')
from app.database import get_db_connection

def verificar_estructura_tabla():
    """Verifica la estructura de la tabla Incidentes"""
    
    print("🔍 Verificando estructura de la tabla Incidentes...\n")
    
    conn = get_db_connection()
    if not conn:
        print("❌ No se pudo conectar a la base de datos")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar columnas de la tabla
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'Incidentes'
            AND COLUMN_NAME IN ('OrigenIncidente', 'SistemasAfectados', 'AccionesInmediatas', 'ResponsableCliente')
            ORDER BY ORDINAL_POSITION
        """)
        
        columnas = cursor.fetchall()
        
        if not columnas:
            print("❌ No se encontraron columnas de origen en la tabla Incidentes")
            return False
        
        print("✅ Columnas de origen encontradas:")
        for col in columnas:
            print(f"  - {col[0]} ({col[1]}) - Nullable: {col[2]} - Default: {col[3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando estructura: {e}")
        return False
    finally:
        if conn:
            conn.close()

def verificar_datos_incidente_especifico(incidente_id):
    """Verifica los datos de un incidente específico"""
    
    print(f"🔍 Verificando datos del incidente {incidente_id}...\n")
    
    conn = get_db_connection()
    if not conn:
        print("❌ No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor()
        
        # Obtener datos del incidente
        cursor.execute("""
            SELECT 
                IncidenteID,
                Titulo,
                OrigenIncidente,
                SistemasAfectados,
                AccionesInmediatas,
                ResponsableCliente,
                FechaCreacion,
                CreadoPor
            FROM Incidentes
            WHERE IncidenteID = ?
        """, (incidente_id,))
        
        row = cursor.fetchone()
        
        if not row:
            print(f"❌ No se encontró el incidente {incidente_id}")
            return
        
        print(f"✅ Datos del incidente {incidente_id}:")
        print(f"  - Título: {row[1]}")
        print(f"  - OrigenIncidente: '{row[2]}' {'(VACÍO)' if not row[2] else ''}")
        print(f"  - SistemasAfectados: '{row[3]}' {'(VACÍO)' if not row[3] else ''}")
        print(f"  - AccionesInmediatas: '{row[4]}' {'(VACÍO)' if not row[4] else ''}")
        print(f"  - ResponsableCliente: '{row[5]}' {'(VACÍO)' if not row[5] else ''}")
        print(f"  - FechaCreacion: {row[6]}")
        print(f"  - CreadoPor: {row[7]}")
        
        # Verificar si hay campos vacíos
        campos_vacios = []
        if not row[2]:
            campos_vacios.append('OrigenIncidente')
        if not row[3]:
            campos_vacios.append('SistemasAfectados')
        if not row[4]:
            campos_vacios.append('AccionesInmediatas')
        if not row[5]:
            campos_vacios.append('ResponsableCliente')
        
        if campos_vacios:
            print(f"\n⚠️  Campos vacíos encontrados: {', '.join(campos_vacios)}")
            return True  # Necesita actualización
        else:
            print(f"\n✅ Todos los campos de origen tienen datos")
            return False  # No necesita actualización
        
    except Exception as e:
        print(f"❌ Error verificando incidente: {e}")
        return False
    finally:
        if conn:
            conn.close()

def verificar_todos_incidentes():
    """Verifica todos los incidentes en la base de datos"""
    
    print("🔍 Verificando todos los incidentes...\n")
    
    conn = get_db_connection()
    if not conn:
        print("❌ No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor()
        
        # Obtener estadísticas de incidentes
        cursor.execute("""
            SELECT 
                COUNT(*) as Total,
                COUNT(CASE WHEN OrigenIncidente IS NOT NULL AND OrigenIncidente != '' THEN 1 END) as ConOrigen,
                COUNT(CASE WHEN SistemasAfectados IS NOT NULL AND SistemasAfectados != '' THEN 1 END) as ConSistemas,
                COUNT(CASE WHEN AccionesInmediatas IS NOT NULL AND AccionesInmediatas != '' THEN 1 END) as ConAcciones,
                COUNT(CASE WHEN ResponsableCliente IS NOT NULL AND ResponsableCliente != '' THEN 1 END) as ConResponsable
            FROM Incidentes
        """)
        
        stats = cursor.fetchone()
        
        print(f"📊 Estadísticas de incidentes:")
        print(f"  - Total de incidentes: {stats[0]}")
        print(f"  - Con OrigenIncidente: {stats[1]} ({stats[1]/stats[0]*100:.1f}%)")
        print(f"  - Con SistemasAfectados: {stats[2]} ({stats[2]/stats[0]*100:.1f}%)")
        print(f"  - Con AccionesInmediatas: {stats[3]} ({stats[3]/stats[0]*100:.1f}%)")
        print(f"  - Con ResponsableCliente: {stats[4]} ({stats[4]/stats[0]*100:.1f}%)")
        
        # Obtener incidentes con campos vacíos
        cursor.execute("""
            SELECT 
                IncidenteID,
                Titulo,
                OrigenIncidente,
                SistemasAfectados,
                AccionesInmediatas,
                ResponsableCliente
            FROM Incidentes
            WHERE OrigenIncidente IS NULL OR OrigenIncidente = ''
               OR SistemasAfectados IS NULL 
               OR AccionesInmediatas IS NULL 
               OR ResponsableCliente IS NULL OR ResponsableCliente = ''
            ORDER BY IncidenteID
        """)
        
        incidentes_vacios = cursor.fetchall()
        
        if incidentes_vacios:
            print(f"\n⚠️  Incidentes con campos vacíos ({len(incidentes_vacios)}):")
            for inc in incidentes_vacios:
                print(f"  - ID {inc[0]}: {inc[1]}")
                campos_vacios = []
                if not inc[2]:
                    campos_vacios.append('Origen')
                if not inc[3]:
                    campos_vacios.append('Sistemas')
                if not inc[4]:
                    campos_vacios.append('Acciones')
                if not inc[5]:
                    campos_vacios.append('Responsable')
                print(f"    Campos vacíos: {', '.join(campos_vacios)}")
        else:
            print(f"\n✅ Todos los incidentes tienen campos de origen completos")
        
    except Exception as e:
        print(f"❌ Error verificando incidentes: {e}")
    finally:
        if conn:
            conn.close()

def poblar_datos_origen_incidente(incidente_id):
    """Pobla los datos de origen de un incidente específico"""
    
    print(f"🔧 Poblando datos de origen para incidente {incidente_id}...\n")
    
    conn = get_db_connection()
    if not conn:
        print("❌ No se pudo conectar a la base de datos")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Actualizar campos vacíos con valores por defecto
        cursor.execute("""
            UPDATE Incidentes
            SET 
                OrigenIncidente = CASE 
                    WHEN OrigenIncidente IS NULL OR OrigenIncidente = '' 
                    THEN 'Sistema interno' 
                    ELSE OrigenIncidente 
                END,
                SistemasAfectados = CASE 
                    WHEN SistemasAfectados IS NULL 
                    THEN 'No especificado' 
                    ELSE SistemasAfectados 
                END,
                AccionesInmediatas = CASE 
                    WHEN AccionesInmediatas IS NULL 
                    THEN 'Pendiente de definir' 
                    ELSE AccionesInmediatas 
                END,
                ResponsableCliente = CASE 
                    WHEN ResponsableCliente IS NULL OR ResponsableCliente = '' 
                    THEN 'No asignado' 
                    ELSE ResponsableCliente 
                END
            WHERE IncidenteID = ?
        """, (incidente_id,))
        
        rows_affected = cursor.rowcount
        conn.commit()
        
        if rows_affected > 0:
            print(f"✅ Incidente {incidente_id} actualizado exitosamente")
            
            # Verificar los datos actualizados
            cursor.execute("""
                SELECT 
                    OrigenIncidente,
                    SistemasAfectados,
                    AccionesInmediatas,
                    ResponsableCliente
                FROM Incidentes
                WHERE IncidenteID = ?
            """, (incidente_id,))
            
            row = cursor.fetchone()
            if row:
                print(f"  - OrigenIncidente: '{row[0]}'")
                print(f"  - SistemasAfectados: '{row[1]}'")
                print(f"  - AccionesInmediatas: '{row[2]}'")
                print(f"  - ResponsableCliente: '{row[3]}'")
            
            return True
        else:
            print(f"⚠️  No se realizaron cambios en el incidente {incidente_id}")
            return False
        
    except Exception as e:
        print(f"❌ Error actualizando incidente: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Función principal"""
    
    print("🚀 Verificación y Corrección de Datos de Origen en Incidentes\n")
    
    # 1. Verificar estructura de la tabla
    if not verificar_estructura_tabla():
        print("\n❌ No se puede continuar sin la estructura correcta de la tabla")
        return
    
    print("\n" + "="*60 + "\n")
    
    # 2. Verificar todos los incidentes
    verificar_todos_incidentes()
    
    print("\n" + "="*60 + "\n")
    
    # 3. Verificar incidente específico (ID 3)
    necesita_actualizacion = verificar_datos_incidente_especifico(3)
    
    if necesita_actualizacion:
        print("\n" + "="*60 + "\n")
        
        # 4. Poblar datos del incidente 3
        if poblar_datos_origen_incidente(3):
            print("\n" + "="*60 + "\n")
            
            # 5. Verificar de nuevo
            print("🔍 Verificando datos después de la actualización...\n")
            verificar_datos_incidente_especifico(3)
    
    print("\n🎉 Verificación completada")
    print("\n💡 Próximos pasos:")
    print("  1. Reiniciar el servidor Flask")
    print("  2. Probar el endpoint GET /api/admin/incidentes/3")
    print("  3. Verificar que los datos de origen aparezcan en la interfaz")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script para verificar y limpiar registros duplicados en CumplimientoEmpresa
"""

import pyodbc
from datetime import datetime

# Configuración de la base de datos
DB_CONFIG = {
    'driver': 'ODBC Driver 17 for SQL Server',
    'server': '192.168.100.125',
    'database': 'AgenteDigitalDB',
    'username': 'app_usuario',
    'password': 'ClaveSegura123!'
}

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        conn_str = f"DRIVER={{{DB_CONFIG['driver']}}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']};Encrypt=no;TrustServerCertificate=yes"
        conn = pyodbc.connect(conn_str)
        # Configurar codificación
        conn.setdecoding(pyodbc.SQL_CHAR, encoding='latin-1')
        conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16le')
        conn.setencoding(encoding='utf-8')
        return conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

def verificar_duplicados():
    """Verificar y mostrar registros duplicados"""
    conn = get_db_connection()
    if not conn:
        print("ERROR: No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor()
        
        print("=" * 80)
        print("VERIFICACIÓN DE REGISTROS DUPLICADOS EN CumplimientoEmpresa")
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Buscar duplicados
        cursor.execute("""
            SELECT 
                EmpresaID,
                ObligacionID,
                COUNT(*) as Cantidad,
                STRING_AGG(CAST(CumplimientoID as VARCHAR), ', ') as IDs
            FROM CumplimientoEmpresa
            GROUP BY EmpresaID, ObligacionID
            HAVING COUNT(*) > 1
            ORDER BY EmpresaID, ObligacionID
        """)
        
        duplicados = cursor.fetchall()
        
        if not duplicados:
            print("\n✅ No se encontraron registros duplicados")
            return
        
        print(f"\n⚠️ Se encontraron {len(duplicados)} combinaciones duplicadas:")
        print("-" * 80)
        
        for row in duplicados:
            print(f"\nEmpresa ID: {row.EmpresaID}, Obligación ID: {row.ObligacionID}")
            print(f"  Cantidad de registros: {row.Cantidad}")
            print(f"  IDs de cumplimiento: {row.IDs}")
            
            # Mostrar detalles de cada registro duplicado
            cursor.execute("""
                SELECT 
                    CumplimientoID,
                    Estado,
                    PorcentajeAvance,
                    Responsable,
                    FechaTermino
                FROM CumplimientoEmpresa
                WHERE EmpresaID = ? AND ObligacionID = ?
                ORDER BY CumplimientoID
            """, (row.EmpresaID, row.ObligacionID))
            
            detalles = cursor.fetchall()
            for detalle in detalles:
                print(f"    - ID {detalle.CumplimientoID}: Estado={detalle.Estado}, "
                      f"Avance={detalle.PorcentajeAvance}%, "
                      f"Responsable={detalle.Responsable or 'N/A'}")
        
        print("\n" + "=" * 80)
        print("OPCIONES DE LIMPIEZA:")
        print("1. Mantener el registro más reciente (mayor ID)")
        print("2. Mantener el registro con mayor porcentaje de avance")
        print("3. No hacer nada (resolver manualmente)")
        
        opcion = input("\nSeleccione una opción (1-3): ")
        
        if opcion == "1":
            limpiar_manteniendo_mas_reciente(conn, cursor)
        elif opcion == "2":
            limpiar_manteniendo_mayor_avance(conn, cursor)
        else:
            print("\nNo se realizaron cambios.")
            
    except Exception as e:
        print(f"Error durante verificación: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

def limpiar_manteniendo_mas_reciente(conn, cursor):
    """Eliminar duplicados manteniendo el registro más reciente"""
    try:
        # Eliminar duplicados manteniendo el de mayor ID
        cursor.execute("""
            DELETE FROM CumplimientoEmpresa
            WHERE CumplimientoID NOT IN (
                SELECT MAX(CumplimientoID)
                FROM CumplimientoEmpresa
                GROUP BY EmpresaID, ObligacionID
            )
        """)
        
        registros_eliminados = cursor.rowcount
        conn.commit()
        
        print(f"\n✅ Se eliminaron {registros_eliminados} registros duplicados")
        print("   Se mantuvieron los registros más recientes (mayor ID)")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error al limpiar duplicados: {e}")

def limpiar_manteniendo_mayor_avance(conn, cursor):
    """Eliminar duplicados manteniendo el registro con mayor avance"""
    try:
        # Primero identificar los registros a mantener
        cursor.execute("""
            WITH RankedCumplimientos AS (
                SELECT 
                    CumplimientoID,
                    ROW_NUMBER() OVER (
                        PARTITION BY EmpresaID, ObligacionID 
                        ORDER BY PorcentajeAvance DESC, CumplimientoID DESC
                    ) as rn
                FROM CumplimientoEmpresa
            )
            DELETE FROM CumplimientoEmpresa
            WHERE CumplimientoID IN (
                SELECT CumplimientoID 
                FROM RankedCumplimientos 
                WHERE rn > 1
            )
        """)
        
        registros_eliminados = cursor.rowcount
        conn.commit()
        
        print(f"\n✅ Se eliminaron {registros_eliminados} registros duplicados")
        print("   Se mantuvieron los registros con mayor porcentaje de avance")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error al limpiar duplicados: {e}")

if __name__ == '__main__':
    verificar_duplicados()
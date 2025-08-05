#!/usr/bin/env python3
"""
Script para verificar un cumplimiento específico
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
        conn.setdecoding(pyodbc.SQL_CHAR, encoding='latin-1')
        conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16le')
        conn.setencoding(encoding='utf-8')
        return conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

def verificar_cumplimiento():
    """Verificar cumplimiento específico"""
    conn = get_db_connection()
    if not conn:
        print("ERROR: No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor()
        
        print("=" * 80)
        print("VERIFICACIÓN DE CUMPLIMIENTO ESPECÍFICO")
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        empresa_id = 3
        obligacion_id = 'OBL_002_REP_007'
        
        print(f"\nBuscando: EmpresaID={empresa_id}, ObligacionID='{obligacion_id}'")
        
        # Buscar registro existente
        cursor.execute("""
            SELECT 
                CumplimientoID,
                Estado,
                PorcentajeAvance,
                Responsable,
                FechaTermino
            FROM CumplimientoEmpresa 
            WHERE EmpresaID = ? AND ObligacionID = ?
        """, (empresa_id, obligacion_id))
        
        result = cursor.fetchone()
        
        if result:
            print(f"\n✅ Registro encontrado:")
            print(f"   CumplimientoID: {result.CumplimientoID}")
            print(f"   Estado: {result.Estado}")
            print(f"   PorcentajeAvance: {result.PorcentajeAvance}%")
            print(f"   Responsable: {result.Responsable or 'N/A'}")
            print(f"   FechaTermino: {result.FechaTermino or 'N/A'}")
        else:
            print(f"\n❌ No se encontró ningún registro")
            
        # Verificar todos los cumplimientos de la empresa
        print(f"\n\nTodos los cumplimientos de la empresa {empresa_id}:")
        print("-" * 80)
        
        cursor.execute("""
            SELECT 
                CumplimientoID,
                ObligacionID,
                Estado,
                PorcentajeAvance
            FROM CumplimientoEmpresa 
            WHERE EmpresaID = ?
            ORDER BY ObligacionID
        """, (empresa_id,))
        
        todos = cursor.fetchall()
        
        if todos:
            for row in todos:
                print(f"ID: {row.CumplimientoID:4d} | Obligación: {row.ObligacionID:20s} | "
                      f"Estado: {row.Estado:15s} | Avance: {row.PorcentajeAvance:3d}%")
        else:
            print("No hay cumplimientos registrados para esta empresa")
            
    except Exception as e:
        print(f"Error durante verificación: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == '__main__':
    verificar_cumplimiento()
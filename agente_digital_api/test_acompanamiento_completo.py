#!/usr/bin/env python3
"""
Script para probar que el endpoint de acompañamiento devuelve todos los campos
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
        print(f"Error conectando: {e}")
        return None

def test_acompanamiento_data():
    """Probar los datos que devolvería el endpoint"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        empresa_id = 3
        
        print("=" * 80)
        print("SIMULACIÓN DE ENDPOINT DE ACOMPAÑAMIENTO")
        print(f"Empresa ID: {empresa_id}")
        print("=" * 80)
        
        # Primero obtener tipo de empresa
        cursor.execute("SELECT RazonSocial, TipoEmpresa FROM Empresas WHERE EmpresaID = ?", (empresa_id,))
        empresa_info = cursor.fetchone()
        
        if not empresa_info:
            print("Empresa no encontrada")
            return
            
        print(f"Empresa: {empresa_info.RazonSocial}")
        print(f"Tipo: {empresa_info.TipoEmpresa}")
        print("-" * 80)
        
        # Ejecutar el mismo query que el endpoint
        query = """
            SELECT DISTINCT
                O.ObligacionID,
                O.ArticuloNorma,
                O.Descripcion,
                O.MedioDeVerificacionSugerido,
                O.AplicaPara,
                CE.CumplimientoID,
                ISNULL(CE.Estado, 'Pendiente') as Estado,
                ISNULL(CE.PorcentajeAvance, 0) as PorcentajeAvance,
                CE.Responsable,
                CE.FechaTermino,
                CE.ObservacionesCiberseguridad,
                CE.ObservacionesLegales
            FROM OBLIGACIONES O
            LEFT JOIN CumplimientoEmpresa CE ON O.ObligacionID = CE.ObligacionID AND CE.EmpresaID = ?
            WHERE (O.AplicaPara = ? OR O.AplicaPara = 'Ambos')
            ORDER BY O.ArticuloNorma
        """
        
        cursor.execute(query, (empresa_id, empresa_info.TipoEmpresa))
        rows = cursor.fetchall()
        
        print(f"\nTotal de obligaciones encontradas: {len(rows)}")
        print("\nPrimeras 3 obligaciones con datos completos:")
        print("=" * 80)
        
        for i, row in enumerate(rows[:3]):
            print(f"\nObligación {i+1}:")
            print(f"  ObligacionID: {row.ObligacionID}")
            print(f"  ArticuloNorma: {row.ArticuloNorma}")
            print(f"  Descripcion: {row.Descripcion[:50]}...")
            print(f"  CumplimientoID: {row.CumplimientoID or 'NULL (no guardado)'}")
            print(f"  Estado: {row.Estado}")
            print(f"  PorcentajeAvance: {row.PorcentajeAvance}%")
            print(f"  Responsable: {row.Responsable or 'N/A'}")
            print(f"  FechaTermino: {row.FechaTermino or 'N/A'}")
            print(f"  ObservacionesCiberseguridad: {row.ObservacionesCiberseguridad or 'N/A'}")
            print(f"  ObservacionesLegales: {row.ObservacionesLegales or 'N/A'}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == '__main__':
    test_acompanamiento_data()
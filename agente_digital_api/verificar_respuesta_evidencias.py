#!/usr/bin/env python3
"""
Script para verificar la respuesta exacta del endpoint de evidencias
"""

import pyodbc
import json
from datetime import datetime

# Configuración de la base de datos
DB_CONFIG = {
    'driver': 'ODBC Driver 17 for SQL Server',
    'server': '192.168.100.125',
    'database': 'AgenteDigitalDB',
    'username': 'app_usuario',
    'password': 'ClaveSegura123!'
}

def verificar_evidencias_cumplimiento_3():
    """Verificar qué datos exactos hay para cumplimiento ID 3"""
    try:
        conn_str = f"DRIVER={{{DB_CONFIG['driver']}}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']};Encrypt=no;TrustServerCertificate=yes"
        conn = pyodbc.connect(conn_str)
        conn.setdecoding(pyodbc.SQL_CHAR, encoding='latin-1')
        conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16le')
        conn.setencoding(encoding='utf-8')
        
        cursor = conn.cursor()
        
        print("=" * 80)
        print("VERIFICANDO EVIDENCIAS PARA CUMPLIMIENTO ID 3")
        print("=" * 80)
        
        # Ejecutar la misma consulta que el endpoint
        cursor.execute("""
            SELECT 
                EvidenciaID,
                CumplimientoID,
                NombreArchivoOriginal,
                TipoArchivo,
                TamanoArchivoKB,
                FechaSubida,
                UsuarioQueSubio,
                Descripcion,
                Version
            FROM EvidenciasCumplimiento
            WHERE CumplimientoID = 3
            ORDER BY FechaSubida DESC
        """)
        
        rows = cursor.fetchall()
        print(f"\n✅ Registros encontrados: {len(rows)}")
        
        if rows:
            print("\nDatos crudos de la base de datos:")
            for i, row in enumerate(rows):
                print(f"\nRegistro {i+1}:")
                print(f"  EvidenciaID: {row.EvidenciaID}")
                print(f"  CumplimientoID: {row.CumplimientoID}")
                print(f"  NombreArchivoOriginal: '{row.NombreArchivoOriginal}' (tipo: {type(row.NombreArchivoOriginal)})")
                print(f"  TipoArchivo: '{row.TipoArchivo}' (tipo: {type(row.TipoArchivo)})")
                print(f"  TamanoArchivoKB: {row.TamanoArchivoKB}")
                print(f"  FechaSubida: {row.FechaSubida}")
                print(f"  UsuarioQueSubio: '{row.UsuarioQueSubio}'")
                print(f"  Descripcion: '{row.Descripcion}'")
                print(f"  Version: {row.Version}")
                
                # Simular la conversión que hace el endpoint
                evidencia_dict = {
                    "EvidenciaID": row.EvidenciaID,
                    "CumplimientoID": row.CumplimientoID,
                    "NombreArchivoOriginal": row.NombreArchivoOriginal,
                    "TipoArchivo": row.TipoArchivo or "",
                    "TamanoArchivoKB": row.TamanoArchivoKB or 0,
                    "FechaSubida": row.FechaSubida.strftime('%Y-%m-%d %H:%M:%S') if row.FechaSubida else None,
                    "UsuarioQueSubio": row.UsuarioQueSubio or "Sistema",
                    "Descripcion": row.Descripcion or "",
                    "Version": getattr(row, 'Version', 1)
                }
                
                print(f"\nJSON simulado del endpoint:")
                print(json.dumps(evidencia_dict, indent=2, ensure_ascii=False))
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verificar_evidencias_cumplimiento_3()
#!/usr/bin/env python3
"""
Script para verificar las obligaciones en la base de datos
y su configuración AplicaPara
"""

import pyodbc
import sys
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
        return conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

def verificar_obligaciones():
    """Verificar obligaciones en la base de datos"""
    conn = get_db_connection()
    if not conn:
        print("ERROR: No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor()
        
        print("=" * 80)
        print("VERIFICACIÓN DE OBLIGACIONES EN BASE DE DATOS")
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # 1. Contar total de obligaciones
        cursor.execute("SELECT COUNT(*) FROM OBLIGACIONES")
        total = cursor.fetchone()[0]
        print(f"\nTotal de obligaciones en la tabla: {total}")
        
        # 2. Contar por tipo (AplicaPara)
        print("\nDistribución por tipo (AplicaPara):")
        cursor.execute("""
            SELECT AplicaPara, COUNT(*) as Cantidad
            FROM OBLIGACIONES
            GROUP BY AplicaPara
            ORDER BY AplicaPara
        """)
        
        for row in cursor.fetchall():
            print(f"  {row.AplicaPara}: {row.Cantidad} obligaciones")
        
        # 3. Verificar empresas por tipo
        print("\nEmpresas por tipo:")
        cursor.execute("""
            SELECT TipoEmpresa, COUNT(*) as Cantidad
            FROM Empresas
            WHERE TipoEmpresa IS NOT NULL
            GROUP BY TipoEmpresa
            ORDER BY TipoEmpresa
        """)
        
        for row in cursor.fetchall():
            print(f"  {row.TipoEmpresa}: {row.Cantidad} empresas")
        
        # 4. Verificar empresa específica ID=3
        print("\nVerificando empresa con ID=3:")
        cursor.execute("SELECT EmpresaID, RazonSocial, TipoEmpresa FROM Empresas WHERE EmpresaID = 3")
        empresa = cursor.fetchone()
        
        if empresa:
            print(f"  ID: {empresa.EmpresaID}")
            print(f"  Razón Social: {empresa.RazonSocial}")
            print(f"  Tipo de Empresa: {empresa.TipoEmpresa}")
            
            # 5. Contar obligaciones que aplicarían a esta empresa
            tipo_empresa = empresa.TipoEmpresa
            if tipo_empresa:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM OBLIGACIONES 
                    WHERE AplicaPara = ? OR AplicaPara = 'Ambos'
                """, (tipo_empresa,))
                count = cursor.fetchone()[0]
                print(f"\nObligaciones que aplican para tipo '{tipo_empresa}': {count}")
                
                # Mostrar primeras 5 obligaciones
                print("\nPrimeras 5 obligaciones para este tipo:")
                cursor.execute("""
                    SELECT TOP 5 ObligacionID, ArticuloNorma, Descripcion, AplicaPara
                    FROM OBLIGACIONES 
                    WHERE AplicaPara = ? OR AplicaPara = 'Ambos'
                    ORDER BY ArticuloNorma
                """, (tipo_empresa,))
                
                for row in cursor.fetchall():
                    print(f"  [{row.ObligacionID}] Art. {row.ArticuloNorma} - {row.Descripcion[:50]}... (Aplica: {row.AplicaPara})")
        else:
            print("  No se encontró empresa con ID=3")
        
        # 6. Verificar estructura de tabla CumplimientoEmpresa
        print("\n" + "-" * 80)
        print("Verificando estructura de tabla CumplimientoEmpresa:")
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'CumplimientoEmpresa'
            ORDER BY ORDINAL_POSITION
        """)
        
        columns = [row[0] for row in cursor.fetchall()]
        print(f"Columnas encontradas: {', '.join(columns)}")
        
        # Verificar columnas problemáticas
        problematic = ['Observaciones', 'ArchivoEvidencia', 'RutaEvidencia']
        for col in problematic:
            if col in columns:
                print(f"  ⚠️ ADVERTENCIA: Columna '{col}' SÍ existe")
            else:
                print(f"  ✓ Columna '{col}' NO existe (correcto)")
        
    except Exception as e:
        print(f"Error durante verificación: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == '__main__':
    verificar_obligaciones()
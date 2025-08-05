#!/usr/bin/env python3
"""
Script para verificar evidencias en la base de datos
"""

import pyodbc

# Configuración de la base de datos
DB_CONFIG = {
    'driver': 'ODBC Driver 17 for SQL Server',
    'server': '192.168.100.125',
    'database': 'AgenteDigitalDB',
    'username': 'app_usuario',
    'password': 'ClaveSegura123!'
}

def verificar_evidencias():
    """Verificar evidencias para cumplimiento ID 3"""
    try:
        conn_str = f"DRIVER={{{DB_CONFIG['driver']}}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']};Encrypt=no;TrustServerCertificate=yes"
        conn = pyodbc.connect(conn_str)
        conn.setdecoding(pyodbc.SQL_CHAR, encoding='latin-1')
        conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16le')
        conn.setencoding(encoding='utf-8')
        
        cursor = conn.cursor()
        
        print("=" * 60)
        print("VERIFICANDO CUMPLIMIENTO ID 3")
        print("=" * 60)
        
        # Verificar si existe el cumplimiento
        cursor.execute("""
            SELECT 
                CumplimientoID,
                EmpresaID,
                ObligacionID,
                Estado,
                PorcentajeAvance
            FROM CumplimientoEmpresa 
            WHERE CumplimientoID = 3
        """)
        
        cumplimiento = cursor.fetchone()
        if cumplimiento:
            print(f"✅ Cumplimiento encontrado:")
            print(f"   - ID: {cumplimiento.CumplimientoID}")
            print(f"   - Empresa ID: {cumplimiento.EmpresaID}")
            print(f"   - Obligación ID: {cumplimiento.ObligacionID}")
            print(f"   - Estado: {cumplimiento.Estado}")
            print(f"   - Avance: {cumplimiento.PorcentajeAvance}%")
        else:
            print("❌ No se encontró el cumplimiento ID 3")
            
        print("\n" + "=" * 60)
        print("VERIFICANDO TABLA DE EVIDENCIAS")
        print("=" * 60)
        
        # Verificar si existe la tabla
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'EvidenciasCumplimiento'
        """)
        
        if cursor.fetchone():
            print("✅ La tabla EvidenciasCumplimiento existe")
            
            # Verificar evidencias para cumplimiento 3
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM EvidenciasCumplimiento
                WHERE CumplimientoID = 3
            """)
            
            total = cursor.fetchone().total
            print(f"\n📊 Total de evidencias para cumplimiento ID 3: {total}")
            
            if total > 0:
                # Mostrar detalles de las evidencias
                cursor.execute("""
                    SELECT 
                        EvidenciaID,
                        NombreArchivoOriginal,
                        FechaSubida,
                        TamanoArchivoKB,
                        UsuarioQueSubio
                    FROM EvidenciasCumplimiento
                    WHERE CumplimientoID = 3
                    ORDER BY FechaSubida DESC
                """)
                
                print("\nDetalles de evidencias:")
                for row in cursor.fetchall():
                    print(f"\n   📄 Evidencia ID: {row.EvidenciaID}")
                    print(f"      - Archivo: {row.NombreArchivoOriginal}")
                    print(f"      - Fecha: {row.FechaSubida}")
                    print(f"      - Tamaño: {row.TamanoArchivoKB:.2f} KB")
                    print(f"      - Usuario: {row.UsuarioQueSubio}")
            
            # Verificar evidencias en general
            cursor.execute("""
                SELECT 
                    CumplimientoID,
                    COUNT(*) as cantidad
                FROM EvidenciasCumplimiento
                GROUP BY CumplimientoID
                ORDER BY cantidad DESC
            """)
            
            print("\n" + "=" * 60)
            print("RESUMEN DE EVIDENCIAS POR CUMPLIMIENTO")
            print("=" * 60)
            
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    print(f"Cumplimiento ID {row.CumplimientoID}: {row.cantidad} evidencias")
            else:
                print("No hay evidencias en ningún cumplimiento")
                
        else:
            print("❌ La tabla EvidenciasCumplimiento NO existe")
            
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    verificar_evidencias()
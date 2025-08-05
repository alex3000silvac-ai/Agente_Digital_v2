#!/usr/bin/env python3
"""
Script para agregar observaciones de prueba
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

def actualizar_observaciones():
    """Actualizar observaciones para prueba"""
    try:
        conn_str = f"DRIVER={{{DB_CONFIG['driver']}}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']};Encrypt=no;TrustServerCertificate=yes"
        conn = pyodbc.connect(conn_str)
        conn.setdecoding(pyodbc.SQL_CHAR, encoding='latin-1')
        conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16le')
        conn.setencoding(encoding='utf-8')
        
        cursor = conn.cursor()
        
        print("Actualizando observaciones de prueba...")
        
        cursor.execute("""
            UPDATE CumplimientoEmpresa 
            SET ObservacionesCiberseguridad = 'Prueba de observación de ciberseguridad',
                ObservacionesLegales = 'Prueba de observación legal',
                Responsable = 'Juan Pérez'
            WHERE CumplimientoID = 3
        """)
        
        conn.commit()
        print("✅ Observaciones actualizadas")
        
        # Verificar
        cursor.execute("""
            SELECT ObservacionesCiberseguridad, ObservacionesLegales, Responsable
            FROM CumplimientoEmpresa 
            WHERE CumplimientoID = 3
        """)
        
        row = cursor.fetchone()
        print(f"\nDatos actualizados:")
        print(f"  ObservacionesCiberseguridad: {row.ObservacionesCiberseguridad}")
        print(f"  ObservacionesLegales: {row.ObservacionesLegales}")
        print(f"  Responsable: {row.Responsable}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    actualizar_observaciones()
#!/usr/bin/env python3
"""
Script para corregir los datos de la tabla TAXONOMIA_INCIDENTES
"""

import pyodbc
import sys

# Configuración de la base de datos
DB_CONFIG = {
    'driver': 'ODBC Driver 17 for SQL Server',
    'server': 'localhost',
    'database': 'AgenteDigitalDB',
    'trusted_connection': 'yes'
}

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        conn_str = f"DRIVER={{{DB_CONFIG['driver']}}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};TRUSTED_CONNECTION={DB_CONFIG['trusted_connection']}"
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

def fix_data_mapping(cursor):
    """Corregir el mapeo de datos incorrecto"""
    
    print("Corrigiendo mapeo de datos...")
    
    # Mover Subcategoria_del_Incidente a AplicaTipoEmpresa y limpiar Subcategoria
    cursor.execute("""
        UPDATE TAXONOMIA_INCIDENTES 
        SET 
            AplicaTipoEmpresa = Subcategoria_del_Incidente,
            Subcategoria_del_Incidente = NULL
        WHERE AplicaTipoEmpresa IS NULL AND Subcategoria_del_Incidente IN ('AMBAS', 'OIV', 'PSE')
    """)
    
    affected_rows = cursor.rowcount
    print(f"Actualizados {affected_rows} registros")
    
    # Insertar datos adicionales para PSE específicamente
    additional_pse_taxonomies = [
        ('INC_PSE_PAGO_FRAUD', 'Impacto en servicios de pago', 'Fraude en transacciones', 'Transacciones fraudulentas', 'Operaciones de pago no autorizadas', 'PSE'),
        ('INC_PSE_PAGO_LAVAN', 'Impacto en servicios de pago', 'Lavado de dinero', 'Uso del sistema para lavado de activos', 'Utilización para blanqueo de capitales', 'PSE'),
        ('INC_PSE_PAGO_SKIMM', 'Impacto en servicios de pago', 'Skimming de tarjetas', 'Clonación de tarjetas de pago', 'Captura ilegal de datos de tarjetas', 'PSE'),
    ]
    
    # Verificar si ya existen estos registros
    for tax in additional_pse_taxonomies:
        cursor.execute("SELECT COUNT(*) FROM TAXONOMIA_INCIDENTES WHERE Id_Incidente = ?", (tax[0],))
        exists = cursor.fetchone()[0] > 0
        
        if not exists:
            cursor.execute("""
                INSERT INTO TAXONOMIA_INCIDENTES (
                    Id_Incidente, Area, Efecto, Categoria_del_Incidente, 
                    Subcategoria_del_Incidente, AplicaTipoEmpresa
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, tax)
            print(f"Insertado: {tax[0]}")
    
    cursor.commit()

def main():
    conn = get_db_connection()
    if not conn:
        print("ERROR: No se pudo conectar a la base de datos")
        sys.exit(1)
    
    try:
        cursor = conn.cursor()
        
        # Verificar estado actual
        cursor.execute("SELECT COUNT(*) FROM TAXONOMIA_INCIDENTES")
        total_before = cursor.fetchone()[0]
        print(f"Total de registros antes: {total_before}")
        
        cursor.execute("SELECT COUNT(*) FROM TAXONOMIA_INCIDENTES WHERE AplicaTipoEmpresa IS NULL")
        null_empresa = cursor.fetchone()[0]
        print(f"Registros con AplicaTipoEmpresa NULL: {null_empresa}")
        
        # Corregir datos
        fix_data_mapping(cursor)
        
        # Verificar después de la corrección
        cursor.execute("SELECT COUNT(*) FROM TAXONOMIA_INCIDENTES")
        total_after = cursor.fetchone()[0]
        print(f"Total de registros después: {total_after}")
        
        cursor.execute("SELECT AplicaTipoEmpresa, COUNT(*) FROM TAXONOMIA_INCIDENTES GROUP BY AplicaTipoEmpresa")
        print("Distribución por tipo de empresa:")
        for row in cursor.fetchall():
            tipo = row[0] if row[0] else "NULL"
            print(f"  - {tipo}: {row[1]} registros")
        
        # Mostrar algunos ejemplos corregidos
        cursor.execute("SELECT TOP 3 Id_Incidente, Area, Categoria_del_Incidente, AplicaTipoEmpresa FROM TAXONOMIA_INCIDENTES WHERE AplicaTipoEmpresa = 'PSE'")
        print("Ejemplos de taxonomías para PSE:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[2]} ({row[3]})")
        
        print("Corrección completada exitosamente")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    main()
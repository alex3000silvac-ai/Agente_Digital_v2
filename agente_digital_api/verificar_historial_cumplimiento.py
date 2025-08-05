#!/usr/bin/env python3
"""
Script para verificar tabla de historial y crear si no existe
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

def verificar_y_crear_historial():
    """Verificar tabla HistorialCumplimiento y crear si no existe"""
    try:
        conn_str = f"DRIVER={{{DB_CONFIG['driver']}}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']};Encrypt=no;TrustServerCertificate=yes"
        conn = pyodbc.connect(conn_str)
        conn.setdecoding(pyodbc.SQL_CHAR, encoding='latin-1')
        conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16le')
        conn.setencoding(encoding='utf-8')
        
        cursor = conn.cursor()
        
        print("=" * 60)
        print("VERIFICANDO TABLA HistorialCumplimiento")
        print("=" * 60)
        
        # Verificar si existe la tabla
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'HistorialCumplimiento'
        """)
        
        if cursor.fetchone():
            print("✅ La tabla HistorialCumplimiento existe")
            
            # Mostrar estructura
            cursor.execute("""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'HistorialCumplimiento'
                ORDER BY ORDINAL_POSITION
            """)
            
            print("\nEstructura de la tabla:")
            print(f"{'Columna':<25} {'Tipo':<15} {'Tamaño':<10} {'Nullable':<10}")
            print("-" * 60)
            
            for col in cursor.fetchall():
                col_name = col.COLUMN_NAME
                data_type = col.DATA_TYPE
                max_length = col.CHARACTER_MAXIMUM_LENGTH or ''
                is_nullable = col.IS_NULLABLE
                print(f"{col_name:<25} {data_type:<15} {str(max_length):<10} {is_nullable:<10}")
                
            # Verificar registros
            cursor.execute("SELECT COUNT(*) as total FROM HistorialCumplimiento")
            total = cursor.fetchone().total
            print(f"\n📊 Total de registros en historial: {total}")
            
            if total > 0:
                # Mostrar últimos 5 registros
                cursor.execute("""
                    SELECT TOP 5 
                        HistorialID,
                        CumplimientoID,
                        CampoModificado,
                        FechaCambio
                    FROM HistorialCumplimiento
                    ORDER BY FechaCambio DESC
                """)
                
                print("\nÚltimos 5 cambios:")
                for row in cursor.fetchall():
                    print(f"  ID: {row.HistorialID} | Cumplimiento: {row.CumplimientoID} | " +
                          f"Campo: {row.CampoModificado} | Fecha: {row.FechaCambio}")
        else:
            print("❌ La tabla HistorialCumplimiento NO existe")
            
            # Preguntar si crear la tabla
            respuesta = input("\n¿Desea crear la tabla HistorialCumplimiento? (s/n): ")
            
            if respuesta.lower() == 's':
                print("\n📝 Creando tabla HistorialCumplimiento...")
                
                create_query = """
                CREATE TABLE HistorialCumplimiento (
                    HistorialID INT IDENTITY(1,1) PRIMARY KEY,
                    CumplimientoID INT NOT NULL,
                    CampoModificado NVARCHAR(100) NOT NULL,
                    ValorAnterior NVARCHAR(MAX),
                    ValorNuevo NVARCHAR(MAX),
                    FechaCambio DATETIME2 NOT NULL DEFAULT GETDATE(),
                    UsuarioCambio NVARCHAR(255),
                    FOREIGN KEY (CumplimientoID) REFERENCES CumplimientoEmpresa(CumplimientoID)
                )
                """
                
                cursor.execute(create_query)
                conn.commit()
                
                print("✅ Tabla creada exitosamente")
                
                # Insertar registros de prueba
                respuesta2 = input("\n¿Desea insertar registros de prueba? (s/n): ")
                
                if respuesta2.lower() == 's':
                    # Obtener algunos cumplimientos existentes
                    cursor.execute("SELECT TOP 3 CumplimientoID FROM CumplimientoEmpresa")
                    cumplimientos = [row.CumplimientoID for row in cursor.fetchall()]
                    
                    if cumplimientos:
                        for cumpl_id in cumplimientos:
                            # Insertar cambios de ejemplo
                            cambios = [
                                ('Estado', 'Pendiente', 'En Proceso'),
                                ('PorcentajeAvance', '0', '25'),
                                ('Responsable', '', 'admin')
                            ]
                            
                            for campo, val_ant, val_nuevo in cambios:
                                cursor.execute("""
                                    INSERT INTO HistorialCumplimiento 
                                    (CumplimientoID, CampoModificado, ValorAnterior, ValorNuevo, UsuarioCambio)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (cumpl_id, campo, val_ant, val_nuevo, 'sistema'))
                        
                        conn.commit()
                        print(f"✅ Insertados {len(cumplimientos) * 3} registros de prueba")
                    else:
                        print("⚠️ No hay cumplimientos para crear historial de prueba")
        
        # Verificar triggers para historial automático
        print("\n" + "=" * 60)
        print("VERIFICANDO TRIGGERS PARA HISTORIAL AUTOMÁTICO")
        print("=" * 60)
        
        cursor.execute("""
            SELECT 
                name,
                create_date,
                modify_date
            FROM sys.triggers
            WHERE parent_id = OBJECT_ID('CumplimientoEmpresa')
        """)
        
        triggers = cursor.fetchall()
        if triggers:
            print(f"✅ Se encontraron {len(triggers)} triggers:")
            for trig in triggers:
                print(f"  - {trig.name} (creado: {trig.create_date})")
        else:
            print("❌ No hay triggers para registro automático de cambios")
            print("💡 Sugerencia: Crear un trigger para registrar cambios automáticamente")
            
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    verificar_y_crear_historial()
#!/usr/bin/env python3
"""
Script para verificar la estructura de la tabla CumplimientoEmpresa
y generar el script SQL para verificar/agregar columnas faltantes
"""

import pyodbc
import sys
from datetime import datetime

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

def check_cumplimiento_table():
    """Verificar la estructura de la tabla CumplimientoEmpresa"""
    conn = get_db_connection()
    if not conn:
        print("ERROR: No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sys.tables WHERE name = 'CumplimientoEmpresa'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✓ Tabla CumplimientoEmpresa existe")
            print("-" * 80)
            
            # Obtener estructura actual de la tabla
            cursor.execute("""
                SELECT 
                    c.COLUMN_NAME, 
                    c.DATA_TYPE, 
                    c.IS_NULLABLE,
                    c.CHARACTER_MAXIMUM_LENGTH,
                    c.NUMERIC_PRECISION,
                    c.NUMERIC_SCALE,
                    c.COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS c
                WHERE c.TABLE_NAME = 'CumplimientoEmpresa'
                ORDER BY c.ORDINAL_POSITION
            """)
            
            columns = cursor.fetchall()
            print("ESTRUCTURA ACTUAL DE LA TABLA:")
            print("-" * 80)
            for col in columns:
                col_name = col[0]
                data_type = col[1]
                nullable = col[2]
                max_length = col[3]
                precision = col[4]
                scale = col[5]
                default = col[6]
                
                type_info = data_type
                if max_length:
                    type_info += f"({max_length})"
                elif precision and scale:
                    type_info += f"({precision},{scale})"
                elif precision:
                    type_info += f"({precision})"
                
                print(f"  {col_name:<30} {type_info:<20} {nullable:<10} Default: {default or 'None'}")
            
            print("\n" + "-" * 80)
            
            # Verificar columnas específicas
            column_names = [col[0] for col in columns]
            
            print("\nVERIFICACIÓN DE COLUMNAS ESPECÍFICAS:")
            print("-" * 80)
            
            # Columnas esperadas comúnmente en tablas de cumplimiento
            expected_columns = {
                'CumplimientoID': 'Identificador único',
                'EmpresaID': 'ID de la empresa',
                'ObligacionID': 'ID de la obligación',
                'RecomendacionID': 'ID de la recomendación',
                'Estado': 'Estado del cumplimiento',
                'PorcentajeAvance': 'Porcentaje de avance',
                'Responsable': 'Responsable del cumplimiento',
                'FechaTermino': 'Fecha de término',
                'FechaCreacion': 'Fecha de creación',
                'FechaModificacion': 'Fecha de última modificación',
                'UsuarioCreacion': 'Usuario que creó el registro',
                'UsuarioModificacion': 'Usuario que modificó el registro'
            }
            
            for col_name, description in expected_columns.items():
                if col_name in column_names:
                    print(f"✓ {col_name:<25} - {description}")
                else:
                    print(f"✗ {col_name:<25} - {description} [FALTANTE]")
            
            # Verificar cantidad de registros
            cursor.execute("SELECT COUNT(*) FROM CumplimientoEmpresa")
            count = cursor.fetchone()[0]
            print(f"\n\nCANTIDAD DE REGISTROS: {count}")
            
            # Generar script SQL para agregar columnas faltantes
            print("\n" + "=" * 80)
            print("SCRIPT SQL PARA AGREGAR COLUMNAS FALTANTES:")
            print("=" * 80)
            
            if 'FechaModificacion' not in column_names:
                print("""
-- Agregar columna FechaModificacion
ALTER TABLE CumplimientoEmpresa 
ADD FechaModificacion DATETIME NULL;

-- Actualizar registros existentes con la fecha actual
UPDATE CumplimientoEmpresa 
SET FechaModificacion = GETDATE() 
WHERE FechaModificacion IS NULL;
""")
            
            if 'FechaCreacion' not in column_names:
                print("""
-- Agregar columna FechaCreacion
ALTER TABLE CumplimientoEmpresa 
ADD FechaCreacion DATETIME DEFAULT GETDATE() NOT NULL;

-- Actualizar registros existentes con la fecha actual
UPDATE CumplimientoEmpresa 
SET FechaCreacion = GETDATE() 
WHERE FechaCreacion IS NULL;
""")
            
            if 'UsuarioCreacion' not in column_names:
                print("""
-- Agregar columna UsuarioCreacion
ALTER TABLE CumplimientoEmpresa 
ADD UsuarioCreacion NVARCHAR(100) NULL;
""")
            
            if 'UsuarioModificacion' not in column_names:
                print("""
-- Agregar columna UsuarioModificacion
ALTER TABLE CumplimientoEmpresa 
ADD UsuarioModificacion NVARCHAR(100) NULL;
""")
            
            # Script para verificar columnas antes de usarlas en queries
            print("\n" + "=" * 80)
            print("SCRIPT PARA VERIFICAR COLUMNAS ANTES DE USARLAS:")
            print("=" * 80)
            print("""
-- Verificar si existe la columna FechaModificacion antes de usarla
IF EXISTS (
    SELECT 1 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'CumplimientoEmpresa' 
    AND COLUMN_NAME = 'FechaModificacion'
)
BEGIN
    -- Query que usa FechaModificacion
    SELECT ISNULL(SUM(CASE WHEN Estado = 'Implementado' THEN 1 ELSE 0 END), 0)
    FROM CumplimientoEmpresa
    WHERE EmpresaID = @EmpresaID 
    AND FechaModificacion < DATEADD(day, -30, GETDATE())
END
ELSE
BEGIN
    -- Query alternativa sin FechaModificacion
    SELECT ISNULL(SUM(CASE WHEN Estado = 'Implementado' THEN 1 ELSE 0 END), 0)
    FROM CumplimientoEmpresa
    WHERE EmpresaID = @EmpresaID
END
""")
            
        else:
            print("✗ La tabla CumplimientoEmpresa NO existe")
            print("\nSCRIPT PARA CREAR LA TABLA:")
            print("=" * 80)
            print("""
CREATE TABLE CumplimientoEmpresa (
    CumplimientoID INT IDENTITY(1,1) PRIMARY KEY,
    EmpresaID INT NOT NULL,
    ObligacionID INT NULL,
    RecomendacionID INT NULL,
    Estado NVARCHAR(50) NOT NULL DEFAULT 'Pendiente',
    PorcentajeAvance INT DEFAULT 0,
    Responsable NVARCHAR(255) NULL,
    FechaTermino DATE NULL,
    FechaCreacion DATETIME DEFAULT GETDATE() NOT NULL,
    FechaModificacion DATETIME NULL,
    UsuarioCreacion NVARCHAR(100) NULL,
    UsuarioModificacion NVARCHAR(100) NULL,
    CONSTRAINT FK_CumplimientoEmpresa_Empresa FOREIGN KEY (EmpresaID) 
        REFERENCES Empresas(EmpresaID),
    CONSTRAINT FK_CumplimientoEmpresa_Obligacion FOREIGN KEY (ObligacionID) 
        REFERENCES OBLIGACIONES(ObligacionID),
    CONSTRAINT FK_CumplimientoEmpresa_Recomendacion FOREIGN KEY (RecomendacionID) 
        REFERENCES Recomendaciones(RecomendacionID),
    CONSTRAINT CHK_Estado CHECK (Estado IN ('Pendiente', 'En Proceso', 'Implementado')),
    CONSTRAINT CHK_PorcentajeAvance CHECK (PorcentajeAvance >= 0 AND PorcentajeAvance <= 100)
);

-- Índices para mejorar rendimiento
CREATE INDEX IX_CumplimientoEmpresa_EmpresaID ON CumplimientoEmpresa(EmpresaID);
CREATE INDEX IX_CumplimientoEmpresa_Estado ON CumplimientoEmpresa(Estado);
CREATE INDEX IX_CumplimientoEmpresa_FechaModificacion ON CumplimientoEmpresa(FechaModificacion);
""")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def generate_safe_query():
    """Generar una query segura que verifique la existencia de columnas"""
    print("\n" + "=" * 80)
    print("QUERY SEGURA PARA USAR EN EL CÓDIGO PYTHON:")
    print("=" * 80)
    print("""
def get_cumplimiento_with_fecha_modificacion(cursor, empresa_id):
    '''Obtener cumplimientos con manejo seguro de FechaModificacion'''
    
    # Verificar si existe la columna FechaModificacion
    cursor.execute('''
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'CumplimientoEmpresa' 
        AND COLUMN_NAME = 'FechaModificacion'
    ''')
    
    has_fecha_modificacion = cursor.fetchone()[0] > 0
    
    if has_fecha_modificacion:
        # Query con FechaModificacion
        query = '''
            SELECT ISNULL(SUM(CASE WHEN Estado = 'Implementado' THEN 1 ELSE 0 END), 0)
            FROM CumplimientoEmpresa
            WHERE EmpresaID = ? AND FechaModificacion < DATEADD(day, -30, GETDATE())
        '''
    else:
        # Query sin FechaModificacion
        query = '''
            SELECT ISNULL(SUM(CASE WHEN Estado = 'Implementado' THEN 1 ELSE 0 END), 0)
            FROM CumplimientoEmpresa
            WHERE EmpresaID = ?
        '''
    
    cursor.execute(query, (empresa_id,))
    return cursor.fetchone()[0]
""")

if __name__ == '__main__':
    print("VERIFICACIÓN DE TABLA CumplimientoEmpresa")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    check_cumplimiento_table()
    generate_safe_query()
    
    print("\n" + "=" * 80)
    print("VERIFICACIÓN COMPLETADA")
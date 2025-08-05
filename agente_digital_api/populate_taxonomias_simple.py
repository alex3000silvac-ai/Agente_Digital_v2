#!/usr/bin/env python3
"""
Script para poblar la tabla TAXONOMIA_INCIDENTES con datos básicos
"""

import pyodbc
import sys
import os

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

def create_table_if_not_exists(cursor):
    """Crear tabla si no existe"""
    create_table_sql = """
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[TAXONOMIA_INCIDENTES]') AND type in (N'U'))
    BEGIN
        CREATE TABLE [dbo].[TAXONOMIA_INCIDENTES] (
            [ID_Incidente] INT IDENTITY(1,1) PRIMARY KEY,
            [Codigo_Incidente] NVARCHAR(50) NOT NULL UNIQUE,
            [CategoriaID] INT NULL,
            [Area] NVARCHAR(100) NOT NULL,
            [Efecto] NVARCHAR(100) NOT NULL,
            [Categoria_del_Incidente] NVARCHAR(200) NOT NULL,
            [Subcategoria_del_Incidente] NVARCHAR(200) NULL,
            [AplicaTipoEmpresa] NVARCHAR(50) NOT NULL CHECK (AplicaTipoEmpresa IN ('AMBAS', 'OIV', 'PSE')),
            [FechaCreacion] DATETIME2 DEFAULT GETDATE(),
            [CreadoPor] NVARCHAR(100) DEFAULT 'Sistema'
        );
        PRINT 'Tabla TAXONOMIA_INCIDENTES creada';
    END
    ELSE
    BEGIN
        PRINT 'Tabla TAXONOMIA_INCIDENTES ya existe';
    END
    """
    cursor.execute(create_table_sql)

def populate_basic_taxonomies(cursor):
    """Poblar con taxonomías básicas"""
    
    # Limpiar tabla si existe
    cursor.execute("DELETE FROM TAXONOMIA_INCIDENTES")
    
    # Datos básicos de taxonomías
    taxonomies = [
        # Para AMBAS (OIV y PSE)
        ('INC_USO_UNRI_ACNA', 'Impacto en el uso legítimo de recursos', 'Uso no autorizado de redes y sistemas informáticos', 'Acceso no autorizado a almacenamiento', 'Acceso no autorizado a sistemas de almacenamiento', 'AMBAS'),
        ('INC_USO_UNRI_AFBE', 'Impacto en el uso legítimo de recursos', 'Uso no autorizado de redes y sistemas informáticos', 'Ataque de fuerza bruta exitoso', 'Acceso no autorizado mediante prueba de múltiples credenciales', 'AMBAS'),
        ('INC_USO_UNRI_EXVA', 'Impacto en el uso legítimo de recursos', 'Uso no autorizado de redes y sistemas informáticos', 'Explotación de vulnerabilidades de autenticación', 'Explotación de fallas en mecanismos de autenticación', 'AMBAS'),
        ('INC_USO_UNRI_USCC', 'Impacto en el uso legítimo de recursos', 'Uso no autorizado de redes y sistemas informáticos', 'Uso de credenciales comprometidas', 'Acceso con credenciales válidas previamente robadas', 'AMBAS'),
        ('INC_USO_UNRI_ACRE', 'Impacto en el uso legítimo de recursos', 'Uso no autorizado de redes y sistemas informáticos', 'Acceso remoto no autorizado', 'Conexión remota sin autorización a sistemas internos', 'AMBAS'),
        
        ('INC_CONF_EXDA_ADVM', 'Impacto en la confidencialidad de la información', 'Exfiltración y/o exposición de datos', 'Adversario en el medio (MitM)', 'Interceptación de comunicaciones para robo de información', 'AMBAS'),
        ('INC_CONF_EXDA_ACMP', 'Impacto en la confidencialidad de la información', 'Exfiltración y/o exposición de datos', 'Apropiación de credenciales mediante phishing', 'Obtención exitosa de credenciales via phishing', 'AMBAS'),
        ('INC_CONF_EXDA_FDP', 'Impacto en la confidencialidad de la información', 'Exfiltración y/o exposición de datos', 'Filtración de datos personales', 'Pérdida de confidencialidad de datos personales', 'AMBAS'),
        ('INC_CONF_EXDA_KEYL', 'Impacto en la confidencialidad de la información', 'Exfiltración y/o exposición de datos', 'Keylogger en uso', 'Software que registra pulsaciones de teclado', 'AMBAS'),
        ('INC_CONF_EXDA_ROBO', 'Impacto en la confidencialidad de la información', 'Exfiltración y/o exposición de datos', 'Robo físico de equipos con información', 'Sustracción de dispositivos con datos sensibles', 'AMBAS'),
        
        ('INC_DISP_INDS_ACT', 'Impacto en la disponibilidad de un servicio esencial', 'Indisponibilidad y/o denegación de servicio', 'Agotamiento de conexiones TCP', 'Saturación de conexiones TCP disponibles', 'AMBAS'),
        ('INC_DISP_INDS_ANSI', 'Impacto en la disponibilidad de un servicio esencial', 'Indisponibilidad y/o denegación de servicio', 'Apagado no autorizado de sistemas', 'Desconexión no autorizada de sistemas críticos', 'AMBAS'),
        ('INC_DISP_INDS_AADN', 'Impacto en la disponibilidad de un servicio esencial', 'Indisponibilidad y/o denegación de servicio', 'Ataque de amplificación DNS/NTP', 'Uso de servidores para amplificar ataques DDoS', 'AMBAS'),
        ('INC_DISP_INDS_DSEV', 'Impacto en la disponibilidad de un servicio esencial', 'Indisponibilidad y/o denegación de servicio', 'Denegación por explotación de vulnerabilidades', 'Uso de fallas de software para caída de servicio', 'AMBAS'),
        ('INC_DISP_INDS_RANS', 'Impacto en la disponibilidad de un servicio esencial', 'Indisponibilidad y/o denegación de servicio', 'Ransomware', 'Cifrado malicioso de sistemas y datos', 'AMBAS'),
        
        ('INC_INTE_MODA_DEFAC', 'Impacto en la integridad de la información', 'Modificación o alteración de datos', 'Defacement de sitio web', 'Alteración no autorizada de contenido web', 'AMBAS'),
        ('INC_INTE_MODA_MODBD', 'Impacto en la integridad de la información', 'Modificación o alteración de datos', 'Modificación no autorizada de base de datos', 'Alteración de registros en bases de datos', 'AMBAS'),
        ('INC_INTE_MODA_TAMPE', 'Impacto en la integridad de la información', 'Modificación o alteración de datos', 'Tampering de archivos del sistema', 'Modificación de archivos críticos del sistema', 'AMBAS'),
        ('INC_INTE_DEST_ELIM', 'Impacto en la integridad de la información', 'Destrucción de datos', 'Eliminación masiva de datos', 'Borrado no autorizado de información crítica', 'AMBAS'),
        ('INC_INTE_DEST_CORR', 'Impacto en la integridad de la información', 'Destrucción de datos', 'Corrupción intencional de datos', 'Daño deliberado a la estructura de datos', 'AMBAS'),
        
        # Específicos para PSE
        ('INC_PSE_PAGO_FRAUD', 'Impacto en servicios de pago', 'Fraude en transacciones', 'Transacciones fraudulentas', 'Operaciones de pago no autorizadas', 'PSE'),
        ('INC_PSE_PAGO_LAVAN', 'Impacto en servicios de pago', 'Lavado de dinero', 'Uso del sistema para lavado de activos', 'Utilización para blanqueo de capitales', 'PSE'),
        ('INC_PSE_PAGO_SKIMM', 'Impacto en servicios de pago', 'Skimming de tarjetas', 'Clonación de tarjetas de pago', 'Captura ilegal de datos de tarjetas', 'PSE'),
        
        # Específicos para OIV
        ('INC_OIV_CRIT_SCADA', 'Impacto en infraestructura crítica', 'Compromiso de sistemas de control', 'Acceso no autorizado a sistemas SCADA', 'Intrusión en sistemas de control industrial', 'OIV'),
        ('INC_OIV_CRIT_PLC', 'Impacto en infraestructura crítica', 'Compromiso de sistemas de control', 'Manipulación de controladores lógicos', 'Alteración de PLCs o sistemas de control', 'OIV'),
        ('INC_OIV_CRIT_REDIND', 'Impacto en infraestructura crítica', 'Compromiso de redes industriales', 'Intrusión en red industrial', 'Acceso no autorizado a redes OT', 'OIV'),
        ('INC_OIV_CRIT_SENSO', 'Impacto en infraestructura crítica', 'Compromiso de sistemas de monitoreo', 'Manipulación de sensores críticos', 'Alteración de sistemas de sensores', 'OIV'),
    ]
    
    # Insertar datos
    insert_sql = """
    INSERT INTO TAXONOMIA_INCIDENTES (
        Codigo_Incidente, Area, Efecto, Categoria_del_Incidente, 
        Subcategoria_del_Incidente, AplicaTipoEmpresa
    ) VALUES (?, ?, ?, ?, ?, ?)
    """
    
    cursor.executemany(insert_sql, taxonomies)
    cursor.commit()
    print(f"Insertadas {len(taxonomies)} taxonomias")

def main():
    """Función principal"""
    print("Iniciando poblacion de taxonomias...")
    
    conn = get_db_connection()
    if not conn:
        print("ERROR: No se pudo conectar a la base de datos")
        sys.exit(1)
    
    try:
        cursor = conn.cursor()
        
        # Crear tabla si no existe
        create_table_if_not_exists(cursor)
        
        # Poblar con datos básicos
        populate_basic_taxonomies(cursor)
        
        # Verificar datos insertados
        cursor.execute("SELECT COUNT(*) FROM TAXONOMIA_INCIDENTES")
        total = cursor.fetchone()[0]
        print(f"Total de taxonomias en la tabla: {total}")
        
        # Verificar por tipo de empresa
        cursor.execute("SELECT AplicaTipoEmpresa, COUNT(*) FROM TAXONOMIA_INCIDENTES GROUP BY AplicaTipoEmpresa")
        for row in cursor.fetchall():
            print(f"   - {row[0]}: {row[1]} taxonomias")
        
        print("Poblacion completada exitosamente")
        
    except Exception as e:
        print(f"ERROR durante la poblacion: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
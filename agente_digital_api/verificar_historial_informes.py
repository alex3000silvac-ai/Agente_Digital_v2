"""
Script para verificar el historial de informes ANCI
"""
import pyodbc
import logging
import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verificar_tabla_informes():
    """Verifica si existe la tabla INFORMES_ANCI y muestra su contenido"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("""
            IF EXISTS (SELECT * FROM sys.tables WHERE name = 'INFORMES_ANCI')
                SELECT 1 as tabla_existe
            ELSE
                SELECT 0 as tabla_existe
        """)
        
        existe = cursor.fetchone()[0]
        
        if not existe:
            logger.info("❌ La tabla INFORMES_ANCI no existe")
            
            # Crear la tabla
            logger.info("📝 Creando tabla INFORMES_ANCI...")
            cursor.execute("""
            CREATE TABLE INFORMES_ANCI (
                InformeID INT IDENTITY(1,1) PRIMARY KEY,
                IncidenteID INT NOT NULL,
                TipoInforme VARCHAR(50) NOT NULL,
                EstadoInforme VARCHAR(50) DEFAULT 'generado',
                FechaGeneracion DATETIME DEFAULT GETDATE(),
                RutaArchivo NVARCHAR(500),
                TamanoKB DECIMAL(10,2),
                GeneradoPor NVARCHAR(100),
                Version INT DEFAULT 1,
                Activo BIT DEFAULT 1,
                FechaCreacion DATETIME DEFAULT GETDATE(),
                FechaModificacion DATETIME DEFAULT GETDATE(),
                CONSTRAINT FK_INFORMES_ANCI_INCIDENTE FOREIGN KEY (IncidenteID) 
                    REFERENCES INCIDENTES(IncidenteID)
            )
            """)
            
            # Crear índices
            cursor.execute("""
            CREATE INDEX IX_INFORMES_ANCI_IncidenteID ON INFORMES_ANCI(IncidenteID)
            """)
            
            cursor.execute("""
            CREATE INDEX IX_INFORMES_ANCI_TipoInforme ON INFORMES_ANCI(TipoInforme)
            """)
            
            conn.commit()
            logger.info("✅ Tabla INFORMES_ANCI creada exitosamente")
        else:
            logger.info("✅ La tabla INFORMES_ANCI existe")
            
            # Verificar contenido
            cursor.execute("SELECT COUNT(*) FROM INFORMES_ANCI")
            total = cursor.fetchone()[0]
            logger.info(f"📊 Total de informes en la tabla: {total}")
            
            if total > 0:
                # Mostrar algunos registros
                cursor.execute("""
                    SELECT TOP 5 
                        InformeID,
                        IncidenteID,
                        TipoInforme,
                        EstadoInforme,
                        FechaGeneracion,
                        GeneradoPor,
                        Version
                    FROM INFORMES_ANCI
                    ORDER BY FechaGeneracion DESC
                """)
                
                logger.info("\n📋 Últimos 5 informes generados:")
                for row in cursor.fetchall():
                    logger.info(f"  ID: {row[0]}, Incidente: {row[1]}, Tipo: {row[2]}, Estado: {row[3]}, Fecha: {row[4]}")
            else:
                logger.info("ℹ️ No hay informes generados aún")
                
                # Verificar si hay incidentes con ReporteAnciID
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM INCIDENTES 
                    WHERE ReporteAnciID IS NOT NULL
                """)
                incidentes_anci = cursor.fetchone()[0]
                logger.info(f"📊 Incidentes con ReporteAnciID: {incidentes_anci}")
                
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verificar_tabla_informes()
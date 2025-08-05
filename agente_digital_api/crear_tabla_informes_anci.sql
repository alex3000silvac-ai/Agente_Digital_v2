-- Script para crear la tabla INFORMES_ANCI si no existe
-- Ejecutar en la base de datos Agente_Digital

-- Verificar si la tabla existe y crearla si no
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'INFORMES_ANCI')
BEGIN
    PRINT 'Creando tabla INFORMES_ANCI...'
    
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
    
    -- Crear índices
    CREATE INDEX IX_INFORMES_ANCI_IncidenteID ON INFORMES_ANCI(IncidenteID)
    CREATE INDEX IX_INFORMES_ANCI_TipoInforme ON INFORMES_ANCI(TipoInforme)
    
    PRINT 'Tabla INFORMES_ANCI creada exitosamente'
END
ELSE
BEGIN
    PRINT 'La tabla INFORMES_ANCI ya existe'
END

-- Mostrar información de la tabla
SELECT 
    'Total de informes' as Descripcion,
    COUNT(*) as Cantidad
FROM INFORMES_ANCI

UNION ALL

SELECT 
    'Informes por tipo: ' + TipoInforme,
    COUNT(*)
FROM INFORMES_ANCI
GROUP BY TipoInforme

-- Mostrar últimos 5 informes
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
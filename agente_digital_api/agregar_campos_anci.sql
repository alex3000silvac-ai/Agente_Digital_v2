-- Script para agregar campos ANCI a la tabla INCIDENTES
-- Solo agrega los campos si no existen

-- Campo ReporteAnciID
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'INCIDENTES' 
    AND COLUMN_NAME = 'ReporteAnciID'
)
BEGIN
    ALTER TABLE INCIDENTES ADD ReporteAnciID INT NULL;
    PRINT 'Campo ReporteAnciID agregado a INCIDENTES';
END
ELSE
BEGIN
    PRINT 'Campo ReporteAnciID ya existe';
END
GO

-- Campo FechaTransformacionANCI
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'INCIDENTES' 
    AND COLUMN_NAME = 'FechaTransformacionANCI'
)
BEGIN
    ALTER TABLE INCIDENTES ADD FechaTransformacionANCI DATETIME NULL;
    PRINT 'Campo FechaTransformacionANCI agregado a INCIDENTES';
END
ELSE
BEGIN
    PRINT 'Campo FechaTransformacionANCI ya existe';
END
GO

-- Campo EstadoANCI
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'INCIDENTES' 
    AND COLUMN_NAME = 'EstadoANCI'
)
BEGIN
    ALTER TABLE INCIDENTES ADD EstadoANCI VARCHAR(50) NULL;
    PRINT 'Campo EstadoANCI agregado a INCIDENTES';
END
ELSE
BEGIN
    PRINT 'Campo EstadoANCI ya existe';
END
GO

-- Crear índice para mejorar el rendimiento
IF NOT EXISTS (
    SELECT * FROM sys.indexes 
    WHERE name = 'IX_INCIDENTES_ReporteAnciID' 
    AND object_id = OBJECT_ID('INCIDENTES')
)
BEGIN
    CREATE INDEX IX_INCIDENTES_ReporteAnciID ON INCIDENTES(ReporteAnciID);
    PRINT 'Índice IX_INCIDENTES_ReporteAnciID creado';
END
GO

-- Campos CSIRT
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'INCIDENTES' 
    AND COLUMN_NAME = 'SolicitarCSIRT'
)
BEGIN
    ALTER TABLE INCIDENTES ADD SolicitarCSIRT BIT NULL DEFAULT 0;
    PRINT 'Campo SolicitarCSIRT agregado a INCIDENTES';
END
ELSE
BEGIN
    PRINT 'Campo SolicitarCSIRT ya existe';
END
GO

IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'INCIDENTES' 
    AND COLUMN_NAME = 'TipoApoyoCSIRT'
)
BEGIN
    ALTER TABLE INCIDENTES ADD TipoApoyoCSIRT VARCHAR(100) NULL;
    PRINT 'Campo TipoApoyoCSIRT agregado a INCIDENTES';
END
ELSE
BEGIN
    PRINT 'Campo TipoApoyoCSIRT ya existe';
END
GO

IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'INCIDENTES' 
    AND COLUMN_NAME = 'UrgenciaCSIRT'
)
BEGIN
    ALTER TABLE INCIDENTES ADD UrgenciaCSIRT VARCHAR(50) NULL;
    PRINT 'Campo UrgenciaCSIRT agregado a INCIDENTES';
END
ELSE
BEGIN
    PRINT 'Campo UrgenciaCSIRT ya existe';
END
GO

IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'INCIDENTES' 
    AND COLUMN_NAME = 'ObservacionesCSIRT'
)
BEGIN
    ALTER TABLE INCIDENTES ADD ObservacionesCSIRT VARCHAR(4000) NULL;
    PRINT 'Campo ObservacionesCSIRT agregado a INCIDENTES';
END
ELSE
BEGIN
    PRINT 'Campo ObservacionesCSIRT ya existe';
END
GO

PRINT 'Script completado. Los campos ANCI y CSIRT han sido verificados/agregados.';
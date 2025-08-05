-- =====================================================
-- CREAR TABLAS FALTANTES - VERSIÓN CORREGIDA
-- =====================================================
-- Script corregido para crear ÚNICAMENTE las tablas
-- que NO existen según tablas_bd.txt
-- Fecha: 2025-01-18
-- =====================================================

USE AgenteDigitalDB;
GO

PRINT '======================================'
PRINT 'CREANDO TABLAS FALTANTES'
PRINT 'Base de datos: AgenteDigitalDB'
PRINT '======================================'
PRINT ''

-- =====================================================
-- 1. TABLA INFORMES_ANCI
-- =====================================================
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
    );
    
    CREATE INDEX IX_INFORMES_ANCI_IncidenteID ON INFORMES_ANCI(IncidenteID);
    CREATE INDEX IX_INFORMES_ANCI_TipoInforme ON INFORMES_ANCI(TipoInforme);
    CREATE INDEX IX_INFORMES_ANCI_FechaGeneracion ON INFORMES_ANCI(FechaGeneracion DESC);
    
    PRINT 'Tabla INFORMES_ANCI creada exitosamente'
END
ELSE
BEGIN
    PRINT 'La tabla INFORMES_ANCI ya existe'
END
GO

-- =====================================================
-- 2. CAMPOS ANCI EN INCIDENTES
-- =====================================================
PRINT ''
PRINT 'Verificando campos ANCI en tabla Incidentes...'

-- ReporteAnciID
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'ReporteAnciID')
BEGIN
    ALTER TABLE Incidentes ADD ReporteAnciID INT NULL;
    PRINT 'Campo ReporteAnciID agregado'
END

-- FechaTransformacionAnci
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'FechaTransformacionAnci')
BEGIN
    ALTER TABLE Incidentes ADD FechaTransformacionAnci DATETIME NULL;
    PRINT 'Campo FechaTransformacionAnci agregado'
END

-- EstadoAnci
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'EstadoAnci')
BEGIN
    ALTER TABLE Incidentes ADD EstadoAnci VARCHAR(50) NULL;
    PRINT 'Campo EstadoAnci agregado'
END

-- AnciTipoAmenaza
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'AnciTipoAmenaza')
BEGIN
    ALTER TABLE Incidentes ADD AnciTipoAmenaza NVARCHAR(200) NULL;
    PRINT 'Campo AnciTipoAmenaza agregado'
END

-- AnciImpactoPreliminar
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'AnciImpactoPreliminar')
BEGIN
    ALTER TABLE Incidentes ADD AnciImpactoPreliminar NVARCHAR(MAX) NULL;
    PRINT 'Campo AnciImpactoPreliminar agregado'
END

-- SeccionCongelada
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'SeccionCongelada')
BEGIN
    ALTER TABLE Incidentes ADD SeccionCongelada INT NULL;
    PRINT 'Campo SeccionCongelada agregado'
END

-- =====================================================
-- 3. CAMPOS CSIRT EN INCIDENTES
-- =====================================================
PRINT ''
PRINT 'Verificando campos CSIRT en tabla Incidentes...'

-- SolicitarCSIRT
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'SolicitarCSIRT')
BEGIN
    ALTER TABLE Incidentes ADD SolicitarCSIRT BIT DEFAULT 0;
    PRINT 'Campo SolicitarCSIRT agregado'
END

-- TipoApoyoCSIRT
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'TipoApoyoCSIRT')
BEGIN
    ALTER TABLE Incidentes ADD TipoApoyoCSIRT NVARCHAR(200) NULL;
    PRINT 'Campo TipoApoyoCSIRT agregado'
END

-- UrgenciaCSIRT
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'UrgenciaCSIRT')
BEGIN
    ALTER TABLE Incidentes ADD UrgenciaCSIRT NVARCHAR(50) NULL;
    PRINT 'Campo UrgenciaCSIRT agregado'
END

-- ObservacionesCSIRT
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'ObservacionesCSIRT')
BEGIN
    ALTER TABLE Incidentes ADD ObservacionesCSIRT NVARCHAR(MAX) NULL;
    PRINT 'Campo ObservacionesCSIRT agregado'
END

-- =====================================================
-- 4. CAMPO NombreOriginal EN INCIDENTES_ARCHIVOS
-- =====================================================
PRINT ''
PRINT 'Verificando campo NombreOriginal en INCIDENTES_ARCHIVOS...'

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('INCIDENTES_ARCHIVOS') AND name = 'NombreOriginal')
BEGIN
    ALTER TABLE INCIDENTES_ARCHIVOS ADD NombreOriginal NVARCHAR(255) NULL;
    PRINT 'Campo NombreOriginal agregado'
END

-- =====================================================
-- 5. RESUMEN FINAL
-- =====================================================
PRINT ''
PRINT '======================================'
PRINT 'RESUMEN DE EJECUCIÓN:'
PRINT '======================================'

-- Verificar tabla INFORMES_ANCI
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'INFORMES_ANCI')
    PRINT 'INFORMES_ANCI - OK'
ELSE
    PRINT 'INFORMES_ANCI - NO CREADA'

-- Verificar campos en Incidentes
DECLARE @camposAnci INT = 0;
DECLARE @camposCSIRT INT = 0;

IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'ReporteAnciID')
    SET @camposAnci = @camposAnci + 1;
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'FechaTransformacionAnci')
    SET @camposAnci = @camposAnci + 1;
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'EstadoAnci')
    SET @camposAnci = @camposAnci + 1;
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'AnciTipoAmenaza')
    SET @camposAnci = @camposAnci + 1;
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'AnciImpactoPreliminar')
    SET @camposAnci = @camposAnci + 1;
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'SeccionCongelada')
    SET @camposAnci = @camposAnci + 1;

IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'SolicitarCSIRT')
    SET @camposCSIRT = @camposCSIRT + 1;
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'TipoApoyoCSIRT')
    SET @camposCSIRT = @camposCSIRT + 1;
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'UrgenciaCSIRT')
    SET @camposCSIRT = @camposCSIRT + 1;
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'ObservacionesCSIRT')
    SET @camposCSIRT = @camposCSIRT + 1;

PRINT ''
PRINT 'Campos ANCI en Incidentes: ' + CAST(@camposAnci AS VARCHAR(10)) + '/6'
PRINT 'Campos CSIRT en Incidentes: ' + CAST(@camposCSIRT AS VARCHAR(10)) + '/4'

IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('INCIDENTES_ARCHIVOS') AND name = 'NombreOriginal')
    PRINT 'Campo NombreOriginal en INCIDENTES_ARCHIVOS - OK'
ELSE
    PRINT 'Campo NombreOriginal en INCIDENTES_ARCHIVOS - NO CREADO'

PRINT ''
PRINT '======================================'
PRINT 'SCRIPT COMPLETADO'
PRINT '======================================' 
-- =====================================================
-- SCRIPT MAESTRO - EJECUTAR TODOS LOS SCRIPTS SQL
-- =====================================================
-- Este archivo ejecuta todos los scripts SQL necesarios
-- en el orden correcto para el sistema ANCI
-- 
-- IMPORTANTE: Ejecutar con permisos de administrador
-- en la base de datos AgenteDigitalDB
-- =====================================================

PRINT '======================================'
PRINT 'INICIANDO EJECUCIÓN DE SCRIPTS SQL'
PRINT 'Base de datos: AgenteDigitalDB'
PRINT 'Fecha: ' + CONVERT(VARCHAR, GETDATE(), 120)
PRINT '======================================'
PRINT ''

-- =====================================================
-- 1. AGREGAR CAMPOS ANCI A INCIDENTES
-- =====================================================
PRINT '1. AGREGANDO CAMPOS ANCI...'
PRINT '======================================'

-- Verificar y agregar ReporteAnciID
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'ReporteAnciID')
    ALTER TABLE Incidentes ADD ReporteAnciID INT NULL;

-- Verificar y agregar FechaTransformacionAnci
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'FechaTransformacionAnci')
    ALTER TABLE Incidentes ADD FechaTransformacionAnci DATETIME NULL;

-- Verificar y agregar EstadoAnci
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'EstadoAnci')
    ALTER TABLE Incidentes ADD EstadoAnci VARCHAR(50) NULL;

-- Verificar y agregar AnciTipoAmenaza
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'AnciTipoAmenaza')
    ALTER TABLE Incidentes ADD AnciTipoAmenaza NVARCHAR(200) NULL;

-- Verificar y agregar AnciImpactoPreliminar
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'AnciImpactoPreliminar')
    ALTER TABLE Incidentes ADD AnciImpactoPreliminar NVARCHAR(MAX) NULL;

-- Verificar y agregar SeccionCongelada
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'SeccionCongelada')
    ALTER TABLE Incidentes ADD SeccionCongelada INT NULL;

PRINT '✅ Campos ANCI agregados/verificados'
PRINT ''

-- =====================================================
-- 2. AGREGAR CAMPOS CSIRT A INCIDENTES
-- =====================================================
PRINT '2. AGREGANDO CAMPOS CSIRT...'
PRINT '======================================'

-- Verificar y agregar SolicitarCSIRT
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'SolicitarCSIRT')
    ALTER TABLE Incidentes ADD SolicitarCSIRT BIT DEFAULT 0;

-- Verificar y agregar TipoApoyoCSIRT
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'TipoApoyoCSIRT')
    ALTER TABLE Incidentes ADD TipoApoyoCSIRT NVARCHAR(200) NULL;

-- Verificar y agregar UrgenciaCSIRT
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'UrgenciaCSIRT')
    ALTER TABLE Incidentes ADD UrgenciaCSIRT NVARCHAR(50) NULL;

-- Verificar y agregar ObservacionesCSIRT
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'ObservacionesCSIRT')
    ALTER TABLE Incidentes ADD ObservacionesCSIRT NVARCHAR(MAX) NULL;

PRINT '✅ Campos CSIRT agregados/verificados'
PRINT ''

-- =====================================================
-- 3. CREAR TABLA INFORMES_ANCI
-- =====================================================
PRINT '3. CREANDO TABLA INFORMES_ANCI...'
PRINT '======================================'

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'INFORMES_ANCI')
BEGIN
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
    CREATE INDEX IX_INFORMES_ANCI_FechaGeneracion ON INFORMES_ANCI(FechaGeneracion DESC)
    
    PRINT '✅ Tabla INFORMES_ANCI creada exitosamente'
END
ELSE
BEGIN
    PRINT '⚠️ La tabla INFORMES_ANCI ya existe'
END
PRINT ''

-- =====================================================
-- 4. VERIFICAR ESTRUCTURA DE ARCHIVOS
-- =====================================================
PRINT '4. VERIFICANDO TABLA INCIDENTES_ARCHIVOS...'
PRINT '======================================'

-- Verificar que exista la columna NombreOriginal
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('INCIDENTES_ARCHIVOS') AND name = 'NombreOriginal')
BEGIN
    PRINT '⚠️ Agregando columna NombreOriginal a INCIDENTES_ARCHIVOS'
    ALTER TABLE INCIDENTES_ARCHIVOS ADD NombreOriginal NVARCHAR(255) NULL;
    
    -- Copiar datos de NombreArchivo si existe
    IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('INCIDENTES_ARCHIVOS') AND name = 'NombreArchivo')
    BEGIN
        UPDATE INCIDENTES_ARCHIVOS SET NombreOriginal = NombreArchivo WHERE NombreOriginal IS NULL;
    END
END
ELSE
BEGIN
    PRINT '✅ Columna NombreOriginal ya existe'
END
PRINT ''

-- =====================================================
-- 5. RESUMEN FINAL
-- =====================================================
PRINT '======================================'
PRINT 'RESUMEN DE EJECUCIÓN:'
PRINT '======================================'
PRINT ''

-- Verificar tablas
PRINT 'TABLAS VERIFICADAS:'
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'INFORMES_ANCI')
    PRINT '✅ INFORMES_ANCI existe'
ELSE
    PRINT '❌ INFORMES_ANCI NO existe'

IF EXISTS (SELECT * FROM sys.tables WHERE name = 'INCIDENTES_ARCHIVOS')
    PRINT '✅ INCIDENTES_ARCHIVOS existe'
ELSE
    PRINT '❌ INCIDENTES_ARCHIVOS NO existe'

PRINT ''
PRINT 'CAMPOS EN TABLA INCIDENTES:'

-- Verificar campos ANCI
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'ReporteAnciID')
    PRINT '✅ ReporteAnciID'
ELSE
    PRINT '❌ ReporteAnciID'

IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'SolicitarCSIRT')
    PRINT '✅ SolicitarCSIRT'
ELSE
    PRINT '❌ SolicitarCSIRT'

PRINT ''
PRINT '======================================'
PRINT 'SCRIPT COMPLETADO'
PRINT 'Fecha: ' + CONVERT(VARCHAR, GETDATE(), 120)
PRINT '======================================' 
-- =====================================================
-- CREAR SOLO TABLAS FALTANTES
-- =====================================================
-- Script específico para crear ÚNICAMENTE las tablas
-- que NO existen según tablas_bd.txt
-- Fecha de análisis: 2025-01-18
-- Total de tablas existentes: 54
-- =====================================================

USE AgenteDigitalDB;
GO

PRINT '======================================'
PRINT 'CREANDO TABLAS FALTANTES'
PRINT 'Base de datos: AgenteDigitalDB'
PRINT 'Fecha: ' + CONVERT(VARCHAR, GETDATE(), 120)
PRINT '======================================'
PRINT ''

-- =====================================================
-- 1. TABLA INFORMES_ANCI (Para historial de informes)
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'INFORMES_ANCI')
BEGIN
    PRINT '📋 Creando tabla INFORMES_ANCI...'
    
    CREATE TABLE INFORMES_ANCI (
        InformeID INT IDENTITY(1,1) PRIMARY KEY,
        IncidenteID INT NOT NULL,
        TipoInforme VARCHAR(50) NOT NULL, -- 'preliminar', 'completo', 'final'
        EstadoInforme VARCHAR(50) DEFAULT 'generado',
        FechaGeneracion DATETIME DEFAULT GETDATE(),
        RutaArchivo NVARCHAR(500),
        TamanoKB DECIMAL(10,2),
        GeneradoPor NVARCHAR(100),
        Version INT DEFAULT 1,
        Activo BIT DEFAULT 1,
        FechaCreacion DATETIME DEFAULT GETDATE(),
        FechaModificacion DATETIME DEFAULT GETDATE(),
        -- Campos adicionales para tracking
        HashArchivo NVARCHAR(256) NULL, -- Para verificar integridad
        TiempoGeneracion INT NULL, -- Milisegundos
        Observaciones NVARCHAR(MAX) NULL,
        CONSTRAINT FK_INFORMES_ANCI_INCIDENTE FOREIGN KEY (IncidenteID) 
            REFERENCES INCIDENTES(IncidenteID) ON DELETE CASCADE
    );
    
    -- Crear índices para optimización
    CREATE INDEX IX_INFORMES_ANCI_IncidenteID ON INFORMES_ANCI(IncidenteID);
    CREATE INDEX IX_INFORMES_ANCI_TipoInforme ON INFORMES_ANCI(TipoInforme);
    CREATE INDEX IX_INFORMES_ANCI_FechaGeneracion ON INFORMES_ANCI(FechaGeneracion DESC);
    CREATE INDEX IX_INFORMES_ANCI_Activo ON INFORMES_ANCI(Activo) WHERE Activo = 1;
    
    PRINT '✅ Tabla INFORMES_ANCI creada exitosamente'
END
ELSE
BEGIN
    PRINT '⚠️ La tabla INFORMES_ANCI ya existe'
END
GO

-- =====================================================
-- 2. TABLA CSIRT_SOLICITUDES_LOG (Para auditoría CSIRT)
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'CSIRT_SOLICITUDES_LOG')
BEGIN
    PRINT '📋 Creando tabla CSIRT_SOLICITUDES_LOG...'
    
    CREATE TABLE CSIRT_SOLICITUDES_LOG (
        LogID INT PRIMARY KEY IDENTITY(1,1),
        IncidenteID INT NOT NULL,
        TipoEvento NVARCHAR(50) NOT NULL, -- 'SOLICITUD', 'ACTUALIZACION', 'RESPUESTA'
        FechaEvento DATETIME DEFAULT GETDATE(),
        Usuario NVARCHAR(100),
        Descripcion NVARCHAR(MAX),
        DatosAnteriores NVARCHAR(MAX), -- JSON
        DatosNuevos NVARCHAR(MAX), -- JSON
        IPOrigen NVARCHAR(50) NULL,
        UserAgent NVARCHAR(500) NULL,
        FOREIGN KEY (IncidenteID) REFERENCES Incidentes(IncidenteID) ON DELETE CASCADE
    );
    
    -- Índices
    CREATE INDEX IDX_CSIRT_Log_Incidente ON CSIRT_SOLICITUDES_LOG(IncidenteID, FechaEvento);
    CREATE INDEX IDX_CSIRT_Log_Tipo ON CSIRT_SOLICITUDES_LOG(TipoEvento);
    CREATE INDEX IDX_CSIRT_Log_Fecha ON CSIRT_SOLICITUDES_LOG(FechaEvento DESC);
    
    PRINT '✅ Tabla CSIRT_SOLICITUDES_LOG creada exitosamente'
END
ELSE
BEGIN
    PRINT '⚠️ La tabla CSIRT_SOLICITUDES_LOG ya existe'
END
GO

-- =====================================================
-- 3. VERIFICAR Y AGREGAR CAMPOS FALTANTES
-- =====================================================
PRINT ''
PRINT '📋 Verificando campos faltantes en tablas existentes...'
PRINT ''

-- CAMPOS ANCI EN TABLA INCIDENTES
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'ReporteAnciID')
BEGIN
    ALTER TABLE Incidentes ADD ReporteAnciID INT NULL;
    PRINT '✅ Campo ReporteAnciID agregado a Incidentes'
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'FechaTransformacionAnci')
BEGIN
    ALTER TABLE Incidentes ADD FechaTransformacionAnci DATETIME NULL;
    PRINT '✅ Campo FechaTransformacionAnci agregado a Incidentes'
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'EstadoAnci')
BEGIN
    ALTER TABLE Incidentes ADD EstadoAnci VARCHAR(50) NULL;
    PRINT '✅ Campo EstadoAnci agregado a Incidentes'
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'AnciTipoAmenaza')
BEGIN
    ALTER TABLE Incidentes ADD AnciTipoAmenaza NVARCHAR(200) NULL;
    PRINT '✅ Campo AnciTipoAmenaza agregado a Incidentes'
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'AnciImpactoPreliminar')
BEGIN
    ALTER TABLE Incidentes ADD AnciImpactoPreliminar NVARCHAR(MAX) NULL;
    PRINT '✅ Campo AnciImpactoPreliminar agregado a Incidentes'
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'SeccionCongelada')
BEGIN
    ALTER TABLE Incidentes ADD SeccionCongelada INT NULL;
    PRINT '✅ Campo SeccionCongelada agregado a Incidentes'
END

-- CAMPOS CSIRT EN TABLA INCIDENTES
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'SolicitarCSIRT')
BEGIN
    ALTER TABLE Incidentes ADD SolicitarCSIRT BIT DEFAULT 0;
    PRINT '✅ Campo SolicitarCSIRT agregado a Incidentes'
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'TipoApoyoCSIRT')
BEGIN
    ALTER TABLE Incidentes ADD TipoApoyoCSIRT NVARCHAR(200) NULL;
    PRINT '✅ Campo TipoApoyoCSIRT agregado a Incidentes'
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'UrgenciaCSIRT')
BEGIN
    ALTER TABLE Incidentes ADD UrgenciaCSIRT NVARCHAR(50) NULL;
    PRINT '✅ Campo UrgenciaCSIRT agregado a Incidentes'
END

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'ObservacionesCSIRT')
BEGIN
    ALTER TABLE Incidentes ADD ObservacionesCSIRT NVARCHAR(MAX) NULL;
    PRINT '✅ Campo ObservacionesCSIRT agregado a Incidentes'
END

-- VERIFICAR COLUMNA NombreOriginal EN INCIDENTES_ARCHIVOS
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('INCIDENTES_ARCHIVOS') AND name = 'NombreOriginal')
BEGIN
    ALTER TABLE INCIDENTES_ARCHIVOS ADD NombreOriginal NVARCHAR(255) NULL;
    PRINT '✅ Campo NombreOriginal agregado a INCIDENTES_ARCHIVOS'
    
    -- Actualización condicional usando SQL dinámico
    IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('INCIDENTES_ARCHIVOS') AND name = 'NombreArchivo')
    BEGIN
        DECLARE @sql NVARCHAR(MAX) = 'UPDATE INCIDENTES_ARCHIVOS SET NombreOriginal = NombreArchivo WHERE NombreOriginal IS NULL';
        EXEC sp_executesql @sql;
        PRINT '✅ Datos copiados de NombreArchivo a NombreOriginal'
    END
END

-- =====================================================
-- 4. CREAR VISTAS ÚTILES
-- =====================================================
PRINT ''
PRINT '📋 Creando vistas auxiliares...'
PRINT ''

-- Vista para Dashboard ANCI
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_IncidentesANCI_Dashboard')
    DROP VIEW vw_IncidentesANCI_Dashboard;
GO

CREATE VIEW vw_IncidentesANCI_Dashboard AS
SELECT 
    i.IncidenteID,
    i.IDVisible,
    i.Titulo,
    i.Criticidad,
    i.EstadoActual,
    i.FechaDeteccion,
    i.FechaOcurrencia,
    i.ReporteAnciID,
    i.FechaTransformacionAnci,
    i.EstadoAnci,
    i.SolicitarCSIRT,
    i.TipoApoyoCSIRT,
    e.RazonSocial as EmpresaNombre,
    e.TipoEmpresa as TipoEmpresa,
    -- Contar informes generados
    (SELECT COUNT(*) FROM INFORMES_ANCI 
     WHERE IncidenteID = i.IncidenteID AND Activo = 1) as TotalInformesGenerados,
    -- Último informe
    (SELECT TOP 1 TipoInforme FROM INFORMES_ANCI 
     WHERE IncidenteID = i.IncidenteID AND Activo = 1 
     ORDER BY FechaGeneracion DESC) as UltimoInformeTipo,
    (SELECT TOP 1 FechaGeneracion FROM INFORMES_ANCI 
     WHERE IncidenteID = i.IncidenteID AND Activo = 1 
     ORDER BY FechaGeneracion DESC) as UltimaGeneracion,
    -- Calcular plazos
    CASE 
        WHEN i.FechaTransformacionAnci IS NOT NULL 
        THEN DATEDIFF(HOUR, i.FechaTransformacionAnci, GETDATE()) 
        ELSE NULL 
    END as HorasDesdeTransformacion,
    -- Archivos adjuntos
    (SELECT COUNT(*) FROM INCIDENTES_ARCHIVOS 
     WHERE IncidenteID = i.IncidenteID AND Activo = 1) as TotalArchivos
FROM Incidentes i
INNER JOIN Empresas e ON i.EmpresaID = e.EmpresaID
WHERE i.ReporteAnciID IS NOT NULL;
GO

PRINT '✅ Vista vw_IncidentesANCI_Dashboard creada'

-- =====================================================
-- 5. RESUMEN FINAL
-- =====================================================
PRINT ''
PRINT '======================================'
PRINT 'RESUMEN DE EJECUCIÓN:'
PRINT '======================================'

-- Verificar tablas creadas
DECLARE @tablas_nuevas INT = 0;

IF EXISTS (SELECT * FROM sys.tables WHERE name = 'INFORMES_ANCI')
BEGIN
    PRINT '✅ INFORMES_ANCI - OK'
    SET @tablas_nuevas = @tablas_nuevas + 1;
END
ELSE
    PRINT '❌ INFORMES_ANCI - NO CREADA'

IF EXISTS (SELECT * FROM sys.tables WHERE name = 'CSIRT_SOLICITUDES_LOG')
BEGIN
    PRINT '✅ CSIRT_SOLICITUDES_LOG - OK'
    SET @tablas_nuevas = @tablas_nuevas + 1;
END
ELSE
    PRINT '❌ CSIRT_SOLICITUDES_LOG - NO CREADA'

PRINT ''
PRINT 'Total tablas nuevas: ' + CAST(@tablas_nuevas AS VARCHAR(10))
PRINT 'Total tablas ahora: ' + CAST((SELECT COUNT(*) FROM sys.tables) AS VARCHAR(10))
PRINT ''
PRINT '======================================'
PRINT 'SCRIPT COMPLETADO'
PRINT 'Fecha: ' + CONVERT(VARCHAR, GETDATE(), 120)
PRINT '======================================'

-- Mostrar información de las nuevas tablas
IF @tablas_nuevas > 0
BEGIN
    PRINT ''
    PRINT 'NUEVAS TABLAS CREADAS:'
    PRINT '----------------------'
    
    IF EXISTS (SELECT * FROM sys.tables WHERE name = 'INFORMES_ANCI')
    BEGIN
        DECLARE @fecha1 DATETIME = (SELECT create_date FROM sys.tables WHERE name = 'INFORMES_ANCI');
        PRINT '• INFORMES_ANCI - Creada: ' + CONVERT(VARCHAR, @fecha1, 120);
    END
    
    IF EXISTS (SELECT * FROM sys.tables WHERE name = 'CSIRT_SOLICITUDES_LOG')
    BEGIN
        DECLARE @fecha2 DATETIME = (SELECT create_date FROM sys.tables WHERE name = 'CSIRT_SOLICITUDES_LOG');
        PRINT '• CSIRT_SOLICITUDES_LOG - Creada: ' + CONVERT(VARCHAR, @fecha2, 120);
    END
END
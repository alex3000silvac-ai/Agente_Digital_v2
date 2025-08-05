-- =====================================================
-- CREAR TABLAS FALTANTES PARA EL SISTEMA ANCI
-- =====================================================
-- Este script crea las tablas que faltan según el análisis
-- de tablas_bd.txt comparado con el sistema actual
-- =====================================================

-- 1. TABLA INFORMES_ANCI (Historial de informes generados)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'INFORMES_ANCI')
BEGIN
    PRINT 'Creando tabla INFORMES_ANCI...'
    
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
GO

-- 2. VERIFICAR CAMPOS ANCI EN TABLA INCIDENTES
-- Estos campos son necesarios para el sistema ANCI
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'ReporteAnciID')
BEGIN
    PRINT 'Agregando campos ANCI a tabla Incidentes...'
    
    ALTER TABLE Incidentes ADD ReporteAnciID INT NULL;
    ALTER TABLE Incidentes ADD FechaTransformacionAnci DATETIME NULL;
    ALTER TABLE Incidentes ADD EstadoAnci VARCHAR(50) NULL;
    ALTER TABLE Incidentes ADD AnciTipoAmenaza NVARCHAR(200) NULL;
    ALTER TABLE Incidentes ADD AnciImpactoPreliminar NVARCHAR(MAX) NULL;
    ALTER TABLE Incidentes ADD SeccionCongelada INT NULL;
    
    PRINT '✅ Campos ANCI agregados a tabla Incidentes'
END

-- 3. VERIFICAR CAMPOS CSIRT EN TABLA INCIDENTES
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Incidentes') AND name = 'SolicitarCSIRT')
BEGIN
    PRINT 'Agregando campos CSIRT a tabla Incidentes...'
    
    ALTER TABLE Incidentes ADD SolicitarCSIRT BIT DEFAULT 0;
    ALTER TABLE Incidentes ADD TipoApoyoCSIRT NVARCHAR(200) NULL;
    ALTER TABLE Incidentes ADD UrgenciaCSIRT NVARCHAR(50) NULL;
    ALTER TABLE Incidentes ADD ObservacionesCSIRT NVARCHAR(MAX) NULL;
    
    PRINT '✅ Campos CSIRT agregados a tabla Incidentes'
END

-- 4. CREAR VISTA PARA DASHBOARD ANCI
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_IncidentesANCI')
    DROP VIEW vw_IncidentesANCI
GO

CREATE VIEW vw_IncidentesANCI AS
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
    e.RazonSocial as EmpresaNombre,
    e.Tipo_Empresa as TipoEmpresa,
    -- Contar informes generados
    (SELECT COUNT(*) FROM INFORMES_ANCI WHERE IncidenteID = i.IncidenteID AND Activo = 1) as TotalInformesGenerados,
    -- Último informe
    (SELECT TOP 1 TipoInforme FROM INFORMES_ANCI 
     WHERE IncidenteID = i.IncidenteID AND Activo = 1 
     ORDER BY FechaGeneracion DESC) as UltimoInformeTipo,
    -- Calcular tiempo desde transformación
    CASE 
        WHEN i.FechaTransformacionAnci IS NOT NULL 
        THEN DATEDIFF(HOUR, i.FechaTransformacionAnci, GETDATE()) 
        ELSE NULL 
    END as HorasDesdeTransformacion
FROM Incidentes i
INNER JOIN Empresas e ON i.EmpresaID = e.EmpresaID
WHERE i.ReporteAnciID IS NOT NULL
GO

PRINT '✅ Vista vw_IncidentesANCI creada exitosamente'

-- 5. MOSTRAR RESUMEN
PRINT ''
PRINT '======================================'
PRINT 'RESUMEN DE CAMBIOS APLICADOS:'
PRINT '======================================'
PRINT '1. Tabla INFORMES_ANCI - Para historial de informes'
PRINT '2. Campos ANCI en tabla Incidentes'
PRINT '3. Campos CSIRT en tabla Incidentes'
PRINT '4. Vista vw_IncidentesANCI para dashboard'
PRINT '======================================'
-- =====================================================
-- SCRIPT SQL - CAMPOS FALTANTES PARA CUMPLIR CON ANCI (v2)
-- =====================================================
-- Fecha: 2025-07-19
-- Versión: 2.0 - Corregido para evitar duplicados
-- Descripción: Agrega campos obligatorios faltantes para ANCI
-- =====================================================

-- 1. VERIFICAR Y AGREGAR CAMPOS FALTANTES A TABLA INCIDENTES
-- =====================================================

-- Identificación y contacto de emergencia
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'SectorEsencial')
    ALTER TABLE INCIDENTES ADD SectorEsencial VARCHAR(100);

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'NombreReportante')
    ALTER TABLE INCIDENTES ADD NombreReportante VARCHAR(200);

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'CargoReportante')
    ALTER TABLE INCIDENTES ADD CargoReportante VARCHAR(100);

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'TelefonoEmergencia')
    ALTER TABLE INCIDENTES ADD TelefonoEmergencia VARCHAR(50);

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'EmailOficialSeguridad')
    ALTER TABLE INCIDENTES ADD EmailOficialSeguridad VARCHAR(200);

-- Estado y duración del incidente
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'IncidenteEnCurso')
    ALTER TABLE INCIDENTES ADD IncidenteEnCurso BIT DEFAULT 1;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'ContencionAplicada')
    ALTER TABLE INCIDENTES ADD ContencionAplicada BIT DEFAULT 0;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'DescripcionEstadoActual')
    ALTER TABLE INCIDENTES ADD DescripcionEstadoActual TEXT;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'DuracionEstimadaHoras')
    ALTER TABLE INCIDENTES ADD DuracionEstimadaHoras INT;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'DuracionRealHoras')
    ALTER TABLE INCIDENTES ADD DuracionRealHoras DECIMAL(10,2);

-- Análisis detallado del incidente
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'DescripcionCompleta')
    ALTER TABLE INCIDENTES ADD DescripcionCompleta TEXT;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'VectorAtaque')
    ALTER TABLE INCIDENTES ADD VectorAtaque VARCHAR(200);

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'VolumenDatosComprometidosGB')
    ALTER TABLE INCIDENTES ADD VolumenDatosComprometidosGB DECIMAL(10,2);

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'EfectosColaterales')
    ALTER TABLE INCIDENTES ADD EfectosColaterales TEXT;

-- Indicadores de Compromiso (IoCs)
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'IPsSospechosas')
    ALTER TABLE INCIDENTES ADD IPsSospechosas TEXT;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'HashesMalware')
    ALTER TABLE INCIDENTES ADD HashesMalware TEXT;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'DominiosMaliciosos')
    ALTER TABLE INCIDENTES ADD DominiosMaliciosos TEXT;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'CuentasComprometidas')
    ALTER TABLE INCIDENTES ADD CuentasComprometidas TEXT;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'URLsMaliciosas')
    ALTER TABLE INCIDENTES ADD URLsMaliciosas TEXT;

-- Análisis técnico y vulnerabilidades
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'VulnerabilidadExplotada')
    ALTER TABLE INCIDENTES ADD VulnerabilidadExplotada VARCHAR(200);

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'FallaControlSeguridad')
    ALTER TABLE INCIDENTES ADD FallaControlSeguridad TEXT;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'ErrorHumanoInvolucrado')
    ALTER TABLE INCIDENTES ADD ErrorHumanoInvolucrado BIT DEFAULT 0;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'DescripcionErrorHumano')
    ALTER TABLE INCIDENTES ADD DescripcionErrorHumano TEXT;

-- Acciones de respuesta y recuperación
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'MedidasErradicacion')
    ALTER TABLE INCIDENTES ADD MedidasErradicacion TEXT;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'EstadoRecuperacion')
    ALTER TABLE INCIDENTES ADD EstadoRecuperacion VARCHAR(50);

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'TiempoEstimadoResolucion')
    ALTER TABLE INCIDENTES ADD TiempoEstimadoResolucion INT;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'SistemasAislados')
    ALTER TABLE INCIDENTES ADD SistemasAislados TEXT;

-- Coordinaciones externas
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'NotificacionRegulador')
    ALTER TABLE INCIDENTES ADD NotificacionRegulador BIT DEFAULT 0;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'ReguladorNotificado')
    ALTER TABLE INCIDENTES ADD ReguladorNotificado VARCHAR(200);

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'DenunciaPolicial')
    ALTER TABLE INCIDENTES ADD DenunciaPolicial BIT DEFAULT 0;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'NumeroPartePolicial')
    ALTER TABLE INCIDENTES ADD NumeroPartePolicial VARCHAR(100);

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'ContactoProveedoresSeguridad')
    ALTER TABLE INCIDENTES ADD ContactoProveedoresSeguridad BIT DEFAULT 0;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'ComunicacionPublica')
    ALTER TABLE INCIDENTES ADD ComunicacionPublica BIT DEFAULT 0;

-- Plan de acción específico para OIV
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'ProgramaRestauracion')
    ALTER TABLE INCIDENTES ADD ProgramaRestauracion TEXT;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'ResponsablesAdministrativos')
    ALTER TABLE INCIDENTES ADD ResponsablesAdministrativos TEXT;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'TiempoRestablecimientoHoras')
    ALTER TABLE INCIDENTES ADD TiempoRestablecimientoHoras INT;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'RecursosNecesarios')
    ALTER TABLE INCIDENTES ADD RecursosNecesarios TEXT;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'AccionesCortoPlazo')
    ALTER TABLE INCIDENTES ADD AccionesCortoPlazo TEXT;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'AccionesMedianoPlazo')
    ALTER TABLE INCIDENTES ADD AccionesMedianoPlazo TEXT;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'AccionesLargoPlazo')
    ALTER TABLE INCIDENTES ADD AccionesLargoPlazo TEXT;

-- Impacto económico
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'CostosRecuperacion')
    ALTER TABLE INCIDENTES ADD CostosRecuperacion DECIMAL(15,2);

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'PerdidasOperativas')
    ALTER TABLE INCIDENTES ADD PerdidasOperativas DECIMAL(15,2);

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'CostosTerceros')
    ALTER TABLE INCIDENTES ADD CostosTerceros DECIMAL(15,2);

-- Timeline y cronología
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'CronologiaDetallada')
    ALTER TABLE INCIDENTES ADD CronologiaDetallada TEXT;

-- Campos para tracking de reportes ANCI
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'AlertaTempranaEnviada')
    ALTER TABLE INCIDENTES ADD AlertaTempranaEnviada BIT DEFAULT 0;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'FechaAlertaTemprana')
    ALTER TABLE INCIDENTES ADD FechaAlertaTemprana DATETIME;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'InformePreliminarEnviado')
    ALTER TABLE INCIDENTES ADD InformePreliminarEnviado BIT DEFAULT 0;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'FechaInformePreliminar')
    ALTER TABLE INCIDENTES ADD FechaInformePreliminar DATETIME;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'InformeCompletoEnviado')
    ALTER TABLE INCIDENTES ADD InformeCompletoEnviado BIT DEFAULT 0;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'FechaInformeCompleto')
    ALTER TABLE INCIDENTES ADD FechaInformeCompleto DATETIME;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'PlanAccionEnviado')
    ALTER TABLE INCIDENTES ADD PlanAccionEnviado BIT DEFAULT 0;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'FechaPlanAccion')
    ALTER TABLE INCIDENTES ADD FechaPlanAccion DATETIME;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'InformeFinalEnviado')
    ALTER TABLE INCIDENTES ADD InformeFinalEnviado BIT DEFAULT 0;

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'INCIDENTES' AND COLUMN_NAME = 'FechaInformeFinal')
    ALTER TABLE INCIDENTES ADD FechaInformeFinal DATETIME;

-- 2. CREAR TABLA PARA TIMELINE DE EVENTOS (SI NO EXISTE)
-- =====================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'INCIDENTES_TIMELINE')
BEGIN
    CREATE TABLE INCIDENTES_TIMELINE (
        TimelineID INT IDENTITY(1,1) PRIMARY KEY,
        IncidenteID INT NOT NULL,
        FechaHora DATETIME NOT NULL,
        Evento VARCHAR(500) NOT NULL,
        TipoEvento VARCHAR(50),
        Usuario VARCHAR(200),
        Detalles TEXT,
        Impacto VARCHAR(50),
        AccionTomada TEXT,
        FechaCreacion DATETIME DEFAULT GETDATE(),
        FOREIGN KEY (IncidenteID) REFERENCES INCIDENTES(IncidenteID)
    );
    PRINT 'Tabla INCIDENTES_TIMELINE creada exitosamente';
END
ELSE
    PRINT 'Tabla INCIDENTES_TIMELINE ya existe';

-- 3. CREAR TABLA PARA INDICADORES DE COMPROMISO (SI NO EXISTE)
-- =====================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'INCIDENTES_IOCS')
BEGIN
    CREATE TABLE INCIDENTES_IOCS (
        IoCID INT IDENTITY(1,1) PRIMARY KEY,
        IncidenteID INT NOT NULL,
        TipoIoC VARCHAR(50) NOT NULL,
        Valor VARCHAR(500) NOT NULL,
        Descripcion TEXT,
        Origen VARCHAR(200),
        Accion VARCHAR(100),
        Criticidad VARCHAR(20),
        FechaDeteccion DATETIME,
        FechaBloqueo DATETIME,
        Activo BIT DEFAULT 1,
        FechaCreacion DATETIME DEFAULT GETDATE(),
        FOREIGN KEY (IncidenteID) REFERENCES INCIDENTES(IncidenteID)
    );
    PRINT 'Tabla INCIDENTES_IOCS creada exitosamente';
END
ELSE
    PRINT 'Tabla INCIDENTES_IOCS ya existe';

-- 4. CREAR TABLA PARA COORDINACIONES EXTERNAS (SI NO EXISTE)
-- =====================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'INCIDENTES_COORDINACIONES')
BEGIN
    CREATE TABLE INCIDENTES_COORDINACIONES (
        CoordinacionID INT IDENTITY(1,1) PRIMARY KEY,
        IncidenteID INT NOT NULL,
        TipoEntidad VARCHAR(100),
        NombreEntidad VARCHAR(200),
        PersonaContacto VARCHAR(200),
        CargoContacto VARCHAR(100),
        TelefonoContacto VARCHAR(50),
        EmailContacto VARCHAR(200),
        FechaNotificacion DATETIME,
        TipoNotificacion VARCHAR(50),
        NumeroOficio VARCHAR(100),
        Descripcion TEXT,
        Respuesta TEXT,
        EstadoCoordinacion VARCHAR(50),
        FechaCreacion DATETIME DEFAULT GETDATE(),
        FOREIGN KEY (IncidenteID) REFERENCES INCIDENTES(IncidenteID)
    );
    PRINT 'Tabla INCIDENTES_COORDINACIONES creada exitosamente';
END
ELSE
    PRINT 'Tabla INCIDENTES_COORDINACIONES ya existe';

-- 5. CREAR ÍNDICES PARA MEJORAR PERFORMANCE
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_INCIDENTES_TIMELINE_IncidenteID')
    CREATE INDEX IX_INCIDENTES_TIMELINE_IncidenteID ON INCIDENTES_TIMELINE(IncidenteID);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_INCIDENTES_TIMELINE_FechaHora')
    CREATE INDEX IX_INCIDENTES_TIMELINE_FechaHora ON INCIDENTES_TIMELINE(FechaHora);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_INCIDENTES_IOCS_IncidenteID')
    CREATE INDEX IX_INCIDENTES_IOCS_IncidenteID ON INCIDENTES_IOCS(IncidenteID);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_INCIDENTES_IOCS_TipoIoC')
    CREATE INDEX IX_INCIDENTES_IOCS_TipoIoC ON INCIDENTES_IOCS(TipoIoC);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_INCIDENTES_COORDINACIONES_IncidenteID')
    CREATE INDEX IX_INCIDENTES_COORDINACIONES_IncidenteID ON INCIDENTES_COORDINACIONES(IncidenteID);

-- 6. AGREGAR CAMPOS A TABLA EMPRESAS SI NO EXISTEN
-- =====================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'EMPRESAS' AND COLUMN_NAME = 'SectorEsencial')
BEGIN
    ALTER TABLE EMPRESAS ADD SectorEsencial VARCHAR(100);
    PRINT 'Campo SectorEsencial agregado a tabla EMPRESAS';
END

-- 7. ELIMINAR Y RECREAR PROCEDIMIENTO
-- =====================================================
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_RegistrarEventoTimeline')
    DROP PROCEDURE sp_RegistrarEventoTimeline;
GO

CREATE PROCEDURE sp_RegistrarEventoTimeline
    @IncidenteID INT,
    @Evento VARCHAR(500),
    @TipoEvento VARCHAR(50),
    @Usuario VARCHAR(200) = NULL,
    @Detalles TEXT = NULL,
    @Impacto VARCHAR(50) = NULL,
    @AccionTomada TEXT = NULL
AS
BEGIN
    INSERT INTO INCIDENTES_TIMELINE (
        IncidenteID, FechaHora, Evento, TipoEvento, 
        Usuario, Detalles, Impacto, AccionTomada
    )
    VALUES (
        @IncidenteID, GETDATE(), @Evento, @TipoEvento,
        @Usuario, @Detalles, @Impacto, @AccionTomada
    );
END;
GO

-- 8. ELIMINAR Y RECREAR VISTA PARA REPORTES ANCI
-- =====================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_IncidentesANCI_Completo')
    DROP VIEW vw_IncidentesANCI_Completo;
GO

CREATE VIEW vw_IncidentesANCI_Completo AS
SELECT 
    i.IncidenteID,
    i.Titulo,
    i.FechaDeteccion,
    i.FechaOcurrencia,
    i.Criticidad,
    i.EstadoActual,
    
    -- Datos empresa
    e.RazonSocial,
    e.RUT,
    e.TipoEmpresa,
    COALESCE(i.SectorEsencial, e.SectorEsencial) as SectorEsencial,
    
    -- Contacto emergencia
    i.NombreReportante,
    i.CargoReportante,
    i.TelefonoEmergencia,
    i.EmailOficialSeguridad,
    
    -- Estado incidente
    i.IncidenteEnCurso,
    i.ContencionAplicada,
    i.DuracionEstimadaHoras,
    i.DuracionRealHoras,
    
    -- Impacto
    i.SistemasAfectados,
    i.ServiciosInterrumpidos,
    i.AlcanceGeografico,
    i.VolumenDatosComprometidosGB,
    
    -- Análisis
    i.VectorAtaque,
    i.VulnerabilidadExplotada,
    i.CausaRaiz,
    
    -- Coordinaciones
    i.SolicitarCSIRT,
    i.NotificacionRegulador,
    i.DenunciaPolicial,
    i.ComunicacionPublica,
    
    -- Tracking reportes
    i.AlertaTempranaEnviada,
    i.FechaAlertaTemprana,
    i.InformePreliminarEnviado,
    i.FechaInformePreliminar,
    i.InformeCompletoEnviado,
    i.FechaInformeCompleto,
    i.InformeFinalEnviado,
    i.FechaInformeFinal,
    
    -- Fechas transformación
    i.FechaTransformacionANCI,
    i.FechaActualizacion
    
FROM INCIDENTES i
LEFT JOIN EMPRESAS e ON i.EmpresaID = e.EmpresaID
WHERE i.ReporteAnciID IS NOT NULL;
GO

-- 9. MENSAJE FINAL
-- =====================================================
PRINT '=====================================================';
PRINT 'SCRIPT v2 EJECUTADO EXITOSAMENTE';
PRINT '';
PRINT 'RESUMEN DE CAMBIOS:';
PRINT '- Campos ANCI agregados a tabla INCIDENTES';
PRINT '- Tablas nuevas verificadas/creadas:';
PRINT '  * INCIDENTES_TIMELINE';
PRINT '  * INCIDENTES_IOCS';
PRINT '  * INCIDENTES_COORDINACIONES';
PRINT '- Procedimiento: sp_RegistrarEventoTimeline';
PRINT '- Vista: vw_IncidentesANCI_Completo';
PRINT '';
PRINT 'SIGUIENTE PASO:';
PRINT 'Actualizar valores de SectorEsencial en tabla EMPRESAS';
PRINT '=====================================================';

-- 10. QUERY DE VERIFICACIÓN
-- =====================================================
SELECT 
    'Campos agregados a INCIDENTES' as Verificacion,
    COUNT(*) as Total
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'INCIDENTES' 
AND COLUMN_NAME IN (
    'SectorEsencial', 'NombreReportante', 'CargoReportante',
    'TelefonoEmergencia', 'EmailOficialSeguridad', 'IncidenteEnCurso',
    'VectorAtaque', 'IPsSospechosas', 'AlertaTempranaEnviada'
);
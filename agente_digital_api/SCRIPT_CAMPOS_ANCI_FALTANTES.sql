-- =====================================================
-- SCRIPT SQL - CAMPOS FALTANTES PARA CUMPLIR CON ANCI
-- =====================================================
-- Fecha: 2025-07-19
-- Descripción: Agrega todos los campos obligatorios faltantes
-- para cumplir con los requisitos de reporte ANCI
-- =====================================================

-- 1. AGREGAR CAMPOS FALTANTES A TABLA INCIDENTES
-- =====================================================

-- Identificación y contacto de emergencia
ALTER TABLE INCIDENTES ADD SectorEsencial VARCHAR(100);
ALTER TABLE INCIDENTES ADD NombreReportante VARCHAR(200);
ALTER TABLE INCIDENTES ADD CargoReportante VARCHAR(100);
ALTER TABLE INCIDENTES ADD TelefonoEmergencia VARCHAR(50);
ALTER TABLE INCIDENTES ADD EmailOficialSeguridad VARCHAR(200);

-- Estado y duración del incidente
ALTER TABLE INCIDENTES ADD IncidenteEnCurso BIT DEFAULT 1;
ALTER TABLE INCIDENTES ADD ContencionAplicada BIT DEFAULT 0;
ALTER TABLE INCIDENTES ADD DescripcionEstadoActual TEXT;
ALTER TABLE INCIDENTES ADD DuracionEstimadaHoras INT;
ALTER TABLE INCIDENTES ADD DuracionRealHoras DECIMAL(10,2);

-- Análisis detallado del incidente
ALTER TABLE INCIDENTES ADD DescripcionCompleta TEXT;
ALTER TABLE INCIDENTES ADD VectorAtaque VARCHAR(200);
ALTER TABLE INCIDENTES ADD VolumenDatosComprometidosGB DECIMAL(10,2);
ALTER TABLE INCIDENTES ADD EfectosColaterales TEXT;

-- Indicadores de Compromiso (IoCs)
ALTER TABLE INCIDENTES ADD IPsSospechosas TEXT;
ALTER TABLE INCIDENTES ADD HashesMalware TEXT;
ALTER TABLE INCIDENTES ADD DominiosMaliciosos TEXT;
ALTER TABLE INCIDENTES ADD CuentasComprometidas TEXT;
ALTER TABLE INCIDENTES ADD URLsMaliciosas TEXT;

-- Análisis técnico y vulnerabilidades
ALTER TABLE INCIDENTES ADD VulnerabilidadExplotada VARCHAR(200);
ALTER TABLE INCIDENTES ADD FallaControlSeguridad TEXT;
ALTER TABLE INCIDENTES ADD ErrorHumanoInvolucrado BIT DEFAULT 0;
ALTER TABLE INCIDENTES ADD DescripcionErrorHumano TEXT;

-- Acciones de respuesta y recuperación
ALTER TABLE INCIDENTES ADD MedidasErradicacion TEXT;
ALTER TABLE INCIDENTES ADD EstadoRecuperacion VARCHAR(50);
ALTER TABLE INCIDENTES ADD TiempoEstimadoResolucion INT;
ALTER TABLE INCIDENTES ADD SistemasAislados TEXT;

-- Coordinaciones externas
ALTER TABLE INCIDENTES ADD NotificacionRegulador BIT DEFAULT 0;
ALTER TABLE INCIDENTES ADD ReguladorNotificado VARCHAR(200);
ALTER TABLE INCIDENTES ADD DenunciaPolicial BIT DEFAULT 0;
ALTER TABLE INCIDENTES ADD NumeroPartePolicial VARCHAR(100);
ALTER TABLE INCIDENTES ADD ContactoProveedoresSeguridad BIT DEFAULT 0;
ALTER TABLE INCIDENTES ADD ComunicacionPublica BIT DEFAULT 0;

-- Plan de acción específico para OIV
ALTER TABLE INCIDENTES ADD ProgramaRestauracion TEXT;
ALTER TABLE INCIDENTES ADD ResponsablesAdministrativos TEXT;
ALTER TABLE INCIDENTES ADD TiempoRestablecimientoHoras INT;
ALTER TABLE INCIDENTES ADD RecursosNecesarios TEXT;
ALTER TABLE INCIDENTES ADD AccionesCortoPlazo TEXT;
ALTER TABLE INCIDENTES ADD AccionesMedianoPlazo TEXT;
ALTER TABLE INCIDENTES ADD AccionesLargoPlazo TEXT;

-- Impacto económico
ALTER TABLE INCIDENTES ADD CostosRecuperacion DECIMAL(15,2);
ALTER TABLE INCIDENTES ADD PerdidasOperativas DECIMAL(15,2);
ALTER TABLE INCIDENTES ADD CostosTerceros DECIMAL(15,2);

-- Timeline y cronología
ALTER TABLE INCIDENTES ADD CronologiaDetallada TEXT;

-- Campos para tracking de reportes ANCI
ALTER TABLE INCIDENTES ADD AlertaTempranaEnviada BIT DEFAULT 0;
ALTER TABLE INCIDENTES ADD FechaAlertaTemprana DATETIME;
ALTER TABLE INCIDENTES ADD InformePreliminarEnviado BIT DEFAULT 0;
ALTER TABLE INCIDENTES ADD FechaInformePreliminar DATETIME;
ALTER TABLE INCIDENTES ADD InformeCompletoEnviado BIT DEFAULT 0;
ALTER TABLE INCIDENTES ADD FechaInformeCompleto DATETIME;
ALTER TABLE INCIDENTES ADD PlanAccionEnviado BIT DEFAULT 0;
ALTER TABLE INCIDENTES ADD FechaPlanAccion DATETIME;
ALTER TABLE INCIDENTES ADD InformeFinalEnviado BIT DEFAULT 0;
ALTER TABLE INCIDENTES ADD FechaInformeFinal DATETIME;

-- 2. CREAR TABLA PARA TIMELINE DE EVENTOS
-- =====================================================
CREATE TABLE INCIDENTES_TIMELINE (
    TimelineID INT IDENTITY(1,1) PRIMARY KEY,
    IncidenteID INT NOT NULL,
    FechaHora DATETIME NOT NULL,
    Evento VARCHAR(500) NOT NULL,
    TipoEvento VARCHAR(50), -- deteccion, contencion, escalamiento, resolucion, notificacion
    Usuario VARCHAR(200),
    Detalles TEXT,
    Impacto VARCHAR(50), -- critico, alto, medio, bajo
    AccionTomada TEXT,
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (IncidenteID) REFERENCES INCIDENTES(IncidenteID)
);

-- 3. CREAR TABLA PARA INDICADORES DE COMPROMISO
-- =====================================================
CREATE TABLE INCIDENTES_IOCS (
    IoCID INT IDENTITY(1,1) PRIMARY KEY,
    IncidenteID INT NOT NULL,
    TipoIoC VARCHAR(50) NOT NULL, -- IP, Hash, Dominio, URL, Cuenta, Email
    Valor VARCHAR(500) NOT NULL,
    Descripcion TEXT,
    Origen VARCHAR(200), -- Logs, Análisis forense, Reporte usuario, etc
    Accion VARCHAR(100), -- Bloqueado, Monitoreado, Pendiente, Investigando
    Criticidad VARCHAR(20), -- Alta, Media, Baja
    FechaDeteccion DATETIME,
    FechaBloqueo DATETIME,
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (IncidenteID) REFERENCES INCIDENTES(IncidenteID)
);

-- 4. CREAR TABLA PARA COORDINACIONES EXTERNAS
-- =====================================================
CREATE TABLE INCIDENTES_COORDINACIONES (
    CoordinacionID INT IDENTITY(1,1) PRIMARY KEY,
    IncidenteID INT NOT NULL,
    TipoEntidad VARCHAR(100), -- Regulador, Policia, Proveedor, CSIRT, Otro
    NombreEntidad VARCHAR(200),
    PersonaContacto VARCHAR(200),
    CargoContacto VARCHAR(100),
    TelefonoContacto VARCHAR(50),
    EmailContacto VARCHAR(200),
    FechaNotificacion DATETIME,
    TipoNotificacion VARCHAR(50), -- Formal, Informal, Urgente
    NumeroOficio VARCHAR(100),
    Descripcion TEXT,
    Respuesta TEXT,
    EstadoCoordinacion VARCHAR(50), -- Notificado, En proceso, Cerrado
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (IncidenteID) REFERENCES INCIDENTES(IncidenteID)
);

-- 5. CREAR ÍNDICES PARA MEJORAR PERFORMANCE
-- =====================================================
CREATE INDEX IX_INCIDENTES_TIMELINE_IncidenteID ON INCIDENTES_TIMELINE(IncidenteID);
CREATE INDEX IX_INCIDENTES_TIMELINE_FechaHora ON INCIDENTES_TIMELINE(FechaHora);
CREATE INDEX IX_INCIDENTES_IOCS_IncidenteID ON INCIDENTES_IOCS(IncidenteID);
CREATE INDEX IX_INCIDENTES_IOCS_TipoIoC ON INCIDENTES_IOCS(TipoIoC);
CREATE INDEX IX_INCIDENTES_COORDINACIONES_IncidenteID ON INCIDENTES_COORDINACIONES(IncidenteID);

-- 6. AGREGAR CAMPOS A TABLA EMPRESAS SI NO EXISTEN
-- =====================================================
-- Verificar si existe columna SectorEsencial en EMPRESAS
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'EMPRESAS' AND COLUMN_NAME = 'SectorEsencial')
BEGIN
    ALTER TABLE EMPRESAS ADD SectorEsencial VARCHAR(100);
END

-- 7. VALORES PREDETERMINADOS PARA SECTORES ESENCIALES
-- =====================================================
-- Actualizar con valores según normativa ANCI
/*
UPDATE EMPRESAS SET SectorEsencial = 
    CASE 
        WHEN LOWER(RazonSocial) LIKE '%banco%' OR LOWER(RazonSocial) LIKE '%financ%' THEN 'Financiero'
        WHEN LOWER(RazonSocial) LIKE '%salud%' OR LOWER(RazonSocial) LIKE '%clinic%' OR LOWER(RazonSocial) LIKE '%hospital%' THEN 'Salud'
        WHEN LOWER(RazonSocial) LIKE '%energ%' OR LOWER(RazonSocial) LIKE '%electric%' THEN 'Energía'
        WHEN LOWER(RazonSocial) LIKE '%telec%' OR LOWER(RazonSocial) LIKE '%telefo%' THEN 'Telecomunicaciones'
        WHEN LOWER(RazonSocial) LIKE '%agua%' OR LOWER(RazonSocial) LIKE '%sanit%' THEN 'Agua'
        WHEN LOWER(RazonSocial) LIKE '%transport%' THEN 'Transporte'
        ELSE 'Por Definir'
    END
WHERE SectorEsencial IS NULL;
*/

-- 8. PROCEDIMIENTO PARA REGISTRAR EVENTOS EN TIMELINE
-- =====================================================
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

-- 9. VISTA PARA REPORTES ANCI
-- =====================================================
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
    i.UsuariosAfectados,
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

-- 10. MENSAJE FINAL
-- =====================================================
PRINT '=====================================================';
PRINT 'SCRIPT EJECUTADO EXITOSAMENTE';
PRINT 'Campos ANCI agregados a la base de datos';
PRINT 'Tablas nuevas creadas:';
PRINT '  - INCIDENTES_TIMELINE';
PRINT '  - INCIDENTES_IOCS';
PRINT '  - INCIDENTES_COORDINACIONES';
PRINT 'Vista creada: vw_IncidentesANCI_Completo';
PRINT '=====================================================';
PRINT 'IMPORTANTE: Actualizar los valores de SectorEsencial';
PRINT 'en la tabla EMPRESAS según corresponda';
PRINT '=====================================================';
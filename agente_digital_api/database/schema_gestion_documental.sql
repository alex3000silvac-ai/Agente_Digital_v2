-- Schema para Gestión Documental ANCI
-- Sistema de gestión de cumplimiento según Ley 21.663

-- Tabla principal de documentos
CREATE TABLE DOCUMENTOS_ANCI (
    DocumentoID INT IDENTITY(1,1) PRIMARY KEY,
    EmpresaID INT NOT NULL,
    CarpetaID INT NOT NULL,
    NombreArchivo NVARCHAR(255) NOT NULL,
    RutaArchivo NVARCHAR(500) NOT NULL,
    TipoDocumento NVARCHAR(100),
    FechaSubida DATETIME DEFAULT GETDATE(),
    FechaVencimiento DATETIME NULL,
    FechaEliminacion DATETIME NULL,
    Descripcion NVARCHAR(MAX),
    SubidoPor NVARCHAR(100),
    Hash NVARCHAR(64), -- SHA-256 del archivo
    Tamaño BIGINT,
    Activo BIT DEFAULT 1,
    Version INT DEFAULT 1,
    CONSTRAINT FK_DocumentosANCI_Empresa FOREIGN KEY (EmpresaID) REFERENCES Empresas(EmpresaID),
    INDEX IX_DocumentosANCI_Empresa (EmpresaID),
    INDEX IX_DocumentosANCI_Carpeta (CarpetaID),
    INDEX IX_DocumentosANCI_Vencimiento (FechaVencimiento),
    INDEX IX_DocumentosANCI_Activo (Activo)
);

-- Tabla de auditoría de documentos
CREATE TABLE AUDITORIA_DOCUMENTOS (
    AuditoriaID INT IDENTITY(1,1) PRIMARY KEY,
    DocumentoID INT NOT NULL,
    Accion NVARCHAR(50) NOT NULL, -- CREAR, VER, DESCARGAR, EDITAR, ELIMINAR
    Usuario NVARCHAR(100) NOT NULL,
    FechaAccion DATETIME DEFAULT GETDATE(),
    IP NVARCHAR(45),
    Detalles NVARCHAR(MAX),
    CONSTRAINT FK_AuditoriaDocumentos_Documento FOREIGN KEY (DocumentoID) REFERENCES DOCUMENTOS_ANCI(DocumentoID),
    INDEX IX_AuditoriaDocumentos_Documento (DocumentoID),
    INDEX IX_AuditoriaDocumentos_FechaAccion (FechaAccion)
);

-- Tabla de alertas configuradas
CREATE TABLE ALERTAS_DOCUMENTOS (
    AlertaID INT IDENTITY(1,1) PRIMARY KEY,
    DocumentoID INT NOT NULL,
    TipoAlerta NVARCHAR(50) NOT NULL, -- VENCIMIENTO, FALTA_DOCUMENTO, ACTUALIZACION
    DiasAnticipacion INT NOT NULL,
    FechaAlerta DATETIME NOT NULL,
    Enviada BIT DEFAULT 0,
    FechaEnvio DATETIME NULL,
    Destinatarios NVARCHAR(MAX), -- JSON con emails
    CONSTRAINT FK_AlertasDocumentos_Documento FOREIGN KEY (DocumentoID) REFERENCES DOCUMENTOS_ANCI(DocumentoID),
    INDEX IX_AlertasDocumentos_FechaAlerta (FechaAlerta),
    INDEX IX_AlertasDocumentos_Enviada (Enviada)
);

-- Tabla de plantillas de documentos
CREATE TABLE PLANTILLAS_DOCUMENTOS (
    PlantillaID INT IDENTITY(1,1) PRIMARY KEY,
    CarpetaID INT NOT NULL,
    NombrePlantilla NVARCHAR(255) NOT NULL,
    TipoDocumento NVARCHAR(100) NOT NULL,
    Descripcion NVARCHAR(MAX),
    RutaPlantilla NVARCHAR(500),
    CamposRequeridos NVARCHAR(MAX), -- JSON con campos requeridos
    Obligatorio BIT DEFAULT 0,
    SoloOIV BIT DEFAULT 0,
    SoloPSE BIT DEFAULT 0,
    Activo BIT DEFAULT 1
);

-- Tabla de checklist de cumplimiento
CREATE TABLE CHECKLIST_CUMPLIMIENTO (
    ChecklistID INT IDENTITY(1,1) PRIMARY KEY,
    EmpresaID INT NOT NULL,
    CarpetaID INT NOT NULL,
    ItemID INT NOT NULL,
    Completado BIT DEFAULT 0,
    DocumentoID INT NULL,
    FechaCompletado DATETIME NULL,
    Observaciones NVARCHAR(MAX),
    CONSTRAINT FK_Checklist_Empresa FOREIGN KEY (EmpresaID) REFERENCES Empresas(EmpresaID),
    CONSTRAINT FK_Checklist_Documento FOREIGN KEY (DocumentoID) REFERENCES DOCUMENTOS_ANCI(DocumentoID),
    UNIQUE(EmpresaID, CarpetaID, ItemID)
);

-- Tabla de configuración de carpetas
CREATE TABLE CONFIGURACION_CARPETAS (
    ConfigID INT IDENTITY(1,1) PRIMARY KEY,
    EmpresaID INT NOT NULL,
    CarpetaID INT NOT NULL,
    Configuracion NVARCHAR(MAX), -- JSON con configuración específica
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FechaActualizacion DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_ConfigCarpetas_Empresa FOREIGN KEY (EmpresaID) REFERENCES Empresas(EmpresaID),
    UNIQUE(EmpresaID, CarpetaID)
);

-- Tabla de versiones de documentos
CREATE TABLE VERSIONES_DOCUMENTOS (
    VersionID INT IDENTITY(1,1) PRIMARY KEY,
    DocumentoID INT NOT NULL,
    VersionNumero INT NOT NULL,
    NombreArchivo NVARCHAR(255) NOT NULL,
    RutaArchivo NVARCHAR(500) NOT NULL,
    Hash NVARCHAR(64),
    FechaVersion DATETIME DEFAULT GETDATE(),
    SubidoPor NVARCHAR(100),
    Comentarios NVARCHAR(MAX),
    CONSTRAINT FK_Versiones_Documento FOREIGN KEY (DocumentoID) REFERENCES DOCUMENTOS_ANCI(DocumentoID),
    INDEX IX_Versiones_Documento (DocumentoID)
);

-- Vistas útiles
GO

-- Vista de documentos con estado de vencimiento
CREATE VIEW VW_DOCUMENTOS_ESTADO AS
SELECT 
    d.DocumentoID,
    d.EmpresaID,
    e.RazonSocial,
    e.TipoEmpresa,
    d.CarpetaID,
    d.NombreArchivo,
    d.TipoDocumento,
    d.FechaSubida,
    d.FechaVencimiento,
    CASE 
        WHEN d.FechaVencimiento IS NULL THEN 'Sin vencimiento'
        WHEN d.FechaVencimiento < GETDATE() THEN 'Vencido'
        WHEN d.FechaVencimiento BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE()) THEN 'Por vencer'
        ELSE 'Vigente'
    END AS EstadoDocumento,
    DATEDIFF(day, GETDATE(), d.FechaVencimiento) AS DiasParaVencer,
    d.Activo
FROM DOCUMENTOS_ANCI d
INNER JOIN Empresas e ON d.EmpresaID = e.EmpresaID
WHERE d.Activo = 1;

GO

-- Vista de cumplimiento por empresa
CREATE VIEW VW_CUMPLIMIENTO_EMPRESA AS
SELECT 
    e.EmpresaID,
    e.RazonSocial,
    e.TipoEmpresa,
    COUNT(DISTINCT d.CarpetaID) AS CarpetasConDocumentos,
    12 AS TotalCarpetas, -- Total de carpetas en el sistema
    CAST(COUNT(DISTINCT d.CarpetaID) AS FLOAT) / 12 * 100 AS PorcentajeCumplimiento,
    SUM(CASE WHEN d.FechaVencimiento < GETDATE() THEN 1 ELSE 0 END) AS DocumentosVencidos,
    SUM(CASE WHEN d.FechaVencimiento BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE()) THEN 1 ELSE 0 END) AS DocumentosPorVencer
FROM Empresas e
LEFT JOIN DOCUMENTOS_ANCI d ON e.EmpresaID = d.EmpresaID AND d.Activo = 1
GROUP BY e.EmpresaID, e.RazonSocial, e.TipoEmpresa;

GO

-- Procedimientos almacenados

-- Procedimiento para generar alertas automáticas
CREATE PROCEDURE SP_GENERAR_ALERTAS_VENCIMIENTO
AS
BEGIN
    -- Insertar alertas para documentos próximos a vencer
    INSERT INTO ALERTAS_DOCUMENTOS (DocumentoID, TipoAlerta, DiasAnticipacion, FechaAlerta, Destinatarios)
    SELECT 
        d.DocumentoID,
        'VENCIMIENTO',
        DATEDIFF(day, GETDATE(), d.FechaVencimiento),
        DATEADD(day, -30, d.FechaVencimiento),
        '[]' -- Se debe actualizar con los destinatarios reales
    FROM DOCUMENTOS_ANCI d
    WHERE d.Activo = 1 
        AND d.FechaVencimiento IS NOT NULL
        AND d.FechaVencimiento BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE())
        AND NOT EXISTS (
            SELECT 1 FROM ALERTAS_DOCUMENTOS a 
            WHERE a.DocumentoID = d.DocumentoID 
                AND a.TipoAlerta = 'VENCIMIENTO'
                AND a.Enviada = 0
        );
END;

GO

-- Procedimiento para obtener dashboard de cumplimiento
CREATE PROCEDURE SP_DASHBOARD_CUMPLIMIENTO
    @EmpresaID INT
AS
BEGIN
    -- Métricas generales
    SELECT 
        COUNT(DISTINCT CarpetaID) as CarpetasConDocumentos,
        COUNT(*) as TotalDocumentos,
        SUM(CASE WHEN FechaVencimiento < GETDATE() THEN 1 ELSE 0 END) as DocumentosVencidos,
        SUM(CASE WHEN FechaVencimiento BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE()) THEN 1 ELSE 0 END) as ProximosVencer,
        SUM(CASE WHEN FechaVencimiento IS NULL OR FechaVencimiento > DATEADD(day, 30, GETDATE()) THEN 1 ELSE 0 END) as DocumentosVigentes
    FROM DOCUMENTOS_ANCI
    WHERE EmpresaID = @EmpresaID AND Activo = 1;
    
    -- Documentos por carpeta
    SELECT 
        CarpetaID,
        COUNT(*) as CantidadDocumentos,
        MAX(FechaSubida) as UltimaActualizacion
    FROM DOCUMENTOS_ANCI
    WHERE EmpresaID = @EmpresaID AND Activo = 1
    GROUP BY CarpetaID;
    
    -- Alertas activas
    SELECT TOP 10
        a.AlertaID,
        a.TipoAlerta,
        a.DiasAnticipacion,
        a.FechaAlerta,
        d.NombreArchivo,
        d.CarpetaID
    FROM ALERTAS_DOCUMENTOS a
    INNER JOIN DOCUMENTOS_ANCI d ON a.DocumentoID = d.DocumentoID
    WHERE d.EmpresaID = @EmpresaID AND a.Enviada = 0
    ORDER BY a.FechaAlerta;
END;

GO

-- Índices adicionales para mejorar rendimiento
CREATE INDEX IX_DocumentosANCI_EmpresaCarpeta ON DOCUMENTOS_ANCI(EmpresaID, CarpetaID);
CREATE INDEX IX_DocumentosANCI_TipoDocumento ON DOCUMENTOS_ANCI(TipoDocumento);
CREATE INDEX IX_AuditoriaDocumentos_Usuario ON AUDITORIA_DOCUMENTOS(Usuario);

-- Datos iniciales de plantillas
INSERT INTO PLANTILLAS_DOCUMENTOS (CarpetaID, NombrePlantilla, TipoDocumento, Descripcion, Obligatorio, SoloOIV, SoloPSE)
VALUES
-- Carpeta 01_REGISTRO_ANCI (ID: 2)
(2, 'Comprobante de Registro ANCI', 'comprobante_registro', 'Comprobante oficial del registro en la plataforma ANCI', 1, 0, 0),
(2, 'Designación de Encargado (FEA)', 'designacion_encargado', 'Documento de designación firmado con Firma Electrónica Avanzada', 1, 0, 0),
(2, 'Certificado de Vigencia de la Sociedad', 'certificado_vigencia_sociedad', 'Certificado actualizado de vigencia de la sociedad', 1, 0, 0),
(2, 'Certificado de Vigencia de Poderes', 'certificado_vigencia_poderes', 'Certificado de vigencia de poderes del representante legal', 1, 0, 0),

-- Carpeta 03_GOBERNANZA_SEGURIDAD (ID: 4)
(4, 'Política General de Seguridad', 'politica_seguridad', 'Política de seguridad de la información aprobada', 1, 0, 0),
(4, 'Manual SGSI', 'manual_sgsi', 'Manual del Sistema de Gestión de Seguridad de la Información', 1, 1, 0), -- Solo OIV
(4, 'Matriz de Riesgos', 'matriz_riesgos', 'Matriz de identificación y evaluación de riesgos', 1, 0, 0),
(4, 'Declaración de Aplicabilidad', 'declaracion_aplicabilidad', 'Declaración de aplicabilidad de controles ISO 27001', 0, 1, 0), -- Solo OIV
(4, 'Plan de Tratamiento de Riesgos', 'plan_tratamiento_riesgos', 'Plan de tratamiento de riesgos identificados', 1, 0, 0),

-- Carpeta 04_GESTION_INCIDENTES (ID: 5)
(5, 'Plan de Respuesta a Incidentes', 'plan_respuesta_incidentes', 'Plan documentado de respuesta a incidentes', 1, 0, 0),
(5, 'Procedimiento de Clasificación', 'procedimiento_clasificacion', 'Procedimiento para clasificar incidentes', 1, 0, 0),
(5, 'Contactos de Emergencia', 'contactos_emergencia', 'Lista actualizada de contactos de emergencia', 1, 0, 0),

-- Carpeta 06_CERTIFICACIONES (ID: 7)
(7, 'Certificado ISO 27001', 'cert_iso27001', 'Certificado vigente ISO 27001', 1, 1, 0), -- Obligatorio para OIV
(7, 'Certificado ISO 22301', 'cert_iso22301', 'Certificado ISO 22301 de continuidad de negocio', 0, 0, 0),
(7, 'Certificado ISO 20000', 'cert_iso20000', 'Certificado ISO 20000 de gestión de servicios', 0, 0, 0),

-- Carpeta 09_CONTINUIDAD_NEGOCIO (ID: 10)
(10, 'Análisis de Impacto de Negocio (BIA)', 'bia_completo', 'Análisis completo de impacto de negocio', 1, 1, 0), -- Crítico para OIV
(10, 'Plan de Continuidad de Negocio (BCP)', 'bcp_master', 'Plan maestro de continuidad de negocio', 1, 1, 0), -- Crítico para OIV
(10, 'Plan de Recuperación ante Desastres (DRP)', 'drp_tecnologico', 'Plan de recuperación tecnológica', 1, 1, 0); -- Crítico para OIV

-- Fin del script
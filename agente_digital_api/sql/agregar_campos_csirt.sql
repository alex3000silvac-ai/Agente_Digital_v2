-- ========================================
-- AGREGAR CAMPOS CSIRT A INCIDENTES
-- ========================================
-- Campos para gestionar solicitudes de ayuda al CSIRT
-- Requerido por plantilla ANCI
-- ========================================

-- 1. Agregar campos a la tabla Incidentes
ALTER TABLE Incidentes ADD SolicitarAyudaCSIRT BIT DEFAULT 0;
ALTER TABLE Incidentes ADD FechaSolicitudCSIRT DATETIME NULL;
ALTER TABLE Incidentes ADD TipoAyudaCSIRT NVARCHAR(200) NULL;
ALTER TABLE Incidentes ADD DescripcionAyudaCSIRT NVARCHAR(MAX) NULL;
ALTER TABLE Incidentes ADD EstadoSolicitudCSIRT NVARCHAR(50) NULL;
ALTER TABLE Incidentes ADD RespuestaCSIRT NVARCHAR(MAX) NULL;
ALTER TABLE Incidentes ADD ContactoCSIRT NVARCHAR(200) NULL;

-- 2. Agregar comentarios descriptivos
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Indica si se solicitó ayuda al CSIRT para este incidente',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE',  @level1name = N'Incidentes',
    @level2type = N'COLUMN', @level2name = N'SolicitarAyudaCSIRT';

EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Fecha y hora en que se solicitó ayuda al CSIRT',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE',  @level1name = N'Incidentes',
    @level2type = N'COLUMN', @level2name = N'FechaSolicitudCSIRT';

EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Tipo de ayuda solicitada: Análisis Forense, Contención, Asesoría, Coordinación, Otro',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE',  @level1name = N'Incidentes',
    @level2type = N'COLUMN', @level2name = N'TipoAyudaCSIRT';

EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Descripción detallada de la ayuda solicitada al CSIRT',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE',  @level1name = N'Incidentes',
    @level2type = N'COLUMN', @level2name = N'DescripcionAyudaCSIRT';

EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Estado de la solicitud: Pendiente, En Proceso, Completada, Rechazada',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE',  @level1name = N'Incidentes',
    @level2type = N'COLUMN', @level2name = N'EstadoSolicitudCSIRT';

-- 3. Crear tabla de auditoría para solicitudes CSIRT
CREATE TABLE IF NOT EXISTS CSIRT_SOLICITUDES_LOG (
    LogID INT PRIMARY KEY IDENTITY(1,1),
    IncidenteID INT NOT NULL,
    TipoEvento NVARCHAR(50) NOT NULL, -- 'SOLICITUD', 'ACTUALIZACION', 'RESPUESTA'
    FechaEvento DATETIME DEFAULT GETDATE(),
    Usuario NVARCHAR(100),
    Descripcion NVARCHAR(MAX),
    DatosAnteriores NVARCHAR(MAX), -- JSON
    DatosNuevos NVARCHAR(MAX), -- JSON
    FOREIGN KEY (IncidenteID) REFERENCES Incidentes(IncidenteID)
);

-- 4. Índices para optimización
CREATE INDEX IDX_CSIRT_Solicitudes ON Incidentes(SolicitarAyudaCSIRT) WHERE SolicitarAyudaCSIRT = 1;
CREATE INDEX IDX_CSIRT_Estado ON Incidentes(EstadoSolicitudCSIRT) WHERE EstadoSolicitudCSIRT IS NOT NULL;
CREATE INDEX IDX_CSIRT_Log_Incidente ON CSIRT_SOLICITUDES_LOG(IncidenteID, FechaEvento);

-- 5. Vista para dashboard CSIRT
CREATE VIEW vw_SolicitudesCSIRT AS
SELECT 
    i.IncidenteID,
    i.IDVisible,
    i.Titulo,
    i.Criticidad,
    i.EstadoActual,
    i.FechaDeteccion,
    i.SolicitarAyudaCSIRT,
    i.FechaSolicitudCSIRT,
    i.TipoAyudaCSIRT,
    i.EstadoSolicitudCSIRT,
    i.ContactoCSIRT,
    e.RazonSocial as Empresa,
    e.Tipo_Empresa,
    DATEDIFF(HOUR, i.FechaSolicitudCSIRT, GETDATE()) as HorasDesdeSOlicitud
FROM Incidentes i
INNER JOIN Empresas e ON i.EmpresaID = e.EmpresaID
WHERE i.SolicitarAyudaCSIRT = 1;

PRINT '✅ Campos CSIRT agregados exitosamente a la tabla Incidentes';
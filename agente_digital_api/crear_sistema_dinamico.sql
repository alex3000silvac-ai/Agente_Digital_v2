-- ========================================
-- SISTEMA DINÁMICO DE INCIDENTES ANCI
-- ========================================
-- Diseño simple pero escalable para manejar:
-- - 6 secciones fijas del formulario
-- - 35 taxonomías dinámicas
-- - 6 comentarios por sección
-- - 10 archivos de 10MB por sección
-- ========================================

-- 1. TABLA PRINCIPAL DE INCIDENTES (ya existe, solo referencia)
-- La tabla Incidentes mantiene los datos básicos

-- 2. TABLA DE CONFIGURACIÓN DE SECCIONES
-- Define las 41 secciones (6 fijas + 35 taxonomías)
CREATE TABLE IF NOT EXISTS ANCI_SECCIONES_CONFIG (
    SeccionID INT PRIMARY KEY IDENTITY(1,1),
    CodigoSeccion NVARCHAR(50) NOT NULL UNIQUE,  -- 'SEC_1', 'SEC_2', ..., 'TAX_1', 'TAX_2', etc
    TipoSeccion NVARCHAR(20) NOT NULL,            -- 'FIJA' o 'TAXONOMIA'
    NumeroOrden INT NOT NULL,                     -- Orden de aparición (1-41)
    Titulo NVARCHAR(200) NOT NULL,                -- Título de la sección/taxonomía
    Descripcion NVARCHAR(MAX),                    -- Descripción detallada
    CamposJSON NVARCHAR(MAX),                     -- Definición de campos del formulario en JSON
    AplicaOIV BIT DEFAULT 1,                      -- Si aplica a empresas OIV
    AplicaPSE BIT DEFAULT 1,                      -- Si aplica a empresas PSE
    Activo BIT DEFAULT 1,                         -- Si la sección está activa
    ColorIndicador NVARCHAR(20) DEFAULT '#28a745', -- Color cuando tiene datos
    IconoSeccion NVARCHAR(50),                   -- Icono para el acordeón
    MaxComentarios INT DEFAULT 6,                 -- Máximo de comentarios permitidos
    MaxArchivos INT DEFAULT 10,                   -- Máximo de archivos permitidos
    MaxSizeMB INT DEFAULT 10,                     -- Tamaño máximo por archivo en MB
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FechaActualizacion DATETIME DEFAULT GETDATE()
);

-- 3. TABLA DE DATOS DE INCIDENTES POR SECCIÓN
-- Almacena todos los datos de todas las secciones para cada incidente
CREATE TABLE IF NOT EXISTS INCIDENTES_SECCIONES_DATOS (
    DatoID INT PRIMARY KEY IDENTITY(1,1),
    IncidenteID INT NOT NULL,
    SeccionID INT NOT NULL,
    DatosJSON NVARCHAR(MAX),                      -- Todos los datos del formulario en JSON
    EstadoSeccion NVARCHAR(20) DEFAULT 'VACIO',  -- 'VACIO', 'PARCIAL', 'COMPLETO'
    PorcentajeCompletado INT DEFAULT 0,           -- 0-100 del llenado de la sección
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FechaActualizacion DATETIME DEFAULT GETDATE(),
    ActualizadoPor NVARCHAR(100),
    FOREIGN KEY (IncidenteID) REFERENCES Incidentes(IncidenteID),
    FOREIGN KEY (SeccionID) REFERENCES ANCI_SECCIONES_CONFIG(SeccionID),
    UNIQUE(IncidenteID, SeccionID)               -- Un registro por incidente-sección
);

-- 4. TABLA DE COMENTARIOS POR SECCIÓN
-- Hasta 6 comentarios por sección
CREATE TABLE IF NOT EXISTS INCIDENTES_COMENTARIOS (
    ComentarioID INT PRIMARY KEY IDENTITY(1,1),
    IncidenteID INT NOT NULL,
    SeccionID INT NOT NULL,
    NumeroComentario INT NOT NULL,                -- 1-6
    Comentario NVARCHAR(MAX) NOT NULL,
    TipoComentario NVARCHAR(50),                 -- 'GENERAL', 'EVIDENCIA', 'ACLARACION', etc
    FechaCreacion DATETIME DEFAULT GETDATE(),
    CreadoPor NVARCHAR(100),
    Activo BIT DEFAULT 1,
    FOREIGN KEY (IncidenteID) REFERENCES Incidentes(IncidenteID),
    FOREIGN KEY (SeccionID) REFERENCES ANCI_SECCIONES_CONFIG(SeccionID),
    CONSTRAINT CHK_NumComentario CHECK (NumeroComentario BETWEEN 1 AND 6)
);

-- 5. TABLA DE ARCHIVOS POR SECCIÓN
-- Hasta 10 archivos por sección
CREATE TABLE IF NOT EXISTS INCIDENTES_ARCHIVOS (
    ArchivoID INT PRIMARY KEY IDENTITY(1,1),
    IncidenteID INT NOT NULL,
    SeccionID INT NOT NULL,
    NumeroArchivo INT NOT NULL,                   -- 1-10
    NombreOriginal NVARCHAR(255) NOT NULL,        
    NombreServidor NVARCHAR(255) NOT NULL UNIQUE, -- Nombre único en servidor
    RutaArchivo NVARCHAR(500) NOT NULL,
    TipoArchivo NVARCHAR(50),
    TamanoKB INT NOT NULL,
    HashArchivo NVARCHAR(64),                     -- SHA256 del archivo
    Descripcion NVARCHAR(500),
    FechaSubida DATETIME DEFAULT GETDATE(),
    SubidoPor NVARCHAR(100),
    Activo BIT DEFAULT 1,                         -- Para soft delete
    FOREIGN KEY (IncidenteID) REFERENCES Incidentes(IncidenteID),
    FOREIGN KEY (SeccionID) REFERENCES ANCI_SECCIONES_CONFIG(SeccionID),
    CONSTRAINT CHK_NumArchivo CHECK (NumeroArchivo BETWEEN 1 AND 10)
);

-- 6. TABLA DE AUDITORÍA
-- Registra todos los cambios
CREATE TABLE IF NOT EXISTS INCIDENTES_AUDITORIA (
    AuditoriaID INT PRIMARY KEY IDENTITY(1,1),
    IncidenteID INT NOT NULL,
    SeccionID INT,
    TipoAccion NVARCHAR(50) NOT NULL,            -- 'CREAR', 'EDITAR', 'ELIMINAR', 'ARCHIVO_SUBIR', etc
    TablaAfectada NVARCHAR(50),
    RegistroID INT,
    DatosAnteriores NVARCHAR(MAX),               -- JSON con datos anteriores
    DatosNuevos NVARCHAR(MAX),                   -- JSON con datos nuevos
    Usuario NVARCHAR(100),
    DireccionIP NVARCHAR(50),
    UserAgent NVARCHAR(500),
    FechaAccion DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (IncidenteID) REFERENCES Incidentes(IncidenteID)
);

-- 7. ÍNDICES PARA OPTIMIZACIÓN
CREATE INDEX IDX_Secciones_Tipo ON ANCI_SECCIONES_CONFIG(TipoSeccion);
CREATE INDEX IDX_Secciones_Activo ON ANCI_SECCIONES_CONFIG(Activo);
CREATE INDEX IDX_Datos_Incidente ON INCIDENTES_SECCIONES_DATOS(IncidenteID);
CREATE INDEX IDX_Datos_Estado ON INCIDENTES_SECCIONES_DATOS(EstadoSeccion);
CREATE INDEX IDX_Comentarios_Incidente ON INCIDENTES_COMENTARIOS(IncidenteID, SeccionID);
CREATE INDEX IDX_Archivos_Incidente ON INCIDENTES_ARCHIVOS(IncidenteID, SeccionID);
CREATE INDEX IDX_Archivos_Activo ON INCIDENTES_ARCHIVOS(Activo);
CREATE INDEX IDX_Auditoria_Incidente ON INCIDENTES_AUDITORIA(IncidenteID, FechaAccion);

-- 8. INSERTAR LAS 6 SECCIONES FIJAS
INSERT INTO ANCI_SECCIONES_CONFIG (CodigoSeccion, TipoSeccion, NumeroOrden, Titulo, Descripcion, CamposJSON, IconoSeccion)
VALUES 
('SEC_1', 'FIJA', 1, 'Información General', 'Datos básicos del incidente', 
 '{"campos": ["titulo", "fecha_deteccion", "fecha_ocurrencia", "origen", "criticidad"]}', 'info-circle'),

('SEC_2', 'FIJA', 2, 'Descripción del Incidente', 'Descripción detallada del incidente', 
 '{"campos": ["descripcion_detallada", "sistemas_afectados", "servicios_interrumpidos"]}', 'file-text'),

('SEC_3', 'FIJA', 3, 'Análisis del Incidente', 'Análisis técnico y de impacto', 
 '{"campos": ["analisis_tecnico", "impacto_preliminar", "alcance_geografico"]}', 'search'),

('SEC_4', 'FIJA', 4, 'Acciones Inmediatas', 'Medidas tomadas inmediatamente', 
 '{"campos": ["acciones_inmediatas", "responsable_cliente", "medidas_contencion"]}', 'shield'),

('SEC_5', 'FIJA', 5, 'Análisis Final', 'Análisis de causa raíz y lecciones', 
 '{"campos": ["causa_raiz", "lecciones_aprendidas", "plan_mejora"]}', 'check-circle'),

('SEC_6', 'FIJA', 6, 'Información ANCI', 'Datos específicos para reporte ANCI', 
 '{"campos": ["reporte_anci_id", "fecha_declaracion_anci", "tipo_amenaza"]}', 'file-shield');

-- 9. PROCEDIMIENTO PARA CARGAR TAXONOMÍAS DESDE LA TABLA EXISTENTE
-- Este procedimiento carga las 35 taxonomías como secciones
CREATE PROCEDURE sp_CargarTaxonomiasComoSecciones
AS
BEGIN
    DECLARE @contador INT = 7;  -- Empezamos después de las 6 secciones fijas
    
    INSERT INTO ANCI_SECCIONES_CONFIG (
        CodigoSeccion, TipoSeccion, NumeroOrden, Titulo, 
        Descripcion, AplicaOIV, AplicaPSE, IconoSeccion
    )
    SELECT TOP 35
        'TAX_' + CAST(ROW_NUMBER() OVER (ORDER BY Id_Incidente) AS NVARCHAR(10)),
        'TAXONOMIA',
        @contador + ROW_NUMBER() OVER (ORDER BY Id_Incidente),
        CONCAT(Area, ' - ', Efecto),
        CONCAT('Categoría: ', Categoria_del_Incidente, ' | Subcategoría: ', Subcategoria_del_Incidente),
        CASE WHEN Tipo_Empresa IN ('OIV', 'AMBAS') THEN 1 ELSE 0 END,
        CASE WHEN Tipo_Empresa IN ('PSE', 'AMBAS') THEN 1 ELSE 0 END,
        'tag'
    FROM TAXONOMIA_INCIDENTES
    WHERE Activo = 1
    ORDER BY Id_Incidente;
END;

-- 10. VISTA PARA FACILITAR CONSULTAS
CREATE VIEW vw_IncidentesSeccionesCompletas AS
SELECT 
    i.IncidenteID,
    i.IDVisible,
    i.Titulo AS TituloIncidente,
    i.EmpresaID,
    sc.SeccionID,
    sc.CodigoSeccion,
    sc.TipoSeccion,
    sc.NumeroOrden,
    sc.Titulo AS TituloSeccion,
    sd.DatosJSON,
    sd.EstadoSeccion,
    sd.PorcentajeCompletado,
    (SELECT COUNT(*) FROM INCIDENTES_COMENTARIOS WHERE IncidenteID = i.IncidenteID AND SeccionID = sc.SeccionID AND Activo = 1) AS TotalComentarios,
    (SELECT COUNT(*) FROM INCIDENTES_ARCHIVOS WHERE IncidenteID = i.IncidenteID AND SeccionID = sc.SeccionID AND Activo = 1) AS TotalArchivos
FROM Incidentes i
CROSS JOIN ANCI_SECCIONES_CONFIG sc
LEFT JOIN INCIDENTES_SECCIONES_DATOS sd ON i.IncidenteID = sd.IncidenteID AND sc.SeccionID = sd.SeccionID
WHERE sc.Activo = 1;

-- 11. FUNCIÓN PARA VERIFICAR LÍMITES
CREATE FUNCTION fn_VerificarLimites
(
    @IncidenteID INT,
    @SeccionID INT,
    @TipoElemento NVARCHAR(20)  -- 'COMENTARIO' o 'ARCHIVO'
)
RETURNS BIT
AS
BEGIN
    DECLARE @resultado BIT = 0;
    DECLARE @maxPermitido INT;
    DECLARE @actualCount INT;
    
    IF @TipoElemento = 'COMENTARIO'
    BEGIN
        SELECT @maxPermitido = MaxComentarios FROM ANCI_SECCIONES_CONFIG WHERE SeccionID = @SeccionID;
        SELECT @actualCount = COUNT(*) FROM INCIDENTES_COMENTARIOS 
        WHERE IncidenteID = @IncidenteID AND SeccionID = @SeccionID AND Activo = 1;
    END
    ELSE IF @TipoElemento = 'ARCHIVO'
    BEGIN
        SELECT @maxPermitido = MaxArchivos FROM ANCI_SECCIONES_CONFIG WHERE SeccionID = @SeccionID;
        SELECT @actualCount = COUNT(*) FROM INCIDENTES_ARCHIVOS 
        WHERE IncidenteID = @IncidenteID AND SeccionID = @SeccionID AND Activo = 1;
    END
    
    IF @actualCount < @maxPermitido
        SET @resultado = 1;
        
    RETURN @resultado;
END;
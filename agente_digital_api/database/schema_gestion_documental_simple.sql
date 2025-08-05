-- Tabla simplificada para Gestión Documental
-- Solo almacena archivos con comentarios por carpeta

CREATE TABLE DOCUMENTOS_GESTION (
    DocumentoID INT IDENTITY(1,1) PRIMARY KEY,
    EmpresaID INT NOT NULL,
    CarpetaID INT NOT NULL,         -- 1-12 según las carpetas
    SubcarpetaID INT NULL,          -- Para subcarpetas opcionales
    NombreArchivo NVARCHAR(255) NOT NULL,
    RutaArchivo NVARCHAR(500) NOT NULL,
    Extension NVARCHAR(10),
    Comentario NVARCHAR(MAX),
    FechaSubida DATETIME DEFAULT GETDATE(),
    FechaModificacion DATETIME NULL,
    FechaEliminacion DATETIME NULL,
    Activo BIT DEFAULT 1,
    CONSTRAINT FK_DocumentosGestion_Empresa FOREIGN KEY (EmpresaID) REFERENCES Empresas(EmpresaID),
    INDEX IX_DocumentosGestion_Empresa (EmpresaID),
    INDEX IX_DocumentosGestion_Carpeta (CarpetaID),
    INDEX IX_DocumentosGestion_Activo (Activo)
);

-- Vista para facilitar consultas
CREATE VIEW VW_DOCUMENTOS_GESTION AS
SELECT 
    d.DocumentoID,
    d.EmpresaID,
    e.RazonSocial,
    d.CarpetaID,
    d.SubcarpetaID,
    d.NombreArchivo,
    d.Extension,
    d.Comentario,
    d.FechaSubida,
    d.FechaModificacion,
    d.Activo
FROM DOCUMENTOS_GESTION d
INNER JOIN Empresas e ON d.EmpresaID = e.EmpresaID
WHERE d.Activo = 1;
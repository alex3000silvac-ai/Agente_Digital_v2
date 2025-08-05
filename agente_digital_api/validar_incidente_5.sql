-- =====================================================
-- VALIDACIÓN COMPLETA DEL INCIDENTE 5
-- =====================================================

DECLARE @IncidenteID INT = 5;

PRINT '=========================================='
PRINT 'VALIDACIÓN INCIDENTE ' + CAST(@IncidenteID AS VARCHAR)
PRINT '=========================================='
PRINT ''

-- 1. DATOS PRINCIPALES
PRINT '1. DATOS PRINCIPALES DEL INCIDENTE'
PRINT '------------------------------------------'

SELECT 
    'ID: ' + CAST(IncidenteID AS VARCHAR) AS Campo,
    Titulo,
    CONVERT(VARCHAR, FechaDeteccion, 120) AS FechaDeteccion,
    CONVERT(VARCHAR, FechaOcurrencia, 120) AS FechaOcurrencia,
    Criticidad,
    AlcanceGeografico,
    EstadoActual,
    IDVisible,
    CreadoPor,
    CONVERT(VARCHAR, FechaCreacion, 120) AS FechaCreacion
FROM Incidentes 
WHERE IncidenteID = @IncidenteID;

-- 2. CAMPOS DE TEXTO LARGO
PRINT ''
PRINT '2. CAMPOS DE TEXTO LARGO (caracteres)'
PRINT '------------------------------------------'

SELECT 
    'DescripcionInicial' as Campo,
    LEN(DescripcionInicial) as Longitud,
    LEFT(DescripcionInicial, 100) + '...' as Primeros100Chars
FROM Incidentes WHERE IncidenteID = @IncidenteID
UNION ALL
SELECT 
    'AnciImpactoPreliminar',
    LEN(AnciImpactoPreliminar),
    LEFT(AnciImpactoPreliminar, 100) + '...'
FROM Incidentes WHERE IncidenteID = @IncidenteID
UNION ALL
SELECT 
    'SistemasAfectados',
    LEN(SistemasAfectados),
    LEFT(SistemasAfectados, 100) + '...'
FROM Incidentes WHERE IncidenteID = @IncidenteID
UNION ALL
SELECT 
    'ServiciosInterrumpidos',
    LEN(ServiciosInterrumpidos),
    LEFT(ServiciosInterrumpidos, 100) + '...'
FROM Incidentes WHERE IncidenteID = @IncidenteID
UNION ALL
SELECT 
    'AccionesInmediatas',
    LEN(AccionesInmediatas),
    LEFT(AccionesInmediatas, 100) + '...'
FROM Incidentes WHERE IncidenteID = @IncidenteID
UNION ALL
SELECT 
    'CausaRaiz',
    LEN(CausaRaiz),
    LEFT(CausaRaiz, 100) + '...'
FROM Incidentes WHERE IncidenteID = @IncidenteID
UNION ALL
SELECT 
    'LeccionesAprendidas',
    LEN(LeccionesAprendidas),
    LEFT(LeccionesAprendidas, 100) + '...'
FROM Incidentes WHERE IncidenteID = @IncidenteID
UNION ALL
SELECT 
    'PlanMejora',
    LEN(PlanMejora),
    LEFT(PlanMejora, 100) + '...'
FROM Incidentes WHERE IncidenteID = @IncidenteID;

-- 3. TAXONOMÍAS ASOCIADAS
PRINT ''
PRINT '3. TAXONOMÍAS ASOCIADAS'
PRINT '------------------------------------------'

SELECT 
    it.Id_Taxonomia,
    t.nombre AS NombreTaxonomia,
    t.area,
    t.efecto,
    t.categoria,
    it.Comentarios,
    CONVERT(VARCHAR, it.FechaAsignacion, 120) AS FechaAsignacion
FROM INCIDENTE_TAXONOMIA it
LEFT JOIN Taxonomia_incidentes t ON it.Id_Taxonomia = t.id
WHERE it.IncidenteID = @IncidenteID;

-- Contar taxonomías
DECLARE @TotalTaxonomias INT;
SELECT @TotalTaxonomias = COUNT(*) 
FROM INCIDENTE_TAXONOMIA 
WHERE IncidenteID = @IncidenteID;

PRINT ''
PRINT 'Total taxonomías asociadas: ' + CAST(@TotalTaxonomias AS VARCHAR)

-- 4. VERIFICAR ARCHIVOS (si existe tabla)
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'INCIDENTE_ARCHIVOS')
BEGIN
    PRINT ''
    PRINT '4. ARCHIVOS EN BASE DE DATOS'
    PRINT '------------------------------------------'
    
    SELECT * FROM INCIDENTE_ARCHIVOS WHERE IncidenteID = @IncidenteID;
    
    DECLARE @TotalArchivos INT;
    SELECT @TotalArchivos = COUNT(*) 
    FROM INCIDENTE_ARCHIVOS 
    WHERE IncidenteID = @IncidenteID;
    
    PRINT 'Total archivos en BD: ' + CAST(@TotalArchivos AS VARCHAR)
END
ELSE
BEGIN
    PRINT ''
    PRINT '4. ARCHIVOS'
    PRINT '------------------------------------------'
    PRINT 'No existe tabla INCIDENTE_ARCHIVOS'
    PRINT 'Los archivos se almacenan solo en el filesystem'
END

-- 5. RESUMEN
PRINT ''
PRINT '=========================================='
PRINT 'RESUMEN DE VALIDACIÓN'
PRINT '=========================================='

DECLARE @Titulo VARCHAR(500), @IDVisible VARCHAR(100);
SELECT @Titulo = Titulo, @IDVisible = IDVisible 
FROM Incidentes 
WHERE IncidenteID = @IncidenteID;

IF @Titulo IS NOT NULL
    PRINT '✓ Incidente encontrado: ' + @Titulo
ELSE
    PRINT '✗ Incidente NO encontrado'

PRINT '✓ ID Visible (carpeta archivos): ' + ISNULL(@IDVisible, 'NO TIENE')
PRINT '✓ Total taxonomías: ' + CAST(@TotalTaxonomias AS VARCHAR)

-- 6. MOSTRAR TODOS LOS CAMPOS
PRINT ''
PRINT '6. TODOS LOS CAMPOS DEL INCIDENTE'
PRINT '------------------------------------------'

SELECT * FROM Incidentes WHERE IncidenteID = @IncidenteID;

-- 7. VERIFICACIÓN ESPECÍFICA PARA ARCHIVOS
PRINT ''
PRINT '7. CARPETA DE ARCHIVOS ESPERADA'
PRINT '------------------------------------------'
PRINT 'Los archivos deben estar en: /uploads/evidencias/' + ISNULL(@IDVisible, 'SIN_ID_VISIBLE')
PRINT 'Verificar manualmente:'
PRINT '  - 1 archivo por cada sección donde se subió'
PRINT '  - Archivos de taxonomías en carpeta separada'
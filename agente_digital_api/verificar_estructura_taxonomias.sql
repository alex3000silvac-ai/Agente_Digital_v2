-- Script para verificar la estructura de las tablas de taxonomías

-- 1. Verificar columnas de INCIDENTE_TAXONOMIA
SELECT 
    c.COLUMN_NAME,
    c.DATA_TYPE,
    c.CHARACTER_MAXIMUM_LENGTH,
    c.IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS c
WHERE c.TABLE_NAME = 'INCIDENTE_TAXONOMIA'
ORDER BY c.ORDINAL_POSITION;

-- 2. Ver algunos registros de ejemplo
SELECT TOP 5 * FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = 5;

-- 3. Verificar la tabla de taxonomías
SELECT 
    c.COLUMN_NAME,
    c.DATA_TYPE,
    c.CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS c
WHERE c.TABLE_NAME = 'Taxonomia_incidentes'
ORDER BY c.ORDINAL_POSITION;

-- 4. Contar registros para el incidente 5
SELECT 
    COUNT(*) as TotalTaxonomias 
FROM INCIDENTE_TAXONOMIA 
WHERE IncidenteID = 5;
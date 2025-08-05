# SOLUCIÓN: Taxonomías no se muestran marcadas en edición ANCI

## Problema Identificado
En la edición de incidentes ANCI, las taxonomías guardadas en la base de datos no se mostraban como seleccionadas (checkboxes no marcados) aunque los datos estaban correctamente almacenados.

## Causa Raíz
El problema estaba en el endpoint `/api/admin/incidentes/<id>` que tenía un error en la consulta SQL:

```sql
-- INCORRECTO (antes)
SELECT 
    it.Id_Taxonomia,
    ti.Id_Incidente as Nombre,  -- ❌ Esto devolvía un ID, no un nombre
    ...
```

La columna `ti.Id_Incidente` contiene el ID de la taxonomía (ej: 'INC_CONF_EXCF_FCRA'), no el nombre descriptivo. Esto causaba que el campo `nombre` en el JSON contenga un ID duplicado.

## Solución Implementada

### 1. Corrección del Query SQL
Se modificó el archivo `/app/modules/admin/incidentes_admin_endpoints.py`:

```sql
-- CORRECTO (ahora)
SELECT 
    it.Id_Taxonomia,
    COALESCE(ti.Categoria_del_Incidente + ' - ' + ti.Subcategoria_del_Incidente, 
             ti.Categoria_del_Incidente) as Nombre,  -- ✅ Ahora devuelve el nombre real
    ...
```

### 2. Verificación de Estructura de BD
Se confirmó que la tabla `Taxonomia_incidentes` tiene las siguientes columnas:
- `Id_Incidente` (el ID único)
- `Categoria_del_Incidente` 
- `Subcategoria_del_Incidente`
- `Area`, `Efecto`, `Descripcion`, etc.

### 3. Frontend ya está preparado
El componente `AcordeonIncidenteANCI.vue` ya tiene la normalización correcta:

```javascript
// Función que compara taxonomías normalizando IDs a string
function taxonomiaSeleccionada(taxId) {
  const idStr = String(taxId)
  return taxonomiasSeleccionadas.value.some(t => String(t.id) === idStr)
}
```

## Scripts de Verificación Creados

1. **verificar_columnas_taxonomia.py** - Verifica estructura de tabla Taxonomia_incidentes
2. **verificar_columnas_incidente_taxonomia.py** - Verifica estructura de INCIDENTE_TAXONOMIA
3. **simular_endpoint_taxonomias.py** - Simula la respuesta del endpoint
4. **debug_taxonomias_frontend.js** - Debug para ejecutar en el navegador

## Resultado Esperado

Ahora cuando se edite un incidente ANCI:

1. ✅ Las taxonomías guardadas se mostrarán con sus checkboxes marcados
2. ✅ Los nombres de las taxonomías se mostrarán correctamente (no IDs)
3. ✅ Los comentarios/justificaciones se cargarán apropiadamente
4. ✅ Los archivos asociados a cada taxonomía se mostrarán

## Pasos para Verificar

1. Reiniciar el servidor Flask para aplicar los cambios
2. Abrir la edición de un incidente ANCI (ej: incidente ID 5)
3. Verificar que en la Sección 4 las taxonomías aparezcan marcadas
4. Si persiste el problema, ejecutar en la consola del navegador:
   ```javascript
   // Copiar y pegar el contenido de debug_taxonomias_frontend.js
   ```

## Estructura de Datos Correcta

El endpoint ahora devuelve:
```json
{
  "taxonomias_seleccionadas": [
    {
      "id": "INC_CONF_EXCF_FCRA",
      "nombre": "Filtración de configuraciones en rutas de aplicación - Exfiltración y/o exposición de configuraciones",
      "area": "Impacto en la confidencialidad de la información",
      "categoria": "Filtración de configuraciones en rutas de aplicación",
      "subcategoria": "Exfiltración y/o exposición de configuraciones",
      "justificacion": "Esta taxonomía aplica porque...",
      ...
    }
  ]
}
```

## Archivos Modificados
- `/app/modules/admin/incidentes_admin_endpoints.py` (línea 174)
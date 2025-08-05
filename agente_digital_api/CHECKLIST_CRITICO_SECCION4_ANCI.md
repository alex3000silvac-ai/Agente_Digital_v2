# CHECKLIST CRÍTICO - Sección 4 (Taxonomía) en Incidentes ANCI

## 🚨 PROBLEMA IDENTIFICADO
La Sección 4 de taxonomías no funciona correctamente cuando un incidente se declara como ANCI:
- No se visualizan taxonomías seleccionadas con color distintivo
- No aparecen comentarios asociados
- No se muestran archivos adjuntos
- Faltan botones de edición

## ✅ CHECKLIST DE DIAGNÓSTICO

### 1. VERIFICACIÓN DE DATOS EN BASE DE DATOS
```sql
-- Verificar si las taxonomías están guardadas
SELECT 
    it.ID,
    it.IncidenteID,
    it.Id_Taxonomia,
    it.Comentarios,
    it.FechaAsignacion,
    i.ReporteAnciID,
    i.TieneReporteANCI
FROM INCIDENTE_TAXONOMIA it
INNER JOIN INCIDENTES i ON it.IncidenteID = i.IncidenteID
WHERE i.ReporteAnciID IS NOT NULL OR i.TieneReporteANCI = 1
ORDER BY it.IncidenteID DESC;

-- Verificar archivos de taxonomías
SELECT 
    et.*,
    it.Id_Taxonomia
FROM EVIDENCIAS_TAXONOMIA et
INNER JOIN INCIDENTE_TAXONOMIA it ON et.IncidenteTaxonomiaID = it.ID
WHERE et.IncidenteID IN (
    SELECT IncidenteID 
    FROM INCIDENTES 
    WHERE ReporteAnciID IS NOT NULL
);
```

### 2. VERIFICACIÓN DE ENDPOINT BACKEND
```python
# Archivo: /app/modules/admin/incidentes_admin_endpoints.py
# Verificar que el endpoint incluya:
- taxonomias_seleccionadas con todos sus campos
- archivos asociados a cada taxonomía
- comentarios/justificaciones
```

### 3. VERIFICACIÓN DE COMPONENTE FRONTEND
```javascript
// Archivo: /src/components/AcordeonIncidenteANCI.vue
// Verificar:
- Función taxonomiaSeleccionada()
- Carga de taxonomiasSeleccionadas en onMounted
- Renderizado de comentarios y archivos
- Clases CSS para color distintivo
```

### 4. VERIFICACIÓN DE FLUJO DE DATOS
```javascript
// En la consola del navegador:
// 1. Verificar datos iniciales
console.log(window.debugTaxonomias?.seleccionadas);

// 2. Verificar función de comparación
const comp = document.querySelector('.acordeon-incidente-anci')?.__vueParentComponent;
console.log(comp?.ctx?.taxonomiaSeleccionada('ID_TAXONOMIA'));

// 3. Verificar clases CSS aplicadas
document.querySelectorAll('.taxonomia-seleccionada');
```

## 🔧 SOLUCIÓN UNIVERSAL PROPUESTA

### PASO 1: Crear Script de Diagnóstico Automático
```python
# diagnosticar_seccion4_anci.py
```

### PASO 2: Patch Universal para Frontend
```javascript
// fix_taxonomias_anci_universal.js
```

### PASO 3: Actualización de Endpoint Backend
```python
# Asegurar que devuelva estructura completa
```

### PASO 4: CSS para Destacar Taxonomías
```css
/* Estilos que faltan para destacar */
.taxonomia-item.seleccionada {
    background-color: #e3f2fd;
    border-left: 4px solid #2196f3;
}
```

## 📋 LISTA DE VERIFICACIÓN RÁPIDA

### Frontend:
- [ ] ¿Se cargan las taxonomías seleccionadas en `onMounted`?
- [ ] ¿La función `taxonomiaSeleccionada()` compara IDs correctamente?
- [ ] ¿Existen las clases CSS para destacar?
- [ ] ¿Se renderizan los comentarios en el template?
- [ ] ¿Se muestran los archivos adjuntos?
- [ ] ¿Están los botones de edición en el template?

### Backend:
- [ ] ¿El endpoint devuelve `taxonomias_seleccionadas`?
- [ ] ¿Incluye los comentarios/justificaciones?
- [ ] ¿Incluye los archivos asociados?
- [ ] ¿Los IDs son del tipo correcto (string/number)?

### Base de Datos:
- [ ] ¿Existen registros en INCIDENTE_TAXONOMIA?
- [ ] ¿Los comentarios están guardados?
- [ ] ¿Hay archivos en EVIDENCIAS_TAXONOMIA?

## 🚀 APLICACIÓN INMEDIATA

Ejecutar en orden:
1. Script de diagnóstico
2. Aplicar fix universal
3. Verificar en navegador
4. Confirmar funcionamiento
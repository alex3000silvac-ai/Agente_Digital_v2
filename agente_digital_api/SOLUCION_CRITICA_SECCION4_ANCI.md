# SOLUCIÓN CRÍTICA - Sección 4 (Taxonomías) en Incidentes ANCI

## 🎯 PROBLEMA IDENTIFICADO
La Sección 4 no muestra correctamente las taxonomías seleccionadas en incidentes ANCI:
- No se destacan visualmente (falta color distintivo)
- Los comentarios/justificaciones no se visualizan
- Los archivos adjuntos no aparecen
- Faltan botones de edición

## 🔍 CAUSA RAÍZ
Discrepancia entre clases CSS en el template y los estilos definidos:
- Template usa: `:class="{ 'taxonomia-seleccionada': taxonomiaSeleccionada(tax.id) }"`
- CSS busca: `.taxonomia-item.seleccionada`

## ✅ SOLUCIÓN INMEDIATA

### OPCIÓN 1: Fix JavaScript (Ejecutar en consola del navegador)
```javascript
// Copiar y pegar el contenido de fix_taxonomias_anci_universal.js
```

### OPCIÓN 2: Modificación directa del componente

#### 1. Corregir la clase CSS en el template
En `AcordeonIncidenteANCI.vue`, línea 419, cambiar:
```vue
<!-- ANTES -->
:class="{ 'taxonomia-seleccionada': taxonomiaSeleccionada(tax.id) }"

<!-- DESPUÉS -->
:class="{ 'seleccionada': taxonomiaSeleccionada(tax.id) }"
```

#### 2. O alternativamente, agregar el estilo CSS correcto
Agregar en la sección `<style>`:
```css
.taxonomia-seleccionada {
  background: linear-gradient(145deg, #2563eb, #1d4ed8) !important;
  box-shadow: 
    0 10px 30px rgba(37, 99, 235, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
  border-left: 4px solid #3b82f6 !important;
  padding-left: 16px !important;
}

.taxonomia-seleccionada .taxonomia-header {
  color: white !important;
  font-weight: 600 !important;
}

.taxonomia-seleccionada input[type="checkbox"] {
  accent-color: #60a5fa !important;
}
```

## 🔧 SOLUCIÓN PERMANENTE

### Backend - Verificar endpoint
El endpoint debe devolver la estructura completa:
```json
{
  "taxonomias_seleccionadas": [
    {
      "id": "INC_CONF_EXCF_FCRA",
      "nombre": "Categoría - Subcategoría",
      "justificacion": "Por qué fue seleccionada...",
      "descripcionProblema": "Descripción del problema...",
      "archivos": [
        {
          "id": "123",
          "nombre": "evidencia.pdf",
          "url": "/api/archivo/123"
        }
      ]
    }
  ]
}
```

### Frontend - Verificaciones necesarias
1. **Normalización de IDs**: ✅ Ya implementada
2. **Función obtenerTaxonomiaSeleccionada**: ✅ Correcta
3. **Renderizado condicional**: ✅ Implementado
4. **Estilos CSS**: ❌ Requiere corrección

## 📋 CHECKLIST DE VERIFICACIÓN

### Antes de aplicar la solución:
- [ ] Verificar que el incidente es ANCI (ReporteAnciID no es null)
- [ ] Confirmar que hay taxonomías guardadas en BD
- [ ] Verificar que el endpoint devuelve las taxonomías

### Después de aplicar la solución:
- [ ] Las taxonomías seleccionadas se muestran con fondo azul
- [ ] Los comentarios/justificaciones son visibles
- [ ] Los archivos adjuntos aparecen listados
- [ ] Los botones de edición están presentes

## 🚀 APLICACIÓN RÁPIDA

1. **Diagnóstico**:
   ```bash
   python3 diagnosticar_seccion4_anci.py
   ```

2. **Fix temporal** (en navegador):
   ```javascript
   // Copiar contenido de fix_taxonomias_anci_universal.js
   ```

3. **Fix permanente**:
   - Modificar el componente Vue según las instrucciones
   - O agregar los estilos CSS faltantes

## 💡 SOLUCIÓN UNIVERSAL PARA TODOS LOS CLIENTES

Para aplicar a todos los clientes sin modificar código:

1. **Crear archivo CSS global**:
   ```css
   /* anci-taxonomias-fix.css */
   .taxonomia-seleccionada,
   .taxonomia-item.seleccionada {
     background: #e3f2fd !important;
     border-left: 4px solid #2196f3 !important;
   }
   ```

2. **Incluir en el index.html**:
   ```html
   <link rel="stylesheet" href="/css/anci-taxonomias-fix.css">
   ```

## 📊 RESULTADO ESPERADO

### Antes (❌):
- Taxonomías sin destacar
- Sin comentarios visibles
- Sin archivos
- Sin botones

### Después (✅):
- Taxonomías con fondo azul distintivo
- Comentarios y justificaciones visibles
- Lista de archivos adjuntos
- Botones de edición funcionales

## 🆘 SOPORTE

Si el problema persiste:
1. Ejecutar diagnóstico completo
2. Revisar logs del navegador
3. Verificar permisos del usuario
4. Confirmar versión del componente
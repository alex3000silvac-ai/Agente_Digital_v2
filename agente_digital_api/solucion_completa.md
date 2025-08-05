# 🔧 SOLUCIÓN COMPLETA PARA LOS PROBLEMAS DEL CHECKLIST

## 📋 Problemas Identificados:

1. **Archivos no se muestran en ninguna sección**
2. **Comentarios/justificaciones de taxonomías no se cargan (sección 4)**
3. **Botones de edición de archivos no aparecen**

## 🎯 Pasos de Solución:

### 1. VERIFICAR EN EL NAVEGADOR (F12 - Consola)

Ejecuta este código en la consola:

```javascript
// Paso 1: Verificar el componente
const comp = document.querySelector('.acordeon-incidente-mejorado')?.__vueParentComponent;
console.log('Componente encontrado:', !!comp);
console.log('Modo:', comp?.props?.modo);
console.log('IncidenteId:', comp?.props?.incidenteId);

// Paso 2: Ver qué datos tiene cargados
console.log('\nDATOS ACTUALES:');
console.log('Archivos S2:', comp?.ctx?.archivosSeccion2?.value?.length || 0);
console.log('Archivos S3:', comp?.ctx?.archivosSeccion3?.value?.length || 0);
console.log('Taxonomías:', comp?.ctx?.taxonomiasSeleccionadas?.value?.length || 0);

// Paso 3: Forzar recarga
if (comp?.ctx?.cargarIncidenteExistente) {
    console.log('\nRecargando datos...');
    comp.ctx.cargarIncidenteExistente();
}
```

### 2. SI NO SE CARGAN LOS DATOS

El problema está en que `cargarIncidenteExistente` espera una estructura específica. Ejecuta:

```javascript
// Verificar qué devuelve el backend
fetch('http://localhost:5000/api/admin/incidentes/5', {
    headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
})
.then(r => r.json())
.then(data => {
    console.log('Backend devuelve:');
    console.log('- formData:', !!data.formData);
    console.log('- archivos:', data.archivos);
    console.log('- taxonomias_seleccionadas:', data.taxonomias_seleccionadas?.length);
    window.backendData = data;
});
```

### 3. SOLUCIÓN RÁPIDA (Parche temporal)

Si los datos vienen del backend pero no se cargan, ejecuta:

```javascript
// Cargar datos manualmente
const comp = document.querySelector('.acordeon-incidente-mejorado').__vueParentComponent;
const data = window.backendData; // Datos del paso anterior

if (data && comp) {
    // Cargar archivos
    if (data.archivos) {
        comp.ctx.archivosSeccion2.value = data.archivos.seccion_2 || [];
        comp.ctx.archivosSeccion3.value = data.archivos.seccion_3 || [];
        comp.ctx.archivosSeccion5.value = data.archivos.seccion_5 || [];
        comp.ctx.archivosSeccion6.value = data.archivos.seccion_6 || [];
        console.log('✅ Archivos cargados manualmente');
    }
    
    // Cargar taxonomías
    if (data.taxonomias_seleccionadas) {
        comp.ctx.taxonomiasSeleccionadas.value = data.taxonomias_seleccionadas;
        console.log('✅ Taxonomías cargadas manualmente');
    }
    
    // Forzar actualización
    comp.proxy.$forceUpdate();
}
```

## 🔍 Verificación de Botones

Los botones de gestión YA EXISTEN en el componente `GestorArchivosSeccion`:
- **Ver archivo** (ojo) 
- **Eliminar archivo** (papelera)
- **Editar descripción**: Campo de texto directo
- **Editar comentario**: Textarea directo

Si no los ves, es porque no hay archivos cargados.

## 🚨 SOLUCIÓN PERMANENTE

El problema real está en la línea 2133 de `AcordeonIncidenteMejorado.vue`:

```javascript
// PROBLEMA: Espera datos.formData
if (datos.formData) {
    formData.value = { ...datos.formData }
}
```

Pero el backend NO envía `formData`, envía los campos directamente. La solución ya está implementada en las líneas siguientes con el mapeo directo.

## 📝 VERIFICACIÓN FINAL

Después de aplicar las soluciones, verifica:

1. **Archivos**: Deben aparecer en cada sección con sus botones
2. **Taxonomías**: Deben mostrar las justificaciones en los textareas
3. **Sección 7**: Debe mostrar el resumen de todos los archivos

Si aún no funciona, el problema puede ser:
- Token JWT expirado (hacer login de nuevo)
- CORS bloqueando las peticiones
- El componente está en modo 'crear' en lugar de 'editar'
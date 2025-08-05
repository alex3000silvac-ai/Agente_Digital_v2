# 🎯 SOLUCIÓN SIMPLE Y EFECTIVA

## Problema Identificado:
El componente AcordeonIncidenteMejorado en modo 'editar' ignora los `datosIniciales` y trata de cargar desde el servidor con `cargarIncidenteExistente()`, pero esta función no está procesando bien los datos.

## Solución Temporal (Ejecutar en consola):

```javascript
// PASO 1: Obtener el componente padre (VistaDetalleIncidente)
const vistaDetalle = document.querySelector('#app').__vue__.$children[0].$children.find(c => c.$options.name === 'VistaDetalleIncidente' || c.$el.className?.includes('vista-normal'));

// PASO 2: Obtener los datos que ya están cargados
const datosParaEdicion = vistaDetalle?.datosParaEdicion || vistaDetalle?.$data?.datosParaEdicion;
const incidente = vistaDetalle?.incidente || vistaDetalle?.$data?.incidente;

console.log('Datos disponibles:', {
    tieneDataParaEdicion: !!datosParaEdicion,
    tieneIncidente: !!incidente,
    archivos: incidente?.archivos,
    taxonomias: incidente?.taxonomias_seleccionadas
});

// PASO 3: Forzar al componente hijo a usar estos datos
const acordeon = document.querySelector('.acordeon-incidente-mejorado')?.__vueParentComponent;

if (acordeon && incidente) {
    // Cargar campos del formulario
    if (datosParaEdicion) {
        Object.keys(datosParaEdicion).forEach(key => {
            if (acordeon.ctx.formData.value.hasOwnProperty(key)) {
                acordeon.ctx.formData.value[key] = datosParaEdicion[key];
            }
        });
        console.log('✅ Campos del formulario cargados');
    }
    
    // Cargar archivos
    if (incidente.archivos) {
        // Intentar con diferentes formatos de clave
        acordeon.ctx.archivosSeccion2.value = incidente.archivos.seccion_2 || incidente.archivos['2'] || [];
        acordeon.ctx.archivosSeccion3.value = incidente.archivos.seccion_3 || incidente.archivos['3'] || [];
        acordeon.ctx.archivosSeccion5.value = incidente.archivos.seccion_5 || incidente.archivos['5'] || [];
        acordeon.ctx.archivosSeccion6.value = incidente.archivos.seccion_6 || incidente.archivos['6'] || [];
        
        console.log('✅ Archivos cargados:', {
            seccion2: acordeon.ctx.archivosSeccion2.value.length,
            seccion3: acordeon.ctx.archivosSeccion3.value.length,
            seccion5: acordeon.ctx.archivosSeccion5.value.length,
            seccion6: acordeon.ctx.archivosSeccion6.value.length
        });
    }
    
    // Cargar taxonomías
    if (incidente.taxonomias_seleccionadas && incidente.taxonomias_seleccionadas.length > 0) {
        acordeon.ctx.taxonomiasSeleccionadas.value = incidente.taxonomias_seleccionadas;
        console.log('✅ Taxonomías cargadas:', acordeon.ctx.taxonomiasSeleccionadas.value.length);
    }
    
    // Forzar actualización
    acordeon.proxy.$forceUpdate();
    
    // Abrir secciones relevantes
    [2, 3, 4, 5, 6, 7].forEach(seccion => {
        if (acordeon.ctx.seccionesAbiertas?.value) {
            acordeon.ctx.seccionesAbiertas.value[seccion] = true;
        }
    });
    
    console.log('\n✅ DATOS CARGADOS EXITOSAMENTE');
} else {
    console.error('❌ No se pudo obtener el componente o los datos');
}
```

## Solución Permanente Propuesta:

En lugar de modificar la lógica compleja de `cargarIncidenteExistente()`, podemos hacer que el componente use los datos que YA vienen preparados desde el padre.

### Opción 1: Modificar VistaDetalleIncidente.vue
Cambiar la línea donde pasa `datos-iniciales` para que también funcione en modo editar:

```vue
<AcordeonIncidenteMejorado
  :modo="'editar'"
  :datos-iniciales="datosCompletos"  <!-- Pasar todos los datos -->
  @incidente-guardado="guardarCambios"
/>
```

### Opción 2: Crear un flag para forzar uso de datos iniciales
Agregar una prop `usar-datos-iniciales` que fuerce al componente a usar los datos iniciales incluso en modo editar.

### Opción 3: Simplificar cargarIncidenteExistente()
En lugar de hacer una petición nueva al servidor, usar los datos que ya están en el componente padre.

## Verificación:
Después de ejecutar el script, deberías ver:
1. Archivos en cada sección con botones de gestión
2. Taxonomías seleccionadas con sus justificaciones
3. Sección 7 con el resumen de todos los archivos
4. Campos del formulario llenos con los datos del incidente
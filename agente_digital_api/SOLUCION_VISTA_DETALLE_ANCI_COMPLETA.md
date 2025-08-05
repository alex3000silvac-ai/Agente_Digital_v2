# SOLUCIÓN COMPLETA - Vista Detalle Incidente ANCI

## 🎯 PROBLEMAS IDENTIFICADOS

En la vista `/incidente-detalle/5` se encontraron 3 problemas críticos:

1. **Expediente Semilla**: No muestra información actualizada
2. **Informe ANCI**: Los botones de exportación (PDF, Word, Texto) no funcionan
3. **Cuenta Regresiva**: No hay un reloj visible con el tiempo restante

## 🔍 ANÁLISIS TÉCNICO

### Componentes involucrados:
- **Vista principal**: `VistaDetalleIncidenteANCI.vue`
- **Sistema de 3 tarjetas**:
  - Tarjeta 1: Expediente Semilla
  - Tarjeta 2: Informe ANCI  
  - Tarjeta 3: Cuenta Regresiva

### Problemas específicos:

1. **Expediente Semilla**:
   - Los datos no se actualizan al abrir el modal
   - El componente `AcordeonIncidenteANCI` no recibe datos actualizados

2. **Exportación de Informes**:
   - Las funciones `exportarPDF`, `exportarWord` y `exportarTexto` están vacías
   - El endpoint existe en el backend pero no está implementado en el frontend

3. **Reloj de Cuenta Regresiva**:
   - Los plazos se calculan pero no se muestran visualmente
   - Falta un reloj en tiempo real que muestre el tiempo restante

## ✅ SOLUCIÓN IMPLEMENTADA

### Scripts creados:

1. **`fix_vista_detalle_anci_completo.js`**
   - Actualiza datos del expediente automáticamente
   - Implementa las funciones de exportación
   - Agrega un reloj flotante de cuenta regresiva
   - Muestra el tiempo en formato grande en la tarjeta

2. **`verificar_vista_detalle_anci.js`**
   - Verifica que todos los componentes funcionen
   - Comprueba datos, exportación y reloj
   - Proporciona un diagnóstico detallado

## 📋 INSTRUCCIONES DE USO

### Para aplicar la solución completa:

1. **Navegar al incidente ANCI**:
   ```
   http://localhost:5173/incidente-detalle/5
   ```

2. **Abrir la consola del navegador** (F12)

3. **Copiar y pegar**:
   ```javascript
   // Contenido completo de fix_vista_detalle_anci_completo.js
   ```

4. **Presionar Enter**

### Resultado esperado:

1. **Expediente Semilla** ✅
   - Datos actualizados automáticamente
   - Información sincronizada con la BD

2. **Botones de Exportación** ✅
   - **PDF**: Genera y descarga el informe en PDF
   - **Word**: Genera y descarga el informe en DOCX
   - **Texto**: Genera y descarga el informe en TXT

3. **Reloj de Cuenta Regresiva** ✅
   - Reloj flotante rojo en esquina superior derecha
   - Actualización cada segundo
   - Animación pulsante para urgencias
   - Tiempo grande visible en la tarjeta

## 🔧 DETALLES TÉCNICOS

### 1. Actualización de datos:
```javascript
// Fuerza la recarga desde el servidor
await ctx.cargarDatos();
```

### 2. Funciones de exportación:
```javascript
// Ejemplo: Exportar PDF
ctx.exportarPDF = async function() {
    const response = await fetch(`/api/informes-anci/generar/${incidenteId}`, {
        method: 'POST',
        body: JSON.stringify({ tipo: 'completo', formato: 'pdf' })
    });
    // Manejo de descarga...
}
```

### 3. Reloj en tiempo real:
```javascript
// Actualización cada segundo
setInterval(() => {
    ctx.calcularPlazos();
    actualizarReloj();
}, 1000);
```

## 🎨 CARACTERÍSTICAS DEL RELOJ

- **Posición fija**: Esquina superior derecha
- **Fondo rojo**: Con transparencia y blur
- **Animación**: Pulso suave continuo
- **Urgente**: Pulso rápido cuando queda poco tiempo
- **Información mostrada**:
  - Tipo de informe pendiente
  - Tiempo restante actualizado
  - Indicador visual con icono giratorio

## 📊 VERIFICACIÓN

Para verificar que todo funciona:

```javascript
// Copiar y pegar: verificar_vista_detalle_anci.js
```

Resultados esperados:
- ✅ Componente cargado
- ✅ Datos del expediente actualizados
- ✅ Funciones de exportación disponibles
- ✅ Reloj de cuenta regresiva visible

## 🚨 NOTAS IMPORTANTES

1. **El fix es temporal** - Se pierde al recargar la página
2. **El reloj consume recursos** - Para detenerlo: `clearInterval(window.relojIntervalANCI)`
3. **Las exportaciones requieren autenticación** - El token debe estar en localStorage
4. **Los plazos dependen del tipo de empresa**:
   - OIV: 24 horas para informe preliminar
   - PSE: 72 horas para informe preliminar
   - Ambos: 72 horas para informe completo

## 🛠️ SOLUCIÓN PERMANENTE

### Para el equipo de desarrollo:

1. **Actualizar `VistaDetalleIncidenteANCI.vue`**:
   - Implementar las funciones de exportación
   - Agregar el reloj como componente nativo
   - Mejorar la actualización de datos

2. **Crear componente `RelojCuentaRegresiva.vue`**:
   - Componente reutilizable
   - Con props para configuración
   - Estilos personalizables

3. **Mejorar endpoints de exportación**:
   - Soporte para múltiples formatos
   - Generación asíncrona para archivos grandes
   - Preview antes de descargar

## 🆘 SOPORTE

Si algún componente no funciona:
1. Verificar que el incidente tenga `ReporteAnciID`
2. Confirmar que el token de autenticación esté presente
3. Revisar la consola para errores específicos
4. Ejecutar el script de verificación

## 📝 ARCHIVOS RELACIONADOS

- Frontend: `/agente_digital_ui/src/views/VistaDetalleIncidenteANCI.vue`
- Backend: `/app/modules/informes_anci_views.py`
- Fix completo: `fix_vista_detalle_anci_completo.js`
- Verificación: `verificar_vista_detalle_anci.js`
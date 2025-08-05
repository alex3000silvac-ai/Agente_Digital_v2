# ✅ CAMBIOS IMPLEMENTADOS - PLAZOS ANCI CORREGIDOS

## RESUMEN DE CORRECCIONES REALIZADAS

### 1. ✅ **ALERTA TEMPRANA (3 HORAS)** - IMPLEMENTADA
- Agregada nueva etapa obligatoria para TODOS (OIV y PSE)
- Aparece primero en el timeline de plazos
- Incluida en las alertas de vencimiento

### 2. ✅ **INFORME FINAL CORREGIDO (15 DÍAS)**
- Cambiado de 30 días a **15 días**
- Actualizado en el cálculo de plazos (línea 496)
- Actualizado en la visualización (línea 246)

### 3. ✅ **PLAN DE ACCIÓN OIV (7 DÍAS)** - IMPLEMENTADO
- Nueva etapa exclusiva para OIV
- Se muestra solo cuando `TipoEmpresa === 'OIV'`
- Aparece entre Informe Completo e Informe Final

### 4. ⚠️ **PENDIENTE: Lógica condicional OIV**
- TODO: Implementar verificación de "servicio esencial afectado"
- Actualmente: OIV siempre usa 24h para preliminar
- Correcto: 24h solo si servicio esencial afectado, sino 72h

## CAMBIOS EN EL CÓDIGO

### Frontend - VistaDetalleIncidenteANCI.vue

```javascript
// Líneas 491-497 - Plazos actualizados
const plazosConfig = {
  alertaTemprana: 3,        // NUEVO: 3 horas para TODOS
  preliminar: incidente.value.TipoEmpresa === 'OIV' ? 24 : 72,
  completo: 72,
  planAccion: incidente.value.TipoEmpresa === 'OIV' ? 168 : null, // NUEVO: 7 días
  final: 360               // CORREGIDO: 15 días (era 30)
}

// Líneas 358-363 - Estado inicial actualizado
const plazos = ref({
  alertaTemprana: { completado: false, vencido: false, tiempoRestante: '' },
  preliminar: { completado: false, vencido: false, tiempoRestante: '' },
  completo: { completado: false, vencido: false, tiempoRestante: '' },
  planAccion: { completado: false, vencido: false, tiempoRestante: '' },
  final: { completado: false, vencido: false, tiempoRestante: '' }
})
```

### Visualización del Timeline

1. **Alerta Temprana** (líneas 194-207)
   - Primera en el timeline
   - 3 horas para todos

2. **Informe Preliminar** (líneas 209-223)
   - 24h OIV / 72h PSE

3. **Informe Completo** (líneas 225-237)
   - 72 horas para todos

4. **Plan de Acción** (líneas 240-253)
   - Solo visible para OIV
   - 7 días

5. **Informe Final** (líneas 255-267)
   - 15 días (corregido)

## VERIFICACIÓN DE FUNCIONAMIENTO

### Para PSE (como empresa Surtika):
✅ Alerta Temprana: 3 horas
✅ Informe Preliminar: 72 horas
✅ Informe Completo: 72 horas
❌ Plan de Acción: No aplica (correcto)
✅ Informe Final: 15 días

### Para OIV:
✅ Alerta Temprana: 3 horas
⚠️ Informe Preliminar: 24 horas (falta condicional)
✅ Informe Completo: 72 horas
✅ Plan de Acción: 7 días
✅ Informe Final: 15 días

## PRÓXIMOS PASOS RECOMENDADOS

1. **Backend**: Agregar campo `servicioEsencialAfectado` en INCIDENTES
2. **Frontend**: Implementar lógica condicional para OIV
3. **Validaciones**: Crear alertas automáticas 1 hora antes de cada vencimiento
4. **Auditoría**: Registrar timestamps de cada etapa completada
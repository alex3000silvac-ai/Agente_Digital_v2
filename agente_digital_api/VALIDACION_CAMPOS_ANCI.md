# 📋 Validación de Campos: Formulario vs Plantilla ANCI

## 🔍 Análisis de Compatibilidad

### ✅ Campos que SÍ coinciden (formulario → plantilla):

| Campo en Formulario | Marcador en Plantilla | Estado |
|-------------------|---------------------|---------|
| `titulo` | `{{TITULO_INCIDENTE}}` | ✅ OK |
| `fechaDeteccion` | `{{FECHA_DETECCION}}` | ✅ OK |
| `fechaOcurrencia` | `{{FECHA_OCURRENCIA}}` | ✅ OK |
| `criticidad` | `{{CRITICIDAD}}` | ✅ OK |
| `sistemasAfectados` | `{{SISTEMAS_AFECTADOS}}` | ✅ OK |
| `serviciosInterrumpidos` | `{{SERVICIOS_INTERRUMPIDOS}}` | ✅ OK |
| `alcanceGeografico` | `{{ALCANCE_GEOGRAFICO}}` | ✅ OK |
| `responsableCliente` | `{{RESPONSABLE_CLIENT}}` | ✅ OK |
| `tipoAmenaza` | `{{TIPO_AMENAZA}}` | ✅ OK |
| `impactoPreliminar` | `{{IMPACTO_PRELIMINAR}}` | ✅ OK |
| `analisisCausaRaiz` | `{{CAUSA_RAIZ}}` | ✅ OK |
| `leccionesAprendidas` | `{{LECCIONES_APRENDIDAS}}` | ✅ OK |
| `recomendacionesMejora` | `{{PLAN_MEJORA}}` | ✅ OK |

### ❌ Campos FALTANTES en el formulario:

| Marcador en Plantilla | Campo Necesario | Descripción |
|---------------------|-----------------|-------------|
| `{{ID_INCIDENTE}}` | IDVisible | ID único del incidente (se genera al guardar) |
| `{{ESTADO}}` | EstadoActual | Estado del incidente |
| `{{EMPRESA_ID}}` | EmpresaID | ID de la empresa (disponible en contexto) |
| `{{TIPO_EMPRESA}}` | Tipo_Empresa | OIV/PSE/AMBAS |
| `{{REPORTE_ANCI_ID}}` | ReporteAnciID | ID del reporte ANCI |
| `{{FECHA_DECLARACION_ANCI}}` | FechaDeclaracionANCI | Fecha de declaración a ANCI |
| `{{ORIGEN_INCIDENTE}}` | OrigenIncidente | Se captura como `vectorAtaque` |

### 🔄 Campos con nombres diferentes:

| Formulario | Base de Datos | Plantilla |
|------------|---------------|-----------|
| `vectorAtaque` | `OrigenIncidente` | `{{ORIGEN_INCIDENTE}}` |
| `medidasContencion` | `AccionesInmediatas` | `{{ACCIONES_INMEDIATAS}}` (no está en plantilla) |

### 📊 Resumen de Estado:

- **Campos completos**: 13/20 (65%)
- **Campos faltantes críticos**: 3
  - Estado del incidente
  - ID del reporte ANCI
  - Fecha de declaración ANCI
- **Campos generados automáticamente**: 4
  - ID del incidente
  - Fecha del reporte
  - Empresa ID
  - Tipo de empresa

## 🛠️ Recomendaciones:

### 1. **Agregar campos faltantes al formulario**:

```vue
<!-- En Sección 1 o nueva sección ANCI -->
<div class="form-group">
  <label>Estado del Incidente</label>
  <select v-model="datosIncidente.estadoActual" class="form-control">
    <option value="Activo">Activo</option>
    <option value="En Investigación">En Investigación</option>
    <option value="Contenido">Contenido</option>
    <option value="Erradicado">Erradicado</option>
    <option value="Cerrado">Cerrado</option>
  </select>
</div>

<div class="form-group">
  <label>ID Reporte ANCI</label>
  <input 
    v-model="datosIncidente.reporteAnciId" 
    type="text" 
    class="form-control"
    placeholder="Ej: ANCI-2024-001">
</div>

<div class="form-group">
  <label>Fecha Declaración ANCI</label>
  <input 
    v-model="datosIncidente.fechaDeclaracionAnci" 
    type="datetime-local" 
    class="form-control">
</div>
```

### 2. **Valores por defecto**:
- `EstadoActual`: "Activo" (al crear)
- `Tipo_Empresa`: Obtener de la tabla Empresas
- `FECHA_REPORTE`: Fecha actual al generar

### 3. **Mapeo de campos**:
```javascript
// En el backend al guardar
OrigenIncidente = formulario.vectorAtaque
AccionesInmediatas = formulario.medidasContencion
```

### 4. **Campos opcionales** que podrían agregarse:
- Número de personas afectadas
- Datos comprometidos (tipo y cantidad)
- Tiempo de recuperación estimado
- Costos estimados del incidente

## ✅ Conclusión:

El formulario actual captura **la mayoría** de los datos necesarios para el informe ANCI. Sin embargo, faltan algunos campos críticos relacionados específicamente con el reporte ANCI:

1. **Estado del incidente** - Crítico para el seguimiento
2. **ID del reporte ANCI** - Necesario para trazabilidad
3. **Fecha de declaración ANCI** - Requerido por normativa

Con estos 3 campos adicionales, el formulario estaría 100% compatible con la plantilla ANCI.
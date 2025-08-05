# 🚨 CORRECCIONES URGENTES - PLAZOS ANCI INCORRECTOS

## ERRORES CRÍTICOS DETECTADOS

### 1. ❌ **FALTA ALERTA TEMPRANA (3 HORAS)**
- **GRAVE**: No existe la etapa más crítica del proceso
- **Requisito Legal**: Primera notificación en 3 horas desde detección
- **Aplica para**: TODOS (OIV y PSE)

### 2. ❌ **INFORME FINAL ERRÓNEO (30 días → 15 días)**
- Implementado: 30 días
- Correcto: **15 DÍAS** desde la alerta temprana

### 3. ❌ **LÓGICA OIV INCORRECTA**
- Implementado: Siempre 24 horas para OIV
- Correcto: 
  - **24 horas** SI servicio esencial afectado
  - **72 horas** para otros casos

### 4. ❌ **FALTA PLAN DE ACCIÓN OIV**
- Obligatorio para OIV: **7 DÍAS**
- No existe en el sistema actual

## PLAZOS CORRECTOS SEGÚN DOCUMENTO OFICIAL

### PSE (Prestadores de Servicios Esenciales):
1. **Alerta Temprana**: 3 horas
2. **Segundo Reporte**: 72 horas  
3. **Informe Final**: 15 días

### OIV (Operadores de Importancia Vital):
1. **Alerta Temprana**: 3 horas
2. **Segundo Reporte**: 
   - 24 horas (si servicio esencial afectado)
   - 72 horas (otros casos)
3. **Plan de Acción**: 7 días (SOLO OIV)
4. **Informe Final**: 15 días

## CAMBIOS NECESARIOS EN EL CÓDIGO

### 1. Frontend - VistaDetalleIncidenteANCI.vue
```javascript
// CAMBIAR línea 493:
final: 360 // 15 días (no 30)

// AGREGAR nueva etapa:
alertaTemprana: 3 // 3 horas

// MODIFICAR lógica OIV línea 200:
// Necesita verificar si servicio esencial afectado
```

### 2. Backend - Agregar campos necesarios
- Campo para indicar si servicio esencial afectado
- Timestamp de alerta temprana
- Tracking de Plan de Acción para OIV

### 3. Nuevas validaciones
- Alerta automática a las 2 horas (recordatorio)
- Validar tipo de reporte según etapa
- Verificar campos obligatorios por etapa

## IMPACTO LEGAL

**SANCIONES POR INCUMPLIMIENTO**:
- PSE: Hasta 20,000 UTM
- OIV: Hasta 40,000 UTM

**INFRACCIONES**:
- No reportar en 3 horas: GRAVE
- Información incompleta: GRAVÍSIMA

## ACCIONES INMEDIATAS

1. **Implementar Alerta Temprana (3h)**
2. **Corregir Informe Final a 15 días**
3. **Agregar Plan de Acción OIV**
4. **Modificar lógica condicional OIV**
5. **Actualizar validaciones y alertas**
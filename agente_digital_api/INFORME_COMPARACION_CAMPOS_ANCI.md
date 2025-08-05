# INFORME DE COMPARACIÓN: CAMPOS ANCI vs SISTEMA ACTUAL

## Fecha: 2025-07-19
## Análisis realizado sobre el sistema de incidentes actual

---

## 1. RESUMEN EJECUTIVO

El análisis comparativo entre los campos obligatorios ANCI y los campos actuales del sistema revela que:
- **Campos en la semilla (JSON)**: 45 campos estructurados en 8 secciones
- **Campos agregados vía SQL**: 65 campos adicionales para cumplir ANCI
- **Campos obligatorios ANCI faltantes**: Varios campos críticos aún no están integrados en la semilla

---

## 2. CAMPOS OBLIGATORIOS ANCI PARA ALERTA TEMPRANA

### 2.1 IDENTIFICACIÓN DE LA ENTIDAD

| Campo ANCI Obligatorio | ¿Existe en Semilla? | ¿Existe en BD (SQL)? | Estado |
|------------------------|---------------------|----------------------|---------|
| nombre_institucion | NO | SÍ (vía tabla EMPRESAS) | ⚠️ Parcial |
| rut | NO | SÍ (vía tabla EMPRESAS) | ⚠️ Parcial |
| tipo_entidad | NO | SÍ (TipoEmpresa en EMPRESAS) | ⚠️ Parcial |
| sector_esencial | NO | SÍ (agregado en SQL) | ✅ Completo |

### 2.2 DATOS DE CONTACTO

| Campo ANCI Obligatorio | ¿Existe en Semilla? | ¿Existe en BD (SQL)? | Estado |
|------------------------|---------------------|----------------------|---------|
| nombre_reportante | NO | SÍ (NombreReportante) | ❌ Faltante en semilla |
| cargo | NO | SÍ (CargoReportante) | ❌ Faltante en semilla |
| telefono_24_7 | NO | SÍ (TelefonoEmergencia) | ❌ Faltante en semilla |
| email_oficial | NO | SÍ (EmailOficialSeguridad) | ❌ Faltante en semilla |

### 2.3 DATOS DEL INCIDENTE

| Campo ANCI Obligatorio | ¿Existe en Semilla? | ¿Existe en BD (SQL)? | Estado |
|------------------------|---------------------|----------------------|---------|
| fecha_hora_deteccion | PARCIAL (fecha/hora separados) | SÍ (FechaDeteccion) | ⚠️ Parcial |
| fecha_hora_inicio_estimada | PARCIAL (fecha_incidente) | SÍ (FechaOcurrencia) | ⚠️ Parcial |
| descripcion_breve | SÍ (descripcion) | SÍ | ✅ Completo |
| taxonomia_inicial | SÍ (sección 4 completa) | SÍ | ✅ Completo |

### 2.4 IMPACTO INICIAL

| Campo ANCI Obligatorio | ¿Existe en Semilla? | ¿Existe en BD (SQL)? | Estado |
|------------------------|---------------------|----------------------|---------|
| sistemas_afectados | NO | SÍ (SistemasAfectados) | ❌ Faltante en semilla |
| servicios_interrumpidos | PARCIAL (tipo_servicio_afectado) | SÍ (ServiciosInterrumpidos) | ⚠️ Parcial |
| duracion_estimada | NO | SÍ (DuracionEstimadaHoras) | ❌ Faltante en semilla |
| usuarios_afectados | SÍ (cantidad_usuarios_afectados) | SÍ | ✅ Completo |
| alcance_geografico | NO | SÍ (AlcanceGeografico) | ❌ Faltante en semilla |

### 2.5 ESTADO ACTUAL

| Campo ANCI Obligatorio | ¿Existe en Semilla? | ¿Existe en BD (SQL)? | Estado |
|------------------------|---------------------|----------------------|---------|
| incidente_en_curso | NO | SÍ (IncidenteEnCurso) | ❌ Faltante en semilla |
| contencion_aplicada | PARCIAL (medidas_contencion texto) | SÍ (ContencionAplicada) | ⚠️ Parcial |
| descripcion_estado | NO | SÍ (DescripcionEstadoActual) | ❌ Faltante en semilla |

### 2.6 ACCIONES INMEDIATAS

| Campo ANCI Obligatorio | ¿Existe en Semilla? | ¿Existe en BD (SQL)? | Estado |
|------------------------|---------------------|----------------------|---------|
| medidas_contencion | SÍ | SÍ | ✅ Completo |
| sistemas_aislados | NO | SÍ (SistemasAislados) | ❌ Faltante en semilla |

### 2.7 SOLICITUD DE APOYO

| Campo ANCI Obligatorio | ¿Existe en Semilla? | ¿Existe en BD (SQL)? | Estado |
|------------------------|---------------------|----------------------|---------|
| requiere_asistencia_csirt | NO | SÍ (SolicitarCSIRT) | ❌ Faltante en semilla |
| tipo_apoyo_requerido | NO | NO | ❌ Faltante total |

---

## 3. CAMPOS ACTUALES EN LA SEMILLA (ESTRUCTURA JSON)

### Sección 1: Información General
- tipo_persona
- nombre_informante, rut_informante, email_informante, telefono_informante
- region
- tiene_representante
- nombre_representante, rut_representante, email_representante, telefono_representante

### Sección 2: Identificación y Clasificación
- titulo, descripcion
- fecha_incidente, hora_incidente
- incidente_critico
- estado_operacional
- tipo_servicio_afectado
- impacto_operacional
- detectado_por, descripcion_deteccion
- evidencias (estructura para archivos)

### Sección 3: Evaluación de Impacto
- afectacion_servicio
- cantidad_usuarios_afectados, tipo_usuarios_afectados
- impacto_economico, impacto_reputacional, impacto_operativo
- otros_impactos
- evidencias

### Sección 4: Taxonomías
- Estructura completa con soporte para múltiples taxonomías
- Evidencias jerárquicas por taxonomía
- Historial de cambios

### Sección 5: Respuesta y Mitigación
- acciones_inmediatas
- fecha_inicio_mitigacion, hora_inicio_mitigacion
- medidas_contencion
- se_activo_protocolo, protocolo_activado
- evidencias

### Sección 6: Análisis de Causa
- analisis_preliminar
- causa_raiz_identificada, descripcion_causa_raiz
- factores_contribuyentes
- evidencias

### Sección 7: Lecciones Aprendidas
- acciones_correctivas, acciones_preventivas
- mejoras_procesos
- actualizacion_documentacion
- capacitacion_requerida

### Sección 8: Seguimiento
- responsable_seguimiento
- fecha_compromiso_acciones
- metricas_seguimiento
- periodicidad_revision
- observaciones_adicionales

---

## 4. CAMPOS AGREGADOS VÍA SQL (NO EN SEMILLA)

### Identificación y Contacto
- SectorEsencial
- NombreReportante, CargoReportante
- TelefonoEmergencia
- EmailOficialSeguridad

### Estado y Duración
- IncidenteEnCurso, ContencionAplicada
- DescripcionEstadoActual
- DuracionEstimadaHoras, DuracionRealHoras

### Análisis Detallado
- DescripcionCompleta
- VectorAtaque
- VolumenDatosComprometidosGB
- EfectosColaterales

### Indicadores de Compromiso (IoCs)
- IPsSospechosas
- HashesMalware
- DominiosMaliciosos
- CuentasComprometidas
- URLsMaliciosas

### Análisis Técnico
- VulnerabilidadExplotada
- FallaControlSeguridad
- ErrorHumanoInvolucrado
- DescripcionErrorHumano

### Acciones de Respuesta
- MedidasErradicacion
- EstadoRecuperacion
- TiempoEstimadoResolucion
- SistemasAislados

### Coordinaciones Externas
- NotificacionRegulador, ReguladorNotificado
- DenunciaPolicial, NumeroPartePolicial
- ContactoProveedoresSeguridad
- ComunicacionPublica

### Plan de Acción OIV
- ProgramaRestauracion
- ResponsablesAdministrativos
- TiempoRestablecimientoHoras
- RecursosNecesarios
- AccionesCortoPlazo, AccionesMedianoPlazo, AccionesLargoPlazo

### Impacto Económico
- CostosRecuperacion
- PerdidasOperativas
- CostosTerceros

### Tracking de Reportes ANCI
- AlertaTempranaEnviada, FechaAlertaTemprana
- InformePreliminarEnviado, FechaInformePreliminar
- InformeCompletoEnviado, FechaInformeCompleto
- PlanAccionEnviado, FechaPlanAccion
- InformeFinalEnviado, FechaInformeFinal

---

## 5. ANÁLISIS DE BRECHAS CRÍTICAS

### 5.1 Campos ANCI Obligatorios NO presentes en la semilla:
1. **Datos de la entidad**: Todos los campos de identificación de la empresa
2. **Contacto de emergencia**: Nombre, cargo, teléfono 24/7 y email oficial del reportante
3. **Sistemas afectados**: Lista específica de sistemas comprometidos
4. **Alcance geográfico**: Zonas o regiones afectadas
5. **Estado del incidente**: Si está en curso o contenido
6. **Sistemas aislados**: Qué sistemas se han aislado como medida de contención
7. **Solicitud CSIRT**: Si requiere asistencia del equipo de respuesta

### 5.2 Campos importantes para OIV no incluidos:
1. **Vector de ataque**: Cómo se produjo el incidente
2. **Indicadores de compromiso**: IPs, hashes, dominios maliciosos
3. **Vulnerabilidad explotada**: CVE o descripción técnica
4. **Volumen de datos comprometidos**: En GB
5. **Cronología detallada**: Timeline de eventos

---

## 6. RECOMENDACIONES URGENTES

### 6.1 Integración Inmediata en la Semilla
Agregar los siguientes campos a la estructura JSON del incidente:

#### En Sección 1 (Información General):
```json
"empresa": {
    "razon_social": "",
    "rut": "",
    "tipo_entidad": "",
    "sector_esencial": ""
},
"contacto_emergencia": {
    "nombre_reportante": "",
    "cargo_reportante": "",
    "telefono_24_7": "",
    "email_oficial_seguridad": ""
}
```

#### En Sección 2 (Identificación):
```json
"sistemas_afectados": [],
"alcance_geografico": "",
"incidente_en_curso": true,
"contencion_aplicada": false,
"descripcion_estado_actual": ""
```

#### En Sección 5 (Respuesta):
```json
"sistemas_aislados": [],
"solicitar_csirt": false,
"tipo_apoyo_requerido": ""
```

### 6.2 Campos Adicionales Recomendados:
```json
"analisis_tecnico": {
    "vector_ataque": "",
    "vulnerabilidad_explotada": "",
    "volumen_datos_gb": 0,
    "iocs": {
        "ips_sospechosas": [],
        "hashes_malware": [],
        "dominios_maliciosos": [],
        "urls_maliciosas": []
    }
}
```

### 6.3 Acciones Prioritarias:
1. **URGENTE**: Modificar `unificador.py` para incluir campos obligatorios ANCI
2. **IMPORTANTE**: Crear función de migración para incidentes existentes
3. **RECOMENDADO**: Validador específico para requisitos ANCI
4. **OPCIONAL**: Interface unificada para capturar todos los campos

### 6.4 Estrategia de Implementación:
1. **Fase 1** (Inmediata): Agregar campos obligatorios a la estructura base
2. **Fase 2** (1 semana): Migrar datos existentes y actualizar formularios
3. **Fase 3** (2 semanas): Implementar validaciones ANCI completas
4. **Fase 4** (3 semanas): Integrar con generación automática de reportes

---

## 7. CONCLUSIONES

1. **Brecha significativa**: Existen campos críticos ANCI que no están en la semilla JSON
2. **Datos dispersos**: Información requerida está dividida entre JSON y campos SQL
3. **Riesgo de cumplimiento**: Sin estos campos, los reportes ANCI estarán incompletos
4. **Oportunidad**: La estructura modular actual facilita la integración de nuevos campos

## 8. PRÓXIMOS PASOS

1. Actualizar `ESTRUCTURA_BASE` en `unificador.py` con campos faltantes
2. Crear script de migración para poblar nuevos campos desde BD
3. Actualizar validadores para incluir reglas ANCI
4. Modificar formularios de captura para solicitar campos obligatorios
5. Implementar función de verificación pre-envío ANCI

---

**Nota**: Este informe debe actualizarse conforme se implementen los cambios recomendados.
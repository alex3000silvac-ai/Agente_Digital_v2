# VERIFICACIÓN CAMPOS ANCI vs EXPEDIENTE SEMILLA

## CAMPOS REQUERIDOS POR ANCI SEGÚN DOCUMENTO OFICIAL

### 1. ALERTA TEMPRANA (3 HORAS)

**Identificación_Entidad:**
- ✅ nombre_institucion → RazonSocial (EMPRESAS)
- ✅ rut → RUT (EMPRESAS) 
- ✅ tipo_entidad → TipoEmpresa (EMPRESAS)
- ❌ sector_esencial → **FALTA - Agregar campo**

**Datos_Contacto:**
- ❌ nombre_reportante → **FALTA - Campo usuario/responsable**
- ❌ cargo → **FALTA - Cargo del responsable**
- ❌ telefono_24_7 → **FALTA - Teléfono emergencia**
- ❌ email_oficial → **FALTA - Email oficial seguridad**

**Datos_Incidente:**
- ✅ fecha_hora_deteccion → FechaDeteccion (INCIDENTES)
- ✅ fecha_hora_inicio_estimada → FechaOcurrencia (INCIDENTES)
- ✅ descripcion_breve → DescripcionInicial (INCIDENTES)
- ✅ taxonomia_inicial → INCIDENTE_TAXONOMIA

**Impacto_Inicial:**
- ✅ sistemas_afectados → SistemasAfectados (INCIDENTES)
- ✅ servicios_interrumpidos → ServiciosInterrumpidos (INCIDENTES)
- ❌ duracion_estimada → **FALTA - Campo duración**
- ✅ usuarios_afectados → UsuariosAfectados (INCIDENTES)
- ✅ alcance_geografico → AlcanceGeografico (INCIDENTES)

**Estado_Actual:**
- ❌ incidente_en_curso → **FALTA - Estado actual**
- ❌ contenido_aplicado → **FALTA - Medidas aplicadas**
- ❌ descripcion_estado → **FALTA - Descripción estado**

**Acciones_Inmediatas:**
- ✅ medidas_contencion → AccionesInmediatas (INCIDENTES)
- ❌ sistemas_aislados → **FALTA - Sistemas aislados**

**Solicitud_Apoyo:**
- ✅ requiere_asistencia_csirt → SolicitarCSIRT (INCIDENTES)
- ✅ tipo_apoyo_requerido → ObservacionesCSIRT (INCIDENTES)

### 2. SEGUNDO REPORTE (24/72 HORAS)

**Análisis_Detallado:**
- ❌ descripcion_completa → **PARCIAL - Solo DescripcionInicial**
- ❌ vector_ataque → **FALTA - Vector de ataque**
- ✅ causa_raiz_preliminar → CausaRaiz (INCIDENTES)

**Gravedad_Impacto:**
- ✅ nivel_criticidad → Criticidad (INCIDENTES)
- ✅ sistemas_especificos_afectados → SistemasAfectados
- ❌ duracion_real_interrupcion → **FALTA - Duración real**
- ✅ numero_usuarios_impactados → UsuariosAfectados
- ❌ volumen_datos_comprometidos → **FALTA - Volumen datos**
- ❌ efectos_colaterales → **FALTA - Efectos colaterales**

**Indicadores_Compromiso:**
- ❌ direcciones_ip_sospechosas → **FALTA - IPs maliciosas**
- ❌ hashes_malware → **FALTA - Hashes**
- ❌ dominios_maliciosos → **FALTA - Dominios**
- ❌ cuentas_comprometidas → **FALTA - Cuentas**
- ❌ urls_maliciosas → **FALTA - URLs**

**Análisis_Causa_Raíz:**
- ❌ vulnerabilidad_explotada → **FALTA - CVE/Vulnerabilidad**
- ❌ falla_control_seguridad → **FALTA - Control fallido**
- ❌ error_humano_involucrado → **FALTA - Factor humano**

**Acciones_Respuesta:**
- ✅ medidas_contencion_aplicadas → AccionesInmediatas
- ❌ medidas_erradicacion → **FALTA - Erradicación**
- ❌ estado_recuperacion → **FALTA - Estado recuperación**
- ❌ tiempo_estimado_resolucion → **FALTA - Tiempo resolución**

**Coordinaciones_Externas:**
- ❌ notificacion_regulador_sectorial → **FALTA**
- ❌ denuncia_policial → **FALTA**
- ❌ contacto_proveedores_seguridad → **FALTA**
- ❌ comunicacion_publica_emitida → **FALTA**

### 3. PLAN DE ACCIÓN (SOLO OIV - 7 DÍAS)

**Plan_Recuperacion:**
- ❌ programa_restauracion_datos → **FALTA**
- ✅ responsables_tecnicos → ResponsableCliente (parcial)
- ❌ responsables_administrativos → **FALTA**
- ❌ tiempo_estimado_restablecimiento → **FALTA**
- ❌ recursos_necesarios → **FALTA**

**Medidas_Mitigacion:**
- ❌ acciones_corto_plazo → **FALTA**
- ❌ acciones_mediano_plazo → **FALTA**
- ❌ acciones_largo_plazo → **FALTA**

### 4. INFORME FINAL (15 DÍAS)

- ✅ Lecciones aprendidas → LeccionesAprendidas (INCIDENTES)
- ✅ Plan mejora → PlanMejora (INCIDENTES)
- ❌ Cronología detallada → **FALTA - Timeline**
- ❌ Impacto económico → **FALTA - Costos**

## CAMPOS A AGREGAR EN LA BASE DE DATOS

### TABLA INCIDENTES - Campos faltantes críticos:

```sql
ALTER TABLE INCIDENTES ADD:
-- Identificación y contacto
SectorEsencial VARCHAR(100),
NombreReportante VARCHAR(200),
CargoReportante VARCHAR(100),
TelefonoEmergencia VARCHAR(50),
EmailOficialSeguridad VARCHAR(200),

-- Estado y duración
IncidenteEnCurso BIT DEFAULT 1,
ContencionAplicada BIT DEFAULT 0,
DescripcionEstadoActual TEXT,
DuracionEstimadaHoras INT,
DuracionRealHoras DECIMAL(10,2),

-- Análisis detallado
DescripcionCompleta TEXT,
VectorAtaque VARCHAR(200),
VolumenDatosComprometidosGB DECIMAL(10,2),
EfectosColaterales TEXT,

-- Indicadores de compromiso (IoCs)
IPsSospechosas TEXT,
HashesMalware TEXT,
DominiosMaliciosos TEXT,
CuentasComprometidas TEXT,
URLsMaliciosas TEXT,

-- Análisis técnico
VulnerabilidadExplotada VARCHAR(200),
FallaControlSeguridad TEXT,
ErrorHumanoInvolucrado BIT,
DescripcionErrorHumano TEXT,

-- Acciones y recuperación
MedidasErradicacion TEXT,
EstadoRecuperacion VARCHAR(50),
TiempoEstimadoResolucion INT,
SistemasAislados TEXT,

-- Coordinaciones externas
NotificacionRegulador BIT DEFAULT 0,
ReguladorNotificado VARCHAR(200),
DenunciaPolicial BIT DEFAULT 0,
NumeroPartePolicial VARCHAR(100),
ContactoProveedoresSeguridad BIT DEFAULT 0,
ComunicacionPublica BIT DEFAULT 0,

-- Plan de acción OIV
ProgramaRestauracion TEXT,
ResponsablesAdministrativos TEXT,
TiempoRestablecimientoHoras INT,
RecursosNecesarios TEXT,
AccionesCortoPlazo TEXT,
AccionesMedianoPlazo TEXT,
AccionesLargoPlazo TEXT,

-- Impacto económico
CostosRecuperacion DECIMAL(15,2),
PerdidasOperativas DECIMAL(15,2),
CostosTerceros DECIMAL(15,2),

-- Timeline
CronologiaDetallada TEXT
```

### NUEVA TABLA SUGERIDA: INCIDENTES_TIMELINE

```sql
CREATE TABLE INCIDENTES_TIMELINE (
    TimelineID INT IDENTITY(1,1) PRIMARY KEY,
    IncidenteID INT FOREIGN KEY REFERENCES INCIDENTES(IncidenteID),
    FechaHora DATETIME NOT NULL,
    Evento VARCHAR(500) NOT NULL,
    TipoEvento VARCHAR(50), -- deteccion, contencion, escalamiento, resolucion
    Usuario VARCHAR(200),
    Detalles TEXT,
    FechaCreacion DATETIME DEFAULT GETDATE()
)
```

### NUEVA TABLA SUGERIDA: INCIDENTES_IOCS

```sql
CREATE TABLE INCIDENTES_IOCS (
    IoCID INT IDENTITY(1,1) PRIMARY KEY,
    IncidenteID INT FOREIGN KEY REFERENCES INCIDENTES(IncidenteID),
    TipoIoC VARCHAR(50), -- IP, Hash, Dominio, URL, Cuenta
    Valor VARCHAR(500),
    Descripcion TEXT,
    Accion VARCHAR(100), -- Bloqueado, Monitoreado, Pendiente
    FechaDeteccion DATETIME,
    FechaCreacion DATETIME DEFAULT GETDATE()
)
```

## RESUMEN DE ACCIONES NECESARIAS

1. **CRÍTICO**: Agregar campos de contacto de emergencia
2. **CRÍTICO**: Agregar campos de indicadores de compromiso
3. **IMPORTANTE**: Agregar campos de estado y duración
4. **IMPORTANTE**: Crear tabla de timeline para cronología
5. **ÚTIL**: Crear tabla de IoCs para mejor gestión

## CAMPOS YA EXISTENTES APROVECHABLES

✅ Información básica empresa (EMPRESAS)
✅ Datos básicos incidente (INCIDENTES)
✅ Taxonomías (INCIDENTE_TAXONOMIA)
✅ Archivos adjuntos (INCIDENTES_ARCHIVOS)
✅ Comentarios (INCIDENTES_COMENTARIOS)
✅ Causa raíz, lecciones aprendidas, plan mejora
✅ Solicitud CSIRT

Total campos requeridos ANCI: ~70
Total campos disponibles: ~25 (36%)
**Faltan aproximadamente 45 campos críticos**
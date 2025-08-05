# VALIDACIÓN DE CAMPOS ANCI vs SEMILLA DE INCIDENTES

## Fecha: 2025-07-19
## Estado: CRÍTICO - Campos obligatorios ANCI faltantes

---

## 🚨 RESUMEN CRÍTICO

**Situación actual**: La semilla de incidentes NO contiene todos los campos obligatorios ANCI. Esto impide generar reportes completos.

**Campos obligatorios faltantes**: 14 de 28 campos críticos no están en la semilla JSON.

---

## 📊 TABLA DE VALIDACIÓN COMPLETA

### ALERTA TEMPRANA (3 HORAS) - CAMPOS OBLIGATORIOS

| Campo ANCI | ¿En Semilla? | ¿En BD SQL? | Criticidad | Acción Requerida |
|------------|--------------|-------------|------------|------------------|
| **IDENTIFICACIÓN DE LA ENTIDAD** |
| nombre_institucion | ❌ NO | ✅ SÍ (EMPRESAS) | CRÍTICO | Agregar a semilla |
| rut | ❌ NO | ✅ SÍ (EMPRESAS) | CRÍTICO | Agregar a semilla |
| tipo_entidad | ❌ NO | ✅ SÍ (TipoEmpresa) | CRÍTICO | Agregar a semilla |
| sector_esencial | ❌ NO | ✅ SÍ | CRÍTICO | Agregar a semilla |
| **DATOS DE CONTACTO 24/7** |
| nombre_reportante | ❌ NO | ✅ SÍ | CRÍTICO | Agregar a semilla |
| cargo_reportante | ❌ NO | ✅ SÍ | CRÍTICO | Agregar a semilla |
| telefono_24_7 | ❌ NO | ✅ SÍ | CRÍTICO | Agregar a semilla |
| email_oficial | ❌ NO | ✅ SÍ | CRÍTICO | Agregar a semilla |
| **DATOS DEL INCIDENTE** |
| fecha_hora_deteccion | ⚠️ PARCIAL | ✅ SÍ | MEDIO | Unificar fecha/hora |
| fecha_hora_inicio_estimada | ⚠️ PARCIAL | ✅ SÍ | MEDIO | Unificar fecha/hora |
| descripcion_breve | ✅ SÍ | ✅ SÍ | OK | - |
| taxonomia_inicial | ✅ SÍ | ✅ SÍ | OK | - |
| **IMPACTO INICIAL** |
| sistemas_afectados | ❌ NO | ✅ SÍ | CRÍTICO | Agregar a semilla |
| servicios_interrumpidos | ⚠️ PARCIAL | ✅ SÍ | MEDIO | Mejorar estructura |
| duracion_estimada | ❌ NO | ✅ SÍ | CRÍTICO | Agregar a semilla |
| usuarios_afectados | ✅ SÍ | ✅ SÍ | OK | - |
| alcance_geografico | ❌ NO | ✅ SÍ | CRÍTICO | Agregar a semilla |
| **ESTADO ACTUAL** |
| incidente_en_curso | ❌ NO | ✅ SÍ | CRÍTICO | Agregar a semilla |
| contencion_aplicada | ❌ NO | ✅ SÍ | CRÍTICO | Agregar a semilla |
| descripcion_estado | ❌ NO | ✅ SÍ | CRÍTICO | Agregar a semilla |
| **ACCIONES INMEDIATAS** |
| medidas_contencion | ✅ SÍ | ✅ SÍ | OK | - |
| sistemas_aislados | ❌ NO | ✅ SÍ | ALTO | Agregar a semilla |
| **SOLICITUD DE APOYO** |
| requiere_asistencia_csirt | ❌ NO | ✅ SÍ | ALTO | Agregar a semilla |
| tipo_apoyo_requerido | ❌ NO | ❌ NO | ALTO | Agregar a BD y semilla |

---

## 📋 CAMPOS ADICIONALES PARA REPORTES POSTERIORES

### INFORME PRELIMINAR (24/72 HORAS)
- ❌ vector_ataque
- ❌ vulnerabilidad_explotada
- ❌ indicadores_compromiso (IPs, hashes, dominios)
- ❌ cronologia_detallada

### PLAN DE ACCIÓN OIV (7 DÍAS)
- ❌ programa_restauracion
- ❌ responsables_administrativos
- ❌ tiempo_restablecimiento
- ❌ recursos_necesarios

### INFORME FINAL (15 DÍAS)
- ❌ impacto_economico_detallado
- ❌ lecciones_aprendidas_anci
- ❌ plan_mejora_continua
- ❌ costos_recuperacion

---

## 🔧 SOLUCIÓN PROPUESTA

### 1. MODIFICAR ESTRUCTURA BASE (unificador.py)

```python
# Agregar a sección 1
"empresa": {
    "razon_social": "",
    "rut": "",
    "tipo_entidad": "",  # OIV o PSE
    "sector_esencial": ""
},
"contacto_emergencia": {
    "nombre_reportante": "",
    "cargo_reportante": "",
    "telefono_24_7": "",
    "email_oficial_seguridad": ""
}

# Agregar a sección 2
"sistemas_afectados": [],
"alcance_geografico": "",
"duracion_estimada_horas": 0,
"incidente_en_curso": True,
"contencion_aplicada": False,
"descripcion_estado_actual": ""

# Agregar a sección 5
"sistemas_aislados": [],
"solicitar_csirt": False,
"tipo_apoyo_csirt": ""
```

### 2. CREAR FUNCIÓN DE MIGRACIÓN

```python
def migrar_campos_anci(incidente_id):
    """Migra campos ANCI desde BD a semilla JSON"""
    # 1. Obtener datos de EMPRESAS
    # 2. Obtener campos nuevos de INCIDENTES
    # 3. Actualizar JSON manteniendo datos existentes
    # 4. Guardar versión actualizada
```

### 3. VALIDADOR ANCI

```python
def validar_campos_anci(incidente_json, tipo_reporte):
    """Valida que existan todos los campos obligatorios ANCI"""
    campos_faltantes = []
    
    if tipo_reporte == "alerta_temprana":
        # Validar 24 campos obligatorios
        if not incidente_json.get("empresa", {}).get("razon_social"):
            campos_faltantes.append("razon_social")
        # ... más validaciones
    
    return campos_faltantes
```

---

## ⚡ ACCIONES INMEDIATAS REQUERIDAS

1. **HOY**: Actualizar `unificador.py` con campos obligatorios
2. **MAÑANA**: Crear script de migración para incidentes existentes  
3. **ESTA SEMANA**: Implementar validador ANCI
4. **PRÓXIMA SEMANA**: Actualizar formularios de captura

---

## 📈 IMPACTO DE NO IMPLEMENTAR

- **Legal**: Multas hasta 20,000 UTM (PSE) o 40,000 UTM (OIV)
- **Operacional**: Imposibilidad de cumplir plazos ANCI
- **Reputacional**: Sanciones públicas por incumplimiento

---

## ✅ CRITERIO DE ÉXITO

Un incidente semilla debe poder generar automáticamente:
1. Alerta Temprana completa (3h)
2. Informe Preliminar completo (24/72h)
3. Plan de Acción OIV si aplica (7d)
4. Informe Final completo (15d)

**Sin intervención manual para campos obligatorios**
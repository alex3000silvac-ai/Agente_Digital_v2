# 🌱 SISTEMA DE SEMILLAS PARA REPORTE ANCI

## 📋 **Resumen del Sistema**

El sistema de semillas garantiza que cada incidente tenga un formato unificado y consistente que sirve como fuente única de verdad para generar el reporte ANCI.

---

## 🔄 **Flujo del Sistema de Semillas**

### 1. **Creación del Incidente** (Semilla Original)
```
Usuario crea incidente → Formato Unificado → Semilla Original → BD + Archivo JSON
```

### 2. **Edición del Incidente** (Semilla Base)
```
Cargar Semilla → Editar → Guardar → Nueva Semilla Base → BD + Archivo JSON
```

### 3. **Generación Reporte ANCI**
```
Leer Semilla Base → Transformar a formato ANCI → Generar XML/JSON → Enviar
```

---

## 📁 **Estructura de Archivos Semilla**

```
/semillas_incidentes/
  └── {empresa_id}/
      └── {incidente_id}/
          ├── semilla_original_{timestamp}.json    # Primera versión
          ├── semilla_base_{timestamp}.json        # Versión actual
          └── semilla_edicion_{timestamp}.json     # Temporales de edición
```

---

## 🗂️ **Formato Unificado de Semilla**

```json
{
  "metadata": {
    "version_formato": "2.0",
    "timestamp_creacion": "2025-07-17T10:00:00",
    "timestamp_actualizacion": "2025-07-17T15:30:00",
    "estado_temporal": "semilla_base",
    "hash_integridad": "abc123..."
  },
  
  "1": {
    "tipo_persona": "Jurídica",
    "nombre_informante": "Empresa XYZ",
    "rut_informante": "12.345.678-9",
    // ... todos los campos de sección 1
  },
  
  "2": {
    "titulo": "Incidente de seguridad",
    "descripcion": "...",
    "criticidad": "Alta",
    // ... todos los campos de sección 2
  },
  
  "3": {
    "tipo_amenaza": "Phishing",
    "vector_ataque": "Email",
    // ... todos los campos de sección 3
  },
  
  "4": {
    "taxonomias": [
      {
        "id": "INC_USO_PHIP_ECDP",
        "area": "Uso Malicioso",
        "efecto": "Phishing",
        "categoria": "...",
        "evidencias": [
          {
            "numeroEvidencia": "4.4.1.1",
            "archivo": "evidencia1.pdf",
            "comentario": "Primera evidencia de phishing"
          },
          {
            "numeroEvidencia": "4.4.1.2",
            "archivo": "logs.txt",
            "comentario": "Logs del servidor"
          }
        ]
      }
    ]
  },
  
  "5": {
    "analisis_causa_raiz": "...",
    "lecciones_aprendidas": "...",
    "plan_mejora": "...",
    // ... todos los campos de sección 5
  },
  
  "evidencias_generales": {
    "descripcion": ["archivo1.pdf", "archivo2.docx"],
    "analisis": ["forense.zip"],
    "acciones": ["procedimiento.pdf"],
    "analisis_final": ["informe_final.pdf"]
  }
}
```

---

## 🔧 **Módulos del Sistema**

### 1. **UnificadorIncidentes** (`unificador.py`)
- Crea estructura base uniforme
- Mantiene versión del formato
- Genera hash de integridad

### 2. **GestorTaxonomias** (`gestor_taxonomias.py`)
- Gestiona sección 4 (taxonomías múltiples)
- Numera evidencias jerárquicamente
- Asocia comentarios con evidencias

### 3. **GestorEvidencias** (`gestor_evidencias.py`)
- Maneja archivos físicos
- Evita duplicados
- Limpia archivos huérfanos

### 4. **ValidadorIncidentes** (`validador.py`)
- Valida formato de semilla
- Verifica integridad
- Integra con diagnóstico

---

## 🚀 **Uso para Reporte ANCI**

### Cargar Semilla para Reporte:
```python
# En el módulo de generación ANCI
def generar_reporte_anci(incidente_id):
    # 1. Cargar semilla base más reciente
    semilla = cargar_semilla_base(incidente_id)
    
    # 2. Validar integridad
    if not validar_integridad_semilla(semilla):
        raise Exception("Semilla corrupta")
    
    # 3. Transformar a formato ANCI
    datos_anci = {
        # Mapeo directo desde semilla
        "tipo_incidente": semilla["2"]["tipo_flujo"],
        "fecha_deteccion": semilla["2"]["fecha_deteccion"],
        "impacto_preliminar": semilla["2"]["impacto_preliminar"],
        "taxonomias": [
            {
                "codigo": tax["id"],
                "evidencias": len(tax["evidencias"])
            }
            for tax in semilla["4"]["taxonomias"]
        ]
        # ... resto del mapeo
    }
    
    # 4. Generar XML/JSON según requerimientos ANCI
    return generar_xml_anci(datos_anci)
```

---

## ✅ **Garantías del Sistema**

1. **Formato Único**: Un solo formato para todo el ciclo
2. **Versionado**: Cada cambio genera nueva versión
3. **Integridad**: Hash para detectar modificaciones
4. **Trazabilidad**: Historial completo de cambios
5. **Recuperabilidad**: Siempre se puede volver a versión anterior

---

## 🔍 **Validaciones Críticas**

1. **Al Guardar**:
   - Formato correcto de taxonomías
   - Evidencias con numeración correcta
   - Comentarios asociados correctamente
   - Archivos físicos existentes

2. **Al Cargar para ANCI**:
   - Semilla existe y es válida
   - Hash de integridad correcto
   - Todos los campos requeridos presentes
   - Evidencias accesibles

---

## 📝 **Notas Importantes**

- **SIEMPRE** usar la semilla como fuente para ANCI
- **NUNCA** leer directamente de BD para reporte ANCI
- **VALIDAR** integridad antes de generar reporte
- **MANTENER** sincronía entre BD y archivos semilla
- **LIMPIAR** archivos huérfanos regularmente

---

## 🚨 **Puntos de Atención**

1. Las evidencias de taxonomías (sección 4) tienen numeración jerárquica
2. Cada evidencia puede tener comentario asociado
3. Los archivos deben existir físicamente
4. El formato debe ser exactamente el mismo en todo el ciclo
5. La semilla es la única fuente de verdad para ANCI
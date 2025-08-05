# 📄 Sistema de Generación de Informes ANCI

## Descripción

He agregado al sistema dinámico la capacidad de generar informes ANCI basados en plantillas Word (.docx), incluyendo la plantilla que mencionaste.

## Características

### 1. **Generador de Informes** (`generador_informes_anci.py`)
- Busca automáticamente la plantilla en varias ubicaciones:
  - `C:\Users\alexs\Downloads\Informes ANCI_ reporte de incidentes_.docx` (tu ruta)
  - `./plantillas/`
  - `../plantillas/`
  - Variables de entorno configurables

- **Funcionalidades**:
  - Genera informes tipo: completo, preliminar, final
  - Reemplaza marcadores automáticamente ({{TITULO_INCIDENTE}}, {{FECHA_DETECCION}}, etc.)
  - Agrega secciones dinámicas según tipo de empresa
  - Incluye listado de evidencias como anexo
  - Guarda en carpeta del incidente

### 2. **API Endpoints** (`informes_anci_views.py`)

#### Generar Informe
```bash
POST /api/informes-anci/generar/<incidente_id>
Body: {
    "tipo_informe": "completo",
    "plantilla": "C:/Users/alexs/Downloads/Informes ANCI_ reporte de incidentes_.docx"
}
```

#### Descargar Informe
```bash
GET /api/informes-anci/descargar/<incidente_id>/<nombre_archivo>
```

#### Listar Plantillas Disponibles
```bash
GET /api/informes-anci/plantillas
```

#### Historial de Informes
```bash
GET /api/informes-anci/historial/<incidente_id>
```

### 3. **Marcadores Soportados**

La plantilla puede contener estos marcadores que serán reemplazados automáticamente:

- `{{FECHA_REPORTE}}` - Fecha actual
- `{{TIPO_REPORTE}}` - Tipo de informe (COMPLETO, PRELIMINAR, FINAL)
- `{{ID_INCIDENTE}}` - ID visible del incidente
- `{{TITULO_INCIDENTE}}` - Título del incidente
- `{{FECHA_DETECCION}}` - Fecha de detección
- `{{FECHA_OCURRENCIA}}` - Fecha de ocurrencia
- `{{CRITICIDAD}}` - Nivel de criticidad
- `{{ESTADO}}` - Estado actual
- `{{EMPRESA_ID}}` - ID de la empresa
- `{{TIPO_EMPRESA}}` - OIV/PSE/AMBAS
- `{{SISTEMAS_AFECTADOS}}` - Sistemas afectados
- `{{SERVICIOS_INTERRUMPIDOS}}` - Servicios interrumpidos
- `{{RESPONSABLE_CLIENT}}` - Responsable del cliente
- `{{REPORTE_ANCI_ID}}` - ID del reporte ANCI
- `{{TIPO_AMENAZA}}` - Tipo de amenaza ANCI
- Y muchos más...

### 4. **Estructura del Informe Generado**

1. **Página principal** - Datos del marcador reemplazados
2. **Secciones dinámicas** - Solo las que tienen contenido
3. **Anexo de evidencias** - Tabla con todas las evidencias

### 5. **Instalación de Dependencias**

Para usar el generador de informes, necesitas instalar:

```bash
pip install python-docx
```

### 6. **Configuración**

Puedes configurar la ubicación de plantillas con variables de entorno:

```bash
# En Windows
set ANCI_TEMPLATE_PATH=C:\Users\alexs\Downloads\Informes ANCI_ reporte de incidentes_.docx
set ANCI_TEMPLATES_DIR=C:\plantillas

# En Linux
export ANCI_TEMPLATE_PATH="/ruta/a/plantilla.docx"
export ANCI_TEMPLATES_DIR="/plantillas"
```

### 7. **Integración con el Sistema**

Para activar el módulo de informes:

```python
# En app/__init__.py
from .views.informes_anci_views import informes_anci_bp
app.register_blueprint(informes_anci_bp)
```

### 8. **Uso desde Frontend**

```javascript
// Generar informe
async generarInformeANCI(incidenteId, tipoInforme = 'completo') {
    const response = await axios.post(
        `/api/informes-anci/generar/${incidenteId}`,
        { tipo_informe: tipoInforme }
    );
    return response.data;
}

// Descargar informe
descargarInforme(incidenteId, nombreArchivo) {
    window.open(`/api/informes-anci/descargar/${incidenteId}/${nombreArchivo}`);
}
```

## Notas Importantes

1. **La plantilla debe existir** en alguna de las ubicaciones configuradas
2. **Requiere python-docx** instalado
3. Los informes se guardan en: `/archivos/empresa_X/incidente_Y/informes_anci/`
4. Se registra en auditoría cada generación de informe
5. Solo usuarios autenticados pueden generar informes

## Mejoras Futuras

- Cache de plantillas procesadas
- Generación de PDF además de Word
- Plantillas por tipo de empresa
- Firma digital de informes
- Envío automático por email
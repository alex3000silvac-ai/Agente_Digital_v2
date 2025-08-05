# 🚨 Integración del Campo CSIRT en el Formulario

## ❌ Problema Identificado

El formulario de declaración de incidentes **NO tiene** el campo para solicitar ayuda al CSIRT, que es requerido en la plantilla ANCI oficial.

## ✅ Solución Implementada

### 1. **Base de Datos** - `agregar_campos_csirt.sql`

Nuevos campos agregados a la tabla `Incidentes`:
- `SolicitarAyudaCSIRT` (BIT) - Si se solicita ayuda
- `FechaSolicitudCSIRT` (DATETIME) - Cuándo se solicitó
- `TipoAyudaCSIRT` (NVARCHAR) - Tipo de asistencia
- `DescripcionAyudaCSIRT` (NVARCHAR) - Descripción detallada
- `EstadoSolicitudCSIRT` (NVARCHAR) - Estado de la solicitud
- `RespuestaCSIRT` (NVARCHAR) - Respuesta del CSIRT
- `ContactoCSIRT` (NVARCHAR) - Contacto de emergencia

### 2. **Componente Vue** - `SeccionCSIRT.vue`

Características:
- ✅ Switch para activar/desactivar solicitud
- ✅ Tipos de ayuda predefinidos
- ✅ Niveles de urgencia (Inmediata/Alta/Media)
- ✅ Información de contacto CSIRT Nacional
- ✅ Estado de la solicitud
- ✅ Validación de campos requeridos

### 3. **Integración en CuadernoAnalista.vue**

Agregar después de la Sección 4 (Acciones Inmediatas):

```vue
<!-- En el template, después del accordion-item de Sección 4 -->
<div class="accordion-item">
  <h2 class="accordion-header" id="heading-csirt">
    <button 
      class="accordion-button collapsed" 
      type="button" 
      data-bs-toggle="collapse" 
      data-bs-target="#collapse-csirt"
      :class="{ 'text-success': datosCSIRT.solicitarAyuda }">
      <i class="fas fa-shield-alt me-2"></i>
      Sección CSIRT - Solicitud de Asistencia
      <span v-if="datosCSIRT.solicitarAyuda" class="badge bg-danger ms-2">
        Ayuda Solicitada
      </span>
    </button>
  </h2>
  <div 
    id="collapse-csirt" 
    class="accordion-collapse collapse" 
    data-bs-parent="#accordionIncidente">
    <div class="accordion-body">
      <SeccionCSIRT v-model="datosCSIRT" />
    </div>
  </div>
</div>

<!-- En el script -->
<script>
import SeccionCSIRT from './SeccionCSIRT.vue'

export default {
  components: {
    // ... otros componentes
    SeccionCSIRT
  },
  data() {
    return {
      // ... otros datos
      datosCSIRT: {
        solicitarAyuda: false,
        tipoAyuda: '',
        descripcionAyuda: '',
        contacto: '',
        urgencia: 'Media'
      }
    }
  },
  methods: {
    async guardarIncidente() {
      // ... código existente
      
      // Agregar campos CSIRT al FormData
      if (this.datosCSIRT.solicitarAyuda) {
        formData.append('SolicitarAyudaCSIRT', '1')
        formData.append('TipoAyudaCSIRT', this.datosCSIRT.tipoAyuda)
        formData.append('DescripcionAyudaCSIRT', this.datosCSIRT.descripcionAyuda)
        formData.append('ContactoCSIRT', this.datosCSIRT.contacto)
        formData.append('FechaSolicitudCSIRT', new Date().toISOString())
      }
      
      // ... resto del código
    }
  }
}
</script>
```

### 4. **Backend - Actualizar incidente_views.py**

Agregar en la función `crear_incidente_completo`:

```python
# Campos CSIRT
solicitar_csirt = request.form.get('SolicitarAyudaCSIRT', '0') == '1'
if solicitar_csirt:
    datos['SolicitarAyudaCSIRT'] = 1
    datos['FechaSolicitudCSIRT'] = datetime.now()
    datos['TipoAyudaCSIRT'] = request.form.get('TipoAyudaCSIRT')
    datos['DescripcionAyudaCSIRT'] = request.form.get('DescripcionAyudaCSIRT')
    datos['ContactoCSIRT'] = request.form.get('ContactoCSIRT')
    datos['EstadoSolicitudCSIRT'] = 'Pendiente'
```

### 5. **Plantilla ANCI - Nuevos Marcadores**

La plantilla podrá usar estos marcadores:
- `{{SOLICITUD_CSIRT}}` - Sí/No
- `{{TIPO_AYUDA_CSIRT}}` - Tipo de asistencia
- `{{FECHA_SOLICITUD_CSIRT}}` - Fecha de solicitud
- `{{DESCRIPCION_AYUDA_CSIRT}}` - Descripción
- `{{ESTADO_SOLICITUD_CSIRT}}` - Estado actual
- `{{CONTACTO_CSIRT}}` - Contacto de emergencia

## 📝 Pasos para Implementar

1. **Ejecutar SQL**:
   ```bash
   sqlcmd -S servidor -d BD -i sql/agregar_campos_csirt.sql
   ```

2. **Copiar componente**:
   - Copiar `SeccionCSIRT.vue` a `src/components/`

3. **Actualizar CuadernoAnalista.vue**:
   - Importar componente
   - Agregar sección al acordeón
   - Agregar datos al guardar

4. **Actualizar backend**:
   - Modificar `incidente_views.py` para manejar campos CSIRT

5. **Actualizar generador de informes**:
   - Agregar marcadores CSIRT en `generador_informes_anci.py`

## 🎯 Resultado

Con esta integración, el formulario tendrá:
- ✅ Campo para solicitar ayuda CSIRT
- ✅ Información de contacto del CSIRT Nacional
- ✅ Tipos de asistencia predefinidos
- ✅ Estado de seguimiento de la solicitud
- ✅ Compatible con plantilla ANCI
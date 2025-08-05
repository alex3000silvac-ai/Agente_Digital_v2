# 🔍 VERIFICACIÓN COMPLETA DE RUTAS Y ENDPOINTS

## ✅ **Endpoints Principales del Sistema**

### 🔷 **Incidentes - CRUD Completo**

#### 1. **Crear Incidente**
- **Endpoint**: `POST /api/incidente/`
- **Frontend**: `CuadernoAnalista.vue` → `guardarIncidente()`
- **Backend**: `incidente_views.py` → `create_incidente()`
- **Datos**: FormData con campos y archivos

#### 2. **Cargar Incidente (MEJORADO)**
- **Endpoint**: `GET /api/incidente/v2/{incidente_id}` ✨ NUEVO
- **Frontend**: `CuadernoAnalista.vue` → `cargarDatosIncidente()`
- **Backend**: `incidente_cargar_completo.py` → `cargar_incidente_completo()`
- **Retorna**: 
  - Datos básicos
  - Evidencias por sección
  - Taxonomías seleccionadas
  - Evidencias por taxonomía con comentarios

#### 3. **Actualizar Incidente**
- **Endpoint**: `PUT /api/incidente/{incidente_id}`
- **Frontend**: `CuadernoAnalista.vue` → `guardarIncidente()`
- **Backend**: `incidente_views.py` → `update_incidente()`
- **Datos**: FormData con cambios y nuevos archivos

#### 4. **Eliminar Incidente**
- **Endpoint**: `DELETE /api/admin/incidentes/{incidente_id}`
- **Frontend**: `VistaListaIncidentes.vue` → `eliminarIncidente()`
- **Backend**: `incidentes_eliminar_completo.py` → `eliminar_incidente_completo()`
- **Acción**: Elimina todo sin dejar rastro

---

### 🔷 **Evidencias - Gestión de Archivos**

#### 1. **Eliminar Evidencia Individual**
- **Endpoint**: `DELETE /api/evidencias/eliminar/{evidencia_id}?incidente_id={id}&tipo={general|taxonomia}`
- **Frontend**: Por implementar en `CuadernoAnalista.vue`
- **Backend**: `evidencias_eliminar.py` → `eliminar_evidencia()`
- **Acción**: Elimina archivo físico y registro BD

#### 2. **Limpiar Archivos Huérfanos**
- **Endpoint**: `POST /api/evidencias/limpiar-huerfanos/{incidente_id}`
- **Frontend**: Llamar al guardar/eliminar
- **Backend**: `evidencias_eliminar.py` → `limpiar_archivos_huerfanos()`
- **Acción**: Busca y elimina archivos sin referencia

#### 3. **Descargar Evidencia**
- **Endpoint**: `GET /api/admin/evidencia-incidente/{evidencia_id}`
- **Frontend**: Enlaces en evidencias mostradas
- **Backend**: `incidentes_evidencias_views.py`

---

### 🔷 **Taxonomías - Sección 4**

#### 1. **Listar Taxonomías**
- **Endpoint**: `GET /api/admin/taxonomias/flat?tipo_empresa={PSE|OTRO}`
- **Frontend**: `CuadernoAnalista.vue` → `cargarTaxonomias()`
- **Backend**: `admin/taxonomias.py`
- **Retorna**: Lista plana de taxonomías disponibles

#### 2. **Guardar Evidencias de Taxonomía**
- **Tabla BD**: `EVIDENCIAS_TAXONOMIA`
- **Campos**: IncidenteID, Id_Taxonomia, NumeroEvidencia, RutaArchivo
- **Comentarios**: En tabla `COMENTARIOS_TAXONOMIA`

---

### 🔷 **Empresas y Context**

#### 1. **Obtener Datos Empresa**
- **Endpoint**: `GET /api/admin/empresas/{empresa_id}`
- **Frontend**: `CuadernoAnalista.vue` → `cargarDatosEmpresa()`
- **Backend**: `empresas_views.py`

#### 2. **Listar Incidentes de Empresa**
- **Endpoint**: `GET /api/admin/empresas/{empresa_id}/incidentes`
- **Frontend**: `VistaListaIncidentes.vue`
- **Backend**: `empresas_views.py`

---

## 📋 **Flujo Completo de Datos**

### 🔄 **Crear → Editar → Guardar**

```mermaid
graph LR
    A[Frontend Form] -->|POST /api/incidente/| B[Crear Incidente]
    B --> C[BD + Semilla Original]
    C --> D[GET /api/incidente/v2/ID]
    D -->|Datos Completos| E[Frontend Edición]
    E -->|PUT /api/incidente/ID| F[Actualizar]
    F --> G[BD + Semilla Base]
    G -->|Para ANCI| H[Leer Semilla]
```

---

## 🚨 **Puntos Críticos a Verificar**

### 1. **Al Crear Incidente**
- ✅ FormData incluye todos los campos
- ✅ Archivos se suben correctamente
- ✅ Taxonomías se guardan en `INCIDENTE_TAXONOMIA`
- ✅ Evidencias de taxonomías en `EVIDENCIAS_TAXONOMIA`
- ✅ Comentarios en `COMENTARIOS_TAXONOMIA`

### 2. **Al Cargar para Editar**
- ✅ Usar endpoint v2: `/api/incidente/v2/{id}`
- ✅ Evidencias se cargan por sección correcta
- ✅ Taxonomías muestran sus evidencias
- ✅ Comentarios aparecen asociados

### 3. **Al Eliminar Evidencias**
- ✅ Eliminar archivo físico
- ✅ Eliminar registro BD
- ✅ Actualizar UI inmediatamente
- ✅ No dejar archivos huérfanos

### 4. **Al Generar Reporte ANCI**
- ✅ Leer desde archivo semilla
- ✅ NO leer directamente de BD
- ✅ Validar integridad de semilla
- ✅ Todos los campos mapeados

---

## 🔧 **Comandos de Prueba**

### Probar Endpoint de Carga Mejorado:
```bash
curl http://localhost:5000/api/incidente/v2/17
```

### Verificar Eliminación de Evidencia:
```bash
curl -X DELETE "http://localhost:5000/api/evidencias/eliminar/123?incidente_id=17&tipo=general"
```

### Limpiar Archivos Huérfanos:
```bash
curl -X POST http://localhost:5000/api/evidencias/limpiar-huerfanos/17
```

---

## ⚠️ **Advertencias**

1. **SIEMPRE** reiniciar servidor Flask después de cambios
2. **VERIFICAR** que nuevos endpoints estén registrados en `__init__.py`
3. **PROBAR** con datos reales antes de producción
4. **MONITOREAR** logs del servidor para errores
5. **RESPALDAR** antes de eliminar masivamente

---

## 📊 **Estado Actual**

- ✅ Endpoint de carga mejorado implementado
- ✅ Frontend actualizado para usar nuevo endpoint
- ✅ Sistema de eliminación de archivos huérfanos
- ✅ Documentación de semillas para ANCI
- ✅ Todas las rutas principales verificadas

**Sistema listo para pruebas completas** 🚀
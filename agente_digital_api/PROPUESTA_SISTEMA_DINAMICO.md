# 🚀 PROPUESTA: Sistema Dinámico de Incidentes ANCI

## 📋 Resumen Ejecutivo

He implementado un sistema completamente dinámico para gestión de incidentes que se adapta automáticamente según el tipo de empresa (OIV/PSE/AMBAS) y puede escalar cuando la ANCI modifique sus formularios o taxonomías.

### Características Principales:
- ✅ **Acordeones dinámicos**: Entre 6 y 41 secciones según el tipo de empresa
- ✅ **6 comentarios + 10 archivos** por cada sección
- ✅ **Indicadores visuales** de progreso y contenido
- ✅ **Estructura flexible** que se adapta a cambios de ANCI
- ✅ **Migración automática** de datos existentes

## 🏗️ Arquitectura Implementada

### 1. Base de Datos (SQL Server)

#### Tablas Principales:
```sql
- ANCI_SECCIONES_CONFIG      -- Define todas las secciones (fijas + taxonomías)
- INCIDENTES_SECCIONES_DATOS  -- Almacena datos JSON por sección
- INCIDENTES_COMENTARIOS      -- Hasta 6 comentarios por sección
- INCIDENTES_ARCHIVOS         -- Hasta 10 archivos de 10MB por sección
- INCIDENTES_AUDITORIA        -- Registro completo de cambios
```

#### Características:
- **Secciones dinámicas**: Se ajustan según tipo de empresa
- **Almacenamiento JSON**: Permite campos flexibles sin cambiar esquema
- **Límites configurables**: Por sección (comentarios, archivos, tamaño)
- **Auditoría completa**: Todos los cambios quedan registrados

### 2. Backend (Python/Flask)

#### Módulo Principal: `sistema_dinamico.py`
```python
class SistemaDinamicoIncidentes:
    - obtener_secciones_empresa()    # 6-41 secciones según tipo
    - crear_incidente_completo()     # Crea con todas las secciones aplicables
    - guardar_seccion()              # Guarda datos de una sección
    - agregar_comentario()           # Máx 6 por sección
    - subir_archivo()                # Máx 10 de 10MB por sección
    - cargar_incidente_completo()    # Carga todo con secciones dinámicas
    - eliminar_incidente_completo()  # Elimina todo sin dejar rastro
```

#### API Endpoints: `incidente_dinamico_views.py`
- `GET /api/incidente-dinamico/secciones-empresa/<id>` - Obtiene secciones aplicables
- `POST /api/incidente-dinamico/crear` - Crea incidente con estructura dinámica
- `PUT /api/incidente-dinamico/<id>/seccion/<sid>` - Guarda sección específica
- `POST /api/incidente-dinamico/<id>/seccion/<sid>/comentario` - Agrega comentario
- `POST /api/incidente-dinamico/<id>/seccion/<sid>/archivo` - Sube archivo
- `GET /api/incidente-dinamico/<id>` - Carga incidente completo
- `DELETE /api/incidente-dinamico/<id>` - Elimina completamente

### 3. Frontend (Vue.js)

#### Componente: `IncidenteDinamico.vue`
- **Acordeones dinámicos**: Se generan según tipo de empresa
- **Indicadores visuales**:
  - Color verde para secciones con contenido
  - Badges con contadores de comentarios/archivos
  - Barra de progreso general
- **Gestión de archivos**: Drag & drop, validación de tamaño
- **Auto-guardado**: Al cambiar campos

## 📊 Flujo de Trabajo

### Crear Incidente:
1. Sistema detecta tipo de empresa (OIV/PSE/AMBAS)
2. Carga solo las secciones aplicables (6-41)
3. Crea estructura inicial vacía
4. Usuario llena solo lo necesario

### Editar Incidente:
1. Carga secciones dinámicamente
2. Muestra acordeones coloreados según contenido
3. Abre automáticamente secciones con datos
4. Permite agregar comentarios/archivos respetando límites

### Visualización:
- **OIV**: ~20-25 acordeones
- **PSE**: ~15-20 acordeones  
- **AMBAS**: 41 acordeones (6 fijas + 35 taxonomías)

## 🔄 Migración de Datos

Script incluido: `migrar_a_sistema_dinamico.py`
- Migra incidentes existentes
- Mapea evidencias a secciones correctas
- Convierte comentarios de taxonomías
- Preserva toda la información histórica

## 💡 Ventajas del Sistema

### 1. **Simplicidad**:
- Un único formulario grande tratado como acordeones
- No hay complejidad de relaciones múltiples
- Fácil de entender y mantener

### 2. **Escalabilidad**:
- Agregar taxonomías = agregar filas en config
- Cambiar campos = modificar JSON
- Sin cambios de código al evolucionar ANCI

### 3. **Performance**:
- Carga solo secciones necesarias
- Índices optimizados
- Queries eficientes con JSON

### 4. **Usabilidad**:
- Interfaz clara con indicadores visuales
- Progreso visible
- Límites claros (6 comentarios, 10 archivos)

## 🚦 Estado de Implementación

✅ **Completado**:
- Scripts SQL para crear estructura
- Módulo Python sistema_dinamico.py
- API endpoints completos
- Componente Vue.js con acordeones
- Script de migración

⏳ **Pendiente**:
- Integrar con app principal (registrar blueprints)
- Ejecutar scripts SQL en BD
- Probar con datos reales
- Ajustar estilos visuales

## 📝 Próximos Pasos

1. **Ejecutar en BD**:
   ```bash
   sqlcmd -S servidor -d BD -i sql/crear_sistema_dinamico.sql
   ```

2. **Registrar módulos**:
   ```python
   # En app/__init__.py
   from .views.incidente_dinamico_views import incidente_dinamico_bp
   app.register_blueprint(incidente_dinamico_bp)
   ```

3. **Migrar datos**:
   ```bash
   python migrations/migrar_a_sistema_dinamico.py
   ```

4. **Actualizar rutas frontend** para usar nuevo componente

## 🎯 Mejoras Identificadas

1. **Cache de secciones**: Para no consultarlas cada vez
2. **Bulk operations**: Guardar múltiples secciones a la vez
3. **Plantillas**: Prellenar secciones comunes
4. **Exportación**: Generar PDF con formato ANCI
5. **Validaciones**: Campos obligatorios por tipo empresa
6. **Búsqueda**: Dentro de todas las secciones
7. **Comparación**: Ver cambios entre versiones
8. **Dashboard**: Métricas por tipo de sección

---

**Nota**: Este sistema es mucho más simple que múltiples tablas relacionadas, pero igual de poderoso. La clave está en usar JSON para flexibilidad y acordeones para UI clara.
# VALIDACIÓN DEL SISTEMA DE INCIDENTES

## 1. CAPACIDAD DE CAMPOS DE COMENTARIOS

### Estado Actual
- Los campos de texto están siendo truncados a 2000-4000 caracteres en el backend
- SQL Server soporta NVARCHAR(MAX) que permite hasta 2GB de texto
- **ACCIÓN REQUERIDA**: Modificar la base de datos para usar NVARCHAR(MAX) en campos de comentarios

### Cambios Realizados
```python
# En incidentes_crear.py - Aumentado límites:
'descripcion_detallada': sanitizar_string(datos.get('2.1', ''), 4000),  # Antes 2000
'impacto_preliminar': sanitizar_string(datos.get('2.2', ''), 4000),
'sistemas_afectados': sanitizar_string(datos.get('2.3', ''), 4000),
'medidas_contencion': sanitizar_string(datos.get('5.1', ''), 4000),
```

### Recomendación SQL
```sql
-- Ejecutar en la base de datos:
ALTER TABLE Incidentes ALTER COLUMN DescripcionInicial NVARCHAR(MAX);
ALTER TABLE Incidentes ALTER COLUMN AnciImpactoPreliminar NVARCHAR(MAX);
ALTER TABLE Incidentes ALTER COLUMN SistemasAfectados NVARCHAR(MAX);
ALTER TABLE Incidentes ALTER COLUMN ServiciosInterrumpidos NVARCHAR(MAX);
ALTER TABLE Incidentes ALTER COLUMN AccionesInmediatas NVARCHAR(MAX);
ALTER TABLE Incidentes ALTER COLUMN CausaRaiz NVARCHAR(MAX);
ALTER TABLE Incidentes ALTER COLUMN LeccionesAprendidas NVARCHAR(MAX);
ALTER TABLE Incidentes ALTER COLUMN PlanMejora NVARCHAR(MAX);
```

## 2. RECUPERACIÓN DE ESTRUCTURA BASE AL EDITAR

### Estado Actual
✅ **IMPLEMENTADO** - Nueva función `obtener_estructura_base_incidente()` que:
- Recupera todos los campos del incidente
- Obtiene taxonomías con justificación y descripción separadas
- Lista archivos asociados por sección
- Mantiene la estructura original para edición

### Características:
- Los comentarios de taxonomías se parsean para separar justificación y descripción
- Los archivos se organizan por sección
- Se incluye información de tamaño de archivos

## 3. ALMACENAMIENTO DE ARCHIVOS EN CARPETAS SEPARADAS

### Estado Actual
✅ **IMPLEMENTADO CORRECTAMENTE**
- Estructura: `/uploads/evidencias/{indice_unico}/`
- Cada incidente tiene su propia carpeta usando el IDVisible único
- Nomenclatura: `{indice_unico}_{seccion}_{numero}_{timestamp}.{extension}`

### Ejemplo:
```
/uploads/
  /evidencias/
    /1_12345678_1_1_INCIDENTE_NUEVO/
      - 1_12345678_1_1_INCIDENTE_NUEVO_1_1_20241218120530.pdf
      - 1_12345678_1_1_INCIDENTE_NUEVO_2_1_20241218120545.jpg
      - 1_12345678_1_1_INCIDENTE_NUEVO_3_2_20241218120600.docx
```

## 4. PROTECCIÓN CONTRA PÉRDIDA DE DATOS

### Estado Actual
⚠️ **PARCIALMENTE IMPLEMENTADO**

### Implementado:
- Guardado de borrador en localStorage
- Función básica de recuperación

### FALTA IMPLEMENTAR:
```javascript
// Agregar al componente AcordeonIncidenteMejorado.vue:

// 1. Prevención de cierre accidental
window.addEventListener('beforeunload', (e) => {
  if (cambiosSinGuardar) {
    e.preventDefault()
    e.returnValue = '¿Hay cambios sin guardar?'
  }
})

// 2. Guardado automático cada 30 segundos
setInterval(() => {
  if (cambiosSinGuardar) guardarBorrador()
}, 30000)

// 3. Atajos de teclado
document.addEventListener('keydown', (e) => {
  // Ctrl+S para guardar
  if (e.ctrlKey && e.key === 's') {
    e.preventDefault()
    guardarIncidente()
  }
  // Prevenir ESC si hay cambios
  if (e.key === 'Escape' && cambiosSinGuardar) {
    e.preventDefault()
  }
})

// 4. Recuperación ante cortes
const recuperarSesion = () => {
  const sesion = localStorage.getItem(`incidente_sesion_${incidenteId}`)
  if (sesion) {
    const datos = JSON.parse(sesion)
    if (confirm('Se detectó una sesión anterior. ¿Recuperar?')) {
      restaurarDatos(datos)
    }
  }
}
```

## 5. PROCESO PARA INFORME ANCI

### Estado Actual
⚠️ **DISEÑO PENDIENTE**

### Propuesta de Implementación:

#### A. Estructura de Datos ANCI
```python
class InformeANCI:
    def __init__(self, incidente_id):
        self.incidente = obtener_estructura_base_incidente(incidente_id)
        self.archivos_anci = []
        self.fecha_generacion = datetime.now()
    
    def seleccionar_archivos_para_anci(self, archivos_seleccionados):
        """Marca qué archivos del incidente se incluirán en ANCI"""
        for archivo_id in archivos_seleccionados:
            self.archivos_anci.append({
                'archivo_original': archivo_id,
                'incluido_en_anci': True,
                'seccion_anci': self.mapear_seccion_anci(archivo_id)
            })
    
    def generar_paquete_anci(self):
        """Genera ZIP con informe PDF y archivos seleccionados"""
        # 1. Generar PDF del informe
        # 2. Copiar archivos seleccionados
        # 3. Crear ZIP con estructura ANCI
        # 4. Firmar digitalmente si es necesario
```

#### B. Tabla de Relación ANCI-Archivos
```sql
CREATE TABLE ANCI_ARCHIVOS (
    AnciArchivoID INT PRIMARY KEY IDENTITY(1,1),
    ReporteAnciID INT NOT NULL,
    IncidenteID INT NOT NULL,
    ArchivoOriginal NVARCHAR(500),
    SeccionANCI NVARCHAR(50),
    IncluidoEnReporte BIT DEFAULT 1,
    FechaIncluido DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (ReporteAnciID) REFERENCES REPORTES_ANCI(ReporteAnciID),
    FOREIGN KEY (IncidenteID) REFERENCES Incidentes(IncidenteID)
);
```

#### C. Proceso de Generación
1. Usuario selecciona archivos relevantes para ANCI
2. Sistema copia archivos a carpeta temporal ANCI
3. Genera informe PDF con datos estructurados
4. Crea paquete ZIP con nomenclatura ANCI
5. Registra en base de datos qué archivos se incluyeron

## RESUMEN DE ACCIONES PENDIENTES

### CRÍTICAS:
1. **Base de Datos**: Modificar campos a NVARCHAR(MAX)
2. **Frontend**: Implementar protección completa contra pérdida de datos
3. **Backend**: Crear endpoint de actualización que preserve estructura base

### IMPORTANTES:
4. **ANCI**: Diseñar e implementar proceso completo
5. **Validación**: Agregar validación de tamaño de archivos (máx 50MB)
6. **Seguridad**: Implementar encriptación de archivos sensibles

### RECOMENDACIONES:
7. **Backup**: Sistema de respaldo automático cada 24 horas
8. **Auditoría**: Log de todos los cambios en incidentes
9. **Notificaciones**: Alertas por email en cambios críticos
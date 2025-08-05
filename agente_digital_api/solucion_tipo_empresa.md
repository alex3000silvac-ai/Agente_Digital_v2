# SOLUCIÓN CRÍTICA: Inconsistencia Tipo de Empresa OIV/PSE

## PROBLEMA IDENTIFICADO

El incidente 5 muestra inconsistencia en el tipo de empresa:
- En la base de datos: La empresa es tipo **PSE** (Proveedor de Servicios Esenciales)
- En el frontend: A veces aparece como **OIV** (Operador de Infraestructura Vital)

## CAUSA RAÍZ

1. El frontend está usando `incidente.TipoEmpresa` que no existe en la tabla INCIDENTES
2. El tipo de empresa está en la tabla EMPRESAS, no en INCIDENTES
3. El backend ya fue modificado para incluir TipoEmpresa desde EMPRESAS

## SOLUCIONES IMPLEMENTADAS

### 1. Backend (✅ COMPLETADO)

Modificado `/app/modules/admin/incidentes.py` líneas 131-141:
```python
# Agregar tipo de empresa desde la tabla EMPRESAS
if incidente_data.get('EmpresaID'):
    cursor.execute("""
        SELECT TipoEmpresa, RazonSocial 
        FROM EMPRESAS 
        WHERE EmpresaID = ?
    """, (incidente_data['EmpresaID'],))
    empresa_row = cursor.fetchone()
    if empresa_row:
        incidente_data['TipoEmpresa'] = empresa_row[0]
        incidente_data['RazonSocial'] = empresa_row[1]
```

### 2. Endpoint de Estadísticas (✅ COMPLETADO)

Creado nuevo endpoint `/api/admin/incidentes/{id}/estadisticas` que retorna:
- TotalEvidencias: 5 (archivos en INCIDENTES_ARCHIVOS)
- TotalComentarios: 0 (en INCIDENTES_COMENTARIOS + COMENTARIOS_TAXONOMIA)
- Completitud: % basado en campos llenos

### 3. Frontend - Verificación Necesaria

El frontend debe:
1. Cargar correctamente el TipoEmpresa del endpoint principal
2. Usar este valor consistentemente en todos los cálculos de plazos
3. Mostrar las estadísticas del nuevo endpoint

## PLAZOS LEGALES CORRECTOS

Para empresa tipo **PSE**:
- **Informe Preliminar**: 72 HORAS
- **Informe Completo**: 72 HORAS
- **Informe Final**: 30 DÍAS

Para empresa tipo **OIV**:
- **Informe Preliminar**: 24 HORAS ⚠️
- **Informe Completo**: 72 HORAS
- **Informe Final**: 30 DÍAS

## ACCIONES PENDIENTES

1. Verificar que el frontend esté usando el TipoEmpresa correcto
2. Asegurar que los plazos se calculen según el tipo real (PSE)
3. Verificar que las estadísticas se muestren correctamente
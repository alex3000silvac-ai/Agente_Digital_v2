# Solución para el Historial de Informes ANCI

## Problema
El cuadro "Historial de informes generados" no muestra información porque:
1. La tabla `INFORMES_ANCI` posiblemente no existe
2. No hay registros de informes generados

## Solución Implementada

### 1. Ajuste del endpoint
Se corrigió el endpoint `/api/informes-anci/historial/<incidente_id>` para:
- Retornar el formato esperado por el frontend: `{'informes': []}`
- Mapear los campos correctamente
- Manejar el caso cuando la tabla no existe

### 2. Script SQL
Se creó `scripts/crear_tabla_informes_anci.sql` para crear la tabla si no existe.

## Pasos para aplicar la solución:

### 1. Ejecutar el script SQL
```sql
-- En SQL Server Management Studio o tu cliente SQL
-- Conectar a la base de datos Agente_Digital
-- Ejecutar el contenido de scripts/crear_tabla_informes_anci.sql
```

### 2. Verificar en el navegador
1. Ir a un incidente ANCI
2. Hacer clic en la tarjeta "Informe ANCI"
3. El historial debería mostrar:
   - "No hay informes generados" si es la primera vez
   - La lista de informes si ya se han generado algunos

### 3. Generar un informe de prueba
1. En la sección "Generar Nuevo Informe"
2. Seleccionar tipo (Preliminar, Completo o Final)
3. Hacer clic en "Generar Informe"
4. El informe debería aparecer en el historial

## ¿Cómo funciona?

Cuando se genera un informe:
1. El sistema crea el PDF
2. Guarda un registro en la tabla `INFORMES_ANCI`
3. El historial consulta esta tabla y muestra los informes

## Verificación
Para verificar que todo funciona:
1. Revisar la consola del navegador (F12)
2. Buscar el log: "✅ Historial cargado: X informes"
3. Si hay error, aparecerá en la consola
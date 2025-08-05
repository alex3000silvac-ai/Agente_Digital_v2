"""
Script para generar mensajes de debug para el frontend
"""

print("=" * 70)
print("INSTRUCCIONES DE DEBUG PARA EL FRONTEND")
print("=" * 70)

print("\n1. ABRIR LA CONSOLA DEL NAVEGADOR (F12)")
print("   - Ve a la pestaña 'Console'")
print("   - Recarga la página de detalle del incidente")

print("\n2. BUSCAR ESTOS MENSAJES EN LA CONSOLA:")
print("   🚀 Acordeón montado con props:")
print("   🔍 Verificando condiciones para cargar:")
print("   📥 Modo edición: cargando datos completos del servidor...")
print("   🔄 Cargando incidente X para edición")

print("\n3. SI NO VES 'Modo edición: cargando datos completos':")
print("   - El componente no está detectando el modo editar")
print("   - Verificar que incidenteId tenga valor")

print("\n4. SI VES 'FormData cargado desde formData: 0 campos':")
print("   - El backend no está devolviendo los datos correctamente")
print("   - Debe aparecer '⚠️ No hay formData, mapeando campos directamente'")

print("\n5. VERIFICAR RESPUESTA DEL SERVIDOR:")
print("   - En la pestaña 'Network' busca: /api/admin/incidentes/5")
print("   - Click en la petición y ve a 'Response'")
print("   - Debe contener:")
print("     * archivos: { seccion_2: [...], seccion_3: [...] }")
print("     * taxonomias_seleccionadas: [...]")

print("\n6. VERIFICAR ARCHIVOS:")
print("   - Buscar: '📁 Estructura de archivos recibida:'")
print("   - Buscar: '✅ Archivos restaurados:'")
print("   - Si dice 'seccion2: 0' significa que no se cargaron")

print("\n7. VERIFICAR TAXONOMÍAS:")
print("   - Buscar: '🏷️ Taxonomías recibidas del servidor:'")
print("   - Buscar: '✅ X taxonomías seleccionadas cargadas'")

print("\n8. SI TODO FALLA, EJECUTAR EN CONSOLA:")
print("""
// Verificar el componente
const comp = document.querySelector('.acordeon-incidente-mejorado').__vueParentComponent
console.log('Props:', comp.props)
console.log('Archivos S2:', comp.ctx.archivosSeccion2)
console.log('Archivos S3:', comp.ctx.archivosSeccion3)
console.log('Taxonomías:', comp.ctx.taxonomiasSeleccionadas)
""")

print("\n9. TAMBIÉN PUEDES EJECUTAR:")
print("""
// Ver el estado del formulario
console.log('FormData:', comp.ctx.formData)
console.log('Modo:', comp.props.modo)
console.log('IncidenteId:', comp.props.incidenteId)
""")

print("\n" + "=" * 70)
print("Si ninguno de estos pasos funciona, el problema está en:")
print("1. El servidor Flask no está corriendo")
print("2. El token JWT ha expirado")
print("3. La URL del incidente es incorrecta")
print("=" * 70)
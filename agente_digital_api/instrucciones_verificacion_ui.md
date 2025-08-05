# INSTRUCCIONES PARA VERIFICAR TAXONOMÍAS EN EL UI

## 1. VERIFICAR QUE EL SERVIDOR ESTÉ CORRIENDO
```bash
cd /mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api
python3 run.py
```

## 2. ABRIR EL NAVEGADOR
1. Ve a http://localhost:5173
2. Inicia sesión con:
   - Email: admin@agentedigital.cl
   - Password: Admin123!

## 3. VERIFICAR EN LA CONSOLA DEL NAVEGADOR

### A. Navegar al incidente 25:
```
http://localhost:5173/incidente-detalle/25
```

### B. Ejecutar en la consola (F12):
```javascript
// 1. Verificar datos del endpoint
const response = await fetch('http://localhost:5002/api/incidente/25/cargar_completo', {
  headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
});
const data = await response.json();

console.log('=== DATOS DEL SERVIDOR ===');
console.log('Incidente:', data.incidente);
console.log('Taxonomías seleccionadas:', data.incidente.taxonomias_seleccionadas);
console.log('Evidencias taxonomías:', data.incidente.evidencias_taxonomias);

// 2. Verificar el componente Vue
const app = document.querySelector('#app').__vue_app__;
const vm = app._instance.subTree.component.subTree.component;

console.log('=== DATOS EN EL COMPONENTE ===');
vm.debugTaxonomias();

// 3. Verificar visualmente
const taxElements = document.querySelectorAll('.taxonomia-item');
console.log('=== ELEMENTOS EN EL DOM ===');
console.log('Total taxonomías en DOM:', taxElements.length);
taxElements.forEach(el => {
  console.log('Taxonomía:', el.dataset.taxonomyId, 'Seleccionada:', el.classList.contains('seleccionada'));
});

// 4. Forzar selección visual para probar estilos
const firstTax = document.querySelector('.taxonomia-item');
if (firstTax) {
  firstTax.classList.add('seleccionada');
  console.log('✅ Primera taxonomía marcada como seleccionada para ver el estilo');
}
```

## 4. VERIFICAR PROBLEMAS COMUNES

### A. Si las taxonomías no se cargan:
```javascript
// Ver qué taxonomías están disponibles
const disponibles = vm.taxonomiasDisponibles;
console.log('Taxonomías disponibles:', disponibles);

// Ver qué taxonomías están seleccionadas
const seleccionadas = vm.taxonomiasSeleccionadas;
console.log('Taxonomías seleccionadas:', seleccionadas);
```

### B. Si los archivos no se muestran:
```javascript
// Ver archivos por taxonomía
vm.taxonomiasSeleccionadas.forEach(tax => {
  console.log(`Taxonomía ${tax.id}:`, tax.archivos);
});
```

## 5. SOLUCIÓN TEMPORAL SI NO SE VEN LAS TAXONOMÍAS

Si las taxonomías no se están cargando, ejecutar:
```javascript
// Forzar recarga de datos
await vm.cargarIncidenteExistente();
```

## 6. QUÉ DEBERÍAS VER

1. **Taxonomías seleccionadas**: Deberían verse con fondo azul degradado
2. **Archivos adjuntos**: Deberían aparecer debajo de cada taxonomía
3. **Justificación y descripción**: Deberían mostrarse en el formulario de cada taxonomía

## 7. REPORTAR RESULTADOS

Por favor ejecuta estos comandos y dime:
1. ¿Qué muestra `data.incidente.taxonomias_seleccionadas`?
2. ¿Qué muestra `vm.debugTaxonomias()`?
3. ¿Las taxonomías tienen la clase `seleccionada`?
4. ¿Se ven con fondo azul cuando forzas la clase?
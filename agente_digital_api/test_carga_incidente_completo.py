"""
Script para probar la carga completa de un incidente con archivos
"""

import requests
import json
from pprint import pprint

# Configuración
BASE_URL = "http://localhost:5000"
INCIDENTE_ID = 5

# Token de prueba
token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGV4YW1wbGUuY29tIiwiZXhwIjoxNzQyNTcwMDAwfQ.test"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("=" * 70)
print("PRUEBA DE CARGA COMPLETA DE INCIDENTE")
print("=" * 70)

print(f"\n1. Cargando incidente {INCIDENTE_ID} con endpoint admin...")
print("-" * 50)

try:
    response = requests.get(
        f"{BASE_URL}/api/admin/incidentes/{INCIDENTE_ID}",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Incidente cargado exitosamente")
        
        # Información básica
        print(f"\n📋 INFORMACIÓN BÁSICA:")
        print(f"   - ID: {data.get('IncidenteID')}")
        print(f"   - Título: {data.get('Titulo')}")
        print(f"   - Estado: {data.get('EstadoActual')}")
        print(f"   - Tiene Reporte ANCI: {data.get('TieneReporteANCI')}")
        
        # Verificar formData
        if 'formData' in data:
            print(f"\n📝 FORM DATA:")
            print(f"   - Total campos: {len(data['formData'])}")
            print(f"   - Campo 1.2 (Título): {data['formData'].get('1.2', 'NO ENCONTRADO')}")
            print(f"   - Campo 2.1 (Descripción): {data['formData'].get('2.1', 'NO ENCONTRADO')[:50]}...")
        else:
            print("\n❌ NO SE ENCONTRÓ formData")
        
        # Verificar archivos
        if 'archivos' in data:
            print(f"\n📎 ARCHIVOS:")
            archivos = data['archivos']
            
            if isinstance(archivos, dict):
                print(f"   - Sección 2: {len(archivos.get('seccion_2', []))} archivos")
                print(f"   - Sección 3: {len(archivos.get('seccion_3', []))} archivos")
                print(f"   - Sección 5: {len(archivos.get('seccion_5', []))} archivos")
                print(f"   - Sección 6: {len(archivos.get('seccion_6', []))} archivos")
                
                # Mostrar detalles de archivos
                for seccion, archivos_seccion in archivos.items():
                    if archivos_seccion and seccion != 'taxonomias':
                        print(f"\n   📁 {seccion}:")
                        for archivo in archivos_seccion[:2]:  # Mostrar máximo 2
                            print(f"      - {archivo.get('nombre')} ({archivo.get('tamaño', 0)/1024:.1f} KB)")
                            print(f"        ID: {archivo.get('id')}")
                            print(f"        Existente: {archivo.get('existente')}")
                            print(f"        Origen: {archivo.get('origen')}")
            else:
                print(f"   - Estructura inesperada: {type(archivos)}")
        else:
            print("\n❌ NO SE ENCONTRARON archivos")
        
        # Verificar taxonomías
        if 'taxonomias_seleccionadas' in data:
            print(f"\n🏷️ TAXONOMÍAS:")
            print(f"   - Total: {len(data['taxonomias_seleccionadas'])}")
            for tax in data['taxonomias_seleccionadas'][:2]:  # Mostrar máximo 2
                print(f"   - {tax.get('nombre')} (ID: {tax.get('id')})")
                print(f"     Justificación: {tax.get('justificacion', 'Sin justificación')[:50]}...")
        else:
            print("\n❌ NO SE ENCONTRARON taxonomías")
        
        # Guardar respuesta completa para análisis
        with open('respuesta_incidente_completo.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("\n💾 Respuesta completa guardada en: respuesta_incidente_completo.json")
        
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error en la petición: {e}")

print("\n" + "=" * 70)
print("PRUEBA COMPLETADA")
print("=" * 70)
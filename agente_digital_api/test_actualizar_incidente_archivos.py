"""
Script para probar la actualización de incidentes con archivos
"""

import requests
import json
import os

# Configuración
BASE_URL = "http://localhost:5000"
INCIDENTE_ID = 5

# Token de prueba (en producción esto vendría del login)
token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGV4YW1wbGUuY29tIiwiZXhwIjoxNzQyNTcwMDAwfQ.test"

# Headers base
headers = {
    "Authorization": f"Bearer {token}"
}

print("=" * 70)
print("PRUEBA DE ACTUALIZACIÓN DE INCIDENTE CON ARCHIVOS")
print("=" * 70)

# 1. Primero, obtener los datos actuales del incidente
print(f"\n1. Obteniendo datos del incidente {INCIDENTE_ID}...")
print("-" * 50)

try:
    response = requests.get(
        f"{BASE_URL}/api/admin/incidentes/{INCIDENTE_ID}",
        headers=headers
    )
    
    if response.status_code == 200:
        incidente_actual = response.json()
        print("✅ Incidente cargado exitosamente")
        print(f"   - Título: {incidente_actual.get('Titulo')}")
        print(f"   - Estado: {incidente_actual.get('EstadoActual')}")
    else:
        print(f"❌ Error al cargar incidente: {response.status_code}")
        print(response.text)
        exit(1)
        
except Exception as e:
    print(f"❌ Error en la petición: {e}")
    exit(1)

# 2. Actualizar el incidente SIN archivos (solo datos)
print(f"\n2. Actualizando incidente SIN archivos...")
print("-" * 50)

datos_actualizacion = {
    "1.2": incidente_actual.get("Titulo") + " - ACTUALIZADO",
    "1.5": "Alta",
    "2.1": "Descripción actualizada desde el script de prueba",
    "taxonomias_seleccionadas": [],
    "archivos": {
        "seccion_2": [],
        "seccion_3": [],
        "seccion_5": [],
        "seccion_6": []
    },
    "archivos_eliminados": []
}

try:
    response = requests.put(
        f"{BASE_URL}/api/incidentes/{INCIDENTE_ID}/actualizar",
        headers={**headers, "Content-Type": "application/json"},
        json=datos_actualizacion
    )
    
    if response.status_code == 200:
        print("✅ Incidente actualizado exitosamente (sin archivos)")
    else:
        print(f"❌ Error al actualizar: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error en la petición: {e}")

# 3. Crear un archivo de prueba
print(f"\n3. Creando archivo de prueba...")
print("-" * 50)

archivo_prueba = "archivo_prueba.txt"
with open(archivo_prueba, "w") as f:
    f.write("Este es un archivo de prueba para el incidente.")
    f.write(f"\nIncidente ID: {INCIDENTE_ID}")
    f.write(f"\nFecha: {incidente_actual.get('FechaCreacion')}")

print(f"✅ Archivo de prueba creado: {archivo_prueba}")

# 4. Actualizar el incidente CON archivos usando FormData
print(f"\n4. Actualizando incidente CON archivos...")
print("-" * 50)

try:
    # Preparar FormData
    files = {
        'archivo_seccion_2_campo_1': ('archivo_prueba.txt', open(archivo_prueba, 'rb'), 'text/plain')
    }
    
    # Datos como parte del form
    data = {
        'datos': json.dumps(datos_actualizacion)
    }
    
    response = requests.put(
        f"{BASE_URL}/api/incidentes/{INCIDENTE_ID}/actualizar",
        headers={"Authorization": f"Bearer {token}"},  # Solo auth, no Content-Type
        files=files,
        data=data
    )
    
    if response.status_code == 200:
        print("✅ Incidente actualizado exitosamente CON archivos")
        resultado = response.json()
        print(f"   - Mensaje: {resultado.get('mensaje')}")
    else:
        print(f"❌ Error al actualizar con archivos: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error en la petición: {e}")
finally:
    # Limpiar archivo de prueba
    if os.path.exists(archivo_prueba):
        os.remove(archivo_prueba)

# 5. Probar endpoint específico de subida de archivos
print(f"\n5. Probando endpoint específico de subida de archivos...")
print("-" * 50)

# Crear otro archivo de prueba
archivo_prueba2 = "documento_prueba.txt"
with open(archivo_prueba2, "w") as f:
    f.write("Documento de prueba para endpoint específico de subida.")

try:
    with open(archivo_prueba2, 'rb') as f:
        files = {'archivo': ('documento_prueba.txt', f, 'text/plain')}
        data = {
            'seccion_id': 3,
            'campo_id': 1
        }
        
        response = requests.post(
            f"{BASE_URL}/api/incidentes/{INCIDENTE_ID}/subir-archivo",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            print("✅ Archivo subido exitosamente")
            resultado = response.json()
            print(f"   - ID: {resultado['archivo']['id']}")
            print(f"   - Nombre: {resultado['archivo']['nombre']}")
            print(f"   - Tamaño: {resultado['archivo']['tamaño']} bytes")
        else:
            print(f"❌ Error al subir archivo: {response.status_code}")
            print(response.text)
            
except Exception as e:
    print(f"❌ Error en la petición: {e}")
finally:
    # Limpiar archivo de prueba
    if os.path.exists(archivo_prueba2):
        os.remove(archivo_prueba2)

print("\n" + "=" * 70)
print("PRUEBA COMPLETADA")
print("=" * 70)
print("\nRECOMENDACIONES:")
print("1. Verificar en la base de datos que los archivos se guardaron en INCIDENTES_ARCHIVOS")
print("2. Verificar que los archivos físicos se crearon en el directorio de uploads")
print("3. Probar la descarga de archivos desde el frontend")
print("4. Verificar que la eliminación de archivos funciona correctamente")
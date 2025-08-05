"""
Script para probar el endpoint administrativo de incidentes con JWT
"""

import requests
import json

# Configuración
BASE_URL = "http://localhost:5000"
INCIDENTE_ID = 5

# Primero obtener un token (simulado para pruebas)
# En producción esto vendría del login
token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGV4YW1wbGUuY29tIiwiZXhwIjoxNzQyNTcwMDAwfQ.test"

# Headers con autenticación
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("=" * 70)
print("PRUEBA DE ENDPOINT ADMINISTRATIVO DE INCIDENTES")
print("=" * 70)

# Probar el endpoint GET /api/admin/incidentes/<id>
print(f"\n1. Probando GET /api/admin/incidentes/{INCIDENTE_ID}")
print("-" * 50)

try:
    response = requests.get(
        f"{BASE_URL}/api/admin/incidentes/{INCIDENTE_ID}",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print("\nDatos del incidente:")
        print(f"- ID: {data.get('IncidenteID')}")
        print(f"- Título: {data.get('Titulo')}")
        print(f"- Estado: {data.get('EstadoActual')}")
        print(f"- Empresa ID: {data.get('EmpresaID')}")
        print(f"- Tiene Reporte ANCI: {data.get('TieneReporteANCI')}")
        
        if data.get('archivos'):
            print(f"\nArchivos adjuntos: {len(data['archivos'])} secciones")
    else:
        print(f"\nError: {response.text}")
        
except Exception as e:
    print(f"Error en la petición: {e}")

# Probar validación para ANCI
print(f"\n\n2. Probando GET /api/admin/incidentes/{INCIDENTE_ID}/validar-para-anci")
print("-" * 50)

try:
    response = requests.get(
        f"{BASE_URL}/api/admin/incidentes/{INCIDENTE_ID}/validar-para-anci",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nValidación ANCI:")
        print(f"- Válido: {data.get('valido')}")
        print(f"- Mensaje: {data.get('mensaje')}")
    else:
        print(f"\nError: {response.text}")
        
except Exception as e:
    print(f"Error en la petición: {e}")

print("\n" + "=" * 70)
print("PRUEBA COMPLETADA")
print("=" * 70)
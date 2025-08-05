#!/usr/bin/env python3
"""
Test del endpoint de estadísticas
"""
import requests

# Test del endpoint
url = "http://localhost:5000/api/admin/incidentes/5/estadisticas"

try:
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
    
# Test del endpoint principal con tipo empresa
url2 = "http://localhost:5000/api/admin/incidentes/5"
try:
    response2 = requests.get(url2)
    print(f"\nIncidente completo:")
    print(f"Status: {response2.status_code}")
    data = response2.json()
    print(f"TipoEmpresa: {data.get('TipoEmpresa')}")
    print(f"RazonSocial: {data.get('RazonSocial')}")
except Exception as e:
    print(f"Error: {e}")
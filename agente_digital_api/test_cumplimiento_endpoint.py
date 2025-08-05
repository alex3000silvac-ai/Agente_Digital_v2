#!/usr/bin/env python3
"""
Script para probar el endpoint de cumplimiento
"""

import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:5000"

def test_crear_cumplimiento():
    """Probar la creación de un cumplimiento"""
    
    print("=" * 80)
    print("PRUEBA DE ENDPOINT DE CUMPLIMIENTO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Datos de prueba (mismos que el frontend está enviando)
    payload = {
        "EmpresaID": "3",
        "ObligacionID": "OBL_002_REP_007",
        "Estado": "Pendiente",
        "PorcentajeAvance": 5,
        "Responsable": "",
        "FechaTermino": None,
        "ObservacionesCiberseguridad": None,
        "ObservacionesLegales": None
    }
    
    print(f"\nPayload de prueba:")
    print(json.dumps(payload, indent=2))
    
    try:
        # Hacer la petición POST
        response = requests.post(
            f"{BASE_URL}/api/admin/cumplimiento",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nCódigo de respuesta: {response.status_code}")
        print(f"Respuesta: {response.text}")
        
        if response.status_code == 409:
            print("\n⚠️ Conflicto detectado - Ya existe un registro")
        elif response.status_code == 201:
            print("\n✅ Cumplimiento creado exitosamente")
        elif response.status_code == 200:
            print("\n✅ Cumplimiento actualizado exitosamente")
        else:
            print(f"\n❌ Error inesperado: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ No se pudo conectar al servidor")
        print("   Asegúrese de que el servidor Flask esté ejecutándose")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")

if __name__ == '__main__':
    test_crear_cumplimiento()
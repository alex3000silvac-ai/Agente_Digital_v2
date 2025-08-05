#!/usr/bin/env python3
"""
Script para probar el endpoint de historial
"""

import requests
import json

# URL del servidor
BASE_URL = "http://localhost:5000"

def test_historial():
    """Probar endpoint de historial"""
    
    # Probar con diferentes IDs de cumplimiento
    cumplimiento_ids = [1, 2, 3]
    
    for cumpl_id in cumplimiento_ids:
        print(f"\n{'=' * 60}")
        print(f"PROBANDO HISTORIAL PARA CUMPLIMIENTO ID: {cumpl_id}")
        print(f"{'=' * 60}")
        
        try:
            # Hacer la solicitud
            response = requests.get(f"{BASE_URL}/api/admin/cumplimiento/{cumpl_id}/historial")
            
            print(f"📊 Status: {response.status_code}")
            print(f"📝 Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Respuesta exitosa")
                print(f"📋 Tipo de respuesta: {type(data)}")
                print(f"📊 Cantidad de registros: {len(data) if isinstance(data, list) else 'No es lista'}")
                
                if isinstance(data, list) and len(data) > 0:
                    print("\nPrimeros 3 registros:")
                    for i, item in enumerate(data[:3]):
                        print(f"\n  Registro {i+1}:")
                        for key, value in item.items():
                            print(f"    {key}: {value}")
                elif isinstance(data, list) and len(data) == 0:
                    print("⚠️ Lista vacía - No hay historial para este cumplimiento")
                else:
                    print(f"📄 Respuesta completa: {json.dumps(data, indent=2)}")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"📄 Respuesta: {response.text}")
                
        except Exception as e:
            print(f"❌ Error en la solicitud: {e}")
    
    # Probar también sin autenticación
    print(f"\n{'=' * 60}")
    print("PROBANDO SIN TOKEN DE AUTENTICACIÓN")
    print(f"{'=' * 60}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/admin/cumplimiento/1/historial")
        print(f"📊 Status sin auth: {response.status_code}")
        if response.status_code == 200:
            print("✅ El endpoint funciona sin autenticación")
        else:
            print("❌ El endpoint requiere autenticación")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_historial()
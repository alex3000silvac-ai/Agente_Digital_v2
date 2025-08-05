#!/usr/bin/env python3
"""
Script para probar el endpoint de acompañamiento
"""

import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:5000"
EMPRESA_ID = 3

def test_acompanamiento_endpoint():
    """Probar el endpoint de acompañamiento"""
    
    print("=" * 80)
    print("PRUEBA DE ENDPOINT DE ACOMPAÑAMIENTO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL: {BASE_URL}/api/admin/empresas/{EMPRESA_ID}/acompanamiento")
    print("=" * 80)
    
    try:
        # Hacer la petición
        response = requests.get(
            f"{BASE_URL}/api/admin/empresas/{EMPRESA_ID}/acompanamiento",
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nCódigo de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                print(f"✅ Respuesta es un array con {len(data)} elementos")
                
                if len(data) > 0:
                    print("\nPrimera obligación:")
                    print("-" * 40)
                    first = data[0]
                    for key, value in first.items():
                        print(f"  {key}: {value}")
                    
                    # Verificar campos esperados
                    expected_fields = [
                        'ObligacionID', 'ArticuloNorma', 'Descripcion',
                        'MedioDeVerificacionSugerido', 'AplicaPara',
                        'Estado', 'PorcentajeAvance', 'Responsable'
                    ]
                    
                    print("\nVerificación de campos:")
                    for field in expected_fields:
                        if field in first:
                            print(f"  ✓ {field}")
                        else:
                            print(f"  ✗ {field} FALTANTE")
                else:
                    print("⚠️ El array está vacío")
            else:
                print(f"❌ Respuesta no es un array: {type(data)}")
                print(json.dumps(data, indent=2))
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Respuesta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar al servidor")
        print("   Asegúrese de que el servidor Flask esté ejecutándose en http://localhost:5000")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_acompanamiento_endpoint()
#!/usr/bin/env python3
"""
Script para verificar el endpoint de informe de cumplimiento
"""

import requests
import json

# URL del servidor
BASE_URL = "http://localhost:5000"

def verificar_informe():
    """Verificar respuesta del endpoint de informe"""
    
    # ID de empresa para probar (basado en el log)
    empresa_id = 3
    
    try:
        print(f"📊 Verificando informe para empresa ID: {empresa_id}")
        print("=" * 60)
        
        # Hacer la solicitud
        response = requests.get(f"{BASE_URL}/api/admin/empresas/{empresa_id}/informe-cumplimiento")
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n📄 Estructura de la respuesta:")
            print(f"Tipo: {type(data)}")
            print(f"Claves principales: {list(data.keys()) if isinstance(data, dict) else 'No es diccionario'}")
            
            if isinstance(data, dict):
                # Verificar cada clave
                for key, value in data.items():
                    print(f"\n🔑 {key}:")
                    if isinstance(value, (dict, list)):
                        print(f"  - Tipo: {type(value)}")
                        if isinstance(value, list):
                            print(f"  - Cantidad de elementos: {len(value)}")
                            if len(value) > 0:
                                print(f"  - Primer elemento: {json.dumps(value[0], indent=2, ensure_ascii=False)[:200]}...")
                        elif isinstance(value, dict):
                            print(f"  - Claves: {list(value.keys())}")
                    else:
                        print(f"  - Valor: {value}")
                        
                # Verificar específicamente obligaciones_detalle
                if 'obligaciones_detalle' in data:
                    print("\n✅ 'obligaciones_detalle' encontrado")
                else:
                    print("\n❌ 'obligaciones_detalle' NO encontrado")
                    print("   El frontend espera esta clave pero no está presente")
                    
            print("\n📝 JSON completo (primeros 1000 caracteres):")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Respuesta: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    verificar_informe()
#\!/usr/bin/env python3
"""
Probar el endpoint de taxonomías
"""

import requests
import json

def test_endpoint():
    """Probar el endpoint de taxonomías"""
    
    print("🔍 PROBANDO ENDPOINT DE TAXONOMÍAS")
    print("=" * 80)
    
    # 1. Probar el endpoint sin autenticación (temporal)
    url = "http://localhost:5000/api/admin/incidentes/25/taxonomias"
    
    print(f"\n📡 Llamando a: {url}")
    
    try:
        response = requests.get(url)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ ÉXITO!")
            print(f"Taxonomías encontradas: {data.get('total', 0)}")
            
            if data.get('taxonomias'):
                for tax in data['taxonomias']:
                    print(f"\n📋 Taxonomía: {tax['id']}")
                    print(f"   Nombre: {tax['nombre']}")
                    print(f"   Justificación: {tax.get('justificacion', 'N/A')}")
                    print(f"   Descripción: {tax.get('descripcionProblema', 'N/A')[:50]}...")
                    print(f"   Archivos: {len(tax.get('archivos', []))}")
                    
                    if tax.get('archivos'):
                        for archivo in tax['archivos']:
                            print(f"      - {archivo['nombreOriginal']}")
            
            # Guardar respuesta para usar en el navegador
            with open('taxonomias_response.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print("\n✅ Respuesta guardada en taxonomias_response.json")
            
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor. ¿Está corriendo en el puerto 5000?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_endpoint()

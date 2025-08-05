#!/usr/bin/env python3
"""
Test directo del endpoint DELETE para verificar si funciona
"""

import requests
import json

def test_delete_endpoint():
    """Prueba el endpoint DELETE directamente"""
    
    incidente_id = 16
    base_url = "http://localhost:5000"
    
    print(f"🧪 TESTING ENDPOINT DELETE PARA INCIDENTE {incidente_id}")
    print("=" * 60)
    
    # 1. Verificar que el incidente existe primero
    print("\n1️⃣ VERIFICANDO QUE EL INCIDENTE EXISTE...")
    try:
        response = requests.get(f"{base_url}/api/admin/empresas/3/incidentes")
        if response.status_code == 200:
            incidentes = response.json()
            incidente_16 = next((inc for inc in incidentes if inc.get('IncidenteID') == 16), None)
            if incidente_16:
                print(f"   ✅ Incidente 16 encontrado: {incidente_16.get('Titulo', 'Sin título')}")
            else:
                print("   ❌ Incidente 16 NO encontrado en la lista")
                return
        else:
            print(f"   ❌ Error obteniendo lista: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # 2. Probar el endpoint DELETE
    print(f"\n2️⃣ PROBANDO DELETE {base_url}/api/admin/incidentes/{incidente_id}")
    try:
        response = requests.delete(f"{base_url}/api/admin/incidentes/{incidente_id}")
        print(f"   📊 Status Code: {response.status_code}")
        print(f"   📋 Response Headers: {dict(response.headers)}")
        print(f"   📄 Response Text: {response.text[:500]}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ Response JSON: {json.dumps(data, indent=2)}")
            except:
                print("   ⚠️ Response no es JSON válido")
        elif response.status_code == 404:
            print("   ❌ Endpoint no encontrado (404)")
        elif response.status_code == 405:
            print("   ❌ Método no permitido (405)")
        else:
            print(f"   ❌ Error inesperado: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Error: No se pudo conectar al servidor")
        print("   💡 ¿Está el servidor corriendo en localhost:5000?")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 3. Verificar si el incidente sigue existiendo
    print(f"\n3️⃣ VERIFICANDO SI EL INCIDENTE SIGUE EXISTIENDO...")
    try:
        response = requests.get(f"{base_url}/api/admin/empresas/3/incidentes")
        if response.status_code == 200:
            incidentes = response.json()
            incidente_16 = next((inc for inc in incidentes if inc.get('IncidenteID') == 16), None)
            if incidente_16:
                print(f"   ❌ Incidente 16 SIGUE EXISTIENDO - La eliminación NO funcionó")
            else:
                print(f"   ✅ Incidente 16 fue eliminado correctamente")
        else:
            print(f"   ❌ Error verificando: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print(f"\n🏁 TEST COMPLETADO")

if __name__ == "__main__":
    test_delete_endpoint()
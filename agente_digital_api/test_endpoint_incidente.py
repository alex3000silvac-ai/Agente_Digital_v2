"""
Script para probar el endpoint de obtener incidente
"""

import requests
import json
import jwt
from datetime import datetime, timedelta

# Configuración
API_URL = "http://localhost:5000"
INCIDENTE_ID = 5

def generar_token_prueba():
    """Genera un token JWT de prueba"""
    secret_key = "dev_secret_key_2024"  # Debe coincidir con la configuración
    
    payload = {
        'user_id': 1,
        'email': 'test@example.com',
        'nombre': 'Usuario Prueba',
        'rol': 'Administrador',
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token

def probar_endpoint():
    """Prueba el endpoint de obtener incidente"""
    
    # Generar token
    token = generar_token_prueba()
    print(f"🔑 Token generado: {token[:50]}...")
    
    # Headers
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Hacer petición
    url = f"{API_URL}/api/admin/incidentes/{INCIDENTE_ID}"
    print(f"\n📡 Llamando a: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"\n📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n✅ RESPUESTA EXITOSA:")
            print(f"   - IncidenteID: {data.get('IncidenteID')}")
            print(f"   - Título: {data.get('Titulo')}")
            
            # Verificar archivos
            if 'archivos' in data:
                print("\n📎 ARCHIVOS:")
                for seccion, archivos in data['archivos'].items():
                    if isinstance(archivos, list) and len(archivos) > 0:
                        print(f"   - {seccion}: {len(archivos)} archivos")
                        for archivo in archivos[:2]:  # Mostrar máx 2 por sección
                            print(f"     • {archivo.get('nombre')} ({archivo.get('id')})")
            else:
                print("\n❌ No se encontró la clave 'archivos' en la respuesta")
            
            # Verificar taxonomías
            if 'taxonomias_seleccionadas' in data:
                print(f"\n🏷️ TAXONOMÍAS: {len(data['taxonomias_seleccionadas'])} seleccionadas")
                for tax in data['taxonomias_seleccionadas'][:2]:
                    print(f"   - {tax.get('id')} - {tax.get('nombre')}")
            
            # Guardar respuesta completa para análisis
            with open('respuesta_incidente.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("\n💾 Respuesta completa guardada en: respuesta_incidente.json")
            
        else:
            print(f"\n❌ Error: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Error en la petición: {e}")

if __name__ == "__main__":
    probar_endpoint()
EOF < /dev/null

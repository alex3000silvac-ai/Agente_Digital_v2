import requests
import jwt
from datetime import datetime, timedelta

# Generar token
payload = {
    'user_id': 1,
    'email': 'test@example.com',
    'nombre': 'Usuario Prueba',
    'rol': 'Administrador',
    'exp': datetime.utcnow() + timedelta(hours=24)
}
token = jwt.encode(payload, "dev_secret_key_2024", algorithm='HS256')

# Hacer petición
headers = {'Authorization': f'Bearer {token}'}
response = requests.get("http://localhost:5000/api/admin/incidentes/5", headers=headers)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Título: {data.get('Titulo')}")
    
    # Verificar archivos
    if 'archivos' in data:
        print("\nARCHIVOS:")
        for seccion, archivos in data['archivos'].items():
            if isinstance(archivos, list) and len(archivos) > 0:
                print(f"  {seccion}: {len(archivos)} archivos")
    
    # Verificar taxonomías
    if 'taxonomias_seleccionadas' in data:
        print(f"\nTAXONOMÍAS: {len(data['taxonomias_seleccionadas'])}")
    
    # Guardar respuesta
    import json
    with open('respuesta.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("\nRespuesta guardada en respuesta.json")
else:
    print(f"Error: {response.text}")
"""
Script para probar la conexión real al servidor
"""

import requests
import jwt
from datetime import datetime, timedelta

# Configuración
BASE_URL = "http://127.0.0.1:5000"  # Usar 127.0.0.1 en lugar de localhost
INCIDENTE_ID = 5

print("=" * 70)
print("PRUEBA DE CONEXIÓN AL SERVIDOR FLASK")
print("=" * 70)

# 1. Probar conexión básica
print("\n1. PROBANDO CONEXIÓN BÁSICA:")
try:
    response = requests.get(f"{BASE_URL}/", timeout=5)
    print(f"   ✅ Servidor respondiendo en {BASE_URL}")
    print(f"   Status: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error de conexión: {e}")
    print("   Verifica que el servidor esté corriendo en el puerto 5000")

# 2. Generar token JWT
print("\n2. GENERANDO TOKEN JWT:")
try:
    # Primero intentar obtener la clave del servidor
    from app.config import Config
    secret_key = Config.SECRET_KEY
    print(f"   ✅ Clave secreta obtenida de config")
except:
    secret_key = "dev_secret_key_2024"
    print(f"   ⚠️ Usando clave secreta por defecto")

payload = {
    'user_id': 1,
    'email': 'admin@example.com',
    'nombre': 'Administrador',
    'rol': 'Administrador',
    'exp': datetime.utcnow() + timedelta(hours=24)
}

token = jwt.encode(payload, secret_key, algorithm='HS256')
print(f"   Token: {token[:50]}...")

# 3. Probar endpoint de incidente
print(f"\n3. PROBANDO ENDPOINT DE INCIDENTE {INCIDENTE_ID}:")
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

try:
    url = f"{BASE_URL}/api/admin/incidentes/{INCIDENTE_ID}"
    print(f"   URL: {url}")
    
    response = requests.get(url, headers=headers, timeout=5)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n   ✅ RESPUESTA EXITOSA:")
        
        # Verificar estructura
        if 'archivos' in data:
            total_archivos = sum(len(archivos) if isinstance(archivos, list) else 0 
                               for archivos in data['archivos'].values())
            print(f"   - Archivos totales: {total_archivos}")
            for seccion, archivos in data['archivos'].items():
                if isinstance(archivos, list) and len(archivos) > 0:
                    print(f"     • {seccion}: {len(archivos)} archivos")
        
        if 'taxonomias_seleccionadas' in data:
            print(f"   - Taxonomías: {len(data['taxonomias_seleccionadas'])}")
        
        if 'formData' in data:
            print(f"   - FormData: {len(data['formData'])} campos")
        else:
            print("   - FormData: NO INCLUIDO (se mapeará en frontend)")
        
        # Guardar respuesta
        import json
        with open('respuesta_real.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("\n   💾 Respuesta guardada en: respuesta_real.json")
        
    elif response.status_code == 401:
        print("\n   ❌ ERROR 401: No autorizado")
        print("   - El token JWT puede ser inválido")
        print("   - Verifica la clave secreta en config.py")
    elif response.status_code == 404:
        print("\n   ❌ ERROR 404: Endpoint no encontrado")
        print("   - Verifica que el blueprint esté registrado")
    else:
        print(f"\n   ❌ ERROR {response.status_code}: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("\n   ❌ ERROR: No se puede conectar al servidor")
    print("   - Verifica que el servidor esté corriendo")
    print("   - Verifica que no haya firewall bloqueando")
except Exception as e:
    print(f"\n   ❌ ERROR: {e}")

# 4. Comandos para el frontend
print("\n" + "=" * 70)
print("PARA PROBAR EN EL FRONTEND:")
print("=" * 70)
print("\n1. En la consola del navegador, ejecuta:")
print(f"""
// Guardar token para pruebas
localStorage.setItem('token', '{token[:50]}...')

// Probar llamada directa
fetch('http://127.0.0.1:5000/api/admin/incidentes/5', {{
  headers: {{
    'Authorization': 'Bearer ' + localStorage.getItem('token')
  }}
}})
.then(r => r.json())
.then(data => {{
  console.log('Archivos:', data.archivos)
  console.log('Taxonomías:', data.taxonomias_seleccionadas)
}})
""")

print("\n2. Si funciona, el problema está en el componente Vue")
print("3. Si no funciona, revisa CORS en el servidor Flask")
print("=" * 70)
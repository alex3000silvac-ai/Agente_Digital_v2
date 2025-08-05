#!/usr/bin/env python3
"""
Probar autenticación del endpoint de taxonomías
"""

import requests
import json
import jwt
import os
from datetime import datetime, timedelta

def test_auth_endpoint():
    """Probar el endpoint de taxonomías con diferentes tokens"""
    
    print("🔍 PROBANDO AUTENTICACIÓN DEL ENDPOINT DE TAXONOMÍAS")
    print("=" * 80)
    
    # 1. Obtener el token del localStorage (simulado)
    print("\n1️⃣ PROBANDO CON TOKEN EXISTENTE:")
    
    # Token de ejemplo (deberías obtenerlo del navegador)
    token_ejemplo = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOjEsInJvbCI6ImFkbWluIiwiZW1haWwiOiJhZG1pbkB0ZXN0LmNvbSIsIm5vbWJyZSI6IkFkbWluIiwiZXhwIjoxNzUzMTAwMDAwLCJpYXQiOjE3MjE0MzAwMDB9.EXAMPLE"
    
    url = "http://localhost:5000/api/admin/incidentes/25/taxonomias"
    
    # Intentar sin token
    print("\n   a) Sin token:")
    try:
        response = requests.get(url)
        print(f"      Status: {response.status_code}")
        print(f"      Response: {response.text[:100]}")
    except Exception as e:
        print(f"      Error: {e}")
    
    # Intentar con Bearer token
    print("\n   b) Con Bearer token:")
    headers = {
        "Authorization": f"Bearer {token_ejemplo}"
    }
    try:
        response = requests.get(url, headers=headers)
        print(f"      Status: {response.status_code}")
        print(f"      Response: {response.text[:200]}")
    except Exception as e:
        print(f"      Error: {e}")
    
    # 2. Generar un token válido
    print("\n2️⃣ GENERANDO TOKEN VÁLIDO:")
    
    # Buscar la clave secreta correcta
    jwt_secrets = [
        os.getenv('JWT_SECRET_KEY', 'your-secret-key-here'),
        'your-secret-key-here',
        'super-secret-key-2024',
        'agente-digital-secret-2024',
        'dev-secret-key'
    ]
    
    payload = {
        'sub': 1,
        'rol': 'admin',
        'email': 'admin@test.com',
        'nombre': 'Admin',
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    
    for i, secret in enumerate(jwt_secrets):
        print(f"\n   Intento {i+1} con clave: {secret[:20]}...")
        try:
            token = jwt.encode(payload, secret, algorithm='HS256')
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(url, headers=headers)
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"      ✅ ÉXITO! Token válido con clave: {secret}")
                data = response.json()
                print(f"      Taxonomías encontradas: {data.get('total', 0)}")
                if data.get('taxonomias'):
                    for tax in data['taxonomias']:
                        print(f"      - {tax['nombre']}")
                        print(f"        Archivos: {len(tax.get('archivos', []))}")
                break
            else:
                print(f"      ❌ Fallo: {response.text[:100]}")
                
        except Exception as e:
            print(f"      Error: {e}")
    
    # 3. Probar endpoint de carga completa como alternativa
    print("\n3️⃣ PROBANDO ENDPOINT ALTERNATIVO:")
    url_alt = "http://localhost:5000/api/incidente/25/cargar_completo"
    
    try:
        response = requests.get(url_alt)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'taxonomias_seleccionadas' in data:
                print(f"   ✅ Taxonomías en carga completa: {len(data['taxonomias_seleccionadas'])}")
                for tax in data['taxonomias_seleccionadas']:
                    print(f"   - {tax.get('nombre', tax.get('Id_Taxonomia'))}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_auth_endpoint()
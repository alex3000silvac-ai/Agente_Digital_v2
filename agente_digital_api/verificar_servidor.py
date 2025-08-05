#!/usr/bin/env python3
"""
Script para verificar el estado del servidor y endpoints
"""

import requests
import json

def verificar_servidor():
    """Verifica si el servidor está corriendo y los endpoints responden"""
    
    base_url = "http://localhost:5000"
    
    print("🔍 VERIFICANDO SERVIDOR FLASK")
    print("=" * 60)
    
    # 1. Verificar si el servidor responde
    print("\n1️⃣ VERIFICANDO CONEXIÓN AL SERVIDOR...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor respondiendo correctamente")
        else:
            print(f"⚠️ Servidor responde pero con código: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: El servidor NO está corriendo")
        print("💡 Ejecuta: python run.py")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False
    
    # 2. Verificar endpoint de empresas
    print("\n2️⃣ VERIFICANDO ENDPOINT DE EMPRESAS...")
    try:
        response = requests.get(f"{base_url}/api/admin/empresas/3")
        if response.status_code == 200:
            print("✅ Endpoint de empresas funcionando")
        else:
            print(f"⚠️ Endpoint de empresas responde con: {response.status_code}")
    except Exception as e:
        print(f"❌ Error en endpoint de empresas: {e}")
    
    # 3. Verificar endpoint de taxonomías
    print("\n3️⃣ VERIFICANDO ENDPOINT DE TAXONOMÍAS...")
    try:
        response = requests.get(f"{base_url}/api/admin/taxonomias/flat?tipo_empresa=PSE")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Endpoint de taxonomías funcionando")
            print(f"   - Taxonomías cargadas: {data.get('total', 0)}")
        else:
            print(f"⚠️ Endpoint de taxonomías responde con: {response.status_code}")
    except Exception as e:
        print(f"❌ Error en endpoint de taxonomías: {e}")
    
    print("\n✅ VERIFICACIÓN COMPLETADA")
    return True

if __name__ == "__main__":
    verificar_servidor()
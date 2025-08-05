#!/usr/bin/env python3
"""
Script para probar la subida de evidencias
"""

import requests
import os

# URL del servidor
BASE_URL = "http://localhost:5000"

def test_upload():
    """Probar subida de archivo"""
    
    # Crear un archivo de prueba
    test_file = "test_evidencia.txt"
    with open(test_file, 'w') as f:
        f.write("Este es un archivo de prueba para evidencias\n")
        f.write("Cumplimiento ID: 3\n")
        f.write("Fecha: 2025-01-11\n")
    
    try:
        # Preparar la solicitud
        files = {
            'file': ('test_evidencia.txt', open(test_file, 'rb'), 'text/plain')
        }
        data = {
            'descripcion': 'Archivo de prueba para verificar funcionalidad',
            'fecha_vigencia': '2025-12-31'
        }
        
        # Hacer la solicitud
        print("📤 Subiendo archivo de prueba...")
        response = requests.post(
            f"{BASE_URL}/api/admin/cumplimiento/3/evidencia",
            files=files,
            data=data
        )
        
        print(f"📊 Status: {response.status_code}")
        print(f"📝 Respuesta: {response.text}")
        
        if response.status_code == 201:
            print("✅ Archivo subido exitosamente!")
            
            # Verificar que se puede listar
            print("\n📋 Verificando lista de evidencias...")
            response = requests.get(f"{BASE_URL}/api/admin/cumplimiento/3/evidencias")
            if response.status_code == 200:
                evidencias = response.json()
                print(f"✅ Evidencias encontradas: {len(evidencias)}")
                for ev in evidencias:
                    print(f"   - {ev.get('NombreArchivo', ev.get('NombreArchivoOriginal'))}")
        else:
            print(f"❌ Error al subir: {response.status_code}")
            
    finally:
        # Limpiar archivo de prueba
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == '__main__':
    test_upload()
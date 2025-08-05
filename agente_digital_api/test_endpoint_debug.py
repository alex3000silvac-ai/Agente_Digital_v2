"""
Script para verificar exactamente qué devuelve el endpoint
"""

from app.database import get_db_connection
from app.modules.admin.incidentes_admin_endpoints import obtener_incidente_admin
import json

# Simular la llamada al endpoint
INCIDENTE_ID = 5

# Parámetros simulados del decorator
current_user_id = 1
current_user_rol = "Administrador"
current_user_email = "test@example.com"
current_user_nombre = "Usuario Test"

print("=" * 70)
print("SIMULACIÓN DE LLAMADA AL ENDPOINT")
print("=" * 70)

# Crear un contexto de aplicación Flask simulado
from flask import Flask, jsonify
app = Flask(__name__)

with app.app_context():
    try:
        # Llamar directamente a la función del endpoint
        response, status_code = obtener_incidente_admin(
            current_user_id, 
            current_user_rol, 
            current_user_email, 
            current_user_nombre, 
            INCIDENTE_ID
        )
        
        # Obtener los datos JSON
        data = response.get_json()
        
        print(f"\n📊 Status Code: {status_code}")
        print(f"\n🔑 Claves principales en la respuesta:")
        for key in data.keys():
            if isinstance(data[key], dict):
                print(f"   - {key}: diccionario con {len(data[key])} claves")
            elif isinstance(data[key], list):
                print(f"   - {key}: lista con {len(data[key])} elementos")
            else:
                print(f"   - {key}: {type(data[key]).__name__}")
        
        # Verificar archivos
        if 'archivos' in data:
            print(f"\n📎 ESTRUCTURA DE ARCHIVOS:")
            for seccion, archivos in data['archivos'].items():
                if isinstance(archivos, list):
                    print(f"   - {seccion}: {len(archivos)} archivos")
                    if len(archivos) > 0:
                        print(f"     Ejemplo: {archivos[0].get('nombre', 'sin nombre')}")
        
        # Verificar taxonomías
        if 'taxonomias_seleccionadas' in data:
            print(f"\n🏷️ TAXONOMÍAS SELECCIONADAS: {len(data['taxonomias_seleccionadas'])}")
            for tax in data['taxonomias_seleccionadas'][:2]:
                print(f"   - {tax.get('id')} - {tax.get('nombre', 'sin nombre')}")
                if tax.get('justificacion'):
                    print(f"     Justificación: {tax['justificacion'][:50]}...")
        
        # Verificar formData
        if 'formData' in data:
            print(f"\n📝 FORMDATA: {len(data['formData'])} campos")
            for campo in ['1.1', '1.2', '2.1', '3.1']:
                if campo in data['formData']:
                    valor = str(data['formData'][campo])[:50]
                    print(f"   - {campo}: {valor}...")
        else:
            print("\n⚠️ NO HAY formData en la respuesta")
            print("   El frontend deberá mapear los campos directamente")
        
        # Guardar respuesta completa
        with open('respuesta_endpoint_debug.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print("\n💾 Respuesta completa guardada en: respuesta_endpoint_debug.json")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
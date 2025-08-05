#!/usr/bin/env python3
"""
Verificar qué devuelve realmente el endpoint cargar_completo
"""

import requests
import json
import sys

def test_endpoint():
    """Probar el endpoint cargar_completo"""
    try:
        # Primero hacer login
        print("1️⃣ HACIENDO LOGIN...")
        login_url = "http://localhost:5002/api/login"
        login_data = {
            "email": "admin@agentedigital.cl",
            "password": "Admin123!"
        }
        
        login_response = requests.post(login_url, json=login_data)
        if login_response.status_code != 200:
            print(f"❌ Error en login: {login_response.text}")
            return
            
        token = login_response.json().get('token')
        print(f"✅ Login exitoso")
        
        # Ahora cargar el incidente 25
        print("\n2️⃣ CARGANDO INCIDENTE 25...")
        url = "http://localhost:5002/api/incidente/25/cargar_completo"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return
            
        data = response.json()
        
        # Guardar respuesta completa
        with open('respuesta_cargar_completo_25.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✅ Respuesta guardada en respuesta_cargar_completo_25.json")
        
        # Analizar taxonomías
        print("\n3️⃣ ANALIZANDO TAXONOMÍAS...")
        incidente = data.get('incidente', {})
        taxonomias = incidente.get('taxonomias_seleccionadas', [])
        
        print(f"   Total taxonomías: {len(taxonomias)}")
        
        if taxonomias:
            for idx, tax in enumerate(taxonomias):
                print(f"\n   📋 Taxonomía {idx + 1}:")
                print(f"      ID: {tax.get('id', 'NO TIENE ID')}")
                print(f"      ID alternativo: {tax.get('Id_Taxonomia', 'NO TIENE Id_Taxonomia')}")
                print(f"      Nombre: {tax.get('nombre', 'NO TIENE NOMBRE')}")
                print(f"      Justificación: {tax.get('justificacion', 'NO TIENE')[:50]}...")
                print(f"      Descripción: {tax.get('descripcionProblema', 'NO TIENE')[:50]}...")
                print(f"      Archivos: {len(tax.get('archivos', []))} archivos")
                
                if tax.get('archivos'):
                    for archivo in tax['archivos']:
                        print(f"         📄 {archivo.get('nombre', 'Sin nombre')}")
        else:
            print("   ❌ NO HAY TAXONOMÍAS SELECCIONADAS")
            
        # Verificar evidencias_taxonomias
        print("\n4️⃣ VERIFICANDO evidencias_taxonomias...")
        evidencias_tax = incidente.get('evidencias_taxonomias', {})
        print(f"   IDs de taxonomías con evidencias: {list(evidencias_tax.keys())}")
        
        for tax_id, archivos in evidencias_tax.items():
            print(f"   📂 {tax_id}: {len(archivos)} archivos")
            
        # Verificar estructura esperada por el frontend
        print("\n5️⃣ ESTRUCTURA ESPERADA POR EL FRONTEND:")
        print("   taxonomias_seleccionadas: [")
        print("     {")
        print("       id: 'INC_USO_PHIP_ECDP',")
        print("       nombre: '...',")
        print("       justificacion: '...',")
        print("       descripcionProblema: '...',")
        print("       archivos: [...]")
        print("     }")
        print("   ]")
        
        # Verificar qué campos faltan
        print("\n6️⃣ CAMPOS FALTANTES:")
        if taxonomias:
            tax = taxonomias[0]
            campos_esperados = ['id', 'nombre', 'justificacion', 'descripcionProblema', 'archivos']
            campos_faltantes = [campo for campo in campos_esperados if not tax.get(campo)]
            
            if campos_faltantes:
                print(f"   ❌ Faltan campos: {', '.join(campos_faltantes)}")
            else:
                print("   ✅ Todos los campos esperados están presentes")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_endpoint()
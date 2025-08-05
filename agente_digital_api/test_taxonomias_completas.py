#!/usr/bin/env python3
"""
Script de prueba para verificar que las taxonomías se cargan correctamente
con todos los campos: área, efecto, categoría y subcategoría
"""

import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:5000"

def test_taxonomias_completas():
    """Prueba obtener taxonomías con todos los campos"""
    
    print("="*80)
    print("PRUEBA DE TAXONOMÍAS COMPLETAS")
    print("="*80)
    
    # Test 1: Obtener taxonomías flat (lista plana)
    print("\n1. Obteniendo taxonomías planas para PSE...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/taxonomias/flat", params={"tipo_empresa": "PSE"})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Estado: {data.get('status')}")
            print(f"✅ Tipo empresa: {data.get('tipo_empresa')}")
            print(f"✅ Total taxonomías: {data.get('total')}")
            
            # Mostrar primeras 3 taxonomías
            taxonomias = data.get('taxonomias', [])
            if taxonomias:
                print("\nPrimeras 3 taxonomías con todos los campos:")
                for i, tax in enumerate(taxonomias[:3]):
                    print(f"\n  Taxonomía {i+1}:")
                    print(f"  - ID: {tax.get('id')}")
                    print(f"  - Área: {tax.get('area')}")
                    print(f"  - Efecto: {tax.get('efecto')}")
                    print(f"  - Categoría: {tax.get('categoria')}")
                    print(f"  - Subcategoría: {tax.get('subcategoria')}")
                    print(f"  - Aplica para: {tax.get('aplica_para')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Respuesta: {response.text}")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
    
    # Test 2: Obtener taxonomías para OIV
    print("\n\n2. Obteniendo taxonomías para OIV...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/taxonomias/flat", params={"tipo_empresa": "OIV"})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total taxonomías OIV: {data.get('total')}")
            
            # Mostrar primera taxonomía completa
            taxonomias = data.get('taxonomias', [])
            if taxonomias:
                tax = taxonomias[0]
                print(f"\nEjemplo de taxonomía OIV:")
                print(f"Formato dropdown esperado:")
                dropdown_text = f'"Area": {tax.get("area")} "Efecto": {tax.get("efecto")} "Categoria del Incidente": {tax.get("categoria")} "Subcategoria del Incidente": {tax.get("subcategoria")}'
                print(f"{dropdown_text}")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Verificar empresa específica
    print("\n\n3. Verificando datos de empresa ID 2...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/empresas/2")
        
        if response.status_code == 200:
            empresa = response.json()
            print(f"✅ Nombre: {empresa.get('Nombre', empresa.get('nombre'))}")
            print(f"✅ Tipo: {empresa.get('TipoEmpresa', empresa.get('tipo_empresa'))}")
        else:
            print(f"❌ Error obteniendo empresa: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    test_taxonomias_completas()
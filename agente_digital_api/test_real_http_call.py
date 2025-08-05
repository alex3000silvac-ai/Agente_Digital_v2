#!/usr/bin/env python3
"""
Simular la llamada HTTP real que hace el frontend
"""
import requests
import json

def test_llamada_real():
    """Hacer la misma llamada HTTP que hace el frontend"""
    try:
        print("🌐 SIMULANDO LLAMADA HTTP REAL DEL FRONTEND")
        print("=" * 80)
        
        # URL exacta que usa el frontend
        url = "http://localhost:5000/api/incidentes/25/cargar-completo"
        
        # Headers que enviaría el frontend
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        
        # Verificar si necesitamos token
        # Primero intentar sin token
        print(f"\n📡 Llamando a: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 401:
                print("   ❌ Necesita autenticación")
                # Obtener token de algún lado o usar uno hardcodeado para prueba
                return
            
            if response.status_code == 200:
                data = response.json()
                print("   ✅ Respuesta recibida")
                
                # Verificar taxonomías
                if 'taxonomias_seleccionadas' in data:
                    taxonomias = data['taxonomias_seleccionadas']
                    print(f"\n📊 TAXONOMÍAS EN LA RESPUESTA: {len(taxonomias)}")
                    
                    for i, tax in enumerate(taxonomias, 1):
                        print(f"\n{i}. Taxonomía:")
                        print(f"   - id: {tax.get('id', 'NO TIENE')}")
                        print(f"   - Id_Taxonomia: {tax.get('Id_Taxonomia', 'NO TIENE')}")
                        print(f"   - justificacion: {tax.get('justificacion', 'NO TIENE')}")
                        print(f"   - descripcionProblema: {tax.get('descripcionProblema', 'NO TIENE')}")
                        print(f"   - nombre: {tax.get('nombre', 'NO TIENE')}")
                        
                        if not tax.get('id'):
                            print("   ❌ FALTA CAMPO 'id' - Frontend no lo mostrará")
                        if not tax.get('justificacion'):
                            print("   ❌ FALTA CAMPO 'justificacion'")
                else:
                    print("\n❌ NO HAY 'taxonomias_seleccionadas' en la respuesta")
                    print("Claves disponibles:", list(data.keys()))
                
                # Guardar respuesta completa para análisis
                with open('respuesta_completa.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print("\n📄 Respuesta completa guardada en: respuesta_completa.json")
                
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("   ❌ No se puede conectar al servidor Flask")
            print("   Verifica que el servidor esté corriendo en http://localhost:5000")
        except requests.exceptions.Timeout:
            print("   ❌ Timeout - El servidor no responde")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_llamada_real()
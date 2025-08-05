#!/usr/bin/env python3
"""
Test directo de eliminación para diagnosticar el problema
"""

import sys
import os

# Agregar el path del proyecto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.modules.admin.incidentes_eliminar_completo import eliminar_incidente_completo

def test_eliminacion_directa():
    """Prueba la eliminación directa del incidente 16"""
    
    incidente_id = 16
    
    print(f"🧪 TESTING ELIMINACIÓN DIRECTA DEL INCIDENTE {incidente_id}")
    print("=" * 60)
    
    # Ejecutar la eliminación directa
    print(f"\n🔥 EJECUTANDO ELIMINACIÓN DIRECTA...")
    try:
        resultado = eliminar_incidente_completo(incidente_id)
        
        print(f"\n📊 RESULTADO DE LA ELIMINACIÓN:")
        print(f"   - Tipo: {type(resultado)}")
        print(f"   - Resultado: {resultado}")
        
        if hasattr(resultado, 'get_json'):
            # Es una respuesta Flask
            status_code = resultado[1] if isinstance(resultado, tuple) else 200
            data = resultado[0].get_json() if isinstance(resultado, tuple) else resultado.get_json()
            
            print(f"\n📋 DATOS DE RESPUESTA:")
            print(f"   - Status Code: {status_code}")
            print(f"   - Success: {data.get('success', 'No definido')}")
            print(f"   - Message: {data.get('message', 'No definido')}")
            
            if 'detalles' in data:
                detalles = data['detalles']
                print(f"   - Tablas afectadas: {detalles.get('tablas_afectadas', [])}")
                print(f"   - Archivos eliminados: {detalles.get('archivos_eliminados', 0)}")
        
    except Exception as e:
        print(f"❌ ERROR EN ELIMINACIÓN DIRECTA: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🏁 TEST ELIMINACIÓN DIRECTA COMPLETADO")

if __name__ == "__main__":
    test_eliminacion_directa()
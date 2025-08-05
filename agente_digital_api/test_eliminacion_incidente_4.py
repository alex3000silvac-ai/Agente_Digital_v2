#!/usr/bin/env python3
"""
Script para probar la eliminación del incidente 4 directamente
"""

import requests
import json

def test_eliminacion_directa():
    incidente_id = 4
    url = f"http://localhost:5000/api/admin/incidentes/{incidente_id}"
    
    print(f"🔥 Probando eliminación directa del incidente {incidente_id}")
    print(f"🌐 URL: {url}")
    
    try:
        # Simular token de autenticación (si es necesario)
        headers = {
            'Content-Type': 'application/json',
            # 'Authorization': 'Bearer token_aqui'  # Descomenta si necesitas auth
        }
        
        print(f"📨 Enviando petición DELETE...")
        response = requests.delete(url, headers=headers, timeout=30)
        
        print(f"📊 Respuesta del servidor:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"   JSON Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"   Raw Response: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ Eliminación exitosa según servidor")
            
            # Verificar inmediatamente en BD
            from app.database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT IncidenteID FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
            existe = cursor.fetchone()
            
            if existe:
                print(f"❌ PROBLEMA: El incidente {incidente_id} AÚN EXISTE en la BD tras eliminación")
            else:
                print(f"✅ ÉXITO: El incidente {incidente_id} fue eliminado correctamente de la BD")
            
            cursor.close()
            conn.close()
            
        else:
            print(f"❌ Error en eliminación: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error en la petición: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_eliminacion_directa()
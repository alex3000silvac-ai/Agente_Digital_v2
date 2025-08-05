#!/usr/bin/env python3
"""
Test de taxonomías para incidente 22 - Verificar guardado y carga
"""
import requests
import json

# Configuración
BASE_URL = "http://localhost:5000"
INCIDENTE_ID = 22

def test_cargar_incidente():
    """Cargar incidente 22 y verificar taxonomías"""
    print(f"🔍 Cargando incidente {INCIDENTE_ID}...")
    
    try:
        # Llamar al endpoint de carga
        response = requests.get(f"{BASE_URL}/api/admin/incidentes/{INCIDENTE_ID}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Incidente cargado exitosamente")
            
            # Verificar taxonomías
            taxonomias = data.get('taxonomias_seleccionadas', [])
            print(f"🏷️  Taxonomías encontradas: {len(taxonomias)}")
            
            for i, tax in enumerate(taxonomias):
                print(f"  {i+1}. ID: {tax.get('id', 'N/A')}")
                print(f"      Nombre: {tax.get('nombre', 'N/A')}")
                print(f"      Justificación: {tax.get('justificacion', 'N/A')}")
                print(f"      Fecha: {tax.get('fechaSeleccion', 'N/A')}")
                print()
                
            return data
        else:
            print(f"❌ Error cargando incidente: {response.status_code}")
            print(f"    Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def test_guardar_taxonomias():
    """Test de guardado de taxonomías"""
    print(f"💾 Probando guardado de taxonomías...")
    
    # Datos de prueba
    datos_test = {
        "taxonomias_seleccionadas": [
            {
                "id": "INC_CONF_EXCF_FCRA",
                "justificacion": "Test de justificación desde script",
                "descripcionProblema": "Test descripción problema"
            },
            {
                "id": "INC_CONF_EXCF_FSRA", 
                "justificacion": "Segunda justificación de prueba",
                "descripcionProblema": "Segunda descripción"
            }
        ]
    }
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer dummy_token'  # Necesario para JWT
        }
        
        response = requests.put(
            f"{BASE_URL}/api/incidentes/{INCIDENTE_ID}/actualizar",
            json=datos_test,
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"✅ Taxonomías guardadas exitosamente")
            return True
        else:
            print(f"❌ Error guardando taxonomías: {response.status_code}")
            print(f"    Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_verificar_base_datos():
    """Verificar datos directamente en la base de datos"""
    print(f"🗃️  Verificando datos en la base de datos...")
    
    try:
        from app.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar taxonomías del incidente
        cursor.execute("""
            SELECT 
                IT.ID,
                IT.IncidenteID,
                IT.Id_Taxonomia,
                IT.Comentarios,
                IT.FechaAsignacion,
                IT.CreadoPor
            FROM INCIDENTE_TAXONOMIA IT
            WHERE IT.IncidenteID = ?
        """, (INCIDENTE_ID,))
        
        rows = cursor.fetchall()
        
        print(f"📊 Registros en INCIDENTE_TAXONOMIA: {len(rows)}")
        for row in rows:
            print(f"  ID: {row[0]}, Taxonomía: {row[2]}")
            print(f"      Comentarios: {row[3][:50] if row[3] else 'Sin comentarios'}...")
            print(f"      Fecha: {row[4]}")
            print()
            
        cursor.close()
        conn.close()
        
        return len(rows) > 0
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        return False

if __name__ == "__main__":
    print("🧪 INICIANDO TESTS DE TAXONOMÍAS")
    print("=" * 50)
    
    # Test 1: Cargar incidente
    data = test_cargar_incidente()
    print()
    
    # Test 2: Verificar BD
    test_verificar_base_datos()
    print()
    
    print("✅ Tests completados")
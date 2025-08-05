#!/usr/bin/env python3
"""
Script para eliminar directamente el incidente 4 usando la función del backend
"""

import sys
sys.path.append('.')

from app.modules.admin.incidentes_eliminar_completo import eliminar_incidente_completo

def eliminar_incidente_manual():
    incidente_id = 4
    
    print(f"🔥 Eliminando incidente {incidente_id} directamente usando la función del backend")
    
    try:
        # Llamar directamente a la función de eliminación
        resultado, status_code = eliminar_incidente_completo(incidente_id)
        
        print(f"📊 Resultado de la eliminación:")
        print(f"   Status Code: {status_code}")
        print(f"   Resultado: {resultado}")
        
        if status_code == 200:
            print(f"✅ Función reporta eliminación exitosa")
            
            # Verificar inmediatamente en BD
            from app.database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT IncidenteID FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
            existe = cursor.fetchone()
            
            if existe:
                print(f"❌ PROBLEMA CRÍTICO: El incidente {incidente_id} AÚN EXISTE en la BD tras eliminación")
                print(f"🐛 Esto indica un problema en la función de eliminación")
            else:
                print(f"✅ ÉXITO TOTAL: El incidente {incidente_id} fue eliminado correctamente de la BD")
            
            cursor.close()
            conn.close()
        else:
            print(f"❌ Error en eliminación: {status_code}")
            
    except Exception as e:
        print(f"❌ Error ejecutando función de eliminación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    eliminar_incidente_manual()
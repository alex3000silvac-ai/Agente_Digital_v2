#!/usr/bin/env python3
"""
Test de eliminación y verificación en una sola conexión
"""

import sys
import os

# Agregar el path del proyecto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db_connection

def eliminar_y_verificar_incidente():
    """Elimina y verifica en la misma conexión"""
    
    incidente_id = 16
    
    print(f"🧪 TESTING ELIMINACIÓN Y VERIFICACIÓN DEL INCIDENTE {incidente_id}")
    print("=" * 70)
    
    conn = None
    try:
        # Obtener conexión
        conn = get_db_connection()
        if not conn:
            print("❌ Error: No se pudo conectar a la base de datos")
            return
            
        cursor = conn.cursor()
        
        # PASO 1: Verificar que el incidente existe
        print(f"\n1️⃣ VERIFICANDO QUE EL INCIDENTE {incidente_id} EXISTE...")
        cursor.execute("SELECT IncidenteID, Titulo, EstadoActual FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        incidente = cursor.fetchone()
        
        if incidente:
            print(f"✅ INCIDENTE {incidente_id} ENCONTRADO:")
            print(f"   - ID: {incidente[0]}")
            print(f"   - Título: {incidente[1]}")
            print(f"   - Estado: {incidente[2]}")
        else:
            print(f"❌ INCIDENTE {incidente_id} NO ENCONTRADO")
            return
        
        # PASO 2: Eliminar evidencias primero
        print(f"\n2️⃣ ELIMINANDO EVIDENCIAS DEL INCIDENTE {incidente_id}...")
        cursor.execute("DELETE FROM EvidenciasIncidentes WHERE IncidenteID = ?", (incidente_id,))
        evidencias_eliminadas = cursor.rowcount
        print(f"🗂️ Evidencias eliminadas: {evidencias_eliminadas}")
        
        # PASO 3: Eliminar el incidente principal
        print(f"\n3️⃣ ELIMINANDO INCIDENTE PRINCIPAL {incidente_id}...")
        cursor.execute("DELETE FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        incidentes_eliminados = cursor.rowcount
        print(f"📋 Incidentes eliminados: {incidentes_eliminados}")
        
        # PASO 4: Confirmar cambios
        print(f"\n4️⃣ CONFIRMANDO CAMBIOS...")
        conn.commit()
        print(f"✅ COMMIT ejecutado correctamente")
        
        # PASO 5: Verificar que el incidente ya no existe
        print(f"\n5️⃣ VERIFICANDO QUE EL INCIDENTE {incidente_id} FUE ELIMINADO...")
        cursor.execute("SELECT IncidenteID, Titulo, EstadoActual FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        incidente_check = cursor.fetchone()
        
        if incidente_check:
            print(f"❌ ERROR: INCIDENTE {incidente_id} TODAVÍA EXISTE DESPUÉS DE LA ELIMINACIÓN")
            print(f"   - ID: {incidente_check[0]}")
            print(f"   - Título: {incidente_check[1]}")
            print(f"   - Estado: {incidente_check[2]}")
        else:
            print(f"✅ PERFECTO: INCIDENTE {incidente_id} FUE ELIMINADO CORRECTAMENTE")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        if conn:
            conn.rollback()
            print(f"🔄 ROLLBACK ejecutado")
        
    finally:
        if conn:
            conn.close()
            print(f"🔌 Conexión cerrada")
    
    print(f"\n🏁 TEST COMPLETADO")

if __name__ == "__main__":
    eliminar_y_verificar_incidente()
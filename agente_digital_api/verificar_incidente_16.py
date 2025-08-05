#!/usr/bin/env python3
"""
Script para verificar si el incidente 16 realmente existe en la BD
"""

import sys
import os

# Agregar el path del proyecto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db_connection

def verificar_incidente(incidente_id):
    """Verifica si un incidente existe en la BD"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ Error: No se pudo conectar a la base de datos")
            return False
            
        cursor = conn.cursor()
        
        # Verificar que el incidente existe
        cursor.execute("SELECT IncidenteID, Titulo, EstadoActual FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        incidente = cursor.fetchone()
        
        if incidente:
            print(f"✅ INCIDENTE {incidente_id} SÍ EXISTE EN LA BD:")
            print(f"   - ID: {incidente[0]}")
            print(f"   - Título: {incidente[1]}")  
            print(f"   - Estado: {incidente[2]}")
            return True
        else:
            print(f"❌ INCIDENTE {incidente_id} NO EXISTE EN LA BD")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando incidente: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

def main():
    """Función principal"""
    incidente_id = 16
    
    print(f"🔍 VERIFICANDO EXISTENCIA DEL INCIDENTE {incidente_id}")
    print("=" * 50)
    
    if verificar_incidente(incidente_id):
        print(f"\n💡 CONCLUSIÓN: El incidente {incidente_id} TODAVÍA existe en la BD")
        print("   Esto explica por qué sigue apareciendo en el frontend")
    else:
        print(f"\n💡 CONCLUSIÓN: El incidente {incidente_id} NO existe en la BD")
        print("   El problema está en el caché del frontend")

if __name__ == "__main__":
    main()
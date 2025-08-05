#!/usr/bin/env python3
"""
Script para verificar si el incidente 4 existe en la base de datos
"""

from app.database import get_db_connection

def verificar_incidente(incidente_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"🔍 Verificando existencia del incidente {incidente_id}...")
    
    # Verificar en tabla principal
    cursor.execute("SELECT IncidenteID, Titulo, EstadoActual, EmpresaID FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
    incidente = cursor.fetchone()
    
    if incidente:
        print(f"✅ Incidente {incidente_id} EXISTE en la tabla Incidentes:")
        print(f"   ID: {incidente[0]}")
        print(f"   Título: {incidente[1]}")
        print(f"   Estado: {incidente[2]}")
        print(f"   EmpresaID: {incidente[3]}")
        
        # Verificar referencias en otras tablas
        tablas_verificar = [
            "INCIDENTE_TAXONOMIA",
            "EvidenciasIncidentes", 
            "HistorialIncidentes",
            "ReportesANCI"
        ]
        
        print(f"\n🔗 Verificando referencias en otras tablas:")
        for tabla in tablas_verificar:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {tabla} WHERE IncidenteID = ?", (incidente_id,))
                count = cursor.fetchone()[0]
                print(f"   {tabla}: {count} registros")
            except Exception as e:
                print(f"   {tabla}: ERROR - {e}")
    else:
        print(f"❌ Incidente {incidente_id} NO EXISTE en la tabla Incidentes")
    
    # Listar todos los incidentes existentes
    cursor.execute("SELECT IncidenteID, Titulo FROM Incidentes ORDER BY IncidenteID")
    todos_incidentes = cursor.fetchall()
    
    print(f"\n📋 Incidentes existentes en la base de datos:")
    for inc in todos_incidentes:
        print(f"   ID {inc[0]}: {inc[1]}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    verificar_incidente(4)
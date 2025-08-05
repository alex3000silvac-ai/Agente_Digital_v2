#!/usr/bin/env python3
"""
Test directo del cálculo de estadísticas
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db_connection

def test_estadisticas():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        incidente_id = 5
        
        # 1. Contar evidencias
        cursor.execute("""
            SELECT COUNT(*) 
            FROM Incidentes_Evidencias 
            WHERE IncidenteID = ?
        """, (incidente_id,))
        total_evidencias = cursor.fetchone()[0]
        print(f"Total evidencias: {total_evidencias}")
        
        # 2. Contar comentarios
        cursor.execute("""
            SELECT COUNT(*) 
            FROM Incidentes_Comentarios 
            WHERE IncidenteID = ?
        """, (incidente_id,))
        total_comentarios = cursor.fetchone()[0]
        print(f"Total comentarios: {total_comentarios}")
        
        # 3. Calcular completitud basada en taxonomías
        cursor.execute("""
            SELECT COUNT(*) 
            FROM Incidentes_Taxonomias 
            WHERE IncidenteID = ?
        """, (incidente_id,))
        taxonomias_seleccionadas = cursor.fetchone()[0]
        print(f"Taxonomías seleccionadas: {taxonomias_seleccionadas}")
        
        # 4. Verificar datos de la empresa
        cursor.execute("""
            SELECT i.EmpresaID, e.TipoEmpresa, e.RazonSocial
            FROM INCIDENTES i
            LEFT JOIN EMPRESAS e ON i.EmpresaID = e.EmpresaID
            WHERE i.IncidenteID = ?
        """, (incidente_id,))
        empresa_info = cursor.fetchone()
        if empresa_info:
            print(f"\nEmpresa ID: {empresa_info[0]}")
            print(f"Tipo Empresa: {empresa_info[1]}")
            print(f"Razón Social: {empresa_info[2]}")
        
        # 5. Verificar si hay datos en las tablas
        print("\n--- Verificación de datos existentes ---")
        
        # Evidencias
        cursor.execute("""
            SELECT TOP 5 EvidenciaID, Descripcion, FechaSubida
            FROM Incidentes_Evidencias 
            WHERE IncidenteID = ?
            ORDER BY FechaSubida DESC
        """, (incidente_id,))
        evidencias = cursor.fetchall()
        if evidencias:
            print(f"\nÚltimas evidencias:")
            for ev in evidencias:
                print(f"  - ID: {ev[0]}, Desc: {ev[1][:50]}..., Fecha: {ev[2]}")
        
        # Comentarios
        cursor.execute("""
            SELECT TOP 5 ComentarioID, Comentario, FechaCreacion
            FROM Incidentes_Comentarios 
            WHERE IncidenteID = ?
            ORDER BY FechaCreacion DESC
        """, (incidente_id,))
        comentarios = cursor.fetchall()
        if comentarios:
            print(f"\nÚltimos comentarios:")
            for com in comentarios:
                print(f"  - ID: {com[0]}, Texto: {com[1][:50]}..., Fecha: {com[2]}")
        
        # Estadísticas finales
        print(f"\n=== RESUMEN ESTADÍSTICAS ===")
        print(f"Evidencias: {total_evidencias}")
        print(f"Comentarios: {total_comentarios}")
        print(f"Taxonomías: {taxonomias_seleccionadas}")
        print(f"Completitud: {min(100, (taxonomias_seleccionadas * 20))}%")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    test_estadisticas()
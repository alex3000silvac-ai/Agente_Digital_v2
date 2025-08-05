#!/usr/bin/env python3
"""
Script para verificar las incidencias reales en la base de datos
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db_connection

def verificar_incidencias():
    """Verifica las incidencias reales en la base de datos"""
    conn = get_db_connection()
    if not conn:
        print("Error: No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor()
        
        # 1. Obtener información de Sub Surtika
        cursor.execute("""
            SELECT EmpresaID, RazonSocial, TipoEmpresa 
            FROM Empresas 
            WHERE RazonSocial LIKE '%Surtika%'
        """)
        empresa = cursor.fetchone()
        
        if empresa:
            empresa_id = empresa.EmpresaID
            print(f"\n=== EMPRESA: {empresa.RazonSocial} (ID: {empresa_id}, Tipo: {empresa.TipoEmpresa}) ===")
            
            # 2. Contar TODAS las incidencias (sin límite de fecha)
            cursor.execute("""
                SELECT COUNT(*) as TotalIncidencias
                FROM Incidentes
                WHERE EmpresaID = ?
            """, (empresa_id,))
            total = cursor.fetchone()
            print(f"\nTOTAL DE INCIDENCIAS (sin límite de fecha): {total.TotalIncidencias}")
            
            # 3. Contar incidencias de los últimos 60 días
            cursor.execute("""
                SELECT COUNT(*) as Total60Dias
                FROM Incidentes
                WHERE EmpresaID = ? AND FechaCreacion >= DATEADD(day, -60, GETDATE())
            """, (empresa_id,))
            total_60 = cursor.fetchone()
            print(f"Incidencias últimos 60 días: {total_60.Total60Dias}")
            
            # 4. Desglose por estado (todas las incidencias)
            cursor.execute("""
                SELECT 
                    EstadoActual,
                    COUNT(*) as Cantidad
                FROM Incidentes
                WHERE EmpresaID = ?
                GROUP BY EstadoActual
                ORDER BY COUNT(*) DESC
            """, (empresa_id,))
            print("\nDESGLOSE POR ESTADO (todas las incidencias):")
            for row in cursor.fetchall():
                print(f"  - {row.EstadoActual}: {row.Cantidad}")
            
            # 5. Desglose por criticidad (todas las incidencias)
            cursor.execute("""
                SELECT 
                    Criticidad,
                    COUNT(*) as Cantidad
                FROM Incidentes
                WHERE EmpresaID = ?
                GROUP BY Criticidad
                ORDER BY COUNT(*) DESC
            """, (empresa_id,))
            print("\nDESGLOSE POR CRITICIDAD (todas las incidencias):")
            for row in cursor.fetchall():
                print(f"  - {row.Criticidad}: {row.Cantidad}")
            
            # 6. Verificar todas las empresas con incidencias
            print("\n=== RESUMEN DE TODAS LAS EMPRESAS ===")
            cursor.execute("""
                SELECT 
                    E.RazonSocial,
                    E.TipoEmpresa,
                    COUNT(I.IncidenteID) as TotalIncidencias,
                    SUM(CASE WHEN I.FechaCreacion >= DATEADD(day, -60, GETDATE()) THEN 1 ELSE 0 END) as Ultimos60Dias
                FROM Empresas E
                LEFT JOIN Incidentes I ON E.EmpresaID = I.EmpresaID
                GROUP BY E.EmpresaID, E.RazonSocial, E.TipoEmpresa
                HAVING COUNT(I.IncidenteID) > 0
                ORDER BY COUNT(I.IncidenteID) DESC
            """)
            print("\nEmpresa | Tipo | Total Incidencias | Últimos 60 días")
            print("-" * 70)
            for row in cursor.fetchall():
                print(f"{row.RazonSocial[:30]:30} | {row.TipoEmpresa:4} | {row.TotalIncidencias:17} | {row.Ultimos60Dias:15}")
        
        else:
            print("No se encontró la empresa Sub Surtika")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    verificar_incidencias()
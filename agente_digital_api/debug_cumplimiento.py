#!/usr/bin/env python3
"""Script de depuración para verificar la consulta de cumplimiento"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.modules.core.database import get_db_connection

def debug_cumplimiento(empresa_id):
    conn = get_db_connection()
    if not conn:
        print("❌ Error de conexión")
        return
        
    cursor = conn.cursor()
    
    try:
        print(f"\n=== DEPURANDO CONSULTA PARA EMPRESA {empresa_id} ===\n")
        
        # 1. Verificar datos en la tabla
        print("1. Datos en CumplimientoEmpresa:")
        cursor.execute("""
            SELECT Estado, COUNT(*) as Total
            FROM CumplimientoEmpresa
            WHERE EmpresaID = ?
            GROUP BY Estado
        """, (empresa_id,))
        
        for row in cursor.fetchall():
            print(f"   - {row.Estado}: {row.Total}")
        
        # 2. Ejecutar la consulta problemática
        print("\n2. Ejecutando consulta del endpoint:")
        q_cumplimiento = """
            SELECT 
                ISNULL(SUM(CASE WHEN C.Estado = 'Implementado' THEN 1 ELSE 0 END), 0) AS Implementadas,
                ISNULL(SUM(CASE WHEN C.Estado = 'En Proceso' THEN 1 ELSE 0 END), 0) AS EnProceso,
                ISNULL(SUM(CASE WHEN C.Estado = 'Pendiente' THEN 1 ELSE 0 END), 0) AS Pendientes,
                ISNULL(SUM(CASE WHEN C.Estado = 'Vencido' THEN 1 ELSE 0 END), 0) AS Vencidas,
                ISNULL(SUM(CASE WHEN C.Estado = 'No Aplica' THEN 1 ELSE 0 END), 0) AS NoAplica
            FROM CumplimientoEmpresa AS C
            WHERE C.EmpresaID = ?
        """
        cursor.execute(q_cumplimiento, (empresa_id,))
        cumplimiento = cursor.fetchone()
        
        if cumplimiento:
            print(f"   Resultado: {cumplimiento}")
            print(f"   Tipo: {type(cumplimiento)}")
            
            # Verificar si tiene atributos o es una tupla
            if hasattr(cumplimiento, 'Implementadas'):
                print(f"   - Implementadas: {cumplimiento.Implementadas}")
                print(f"   - EnProceso: {cumplimiento.EnProceso}")
                print(f"   - Pendientes: {cumplimiento.Pendientes}")
                print(f"   - Vencidas: {cumplimiento.Vencidas}")
                print(f"   - NoAplica: {cumplimiento.NoAplica}")
            else:
                print("   ❌ El objeto no tiene atributos nombrados")
                print(f"   - Valores como tupla: {cumplimiento}")
                
            # Intentar acceder como el código del endpoint
            try:
                suma = cumplimiento.Implementadas + cumplimiento.EnProceso
                print(f"   ✅ Acceso a atributos funciona")
            except Exception as e:
                print(f"   ❌ Error al acceder atributos: {e}")
            
            # Verificar la suma
            suma = (cumplimiento.Implementadas + cumplimiento.EnProceso + 
                   cumplimiento.Pendientes + cumplimiento.Vencidas + cumplimiento.NoAplica)
            print(f"   - SUMA TOTAL: {suma}")
            print(f"   - ¿Suma == 0?: {suma == 0}")
        else:
            print("   ❌ No se obtuvo resultado")
        
        # 3. Consulta alternativa más simple
        print("\n3. Consulta alternativa:")
        cursor.execute("""
            SELECT COUNT(*) as Total,
                   SUM(CASE WHEN Estado = 'Implementado' THEN 1 ELSE 0 END) as Impl
            FROM CumplimientoEmpresa
            WHERE EmpresaID = ?
        """, (empresa_id,))
        alt = cursor.fetchone()
        print(f"   Total: {alt.Total}, Implementadas: {alt.Impl}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    debug_cumplimiento(3)
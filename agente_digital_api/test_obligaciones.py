#!/usr/bin/env python3
"""Verificar la consulta de obligaciones para empresa 3"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.modules.core.database import get_db_connection

def test_consulta():
    conn = get_db_connection()
    if not conn:
        print("Error de conexión")
        return
        
    cursor = conn.cursor()
    empresa_id = 3
    
    # 1. Obtener tipo de empresa
    cursor.execute("SELECT TipoEmpresa FROM Empresas WHERE EmpresaID = ?", (empresa_id,))
    result = cursor.fetchone()
    tipo_empresa = result.TipoEmpresa if result else 'PSE'
    print(f"Tipo empresa: {tipo_empresa}")
    
    # 2. Probar consulta de total obligaciones
    print("\n=== PROBANDO CONSULTA ORIGINAL ===")
    q_total = """
        SELECT COUNT(DISTINCT R.RecomendacionID) AS Total
        FROM OBLIGACIONES AS O
        INNER JOIN VerbosRectores AS V ON O.ObligacionID = V.ObligacionID
        INNER JOIN Recomendaciones AS R ON V.VerboID = R.VerboID
        WHERE O.AplicaPara = ? OR O.AplicaPara = 'Ambos'
    """
    cursor.execute(q_total, (tipo_empresa,))
    total = cursor.fetchone()
    print(f"Total recomendaciones: {total.Total if total else 0}")
    
    # 3. Verificar cada tabla
    print("\n=== VERIFICANDO TABLAS ===")
    
    # Obligaciones
    cursor.execute("SELECT COUNT(*) FROM OBLIGACIONES WHERE AplicaPara = ? OR AplicaPara = 'Ambos'", (tipo_empresa,))
    print(f"Obligaciones para {tipo_empresa}: {cursor.fetchone()[0]}")
    
    # VerbosRectores
    cursor.execute("SELECT COUNT(*) FROM VerbosRectores")
    print(f"Total VerbosRectores: {cursor.fetchone()[0]}")
    
    # Recomendaciones
    cursor.execute("SELECT COUNT(*) FROM Recomendaciones")
    print(f"Total Recomendaciones: {cursor.fetchone()[0]}")
    
    # 4. Verificar JOIN paso a paso
    print("\n=== VERIFICANDO JOINS ===")
    
    # JOIN 1: Obligaciones con VerbosRectores
    cursor.execute("""
        SELECT COUNT(*) 
        FROM OBLIGACIONES O
        INNER JOIN VerbosRectores V ON O.ObligacionID = V.ObligacionID
        WHERE O.AplicaPara = ? OR O.AplicaPara = 'Ambos'
    """, (tipo_empresa,))
    print(f"Obligaciones JOIN VerbosRectores: {cursor.fetchone()[0]}")
    
    # 5. Ver si hay recomendaciones para empresa 3
    cursor.execute("""
        SELECT COUNT(*) FROM CumplimientoEmpresa WHERE EmpresaID = ?
    """, (empresa_id,))
    print(f"\nRegistros en CumplimientoEmpresa para empresa {empresa_id}: {cursor.fetchone()[0]}")
    
    conn.close()

if __name__ == "__main__":
    test_consulta()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 VERIFICADOR DE DATOS DE PRUEBA
Valida que los datos creados coinciden con las especificaciones del usuario
"""

import sqlite3

def verificar_especificaciones():
    """Verifica que los datos coinciden con las especificaciones"""
    conn = sqlite3.connect('test_agente_digital.db')
    cursor = conn.cursor()

    print('📊 VERIFICACIÓN DE ESPECIFICACIONES DEL USUARIO')
    print('=' * 60)

    # Especificaciones del usuario:
    # Inquilino 1: 3 empresas (2 OIV, 1 PSE)
    # Inquilino 2: 4 empresas (2 OIV, 2 PSE) 
    # Inquilino 3: 1 empresa (PSE)
    # Inquilino 4: 5 empresas (2 OIV, 3 PSE)
    # Todas las empresas: 3 incidentes cada una + al menos 1 reporte ANCI

    especificaciones = {
        1: {"OIV": 2, "PSE": 1},
        2: {"OIV": 2, "PSE": 2}, 
        3: {"OIV": 0, "PSE": 1},
        4: {"OIV": 2, "PSE": 3}
    }

    # Verificar inquilinos y sus empresas
    cursor.execute('''
        SELECT i.InquilinoID, i.RazonSocial, e.TipoEmpresa, COUNT(*) as cantidad
        FROM Inquilinos i 
        JOIN Empresas e ON i.InquilinoID = e.InquilinoID 
        GROUP BY i.InquilinoID, i.RazonSocial, e.TipoEmpresa 
        ORDER BY i.InquilinoID, e.TipoEmpresa
    ''')

    inquilinos_empresas = cursor.fetchall()
    datos_reales = {}
    
    for row in inquilinos_empresas:
        inquilino_id, nombre, tipo, cantidad = row
        if inquilino_id not in datos_reales:
            datos_reales[inquilino_id] = {"nombre": nombre, "OIV": 0, "PSE": 0}
        datos_reales[inquilino_id][tipo] = cantidad

    # Verificar especificaciones
    print("🎯 VERIFICACIÓN POR INQUILINO:")
    todo_correcto = True
    
    for inquilino_id, spec in especificaciones.items():
        print(f"\n👤 Inquilino {inquilino_id}: {datos_reales.get(inquilino_id, {}).get('nombre', 'NO ENCONTRADO')}")
        
        if inquilino_id in datos_reales:
            real = datos_reales[inquilino_id]
            
            # Verificar OIV
            oiv_spec = spec["OIV"]
            oiv_real = real["OIV"]
            estado_oiv = "✅" if oiv_spec == oiv_real else "❌"
            print(f"   OIV: Esperado {oiv_spec}, Real {oiv_real} {estado_oiv}")
            
            # Verificar PSE
            pse_spec = spec["PSE"] 
            pse_real = real["PSE"]
            estado_pse = "✅" if pse_spec == pse_real else "❌"
            print(f"   PSE: Esperado {pse_spec}, Real {pse_real} {estado_pse}")
            
            if oiv_spec != oiv_real or pse_spec != pse_real:
                todo_correcto = False
        else:
            print("   ❌ INQUILINO NO ENCONTRADO")
            todo_correcto = False

    # Verificar incidentes por empresa (deben ser 3 cada una)
    print(f"\n🚨 VERIFICACIÓN DE INCIDENTES:")
    cursor.execute('''
        SELECT e.EmpresaID, e.RazonSocial, COUNT(inc.IncidenteID) as total_incidentes
        FROM Empresas e
        LEFT JOIN Incidentes inc ON e.EmpresaID = inc.EmpresaID
        GROUP BY e.EmpresaID, e.RazonSocial
        ORDER BY e.EmpresaID
    ''')

    empresas_incorrectas = 0
    for row in cursor.fetchall():
        empresa_id, nombre, incidentes = row
        estado = "✅" if incidentes == 3 else "❌"
        if incidentes != 3:
            empresas_incorrectas += 1
        print(f"   Empresa {empresa_id}: {incidentes} incidentes {estado}")

    if empresas_incorrectas > 0:
        todo_correcto = False

    # Verificar reportes ANCI
    print(f"\n📋 VERIFICACIÓN DE REPORTES ANCI:")
    cursor.execute('''
        SELECT COUNT(DISTINCT EmpresaID) as empresas_con_anci,
               COUNT(*) as total_reportes
        FROM ReportesANCI
    ''')
    
    empresas_con_anci, total_reportes = cursor.fetchone()
    
    cursor.execute('SELECT COUNT(*) FROM Empresas')
    total_empresas = cursor.fetchone()[0]
    
    print(f"   Total empresas: {total_empresas}")
    print(f"   Empresas con ANCI: {empresas_con_anci}")
    print(f"   Total reportes ANCI: {total_reportes}")
    
    estado_anci = "✅" if empresas_con_anci == total_empresas else "❌"
    print(f"   Cumplimiento ANCI: {estado_anci}")
    
    if empresas_con_anci != total_empresas:
        todo_correcto = False

    # Resumen final
    print(f"\n{'='*60}")
    if todo_correcto:
        print("🎉 ¡TODAS LAS ESPECIFICACIONES SE CUMPLIERON CORRECTAMENTE!")
        print("✅ Datos de prueba creados según los requerimientos exactos")
    else:
        print("⚠️ ALGUNAS ESPECIFICACIONES NO SE CUMPLIERON")
        print("❌ Revisar discrepancias arriba")
    
    print(f"{'='*60}")
    
    conn.close()
    return todo_correcto

if __name__ == "__main__":
    verificar_especificaciones()
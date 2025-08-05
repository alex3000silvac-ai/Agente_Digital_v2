#!/usr/bin/env python3
"""
VERIFICACIÓN URGENTE - Tipo de empresa inconsistente
"""
import pyodbc
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import get_db_connection

def verificar_urgente():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("🚨 VERIFICACIÓN URGENTE - TIPO DE EMPRESA")
        print("="*70 + "\n")
        
        # 1. Verificar incidente 5
        cursor.execute("""
            SELECT 
                i.IncidenteID,
                i.Titulo,
                i.EmpresaID,
                i.ReporteAnciID,
                e.RazonSocial,
                e.TipoEmpresa
            FROM INCIDENTES i
            LEFT JOIN EMPRESAS e ON i.EmpresaID = e.EmpresaID
            WHERE i.IncidenteID = 5
        """)
        
        resultado = cursor.fetchone()
        if resultado:
            print("📋 DATOS DEL INCIDENTE 5:")
            print(f"   - IncidenteID: {resultado[0]}")
            print(f"   - Título: {resultado[1]}")
            print(f"   - EmpresaID: {resultado[2]}")
            print(f"   - ReporteAnciID: {resultado[3]}")
            print(f"   - Razón Social: {resultado[4]}")
            print(f"   - TIPO EMPRESA: {resultado[5]} ⚠️")
            
            tipo_empresa = resultado[5]
            empresa_id = resultado[2]
        
        # 2. Verificar en todas las tablas donde aparece tipo empresa
        print("\n🔍 VERIFICANDO CONSISTENCIA DEL TIPO DE EMPRESA:")
        
        # En la tabla EMPRESAS
        cursor.execute("""
            SELECT TipoEmpresa, RazonSocial 
            FROM EMPRESAS 
            WHERE EmpresaID = ?
        """, (empresa_id,))
        
        empresa_data = cursor.fetchone()
        print(f"\n   TABLA EMPRESAS:")
        print(f"   - Tipo: {empresa_data[0]}")
        print(f"   - Razón Social: {empresa_data[1]}")
        
        # Verificar si hay campo TipoEmpresa en INCIDENTES
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'INCIDENTES' 
            AND COLUMN_NAME = 'TipoEmpresa'
        """)
        
        tiene_tipo_en_incidentes = cursor.fetchone()
        if tiene_tipo_en_incidentes:
            cursor.execute("""
                SELECT TipoEmpresa 
                FROM INCIDENTES 
                WHERE IncidenteID = 5
            """)
            tipo_en_incidente = cursor.fetchone()
            print(f"\n   TABLA INCIDENTES:")
            print(f"   - TipoEmpresa: {tipo_en_incidente[0] if tipo_en_incidente else 'NULL'}")
        
        # 3. PLAZOS SEGÚN TIPO DE EMPRESA
        print("\n⏰ PLAZOS LEGALES SEGÚN TIPO DE EMPRESA:")
        print("\n   OIV (Operador de Infraestructura Vital):")
        print("   - Informe Preliminar: 24 HORAS")
        print("   - Informe Completo: 72 HORAS")
        print("\n   PSE (Proveedor de Servicios Esenciales):")
        print("   - Informe Preliminar: 72 HORAS")
        print("   - Informe Completo: 72 HORAS")
        
        # 4. DIAGNÓSTICO
        print("\n" + "="*70)
        print("🚨 DIAGNÓSTICO CRÍTICO:")
        print("="*70)
        
        if tipo_empresa:
            print(f"\n⚠️  La empresa tiene tipo: {tipo_empresa}")
            print(f"   Esto significa que los plazos deben ser:")
            if tipo_empresa == 'OIV':
                print("   - Informe Preliminar: 24 HORAS (NO 72)")
                print("   - Informe Completo: 72 HORAS")
            else:
                print("   - Informe Preliminar: 72 HORAS")
                print("   - Informe Completo: 72 HORAS")
        
        # 5. Verificar dónde se está tomando el tipo de empresa
        print("\n📍 ORIGEN DEL PROBLEMA:")
        print("   El frontend puede estar:")
        print("   1. Tomando el tipo de empresa de diferentes lugares")
        print("   2. Usando un valor hardcodeado 'PSE' por defecto")
        print("   3. No actualizando el tipo cuando cambia la empresa")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verificar_urgente()
#!/usr/bin/env python3
"""
Script para simular el endpoint de acompañamiento y ver exactamente qué datos devuelve
"""
import pyodbc
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import get_db_connection

def simular_endpoint_acompanamiento():
    """Simula exactamente lo que hace el endpoint de acompañamiento"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        empresa_id = 3  # La empresa que mencionaste
        
        print("\n" + "="*70)
        print(f"SIMULANDO ENDPOINT DE ACOMPAÑAMIENTO PARA EMPRESA {empresa_id}")
        print("="*70 + "\n")
        
        # Verificar que la empresa existe
        cursor.execute("SELECT RazonSocial, TipoEmpresa FROM Empresas WHERE EmpresaID = ?", (empresa_id,))
        empresa_info = cursor.fetchone()
        
        if not empresa_info:
            print("❌ Empresa no encontrada")
            return
            
        print(f"✅ Empresa: {empresa_info[0]} ({empresa_info[1]})")
        
        # Query del endpoint de acompañamiento (igual que en el código real)
        query_obligaciones = """
            SELECT DISTINCT
                O.ObligacionID,
                O.ArticuloNorma,
                O.Descripcion,
                O.MedioDeVerificacionSugerido,
                O.AplicaPara,
                CE.CumplimientoID,
                ISNULL(CE.Estado, 'Pendiente') as Estado,
                ISNULL(CE.PorcentajeAvance, 0) as PorcentajeAvance,
                CE.Responsable,
                CE.FechaTermino,
                CE.ObservacionesCiberseguridad,
                CE.ObservacionesLegales
            FROM Obligaciones O
            LEFT JOIN CumplimientoEmpresa CE ON O.ObligacionID = CE.ObligacionID AND CE.EmpresaID = ?
            WHERE O.AplicaPara IN ('AMBAS', ?)
            ORDER BY O.ArticuloNorma, O.ObligacionID
        """
        
        cursor.execute(query_obligaciones, (empresa_id, empresa_info[1]))
        obligaciones = cursor.fetchall()
        
        print(f"\n✅ Encontradas {len(obligaciones)} obligaciones")
        
        # Buscar específicamente la que contiene DS 295, Art. 10
        obligacion_problema = None
        
        for obligacion in obligaciones:
            if "DS 295" in obligacion[1] and "10" in obligacion[1]:
                obligacion_problema = obligacion
                break
        
        if obligacion_problema:
            print(f"\n🎯 OBLIGACIÓN DS 295, ART.10 ENCONTRADA:")
            print("-" * 50)
            
            print(f"ObligacionID: {obligacion_problema[0]}")
            print(f"ArticuloNorma: {obligacion_problema[1]}")
            print(f"Descripcion: {obligacion_problema[2]}")
            print(f"MedioDeVerificacion: {obligacion_problema[3]}")
            print(f"CumplimientoID: {obligacion_problema[5]}")
            
            # Si tiene cumplimiento, buscar sus evidencias
            if obligacion_problema[5]:
                print(f"\n📁 EVIDENCIAS PARA CUMPLIMIENTO {obligacion_problema[5]}:")
                print("-" * 40)
                
                # Query para obtener evidencias con resumen
                cursor.execute("""
                    SELECT 
                        EvidenciaID,
                        NombreArchivoOriginal,
                        Descripcion,
                        FechaSubida,
                        Version,
                        TipoArchivo
                    FROM EvidenciasCumplimiento
                    WHERE CumplimientoID = ?
                    ORDER BY FechaSubida DESC
                """, (obligacion_problema[5],))
                
                evidencias = cursor.fetchall()
                
                if evidencias:
                    print(f"✅ Encontradas {len(evidencias)} evidencias:")
                    
                    for idx, evidencia in enumerate(evidencias, 1):
                        evidencia_id = evidencia[0]
                        nombre = evidencia[1] or "Sin nombre"
                        descripcion = evidencia[2] or ""
                        fecha = evidencia[3]
                        version = evidencia[4]
                        tipo = evidencia[5] or ""
                        
                        print(f"\n{idx}. EvidenciaID: {evidencia_id}")
                        print(f"   Nombre: {nombre}")
                        
                        # Verificar si contiene caracteres problemáticos
                        if 'Ã' in nombre:
                            print(f"   🎯 PROBLEMA DETECTADO: {nombre}")
                            print(f"   🔍 Contiene caracteres mal codificados!")
                            
                            # Intentar decodificar correctamente
                            try:
                                # Si fue guardado como UTF-8 pero interpretado como Latin-1
                                nombre_bytes = nombre.encode('latin-1')
                                nombre_corregido = nombre_bytes.decode('utf-8')
                                print(f"   ✅ Posible corrección: {nombre_corregido}")
                            except:
                                # Corrección manual
                                nombre_corregido = nombre.replace('ejecuciÃ³n', 'ejecución')
                                print(f"   ✅ Corrección manual: {nombre_corregido}")
                        
                        print(f"   Descripción: {descripcion}")
                        print(f"   Fecha: {fecha}")
                        print(f"   Versión: {version}")
                        print(f"   Tipo: {tipo}")
                        
                else:
                    print("❌ No hay evidencias para este cumplimiento")
            else:
                print("\n📝 No hay cumplimiento registrado para esta obligación")
        else:
            print("\n❌ No se encontró la obligación DS 295, Art. 10")
            
            # Mostrar las que sí contienen DS 295
            print("\n🔍 Obligaciones que contienen 'DS 295':")
            for obligacion in obligaciones:
                if "DS 295" in obligacion[1]:
                    print(f"  - {obligacion[0]}: {obligacion[1]}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    simular_endpoint_acompanamiento()
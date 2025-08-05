"""
Script para simular lo que devuelve el endpoint
"""
import pyodbc
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import get_db_connection

def simular_endpoint(incidente_id):
    """Simula exactamente lo que hace el endpoint"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print(f"\n{'='*70}")
        print(f"SIMULANDO ENDPOINT PARA INCIDENTE {incidente_id}")
        print(f"{'='*70}\n")
        
        # Ejecutar la misma query que el endpoint (con la corrección)
        cursor.execute("""
            SELECT 
                it.Id_Taxonomia,
                COALESCE(ti.Categoria_del_Incidente + ' - ' + ti.Subcategoria_del_Incidente, ti.Categoria_del_Incidente) as Nombre,
                ti.Area,
                ti.Efecto,
                ti.Categoria_del_Incidente as Categoria,
                ti.Subcategoria_del_Incidente as Subcategoria,
                ti.AplicaTipoEmpresa as Tipo,
                ti.Descripcion,
                it.Comentarios as Justificacion,
                '' as DescripcionProblema,
                it.FechaAsignacion
            FROM INCIDENTE_TAXONOMIA it
            INNER JOIN Taxonomia_incidentes ti ON it.Id_Taxonomia = ti.Id_Incidente
            WHERE it.IncidenteID = ?
        """, (incidente_id,))
        
        taxonomias_rows = cursor.fetchall()
        taxonomias_seleccionadas = []
        
        print(f"✅ Query ejecutada. Registros encontrados: {len(taxonomias_rows)}\n")
        
        for row in taxonomias_rows:
            tax_data = {
                'id': row[0],
                'nombre': row[1],
                'area': row[2],
                'efecto': row[3],
                'categoria': row[4],
                'subcategoria': row[5],
                'tipo': row[6],
                'descripcion': row[7],
                'justificacion': row[8] or '',
                'descripcionProblema': row[9] or '',
                'fechaSeleccion': row[10].isoformat() if row[10] else None,
                'archivos': []
            }
            taxonomias_seleccionadas.append(tax_data)
            
            # Mostrar cada taxonomía
            print(f"Taxonomía {len(taxonomias_seleccionadas)}:")
            print(f"  ID: '{tax_data['id']}' (tipo: {type(tax_data['id']).__name__})")
            print(f"  Nombre: {tax_data['nombre']}")
            print(f"  Área: {tax_data['area']}")
            print(f"  Justificación: {tax_data['justificacion'][:50]}...")
            print()
        
        # Guardar resultado como JSON
        resultado = {
            'incidente_id': incidente_id,
            'taxonomias_seleccionadas': taxonomias_seleccionadas
        }
        
        with open('simulacion_endpoint_result.json', 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Resultado guardado en simulacion_endpoint_result.json")
        
        # Mostrar los IDs para debug
        print(f"\n🔍 IDs de taxonomías seleccionadas:")
        for tax in taxonomias_seleccionadas:
            print(f"   - '{tax['id']}' (tipo: {type(tax['id']).__name__})")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    incidente_id = 5
    if len(sys.argv) > 1:
        incidente_id = int(sys.argv[1])
    
    simular_endpoint(incidente_id)
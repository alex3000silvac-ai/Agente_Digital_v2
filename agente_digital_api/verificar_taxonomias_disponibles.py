"""
Script para verificar las taxonomías disponibles y su formato
"""
import pyodbc
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import get_db_connection

def verificar_taxonomias_disponibles():
    """Verifica las taxonomías disponibles en el sistema"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("VERIFICANDO TAXONOMÍAS DISPONIBLES")
        print("="*70 + "\n")
        
        # Query para obtener todas las taxonomías (como lo hace el endpoint de taxonomías disponibles)
        cursor.execute("""
            SELECT 
                Id_Incidente,
                Area,
                Efecto,
                Categoria_del_Incidente,
                Subcategoria_del_Incidente,
                AplicaTipoEmpresa,
                Descripcion
            FROM Taxonomia_incidentes
            ORDER BY Area, Efecto, Categoria_del_Incidente
        """)
        
        taxonomias = cursor.fetchall()
        
        print(f"✅ Total de taxonomías disponibles: {len(taxonomias)}\n")
        
        # Mostrar algunas que coincidan con las seleccionadas
        ids_seleccionados = ['INC_CONF_EXCF_FCRA', 'INC_CONF_EXCF_FSRA', 'INC_CONF_EXCS_ACVE']
        
        print("📋 Taxonomías que coinciden con las seleccionadas:")
        print("-" * 70)
        
        for tax in taxonomias:
            if tax[0] in ids_seleccionados:
                print(f"\nID: '{tax[0]}' (tipo: {type(tax[0]).__name__})")
                print(f"Área: {tax[1]}")
                print(f"Efecto: {tax[2]}")
                print(f"Categoría: {tax[3]}")
                print(f"Subcategoría: {tax[4]}")
                print(f"Aplica a: {tax[5]}")
                print(f"Descripción: {tax[6][:50]}...")
        
        # Simular el formato que usa el frontend
        print("\n\n" + "="*70)
        print("FORMATO QUE ESPERA EL FRONTEND PARA TAXONOMÍAS DISPONIBLES:")
        print("="*70 + "\n")
        
        # Tomar las primeras 3 taxonomías como ejemplo
        taxonomias_formato_frontend = []
        for tax in taxonomias[:3]:
            tax_frontend = {
                'id': tax[0],  # Id_Incidente
                'area': tax[1],
                'efecto': tax[2],
                'categoria': tax[3],
                'subcategoria': tax[4],
                'tipo': tax[5],
                'descripcion': tax[6],
                'nombre': f"{tax[3]} - {tax[4]}" if tax[4] else tax[3]
            }
            taxonomias_formato_frontend.append(tax_frontend)
        
        print("Ejemplo de taxonomías disponibles (primeras 3):")
        for idx, tax in enumerate(taxonomias_formato_frontend, 1):
            print(f"\n{idx}. Taxonomía:")
            print(f"   ID: '{tax['id']}' (tipo: {type(tax['id']).__name__})")
            print(f"   Nombre: {tax['nombre']}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verificar_taxonomias_disponibles()
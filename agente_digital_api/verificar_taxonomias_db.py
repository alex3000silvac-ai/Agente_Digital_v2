"""
Script para verificar taxonomías en la base de datos
"""
import pyodbc
import sys
import os
import json

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db_connection

def verificar_taxonomias_incidente(incidente_id):
    """Verifica las taxonomías guardadas para un incidente específico"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print(f"\n{'='*60}")
        print(f"VERIFICANDO TAXONOMÍAS PARA INCIDENTE {incidente_id}")
        print(f"{'='*60}\n")
        
        # 1. Verificar si el incidente existe
        cursor.execute("""
            SELECT IncidenteID, Titulo, EstadoActual, ReporteAnciID
            FROM INCIDENTES
            WHERE IncidenteID = ?
        """, (incidente_id,))
        
        incidente = cursor.fetchone()
        if not incidente:
            print(f"❌ No se encontró el incidente {incidente_id}")
            return
            
        print(f"✅ Incidente encontrado:")
        print(f"   - ID: {incidente[0]}")
        print(f"   - Título: {incidente[1]}")
        print(f"   - Estado: {incidente[2]}")
        print(f"   - ReporteAnciID: {incidente[3]}")
        
        # 2. Verificar tabla INCIDENTE_TAXONOMIA
        print(f"\n📋 VERIFICANDO TABLA INCIDENTE_TAXONOMIA:")
        print(f"{'='*50}")
        
        # Primero verificar las columnas que existen
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'INCIDENTE_TAXONOMIA'
        """)
        columnas = [row[0] for row in cursor.fetchall()]
        print(f"Columnas en INCIDENTE_TAXONOMIA: {columnas}")
        
        # Ahora hacer la consulta con los nombres correctos
        cursor.execute("""
            SELECT 
                it.*
            FROM INCIDENTE_TAXONOMIA it
            WHERE it.IncidenteID = ?
        """, (incidente_id,))
        
        taxonomias = cursor.fetchall()
        
        if not taxonomias:
            print("❌ No hay taxonomías guardadas para este incidente")
            
            # Verificar si hay registros sin JOIN
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INCIDENTE_TAXONOMIA 
                WHERE IncidenteID = ?
            """, (incidente_id,))
            count = cursor.fetchone()[0]
            print(f"\n   Registros en INCIDENTE_TAXONOMIA: {count}")
            
        else:
            print(f"✅ Se encontraron {len(taxonomias)} taxonomías:\n")
            
            for idx, tax in enumerate(taxonomias, 1):
                print(f"{idx}. TaxonomiaID: {tax[0]}")
                print(f"   Nombre: {tax[5]}")
                print(f"   Área: {tax[6]}")
                print(f"   Efecto: {tax[7]}")
                print(f"   Categoría: {tax[8]}")
                print(f"   Subcategoría: {tax[9]}")
                print(f"   Justificación: {tax[1][:100] + '...' if tax[1] and len(tax[1]) > 100 else tax[1]}")
                print(f"   Descripción Problema: {tax[2][:100] + '...' if tax[2] and len(tax[2]) > 100 else tax[2]}")
                print(f"   Fecha Selección: {tax[3]}")
                print(f"   Usuario: {tax[4]}")
                print(f"   {'-'*40}")
        
        # 3. Verificar archivos asociados a taxonomías
        print(f"\n📎 VERIFICANDO ARCHIVOS DE TAXONOMÍAS:")
        print(f"{'='*50}")
        
        cursor.execute("""
            SELECT 
                et.TaxonomiaID,
                COUNT(*) as CantidadArchivos
            FROM EVIDENCIAS_TAXONOMIA et
            WHERE et.IncidenteID = ?
            GROUP BY et.TaxonomiaID
        """, (incidente_id,))
        
        archivos_tax = cursor.fetchall()
        
        if archivos_tax:
            for tax_arch in archivos_tax:
                print(f"   TaxonomiaID {tax_arch[0]}: {tax_arch[1]} archivo(s)")
        else:
            print("   No hay archivos asociados a taxonomías")
        
        # 4. Verificar estructura de datos para debug
        print(f"\n🔍 ESTRUCTURA DE DATOS (para debug):")
        print(f"{'='*50}")
        
        if taxonomias:
            # Crear estructura como la espera el frontend
            taxonomias_formato_frontend = []
            
            for tax in taxonomias:
                tax_dict = {
                    'id': tax[0],  # TaxonomiaID
                    'TaxonomiaID': tax[0],
                    'nombre': tax[5],
                    'area': tax[6],
                    'efecto': tax[7],
                    'categoria': tax[8],
                    'subcategoria': tax[9],
                    'justificacion': tax[1],
                    'Justificacion': tax[1],  # También con mayúscula
                    'descripcionProblema': tax[2],
                    'fechaSeleccion': tax[3].isoformat() if tax[3] else None,
                    'usuarioSeleccion': tax[4]
                }
                taxonomias_formato_frontend.append(tax_dict)
            
            print("\nFormato JSON que debería recibir el frontend:")
            print(json.dumps(taxonomias_formato_frontend[0], indent=2, ensure_ascii=False))
            
            # Verificar tipos de datos
            print(f"\nTIPOS DE DATOS:")
            print(f"   TaxonomiaID: {type(taxonomias[0][0]).__name__}")
            print(f"   Valor: {taxonomias[0][0]}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Puedes cambiar este ID por el que necesites verificar
    incidente_id = 5  # Por defecto el incidente 5
    
    if len(sys.argv) > 1:
        incidente_id = int(sys.argv[1])
    
    verificar_taxonomias_incidente(incidente_id)
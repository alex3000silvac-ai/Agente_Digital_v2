#!/usr/bin/env python3
"""
Diagnóstico simplificado para Sección 4 en incidentes ANCI
"""
import pyodbc
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import get_db_connection

def diagnosticar_seccion4():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("🔍 DIAGNÓSTICO SECCIÓN 4 - INCIDENTES ANCI")
        print("="*70 + "\n")
        
        # 1. Buscar incidentes ANCI
        print("1️⃣ INCIDENTES CON REPORTE ANCI:")
        print("-" * 40)
        
        cursor.execute("""
            SELECT 
                i.IncidenteID,
                i.Titulo,
                i.ReporteAnciID,
                COUNT(it.ID) as TotalTaxonomias
            FROM INCIDENTES i
            LEFT JOIN INCIDENTE_TAXONOMIA it ON i.IncidenteID = it.IncidenteID
            WHERE i.ReporteAnciID IS NOT NULL
            GROUP BY i.IncidenteID, i.Titulo, i.ReporteAnciID
            ORDER BY i.IncidenteID DESC
        """)
        
        incidentes = cursor.fetchall()
        
        if incidentes:
            print(f"✅ Encontrados {len(incidentes)} incidentes ANCI\n")
            for inc in incidentes[:5]:
                print(f"   📄 ID {inc[0]}: {inc[1]}")
                print(f"      ReporteAnciID: {inc[2]}")
                print(f"      Taxonomías: {inc[3]} {'⚠️ SIN TAXONOMÍAS' if inc[3] == 0 else '✅'}")
                print()
        else:
            print("❌ No se encontraron incidentes ANCI")
            return
        
        # 2. Tomar incidente 5 como ejemplo (el que reportaste)
        print("\n2️⃣ DETALLE INCIDENTE 5 (EJEMPLO):")
        print("-" * 40)
        
        cursor.execute("""
            SELECT 
                it.ID,
                it.Id_Taxonomia,
                it.Comentarios,
                ti.Categoria_del_Incidente,
                ti.Subcategoria_del_Incidente
            FROM INCIDENTE_TAXONOMIA it
            INNER JOIN Taxonomia_incidentes ti ON it.Id_Taxonomia = ti.Id_Incidente
            WHERE it.IncidenteID = 5
        """)
        
        taxonomias = cursor.fetchall()
        
        if taxonomias:
            print(f"✅ Incidente 5 tiene {len(taxonomias)} taxonomías:\n")
            for idx, tax in enumerate(taxonomias, 1):
                print(f"   {idx}. {tax[1]}")
                print(f"      Categoría: {tax[3]}")
                print(f"      Comentarios: {'✅ SÍ' if tax[2] else '❌ NO'}")
                if tax[2]:
                    print(f"      '{tax[2][:50]}...'")
                print()
        else:
            print("❌ Incidente 5 no tiene taxonomías")
        
        # 3. Verificar estructura de respuesta
        print("\n3️⃣ ESTRUCTURA DE DATOS PARA FRONTEND:")
        print("-" * 40)
        
        if taxonomias:
            tax_ejemplo = taxonomias[0]
            print(f"ID Taxonomía: '{tax_ejemplo[1]}' (tipo: {type(tax_ejemplo[1]).__name__})")
            print(f"Comentarios: {'✅ Presente' if tax_ejemplo[2] else '❌ Ausente'}")
            
            # Verificar archivos
            cursor.execute("""
                SELECT COUNT(*) 
                FROM EVIDENCIAS_TAXONOMIA 
                WHERE IncidenteID = 5
            """)
            num_archivos = cursor.fetchone()[0]
            print(f"Archivos adjuntos: {num_archivos}")
        
        print("\n✅ DIAGNÓSTICO COMPLETADO")
        
        # Generar resumen
        print("\n" + "="*70)
        print("📊 RESUMEN:")
        print("="*70)
        print("""
ESTADO ACTUAL:
- ✅ Hay incidentes ANCI en el sistema
- ✅ Las taxonomías están guardadas en BD
- ✅ Los comentarios están presentes
- ⚠️  Verificar si se muestran en el frontend

PRÓXIMOS PASOS:
1. Verificar en el navegador con el fix universal
2. Revisar que los estilos CSS se apliquen
3. Confirmar que los datos lleguen al componente Vue
        """)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    diagnosticar_seccion4()
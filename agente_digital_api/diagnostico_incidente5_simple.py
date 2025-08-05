#!/usr/bin/env python3
"""
Diagnóstico simplificado para Incidente 5
"""
import pyodbc
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import get_db_connection

def diagnosticar():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("🔍 DIAGNÓSTICO INCIDENTE 5 - ESTADÍSTICAS")
        print("="*70 + "\n")
        
        # 1. Datos básicos
        print("1️⃣ INCIDENTE:")
        cursor.execute("SELECT IncidenteID, Titulo, ReporteAnciID FROM INCIDENTES WHERE IncidenteID = 5")
        inc = cursor.fetchone()
        if inc:
            print(f"   ✅ ID: {inc[0]}, Título: {inc[1]}")
            print(f"   ✅ ReporteAnciID: {inc[2]}")
        
        # 2. Contar evidencias
        print("\n2️⃣ EVIDENCIAS/ARCHIVOS:")
        
        # Evidencias por sección
        cursor.execute("""
            SELECT COUNT(*) FROM EVIDENCIAS_INCIDENTE WHERE IncidenteID = 5
        """)
        evidencias_secciones = cursor.fetchone()[0]
        print(f"   📎 Archivos en secciones: {evidencias_secciones}")
        
        # Archivos en taxonomías
        cursor.execute("""
            SELECT COUNT(*) FROM EVIDENCIAS_TAXONOMIA WHERE IncidenteID = 5
        """)
        archivos_taxonomias = cursor.fetchone()[0]
        print(f"   📎 Archivos en taxonomías: {archivos_taxonomias}")
        print(f"   📎 TOTAL EVIDENCIAS: {evidencias_secciones + archivos_taxonomias}")
        
        # 3. Taxonomías y comentarios
        print("\n3️⃣ TAXONOMÍAS SELECCIONADAS:")
        cursor.execute("""
            SELECT 
                it.Id_Taxonomia,
                it.Comentarios,
                it.DescripcionProblema
            FROM INCIDENTE_TAXONOMIA it
            WHERE it.IncidenteID = 5
        """)
        
        taxonomias = cursor.fetchall()
        comentarios_tax = 0
        
        print(f"   ✅ Total taxonomías: {len(taxonomias)}")
        for tax in taxonomias:
            if tax[1]:  # Comentarios
                comentarios_tax += 1
            if tax[2]:  # DescripcionProblema
                comentarios_tax += 1
        
        print(f"   💬 Comentarios en taxonomías: {comentarios_tax}")
        
        # 4. Comentarios CSIRT
        cursor.execute("""
            SELECT ObservacionesCSIRT FROM INCIDENTES WHERE IncidenteID = 5
        """)
        obs_csirt = cursor.fetchone()[0]
        comentarios_csirt = 1 if obs_csirt else 0
        print(f"   💬 Comentarios CSIRT: {comentarios_csirt}")
        
        # 5. Calcular completitud
        print("\n4️⃣ COMPLETITUD:")
        
        # Contar campos llenos
        campos = ['Titulo', 'Criticidad', 'DescripcionInicial', 'AccionesInmediatas']
        query = f"SELECT {', '.join(campos)} FROM INCIDENTES WHERE IncidenteID = 5"
        cursor.execute(query)
        
        valores = cursor.fetchone()
        campos_llenos = sum(1 for v in valores if v and str(v).strip())
        total_campos = len(campos) + 1  # +1 por taxonomías
        
        if len(taxonomias) > 0:
            campos_llenos += 1
        
        completitud = round((campos_llenos / total_campos) * 100)
        print(f"   📊 Campos llenos: {campos_llenos}/{total_campos}")
        print(f"   📊 Completitud: {completitud}%")
        
        # RESUMEN
        print("\n" + "="*70)
        print("📊 ESTADÍSTICAS FINALES:")
        print("="*70)
        
        total_evidencias = evidencias_secciones + archivos_taxonomias
        total_comentarios = comentarios_tax + comentarios_csirt
        
        print(f"""
TARJETA EXPEDIENTE SEMILLA DEBE MOSTRAR:
---------------------------------------
📎 Evidencias: {total_evidencias}
💬 Comentarios: {total_comentarios}
📊 Completado: {completitud}%
        """)
        
        # Generar objeto para frontend
        print("\n📄 OBJETO PARA INYECTAR EN FRONTEND:")
        stats = {
            "TotalEvidencias": total_evidencias,
            "TotalComentarios": total_comentarios,
            "Completitud": completitud
        }
        print(json.dumps(stats, indent=2))
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    diagnosticar()
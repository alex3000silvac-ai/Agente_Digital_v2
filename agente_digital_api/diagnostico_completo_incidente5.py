#!/usr/bin/env python3
"""
Diagnóstico completo para Incidente 5 - Vista ANCI
Verifica estadísticas y taxonomías seleccionadas
"""
import pyodbc
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import get_db_connection

def diagnosticar_incidente5():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("🔍 DIAGNÓSTICO COMPLETO - INCIDENTE 5 ANCI")
        print("="*70 + "\n")
        
        # 1. Verificar datos básicos del incidente
        print("1️⃣ DATOS BÁSICOS DEL INCIDENTE:")
        print("-" * 40)
        
        cursor.execute("""
            SELECT 
                IncidenteID,
                Titulo,
                ReporteAnciID,
                TipoEmpresa,
                FechaTransformacionANCI,
                EmpresaID,
                InquilinoID
            FROM INCIDENTES 
            WHERE IncidenteID = 5
        """)
        
        incidente = cursor.fetchone()
        if incidente:
            print(f"✅ Incidente encontrado:")
            print(f"   - ID: {incidente[0]}")
            print(f"   - Título: {incidente[1]}")
            print(f"   - ReporteAnciID: {incidente[2]}")
            print(f"   - Tipo Empresa: {incidente[3]}")
            print(f"   - Fecha ANCI: {incidente[4]}")
            print(f"   - EmpresaID: {incidente[5]}")
            print(f"   - InquilinoID: {incidente[6]}")
        else:
            print("❌ Incidente 5 no encontrado")
            return
        
        # 2. Contar archivos/evidencias
        print("\n2️⃣ ARCHIVOS/EVIDENCIAS:")
        print("-" * 40)
        
        cursor.execute("""
            SELECT 
                Seccion,
                COUNT(*) as Total
            FROM EVIDENCIAS_INCIDENTE
            WHERE IncidenteID = 5
            GROUP BY Seccion
            ORDER BY Seccion
        """)
        
        total_evidencias = 0
        for row in cursor.fetchall():
            print(f"   Sección {row[0]}: {row[1]} archivos")
            total_evidencias += row[1]
        
        print(f"\n   📎 TOTAL EVIDENCIAS: {total_evidencias}")
        
        # 3. Verificar taxonomías seleccionadas
        print("\n3️⃣ TAXONOMÍAS SELECCIONADAS:")
        print("-" * 40)
        
        cursor.execute("""
            SELECT 
                it.ID,
                it.Id_Taxonomia,
                it.Comentarios,
                it.DescripcionProblema,
                ti.Categoria_del_Incidente,
                ti.Subcategoria_del_Incidente
            FROM INCIDENTE_TAXONOMIA it
            INNER JOIN Taxonomia_incidentes ti ON it.Id_Taxonomia = ti.Id_Incidente
            WHERE it.IncidenteID = 5
        """)
        
        taxonomias = cursor.fetchall()
        total_comentarios = 0
        
        if taxonomias:
            print(f"✅ {len(taxonomias)} taxonomías seleccionadas:\n")
            for idx, tax in enumerate(taxonomias, 1):
                print(f"   {idx}. ID: {tax[1]}")
                print(f"      Categoría: {tax[4]}")
                if tax[5]:
                    print(f"      Subcategoría: {tax[5]}")
                
                # Contar comentarios
                if tax[2]:  # Comentarios/Justificación
                    total_comentarios += 1
                    print(f"      ✅ Justificación: '{tax[2][:50]}...'")
                else:
                    print(f"      ❌ Sin justificación")
                    
                if tax[3]:  # Descripción del problema
                    total_comentarios += 1
                    print(f"      ✅ Descripción problema: '{tax[3][:50]}...'")
                else:
                    print(f"      ❌ Sin descripción del problema")
                print()
        else:
            print("❌ No hay taxonomías seleccionadas")
        
        print(f"   💬 TOTAL COMENTARIOS EN TAXONOMÍAS: {total_comentarios}")
        
        # 4. Verificar archivos de taxonomías
        print("\n4️⃣ ARCHIVOS EN TAXONOMÍAS:")
        print("-" * 40)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as TotalArchivos
            FROM EVIDENCIAS_TAXONOMIA
            WHERE IncidenteID = 5
        """)
        
        archivos_tax = cursor.fetchone()[0]
        print(f"   📎 Archivos adjuntos en taxonomías: {archivos_tax}")
        
        # 5. Verificar campos CSIRT
        print("\n5️⃣ CAMPOS CSIRT:")
        print("-" * 40)
        
        cursor.execute("""
            SELECT 
                SolicitarCSIRT,
                TipoApoyoCSIRT,
                UrgenciaCSIRT,
                ObservacionesCSIRT
            FROM INCIDENTES
            WHERE IncidenteID = 5
        """)
        
        csirt = cursor.fetchone()
        comentarios_csirt = 0
        if csirt:
            print(f"   Solicitar CSIRT: {csirt[0]}")
            if csirt[0]:  # Si solicitó CSIRT
                print(f"   Tipo Apoyo: {csirt[1]}")
                print(f"   Urgencia: {csirt[2]}")
                if csirt[3]:
                    comentarios_csirt = 1
                    print(f"   ✅ Observaciones: '{csirt[3][:50]}...'")
                else:
                    print(f"   ❌ Sin observaciones")
        
        # 6. Calcular completitud
        print("\n6️⃣ CÁLCULO DE COMPLETITUD:")
        print("-" * 40)
        
        # Campos principales para verificar
        campos_verificar = [
            'Titulo', 'TipoRegistro', 'FechaDeteccion', 'FechaOcurrencia',
            'Criticidad', 'AlcanceGeografico', 'DescripcionInicial',
            'AnciImpactoPreliminar', 'SistemasAfectados', 'ServiciosInterrumpidos',
            'OrigenIncidente', 'AnciTipoAmenaza', 'ResponsableCliente',
            'AccionesInmediatas', 'CausaRaiz', 'LeccionesAprendidas', 'PlanMejora'
        ]
        
        campos_query = ', '.join(campos_verificar)
        cursor.execute(f"SELECT {campos_query} FROM INCIDENTES WHERE IncidenteID = 5")
        
        valores = cursor.fetchone()
        campos_llenos = 0
        total_campos = len(campos_verificar)
        
        if valores:
            for idx, valor in enumerate(valores):
                if valor and str(valor).strip():
                    campos_llenos += 1
                    print(f"   ✅ {campos_verificar[idx]}")
                else:
                    print(f"   ❌ {campos_verificar[idx]}")
        
        # Agregar taxonomías a la completitud
        if len(taxonomias) > 0:
            campos_llenos += 2
            total_campos += 2
            print(f"   ✅ Taxonomías seleccionadas ({len(taxonomias)})")
        else:
            total_campos += 1
            print(f"   ❌ Taxonomías seleccionadas")
        
        completitud = round((campos_llenos / total_campos) * 100) if total_campos > 0 else 0
        
        # RESUMEN FINAL
        print("\n" + "="*70)
        print("📊 ESTADÍSTICAS FINALES PARA MOSTRAR:")
        print("="*70)
        print(f"""
VALORES QUE DEBERÍAN APARECER EN LA TARJETA:
-------------------------------------------
📎 Total Evidencias: {total_evidencias + archivos_tax}
💬 Total Comentarios: {total_comentarios + comentarios_csirt}
📊 Completitud: {completitud}%

DESGLOSE:
- Evidencias en secciones: {total_evidencias}
- Archivos en taxonomías: {archivos_tax}
- Comentarios en taxonomías: {total_comentarios}
- Comentarios CSIRT: {comentarios_csirt}
- Campos llenos: {campos_llenos}/{total_campos}
        """)
        
        # 7. Generar JSON para debug
        datos_json = {
            "incidenteId": 5,
            "estadisticas": {
                "totalEvidencias": total_evidencias + archivos_tax,
                "totalComentarios": total_comentarios + comentarios_csirt,
                "completitud": completitud
            },
            "taxonomias_seleccionadas": [
                {
                    "id": tax[1],
                    "categoria": tax[4],
                    "tiene_justificacion": bool(tax[2]),
                    "tiene_descripcion": bool(tax[3])
                } for tax in taxonomias
            ]
        }
        
        print("\n📄 JSON para debug frontend:")
        print(json.dumps(datos_json, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    diagnosticar_incidente5()
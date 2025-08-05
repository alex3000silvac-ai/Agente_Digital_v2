#!/usr/bin/env python3
"""
Script de Diagnóstico Automático para Sección 4 (Taxonomías) en Incidentes ANCI
Identifica todos los problemas relacionados con visualización, comentarios y archivos
"""
import pyodbc
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import get_db_connection

def diagnosticar_seccion4_anci():
    """Diagnóstico completo de problemas en Sección 4 para incidentes ANCI"""
    conn = None
    problemas_encontrados = []
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*80)
        print("🔍 DIAGNÓSTICO AUTOMÁTICO - SECCIÓN 4 (TAXONOMÍAS) EN INCIDENTES ANCI")
        print("="*80 + "\n")
        
        # 1. VERIFICAR INCIDENTES ANCI CON TAXONOMÍAS
        print("1️⃣ VERIFICANDO INCIDENTES ANCI CON TAXONOMÍAS")
        print("-" * 50)
        
        cursor.execute("""
            SELECT 
                i.IncidenteID,
                i.Titulo,
                i.ReporteAnciID,
                i.TieneReporteANCI,
                COUNT(it.ID) as TotalTaxonomias
            FROM INCIDENTES i
            LEFT JOIN INCIDENTE_TAXONOMIA it ON i.IncidenteID = it.IncidenteID
            WHERE i.ReporteAnciID IS NOT NULL OR i.TieneReporteANCI = 1
            GROUP BY i.IncidenteID, i.Titulo, i.ReporteAnciID, i.TieneReporteANCI
            ORDER BY i.IncidenteID DESC
        """)
        
        incidentes_anci = cursor.fetchall()
        
        if not incidentes_anci:
            print("❌ No se encontraron incidentes ANCI")
            problemas_encontrados.append("No hay incidentes ANCI en el sistema")
        else:
            print(f"✅ Encontrados {len(incidentes_anci)} incidentes ANCI\n")
            
            for inc in incidentes_anci[:5]:  # Mostrar primeros 5
                print(f"   📄 Incidente {inc[0]}: {inc[1]}")
                print(f"      ReporteAnciID: {inc[2]}")
                print(f"      Taxonomías: {inc[4]}")
                
                if inc[4] == 0:
                    print(f"      ⚠️  SIN TAXONOMÍAS ASIGNADAS")
                    problemas_encontrados.append(f"Incidente ANCI {inc[0]} sin taxonomías")
                print()
        
        # 2. VERIFICAR DETALLES DE TAXONOMÍAS
        print("\n2️⃣ VERIFICANDO DETALLES DE TAXONOMÍAS SELECCIONADAS")
        print("-" * 50)
        
        # Tomar un incidente ANCI de ejemplo
        if incidentes_anci:
            incidente_ejemplo = incidentes_anci[0][0]
            
            cursor.execute("""
                SELECT 
                    it.ID,
                    it.Id_Taxonomia,
                    it.Comentarios,
                    it.FechaAsignacion,
                    ti.Categoria_del_Incidente,
                    ti.Subcategoria_del_Incidente,
                    ti.Descripcion
                FROM INCIDENTE_TAXONOMIA it
                INNER JOIN Taxonomia_incidentes ti ON it.Id_Taxonomia = ti.Id_Incidente
                WHERE it.IncidenteID = ?
            """, (incidente_ejemplo,))
            
            taxonomias_detalle = cursor.fetchall()
            
            if taxonomias_detalle:
                print(f"✅ Incidente {incidente_ejemplo} tiene {len(taxonomias_detalle)} taxonomías:\n")
                
                for idx, tax in enumerate(taxonomias_detalle, 1):
                    print(f"   {idx}. Taxonomía ID: {tax[1]}")
                    print(f"      Categoría: {tax[4]}")
                    print(f"      Comentarios: {'✅ SÍ' if tax[2] else '❌ NO'}")
                    
                    if not tax[2]:
                        problemas_encontrados.append(f"Taxonomía {tax[1]} sin comentarios")
                    
                    # Verificar archivos
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM EVIDENCIAS_TAXONOMIA 
                        WHERE IncidenteTaxonomiaID = ?
                    """, (tax[0],))
                    
                    num_archivos = cursor.fetchone()[0]
                    print(f"      Archivos: {num_archivos}")
                    
                    if num_archivos == 0:
                        print(f"      ⚠️  SIN ARCHIVOS ADJUNTOS")
                    print()
            else:
                print(f"❌ Incidente {incidente_ejemplo} no tiene taxonomías")
                problemas_encontrados.append(f"Incidente {incidente_ejemplo} sin taxonomías guardadas")
        
        # 3. VERIFICAR ESTRUCTURA DE RESPUESTA DEL ENDPOINT
        print("\n3️⃣ SIMULANDO RESPUESTA DEL ENDPOINT")
        print("-" * 50)
        
        if incidentes_anci:
            incidente_test = incidentes_anci[0][0]
            
            # Simular query del endpoint
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
            """, (incidente_test,))
            
            taxonomias_endpoint = cursor.fetchall()
            
            if taxonomias_endpoint:
                print(f"✅ Endpoint devolvería {len(taxonomias_endpoint)} taxonomías")
                
                # Verificar estructura
                tax_ejemplo = taxonomias_endpoint[0]
                print(f"\n   Estructura de datos:")
                print(f"   - ID: '{tax_ejemplo[0]}' (tipo: {type(tax_ejemplo[0]).__name__})")
                print(f"   - Nombre: {tax_ejemplo[1]}")
                print(f"   - Justificación: {'✅ SÍ' if tax_ejemplo[8] else '❌ NO'}")
                
                # Verificar tipos de datos
                if isinstance(tax_ejemplo[0], int):
                    print(f"   ⚠️  ADVERTENCIA: ID es numérico, puede causar problemas de comparación")
                    problemas_encontrados.append("IDs de taxonomías son numéricos, requieren normalización")
            else:
                print(f"❌ Endpoint no devolvería taxonomías")
                problemas_encontrados.append("Endpoint no devuelve taxonomías")
        
        # 4. VERIFICAR ARCHIVOS DE TAXONOMÍAS
        print("\n\n4️⃣ VERIFICANDO ARCHIVOS ADJUNTOS A TAXONOMÍAS")
        print("-" * 50)
        
        cursor.execute("""
            SELECT 
                et.IncidenteID,
                COUNT(DISTINCT et.TaxonomiaID) as TaxonomiasConArchivos,
                COUNT(*) as TotalArchivos
            FROM EVIDENCIAS_TAXONOMIA et
            INNER JOIN INCIDENTES i ON et.IncidenteID = i.IncidenteID
            WHERE i.ReporteAnciID IS NOT NULL OR i.TieneReporteANCI = 1
            GROUP BY et.IncidenteID
        """)
        
        archivos_stats = cursor.fetchall()
        
        if archivos_stats:
            print(f"✅ Estadísticas de archivos en incidentes ANCI:\n")
            for stat in archivos_stats:
                print(f"   Incidente {stat[0]}: {stat[1]} taxonomías con archivos, {stat[2]} archivos totales")
        else:
            print("❌ No hay archivos adjuntos a taxonomías en incidentes ANCI")
            problemas_encontrados.append("No hay archivos en taxonomías ANCI")
        
        # 5. GENERAR RESUMEN Y SOLUCIONES
        print("\n\n" + "="*80)
        print("📊 RESUMEN DEL DIAGNÓSTICO")
        print("="*80 + "\n")
        
        if problemas_encontrados:
            print(f"❌ Se encontraron {len(problemas_encontrados)} problemas:\n")
            for idx, problema in enumerate(problemas_encontrados, 1):
                print(f"   {idx}. {problema}")
        else:
            print("✅ No se detectaron problemas evidentes en la base de datos")
        
        # 6. SOLUCIONES RECOMENDADAS
        print("\n\n🔧 SOLUCIONES RECOMENDADAS:")
        print("-" * 50)
        
        print("""
1. VERIFICAR COMPONENTE FRONTEND:
   - Revisar AcordeonIncidenteANCI.vue
   - Confirmar que taxonomiaSeleccionada() normaliza IDs
   - Verificar clases CSS para destacar seleccionadas

2. VERIFICAR ENDPOINT BACKEND:
   - Confirmar que devuelve taxonomias_seleccionadas
   - Incluir archivos en la respuesta
   - Normalizar tipos de datos

3. APLICAR FIX UNIVERSAL:
   - Ejecutar fix_taxonomias_anci_universal.js en consola
   - Agregar estilos CSS faltantes
   
4. VERIFICAR PERMISOS:
   - Confirmar que el usuario puede ver taxonomías ANCI
   - Revisar logs de errores en consola
        """)
        
        # 7. GENERAR SCRIPT SQL DE VERIFICACIÓN
        with open('verificar_taxonomias_anci.sql', 'w', encoding='utf-8') as f:
            f.write("""-- Script de verificación para taxonomías ANCI
-- Generado automáticamente

-- 1. Incidentes ANCI sin taxonomías
SELECT 
    i.IncidenteID, 
    i.Titulo,
    i.ReporteAnciID
FROM INCIDENTES i
LEFT JOIN INCIDENTE_TAXONOMIA it ON i.IncidenteID = it.IncidenteID
WHERE (i.ReporteAnciID IS NOT NULL OR i.TieneReporteANCI = 1)
  AND it.ID IS NULL;

-- 2. Taxonomías sin comentarios
SELECT 
    it.IncidenteID,
    it.Id_Taxonomia,
    it.Comentarios
FROM INCIDENTE_TAXONOMIA it
INNER JOIN INCIDENTES i ON it.IncidenteID = i.IncidenteID
WHERE (i.ReporteAnciID IS NOT NULL OR i.TieneReporteANCI = 1)
  AND (it.Comentarios IS NULL OR it.Comentarios = '');

-- 3. Taxonomías sin archivos
SELECT 
    it.IncidenteID,
    it.Id_Taxonomia,
    COUNT(et.EvidenciaID) as NumArchivos
FROM INCIDENTE_TAXONOMIA it
INNER JOIN INCIDENTES i ON it.IncidenteID = i.IncidenteID
LEFT JOIN EVIDENCIAS_TAXONOMIA et ON it.ID = et.IncidenteTaxonomiaID
WHERE (i.ReporteAnciID IS NOT NULL OR i.TieneReporteANCI = 1)
GROUP BY it.IncidenteID, it.Id_Taxonomia
HAVING COUNT(et.EvidenciaID) = 0;
""")
        
        print("\n💾 Script SQL guardado en: verificar_taxonomias_anci.sql")
        
    except Exception as e:
        print(f"\n❌ Error durante diagnóstico: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    diagnosticar_seccion4_anci()
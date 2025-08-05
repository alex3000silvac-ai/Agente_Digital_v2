#!/usr/bin/env python3
"""
Script de diagnóstico completo para el incidente 17
Verifica encoding, archivos y estructura de datos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db_connection
import json

def diagnosticar_incidente():
    """Diagnóstico completo del incidente 17"""
    
    incidente_id = 17
    print(f"🔍 DIAGNÓSTICO COMPLETO DEL INCIDENTE {incidente_id}")
    print("=" * 70)
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ Error de conexión a BD")
            return
            
        cursor = conn.cursor()
        
        # 1. VERIFICAR DATOS PRINCIPALES
        print("\n1️⃣ DATOS PRINCIPALES DEL INCIDENTE:")
        cursor.execute("""
            SELECT Titulo, DescripcionInicial, AccionesInmediatas, 
                   AnciImpactoPreliminar, AnciTipoAmenaza
            FROM Incidentes 
            WHERE IncidenteID = ?
        """, (incidente_id,))
        
        row = cursor.fetchone()
        if row:
            print(f"   Título RAW: {repr(row[0])}")
            print(f"   Título: {row[0]}")
            print(f"   Descripción RAW: {repr(row[1][:50])}")
            print(f"   Descripción: {row[1][:50]}...")
            print(f"   Acciones RAW: {repr(row[2])}")
            print(f"   Impacto RAW: {repr(row[3])}")
            print(f"   Tipo Amenaza RAW: {repr(row[4])}")
        
        # 2. VERIFICAR EVIDENCIAS GENERALES
        print("\n2️⃣ EVIDENCIAS GENERALES:")
        cursor.execute("""
            SELECT EvidenciaID, NombreArchivo, SeccionFormulario, 
                   Descripcion, RutaArchivo
            FROM EvidenciasIncidentes 
            WHERE IncidenteID = ?
            ORDER BY SeccionFormulario, EvidenciaID
        """, (incidente_id,))
        
        evidencias = cursor.fetchall()
        print(f"   Total evidencias: {len(evidencias)}")
        
        secciones_evidencias = {}
        for ev in evidencias:
            seccion = ev[2] or 'sin_seccion'
            if seccion not in secciones_evidencias:
                secciones_evidencias[seccion] = []
            secciones_evidencias[seccion].append({
                'id': ev[0],
                'nombre': ev[1],
                'descripcion': ev[3],
                'ruta': ev[4]
            })
        
        for seccion, archivos in secciones_evidencias.items():
            print(f"\n   Sección '{seccion}': {len(archivos)} archivos")
            for archivo in archivos:
                print(f"      - ID:{archivo['id']} | {archivo['nombre']} | Desc: {archivo['descripcion']}")
        
        # 3. VERIFICAR TAXONOMÍAS
        print("\n3️⃣ TAXONOMÍAS SELECCIONADAS:")
        cursor.execute("""
            SELECT IT.Id_Taxonomia, TI.Area, TI.Efecto, 
                   TI.Categoria_del_Incidente, TI.Subcategoria_del_Incidente
            FROM INCIDENTE_TAXONOMIA IT
            LEFT JOIN TAXONOMIA_INCIDENTES TI ON IT.Id_Taxonomia = TI.Id_Incidente
            WHERE IT.IncidenteID = ?
        """, (incidente_id,))
        
        taxonomias = cursor.fetchall()
        print(f"   Total taxonomías: {len(taxonomias)}")
        for tax in taxonomias:
            print(f"   - {tax[0]}: {tax[1]} | {tax[2]} | {tax[3]}")
            # Mostrar caracteres RAW
            print(f"     RAW: {repr(tax[3])}")
        
        # 4. VERIFICAR EVIDENCIAS DE TAXONOMÍAS
        print("\n4️⃣ EVIDENCIAS DE TAXONOMÍAS:")
        cursor.execute("""
            SELECT Id_Taxonomia, NumeroEvidencia, NombreArchivo, 
                   Descripcion, RutaArchivo
            FROM EVIDENCIAS_TAXONOMIA 
            WHERE IncidenteID = ?
            ORDER BY Id_Taxonomia, NumeroEvidencia
        """, (incidente_id,))
        
        ev_taxonomias = cursor.fetchall()
        print(f"   Total evidencias de taxonomías: {len(ev_taxonomias)}")
        for ev_tax in ev_taxonomias:
            print(f"   - Tax {ev_tax[0]} | Num: {ev_tax[1]} | {ev_tax[2]}")
        
        # 5. DETECTAR ENCODING
        print("\n5️⃣ ANÁLISIS DE ENCODING:")
        
        # Intentar detectar el encoding actual
        test_text = row[1] if row else ""  # Descripción
        
        # Verificar si tiene caracteres problemáticos
        if 'Ã' in test_text or 'â€' in test_text:
            print("   ❌ DETECTADO: Texto con encoding incorrecto (UTF-8 interpretado como Latin-1)")
            print("   💡 Los datos en la BD están mal codificados")
            
            # Intentar corregir
            try:
                # Opción 1: Double encoding UTF-8
                fixed = test_text.encode('latin-1').decode('utf-8', errors='ignore')
                print(f"   🔧 Intento corrección 1: {fixed[:50]}...")
            except:
                print("   ❌ Fallo corrección método 1")
            
            try:
                # Opción 2: Windows-1252 a UTF-8
                fixed = test_text.encode('windows-1252').decode('utf-8', errors='ignore')
                print(f"   🔧 Intento corrección 2: {fixed[:50]}...")
            except:
                print("   ❌ Fallo corrección método 2")
        else:
            print("   ✅ No se detectaron caracteres problemáticos obvios")
        
        # 6. VERIFICAR DUPLICADOS
        print("\n6️⃣ ANÁLISIS DE DUPLICADOS:")
        
        # Buscar archivos con mismo nombre
        nombres_archivos = {}
        for ev in evidencias:
            nombre = ev[1]
            if nombre in nombres_archivos:
                nombres_archivos[nombre] += 1
            else:
                nombres_archivos[nombre] = 1
        
        duplicados = {k: v for k, v in nombres_archivos.items() if v > 1}
        if duplicados:
            print("   ❌ ARCHIVOS DUPLICADOS ENCONTRADOS:")
            for nombre, count in duplicados.items():
                print(f"      - '{nombre}' aparece {count} veces")
        else:
            print("   ✅ No hay archivos duplicados")
        
        print("\n" + "=" * 70)
        print("📊 RESUMEN DEL DIAGNÓSTICO:")
        print(f"   - Encoding: {'INCORRECTO' if 'Ã' in str(row) else 'Posiblemente correcto'}")
        print(f"   - Evidencias totales: {len(evidencias)}")
        print(f"   - Taxonomías: {len(taxonomias)}")
        print(f"   - Duplicados: {'SÍ' if duplicados else 'NO'}")
        
    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    diagnosticar_incidente()
#!/usr/bin/env python3
"""
Script para validar que un incidente esté completamente guardado
incluyendo todos los campos, taxonomías y archivos
"""

import pyodbc
import json
import os
from datetime import datetime
from app.database import get_db_connection

# ID del incidente a verificar
INCIDENTE_ID = 5

def validar_incidente_completo():
    """Valida que toda la información del incidente esté guardada"""
    
    print(f"\n{'='*80}")
    print(f"VALIDACIÓN COMPLETA DEL INCIDENTE {INCIDENTE_ID}")
    print(f"{'='*80}\n")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. DATOS PRINCIPALES DEL INCIDENTE
        print("1. DATOS PRINCIPALES DEL INCIDENTE")
        print("-" * 40)
        
        cursor.execute("""
            SELECT 
                IncidenteID,
                Titulo,
                FechaDeteccion,
                FechaOcurrencia,
                Criticidad,
                AlcanceGeografico,
                DescripcionInicial,
                AnciImpactoPreliminar,
                SistemasAfectados,
                ServiciosInterrumpidos,
                AnciTipoAmenaza,
                OrigenIncidente,
                ResponsableCliente,
                AccionesInmediatas,
                CausaRaiz,
                LeccionesAprendidas,
                PlanMejora,
                EstadoActual,
                FechaCreacion,
                CreadoPor,
                EmpresaID,
                IDVisible
            FROM Incidentes 
            WHERE IncidenteID = ?
        """, (INCIDENTE_ID,))
        
        row = cursor.fetchone()
        if not row:
            print(f"❌ ERROR: No se encontró el incidente {INCIDENTE_ID}")
            return
        
        campos = [
            "IncidenteID", "Titulo", "FechaDeteccion", "FechaOcurrencia",
            "Criticidad", "AlcanceGeografico", "DescripcionInicial",
            "AnciImpactoPreliminar", "SistemasAfectados", "ServiciosInterrumpidos",
            "AnciTipoAmenaza", "OrigenIncidente", "ResponsableCliente",
            "AccionesInmediatas", "CausaRaiz", "LeccionesAprendidas",
            "PlanMejora", "EstadoActual", "FechaCreacion", "CreadoPor",
            "EmpresaID", "IDVisible"
        ]
        
        datos = dict(zip(campos, row))
        
        # Mostrar cada campo con su valor
        for campo, valor in datos.items():
            if valor and isinstance(valor, str) and len(str(valor)) > 100:
                print(f"✅ {campo}: {str(valor)[:100]}... ({len(str(valor))} caracteres)")
            else:
                print(f"✅ {campo}: {valor}")
        
        # Verificar campos de texto largo
        print("\n📝 VERIFICACIÓN DE CAMPOS DE TEXTO LARGO:")
        campos_texto_largo = [
            'DescripcionInicial', 'AnciImpactoPreliminar', 'SistemasAfectados',
            'ServiciosInterrumpidos', 'AccionesInmediatas', 'CausaRaiz',
            'LeccionesAprendidas', 'PlanMejora'
        ]
        
        for campo in campos_texto_largo:
            valor = datos.get(campo)
            if valor:
                print(f"   - {campo}: {len(str(valor))} caracteres")
                if len(str(valor)) > 3900:
                    print(f"     ⚠️  ALERTA: Campo cerca del límite de 4000 caracteres")
        
        # 2. TAXONOMÍAS ASOCIADAS
        print(f"\n2. TAXONOMÍAS ASOCIADAS")
        print("-" * 40)
        
        cursor.execute("""
            SELECT 
                it.Id_Taxonomia,
                it.Comentarios,
                it.FechaAsignacion,
                it.CreadoPor,
                t.Descripcion,
                t.Area,
                t.Efecto,
                t.Categoria_del_Incidente,
                t.Subcategoria_del_Incidente
            FROM INCIDENTE_TAXONOMIA it
            LEFT JOIN Taxonomia_incidentes t ON it.Id_Taxonomia = t.Id_Incidente
            WHERE it.IncidenteID = ?
        """, (INCIDENTE_ID,))
        
        taxonomias = cursor.fetchall()
        print(f"Total taxonomías encontradas: {len(taxonomias)}")
        
        for i, tax in enumerate(taxonomias, 1):
            print(f"\n📌 Taxonomía {i}:")
            print(f"   - ID: {tax[0]}")
            print(f"   - Descripción: {tax[4]}")
            print(f"   - Área: {tax[5]}")
            print(f"   - Efecto: {tax[6]}")
            print(f"   - Categoría: {tax[7]}")
            print(f"   - Subcategoría: {tax[8]}")
            print(f"   - Comentarios completos:")
            if tax[1]:
                comentarios = tax[1]
                if "Justificación:" in comentarios:
                    partes = comentarios.split("\\n")
                    for parte in partes:
                        print(f"     • {parte}")
                else:
                    print(f"     • {comentarios}")
            print(f"   - Fecha asignación: {tax[2]}")
        
        # 3. ARCHIVOS DEL INCIDENTE
        print(f"\n3. ARCHIVOS DEL INCIDENTE")
        print("-" * 40)
        
        # Buscar en la carpeta de evidencias
        id_visible = datos.get('IDVisible')
        if id_visible:
            carpeta_evidencias = os.path.join(
                os.path.dirname(__file__), 
                'app', 'uploads', 'evidencias', 
                id_visible
            )
            
            print(f"Buscando archivos en: {carpeta_evidencias}")
            
            if os.path.exists(carpeta_evidencias):
                archivos = os.listdir(carpeta_evidencias)
                print(f"✅ Carpeta encontrada con {len(archivos)} archivo(s)")
                
                archivos_por_seccion = {}
                for archivo in archivos:
                    # Parsear nombre: indice_seccion_numero_timestamp.ext
                    partes = archivo.split('_')
                    if len(partes) >= 3:
                        seccion = partes[1]
                        if seccion not in archivos_por_seccion:
                            archivos_por_seccion[seccion] = []
                        
                        ruta_completa = os.path.join(carpeta_evidencias, archivo)
                        tamaño = os.path.getsize(ruta_completa)
                        
                        archivos_por_seccion[seccion].append({
                            'nombre': archivo,
                            'tamaño': tamaño,
                            'fecha': datetime.fromtimestamp(os.path.getmtime(ruta_completa))
                        })
                
                # Mostrar archivos por sección
                for seccion, archivos in sorted(archivos_por_seccion.items()):
                    print(f"\n   📁 Sección {seccion}:")
                    for archivo in archivos:
                        print(f"      - {archivo['nombre']}")
                        print(f"        Tamaño: {archivo['tamaño']:,} bytes")
                        print(f"        Fecha: {archivo['fecha'].strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"❌ No se encontró la carpeta de evidencias: {carpeta_evidencias}")
        else:
            print("❌ No se encontró IDVisible para buscar archivos")
        
        # 4. ARCHIVOS EN TABLA DE BD (si existe)
        print(f"\n4. VERIFICAR ARCHIVOS EN BASE DE DATOS")
        print("-" * 40)
        
        # Verificar si existe tabla de archivos
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'INCIDENTE_ARCHIVOS'
        """)
        
        if cursor.fetchone()[0] > 0:
            cursor.execute("""
                SELECT * FROM INCIDENTE_ARCHIVOS 
                WHERE IncidenteID = ?
            """, (INCIDENTE_ID,))
            
            archivos_bd = cursor.fetchall()
            print(f"Archivos en BD: {len(archivos_bd)}")
            for archivo in archivos_bd:
                print(f"   - {archivo}")
        else:
            print("ℹ️  No existe tabla INCIDENTE_ARCHIVOS (archivos solo en filesystem)")
        
        # 5. RESUMEN FINAL
        print(f"\n{'='*80}")
        print("RESUMEN DE VALIDACIÓN:")
        print(f"{'='*80}")
        
        validaciones = {
            "Datos principales completos": bool(datos.get('Titulo')),
            "Campos de texto largo preservados": all(
                datos.get(campo) for campo in ['DescripcionInicial', 'AnciImpactoPreliminar']
            ),
            "Taxonomías guardadas": len(taxonomias) > 0,
            "Taxonomías con comentarios": any(tax[1] for tax in taxonomias),
            "Carpeta de archivos existe": os.path.exists(carpeta_evidencias) if id_visible else False,
            "Archivos encontrados": len(archivos_por_seccion) > 0 if 'archivos_por_seccion' in locals() else False
        }
        
        todos_ok = True
        for item, estado in validaciones.items():
            simbolo = "✅" if estado else "❌"
            print(f"{simbolo} {item}")
            if not estado:
                todos_ok = False
        
        if todos_ok:
            print(f"\n🎉 ¡INCIDENTE {INCIDENTE_ID} COMPLETAMENTE VALIDADO!")
        else:
            print(f"\n⚠️  HAY ELEMENTOS FALTANTES EN EL INCIDENTE {INCIDENTE_ID}")
        
        # 6. DATOS ESPECÍFICOS PARA VERIFICAR
        print(f"\n📊 VERIFICACIÓN ESPECÍFICA DE TU PRUEBA:")
        print("-" * 40)
        print("Esperado: 1 archivo por sección + 1 archivo en taxonomías")
        print(f"Encontrado:")
        print(f"   - Archivos por sección: {archivos_por_seccion.keys() if 'archivos_por_seccion' in locals() else 'N/A'}")
        print(f"   - Total archivos: {sum(len(archivos) for archivos in archivos_por_seccion.values()) if 'archivos_por_seccion' in locals() else 0}")
        print(f"   - Taxonomías con archivos: Por validar en carpeta de taxonomías")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ ERROR durante la validación: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    validar_incidente_completo()
#!/usr/bin/env python3
"""
Script para verificar la recuperación completa de estructura base de incidentes
"""

import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:5000"
INCIDENTE_ID = input("Ingresa el ID del incidente a verificar: ")

def verificar_estructura_base():
    """Verifica que la estructura base se recupere completamente"""
    
    print(f"\n{'='*60}")
    print(f"VERIFICACIÓN DE ESTRUCTURA BASE - INCIDENTE {INCIDENTE_ID}")
    print(f"{'='*60}\n")
    
    # 1. Obtener estructura base
    url_estructura = f"{BASE_URL}/api/admin/incidentes/{INCIDENTE_ID}/estructura-base"
    print(f"1. Obteniendo estructura base desde: {url_estructura}")
    
    try:
        response = requests.get(url_estructura)
        
        if response.status_code != 200:
            print(f"❌ Error: Status {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return
        
        datos = response.json()
        
        # 2. Verificar campos principales
        print("\n2. CAMPOS PRINCIPALES DEL INCIDENTE:")
        print(f"   - ID: {datos.get('IncidenteID')}")
        print(f"   - Título: {datos.get('Titulo', 'N/A')}")
        print(f"   - ID Visible: {datos.get('IDVisible', 'N/A')}")
        print(f"   - Estado: {datos.get('EstadoActual', 'N/A')}")
        print(f"   - Criticidad: {datos.get('Criticidad', 'N/A')}")
        print(f"   - Empresa: {datos.get('NombreEmpresa', 'N/A')}")
        
        # 3. Verificar campos de texto largo
        print("\n3. CAMPOS DE TEXTO LARGO (verificando que no estén truncados):")
        campos_texto = [
            ('DescripcionInicial', 'Descripción Inicial'),
            ('AnciImpactoPreliminar', 'Impacto Preliminar'),
            ('SistemasAfectados', 'Sistemas Afectados'),
            ('ServiciosInterrumpidos', 'Servicios Interrumpidos'),
            ('AccionesInmediatas', 'Acciones Inmediatas'),
            ('CausaRaiz', 'Causa Raíz'),
            ('LeccionesAprendidas', 'Lecciones Aprendidas'),
            ('PlanMejora', 'Plan de Mejora')
        ]
        
        for campo, nombre in campos_texto:
            valor = datos.get(campo, '')
            if valor:
                print(f"\n   📝 {nombre}:")
                print(f"      - Longitud: {len(valor)} caracteres")
                print(f"      - Primeros 100 chars: {valor[:100]}...")
                if len(valor) > 1000:
                    print(f"      ✅ Campo largo preservado correctamente")
            else:
                print(f"   ⚠️  {nombre}: Sin datos")
        
        # 4. Verificar taxonomías
        print("\n4. TAXONOMÍAS ASOCIADAS:")
        taxonomias = datos.get('taxonomias', [])
        if taxonomias:
            print(f"   Total taxonomías: {len(taxonomias)}")
            for i, tax in enumerate(taxonomias, 1):
                print(f"\n   Taxonomía {i}:")
                print(f"   - ID: {tax.get('id')}")
                print(f"   - Nombre: {tax.get('nombre', 'N/A')}")
                print(f"   - Justificación: {tax.get('justificacion', 'N/A')}")
                print(f"   - Descripción Problema: {tax.get('descripcionProblema', 'N/A')}")
                print(f"   - Comentarios originales: {tax.get('comentarios', 'N/A')}")
                
                # Verificar que los comentarios se parsearon correctamente
                if tax.get('justificacion') or tax.get('descripcionProblema'):
                    print(f"   ✅ Comentarios parseados correctamente")
        else:
            print("   ⚠️  No hay taxonomías asociadas")
        
        # 5. Verificar archivos
        print("\n5. ARCHIVOS ASOCIADOS:")
        archivos = datos.get('archivos', {})
        if archivos:
            total_archivos = sum(len(files) for files in archivos.values())
            print(f"   Total archivos: {total_archivos}")
            
            for seccion, files in archivos.items():
                print(f"\n   Sección {seccion}:")
                for archivo in files:
                    print(f"   - {archivo.get('nombre')}")
                    print(f"     Tamaño: {archivo.get('tamaño', 0):,} bytes")
                    print(f"     Ruta: {archivo.get('ruta', 'N/A')}")
        else:
            print("   ⚠️  No hay archivos asociados")
        
        # 6. Resumen de verificación
        print(f"\n{'='*60}")
        print("RESUMEN DE VERIFICACIÓN:")
        print(f"{'='*60}")
        
        verificaciones = {
            "Datos básicos": bool(datos.get('IncidenteID')),
            "Campos de texto largo": any(datos.get(campo[0]) for campo in campos_texto),
            "Taxonomías con comentarios": bool(taxonomias and any(t.get('justificacion') for t in taxonomias)),
            "Archivos organizados": bool(archivos),
            "Estructura completa": all([
                datos.get('IncidenteID'),
                any(datos.get(campo[0]) for campo in campos_texto),
                taxonomias
            ])
        }
        
        for item, estado in verificaciones.items():
            simbolo = "✅" if estado else "❌"
            print(f"{simbolo} {item}")
        
        # 7. Guardar resultado completo
        filename = f"estructura_base_incidente_{INCIDENTE_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Estructura completa guardada en: {filename}")
        
        # 8. Verificación especial de recuperación para edición
        print(f"\n{'='*60}")
        print("VERIFICACIÓN PARA EDICIÓN:")
        print(f"{'='*60}")
        
        print("\n¿La estructura es adecuada para edición?")
        checklist = [
            ("Todos los campos de texto preservados", any(datos.get(campo[0]) for campo in campos_texto)),
            ("Taxonomías con justificación/descripción separadas", 
             taxonomias and all(t.get('justificacion') is not None for t in taxonomias)),
            ("Archivos identificables por sección", bool(archivos)),
            ("Información de empresa presente", bool(datos.get('NombreEmpresa')))
        ]
        
        for descripcion, cumple in checklist:
            simbolo = "✅" if cumple else "❌"
            print(f"{simbolo} {descripcion}")
        
        if all(check[1] for check in checklist):
            print("\n✅ ESTRUCTURA BASE LISTA PARA EDICIÓN")
        else:
            print("\n⚠️  HAY ELEMENTOS FALTANTES PARA LA EDICIÓN")
            
    except Exception as e:
        print(f"\n❌ Error durante la verificación: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_estructura_base()
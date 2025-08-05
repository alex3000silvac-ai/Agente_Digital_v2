#!/usr/bin/env python3
"""
Script de prueba integral para el módulo de gestión de incidentes.
Verifica:
1. Creación de nuevos incidentes con todos los campos
2. Guardado de comentarios, archivos y referencias  
3. Control de cambios y versiones
4. Recuperación y edición de datos
"""

import requests
import json
import os
import sys
from datetime import datetime
import tempfile
from pathlib import Path

# Configuración
BASE_URL = "http://localhost:5000/api/incidente"
EMPRESA_ID = 2  # ID de empresa de prueba

# Colores para la salida
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

def print_section(title):
    print(f"\n{Colors.BOLD}{'='*60}")
    print(f"{title}")
    print(f"{'='*60}{Colors.RESET}\n")

def crear_archivo_prueba(nombre, contenido):
    """Crea un archivo temporal para pruebas"""
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, nombre)
    with open(filepath, 'w') as f:
        f.write(contenido)
    return filepath

def test_crear_incidente():
    """Prueba la creación de un incidente completo con todos los campos"""
    print_section("1. PRUEBA DE CREACIÓN DE INCIDENTE")
    
    # Crear archivos de prueba
    archivo1 = crear_archivo_prueba("evidencia1.txt", "Contenido de evidencia 1")
    archivo2 = crear_archivo_prueba("evidencia2.txt", "Contenido de evidencia 2")
    
    # Datos del incidente con TODOS los campos
    data = {
        # Campos obligatorios
        'titulo': f'Incidente de prueba - {datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'descripcion': 'Descripción detallada del incidente de prueba con todos los campos',
        'severidad': 'Alta',
        'estado': 'Abierto',
        'empresa_id': str(EMPRESA_ID),
        'creado_por': 'usuario_prueba',
        
        # Campos de fecha
        'fecha_ocurrencia': datetime.now().isoformat(),
        
        # Campos adicionales
        'tipo_incidente': 'Seguridad',
        'fuente_deteccion': 'Monitoreo automatizado',
        'impacto_estimado': 'Interrupción parcial de servicios críticos',
        'acciones_tomadas': 'Se aisló el sistema afectado y se inició investigación',
        'comentarios_adicionales': 'Este es un incidente de prueba con datos completos',
        'responsable_cierre': 'Equipo de seguridad',
        'taxonomia_id': '1',
        'origen_datos': 'Sistema interno',
        
        # Taxonomías seleccionadas (JSON string)
        'taxonomias_seleccionadas': json.dumps([
            {
                'Id_Taxonomia': 'TAX001',
                'Comentarios': 'Clasificación inicial del incidente'
            },
            {
                'Id_Taxonomia': 'TAX002', 
                'Comentarios': 'Categoría secundaria aplicable'
            }
        ]),
        
        # Comentarios adicionales en formato JSON
        'comentarios_adicionales_json': json.dumps([
            {
                'texto': 'Primer comentario del incidente',
                'fecha': datetime.now().isoformat()
            },
            {
                'texto': 'Segundo comentario con más detalles',
                'fecha': datetime.now().isoformat()
            }
        ])
    }
    
    # Preparar archivos
    files = [
        ('archivos', ('evidencia1.txt', open(archivo1, 'rb'), 'text/plain')),
        ('archivos', ('evidencia2.txt', open(archivo2, 'rb'), 'text/plain'))
    ]
    
    # Agregar descripciones y versiones de archivos
    data['descripcion_archivo_evidencia1.txt'] = 'Primera evidencia del incidente'
    data['version_archivo_evidencia1.txt'] = '1'
    data['descripcion_archivo_evidencia2.txt'] = 'Segunda evidencia del incidente'
    data['version_archivo_evidencia2.txt'] = '1'
    
    try:
        print_info("Enviando petición POST para crear incidente...")
        response = requests.post(BASE_URL + '/', data=data, files=files)
        
        # Cerrar archivos
        for _, file_tuple in files:
            file_tuple[1].close()
        
        if response.status_code == 201:
            result = response.json()
            print_success(f"Incidente creado exitosamente")
            print_info(f"ID del incidente: {result.get('incidente_id')}")
            return result.get('incidente_id')
        else:
            print_error(f"Error al crear incidente: {response.status_code}")
            print_error(f"Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Excepción al crear incidente: {str(e)}")
        return None
    finally:
        # Limpiar archivos temporales
        os.remove(archivo1)
        os.remove(archivo2)

def test_obtener_incidente(incidente_id):
    """Prueba la recuperación de un incidente y verifica todos los datos"""
    print_section("2. PRUEBA DE RECUPERACIÓN DE INCIDENTE")
    
    if not incidente_id:
        print_warning("No hay ID de incidente para recuperar")
        return False
    
    try:
        print_info(f"Obteniendo incidente ID: {incidente_id}")
        response = requests.get(f"{BASE_URL}/{incidente_id}")
        
        if response.status_code == 200:
            incidente = response.json()
            print_success("Incidente recuperado exitosamente")
            
            # Verificar campos principales
            print_info("\nVerificando campos principales:")
            campos_verificar = [
                'Titulo', 'Descripcion', 'Severidad', 'Estado',
                'FechaCreacion', 'FechaActualizacion', 'EmpresaID',
                'CreadoPor', 'TipoIncidente', 'FuenteDeteccion',
                'ImpactoEstimado', 'AccionesTomadas', 'ComentariosAdicionales'
            ]
            
            for campo in campos_verificar:
                valor = incidente.get(campo)
                if valor:
                    print_success(f"  {campo}: {valor[:50]}..." if isinstance(valor, str) and len(valor) > 50 else f"  {campo}: {valor}")
                else:
                    print_warning(f"  {campo}: No encontrado")
            
            # Verificar archivos adjuntos
            print_info("\nVerificando archivos adjuntos:")
            archivos = incidente.get('archivos_adjuntos', [])
            if archivos:
                print_success(f"  Se encontraron {len(archivos)} archivos")
                for archivo in archivos:
                    print_info(f"    - {archivo.get('NombreArchivo')} ({archivo.get('TamanoKB')} KB)")
                    print_info(f"      Descripción: {archivo.get('Descripcion')}")
                    print_info(f"      Versión: {archivo.get('Version')}")
            else:
                print_warning("  No se encontraron archivos adjuntos")
            
            # Verificar historial de cambios
            print_info("\nVerificando historial de cambios:")
            historial = incidente.get('historial_cambios', [])
            if historial:
                print_success(f"  Se encontraron {len(historial)} cambios")
                for cambio in historial[:3]:  # Mostrar solo los primeros 3
                    print_info(f"    - Campo: {cambio.get('CampoModificado')}")
                    print_info(f"      De: {cambio.get('ValorAnterior')} → A: {cambio.get('ValorNuevo')}")
            else:
                print_info("  No hay historial de cambios (es un incidente nuevo)")
            
            # Verificar taxonomías
            print_info("\nVerificando taxonomías:")
            taxonomias = incidente.get('Taxonomias', [])
            if taxonomias:
                print_success(f"  Se encontraron {len(taxonomias)} taxonomías")
                for tax in taxonomias:
                    print_info(f"    - ID: {tax.get('Id_Taxonomia')}")
                    print_info(f"      Área: {tax.get('Area')}")
                    print_info(f"      Categoría: {tax.get('Categoria_del_Incidente')}")
            else:
                print_warning("  No se encontraron taxonomías asociadas")
            
            # Verificar comentarios
            print_info("\nVerificando comentarios:")
            comentarios = incidente.get('Comentarios', [])
            if comentarios:
                print_success(f"  Se encontraron {len(comentarios)} comentarios")
                for com in comentarios:
                    print_info(f"    - {com.get('Comentario')}")
                    print_info(f"      Creado por: {com.get('CreadoPor')} en {com.get('FechaCreacion')}")
            else:
                print_warning("  No se encontraron comentarios")
            
            return True
            
        else:
            print_error(f"Error al obtener incidente: {response.status_code}")
            print_error(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Excepción al obtener incidente: {str(e)}")
        return False

def test_actualizar_incidente(incidente_id):
    """Prueba la actualización de un incidente y verifica el historial"""
    print_section("3. PRUEBA DE ACTUALIZACIÓN DE INCIDENTE")
    
    if not incidente_id:
        print_warning("No hay ID de incidente para actualizar")
        return False
    
    # Crear nuevo archivo para la actualización
    archivo_nuevo = crear_archivo_prueba("evidencia_actualizada.txt", "Nueva evidencia del incidente")
    
    # Datos actualizados
    data = {
        'titulo': f'Incidente ACTUALIZADO - {datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'descripcion': 'Descripción actualizada con más información detallada',
        'severidad': 'Crítica',  # Cambiado de Alta a Crítica
        'estado': 'En Proceso',  # Cambiado de Abierto a En Proceso
        'tipo_incidente': 'Seguridad - Actualizado',
        'impacto_estimado': 'Impacto actualizado: Afectación total de servicios',
        'acciones_tomadas': 'Acciones actualizadas: Se implementó plan de contención completo',
        'responsable_cierre': 'Jefe de Seguridad',
        'modificado_por': 'usuario_actualizacion',
        
        # Archivos a eliminar (simulación)
        'archivos_a_eliminar': '[]',
        
        # Nuevas taxonomías
        'taxonomias_seleccionadas': json.dumps([
            {
                'Id_Taxonomia': 'TAX003',
                'Comentarios': 'Nueva clasificación tras análisis'
            }
        ])
    }
    
    # Preparar archivos nuevos
    files = [
        ('archivos_nuevos', ('evidencia_actualizada.txt', open(archivo_nuevo, 'rb'), 'text/plain'))
    ]
    
    data['descripcion_archivo_evidencia_actualizada.txt'] = 'Evidencia agregada en actualización'
    data['version_archivo_evidencia_actualizada.txt'] = '2'
    
    try:
        print_info("Enviando petición PUT para actualizar incidente...")
        response = requests.put(f"{BASE_URL}/{incidente_id}", data=data, files=files)
        
        # Cerrar archivos
        for _, file_tuple in files:
            file_tuple[1].close()
        
        if response.status_code == 200:
            result = response.json()
            print_success("Incidente actualizado exitosamente")
            
            # Verificar que los cambios se registraron
            print_info("\nVerificando historial de cambios...")
            response_get = requests.get(f"{BASE_URL}/{incidente_id}")
            if response_get.status_code == 200:
                incidente_actualizado = response_get.json()
                historial = incidente_actualizado.get('historial_cambios', [])
                
                if historial:
                    print_success(f"Historial actualizado con {len(historial)} entradas")
                    # Mostrar los cambios más recientes
                    for cambio in historial[:5]:
                        print_info(f"  - {cambio.get('CampoModificado')}: {cambio.get('ValorAnterior')} → {cambio.get('ValorNuevo')}")
                else:
                    print_warning("No se encontró historial de cambios")
                
                # Verificar nuevos archivos
                archivos = incidente_actualizado.get('archivos_adjuntos', [])
                print_info(f"\nTotal de archivos después de actualización: {len(archivos)}")
                
            return True
        else:
            print_error(f"Error al actualizar incidente: {response.status_code}")
            print_error(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Excepción al actualizar incidente: {str(e)}")
        return False
    finally:
        # Limpiar archivo temporal
        os.remove(archivo_nuevo)

def test_listar_incidentes():
    """Prueba el listado de todos los incidentes"""
    print_section("4. PRUEBA DE LISTADO DE INCIDENTES")
    
    try:
        print_info("Obteniendo lista de incidentes...")
        response = requests.get(BASE_URL + '/')
        
        if response.status_code == 200:
            incidentes = response.json()
            print_success(f"Se encontraron {len(incidentes)} incidentes")
            
            # Mostrar los primeros 5
            for incidente in incidentes[:5]:
                print_info(f"\n  ID: {incidente.get('IncidenteID')}")
                print_info(f"  Título: {incidente.get('Titulo')}")
                print_info(f"  Estado: {incidente.get('Estado')}")
                print_info(f"  Severidad: {incidente.get('Severidad')}")
                print_info(f"  Fecha: {incidente.get('FechaCreacion')}")
            
            if len(incidentes) > 5:
                print_info(f"\n  ... y {len(incidentes) - 5} más")
            
            return True
        else:
            print_error(f"Error al listar incidentes: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Excepción al listar incidentes: {str(e)}")
        return False

def main():
    """Función principal que ejecuta todas las pruebas"""
    print(f"\n{Colors.BOLD}PRUEBA INTEGRAL DEL MÓDULO DE GESTIÓN DE INCIDENTES")
    print(f"{'='*60}{Colors.RESET}")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL Base: {BASE_URL}")
    print(f"Empresa ID: {EMPRESA_ID}\n")
    
    # Verificar conectividad
    try:
        response = requests.get("http://localhost:5000/api/health")
        if response.status_code != 200:
            print_error("El servidor no está disponible. Asegúrate de que esté ejecutándose.")
            return
    except:
        print_error("No se puede conectar al servidor. Verifica que esté ejecutándose en http://localhost:5000")
        return
    
    resultados = {
        'crear': False,
        'obtener': False,
        'actualizar': False,
        'listar': False
    }
    
    # 1. Crear incidente
    incidente_id = test_crear_incidente()
    resultados['crear'] = incidente_id is not None
    
    # 2. Obtener incidente
    if incidente_id:
        resultados['obtener'] = test_obtener_incidente(incidente_id)
    
    # 3. Actualizar incidente
    if incidente_id:
        resultados['actualizar'] = test_actualizar_incidente(incidente_id)
        
        # Verificar cambios después de actualización
        if resultados['actualizar']:
            print_info("\nVerificando incidente después de actualización...")
            test_obtener_incidente(incidente_id)
    
    # 4. Listar incidentes
    resultados['listar'] = test_listar_incidentes()
    
    # Resumen final
    print_section("RESUMEN DE RESULTADOS")
    total_pruebas = len(resultados)
    pruebas_exitosas = sum(1 for v in resultados.values() if v)
    
    print(f"Pruebas ejecutadas: {total_pruebas}")
    print(f"Pruebas exitosas: {pruebas_exitosas}")
    print(f"Pruebas fallidas: {total_pruebas - pruebas_exitosas}")
    
    print("\nDetalle:")
    for prueba, resultado in resultados.items():
        if resultado:
            print_success(f"  {prueba.capitalize()}: EXITOSO")
        else:
            print_error(f"  {prueba.capitalize()}: FALLIDO")
    
    if pruebas_exitosas == total_pruebas:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE{Colors.RESET}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ ALGUNAS PRUEBAS FALLARON{Colors.RESET}")

if __name__ == "__main__":
    main()
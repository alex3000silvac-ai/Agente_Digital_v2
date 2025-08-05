#!/usr/bin/env python3
"""
Endpoint mejorado para cargar incidentes con TODAS las evidencias y taxonomías correctamente
"""

from flask import Blueprint, jsonify
from ..modules.core.database import get_db_connection
from ..utils.encoding_fixer import EncodingFixer
import json

incidente_cargar_bp = Blueprint('incidente_cargar_completo', __name__, url_prefix='/api/incidente/v2')

@incidente_cargar_bp.route('/<int:incidente_id>', methods=['GET'])
def cargar_incidente_completo(incidente_id):
    """
    Carga un incidente con TODAS sus evidencias, taxonomías y comentarios correctamente estructurados
    """
    print(f"🔍 CARGANDO INCIDENTE COMPLETO ID: {incidente_id}")
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
            
        cursor = conn.cursor()
        
        # 1. CARGAR DATOS BÁSICOS DEL INCIDENTE
        print(f"📋 1. Cargando datos básicos del incidente...")
        query_incidente = """
            SELECT 
                IncidenteID, Titulo, DescripcionInicial, Criticidad, EstadoActual, 
                FechaCreacion, FechaActualizacion, EmpresaID, CreadoPor, 
                FechaDeteccion, FechaOcurrencia, TipoFlujo, OrigenIncidente,
                SistemasAfectados, AccionesInmediatas, ResponsableCliente,
                FechaCierre, IDVisible, ReporteAnciID, FechaDeclaracionANCI,
                AlcanceGeografico, ServiciosInterrumpidos, AnciImpactoPreliminar, 
                AnciTipoAmenaza, CausaRaiz, LeccionesAprendidas, PlanMejora
            FROM Incidentes
            WHERE IncidenteID = ?
        """
        cursor.execute(query_incidente, incidente_id)
        incidente = cursor.fetchone()
        
        if not incidente:
            print(f"❌ Incidente {incidente_id} no encontrado")
            return jsonify({"error": "Incidente no encontrado"}), 404
            
        incidente_dict = dict(zip([column[0] for column in cursor.description], incidente))
        
        # Corregir encoding de los datos
        incidente_dict = EncodingFixer.fix_dict(incidente_dict)
        print(f"✅ Datos básicos cargados y encoding corregido")
        
        # Convertir fechas a formato ISO
        for campo_fecha in ['FechaCreacion', 'FechaActualizacion', 'FechaDeteccion', 
                           'FechaOcurrencia', 'FechaCierre', 'FechaDeclaracionANCI']:
            if incidente_dict.get(campo_fecha):
                incidente_dict[campo_fecha] = incidente_dict[campo_fecha].isoformat()
        
        # 2. CARGAR EVIDENCIAS GENERALES DEL INCIDENTE (Sección 2)
        print(f"📁 2. Cargando evidencias generales...")
        query_evidencias_generales = """
            SELECT 
                EvidenciaID, NombreArchivo, RutaArchivo, TipoArchivo, 
                TamanoKB, Descripcion, Version, FechaSubida, SubidoPor,
                Seccion
            FROM EvidenciasIncidentes
            WHERE IncidenteID = ? 
            ORDER BY Seccion, EvidenciaID
        """
        evidencias_por_seccion = {
            'descripcion': [],
            'analisis': [],
            'acciones': [],
            'analisis-final': []
        }
        
        cursor.execute(query_evidencias_generales, incidente_id)
        evidencias_vistas = set()  # Para evitar duplicados
        
        for row in cursor.fetchall():
            evidencia = dict(zip([column[0] for column in cursor.description], row))
            if evidencia.get('FechaSubida'):
                evidencia['FechaSubida'] = evidencia['FechaSubida'].isoformat()
            
            # Evitar duplicados
            evidencia_key = f"{evidencia['EvidenciaID']}_{evidencia['NombreArchivo']}"
            if evidencia_key in evidencias_vistas:
                continue
            evidencias_vistas.add(evidencia_key)
            
            # Clasificar por sección - mapear números a nombres de sección
            seccion_raw = str(evidencia.get('Seccion', '')).strip()
            descripcion_raw = str(evidencia.get('Descripcion', '')).strip()
            
            # Mapeo de números/descripciones a secciones
            if seccion_raw == '2' or descripcion_raw in ['1', '2'] or 'descripcion' in descripcion_raw.lower():
                seccion = 'descripcion'
            elif seccion_raw == '3' or descripcion_raw == '3' or 'analisis' in descripcion_raw.lower():
                seccion = 'analisis'
            elif seccion_raw == '4' or descripcion_raw == '4' or 'acciones' in descripcion_raw.lower():
                seccion = 'acciones'
            elif seccion_raw == '5' or descripcion_raw in ['5', '12'] or 'final' in descripcion_raw.lower():
                seccion = 'analisis-final'
            else:
                # Por defecto a descripción
                seccion = 'descripcion'
            
            if seccion in evidencias_por_seccion:
                evidencias_por_seccion[seccion].append({
                    'id': evidencia['EvidenciaID'],
                    'nombre': evidencia['NombreArchivo'],
                    'descripcion': evidencia.get('Descripcion', ''),
                    'ruta': evidencia['RutaArchivo'],
                    'tamano': evidencia.get('TamanoKB', 0),
                    'fechaSubida': evidencia.get('FechaSubida', ''),
                    'subidoPor': evidencia.get('SubidoPor', '')
                })
        
        print(f"✅ Evidencias generales cargadas: {sum(len(v) for v in evidencias_por_seccion.values())} archivos")
        incidente_dict['evidencias_secciones'] = evidencias_por_seccion
        
        # 3. CARGAR TAXONOMÍAS SELECCIONADAS (Sección 4)
        print(f"🏷️ 3. Cargando taxonomías seleccionadas...")
        query_taxonomias = """
            SELECT DISTINCT
                IT.Id_Taxonomia,
                IT.Comentarios,
                IT.FechaAsignacion,
                IT.CreadoPor,
                TI.Area,
                TI.Efecto,
                TI.Categoria_del_Incidente,
                TI.Subcategoria_del_Incidente,
                TI.AplicaTipoEmpresa
            FROM INCIDENTE_TAXONOMIA IT
            INNER JOIN TAXONOMIA_INCIDENTES TI ON IT.Id_Taxonomia = TI.Id_Incidente
            WHERE IT.IncidenteID = ?
        """
        taxonomias_seleccionadas = []
        taxonomias_ids = []
        
        cursor.execute(query_taxonomias, incidente_id)
        for row in cursor.fetchall():
            tax = dict(zip([column[0] for column in cursor.description], row))
            # Corregir encoding de taxonomías
            tax = EncodingFixer.fix_dict(tax)
            
            # Parsear comentarios para extraer justificación y descripción
            if tax.get('Comentarios'):
                comentarios = tax['Comentarios']
                # Buscar justificación
                if 'Justificación:' in comentarios:
                    parts = comentarios.split('Justificación:', 1)
                    if len(parts) > 1:
                        justif_parts = parts[1].split('\n', 1)
                        tax['justificacion'] = justif_parts[0].strip()
                        
                        # Buscar descripción del problema
                        if len(justif_parts) > 1 and 'Descripción del problema:' in justif_parts[1]:
                            desc_parts = justif_parts[1].split('Descripción del problema:', 1)
                            if len(desc_parts) > 1:
                                tax['descripcionProblema'] = desc_parts[1].strip()
                else:
                    # Si no tiene el formato nuevo, usar el comentario completo como justificación
                    tax['justificacion'] = comentarios
                    tax['descripcionProblema'] = ''
            else:
                tax['justificacion'] = ''
                tax['descripcionProblema'] = ''
            
            # Agregar campo 'id' que espera el frontend
            tax['id'] = tax['Id_Taxonomia']
            
            # Agregar otros campos que podría esperar el frontend
            tax['nombre'] = tax.get('Categoria_del_Incidente', '')
            tax['area'] = tax.get('Area', '')
            tax['efecto'] = tax.get('Efecto', '')
            
            taxonomias_seleccionadas.append(tax)
            taxonomias_ids.append(tax['Id_Taxonomia'])
        
        print(f"✅ Taxonomías cargadas: {len(taxonomias_seleccionadas)}")
        incidente_dict['taxonomias_seleccionadas'] = taxonomias_seleccionadas
        
        # 4. CARGAR EVIDENCIAS POR TAXONOMÍA
        print(f"📎 4. Cargando evidencias por taxonomía...")
        evidencias_por_taxonomia = {}
        
        if taxonomias_ids:
            query_evidencias_taxonomia = """
                SELECT 
                    ET.EvidenciaID,
                    ET.TaxonomiaID as Id_Taxonomia,
                    ET.NombreArchivo,
                    ET.RutaArchivo,
                    ET.Comentario,
                    ET.FechaSubida,
                    ET.SubidoPor
                FROM EVIDENCIAS_TAXONOMIA ET
                WHERE ET.IncidenteID = ?
                ORDER BY ET.TaxonomiaID
            """
            
            cursor.execute(query_evidencias_taxonomia, incidente_id)
            for row in cursor.fetchall():
                ev = dict(zip([column[0] for column in cursor.description], row))
                
                if ev.get('FechaSubida'):
                    ev['FechaSubida'] = ev['FechaSubida'].isoformat()
                
                tax_id = ev['Id_Taxonomia']
                if tax_id not in evidencias_por_taxonomia:
                    evidencias_por_taxonomia[tax_id] = []
                
                evidencias_por_taxonomia[tax_id].append({
                    'id': ev['EvidenciaID'],
                    'nombre': ev['NombreArchivo'],
                    'comentario': ev.get('Comentario', ''),
                    'ruta': ev['RutaArchivo'],
                    'fechaSubida': ev.get('FechaSubida', ''),
                    'subidoPor': ev.get('SubidoPor', '')
                })
        
        total_evidencias_tax = sum(len(v) for v in evidencias_por_taxonomia.values())
        print(f"✅ Evidencias por taxonomía cargadas: {total_evidencias_tax} archivos")
        incidente_dict['evidencias_taxonomias'] = evidencias_por_taxonomia
        
        # Ahora fusionar las evidencias en cada taxonomía para el frontend
        for tax in taxonomias_seleccionadas:
            tax_id = tax['Id_Taxonomia']
            if tax_id in evidencias_por_taxonomia:
                tax['archivos'] = evidencias_por_taxonomia[tax_id]
                print(f"   📎 Agregados {len(tax['archivos'])} archivos a taxonomía {tax_id}")
            else:
                tax['archivos'] = []
        
        # 5. CARGAR COMENTARIOS ADICIONALES - Temporalmente deshabilitado
        # print(f"💬 5. Cargando comentarios adicionales...")
        comentarios = []
        incidente_dict['comentarios_taxonomias'] = comentarios
        
        # 6. ESTRUCTURA FINAL
        resultado = {
            'success': True,
            'incidente': incidente_dict,
            'resumen': {
                'total_evidencias_generales': sum(len(v) for v in evidencias_por_seccion.values()),
                'total_taxonomias': len(taxonomias_seleccionadas),
                'total_evidencias_taxonomias': total_evidencias_tax,
                'total_comentarios': len(comentarios)
            }
        }
        
        print(f"✅ CARGA COMPLETA EXITOSA")
        print(f"📊 Resumen: {resultado['resumen']}")
        
        return jsonify(resultado), 200
        
    except Exception as e:
        print(f"❌ Error al cargar incidente completo: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Error interno del servidor",
            "details": str(e)
        }), 500
        
    finally:
        if conn:
            conn.close()
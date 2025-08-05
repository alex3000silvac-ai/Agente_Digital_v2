# incidentes_editar.py
# Módulo exclusivo para la edición de incidentes
# Siguiendo las especificaciones del archivo incidente.txt

from flask import jsonify, request
from datetime import datetime
import os
import json
import traceback
from functools import wraps
from ...database import get_db_connection
from ...auth_utils import verificar_token
import shutil

# Decorador para autenticación
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Token no proporcionado"}), 401
        
        usuario = verificar_token(token)
        if not usuario:
            return jsonify({"error": "Token inválido o expirado"}), 401
        
        return f(usuario, *args, **kwargs)
    return decorated_function

class EditorIncidentes:
    """Clase para manejar la edición de incidentes según especificaciones"""
    
    def __init__(self):
        self.temp_folder = os.path.join(os.path.dirname(__file__), '..', '..', 'temp_incidentes')
        self.upload_folder = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')
        
        # Crear carpetas si no existen
        os.makedirs(self.temp_folder, exist_ok=True)
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def cargar_incidente_por_indice(self, indice_unico):
        """
        Carga un incidente usando su índice único como referencia principal
        Según especificación: el índice es la única referencia de carga
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Cargar datos principales del incidente
            query_incidente = """
            SELECT 
                id, InquilinoID, EmpresaID, tipo_registro, titulo_incidente,
                fecha_deteccion, fecha_ocurrencia, criticidad, alcance_geografico,
                descripcion_detallada, impacto_preliminar, sistemas_afectados,
                servicios_interrumpidos, tipo_amenaza, origen_ataque,
                responsable_cliente, medidas_contencion, analisis_causa_raiz,
                lecciones_aprendidas, recomendaciones_mejora, estado,
                fecha_creacion, usuario_creacion
            FROM Incidentes
            WHERE indice_unico = ?
            """
            
            cursor.execute(query_incidente, (indice_unico,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Construir objeto incidente
            incidente = {
                'id': row[0],
                'indice_unico': indice_unico,
                'inquilino_id': row[1],
                'empresa_id': row[2],
                'tipo_registro': row[3],
                'titulo_incidente': row[4],
                'fecha_deteccion': row[5].isoformat() if row[5] else None,
                'fecha_ocurrencia': row[6].isoformat() if row[6] else None,
                'criticidad': row[7],
                'alcance_geografico': row[8],
                'descripcion_detallada': row[9],
                'impacto_preliminar': row[10],
                'sistemas_afectados': row[11],
                'servicios_interrumpidos': row[12],
                'tipo_amenaza': row[13],
                'origen_ataque': row[14],
                'responsable_cliente': row[15],
                'medidas_contencion': row[16],
                'analisis_causa_raiz': row[17],
                'lecciones_aprendidas': row[18],
                'recomendaciones_mejora': row[19],
                'estado': row[20],
                'fecha_creacion': row[21].isoformat() if row[21] else None,
                'usuario_creacion': row[22]
            }
            
            # Cargar taxonomías asociadas
            query_taxonomias = """
            SELECT 
                it.TaxonomiaID, t.nombre, t.descripcion, t.categoria,
                it.porque_seleccionada, it.observaciones_adicionales
            FROM INCIDENTE_TAXONOMIA it
            INNER JOIN Taxonomia_incidentes t ON it.TaxonomiaID = t.id
            WHERE it.IncidenteID = ?
            """
            
            cursor.execute(query_taxonomias, (incidente['id'],))
            taxonomias = []
            
            for tax_row in cursor.fetchall():
                taxonomias.append({
                    'id': tax_row[0],
                    'nombre': tax_row[1],
                    'descripcion': tax_row[2],
                    'categoria': tax_row[3],
                    'porque_seleccionada': tax_row[4],
                    'observaciones': tax_row[5]
                })
            
            incidente['taxonomias'] = taxonomias
            
            # Cargar evidencias organizadas por sección
            query_evidencias = """
            SELECT 
                seccion, numero_evidencia, nombre_archivo,
                descripcion, ruta_archivo, fecha_carga
            FROM EvidenciasIncidentes
            WHERE IncidenteID = ?
            ORDER BY seccion, numero_evidencia
            """
            
            cursor.execute(query_evidencias, (incidente['id'],))
            evidencias = {}
            
            for ev_row in cursor.fetchall():
                seccion = ev_row[0]
                if seccion not in evidencias:
                    evidencias[seccion] = []
                
                evidencias[seccion].append({
                    'numero': ev_row[1],
                    'nombre_archivo': ev_row[2],
                    'descripcion': ev_row[3],
                    'ruta': ev_row[4],
                    'fecha_carga': ev_row[5].isoformat() if ev_row[5] else None
                })
            
            incidente['evidencias'] = evidencias
            
            cursor.close()
            conn.close()
            
            return incidente
            
        except Exception as e:
            print(f"Error cargando incidente: {str(e)}")
            raise
    
    def cargar_o_crear_archivo_temporal(self, indice_unico, datos_incidente):
        """
        Carga el archivo temporal si existe, o crea uno nuevo (semilla base)
        """
        try:
            temp_file = os.path.join(self.temp_folder, f"{indice_unico}.json")
            
            if os.path.exists(temp_file):
                # Cargar archivo temporal existente
                with open(temp_file, 'r', encoding='utf-8') as f:
                    datos_temp = json.load(f)
                return datos_temp, temp_file
            else:
                # Crear nuevo archivo temporal como semilla base
                datos_incidente['timestamp_edicion'] = datetime.now().isoformat()
                datos_incidente['estado_temporal'] = 'semilla_base'
                
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(datos_incidente, f, ensure_ascii=False, indent=2)
                
                return datos_incidente, temp_file
                
        except Exception as e:
            print(f"Error manejando archivo temporal: {str(e)}")
            raise
    
    def actualizar_incidente_db(self, datos, indice_unico):
        """Actualiza el incidente en la base de datos"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Iniciar transacción
            cursor.execute("BEGIN TRANSACTION")
            
            # Actualizar incidente principal
            query_update = """
            UPDATE Incidentes SET
                tipo_registro = ?,
                titulo_incidente = ?,
                fecha_deteccion = ?,
                fecha_ocurrencia = ?,
                criticidad = ?,
                alcance_geografico = ?,
                descripcion_detallada = ?,
                impacto_preliminar = ?,
                sistemas_afectados = ?,
                servicios_interrumpidos = ?,
                tipo_amenaza = ?,
                origen_ataque = ?,
                responsable_cliente = ?,
                medidas_contencion = ?,
                analisis_causa_raiz = ?,
                lecciones_aprendidas = ?,
                recomendaciones_mejora = ?,
                estado = ?,
                fecha_actualizacion = GETDATE(),
                usuario_actualizacion = ?
            WHERE indice_unico = ?
            """
            
            valores = (
                datos['tipo_registro'],
                datos['titulo_incidente'],
                datos['fecha_deteccion'],
                datos['fecha_ocurrencia'],
                datos['criticidad'],
                datos.get('alcance_geografico', ''),
                datos['descripcion_detallada'],
                datos['impacto_preliminar'],
                datos['sistemas_afectados'],
                datos['servicios_interrumpidos'],
                datos['tipo_amenaza'],
                datos['origen_ataque'],
                datos.get('responsable_cliente', ''),
                datos['medidas_contencion'],
                datos.get('analisis_causa_raiz', ''),
                datos.get('lecciones_aprendidas', ''),
                datos.get('recomendaciones_mejora', ''),
                datos.get('estado', 'en_proceso'),
                datos['usuario_id'],
                indice_unico
            )
            
            cursor.execute(query_update, valores)
            
            # Obtener ID del incidente
            cursor.execute("SELECT id FROM Incidentes WHERE indice_unico = ?", (indice_unico,))
            incidente_id = cursor.fetchone()[0]
            
            # Actualizar taxonomías (eliminar existentes y reinsertar)
            cursor.execute("DELETE FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?", (incidente_id,))
            
            if 'taxonomias' in datos:
                for taxonomia in datos['taxonomias']:
                    query_tax = """
                    INSERT INTO INCIDENTE_TAXONOMIA (
                        IncidenteID, TaxonomiaID, porque_seleccionada,
                        observaciones_adicionales, fecha_seleccion
                    ) VALUES (?, ?, ?, ?, GETDATE())
                    """
                    cursor.execute(query_tax, (
                        incidente_id,
                        taxonomia['id'],
                        taxonomia['porque_seleccionada'],
                        taxonomia.get('observaciones', '')
                    ))
            
            # NO eliminar evidencias existentes, solo agregar nuevas
            if 'nuevas_evidencias' in datos:
                for seccion, evidencias in datos['nuevas_evidencias'].items():
                    for evidencia in evidencias:
                        query_ev = """
                        INSERT INTO EvidenciasIncidentes (
                            IncidenteID, seccion, numero_evidencia,
                            nombre_archivo, descripcion, ruta_archivo,
                            fecha_carga
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """
                        cursor.execute(query_ev, (
                            incidente_id,
                            seccion,
                            evidencia['numero'],
                            evidencia['nombre_archivo'],
                            evidencia['descripcion'],
                            evidencia['ruta'],
                            evidencia['fecha_carga']
                        ))
            
            # Confirmar transacción
            cursor.execute("COMMIT")
            
            cursor.close()
            conn.close()
            
            return incidente_id
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            print(f"Error actualizando incidente: {str(e)}")
            raise
    
    def eliminar_evidencia(self, incidente_id, numero_evidencia):
        """Elimina una evidencia específica"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Obtener información del archivo antes de eliminar
            cursor.execute("""
                SELECT ruta_archivo 
                FROM EvidenciasIncidentes 
                WHERE IncidenteID = ? AND numero_evidencia = ?
            """, (incidente_id, numero_evidencia))
            
            result = cursor.fetchone()
            if result:
                ruta_archivo = result[0]
                
                # Eliminar registro de la base de datos
                cursor.execute("""
                    DELETE FROM EvidenciasIncidentes 
                    WHERE IncidenteID = ? AND numero_evidencia = ?
                """, (incidente_id, numero_evidencia))
                
                # Eliminar archivo físico
                if os.path.exists(ruta_archivo):
                    os.remove(ruta_archivo)
                
                cursor.commit()
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error eliminando evidencia: {str(e)}")
            raise

# Instancia global del editor
editor = EditorIncidentes()

@login_required
def obtener_incidente_para_edicion(usuario):
    """Obtiene un incidente para edición usando su índice único"""
    try:
        indice_unico = request.args.get('indice_unico')
        
        if not indice_unico:
            return jsonify({"error": "Índice único no proporcionado"}), 400
        
        # Cargar incidente desde la base de datos
        incidente = editor.cargar_incidente_por_indice(indice_unico)
        
        if not incidente:
            return jsonify({"error": "Incidente no encontrado"}), 404
        
        # Verificar permisos del usuario
        # TODO: Implementar verificación de permisos según el rol del usuario
        
        # Cargar o crear archivo temporal
        datos_temp, archivo_temp = editor.cargar_o_crear_archivo_temporal(
            indice_unico, incidente
        )
        
        return jsonify({
            "success": True,
            "incidente": datos_temp,
            "archivo_temporal": archivo_temp,
            "mensaje": "Incidente cargado para edición"
        }), 200
        
    except Exception as e:
        print(f"Error obteniendo incidente: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "error": "Error al obtener incidente",
            "detalle": str(e)
        }), 500

@login_required
def actualizar_incidente(usuario):
    """Actualiza un incidente existente"""
    try:
        datos = request.get_json()
        indice_unico = datos.get('indice_unico')
        
        if not indice_unico:
            return jsonify({"error": "Índice único no proporcionado"}), 400
        
        # Agregar información del usuario
        datos['usuario_id'] = usuario.get('id')
        
        # Actualizar archivo temporal
        temp_file = os.path.join(editor.temp_folder, f"{indice_unico}.json")
        datos['timestamp_actualizacion'] = datetime.now().isoformat()
        datos['estado_temporal'] = 'actualizado'
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        
        # Actualizar en base de datos
        incidente_id = editor.actualizar_incidente_db(datos, indice_unico)
        
        return jsonify({
            "success": True,
            "incidente_id": incidente_id,
            "indice_unico": indice_unico,
            "mensaje": "Incidente actualizado exitosamente"
        }), 200
        
    except Exception as e:
        print(f"Error actualizando incidente: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "error": "Error al actualizar incidente",
            "detalle": str(e)
        }), 500

@login_required
def eliminar_evidencia_incidente(usuario):
    """Elimina una evidencia específica de un incidente"""
    try:
        datos = request.get_json()
        incidente_id = datos.get('incidente_id')
        numero_evidencia = datos.get('numero_evidencia')
        
        if not all([incidente_id, numero_evidencia]):
            return jsonify({"error": "Parámetros faltantes"}), 400
        
        # Eliminar evidencia
        editor.eliminar_evidencia(incidente_id, numero_evidencia)
        
        return jsonify({
            "success": True,
            "mensaje": "Evidencia eliminada exitosamente"
        }), 200
        
    except Exception as e:
        print(f"Error eliminando evidencia: {str(e)}")
        return jsonify({
            "error": "Error al eliminar evidencia",
            "detalle": str(e)
        }), 500

@login_required
def obtener_resumen_evidencias(usuario):
    """Obtiene el resumen de todas las evidencias de un incidente"""
    try:
        indice_unico = request.args.get('indice_unico')
        
        if not indice_unico:
            return jsonify({"error": "Índice único no proporcionado"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener ID del incidente
        cursor.execute("SELECT id FROM Incidentes WHERE indice_unico = ?", (indice_unico,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"error": "Incidente no encontrado"}), 404
        
        incidente_id = result[0]
        
        # Obtener todas las evidencias
        query = """
        SELECT 
            seccion as sub_modulo,
            numero_evidencia as item,
            nombre_archivo,
            descripcion,
            fecha_carga
        FROM EvidenciasIncidentes
        WHERE IncidenteID = ?
        ORDER BY seccion, numero_evidencia
        """
        
        cursor.execute(query, (incidente_id,))
        
        evidencias = []
        for row in cursor.fetchall():
            evidencias.append({
                'sub_modulo': row[0],
                'item': row[1],
                'nombre_archivo': row[2],
                'descripcion': row[3],
                'fecha_carga': row[4].isoformat() if row[4] else None
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "evidencias": evidencias
        }), 200
        
    except Exception as e:
        print(f"Error obteniendo resumen: {str(e)}")
        return jsonify({
            "error": "Error al obtener resumen de evidencias",
            "detalle": str(e)
        }), 500

@login_required
def revertir_a_semilla_original(usuario):
    """Revierte los cambios al estado original del incidente"""
    try:
        datos = request.get_json()
        indice_unico = datos.get('indice_unico')
        
        if not indice_unico:
            return jsonify({"error": "Índice único no proporcionado"}), 400
        
        # Eliminar archivo temporal para forzar recarga desde BD
        temp_file = os.path.join(editor.temp_folder, f"{indice_unico}.json")
        
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        return jsonify({
            "success": True,
            "mensaje": "Cambios revertidos exitosamente"
        }), 200
        
    except Exception as e:
        print(f"Error revirtiendo cambios: {str(e)}")
        return jsonify({
            "error": "Error al revertir cambios",
            "detalle": str(e)
        }), 500

# Rutas del módulo
def registrar_rutas_edicion(app):
    """Registra las rutas del módulo de edición de incidentes"""
    app.add_url_rule('/api/incidentes/editar/obtener', 
                     'obtener_incidente_para_edicion', 
                     obtener_incidente_para_edicion, 
                     methods=['GET'])
    
    app.add_url_rule('/api/incidentes/editar/actualizar', 
                     'actualizar_incidente', 
                     actualizar_incidente, 
                     methods=['PUT'])
    
    app.add_url_rule('/api/incidentes/editar/eliminar-evidencia', 
                     'eliminar_evidencia_incidente', 
                     eliminar_evidencia_incidente, 
                     methods=['DELETE'])
    
    app.add_url_rule('/api/incidentes/editar/resumen-evidencias', 
                     'obtener_resumen_evidencias', 
                     obtener_resumen_evidencias, 
                     methods=['GET'])
    
    app.add_url_rule('/api/incidentes/editar/revertir', 
                     'revertir_a_semilla_original', 
                     revertir_a_semilla_original, 
                     methods=['POST'])
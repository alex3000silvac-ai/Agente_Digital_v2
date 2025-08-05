# modules/admin/incidentes_actualizar.py
# Endpoint para actualizar incidentes con soporte para archivos

from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from app.database import get_db_connection
from app.auth_utils import token_required
import logging
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from config import Config

logger = logging.getLogger(__name__)

incidentes_actualizar_bp = Blueprint('incidentes_actualizar', __name__)

UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'txt', 'zip'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@incidentes_actualizar_bp.route('/api/incidentes/<int:incidente_id>/actualizar', methods=['PUT'])
@cross_origin()
@token_required
def actualizar_incidente(current_user_id, current_user_rol, current_user_email, current_user_nombre, incidente_id):
    """
    Actualiza un incidente existente con soporte para archivos
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar que el incidente existe
        cursor.execute("SELECT IncidenteID FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Incidente no encontrado"}), 404
        
        # Obtener datos del request
        # Si viene como FormData (con archivos), los datos estarán en request.form
        # Si viene como JSON, estarán en request.json
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Datos vienen con archivos
            datos = json.loads(request.form.get('datos', '{}'))
            logger.info("Actualizando con FormData (archivos incluidos)")
        else:
            # Datos vienen como JSON
            datos = request.get_json()
            logger.info("Actualizando con JSON (sin archivos)")
        
        # Extraer campos del formulario
        form_data = datos
        
        # Actualizar campos principales del incidente
        campos_actualizar = []
        valores = []
        
        # Mapeo de campos del formulario a columnas de la BD
        mapeo_campos = {
            '1.1': 'TipoRegistro',
            '1.2': 'Titulo',
            '1.3': 'FechaDeteccion',
            '1.4': 'FechaOcurrencia',
            '1.5': 'Criticidad',
            '1.6': 'OrigenIncidente',
            '1.7.solicitar_csirt': 'SolicitarCSIRT',
            '1.7.tipo_apoyo': 'TipoApoyoCSIRT',
            '1.7.urgencia': 'UrgenciaCSIRT',
            '1.7.observaciones_csirt': 'ObservacionesCSIRT',
            '2.1': 'DescripcionInicial',
            '2.2': 'SistemasAfectados',
            '2.3': 'UsuariosAfectados',
            '2.4': 'TiempoIncidencia',
            '2.5': 'ImpactoPreliminar',
            '2.6': 'AlcanceGeografico',
            '3.1': 'AnciImpactoPreliminar',
            '3.2': 'AnciTipoAmenaza',
            '3.3': 'AnciAgenteAmenaza',
            '3.4': 'AnciVulnerabilidadExplotada',
            '3.5': 'AnciDatosComprometidos',
            '3.6': 'AnciAfectacionTerceros',
            '4.1': 'AccionesInmediatas',
            '4.2': 'ResponsableCliente',
            '4.3': 'NivelEscalamiento',
            '4.4': 'MedidasContencion',
            '4.5': 'PlanComunicacion',
            '4.6': 'NotificacionesRealizadas',
            '5.1': 'CausaRaiz',
            '5.2': 'SolucionImplementada',
            '5.3': 'MedidasPreventivas',
            '5.4': 'ProximosPasos',
            '5.5': 'LeccionesAprendidas',
            '5.6': 'DocumentacionAdjunta',
            '5.2.2': 'DescripcionCompleta',  # Campo 5.2.2 mencionado por usuario
            '6.1': 'FechaResolucion',
            '6.2': 'EstadoFinal',
            '6.3': 'PersonaCierre',
            '6.4': 'AprobacionCierre',
            '6.5': 'ObservacionesFinales',
            '6.6': 'RequiereAcciones',
            # Campos de sección 7 (mapear a campos de descripción/observaciones)
            '7.1': 'DescripcionEstadoActual',  # Sección 7 mencionada por usuario
            '7.2': 'EfectosColaterales',
            '7.3': 'ProgramaRestauracion'
        }
        
        # Construir query de actualización
        for campo_form, campo_bd in mapeo_campos.items():
            if campo_form in form_data:
                valor = form_data[campo_form]
                # Convertir valores booleanos
                if campo_bd in ['SolicitarCSIRT', 'RequiereAcciones']:
                    valor = 1 if valor else 0
                campos_actualizar.append(f"{campo_bd} = ?")
                valores.append(valor)
        
        # Agregar campos de auditoría
        campos_actualizar.append("FechaActualizacion = GETDATE()")
        campos_actualizar.append("ModificadoPor = ?")
        valores.append(current_user_id)
        
        # Agregar ID del incidente al final
        valores.append(incidente_id)
        
        # Ejecutar actualización
        if campos_actualizar:
            query = f"""
                UPDATE Incidentes 
                SET {', '.join(campos_actualizar)}
                WHERE IncidenteID = ?
            """
            cursor.execute(query, valores)
        
        # Procesar taxonomías si vienen
        if 'taxonomias_seleccionadas' in datos:
            # Primero eliminar las existentes
            cursor.execute("DELETE FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?", (incidente_id,))
            
            # Insertar las nuevas
            for tax in datos['taxonomias_seleccionadas']:
                # Crear comentarios en el mismo formato que incidentes_crear.py
                justificacion = tax.get('justificacion', '')
                descripcion_problema = tax.get('descripcionProblema', '')
                comentarios = f"Justificación: {justificacion}\nDescripción del problema: {descripcion_problema}"
                
                cursor.execute("""
                    INSERT INTO INCIDENTE_TAXONOMIA 
                    (IncidenteID, Id_Taxonomia, Comentarios, FechaAsignacion, CreadoPor)
                    VALUES (?, ?, ?, GETDATE(), ?)
                """, (
                    incidente_id,
                    tax.get('id'),
                    comentarios,
                    current_user_id
                ))
        
        # Procesar archivos eliminados
        if 'archivos_eliminados' in datos:
            for archivo in datos['archivos_eliminados']:
                if archivo.get('id'):
                    # Obtener la ruta del archivo antes de eliminarlo
                    cursor.execute("""
                        SELECT RutaArchivo FROM INCIDENTES_ARCHIVOS 
                        WHERE ArchivoID = ? AND IncidenteID = ?
                    """, (archivo['id'], incidente_id))
                    
                    result = cursor.fetchone()
                    if result and result[0]:
                        # Eliminar archivo físico
                        try:
                            if os.path.exists(result[0]):
                                os.remove(result[0])
                                logger.info(f"Archivo físico eliminado: {result[0]}")
                        except Exception as e:
                            logger.error(f"Error eliminando archivo físico: {e}")
                    
                    # Marcar como inactivo en la BD
                    cursor.execute("""
                        UPDATE INCIDENTES_ARCHIVOS 
                        SET Activo = 0, FechaEliminacion = GETDATE(), EliminadoPor = ?
                        WHERE ArchivoID = ? AND IncidenteID = ?
                    """, (current_user_id, archivo['id'], incidente_id))
        
        # Procesar archivos nuevos si vienen en FormData
        if request.files:
            # Crear directorio si no existe
            incidente_dir = os.path.join(UPLOAD_FOLDER, 'incidentes', str(incidente_id))
            os.makedirs(incidente_dir, exist_ok=True)
            
            for field_name in request.files:
                files = request.files.getlist(field_name)
                
                # Extraer información de la sección del nombre del campo
                parts = field_name.split('_')
                
                # Procesar archivos de taxonomías
                # Formato: archivo_taxonomia_{tax_id}_{index}
                if len(parts) >= 4 and parts[0] == 'archivo' and parts[1] == 'taxonomia':
                    tax_id = '_'.join(parts[2:-1])  # Reconstruir el ID de taxonomía
                    
                    for file in files:
                        if file and allowed_file(file.filename):
                            # Validar tamaño
                            file.seek(0, os.SEEK_END)
                            file_size = file.tell()
                            file.seek(0)
                            
                            if file_size > MAX_FILE_SIZE:
                                logger.warning(f"Archivo {file.filename} excede el tamaño máximo")
                                continue
                            
                            # Generar nombre seguro
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            filename = secure_filename(file.filename)
                            nombre_archivo = f"{timestamp}_{filename}"
                            
                            # Crear directorio para taxonomías
                            tax_dir = os.path.join(UPLOAD_FOLDER, 'incidentes', str(incidente_id), 'taxonomias')
                            os.makedirs(tax_dir, exist_ok=True)
                            ruta_archivo = os.path.join(tax_dir, nombre_archivo)
                            
                            # Guardar archivo
                            file.save(ruta_archivo)
                            
                            # Registrar en EVIDENCIAS_TAXONOMIA
                            cursor.execute("""
                                INSERT INTO EVIDENCIAS_TAXONOMIA 
                                (IncidenteID, TaxonomiaID, NombreArchivo, NombreArchivoOriginal,
                                 RutaArchivo, TamanoArchivo, TipoArchivo, FechaSubida, SubidoPor, Activo)
                                VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, 1)
                            """, (
                                incidente_id,
                                tax_id,
                                nombre_archivo,
                                file.filename,
                                ruta_archivo,
                                file_size,
                                file.content_type or 'application/octet-stream',
                                current_user_id
                            ))
                            
                            logger.info(f"Archivo de taxonomía guardado: {nombre_archivo} para taxonomía {tax_id}")
                
                # Procesar archivos de secciones regulares
                # Formato esperado: archivo_seccion_2_campo_5
                elif len(parts) >= 4 and parts[0] == 'archivo' and parts[1] == 'seccion':
                    seccion_id = int(parts[2])
                    
                    for file in files:
                        if file and allowed_file(file.filename):
                            # Validar tamaño
                            file.seek(0, os.SEEK_END)
                            file_size = file.tell()
                            file.seek(0)
                            
                            if file_size > MAX_FILE_SIZE:
                                logger.warning(f"Archivo {file.filename} excede el tamaño máximo")
                                continue
                            
                            # Generar nombre seguro
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            filename = secure_filename(file.filename)
                            nombre_archivo = f"{timestamp}_{filename}"
                            ruta_archivo = os.path.join(incidente_dir, nombre_archivo)
                            
                            # Guardar archivo
                            file.save(ruta_archivo)
                            
                            # Registrar en BD
                            cursor.execute("""
                                INSERT INTO INCIDENTES_ARCHIVOS 
                                (IncidenteID, NombreArchivo, TipoArchivo, TamanoKB, 
                                 RutaArchivo, SeccionID, FechaCarga, SubidoPor, Activo)
                                VALUES (?, ?, ?, ?, ?, ?, GETDATE(), ?, 1)
                            """, (
                                incidente_id,
                                file.filename,
                                file.content_type or 'application/octet-stream',
                                round(file_size / 1024, 2),
                                ruta_archivo,
                                seccion_id,
                                current_user_id
                            ))
                            
                            logger.info(f"Archivo guardado: {nombre_archivo} en sección {seccion_id}")
        
        # Registrar en auditoría
        cursor.execute("""
            INSERT INTO INCIDENTES_AUDITORIA 
            (IncidenteID, TipoAccion, DescripcionAccion, DatosAnteriores, DatosNuevos, Usuario, FechaAccion)
            VALUES (?, 'ACTUALIZAR', 'Incidente actualizado', '', ?, ?, GETDATE())
        """, (
            incidente_id,
            json.dumps({"campos_actualizados": len(campos_actualizar)}, ensure_ascii=False),
            current_user_email
        ))
        
        conn.commit()
        
        logger.info(f"Incidente {incidente_id} actualizado exitosamente por {current_user_email}")
        
        return jsonify({
            "success": True,
            "mensaje": "Incidente actualizado exitosamente",
            "incidente_id": incidente_id
        }), 200
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error actualizando incidente: {str(e)}")
        return jsonify({"error": f"Error al actualizar el incidente: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

@incidentes_actualizar_bp.route('/api/incidentes/<int:incidente_id>/subir-archivo', methods=['POST'])
@cross_origin()
@token_required
def subir_archivo_incidente(current_user_id, current_user_rol, current_user_email, current_user_nombre, incidente_id):
    """
    Endpoint específico para subir archivos a un incidente
    """
    try:
        if 'archivo' not in request.files:
            return jsonify({"error": "No se encontró archivo en la petición"}), 400
        
        file = request.files['archivo']
        seccion_id = request.form.get('seccion_id', type=int)
        campo_id = request.form.get('campo_id', type=int)
        
        if not file or file.filename == '':
            return jsonify({"error": "No se seleccionó ningún archivo"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Tipo de archivo no permitido"}), 400
        
        # Validar tamaño
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({"error": "El archivo excede el tamaño máximo de 10MB"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar que el incidente existe
        cursor.execute("SELECT IncidenteID FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Incidente no encontrado"}), 404
        
        # Crear directorio
        incidente_dir = os.path.join(UPLOAD_FOLDER, 'incidentes', str(incidente_id))
        os.makedirs(incidente_dir, exist_ok=True)
        
        # Generar nombre seguro
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(file.filename)
        nombre_archivo = f"{timestamp}_{filename}"
        ruta_archivo = os.path.join(incidente_dir, nombre_archivo)
        
        # Guardar archivo
        file.save(ruta_archivo)
        
        # Registrar en BD
        cursor.execute("""
            INSERT INTO INCIDENTES_ARCHIVOS 
            (IncidenteID, NombreArchivo, TipoArchivo, TamanoKB, 
             RutaArchivo, SeccionID, FechaCarga, SubidoPor, Activo)
            VALUES (?, ?, ?, ?, ?, ?, GETDATE(), ?, 1)
        """, (
            incidente_id,
            file.filename,
            file.content_type or 'application/octet-stream',
            round(file_size / 1024, 2),
            ruta_archivo,
            seccion_id,
            current_user_id
        ))
        
        cursor.execute("SELECT SCOPE_IDENTITY()")
        archivo_id = cursor.fetchone()[0]
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "archivo": {
                "id": archivo_id,
                "nombre": file.filename,
                "tamaño": file_size,
                "tipo": file.content_type
            }
        }), 200
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error subiendo archivo: {str(e)}")
        return jsonify({"error": f"Error al subir el archivo: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
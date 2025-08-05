from flask import Blueprint, request, jsonify, current_app, send_file
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename
import json
import io
from ..modules.core.database import get_db_connection

incidente_bp = Blueprint('incidente_completo', __name__, url_prefix='/api/incidente')

# Configuración de la carpeta de subida de archivos
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@incidente_bp.route('/', methods=['POST', 'OPTIONS'])
# @login_required
# @has_role('admin')
def create_incidente():
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    try:
        data = request.form.to_dict()
        archivos = request.files.getlist('archivos')

        # Validar campos obligatorios básicos
        titulo = data.get('Titulo', data.get('titulo', ''))
        if not titulo:
            return jsonify({"error": "El campo 'titulo' es obligatorio."}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión a la base de datos"}), 500

        cursor = conn.cursor()

        # Mapear campos del formulario V2 a campos de BD
        # El formulario envía los nombres de BD directamente
        descripcion_inicial = data.get('DescripcionInicial', data.get('descripcion', ''))
        criticidad = data.get('Criticidad', data.get('severidad', 'Media'))
        estado_actual = data.get('EstadoActual', data.get('estado', 'Abierto'))
        tipo_flujo = data.get('TipoFlujo', data.get('tipo_incidente', 'Informativo'))
        fecha_deteccion = data.get('FechaDeteccion', data.get('fecha_deteccion'))
        fecha_ocurrencia = data.get('FechaOcurrencia', data.get('fecha_ocurrencia'))
        origen_incidente = data.get('OrigenIncidente', data.get('fuente_deteccion', ''))
        sistemas_afectados = data.get('SistemasAfectados', data.get('sistemas_afectados', ''))
        acciones_inmediatas = data.get('AccionesInmediatas', data.get('acciones_tomadas', ''))
        responsable_cliente = data.get('ResponsableCliente', data.get('responsable_cliente', ''))
        alcance_geografico = data.get('AlcanceGeografico', data.get('alcance_geografico', ''))
        servicios_interrumpidos = data.get('ServiciosInterrumpidos', data.get('servicios_interrumpidos', ''))
        anci_impacto_preliminar = data.get('AnciImpactoPreliminar', data.get('impacto_estimado', ''))
        anci_tipo_amenaza = data.get('AnciTipoAmenaza', data.get('tipo_amenaza', ''))
        causa_raiz = data.get('CausaRaiz', data.get('causa_raiz', ''))
        lecciones_aprendidas = data.get('LeccionesAprendidas', data.get('lecciones_aprendidas', ''))
        plan_mejora = data.get('PlanMejora', data.get('plan_mejora', ''))

        # Insertar el incidente principal
        query_incidente = """
            INSERT INTO Incidentes (
                Titulo, DescripcionInicial, Criticidad, EstadoActual, FechaCreacion, FechaActualizacion,
                EmpresaID, CreadoPor, FechaDeteccion, FechaOcurrencia, TipoFlujo, OrigenIncidente,
                SistemasAfectados, AccionesInmediatas, ResponsableCliente,
                AlcanceGeografico, ServiciosInterrumpidos, AnciImpactoPreliminar, AnciTipoAmenaza,
                CausaRaiz, LeccionesAprendidas, PlanMejora
            ) VALUES (?, ?, ?, ?, GETDATE(), GETDATE(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        cursor.execute(query_incidente,
            titulo, descripcion_inicial, criticidad, estado_actual,
            data['empresa_id'], data['creado_por'], fecha_deteccion, fecha_ocurrencia, tipo_flujo,
            origen_incidente, sistemas_afectados, acciones_inmediatas, responsable_cliente,
            alcance_geografico, servicios_interrumpidos, anci_impacto_preliminar, anci_tipo_amenaza,
            causa_raiz, lecciones_aprendidas, plan_mejora
        )
        conn.commit()

        # Obtener el IncidenteID recién creado
        cursor.execute("SELECT @@IDENTITY AS IncidenteID;")
        result = cursor.fetchone()
        incidente_id = result.IncidenteID if result else None

        # Guardar archivos adjuntos en EvidenciasIncidentes
        if archivos:
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            
            for archivo in archivos:
                if archivo and allowed_file(archivo.filename):
                    filename = secure_filename(archivo.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                    archivo.save(filepath)

                    query_archivo = """
                        INSERT INTO EvidenciasIncidentes (IncidenteID, NombreArchivo, RutaArchivo, TipoArchivo, TamanoKB, Descripcion, Version, FechaSubida, SubidoPor)
                        VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), ?)
                    """
                    # Obtener el tamaño del archivo de forma segura
                    archivo.seek(0, 2)  # Ir al final del archivo
                    tamano_bytes = archivo.tell()
                    archivo.seek(0)  # Volver al inicio para guardarlo
                    tamano_kb = tamano_bytes / 1024 # Convertir bytes a KB
                    descripcion_archivo = data.get(f'descripcion_archivo_{filename}', '')
                    version_archivo = data.get(f'version_archivo_{filename}', 1)
                    subido_por = data.get('creado_por', 'Sistema') # O del token de usuario

                    cursor.execute(query_archivo, incidente_id, filename, filepath, archivo.mimetype, tamano_kb, descripcion_archivo, version_archivo, subido_por)
                    conn.commit()
                else:
                    print(f"Archivo no permitido o vacío: {archivo.filename}")

        # Guardar taxonomías seleccionadas en INCIDENTE_TAXONOMIA
        taxonomias_seleccionadas_str = data.get('taxonomias_seleccionadas', '[]')
        taxonomias_seleccionadas = json.loads(taxonomias_seleccionadas_str)
        for taxonomia in taxonomias_seleccionadas:
            query_taxonomia = """
                INSERT INTO INCIDENTE_TAXONOMIA (IncidenteID, Id_Taxonomia, Comentarios, FechaAsignacion, CreadoPor)
                VALUES (?, ?, ?, GETDATE(), ?)
            """
            cursor.execute(query_taxonomia, incidente_id, taxonomia['Id_Taxonomia'], taxonomia.get('Comentarios', ''), data['creado_por'])
            conn.commit()

        # Guardar comentarios adicionales en COMENTARIOS_TAXONOMIA (asumiendo que es para comentarios generales del incidente)
        comentarios_adicionales_str = data.get('comentarios_adicionales_json', '[]')
        comentarios_adicionales = json.loads(comentarios_adicionales_str)
        for comentario_data in comentarios_adicionales:
            query_comentario = """
                INSERT INTO COMENTARIOS_TAXONOMIA (IncidenteID, Comentario, FechaCreacion, CreadoPor)
                VALUES (?, ?, GETDATE(), ?)
            """
            cursor.execute(query_comentario, incidente_id, comentario_data['texto'], data['creado_por'])
            conn.commit()

        conn.close()
        response = jsonify({"message": "Incidente creado exitosamente", "incidente_id": incidente_id})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201

    except Exception as e:
        print(f"Error al crear incidente: {e}")
        return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500

@incidente_bp.route('/<int:incidente_id>', methods=['GET', 'OPTIONS'])
# @login_required
def get_incidente(incidente_id):
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor()

        # Obtener detalles del incidente con TODOS los campos
        query_incidente = """
            SELECT 
                IncidenteID, Titulo, DescripcionInicial, Criticidad, EstadoActual, FechaCreacion, FechaActualizacion,
                EmpresaID, CreadoPor, FechaDeteccion, FechaOcurrencia, TipoFlujo, OrigenIncidente,
                SistemasAfectados, AccionesInmediatas, ResponsableCliente,
                FechaCierre, IDVisible, ReporteAnciID, FechaDeclaracionANCI,
                AlcanceGeografico, ServiciosInterrumpidos, AnciImpactoPreliminar, AnciTipoAmenaza,
                CausaRaiz, LeccionesAprendidas, PlanMejora
            FROM Incidentes
            WHERE IncidenteID = ?
        """
        cursor.execute(query_incidente, incidente_id)
        incidente = cursor.fetchone()

        if not incidente:
            return jsonify({"error": "Incidente no encontrado"}), 404

        incidente_dict = dict(zip([column[0] for column in cursor.description], incidente))
        
        # Convertir fechas a formato ISO si existen
        if incidente_dict.get('FechaCreacion'):
            incidente_dict['FechaCreacion'] = incidente_dict['FechaCreacion'].isoformat()
        if incidente_dict.get('FechaActualizacion'):
            incidente_dict['FechaActualizacion'] = incidente_dict['FechaActualizacion'].isoformat()
        if incidente_dict.get('FechaOcurrencia'):
            incidente_dict['FechaOcurrencia'] = incidente_dict['FechaOcurrencia'].isoformat()
        if incidente_dict.get('FechaCierre'):
            incidente_dict['FechaCierre'] = incidente_dict['FechaCierre'].isoformat()

        # Obtener archivos adjuntos de EvidenciasIncidentes
        query_archivos = """
            SELECT EvidenciaID, NombreArchivo, RutaArchivo, TipoArchivo, TamanoKB, Descripcion, Version, FechaSubida, SubidoPor
            FROM EvidenciasIncidentes
            WHERE IncidenteID = ?
            ORDER BY FechaSubida DESC
        """
        archivos_adjuntos = []
        try:
            cursor.execute(query_archivos, incidente_id)
            for row in cursor.fetchall():
                archivo_dict = dict(zip([column[0] for column in cursor.description], row))
                if archivo_dict.get('FechaSubida'):
                    archivo_dict['FechaSubida'] = archivo_dict['FechaSubida'].isoformat()
                archivos_adjuntos.append(archivo_dict)
        except Exception as e:
            print(f"ERROR: Error al recuperar archivos para incidente {incidente_id}: {e}")
            archivos_adjuntos = []
        
        incidente_dict['archivos_adjuntos'] = archivos_adjuntos

        # Obtener historial de cambios de HistorialIncidentes
        query_historial = """
            SELECT HistorialID, CampoModificado, ValorAnterior, ValorNuevo, FechaCambio, UsuarioCambio
            FROM HistorialIncidentes
            WHERE IncidenteID = ?
            ORDER BY FechaCambio DESC
        """
        historial_cambios = []
        try:
            cursor.execute(query_historial, incidente_id)
            for row in cursor.fetchall():
                historial_dict = dict(zip([column[0] for column in cursor.description], row))
                if historial_dict.get('FechaCambio'):
                    historial_dict['FechaCambio'] = historial_dict['FechaCambio'].isoformat()
                historial_cambios.append(historial_dict)
        except Exception as e:
            print(f"ERROR: Error al recuperar historial de cambios para incidente {incidente_id}: {e}")
            historial_cambios = []
        
        incidente_dict['historial_cambios'] = historial_cambios

        # Obtener taxonomías asociadas al incidente de INCIDENTE_TAXONOMIA y TAXONOMIA_INCIDENTES
        query_taxonomias = """
            SELECT IT.Id_Taxonomia, IT.Comentarios, TI.Area, TI.Efecto, TI.Categoria_del_Incidente, TI.Subcategoria_del_Incidente
            FROM INCIDENTE_TAXONOMIA IT
            JOIN TAXONOMIA_INCIDENTES TI ON IT.Id_Taxonomia = TI.Id_Incidente
            WHERE IT.IncidenteID = ?
        """
        taxonomias = []
        try:
            cursor.execute(query_taxonomias, incidente_id)
            for row in cursor.fetchall():
                taxonomias.append(dict(zip([column[0] for column in cursor.description], row)))
        except Exception as e:
            print(f"ERROR: Error al recuperar taxonomías para incidente {incidente_id}: {e}")
            taxonomias = []
        
        incidente_dict['Taxonomias'] = taxonomias # Asegúrate de que el nombre de la clave coincida con el test

        # Obtener comentarios adicionales de COMENTARIOS_TAXONOMIA
        query_comentarios = """
            SELECT ComentarioID, Comentario, FechaCreacion, CreadoPor
            FROM COMENTARIOS_TAXONOMIA
            WHERE IncidenteID = ?
            ORDER BY FechaCreacion DESC
        """
        comentarios = []
        try:
            cursor.execute(query_comentarios, incidente_id)
            for row in cursor.fetchall():
                comentario_dict = dict(zip([column[0] for column in cursor.description], row))
                if comentario_dict.get('FechaCreacion'):
                    comentario_dict['FechaCreacion'] = comentario_dict['FechaCreacion'].isoformat()
                comentarios.append(comentario_dict)
        except Exception as e:
            print(f"ERROR: Error al recuperar comentarios para incidente {incidente_id}: {e}")
            comentarios = []
        
        incidente_dict['Comentarios'] = comentarios # Asegúrate de que el nombre de la clave coincida con el test

        # Manejo de Reportes ANCI (si la tabla REPORTES_ANCI existe y es relevante)
        # Si REPORTES_ANCI es una tabla separada y no un campo en Incidentes, se consultaría aquí.
        # Por ahora, el log indica que el campo ReporteAnciID existe en Incidentes, pero la tabla REPORTES_ANCI no.
        # Si necesitas recuperar detalles de REPORTES_ANCI, deberás crear la tabla y su lógica de consulta.
        # Por el momento, solo se imprime el error si la consulta falla.
        try:
            # Ejemplo de cómo se podría consultar si la tabla ReportesANCI existiera
            query_reporte_anci = "SELECT * FROM ReportesANCI WHERE ReporteAnciID = ?"
            cursor.execute(query_reporte_anci, incidente_dict.get('ReporteAnciID'))
            reporte_anci_data = cursor.fetchone()
            if reporte_anci_data:
                incidente_dict['ReporteAnciDetalle'] = dict(zip([column[0] for column in cursor.description], reporte_anci_data))
            pass # No se hace nada si la tabla no existe o no se consulta
        except Exception as e:
            print(f"ERROR: Error al recuperar ReporteAnciID para incidente {incidente_id}: {e}")
            # No se agrega al diccionario si hay error, o se agrega un valor por defecto

        conn.close()
        return jsonify(incidente_dict), 200

    except Exception as e:
        print(f"Error al obtener incidente: {e}")
        return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500

@incidente_bp.route('/<int:incidente_id>', methods=['PUT', 'OPTIONS'])
# @login_required
# @has_role('admin')
def update_incidente(incidente_id):
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    try:
        data = request.form.to_dict()
        archivos_nuevos = request.files.getlist('archivos_nuevos')
        archivos_a_eliminar_str = data.get('archivos_a_eliminar', '[]')
        archivos_a_eliminar = json.loads(archivos_a_eliminar_str)

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión a la base de datos"}), 500

        cursor = conn.cursor()

        # Obtener el incidente actual para registrar el historial de cambios
        query_get_old_incidente = """
            SELECT 
                Titulo, DescripcionInicial, Criticidad, EstadoActual, FechaDeteccion, FechaOcurrencia, TipoFlujo, 
                OrigenIncidente, SistemasAfectados, AccionesInmediatas, ResponsableCliente,
                FechaCierre, AlcanceGeografico, ServiciosInterrumpidos, AnciImpactoPreliminar, AnciTipoAmenaza,
                CausaRaiz, LeccionesAprendidas, PlanMejora
            FROM Incidentes
            WHERE IncidenteID = ?
        """
        cursor.execute(query_get_old_incidente, incidente_id)
        old_incidente = cursor.fetchone()

        if not old_incidente:
            conn.close()
            return jsonify({"error": "Incidente no encontrado"}), 404
        
        old_incidente_dict = dict(zip([column[0] for column in cursor.description], old_incidente))

        # Mapear campos del formulario V2 a campos de BD para actualización
        titulo = data.get('Titulo', data.get('titulo', old_incidente_dict.get('Titulo')))
        descripcion_inicial = data.get('DescripcionInicial', data.get('descripcion', old_incidente_dict.get('DescripcionInicial')))
        criticidad = data.get('Criticidad', data.get('severidad', old_incidente_dict.get('Criticidad')))
        estado_actual = data.get('EstadoActual', data.get('estado', old_incidente_dict.get('EstadoActual')))
        tipo_flujo = data.get('TipoFlujo', data.get('tipo_incidente', old_incidente_dict.get('TipoFlujo')))
        fecha_deteccion = data.get('FechaDeteccion', data.get('fecha_deteccion', old_incidente_dict.get('FechaDeteccion')))
        fecha_ocurrencia = data.get('FechaOcurrencia', data.get('fecha_ocurrencia', old_incidente_dict.get('FechaOcurrencia')))
        origen_incidente = data.get('OrigenIncidente', data.get('fuente_deteccion', old_incidente_dict.get('OrigenIncidente')))
        sistemas_afectados = data.get('SistemasAfectados', data.get('sistemas_afectados', old_incidente_dict.get('SistemasAfectados')))
        acciones_inmediatas = data.get('AccionesInmediatas', data.get('acciones_tomadas', old_incidente_dict.get('AccionesInmediatas')))
        responsable_cliente = data.get('ResponsableCliente', data.get('responsable_cliente', old_incidente_dict.get('ResponsableCliente')))
        alcance_geografico = data.get('AlcanceGeografico', data.get('alcance_geografico', old_incidente_dict.get('AlcanceGeografico')))
        servicios_interrumpidos = data.get('ServiciosInterrumpidos', data.get('servicios_interrumpidos', old_incidente_dict.get('ServiciosInterrumpidos')))
        anci_impacto_preliminar = data.get('AnciImpactoPreliminar', data.get('impacto_estimado', old_incidente_dict.get('AnciImpactoPreliminar')))
        anci_tipo_amenaza = data.get('AnciTipoAmenaza', data.get('tipo_amenaza', old_incidente_dict.get('AnciTipoAmenaza')))
        causa_raiz = data.get('CausaRaiz', data.get('causa_raiz', old_incidente_dict.get('CausaRaiz')))
        lecciones_aprendidas = data.get('LeccionesAprendidas', data.get('lecciones_aprendidas', old_incidente_dict.get('LeccionesAprendidas')))
        plan_mejora = data.get('PlanMejora', data.get('plan_mejora', old_incidente_dict.get('PlanMejora')))
        fecha_cierre = data.get('FechaCierre', data.get('fecha_cierre', old_incidente_dict.get('FechaCierre')))
        responsable_cierre = data.get('ResponsableCierre', data.get('responsable_cierre', old_incidente_dict.get('ResponsableCliente')))

        # Actualizar el incidente principal
        query_update_incidente = """
            UPDATE Incidentes SET
                Titulo = ?, DescripcionInicial = ?, Criticidad = ?, EstadoActual = ?, FechaActualizacion = GETDATE(),
                FechaDeteccion = ?, FechaOcurrencia = ?, TipoFlujo = ?, OrigenIncidente = ?,
                SistemasAfectados = ?, AccionesInmediatas = ?, ResponsableCliente = ?,
                AlcanceGeografico = ?, ServiciosInterrumpidos = ?, AnciImpactoPreliminar = ?, AnciTipoAmenaza = ?,
                CausaRaiz = ?, LeccionesAprendidas = ?, PlanMejora = ?, FechaCierre = ?
            WHERE IncidenteID = ?
        """

        cursor.execute(query_update_incidente,
            titulo, descripcion_inicial, criticidad, estado_actual,
            fecha_deteccion, fecha_ocurrencia, tipo_flujo, origen_incidente,
            sistemas_afectados, acciones_inmediatas, responsable_cliente,
            alcance_geografico, servicios_interrumpidos, anci_impacto_preliminar, anci_tipo_amenaza,
            causa_raiz, lecciones_aprendidas, plan_mejora, fecha_cierre,
            incidente_id
        )
        conn.commit()

        # Registrar cambios en el historial en HistorialIncidentes
        for field, new_value in data.items():
            if field in old_incidente_dict and str(old_incidente_dict[field]) != str(new_value):
                query_historial = """
                    INSERT INTO HistorialIncidentes (IncidenteID, CampoModificado, ValorAnterior, ValorNuevo, FechaCambio, UsuarioCambio)
                    VALUES (?, ?, ?, ?, GETDATE(), ?)
                """
                # Asumiendo que 'UsuarioCambio' viene en los datos de la solicitud o se obtiene del token
                usuario_cambio = data.get('modificado_por', 'Sistema') 
                cursor.execute(query_historial, incidente_id, field, str(old_incidente_dict[field]), str(new_value), usuario_cambio)
                conn.commit()

        # Eliminar archivos adjuntos de EvidenciasIncidentes
        for archivo_id in archivos_a_eliminar:
            query_get_filepath = "SELECT RutaArchivo FROM EvidenciasIncidentes WHERE EvidenciaID = ? AND IncidenteID = ?"
            cursor.execute(query_get_filepath, archivo_id, incidente_id)
            result = cursor.fetchone()
            if result:
                filepath_to_delete = result.RutaArchivo
                if os.path.exists(filepath_to_delete):
                    os.remove(filepath_to_delete)
                
                query_delete_archivo = "DELETE FROM EvidenciasIncidentes WHERE EvidenciaID = ?"
                cursor.execute(query_delete_archivo, archivo_id)
                conn.commit()

        # Añadir nuevos archivos adjuntos en EvidenciasIncidentes
        if archivos_nuevos:
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            
            for archivo in archivos_nuevos:
                if archivo and allowed_file(archivo.filename):
                    filename = secure_filename(archivo.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                    archivo.save(filepath)

                    query_archivo = """
                        INSERT INTO EvidenciasIncidentes (IncidenteID, NombreArchivo, RutaArchivo, TipoArchivo, TamanoKB, Descripcion, Version, FechaSubida, SubidoPor)
                        VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), ?)
                    """
                    # Obtener el tamaño del archivo de forma segura
                    archivo.seek(0, 2)  # Ir al final del archivo
                    tamano_bytes = archivo.tell()
                    archivo.seek(0)  # Volver al inicio para guardarlo
                    tamano_kb = tamano_bytes / 1024 # Convertir bytes a KB
                    descripcion_archivo = data.get(f'descripcion_archivo_{filename}', '')
                    version_archivo = data.get(f'version_archivo_{filename}', 1)
                    subido_por = data.get('modificado_por', 'Sistema') # O del token de usuario

                    cursor.execute(query_archivo, incidente_id, filename, filepath, archivo.mimetype, tamano_kb, descripcion_archivo, version_archivo, subido_por)
                    conn.commit()
                else:
                    print(f"Archivo no permitido o vacío: {archivo.filename}")

        conn.close()
        return jsonify({"message": "Incidente actualizado exitosamente", "incidente_id": incidente_id}), 200

    except Exception as e:
        print(f"Error al actualizar incidente: {e}")
        return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500

@incidente_bp.route('/<int:incidente_id>', methods=['DELETE'])
# @login_required
# @has_role('admin')
def delete_incidente(incidente_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor()

        # Eliminar archivos adjuntos asociados de EvidenciasIncidentes
        query_get_files = "SELECT RutaArchivo FROM EvidenciasIncidentes WHERE IncidenteID = ?"
        cursor.execute(query_get_files, incidente_id)
        files_to_delete = cursor.fetchall()

        for file_row in files_to_delete:
            filepath = file_row.RutaArchivo
            if os.path.exists(filepath):
                os.remove(filepath)
        
        query_delete_files = "DELETE FROM EvidenciasIncidentes WHERE IncidenteID = ?"
        cursor.execute(query_delete_files, incidente_id)
        conn.commit()

        # Eliminar historial de cambios asociado de HistorialIncidentes
        query_delete_historial = "DELETE FROM HistorialIncidentes WHERE IncidenteID = ?"
        cursor.execute(query_delete_historial, incidente_id)
        conn.commit()

        # Eliminar taxonomías asociadas de INCIDENTE_TAXONOMIA
        query_delete_taxonomias = "DELETE FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?"
        cursor.execute(query_delete_taxonomias, incidente_id)
        conn.commit()

        # Eliminar comentarios asociados de COMENTARIOS_TAXONOMIA
        query_delete_comentarios = "DELETE FROM COMENTARIOS_TAXONOMIA WHERE IncidenteID = ?"
        cursor.execute(query_delete_comentarios, incidente_id)
        conn.commit()

        # Eliminar el incidente principal
        query_delete_incidente = "DELETE FROM Incidentes WHERE IncidenteID = ?"
        cursor.execute(query_delete_incidente, incidente_id)
        conn.commit()

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"error": "Incidente no encontrado"}), 404

        conn.close()
        return jsonify({"message": "Incidente eliminado exitosamente"}), 200

    except Exception as e:
        print(f"Error al eliminar incidente: {e}")
        return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500

@incidente_bp.route('/', methods=['GET'])
# @login_required
def get_all_incidentes():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                IncidenteID, Titulo, DescripcionInicial, Criticidad, EstadoActual, FechaCreacion, FechaActualizacion,
                EmpresaID, CreadoPor, FechaDeteccion, FechaOcurrencia, TipoFlujo, OrigenIncidente,
                SistemasAfectados, AccionesInmediatas, ResponsableCliente,
                FechaCierre, IDVisible, ReporteAnciID, FechaDeclaracionANCI,
                AlcanceGeografico, ServiciosInterrumpidos, AnciImpactoPreliminar, AnciTipoAmenaza,
                CausaRaiz, LeccionesAprendidas, PlanMejora
            FROM Incidentes
            ORDER BY FechaCreacion DESC
        """
        cursor.execute(query)
        incidentes = []
        for row in cursor.fetchall():
            incidente_dict = dict(zip([column[0] for column in cursor.description], row))
            # Convertir fechas a formato ISO si existen
            if incidente_dict.get('FechaCreacion'):
                incidente_dict['FechaCreacion'] = incidente_dict['FechaCreacion'].isoformat()
            if incidente_dict.get('FechaActualizacion'):
                incidente_dict['FechaActualizacion'] = incidente_dict['FechaActualizacion'].isoformat()
            if incidente_dict.get('FechaOcurrencia'):
                incidente_dict['FechaOcurrencia'] = incidente_dict['FechaOcurrencia'].isoformat()
            if incidente_dict.get('FechaCierre'):
                incidente_dict['FechaCierre'] = incidente_dict['FechaCierre'].isoformat()
            incidentes.append(incidente_dict)
        
        conn.close()
        return jsonify(incidentes), 200

    except Exception as e:
        print(f"Error al obtener todos los incidentes: {e}")
        return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500

@incidente_bp.route('/<int:incidente_id>/generar-documento-anci', methods=['POST', 'OPTIONS'])
def generar_documento_anci(incidente_id):
    """
    Genera un documento ANCI para un incidente específico
    """
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
        
    try:
        data = request.get_json() or {}
        tipo_reporte = data.get('tipo_reporte', 'preliminar')
        formato = data.get('formato', 'word')  # Cambiar default a word
        
        # Importar el nuevo generador
        try:
            from ..modules.incidentes.generador_informes_anci_v2 import GeneradorInformesANCIv2
        except ImportError as e:
            print(f"Error importando GeneradorInformesANCIv2: {e}")
            return jsonify({"error": "Error importando generador de informes", "details": str(e)}), 500
        
        # Validar tipo de reporte
        tipos_validos = ['preliminar', 'actualizacion', 'plan_accion', 'final']
        if tipo_reporte not in tipos_validos:
            tipo_reporte = 'preliminar'
        
        # Crear generador
        generador = GeneradorInformesANCIv2()
        
        if formato == 'json':
            # Generar formato JSON estructurado
            datos_json = generador.generar_informe_json(incidente_id, tipo_reporte)
            
            # Agregar metadatos para la carga en ANCI
            datos_json['metadata'] = {
                'version': '1.0',
                'fecha_generacion': datetime.now().isoformat(),
                'sistema_origen': 'AgenteDigital',
                'formato_anci': True
            }
            
            response = jsonify(datos_json)
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
        elif formato == 'word':
            # Generar documento Word
            try:
                output = generador.generar_documento_word(incidente_id, tipo_reporte)
            except Exception as word_error:
                print(f"Error generando documento Word: {word_error}")
                # Fallback a JSON si falla Word
                datos_json = generador.generar_informe_json(incidente_id, tipo_reporte)
                response = jsonify({
                    "error": "No se pudo generar Word, devolviendo JSON",
                    "datos": datos_json
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
            
            filename = f"ANCI_{tipo_reporte}_{incidente_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                as_attachment=True,
                download_name=filename
            )
            
        elif formato == 'txt':
            # Generar formato texto plano (retrocompatibilidad)
            datos_json = generador.generar_informe_json(incidente_id, tipo_reporte)
            
            # Convertir JSON a texto plano estructurado
            contenido = _json_a_texto_plano(datos_json, tipo_reporte)
            
            output = io.BytesIO()
            output.write(contenido.encode('utf-8'))
            output.seek(0)
            
            filename = f"ANCI_{tipo_reporte}_{incidente_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            return send_file(
                output,
                mimetype='text/plain',
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({"error": "Formato no soportado. Use: json, word o txt"}), 400
            
    except Exception as e:
        print(f"Error generando documento ANCI: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500

@incidente_bp.route('/<int:incidente_id>/archivos-semilla', methods=['GET', 'POST', 'OPTIONS'])
def gestionar_archivos_semilla(incidente_id):
    """
    Gestiona archivos semilla (plantillas) para incidentes ANCI
    GET: Lista archivos semilla disponibles
    POST: Sube un nuevo archivo semilla
    """
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    if request.method == 'GET':
        try:
            conn = get_db_connection()
            if not conn:
                return jsonify({"error": "Error de conexión a la base de datos"}), 500
            
            cursor = conn.cursor()
            
            # Obtener archivos semilla asociados al incidente
            query = """
                SELECT 
                    ArchivoID, SeccionID, NombreArchivo, TipoArchivo,
                    Descripcion, FechaSubida, SubidoPor, EsSemilla
                FROM INCIDENTES_ARCHIVOS
                WHERE IncidenteID = ? AND EsSemilla = 1
                ORDER BY SeccionID, FechaSubida DESC
            """
            cursor.execute(query, incidente_id)
            
            archivos_semilla = []
            for row in cursor.fetchall():
                archivo = dict(zip([column[0] for column in cursor.description], row))
                if archivo.get('FechaSubida'):
                    archivo['FechaSubida'] = archivo['FechaSubida'].isoformat()
                archivos_semilla.append(archivo)
            
            conn.close()
            
            response = jsonify({
                "success": True,
                "archivos_semilla": archivos_semilla,
                "total": len(archivos_semilla)
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
        except Exception as e:
            print(f"Error obteniendo archivos semilla: {e}")
            return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500
    
    elif request.method == 'POST':
        try:
            # Validar que hay archivos en la solicitud
            if 'archivo' not in request.files:
                return jsonify({"error": "No se encontró archivo en la solicitud"}), 400
            
            archivo = request.files['archivo']
            if archivo.filename == '':
                return jsonify({"error": "No se seleccionó ningún archivo"}), 400
            
            # Validar tipo de archivo permitido para semillas
            ALLOWED_SEED_EXTENSIONS = {'docx', 'xlsx', 'pdf', 'json', 'txt'}
            if '.' not in archivo.filename or \
               archivo.filename.rsplit('.', 1)[1].lower() not in ALLOWED_SEED_EXTENSIONS:
                return jsonify({"error": "Tipo de archivo no permitido para semilla"}), 400
            
            # Datos adicionales
            seccion_id = request.form.get('seccion_id', 1)
            descripcion = request.form.get('descripcion', 'Archivo semilla ANCI')
            subido_por = request.form.get('subido_por', 'Sistema')
            
            # Guardar archivo físicamente
            filename = secure_filename(archivo.filename)
            unique_filename = f"SEMILLA_{uuid.uuid4()}_{filename}"
            
            # Crear carpeta de semillas si no existe
            carpeta_semillas = os.path.join(UPLOAD_FOLDER, 'semillas', f'incidente_{incidente_id}')
            os.makedirs(carpeta_semillas, exist_ok=True)
            
            filepath = os.path.join(carpeta_semillas, unique_filename)
            archivo.save(filepath)
            
            # Guardar en base de datos
            conn = get_db_connection()
            if not conn:
                # Si falla la BD, eliminar el archivo guardado
                os.remove(filepath)
                return jsonify({"error": "Error de conexión a la base de datos"}), 500
            
            cursor = conn.cursor()
            
            # Insertar registro
            query = """
                INSERT INTO INCIDENTES_ARCHIVOS 
                (IncidenteID, SeccionID, NombreArchivo, TipoArchivo, 
                 RutaArchivo, Descripcion, FechaSubida, SubidoPor, EsSemilla)
                VALUES (?, ?, ?, ?, ?, ?, GETDATE(), ?, 1)
            """
            
            cursor.execute(query, 
                incidente_id, seccion_id, filename, archivo.mimetype,
                filepath, descripcion, subido_por
            )
            conn.commit()
            
            # Obtener ID del archivo insertado
            cursor.execute("SELECT @@IDENTITY AS ArchivoID")
            result = cursor.fetchone()
            archivo_id = result.ArchivoID if result else None
            
            conn.close()
            
            response = jsonify({
                "success": True,
                "message": "Archivo semilla subido exitosamente",
                "archivo_id": archivo_id,
                "nombre_archivo": filename
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 201
            
        except Exception as e:
            print(f"Error subiendo archivo semilla: {e}")
            # Intentar eliminar el archivo si se guardó
            if 'filepath' in locals() and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
            return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500

@incidente_bp.route('/<int:incidente_id>/descargar-semilla/<int:archivo_id>', methods=['GET', 'OPTIONS'])
def descargar_archivo_semilla(incidente_id, archivo_id):
    """
    Descarga un archivo semilla específico
    """
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
        
        cursor = conn.cursor()
        
        # Verificar que el archivo existe y pertenece al incidente
        query = """
            SELECT NombreArchivo, RutaArchivo, TipoArchivo
            FROM INCIDENTES_ARCHIVOS
            WHERE ArchivoID = ? AND IncidenteID = ? AND EsSemilla = 1
        """
        cursor.execute(query, archivo_id, incidente_id)
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({"error": "Archivo semilla no encontrado"}), 404
        
        nombre_archivo = result.NombreArchivo
        ruta_archivo = result.RutaArchivo
        tipo_archivo = result.TipoArchivo
        
        conn.close()
        
        # Verificar que el archivo físico existe
        if not os.path.exists(ruta_archivo):
            return jsonify({"error": "Archivo físico no encontrado"}), 404
        
        # Enviar archivo
        return send_file(
            ruta_archivo,
            mimetype=tipo_archivo,
            as_attachment=True,
            download_name=nombre_archivo
        )
        
    except Exception as e:
        print(f"Error descargando archivo semilla: {e}")
        return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500

@incidente_bp.route('/<int:incidente_id>/plantillas-anci', methods=['GET', 'OPTIONS'])
def obtener_plantillas_anci(incidente_id):
    """
    Obtiene plantillas ANCI predefinidas según el tipo de incidente
    """
    # Manejar OPTIONS para CORS
    if request.method == 'OPTIONS':
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    try:
        # Plantillas predefinidas según tipo de reporte ANCI
        plantillas = [
            {
                "id": 1,
                "nombre": "Alerta Temprana (3 horas)",
                "tipo": "alerta_temprana",
                "descripcion": "Reporte inicial dentro de las primeras 3 horas",
                "campos_requeridos": [
                    "identificacion_entidad", "datos_contacto", 
                    "datos_incidente", "impacto_inicial", 
                    "estado_actual", "acciones_inmediatas"
                ],
                "tiempo_limite": "3 horas"
            },
            {
                "id": 2,
                "nombre": "Segundo Reporte (24-72 horas)",
                "tipo": "segundo_reporte",
                "descripcion": "Actualización con análisis detallado",
                "campos_requeridos": [
                    "analisis_detallado", "gravedad_impacto",
                    "indicadores_compromiso", "analisis_causa_raiz",
                    "acciones_respuesta", "coordinaciones_externas"
                ],
                "tiempo_limite": "24-72 horas según tipo de entidad"
            },
            {
                "id": 3,
                "nombre": "Plan de Acción OIV (7 días)",
                "tipo": "plan_accion",
                "descripcion": "Solo para Operadores de Importancia Vital",
                "campos_requeridos": [
                    "plan_recuperacion", "medidas_mitigacion",
                    "impacto_servicios_vitales"
                ],
                "tiempo_limite": "7 días",
                "solo_oiv": True
            },
            {
                "id": 4,
                "nombre": "Informe Final (15 días)",
                "tipo": "informe_final",
                "descripcion": "Informe completo con lecciones aprendidas",
                "campos_requeridos": [
                    "descripcion_completa", "causa_raiz_final",
                    "impacto_final_detallado", "medidas_contencion_recuperacion",
                    "lecciones_aprendidas", "plan_mejora_continua"
                ],
                "tiempo_limite": "15 días"
            }
        ]
        
        # Obtener información del incidente para determinar tipo de entidad
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            query = """
                SELECT e.TipoEmpresa
                FROM Incidentes i
                INNER JOIN Empresas e ON i.EmpresaID = e.EmpresaID
                WHERE i.IncidenteID = ?
            """
            cursor.execute(query, incidente_id)
            result = cursor.fetchone()
            
            tipo_empresa = result.TipoEmpresa if result else 'PSE'
            conn.close()
            
            # Filtrar plantillas según tipo de empresa
            if tipo_empresa != 'OIV':
                plantillas = [p for p in plantillas if not p.get('solo_oiv', False)]
        
        response = jsonify({
            "success": True,
            "plantillas": plantillas,
            "tipo_empresa": tipo_empresa if 'tipo_empresa' in locals() else 'Desconocido'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        print(f"Error obteniendo plantillas ANCI: {e}")
        return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500

# Función auxiliar para convertir JSON a texto plano
def _json_a_texto_plano(datos_json: dict, tipo_reporte: str) -> str:
    """
    Convierte estructura JSON de ANCI a formato texto plano
    """
    lineas = []
    
    # Encabezado
    lineas.append("="*80)
    lineas.append(f"REPORTE ANCI - {tipo_reporte.upper()}")
    lineas.append("="*80)
    lineas.append("")
    
    # Función recursiva para procesar el JSON
    def procesar_dict(d, nivel=0, prefijo=""):
        indent = "  " * nivel
        for clave, valor in d.items():
            titulo = clave.replace('_', ' ').upper()
            
            if isinstance(valor, dict):
                lineas.append(f"{indent}{titulo}:")
                procesar_dict(valor, nivel + 1)
                lineas.append("")
            elif isinstance(valor, list):
                lineas.append(f"{indent}{titulo}:")
                for i, item in enumerate(valor):
                    if isinstance(item, dict):
                        lineas.append(f"{indent}  [{i+1}]")
                        procesar_dict(item, nivel + 2)
                    else:
                        lineas.append(f"{indent}  - {item}")
                lineas.append("")
            else:
                lineas.append(f"{indent}{titulo}: {valor or 'N/A'}")
    
    # Procesar el JSON
    procesar_dict(datos_json)
    
    # Pie de página
    lineas.append("")
    lineas.append("="*80)
    lineas.append(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lineas.append("Sistema: AgenteDigital")
    lineas.append("="*80)
    
    return '\n'.join(lineas)
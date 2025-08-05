# modules/admin/incidentes_admin_endpoints.py
# Endpoints administrativos para incidentes con autenticación JWT

from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from app.database import get_db_connection
from app.auth_utils import token_required
from app.utils.encoding_fixer import EncodingFixer
import logging

logger = logging.getLogger(__name__)

incidentes_admin_bp = Blueprint('incidentes_admin', __name__)

@incidentes_admin_bp.route('/api/admin/incidentes/<int:incidente_id>', methods=['GET'])
@cross_origin()
@token_required
def obtener_incidente_admin(current_user_id, current_user_rol, current_user_email, current_user_nombre, incidente_id):
    """
    Obtiene detalles completos de un incidente específico con autenticación
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Consulta completa del incidente con todos los campos necesarios
        query = """
        SELECT 
            i.IncidenteID,
            i.EmpresaID,
            i.InquilinoID,
            i.TipoRegistro,
            i.TipoFlujo,
            i.Titulo,
            i.FechaDeteccion,
            i.FechaOcurrencia,
            i.Criticidad,
            i.OrigenIncidente,
            i.SolicitarCSIRT,
            i.TipoApoyoCSIRT,
            i.UrgenciaCSIRT,
            i.ObservacionesCSIRT,
            i.DescripcionInicial as DescripcionBreve,
            i.SistemasAfectados,
            i.UsuariosAfectados,
            i.TiempoIncidencia,
            i.ImpactoPreliminar,
            i.AlcanceGeografico,
            i.AnciImpactoPreliminar,
            i.AnciTipoAmenaza,
            i.AnciAgenteAmenaza,
            i.AnciVulnerabilidadExplotada,
            i.AnciDatosComprometidos,
            i.AnciAfectacionTerceros,
            i.AccionesInmediatas,
            i.ResponsableCliente,
            i.NivelEscalamiento,
            i.MedidasContencion,
            i.PlanComunicacion,
            i.NotificacionesRealizadas,
            i.CausaRaiz,
            i.SolucionImplementada,
            i.MedidasPreventivas,
            i.ProximosPasos,
            i.LeccionesAprendidas,
            i.DocumentacionAdjunta,
            i.FechaResolucion,
            i.EstadoFinal,
            i.PersonaCierre,
            i.AprobacionCierre,
            i.ObservacionesFinales,
            i.RequiereAcciones,
            i.EstadoActual,
            i.IDVisible,
            i.FechaCreacion,
            i.FechaActualizacion,
            i.CreadoPor,
            i.ModificadoPor,
            i.VersionControl,
            i.TieneReporteANCI,
            e.Nombre as EmpresaNombre,
            inq.RazonSocial as InquilinoNombre
        FROM Incidentes i
        LEFT JOIN Empresas e ON i.EmpresaID = e.EmpresaID
        LEFT JOIN Inquilinos inq ON i.InquilinoID = inq.InquilinoID
        WHERE i.IncidenteID = ?
        """
        
        cursor.execute(query, (incidente_id,))
        result = cursor.fetchone()
        
        if not result:
            logger.warning(f"Incidente {incidente_id} no encontrado")
            return jsonify({"error": "Incidente no encontrado"}), 404
        
        # Convertir resultado a diccionario
        columns = [column[0] for column in cursor.description]
        incidente = dict(zip(columns, result))
        
        # Convertir fechas a formato ISO si existen
        date_fields = ['FechaDeteccion', 'FechaOcurrencia', 'FechaResolucion', 'FechaCreacion', 'FechaActualizacion']
        for field in date_fields:
            if incidente.get(field):
                incidente[field] = incidente[field].isoformat()
        
        # Obtener archivos adjuntos si existen
        try:
            cursor.execute("""
                SELECT 
                    ArchivoID,
                    NombreOriginal,
                    TipoArchivo,
                    TamanoKB,
                    SeccionID,
                    FechaSubida,
                    SubidoPor,
                    Descripcion,
                    NumeroArchivo
                FROM INCIDENTES_ARCHIVOS
                WHERE IncidenteID = ? AND Activo = 1
                ORDER BY SeccionID, FechaSubida
            """, (incidente_id,))
            
            archivos_rows = cursor.fetchall()
            
            # Organizar archivos por sección en el formato esperado por el frontend
            archivos_por_seccion = {
                'seccion_2': [],
                'seccion_3': [],
                'seccion_5': [],
                'seccion_6': [],
                'taxonomias': {}
            }
            
            for row in archivos_rows:
                archivo_data = {
                    'id': row[0],
                    'nombre': row[1],
                    'tipo': row[2],
                    'tamaño': row[3] * 1024 if row[3] else 0,  # Convertir KB a bytes
                    'fechaCarga': row[5].isoformat() if row[5] else None,
                    'subidoPor': row[6],
                    'descripcion': row[7] or '',  # Usar descripción de BD
                    'comentario': f'Archivo #{row[8]}' if row[8] else '',   # Usar numero archivo
                    'existente': True,  # Marcar como archivo existente
                    'origen': 'guardado'
                }
                
                seccion_id = row[4]
                
                # Mapear SeccionID a las claves esperadas por el frontend
                if seccion_id == 2:
                    archivos_por_seccion['seccion_2'].append(archivo_data)
                elif seccion_id == 3:
                    archivos_por_seccion['seccion_3'].append(archivo_data)
                elif seccion_id == 5:
                    archivos_por_seccion['seccion_5'].append(archivo_data)
                elif seccion_id == 6:
                    archivos_por_seccion['seccion_6'].append(archivo_data)
                elif seccion_id == 4:  # Sección 4 es para taxonomías
                    # TODO: Manejar archivos de taxonomías si es necesario
                    pass
            
            incidente['archivos'] = archivos_por_seccion
            
        except Exception as e:
            logger.warning(f"Error obteniendo archivos: {e}")
            incidente['archivos'] = {}
        
        # Obtener taxonomías seleccionadas
        try:
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
            """, (incidente_id,))
            
            taxonomias_rows = cursor.fetchall()
            taxonomias_seleccionadas = []
            
            for row in taxonomias_rows:
                tax_data = {
                    'id': row[0],
                    'nombre': row[1],
                    'area': row[2],
                    'efecto': row[3],
                    'categoria': row[4],
                    'subcategoria': row[5],
                    'tipo': row[6],
                    'descripcion': row[7],
                    'justificacion': row[8] or '',
                    'descripcionProblema': row[9] or '',
                    'fechaSeleccion': row[10].isoformat() if row[10] else None,
                    'archivos': []  # Se llenarán después si hay
                }
                # Corregir encoding de los datos de taxonomía
                tax_data = EncodingFixer.fix_dict(tax_data)
                taxonomias_seleccionadas.append(tax_data)
            
            incidente['taxonomias_seleccionadas'] = taxonomias_seleccionadas
            
        except Exception as e:
            logger.warning(f"Error obteniendo taxonomías: {e}")
            incidente['taxonomias_seleccionadas'] = []
        
        # Mapear campos del incidente al formato del formulario
        form_data = {
            '1.1': incidente.get('TipoRegistro', ''),
            '1.2': incidente.get('Titulo', ''),
            '1.3': incidente.get('FechaDeteccion', ''),
            '1.4': incidente.get('FechaOcurrencia', ''),
            '1.5': incidente.get('Criticidad', ''),
            '1.6': incidente.get('OrigenIncidente', ''),
            '1.7.solicitar_csirt': incidente.get('SolicitarCSIRT', False),
            '1.7.tipo_apoyo': incidente.get('TipoApoyoCSIRT', ''),
            '1.7.urgencia': incidente.get('UrgenciaCSIRT', ''),
            '1.7.observaciones_csirt': incidente.get('ObservacionesCSIRT', ''),
            '2.1': incidente.get('DescripcionBreve', ''),
            '2.2': incidente.get('SistemasAfectados', ''),
            '2.3': incidente.get('UsuariosAfectados', ''),
            '2.4': incidente.get('TiempoIncidencia', ''),
            '2.5': incidente.get('ImpactoPreliminar', ''),
            '2.6': incidente.get('AlcanceGeografico', ''),
            '3.1': incidente.get('AnciImpactoPreliminar', ''),
            '3.2': incidente.get('AnciTipoAmenaza', ''),
            '3.3': incidente.get('AnciAgenteAmenaza', ''),
            '3.4': incidente.get('AnciVulnerabilidadExplotada', ''),
            '3.5': incidente.get('AnciDatosComprometidos', ''),
            '3.6': incidente.get('AnciAfectacionTerceros', ''),
            '4.1': incidente.get('AccionesInmediatas', ''),
            '4.2': incidente.get('ResponsableCliente', ''),
            '4.3': incidente.get('NivelEscalamiento', ''),
            '4.4': incidente.get('MedidasContencion', ''),
            '4.5': incidente.get('PlanComunicacion', ''),
            '4.6': incidente.get('NotificacionesRealizadas', ''),
            '5.1': incidente.get('CausaRaiz', ''),
            '5.2': incidente.get('SolucionImplementada', ''),
            '5.3': incidente.get('MedidasPreventivas', ''),
            '5.4': incidente.get('ProximosPasos', ''),
            '5.5': incidente.get('LeccionesAprendidas', ''),
            '5.6': incidente.get('DocumentacionAdjunta', ''),
            '6.1': incidente.get('FechaResolucion', ''),
            '6.2': incidente.get('EstadoFinal', ''),
            '6.3': incidente.get('PersonaCierre', ''),
            '6.4': incidente.get('AprobacionCierre', ''),
            '6.5': incidente.get('ObservacionesFinales', ''),
            '6.6': incidente.get('RequiereAcciones', False)
        }
        
        incidente['formData'] = form_data
        
        logger.info(f"Incidente {incidente_id} cargado exitosamente para usuario {current_user_email}")
        return jsonify(incidente), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo incidente {incidente_id}: {str(e)}")
        return jsonify({"error": "Error al obtener el incidente"}), 500
    finally:
        if conn:
            conn.close()

@incidentes_admin_bp.route('/api/admin/incidentes/<int:incidente_id>/validar-para-anci', methods=['GET'])
@cross_origin()
@token_required
def validar_incidente_para_anci(current_user_id, current_user_rol, current_user_email, current_user_nombre, incidente_id):
    """
    Valida si un incidente puede ser transformado a formato ANCI
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar que el incidente existe
        cursor.execute("SELECT TieneReporteANCI FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"error": "Incidente no encontrado"}), 404
        
        tiene_reporte_anci = result[0]
        
        if tiene_reporte_anci:
            return jsonify({
                "valido": False,
                "mensaje": "Este incidente ya fue transformado a formato ANCI"
            }), 200
        
        # Verificar campos requeridos para ANCI
        cursor.execute("""
            SELECT 
                Titulo,
                FechaDeteccion,
                FechaOcurrencia,
                Criticidad,
                OrigenIncidente,
                DescripcionInicial,
                AnciImpactoPreliminar,
                AccionesInmediatas
            FROM Incidentes
            WHERE IncidenteID = ?
        """, (incidente_id,))
        
        campos = cursor.fetchone()
        
        if not campos:
            return jsonify({
                "valido": False,
                "mensaje": "No se pudieron obtener los datos del incidente"
            }), 200
        
        # Verificar campos obligatorios
        campos_faltantes = []
        nombres_campos = [
            'Título', 'Fecha de Detección', 'Fecha de Ocurrencia', 
            'Criticidad', 'Origen del Incidente', 'Descripción Inicial',
            'Impacto Preliminar ANCI', 'Acciones Inmediatas'
        ]
        
        for i, campo in enumerate(campos):
            if not campo or (isinstance(campo, str) and campo.strip() == ''):
                campos_faltantes.append(nombres_campos[i])
        
        if campos_faltantes:
            return jsonify({
                "valido": False,
                "mensaje": f"Faltan completar los siguientes campos: {', '.join(campos_faltantes)}"
            }), 200
        
        return jsonify({
            "valido": True,
            "mensaje": "El incidente está listo para ser transformado a formato ANCI"
        }), 200
        
    except Exception as e:
        logger.error(f"Error validando incidente para ANCI: {str(e)}")
        return jsonify({"error": "Error al validar el incidente"}), 500
    finally:
        if conn:
            conn.close()

@incidentes_admin_bp.route('/api/admin/incidentes/<int:incidente_id>/transformar-anci', methods=['POST'])
@cross_origin()
@token_required
def transformar_incidente_anci(current_user_id, current_user_rol, current_user_email, current_user_nombre, incidente_id):
    """
    Transforma un incidente a formato ANCI
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Marcar el incidente como transformado a ANCI
        cursor.execute("""
            UPDATE Incidentes 
            SET TieneReporteANCI = 1,
                FechaActualizacion = GETDATE(),
                ModificadoPor = ?
            WHERE IncidenteID = ?
        """, (current_user_id, incidente_id))
        
        # Registrar en auditoría
        cursor.execute("""
            INSERT INTO INCIDENTES_AUDITORIA 
            (IncidenteID, TipoAccion, DescripcionAccion, Usuario, FechaAccion)
            VALUES (?, 'TRANSFORMAR_ANCI', 'Incidente transformado a formato ANCI', ?, GETDATE())
        """, (incidente_id, current_user_email))
        
        conn.commit()
        
        logger.info(f"Incidente {incidente_id} transformado a ANCI por {current_user_email}")
        
        return jsonify({
            "success": True,
            "mensaje": "Incidente transformado exitosamente a formato ANCI"
        }), 200
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error transformando incidente a ANCI: {str(e)}")
        return jsonify({"error": "Error al transformar el incidente"}), 500
    finally:
        if conn:
            conn.close()
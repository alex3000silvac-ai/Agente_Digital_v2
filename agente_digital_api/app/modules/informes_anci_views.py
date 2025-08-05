"""
Módulo de vistas para gestión de informes ANCI
Maneja la generación, consulta y descarga de informes ANCI
"""

import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, send_file, make_response
from flask_cors import cross_origin
import logging
from app.database import get_db_connection
from config import Config
UPLOAD_FOLDER = Config.UPLOAD_FOLDER
from app.modules.informes_anci_simple import InformesANCI

# Configurar logging
logger = logging.getLogger(__name__)

# Crear blueprint
informes_anci_bp = Blueprint('informes_anci', __name__)

@informes_anci_bp.route('/api/informes-anci/historial/<int:incidente_id>', methods=['GET'])
@cross_origin()
def obtener_historial_informes(incidente_id):
    """
    Obtiene el historial de informes ANCI generados para un incidente
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Primero verificar si la tabla existe
        cursor.execute("""
            IF EXISTS (SELECT * FROM sys.tables WHERE name = 'INFORMES_ANCI')
                SELECT 1 as tabla_existe
            ELSE
                SELECT 0 as tabla_existe
        """)
        
        existe = cursor.fetchone()[0]
        
        if not existe:
            logger.warning("La tabla INFORMES_ANCI no existe aún")
            return jsonify({'informes': []}), 200  # Retornar lista vacía si no existe la tabla
        
        # Consultar historial de informes
        query = """
        SELECT 
            ia.InformeID,
            ia.TipoInforme,
            ia.EstadoInforme,
            ia.FechaGeneracion,
            ia.RutaArchivo,
            ia.TamanoKB,
            ia.GeneradoPor,
            ia.Version
        FROM INFORMES_ANCI ia
        WHERE ia.IncidenteID = ? AND ia.Activo = 1
        ORDER BY ia.FechaGeneracion DESC
        """
        
        cursor.execute(query, (incidente_id,))
        columns = [column[0] for column in cursor.description]
        informes = []
        
        for row in cursor.fetchall():
            informe = dict(zip(columns, row))
            
            # Convertir fechas
            if informe['FechaGeneracion']:
                informe['FechaGeneracion'] = informe['FechaGeneracion'].isoformat()
            
            # Verificar si el archivo existe
            if informe['RutaArchivo']:
                informe['ArchivoDisponible'] = os.path.exists(informe['RutaArchivo'])
            else:
                informe['ArchivoDisponible'] = False
                
            informes.append(informe)
        
        logger.info(f"Se encontraron {len(informes)} informes para el incidente {incidente_id}")
        
        # Mapear campos para el frontend
        informes_formateados = []
        for informe in informes:
            informes_formateados.append({
                'id': informe['InformeID'],
                'nombre_archivo': f"Informe_{informe['TipoInforme'].upper()}_{informe['InformeID']}.pdf",
                'tipo_informe': informe['TipoInforme'].capitalize(),
                'fecha_generacion': informe['FechaGeneracion'],
                'tamano': informe['TamanoKB'],
                'generado_por': informe['GeneradoPor'],
                'version': informe['Version'],
                'disponible': informe['ArchivoDisponible']
            })
        
        return jsonify({'informes': informes_formateados}), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo historial de informes: {str(e)}")
        # Si hay error, retornar lista vacía en lugar de error 500
        return jsonify({'informes': []}), 200
    finally:
        if conn:
            conn.close()

@informes_anci_bp.route('/api/informes-anci/generar/<int:incidente_id>', methods=['POST'])
@cross_origin()
def generar_informe_anci(incidente_id):
    """
    Genera un informe ANCI para un incidente
    """
    try:
        data = request.get_json()
        tipo_informe = data.get('tipo_informe', data.get('tipo', 'preliminar'))
        usuario_id = data.get('usuario_id', 'sistema')
        
        logger.info(f"Generando informe {tipo_informe} para incidente {incidente_id}")
        
        # Crear instancia del generador
        generador = InformesANCI()
        
        # Generar el informe
        resultado = generador.generar_informe(
            incidente_id=incidente_id,
            tipo_informe=tipo_informe,
            usuario_id=usuario_id
        )
        
        if resultado['exito']:
            logger.info(f"Informe generado exitosamente: {resultado['ruta_archivo']}")
            return jsonify({
                "exito": True,
                "mensaje": "Informe generado exitosamente",
                "informe_id": resultado['informe_id'],
                "ruta_archivo": resultado['ruta_archivo'],
                "contenido": resultado.get('contenido', ''),
                "datos_incidente": resultado.get('datos_incidente', {})
            }), 200
        else:
            logger.error(f"Error generando informe: {resultado['error']}")
            return jsonify({
                "exito": False,
                "error": resultado['error']
            }), 400
            
    except Exception as e:
        logger.error(f"Error generando informe ANCI: {str(e)}")
        return jsonify({"error": "Error al generar informe ANCI"}), 500

@informes_anci_bp.route('/api/informes-anci/descargar/<int:informe_id>', methods=['GET'])
@cross_origin()
def descargar_informe_anci(informe_id):
    """
    Descarga un informe ANCI específico
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener información del informe
        query = """
        SELECT 
            ia.RutaArchivo,
            ia.TipoInforme,
            i.IDVisible,
            ia.FechaGeneracion
        FROM INFORMES_ANCI ia
        INNER JOIN Incidentes i ON ia.IncidenteID = i.IncidenteID
        WHERE ia.InformeID = ? AND ia.Activo = 1
        """
        
        cursor.execute(query, (informe_id,))
        resultado = cursor.fetchone()
        
        if not resultado:
            return jsonify({"error": "Informe no encontrado"}), 404
            
        ruta_archivo, tipo_informe, id_visible, fecha_generacion = resultado
        
        # Verificar que el archivo existe
        if not os.path.exists(ruta_archivo):
            logger.error(f"Archivo no encontrado: {ruta_archivo}")
            return jsonify({"error": "Archivo no encontrado en el servidor"}), 404
        
        # Determinar tipo de archivo y nombre
        fecha_str = fecha_generacion.strftime('%Y%m%d_%H%M%S')
        
        # Detectar extensión del archivo
        extension = os.path.splitext(ruta_archivo)[1].lower()
        if extension == '.txt':
            mimetype = 'text/plain; charset=utf-8'
            nombre_archivo = f"Informe_ANCI_{tipo_informe}_{id_visible}_{fecha_str}.txt"
        else:
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            nombre_archivo = f"Informe_ANCI_{tipo_informe}_{id_visible}_{fecha_str}.docx"
        
        # Enviar archivo
        return send_file(
            ruta_archivo,
            as_attachment=True,
            download_name=nombre_archivo,
            mimetype=mimetype
        )
        
    except Exception as e:
        logger.error(f"Error descargando informe: {str(e)}")
        return jsonify({"error": "Error al descargar informe"}), 500
    finally:
        if conn:
            conn.close()

@informes_anci_bp.route('/api/informes-anci/cuenta-regresiva', methods=['GET'])
@cross_origin()
def obtener_cuenta_regresiva():
    """
    Obtiene información de cuenta regresiva para informes ANCI pendientes
    """
    try:
        inquilino_id = request.args.get('inquilino_id', type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Primero verificar si la tabla INFORMES_ANCI existe
        cursor.execute("""
            IF EXISTS (SELECT * FROM sys.tables WHERE name = 'INFORMES_ANCI')
                SELECT 1 as tabla_existe
            ELSE
                SELECT 0 as tabla_existe
        """)
        
        tabla_existe = cursor.fetchone()[0]
        
        # Query para obtener incidentes
        if tabla_existe:
            # Query completa con verificación de informes existentes
            query = """
            SELECT 
                i.IncidenteID,
                i.IDVisible,
                i.Titulo,
                i.FechaDeteccion,
                i.EmpresaID,
                e.Nombre as NombreEmpresa,
                -- Verificar si existe informe preliminar
                (SELECT COUNT(*) FROM INFORMES_ANCI 
                 WHERE IncidenteID = i.IncidenteID 
                 AND TipoInforme = 'preliminar' 
                 AND Activo = 1) as TienePreliminar,
                -- Verificar si existe informe completo
                (SELECT COUNT(*) FROM INFORMES_ANCI 
                 WHERE IncidenteID = i.IncidenteID 
                 AND TipoInforme = 'completo' 
                 AND Activo = 1) as TieneCompleto,
                -- Verificar si existe informe final
                (SELECT COUNT(*) FROM INFORMES_ANCI 
                 WHERE IncidenteID = i.IncidenteID 
                 AND TipoInforme = 'final' 
                 AND Activo = 1) as TieneFinal
            FROM Incidentes i
            INNER JOIN Empresas e ON i.EmpresaID = e.ID
            WHERE i.Activo = 1
            """
        else:
            # Query simplificada sin verificación de informes
            query = """
            SELECT 
                i.IncidenteID,
                i.IDVisible,
                i.Titulo,
                i.FechaDeteccion,
                i.EmpresaID,
                e.Nombre as NombreEmpresa,
                0 as TienePreliminar,
                0 as TieneCompleto,
                0 as TieneFinal
            FROM Incidentes i
            INNER JOIN Empresas e ON i.EmpresaID = e.ID
            WHERE i.Activo = 1
            """
        
        params = []
        
        # Filtrar por inquilino si se especifica
        if inquilino_id:
            query += " AND e.InquilinoID = ?"
            params.append(inquilino_id)
            
        query += " ORDER BY i.FechaDeteccion DESC"
        
        cursor.execute(query, params)
        columns = [column[0] for column in cursor.description]
        incidentes = []
        
        ahora = datetime.now()
        
        for row in cursor.fetchall():
            incidente = dict(zip(columns, row))
            
            # Convertir fecha
            fecha_deteccion = incidente['FechaDeteccion']
            if isinstance(fecha_deteccion, str):
                fecha_deteccion = datetime.fromisoformat(fecha_deteccion)
            
            # Calcular tiempos límite
            limite_preliminar = fecha_deteccion + timedelta(hours=24)
            limite_completo = fecha_deteccion + timedelta(hours=72)
            limite_final = fecha_deteccion + timedelta(days=30)
            
            # Preparar respuesta
            incidente_info = {
                'id': incidente['IncidenteID'],
                'idVisible': incidente['IDVisible'],
                'titulo': incidente['Titulo'],
                'fechaDeteccion': fecha_deteccion.isoformat(),
                'empresa': incidente['NombreEmpresa'],
                'empresaId': incidente['EmpresaID'],
                'informePreliminar': incidente['TienePreliminar'] > 0,
                'informeCompleto': incidente['TieneCompleto'] > 0,
                'informeFinal': incidente['TieneFinal'] > 0,
                'plazos': {
                    'preliminar': {
                        'limite': limite_preliminar.isoformat(),
                        'vencido': ahora > limite_preliminar and incidente['TienePreliminar'] == 0,
                        'horasRestantes': max(0, (limite_preliminar - ahora).total_seconds() / 3600)
                    },
                    'completo': {
                        'limite': limite_completo.isoformat(),
                        'vencido': ahora > limite_completo and incidente['TieneCompleto'] == 0,
                        'horasRestantes': max(0, (limite_completo - ahora).total_seconds() / 3600)
                    },
                    'final': {
                        'limite': limite_final.isoformat(),
                        'vencido': ahora > limite_final and incidente['TieneFinal'] == 0,
                        'horasRestantes': max(0, (limite_final - ahora).total_seconds() / 3600)
                    }
                }
            }
            
            incidentes.append(incidente_info)
        
        logger.info(f"Se encontraron {len(incidentes)} incidentes para cuenta regresiva")
        return jsonify(incidentes), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo cuenta regresiva: {str(e)}")
        return jsonify({"error": "Error al obtener cuenta regresiva"}), 500
    finally:
        if conn:
            conn.close()

@informes_anci_bp.route('/api/informes-anci/validar/<int:incidente_id>', methods=['GET'])
@cross_origin()
def validar_datos_informe(incidente_id):
    """
    Valida que el incidente tenga todos los datos necesarios para generar un informe
    """
    try:
        generador = InformesANCI()
        validacion = generador.validar_datos_incidente(incidente_id)
        
        return jsonify(validacion), 200
        
    except Exception as e:
        logger.error(f"Error validando datos del incidente: {str(e)}")
        return jsonify({"error": "Error al validar datos del incidente"}), 500
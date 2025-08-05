#!/usr/bin/env python3
"""
Endpoints para generación de informes ANCI
"""

from flask import Blueprint, jsonify, send_file, request
from flask_login import login_required, current_user
from ..modules.incidentes.generador_informes_anci import GeneradorInformesANCI
import os

informes_anci_bp = Blueprint('informes_anci', __name__, url_prefix='/api/informes-anci')

generador = GeneradorInformesANCI()

@informes_anci_bp.route('/generar/<int:incidente_id>', methods=['POST'])
@login_required
def generar_informe_anci(incidente_id):
    """
    Genera un informe ANCI para un incidente
    
    Body JSON:
    {
        "tipo_informe": "completo" | "preliminar" | "final",
        "plantilla": "ruta/opcional/a/plantilla.docx"
    }
    """
    try:
        data = request.get_json() or {}
        tipo_informe = data.get('tipo_informe', 'completo')
        
        # Si se especifica una plantilla custom
        if data.get('plantilla'):
            generador.plantilla_path = data['plantilla']
        
        # Generar informe
        ruta_informe = generador.generar_informe(incidente_id, tipo_informe)
        
        return jsonify({
            'success': True,
            'mensaje': 'Informe generado exitosamente',
            'archivo': os.path.basename(ruta_informe),
            'ruta': ruta_informe,
            'tipo': tipo_informe
        }), 201
        
    except FileNotFoundError as e:
        return jsonify({
            'success': False,
            'error': 'Plantilla ANCI no encontrada',
            'detalles': str(e),
            'sugerencia': 'Verifique que existe el archivo de plantilla ANCI'
        }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@informes_anci_bp.route('/descargar/<int:incidente_id>/<nombre_archivo>', methods=['GET'])
@login_required
def descargar_informe_anci(incidente_id, nombre_archivo):
    """
    Descarga un informe ANCI generado previamente
    """
    try:
        # Construir ruta segura
        base_path = os.environ.get('ARCHIVOS_PATH', '/archivos')
        
        # Obtener empresa del incidente
        from ..database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT EmpresaID, IDVisible FROM Incidentes WHERE IncidenteID = ?
        """, (incidente_id,))
        
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'Incidente no encontrado'}), 404
            
        empresa_id, id_visible = result
        conn.close()
        
        # Construir ruta completa
        ruta_archivo = os.path.join(
            base_path,
            f"empresa_{empresa_id}",
            f"incidente_{id_visible}",
            'informes_anci',
            nombre_archivo
        )
        
        # Verificar que el archivo existe y es un .docx
        if not os.path.exists(ruta_archivo):
            return jsonify({'error': 'Archivo no encontrado'}), 404
            
        if not nombre_archivo.endswith('.docx'):
            return jsonify({'error': 'Tipo de archivo no permitido'}), 403
        
        # Enviar archivo
        return send_file(
            ruta_archivo,
            as_attachment=True,
            download_name=nombre_archivo,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        return jsonify({
            'error': 'Error descargando archivo',
            'detalles': str(e)
        }), 500


@informes_anci_bp.route('/plantillas', methods=['GET'])
@login_required
def listar_plantillas():
    """
    Lista las plantillas ANCI disponibles
    """
    try:
        plantillas = generador.listar_plantillas_disponibles()
        
        return jsonify({
            'success': True,
            'plantillas': plantillas,
            'plantilla_actual': generador.plantilla_path
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@informes_anci_bp.route('/historial/<int:incidente_id>', methods=['GET'])
@login_required
def historial_informes(incidente_id):
    """
    Obtiene el historial de informes generados para un incidente
    """
    try:
        # Obtener datos del incidente
        from ..database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT EmpresaID, IDVisible FROM Incidentes WHERE IncidenteID = ?
        """, (incidente_id,))
        
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'Incidente no encontrado'}), 404
            
        empresa_id, id_visible = result
        
        # Buscar archivos de informes
        base_path = os.environ.get('ARCHIVOS_PATH', '/archivos')
        carpeta_informes = os.path.join(
            base_path,
            f"empresa_{empresa_id}",
            f"incidente_{id_visible}",
            'informes_anci'
        )
        
        informes = []
        if os.path.exists(carpeta_informes):
            for archivo in os.listdir(carpeta_informes):
                if archivo.endswith('.docx'):
                    ruta_completa = os.path.join(carpeta_informes, archivo)
                    informes.append({
                        'nombre': archivo,
                        'tamano': os.path.getsize(ruta_completa),
                        'fecha_creacion': os.path.getctime(ruta_completa),
                        'fecha_modificacion': os.path.getmtime(ruta_completa)
                    })
        
        # Ordenar por fecha de creación descendente
        informes.sort(key=lambda x: x['fecha_creacion'], reverse=True)
        
        return jsonify({
            'success': True,
            'incidente_id': incidente_id,
            'total_informes': len(informes),
            'informes': informes
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if conn:
            conn.close()


@informes_anci_bp.route('/configurar-plantilla', methods=['POST'])
@login_required
def configurar_plantilla():
    """
    Configura la ruta de la plantilla ANCI a usar
    Solo usuarios admin
    """
    try:
        # Verificar permisos admin
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Permisos insuficientes'
            }), 403
        
        data = request.get_json()
        nueva_ruta = data.get('ruta_plantilla')
        
        if not nueva_ruta:
            return jsonify({
                'success': False,
                'error': 'Debe proporcionar la ruta de la plantilla'
            }), 400
        
        # Verificar que existe
        if not os.path.exists(nueva_ruta):
            return jsonify({
                'success': False,
                'error': 'La plantilla especificada no existe'
            }), 404
        
        # Actualizar configuración
        generador.plantilla_path = nueva_ruta
        
        # Aquí podrías guardar la configuración en BD o archivo config
        
        return jsonify({
            'success': True,
            'mensaje': 'Plantilla configurada exitosamente',
            'plantilla_actual': generador.plantilla_path
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
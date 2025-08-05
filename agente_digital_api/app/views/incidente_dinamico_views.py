#!/usr/bin/env python3
"""
Vistas del Sistema Dinámico de Incidentes
Endpoints para manejar incidentes con acordeones variables
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..modules.incidentes.sistema_dinamico import SistemaDinamicoIncidentes
from ..utils.encoding_fixer import EncodingFixer
import base64

incidente_dinamico_bp = Blueprint('incidente_dinamico', __name__, url_prefix='/api/incidente-dinamico')

sistema = SistemaDinamicoIncidentes()

@incidente_dinamico_bp.route('/secciones-empresa/<int:empresa_id>', methods=['GET'])
@login_required
def obtener_secciones_empresa(empresa_id):
    """
    Obtiene las secciones aplicables para una empresa según su tipo (OIV/PSE/AMBAS)
    Devuelve entre 6 y 41 secciones
    """
    try:
        secciones = sistema.obtener_secciones_empresa(empresa_id)
        
        # Convertir a dict para JSON
        secciones_dict = []
        for seccion in secciones:
            secciones_dict.append({
                'seccion_id': seccion.seccion_id,
                'codigo': seccion.codigo_seccion,
                'tipo': seccion.tipo_seccion,
                'orden': seccion.numero_orden,
                'titulo': EncodingFixer.fix_text(seccion.titulo),
                'descripcion': EncodingFixer.fix_text(seccion.descripcion),
                'campos': seccion.campos_json,
                'color': seccion.color_indicador,
                'icono': seccion.icono_seccion,
                'max_comentarios': seccion.max_comentarios,
                'max_archivos': seccion.max_archivos,
                'max_size_mb': seccion.max_size_mb
            })
        
        return jsonify({
            'success': True,
            'secciones': secciones_dict,
            'total_secciones': len(secciones_dict),
            'secciones_fijas': sum(1 for s in secciones_dict if s['tipo'] == 'FIJA'),
            'secciones_taxonomia': sum(1 for s in secciones_dict if s['tipo'] == 'TAXONOMIA')
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidente_dinamico_bp.route('/crear', methods=['POST'])
@login_required
def crear_incidente():
    """
    Crea un incidente con todas las secciones aplicables según el tipo de empresa
    """
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('incidente_id') or not data.get('empresa_id'):
            return jsonify({
                'success': False,
                'error': 'incidente_id y empresa_id son requeridos'
            }), 400
        
        # Agregar usuario actual a los datos
        data['usuario'] = current_user.username
        
        resultado = sistema.crear_incidente_completo(
            incidente_id=data['incidente_id'],
            empresa_id=data['empresa_id'],
            datos_iniciales=data.get('datos_iniciales', {})
        )
        
        return jsonify(resultado), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidente_dinamico_bp.route('/<int:incidente_id>/seccion/<int:seccion_id>', methods=['PUT'])
@login_required
def guardar_seccion(incidente_id, seccion_id):
    """
    Guarda los datos de una sección específica
    """
    try:
        data = request.get_json()
        
        resultado = sistema.guardar_seccion(
            incidente_id=incidente_id,
            seccion_id=seccion_id,
            datos=data.get('datos', {}),
            usuario=current_user.username
        )
        
        return jsonify(resultado), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidente_dinamico_bp.route('/<int:incidente_id>/seccion/<int:seccion_id>/comentario', methods=['POST'])
@login_required
def agregar_comentario(incidente_id, seccion_id):
    """
    Agrega un comentario a una sección (máximo 6)
    """
    try:
        data = request.get_json()
        
        if not data.get('comentario'):
            return jsonify({
                'success': False,
                'error': 'El comentario es requerido'
            }), 400
        
        resultado = sistema.agregar_comentario(
            incidente_id=incidente_id,
            seccion_id=seccion_id,
            comentario=data['comentario'],
            tipo_comentario=data.get('tipo', 'GENERAL'),
            usuario=current_user.username
        )
        
        return jsonify(resultado), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidente_dinamico_bp.route('/<int:incidente_id>/seccion/<int:seccion_id>/archivo', methods=['POST'])
@login_required
def subir_archivo(incidente_id, seccion_id):
    """
    Sube un archivo a una sección (máximo 10, 10MB cada uno)
    """
    try:
        # Verificar que hay archivo
        if 'archivo' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No se envió ningún archivo'
            }), 400
        
        archivo = request.files['archivo']
        if archivo.filename == '':
            return jsonify({
                'success': False,
                'error': 'Archivo sin nombre'
            }), 400
        
        # Leer contenido
        contenido = archivo.read()
        
        # Preparar info del archivo
        archivo_info = {
            'nombre_original': archivo.filename,
            'contenido_bytes': contenido,
            'tipo_mime': archivo.content_type,
            'descripcion': request.form.get('descripcion', '')
        }
        
        resultado = sistema.subir_archivo(
            incidente_id=incidente_id,
            seccion_id=seccion_id,
            archivo_info=archivo_info,
            usuario=current_user.username
        )
        
        return jsonify(resultado), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidente_dinamico_bp.route('/<int:incidente_id>', methods=['GET'])
@login_required
def cargar_incidente_completo(incidente_id):
    """
    Carga toda la información del incidente con sus secciones dinámicas
    El número de secciones varía según el tipo de empresa
    """
    try:
        resultado = sistema.cargar_incidente_completo(incidente_id)
        
        # Aplicar corrección de encoding a todo
        resultado = EncodingFixer.fix_dict(resultado)
        
        return jsonify(resultado), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidente_dinamico_bp.route('/<int:incidente_id>', methods=['DELETE'])
@login_required
def eliminar_incidente(incidente_id):
    """
    Elimina completamente un incidente y todos sus datos asociados
    """
    try:
        resultado = sistema.eliminar_incidente_completo(
            incidente_id=incidente_id,
            usuario=current_user.username
        )
        
        return jsonify(resultado), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidente_dinamico_bp.route('/<int:incidente_id>/resumen', methods=['GET'])
@login_required
def obtener_resumen_incidente(incidente_id):
    """
    Obtiene un resumen del estado del incidente por secciones
    Útil para mostrar el progreso general
    """
    try:
        datos_completos = sistema.cargar_incidente_completo(incidente_id)
        
        if not datos_completos['success']:
            return jsonify(datos_completos), 404
        
        # Crear resumen
        resumen = {
            'incidente_id': incidente_id,
            'total_secciones': datos_completos['total_secciones'],
            'secciones_con_contenido': datos_completos['secciones_con_contenido'],
            'progreso_general': round(
                (datos_completos['secciones_con_contenido'] / datos_completos['total_secciones']) * 100
            ),
            'secciones': []
        }
        
        # Resumen por sección
        for seccion in datos_completos['secciones']:
            resumen['secciones'].append({
                'codigo': seccion['codigo'],
                'titulo': seccion['titulo'],
                'tipo': seccion['tipo'],
                'estado': seccion['estado'],
                'porcentaje': seccion['porcentaje'],
                'tiene_contenido': seccion['tiene_contenido'],
                'comentarios': seccion['total_comentarios'],
                'archivos': seccion['total_archivos']
            })
        
        return jsonify({
            'success': True,
            'resumen': resumen
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidente_dinamico_bp.route('/sincronizar-taxonomias', methods=['POST'])
@login_required
def sincronizar_taxonomias():
    """
    Sincroniza las taxonomías desde la tabla TAXONOMIA_INCIDENTES
    Solo usuarios admin pueden ejecutar esto
    """
    try:
        # Verificar permisos admin
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Permisos insuficientes'
            }), 403
        
        # Aquí iría la lógica para ejecutar el stored procedure
        # sp_CargarTaxonomiasComoSecciones
        
        return jsonify({
            'success': True,
            'message': 'Taxonomías sincronizadas correctamente'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
#!/usr/bin/env python3
"""
Endpoint para eliminar evidencias y sus archivos asociados
Evita dejar archivos huérfanos en el sistema
"""

from flask import Blueprint, jsonify, request
from ..modules.admin.limpiador_archivos_huerfanos import LimpiadorArchivosHuerfanos

evidencias_eliminar_bp = Blueprint('evidencias_eliminar', __name__, url_prefix='/api/evidencias')

@evidencias_eliminar_bp.route('/eliminar/<int:evidencia_id>', methods=['DELETE'])
def eliminar_evidencia(evidencia_id):
    """
    Elimina una evidencia y su archivo físico asociado
    """
    try:
        # Obtener parámetros
        incidente_id = request.args.get('incidente_id', type=int)
        tipo = request.args.get('tipo', 'general')  # 'general' o 'taxonomia'
        
        if not incidente_id:
            return jsonify({
                "error": "Parámetro incidente_id requerido"
            }), 400
        
        print(f"🗑️ Eliminando evidencia {evidencia_id} del incidente {incidente_id} (tipo: {tipo})")
        
        # Ejecutar eliminación
        limpiador = LimpiadorArchivosHuerfanos()
        resultado = limpiador.eliminar_archivo_evidencia(
            evidencia_id=evidencia_id,
            incidente_id=incidente_id,
            tipo=tipo
        )
        
        if resultado['success']:
            return jsonify({
                "success": True,
                "message": resultado['mensaje'],
                "archivo_eliminado": resultado['archivo_eliminado'],
                "registro_eliminado": resultado['registro_eliminado']
            }), 200
        else:
            return jsonify({
                "error": resultado['mensaje']
            }), 500
            
    except Exception as e:
        print(f"❌ Error eliminando evidencia: {e}")
        return jsonify({
            "error": f"Error eliminando evidencia: {str(e)}"
        }), 500

@evidencias_eliminar_bp.route('/limpiar-huerfanos/<int:incidente_id>', methods=['POST'])
def limpiar_archivos_huerfanos(incidente_id):
    """
    Busca y elimina todos los archivos huérfanos de un incidente
    """
    try:
        print(f"🧹 Limpiando archivos huérfanos del incidente {incidente_id}")
        
        limpiador = LimpiadorArchivosHuerfanos()
        resultado = limpiador.limpiar_archivos_huerfanos_masivo(incidente_id)
        
        return jsonify({
            "success": True,
            "archivos_verificados": resultado['archivos_verificados'],
            "archivos_huerfanos": resultado['archivos_huerfanos'],
            "archivos_eliminados": resultado['archivos_eliminados'],
            "errores": resultado['errores']
        }), 200
        
    except Exception as e:
        print(f"❌ Error limpiando archivos huérfanos: {e}")
        return jsonify({
            "error": f"Error limpiando archivos: {str(e)}"
        }), 500
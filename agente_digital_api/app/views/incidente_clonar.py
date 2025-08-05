#!/usr/bin/env python3
"""
Endpoints para el sistema de clonado perfecto de incidentes
Garantiza que lo que se guarda es EXACTAMENTE lo que se obtiene al editar
"""

from flask import Blueprint, jsonify, request
from ..modules.incidentes.clonador_perfecto import IncidenteClonadorPerfecto

incidente_clonar_bp = Blueprint('incidente_clonar', __name__, url_prefix='/api/incidente/clonar')

@incidente_clonar_bp.route('/<int:incidente_id>', methods=['GET'])
def obtener_clon_incidente(incidente_id):
    """
    Obtiene un clon perfecto del incidente para edición
    """
    try:
        print(f"🔄 Clonando incidente {incidente_id} para edición...")
        
        clonador = IncidenteClonadorPerfecto()
        
        # Intentar cargar fotografía existente primero
        fotografia = clonador.cargar_fotografia_ultima(incidente_id, "actual")
        
        # Si no existe, crear nueva
        if not fotografia:
            fotografia = clonador.clonar_para_editar(incidente_id)
        
        return jsonify({
            "success": True,
            "incidente": fotografia,
            "mensaje": "Incidente clonado exitosamente"
        }), 200
        
    except Exception as e:
        print(f"❌ Error clonando incidente: {e}")
        return jsonify({
            "error": f"Error clonando incidente: {str(e)}"
        }), 500

@incidente_clonar_bp.route('/<int:incidente_id>/fotografia', methods=['POST'])
def crear_fotografia_incidente(incidente_id):
    """
    Crea una nueva fotografía del estado actual del incidente
    """
    try:
        print(f"📸 Creando fotografía del incidente {incidente_id}...")
        
        clonador = IncidenteClonadorPerfecto()
        fotografia = clonador.crear_fotografia_completa(incidente_id)
        
        # Guardar fotografía
        ruta = clonador.guardar_fotografia(incidente_id, None, fotografia, "manual")
        
        return jsonify({
            "success": True,
            "mensaje": "Fotografía creada exitosamente",
            "ruta": ruta,
            "resumen": fotografia['resumen']
        }), 200
        
    except Exception as e:
        print(f"❌ Error creando fotografía: {e}")
        return jsonify({
            "error": f"Error creando fotografía: {str(e)}"
        }), 500

@incidente_clonar_bp.route('/<int:incidente_id>/historial', methods=['GET'])
def obtener_historial_fotografias(incidente_id):
    """
    Obtiene el historial de todas las fotografías del incidente
    """
    try:
        clonador = IncidenteClonadorPerfecto()
        historial = clonador.obtener_historial_fotografias(incidente_id)
        
        return jsonify({
            "success": True,
            "historial": historial,
            "total": len(historial)
        }), 200
        
    except Exception as e:
        print(f"❌ Error obteniendo historial: {e}")
        return jsonify({
            "error": f"Error obteniendo historial: {str(e)}"
        }), 500

@incidente_clonar_bp.route('/test-encoding', methods=['GET'])
def test_encoding():
    """
    Endpoint de prueba para verificar la corrección de encoding
    """
    from ..utils.encoding_fixer import EncodingFixer
    
    # Textos de prueba con problemas comunes
    textos_prueba = [
        "Por eso no se cargan las taxonomÃ­as en la secciÃ³n 4.",
        "ExfiltraciÃ³n y/o exposiciÃ³n de configuraciones",
        "FiltraciÃ³n de secretos en rutas de aplicaciÃ³n",
        "CategorÃ­a del Incidente",
        "DescripciÃ³n inicial muy corta",
        "InformaciÃ³n del sistema"
    ]
    
    resultados = []
    for texto in textos_prueba:
        resultado = {
            "original": texto,
            "corregido": EncodingFixer.fix_text(texto),
            "exitoso": 'Ã' not in EncodingFixer.fix_text(texto)
        }
        resultados.append(resultado)
    
    return jsonify({
        "success": True,
        "pruebas": resultados,
        "resumen": {
            "total": len(resultados),
            "exitosos": sum(1 for r in resultados if r['exitoso'])
        }
    }), 200
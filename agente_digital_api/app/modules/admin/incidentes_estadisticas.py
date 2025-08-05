"""
Endpoint para calcular estadísticas de incidentes ANCI
"""
from flask import Blueprint, jsonify
from flask_cors import cross_origin
from app.database import get_db_connection
import logging

logger = logging.getLogger(__name__)

estadisticas_bp = Blueprint('estadisticas', __name__)

@estadisticas_bp.route('/api/admin/incidentes/<int:incidente_id>/estadisticas', methods=['GET'])
@cross_origin()
def obtener_estadisticas_incidente(incidente_id):
    """
    Calcula y retorna las estadísticas reales de un incidente
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Inicializar contadores
        total_evidencias = 0
        total_comentarios = 0
        
        # 1. Contar archivos (evidencias) de INCIDENTES_ARCHIVOS
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INCIDENTES_ARCHIVOS 
            WHERE IncidenteID = ? AND Activo = 1
        """, (incidente_id,))
        total_evidencias = cursor.fetchone()[0]
        
        # 2. Contar comentarios de INCIDENTES_COMENTARIOS
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INCIDENTES_COMENTARIOS 
            WHERE IncidenteID = ? AND Activo = 1
        """, (incidente_id,))
        total_comentarios = cursor.fetchone()[0]
        
        # 3. Contar comentarios de taxonomías
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM COMENTARIOS_TAXONOMIA 
                WHERE Id_Incidente = ?
            """, (incidente_id,))
            comentarios_taxonomia = cursor.fetchone()[0]
            total_comentarios += comentarios_taxonomia
        except:
            pass
        
        # 4. Contar evidencias de taxonomías
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM EVIDENCIAS_TAXONOMIA 
                WHERE Id_Incidente = ?
            """, (incidente_id,))
            evidencias_taxonomia = cursor.fetchone()[0]
            total_evidencias += evidencias_taxonomia
        except:
            pass
        
        # 5. Contar taxonomías seleccionadas
        taxonomias_seleccionadas = 0
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INCIDENTE_TAXONOMIA 
                WHERE Id_Incidente = ?
            """, (incidente_id,))
            taxonomias_seleccionadas = cursor.fetchone()[0]
        except:
            pass
        
        # 6. Calcular completitud basada en campos llenos
        cursor.execute("""
            SELECT 
                Titulo, TipoRegistro, FechaDeteccion, FechaOcurrencia,
                Criticidad, AlcanceGeografico, DescripcionInicial,
                AnciImpactoPreliminar, SistemasAfectados, ServiciosInterrumpidos,
                OrigenIncidente, AnciTipoAmenaza, ResponsableCliente,
                AccionesInmediatas, CausaRaiz, LeccionesAprendidas, PlanMejora
            FROM INCIDENTES 
            WHERE IncidenteID = ?
        """, (incidente_id,))
        
        campos = cursor.fetchone()
        campos_llenos = 0
        total_campos = 17  # Número de campos principales
        
        if campos:
            for campo in campos:
                if campo is not None and str(campo).strip() != '':
                    campos_llenos += 1
        
        # También considerar taxonomías, evidencias y comentarios para completitud
        if taxonomias_seleccionadas > 0:
            campos_llenos += 2  # Las taxonomías valen más
        if total_evidencias > 0:
            campos_llenos += 1
        if total_comentarios > 0:
            campos_llenos += 1
            
        total_campos += 4  # Agregar estos elementos al total
        
        # Calcular porcentaje
        completitud = int((campos_llenos / total_campos) * 100) if total_campos > 0 else 0
        completitud = min(100, completitud)  # No pasar de 100%
        
        # Retornar estadísticas
        estadisticas = {
            'TotalEvidencias': total_evidencias,
            'TotalComentarios': total_comentarios,
            'Completitud': completitud
        }
        
        logger.info(f"Estadísticas para incidente {incidente_id}: {estadisticas}")
        
        return jsonify(estadisticas), 200
        
    except Exception as e:
        logger.error(f"Error calculando estadísticas: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Retornar valores por defecto en caso de error
        return jsonify({
            'TotalEvidencias': 0,
            'TotalComentarios': 0,
            'Completitud': 0
        }), 200  # 200 para no romper el frontend
        
    finally:
        if conn:
            conn.close()

# Registrar blueprint
def register_estadisticas_blueprint(app):
    app.register_blueprint(estadisticas_bp)
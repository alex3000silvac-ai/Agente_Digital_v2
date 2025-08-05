# views/incidente_taxonomias.py
# Endpoint para cargar taxonomías de un incidente

from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from app.database import get_db_connection
from app.auth_utils import token_required
import logging

logger = logging.getLogger(__name__)

incidente_taxonomias_bp = Blueprint('incidente_taxonomias', __name__)

@incidente_taxonomias_bp.route('/api/admin/incidentes/<int:incidente_id>/taxonomias', methods=['GET'])
@cross_origin()
def obtener_taxonomias_incidente(incidente_id):
    # Temporalmente sin autenticación para pruebas
    current_user_id = 1
    current_user_rol = 'admin'
    current_user_email = 'admin@test.com'
    current_user_nombre = 'Admin'
    """
    Obtiene las taxonomías seleccionadas de un incidente con sus archivos
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar que el incidente existe
        cursor.execute("SELECT IncidenteID FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Incidente no encontrado"}), 404
        
        # Obtener taxonomías seleccionadas
        cursor.execute("""
            SELECT 
                IT.Id_Taxonomia,
                TI.Subcategoria_del_Incidente as nombre,
                TI.Descripcion,
                TI.AplicaTipoEmpresa,
                IT.Comentarios,
                IT.FechaAsignacion,
                IT.CreadoPor,
                TI.Categoria_del_Incidente as categoria
            FROM INCIDENTE_TAXONOMIA IT
            INNER JOIN Taxonomia_incidentes TI ON IT.Id_Taxonomia = TI.Id_Incidente
            WHERE IT.IncidenteID = ?
        """, (incidente_id,))
        
        taxonomias = []
        columns = [column[0] for column in cursor.description]
        
        for row in cursor.fetchall():
            tax = dict(zip(columns, row))
            
            # Parsear justificación y descripción del problema
            if tax.get('Comentarios'):
                comentarios = tax['Comentarios']
                if 'Justificación:' in comentarios:
                    parts = comentarios.split('Justificación:', 1)
                    if len(parts) > 1:
                        justif_parts = parts[1].split('\n', 1)
                        tax['justificacion'] = justif_parts[0].strip()
                        
                        if len(justif_parts) > 1 and 'Descripción del problema:' in justif_parts[1]:
                            desc_parts = justif_parts[1].split('Descripción del problema:', 1)
                            if len(desc_parts) > 1:
                                tax['descripcionProblema'] = desc_parts[1].strip()
                            else:
                                tax['descripcionProblema'] = ''
                        else:
                            tax['descripcionProblema'] = ''
                else:
                    tax['justificacion'] = comentarios
                    tax['descripcionProblema'] = ''
            else:
                tax['justificacion'] = ''
                tax['descripcionProblema'] = ''
            
            # Agregar campos esperados por el frontend
            tax['id'] = tax['Id_Taxonomia']
            
            # Convertir fecha a string
            if tax.get('FechaAsignacion'):
                tax['FechaAsignacion'] = tax['FechaAsignacion'].isoformat()
            
            taxonomias.append(tax)
        
        # Obtener archivos de cada taxonomía
        cursor.execute("""
            SELECT 
                ET.TaxonomiaID,
                ET.EvidenciaID,
                ET.NombreArchivo,
                ET.NombreArchivoOriginal,
                ET.RutaArchivo,
                ET.TamanoArchivo,
                ET.FechaSubida
            FROM EVIDENCIAS_TAXONOMIA ET
            WHERE ET.IncidenteID = ?
            ORDER BY ET.TaxonomiaID, ET.FechaSubida DESC
        """, (incidente_id,))
        
        # Agrupar archivos por taxonomía
        archivos_por_taxonomia = {}
        for row in cursor.fetchall():
            tax_id = row[0]
            if tax_id not in archivos_por_taxonomia:
                archivos_por_taxonomia[tax_id] = []
            
            archivos_por_taxonomia[tax_id].append({
                'id': row[1],
                'nombre': row[2],
                'nombreOriginal': row[3],
                'ruta': row[4],
                'tamaño': row[5],
                'fechaSubida': row[6].isoformat() if row[6] else None
            })
        
        # Agregar archivos a cada taxonomía
        for tax in taxonomias:
            tax_id = tax['id']
            tax['archivos'] = archivos_por_taxonomia.get(tax_id, [])
        
        cursor.close()
        conn.close()
        
        logger.info(f"Taxonomías del incidente {incidente_id} obtenidas: {len(taxonomias)}")
        
        return jsonify({
            "success": True,
            "taxonomias": taxonomias,
            "total": len(taxonomias)
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo taxonomías del incidente: {str(e)}")
        return jsonify({"error": f"Error al obtener taxonomías: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
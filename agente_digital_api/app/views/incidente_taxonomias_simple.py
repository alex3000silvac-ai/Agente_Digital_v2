# views/incidente_taxonomias_simple.py
# Endpoint simplificado para cargar taxonomías sin autenticación

from flask import Blueprint, jsonify
from flask_cors import cross_origin
from app.database import get_db_connection

incidente_taxonomias_simple_bp = Blueprint('incidente_taxonomias_simple', __name__)

@incidente_taxonomias_simple_bp.route('/api/incidentes/<int:incidente_id>/taxonomias-simple', methods=['GET'])
@cross_origin()
def obtener_taxonomias_simple(incidente_id):
    """
    Obtiene las taxonomías de un incidente sin autenticación
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Consulta simplificada
        cursor.execute("""
            SELECT 
                IT.Id_Taxonomia,
                TI.Subcategoria_del_Incidente as nombre,
                IT.Comentarios,
                TI.Categoria_del_Incidente as categoria
            FROM INCIDENTE_TAXONOMIA IT
            INNER JOIN Taxonomia_incidentes TI ON IT.Id_Taxonomia = TI.Id_Incidente
            WHERE IT.IncidenteID = ?
        """, (incidente_id,))
        
        taxonomias = []
        for row in cursor.fetchall():
            comentarios = row[2] or ''
            justificacion = ''
            descripcion = ''
            
            # Parsear comentarios
            if 'Justificación:' in comentarios:
                parts = comentarios.split('Justificación:', 1)
                if len(parts) > 1:
                    justif_parts = parts[1].split('\n', 1)
                    justificacion = justif_parts[0].strip()
                    if len(justif_parts) > 1 and 'Descripción del problema:' in justif_parts[1]:
                        desc_parts = justif_parts[1].split('Descripción del problema:', 1)
                        if len(desc_parts) > 1:
                            descripcion = desc_parts[1].strip()
            
            taxonomias.append({
                'id': row[0],
                'nombre': row[1],
                'justificacion': justificacion,
                'descripcionProblema': descripcion,
                'categoria': row[3],
                'archivos': []  # Se llenarán después
            })
        
        # Obtener archivos
        cursor.execute("""
            SELECT 
                TaxonomiaID,
                NombreArchivoOriginal,
                TamanoArchivo
            FROM EVIDENCIAS_TAXONOMIA
            WHERE IncidenteID = ?
        """, (incidente_id,))
        
        # Agrupar archivos
        for row in cursor.fetchall():
            tax_id = row[0]
            for tax in taxonomias:
                if tax['id'] == tax_id:
                    tax['archivos'].append({
                        'nombreOriginal': row[1],
                        'tamaño': row[2]
                    })
                    break
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "taxonomias": taxonomias,
            "total": len(taxonomias)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
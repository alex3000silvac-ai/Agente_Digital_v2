#!/usr/bin/env python3
"""
Endpoint para actualizar campos ANCI faltantes en incidentes existentes
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..database import get_db_connection
from datetime import datetime

campos_anci_bp = Blueprint('campos_anci', __name__, url_prefix='/api/incidente')

@campos_anci_bp.route('/<int:incidente_id>/campos-anci', methods=['PUT'])
@login_required
def actualizar_campos_anci(incidente_id):
    """
    Actualiza los campos específicos de ANCI en un incidente
    
    Body JSON esperado:
    {
        "estadoActual": "Activo|En Investigación|Contenido|Erradicado|Cerrado",
        "reporteAnciId": "ANCI-2024-001",
        "fechaDeclaracionAnci": "2024-01-15T10:30:00"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se proporcionaron datos'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
        cursor = conn.cursor()
        
        # Verificar que el incidente existe
        cursor.execute("SELECT IncidenteID FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Incidente no encontrado'}), 404
        
        # Construir query de actualización dinámica
        campos_actualizar = []
        valores = []
        
        if 'estadoActual' in data:
            campos_actualizar.append("EstadoActual = ?")
            valores.append(data['estadoActual'])
        
        if 'reporteAnciId' in data:
            campos_actualizar.append("ReporteAnciID = ?")
            valores.append(data['reporteAnciId'])
        
        if 'fechaDeclaracionAnci' in data:
            campos_actualizar.append("FechaDeclaracionANCI = ?")
            # Convertir string ISO a datetime
            fecha_str = data['fechaDeclaracionAnci']
            if fecha_str:
                fecha_dt = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
                valores.append(fecha_dt)
            else:
                valores.append(None)
        
        # Siempre actualizar fecha de modificación
        campos_actualizar.append("FechaActualizacion = GETDATE()")
        
        if campos_actualizar:
            # Agregar el ID al final para el WHERE
            valores.append(incidente_id)
            
            query = f"""
                UPDATE Incidentes 
                SET {', '.join(campos_actualizar)}
                WHERE IncidenteID = ?
            """
            
            cursor.execute(query, valores)
            conn.commit()
            
            # Obtener los datos actualizados
            cursor.execute("""
                SELECT EstadoActual, ReporteAnciID, FechaDeclaracionANCI
                FROM Incidentes 
                WHERE IncidenteID = ?
            """, (incidente_id,))
            
            row = cursor.fetchone()
            
            resultado = {
                'success': True,
                'incidente_id': incidente_id,
                'campos_actualizados': {
                    'estadoActual': row[0],
                    'reporteAnciId': row[1],
                    'fechaDeclaracionAnci': row[2].isoformat() if row[2] else None
                }
            }
            
            return jsonify(resultado), 200
            
        else:
            return jsonify({'error': 'No se proporcionaron campos válidos para actualizar'}), 400
            
    except Exception as e:
        print(f"Error actualizando campos ANCI: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'detalles': str(e)
        }), 500
        
    finally:
        if conn:
            conn.close()


@campos_anci_bp.route('/<int:incidente_id>/validar-anci', methods=['GET'])
@login_required
def validar_campos_anci(incidente_id):
    """
    Valida si un incidente tiene todos los campos necesarios para generar informe ANCI
    """
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
        cursor = conn.cursor()
        
        # Obtener todos los campos relevantes
        cursor.execute("""
            SELECT 
                i.Titulo, i.FechaDeteccion, i.FechaOcurrencia, i.Criticidad,
                i.EstadoActual, i.EmpresaID, i.OrigenIncidente, i.SistemasAfectados,
                i.ServiciosInterrumpidos, i.AlcanceGeografico, i.ResponsableCliente,
                i.ReporteAnciID, i.FechaDeclaracionANCI, i.AnciTipoAmenaza,
                i.AnciImpactoPreliminar, i.CausaRaiz, i.LeccionesAprendidas,
                i.PlanMejora, i.IDVisible,
                e.Tipo_Empresa
            FROM Incidentes i
            INNER JOIN Empresas e ON i.EmpresaID = e.EmpresaID
            WHERE i.IncidenteID = ?
        """, (incidente_id,))
        
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Incidente no encontrado'}), 404
        
        # Mapear campos
        campos = {
            'titulo': row[0],
            'fechaDeteccion': row[1],
            'fechaOcurrencia': row[2],
            'criticidad': row[3],
            'estadoActual': row[4],
            'empresaId': row[5],
            'origenIncidente': row[6],
            'sistemasAfectados': row[7],
            'serviciosInterrumpidos': row[8],
            'alcanceGeografico': row[9],
            'responsableCliente': row[10],
            'reporteAnciId': row[11],
            'fechaDeclaracionAnci': row[12],
            'tipoAmenaza': row[13],
            'impactoPreliminar': row[14],
            'causaRaiz': row[15],
            'leccionesAprendidas': row[16],
            'planMejora': row[17],
            'idVisible': row[18],
            'tipoEmpresa': row[19]
        }
        
        # Validar campos requeridos
        campos_requeridos = {
            'titulo': 'Título del incidente',
            'fechaDeteccion': 'Fecha de detección',
            'criticidad': 'Criticidad',
            'estadoActual': 'Estado actual',
            'empresaId': 'ID de empresa',
            'sistemasAfectados': 'Sistemas afectados',
            'tipoEmpresa': 'Tipo de empresa'
        }
        
        campos_faltantes = []
        campos_vacios = []
        
        for campo, descripcion in campos_requeridos.items():
            if campo not in campos or campos[campo] is None:
                campos_faltantes.append(descripcion)
            elif isinstance(campos[campo], str) and not campos[campo].strip():
                campos_vacios.append(descripcion)
        
        # Determinar si está listo para ANCI
        listo_para_anci = len(campos_faltantes) == 0 and len(campos_vacios) == 0
        
        # Calcular porcentaje de completitud
        total_campos = len(campos)
        campos_completos = sum(1 for v in campos.values() if v is not None and (not isinstance(v, str) or v.strip()))
        porcentaje_completitud = round((campos_completos / total_campos) * 100)
        
        resultado = {
            'incidente_id': incidente_id,
            'listo_para_anci': listo_para_anci,
            'porcentaje_completitud': porcentaje_completitud,
            'campos_faltantes': campos_faltantes,
            'campos_vacios': campos_vacios,
            'resumen': {
                'total_campos': total_campos,
                'campos_completos': campos_completos,
                'campos_incompletos': total_campos - campos_completos
            },
            'datos_actuales': {
                k: v.isoformat() if hasattr(v, 'isoformat') else v 
                for k, v in campos.items()
            }
        }
        
        return jsonify(resultado), 200
        
    except Exception as e:
        print(f"Error validando campos ANCI: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'detalles': str(e)
        }), 500
        
    finally:
        if conn:
            conn.close()
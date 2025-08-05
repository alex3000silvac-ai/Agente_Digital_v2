#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Endpoints para generación de informes ANCI completos
"""

from flask import Blueprint, jsonify, send_file, request
from flask_cors import cross_origin
from .informes_anci_completo import generar_informe_anci_completo
from ..database import get_db_connection
from ..auth_utils import token_required
import os
import traceback

# Crear blueprint
informes_anci_completo_bp = Blueprint('informes_anci_completo', __name__)

@informes_anci_completo_bp.route('/api/admin/reportes-anci/<int:reporte_id>/exportar-completo', methods=['GET'])
@cross_origin()
@token_required
def exportar_informe_completo(current_user_id, current_user_rol, current_user_email, current_user_nombre, reporte_id):
    """
    Genera y descarga un informe ANCI completo con todos los campos requeridos
    """
    try:
        # Verificar que el reporte existe
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                r.ReporteAnciID,
                r.IncidenteID,
                r.EstadoReporte,
                i.Titulo,
                e.TipoEmpresa
            FROM ReportesANCI r
            INNER JOIN Incidentes i ON r.IncidenteID = i.IncidenteID
            INNER JOIN Empresas e ON i.EmpresaID = e.EmpresaID
            WHERE r.ReporteAnciID = ?
        """, (reporte_id,))
        
        reporte = cursor.fetchone()
        
        if not reporte:
            return jsonify({"error": "Reporte ANCI no encontrado"}), 404
        
        # Generar el informe
        filepath = generar_informe_anci_completo(reporte_id)
        
        if not os.path.exists(filepath):
            return jsonify({"error": "Error al generar el informe"}), 500
        
        # Registrar la generación en auditoría
        cursor.execute("""
            INSERT INTO INCIDENTES_AUDITORIA 
            (IncidenteID, TipoAccion, DatosNuevos, Usuario, FechaAccion)
            VALUES (?, ?, ?, ?, GETDATE())
        """, (
            reporte.IncidenteID,
            'EXPORTAR_INFORME_ANCI_COMPLETO',
            f'Reporte ANCI ID: {reporte_id}',
            current_user_email,
        ))
        
        conn.commit()
        conn.close()
        
        # Enviar el archivo
        filename = f"Informe_ANCI_Completo_{reporte.IncidenteID}_{reporte_id}.docx"
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        print(f"Error exportando informe ANCI completo: {e}")
        traceback.print_exc()
        return jsonify({"error": "Error al generar el informe ANCI"}), 500


@informes_anci_completo_bp.route('/api/admin/incidentes/<int:incidente_id>/generar-informe-anci-completo', methods=['POST'])
@cross_origin()
@token_required
def generar_desde_incidente(current_user_id, current_user_rol, current_user_email, current_user_nombre, incidente_id):
    """
    Genera un informe ANCI completo directamente desde un incidente
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si ya existe un reporte ANCI para este incidente
        cursor.execute("""
            SELECT ReporteAnciID 
            FROM ReportesANCI 
            WHERE IncidenteID = ? 
            ORDER BY FechaGeneracion DESC
        """, (incidente_id,))
        
        reporte = cursor.fetchone()
        
        if not reporte:
            # Crear un reporte ANCI temporal
            cursor.execute("""
                INSERT INTO ReportesANCI (
                    IncidenteID,
                    TipoReporte,
                    EstadoReporte,
                    FechaGeneracion,
                    CreadoPor
                ) VALUES (?, ?, ?, GETDATE(), ?)
            """, (
                incidente_id,
                'EXPORTACION',
                'GENERADO',
                current_user_id
            ))
            
            cursor.execute("SELECT SCOPE_IDENTITY()")
            reporte_id = cursor.fetchone()[0]
            
            conn.commit()
        else:
            reporte_id = reporte.ReporteAnciID
        
        conn.close()
        
        # Generar el informe
        filepath = generar_informe_anci_completo(reporte_id)
        
        if not os.path.exists(filepath):
            return jsonify({"error": "Error al generar el informe"}), 500
        
        # Enviar el archivo
        filename = f"Informe_ANCI_Completo_Incidente_{incidente_id}.docx"
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        print(f"Error generando informe ANCI: {e}")
        traceback.print_exc()
        return jsonify({"error": "Error al generar el informe ANCI"}), 500


@informes_anci_completo_bp.route('/api/admin/reportes-anci/<int:reporte_id>/validar-campos', methods=['GET'])
@cross_origin()
@token_required
def validar_campos_completos(current_user_id, current_user_rol, current_user_email, current_user_nombre, reporte_id):
    """
    Valida qué campos están completos para el informe ANCI
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener todos los campos del reporte
        cursor.execute("""
            SELECT 
                -- Datos del reportante
                AnciNombreReportante,
                AnciCargoReportante,
                AnciCorreoReportante,
                AnciTelefonoReportante,
                AnciFormacionCertificacion,
                -- Identificación del incidente
                AnciTipoIncidenteTaxonomia,
                AnciSistemasAfectadosDetalle,
                AnciImpactoContinuidadDatos,
                AnciAfectacionTerceros,
                AnciNumeroAfectados,
                -- Medidas iniciales
                AnciAccionesContencion,
                AnciSistemasDesconectados,
                AnciNotificacionesInternas,
                AnciEstadoActualIncidente,
                -- OIV
                AnciOIVCuentaConSGSI,
                AnciOIVDetallePlanContinuidad,
                AnciOIVActivoPlanRecuperacion,
                AnciOIVAuditoriasRealizadas,
                AnciOIVFechaUltimaAuditoria,
                AnciOIVDelegadoTecnico,
                AnciOIVMedidasPropagacion,
                AnciOIVNotificacionAfectados,
                AnciOIVRegistroCapacitaciones,
                -- Contacto seguimiento
                AnciContactoSeguimientoNombre,
                AnciContactoSeguimientoHorario,
                AnciContactoSeguimientoCorreo,
                AnciContactoSeguimientoTelefono,
                -- Tipo empresa
                TipoEmpresa
            FROM ReportesANCI
            WHERE ReporteAnciID = ?
        """, (reporte_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return jsonify({"error": "Reporte no encontrado"}), 404
        
        # Analizar campos completos y faltantes
        campos_obligatorios = {
            'seccion_1': {
                'AnciNombreReportante': 'Nombre del reportante',
                'AnciCargoReportante': 'Cargo del reportante',
                'AnciCorreoReportante': 'Correo del reportante',
                'AnciTelefonoReportante': 'Teléfono del reportante',
                'AnciFormacionCertificacion': 'Formación/Certificación'
            },
            'seccion_2': {
                'AnciTipoIncidenteTaxonomia': 'Tipo de incidente (Taxonomía)',
                'AnciSistemasAfectadosDetalle': 'Sistemas afectados',
                'AnciImpactoContinuidadDatos': 'Impacto en continuidad/datos',
                'AnciAfectacionTerceros': 'Afectación a terceros',
                'AnciNumeroAfectados': 'Número de afectados'
            },
            'seccion_3': {
                'AnciAccionesContencion': 'Acciones de contención',
                'AnciSistemasDesconectados': 'Sistemas desconectados',
                'AnciNotificacionesInternas': 'Notificaciones internas',
                'AnciEstadoActualIncidente': 'Estado actual'
            },
            'contacto': {
                'AnciContactoSeguimientoNombre': 'Nombre contacto seguimiento',
                'AnciContactoSeguimientoHorario': 'Horario contacto',
                'AnciContactoSeguimientoCorreo': 'Correo contacto',
                'AnciContactoSeguimientoTelefono': 'Teléfono contacto'
            }
        }
        
        # Si es OIV, agregar campos adicionales
        if row.TipoEmpresa == 'OIV':
            campos_obligatorios['seccion_4_oiv'] = {
                'AnciOIVCuentaConSGSI': 'SGSI certificado',
                'AnciOIVDetallePlanContinuidad': 'Plan de continuidad',
                'AnciOIVActivoPlanRecuperacion': 'Activación plan recuperación',
                'AnciOIVAuditoriasRealizadas': 'Auditorías realizadas',
                'AnciOIVFechaUltimaAuditoria': 'Fecha última auditoría',
                'AnciOIVDelegadoTecnico': 'Delegado técnico',
                'AnciOIVMedidasPropagacion': 'Medidas contra propagación',
                'AnciOIVNotificacionAfectados': 'Notificación a afectados',
                'AnciOIVRegistroCapacitaciones': 'Registro capacitaciones'
            }
        
        # Verificar completitud
        resultado = {
            'completo': True,
            'porcentaje': 0,
            'secciones': {}
        }
        
        total_campos = 0
        campos_completos = 0
        
        for seccion, campos in campos_obligatorios.items():
            seccion_completa = True
            campos_seccion_completos = 0
            campos_faltantes = []
            
            for campo, descripcion in campos.items():
                total_campos += 1
                valor = getattr(row, campo, None)
                
                if valor and str(valor).strip():
                    campos_completos += 1
                    campos_seccion_completos += 1
                else:
                    seccion_completa = False
                    campos_faltantes.append(descripcion)
            
            resultado['secciones'][seccion] = {
                'completa': seccion_completa,
                'porcentaje': (campos_seccion_completos / len(campos)) * 100 if campos else 0,
                'campos_faltantes': campos_faltantes
            }
        
        resultado['completo'] = (campos_completos == total_campos)
        resultado['porcentaje'] = (campos_completos / total_campos) * 100 if total_campos > 0 else 0
        
        conn.close()
        
        return jsonify(resultado), 200
        
    except Exception as e:
        print(f"Error validando campos: {e}")
        traceback.print_exc()
        return jsonify({"error": "Error al validar campos"}), 500

# Función para registrar las rutas
def registrar_rutas_informes_completos(app):
    """Registra las rutas del módulo de informes ANCI completos"""
    app.register_blueprint(informes_anci_completo_bp)
#!/usr/bin/env python3
"""
Endpoint para actualizar incidentes ANCI con todos los campos requeridos
Integra con el UnificadorIncidentes para mantener consistencia
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..database import get_db_connection
from ..modules.incidentes.unificador import UnificadorIncidentes
import json
from datetime import datetime
import traceback

incidente_anci_actualizar_bp = Blueprint('incidente_anci_actualizar', __name__, url_prefix='/api/incidente')

@incidente_anci_actualizar_bp.route('/<int:incidente_id>/actualizar-anci', methods=['PUT'])
@login_required
def actualizar_incidente_anci(incidente_id):
    """
    Actualiza un incidente ANCI con todos los campos obligatorios
    Usa el UnificadorIncidentes para mantener consistencia
    """
    conn = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se proporcionaron datos'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
        cursor = conn.cursor()
        
        # 1. Verificar que el incidente existe y obtener datos actuales
        cursor.execute("""
            SELECT 
                i.IncidenteID, i.DatosIncidente, i.EmpresaID, i.ReporteAnciID,
                e.RazonSocial, e.RUT, e.TipoEmpresa, 
                i.SectorEsencial, i.NombreReportante, i.CargoReportante,
                i.TelefonoEmergencia, i.EmailOficialSeguridad,
                i.SistemasAfectados, i.ServiciosInterrumpidos, i.AlcanceGeografico,
                i.DuracionEstimadaHoras, i.IncidenteEnCurso, i.ContencionAplicada,
                i.DescripcionEstadoActual, i.SistemasAislados, i.SolicitarCSIRT,
                i.TipoApoyoCSIRT, i.VectorAtaque, i.VulnerabilidadExplotada,
                i.VolumenDatosComprometidosGB, i.EfectosColaterales,
                i.IPsSospechosas, i.HashesMalware, i.DominiosMaliciosos,
                i.URLsMaliciosas, i.CuentasComprometidas, i.CronologiaDetallada,
                i.NotificacionRegulador, i.ReguladorNotificado, i.DenunciaPolicial,
                i.NumeroPartePolicial, i.ContactoProveedoresSeguridad, i.ComunicacionPublica,
                i.ProgramaRestauracion, i.ResponsablesAdministrativos, i.TiempoRestablecimientoHoras,
                i.RecursosNecesarios, i.AccionesCortoPlazo, i.AccionesMedianoPlazo,
                i.AccionesLargoPlazo, i.CostosRecuperacion, i.PerdidasOperativas,
                i.CostosTerceros, i.AlertaTempranaEnviada, i.FechaAlertaTemprana,
                i.InformePreliminarEnviado, i.FechaInformePreliminar, i.InformeCompletoEnviado,
                i.FechaInformeCompleto, i.PlanAccionEnviado, i.FechaPlanAccion,
                i.InformeFinalEnviado, i.FechaInformeFinal
            FROM Incidentes i
            LEFT JOIN Empresas e ON i.EmpresaID = e.EmpresaID
            WHERE i.IncidenteID = ?
        """, (incidente_id,))
        
        incidente_row = cursor.fetchone()
        if not incidente_row:
            return jsonify({'error': 'Incidente no encontrado'}), 404
        
        # Mapear los datos actuales de la BD
        columns = [column[0] for column in cursor.description]
        datos_bd = dict(zip(columns, incidente_row))
        
        # 2. Cargar o crear estructura JSON del incidente
        datos_json_actuales = None
        if datos_bd.get('DatosIncidente'):
            try:
                datos_json_actuales = json.loads(datos_bd['DatosIncidente'])
            except:
                # Si el JSON está corrupto, crear uno nuevo
                datos_json_actuales = None
        
        # Si no hay JSON o está corrupto, crear estructura base
        if not datos_json_actuales:
            datos_json_actuales = UnificadorIncidentes.crear_estructura_incidente()
        
        # 3. Migrar campos ANCI desde la BD al JSON
        datos_json_actuales = UnificadorIncidentes.migrar_campos_anci(datos_json_actuales, datos_bd)
        
        # 4. Actualizar con los nuevos datos del request
        if 'secciones' in data:
            for seccion_id, contenido in data['secciones'].items():
                if seccion_id in datos_json_actuales and isinstance(contenido, dict):
                    # Actualizar recursivamente manteniendo estructura existente
                    _actualizar_dict_recursivo(datos_json_actuales[seccion_id], contenido)
        
        # 5. Validar campos ANCI según tipo de reporte
        tipo_reporte = data.get('tipo_reporte', 'alerta_temprana')
        es_valido, campos_faltantes = UnificadorIncidentes.validar_campos_anci(datos_json_actuales, tipo_reporte)
        
        # 6. Preparar el JSON para guardar
        datos_json_final = UnificadorIncidentes.exportar_para_guardar(datos_json_actuales)
        json_string = json.dumps(datos_json_final, ensure_ascii=False)
        
        # 7. Actualizar campos en la BD
        campos_actualizar = []
        valores = []
        
        # Actualizar DatosIncidente
        campos_actualizar.append("DatosIncidente = ?")
        valores.append(json_string)
        
        # Actualizar campos individuales desde el JSON (para búsquedas y reportes)
        # Sección 1 - Empresa y contacto
        if "1" in datos_json_actuales:
            sec1 = datos_json_actuales["1"]
            if sec1.get("empresa"):
                if sec1["empresa"].get("sector_esencial"):
                    campos_actualizar.append("SectorEsencial = ?")
                    valores.append(sec1["empresa"]["sector_esencial"])
            
            if sec1.get("contacto_emergencia"):
                contacto = sec1["contacto_emergencia"]
                if contacto.get("nombre_reportante"):
                    campos_actualizar.append("NombreReportante = ?")
                    valores.append(contacto["nombre_reportante"])
                if contacto.get("cargo_reportante"):
                    campos_actualizar.append("CargoReportante = ?")
                    valores.append(contacto["cargo_reportante"])
                if contacto.get("telefono_24_7"):
                    campos_actualizar.append("TelefonoEmergencia = ?")
                    valores.append(contacto["telefono_24_7"])
                if contacto.get("email_oficial_seguridad"):
                    campos_actualizar.append("EmailOficialSeguridad = ?")
                    valores.append(contacto["email_oficial_seguridad"])
        
        # Sección 2 - Estado e impacto
        if "2" in datos_json_actuales:
            sec2 = datos_json_actuales["2"]
            if sec2.get("sistemas_afectados"):
                campos_actualizar.append("SistemasAfectados = ?")
                valores.append(",".join(sec2["sistemas_afectados"]) if isinstance(sec2["sistemas_afectados"], list) else sec2["sistemas_afectados"])
            if sec2.get("servicios_interrumpidos"):
                campos_actualizar.append("ServiciosInterrumpidos = ?")
                valores.append(sec2["servicios_interrumpidos"])
            if sec2.get("alcance_geografico"):
                campos_actualizar.append("AlcanceGeografico = ?")
                valores.append(sec2["alcance_geografico"])
            if sec2.get("duracion_estimada_horas") is not None:
                campos_actualizar.append("DuracionEstimadaHoras = ?")
                valores.append(sec2["duracion_estimada_horas"])
            if sec2.get("incidente_en_curso") is not None:
                campos_actualizar.append("IncidenteEnCurso = ?")
                valores.append(1 if sec2["incidente_en_curso"] else 0)
            if sec2.get("contencion_aplicada") is not None:
                campos_actualizar.append("ContencionAplicada = ?")
                valores.append(1 if sec2["contencion_aplicada"] else 0)
            if sec2.get("descripcion_estado_actual"):
                campos_actualizar.append("DescripcionEstadoActual = ?")
                valores.append(sec2["descripcion_estado_actual"])
        
        # Sección 5 - Respuesta
        if "5" in datos_json_actuales:
            sec5 = datos_json_actuales["5"]
            if sec5.get("sistemas_aislados"):
                campos_actualizar.append("SistemasAislados = ?")
                valores.append(",".join(sec5["sistemas_aislados"]) if isinstance(sec5["sistemas_aislados"], list) else sec5["sistemas_aislados"])
            if sec5.get("solicitar_csirt") is not None:
                campos_actualizar.append("SolicitarCSIRT = ?")
                valores.append(1 if sec5["solicitar_csirt"] else 0)
            if sec5.get("tipo_apoyo_csirt"):
                campos_actualizar.append("TipoApoyoCSIRT = ?")
                valores.append(sec5["tipo_apoyo_csirt"])
        
        # Sección 9 - Campos técnicos ANCI
        if "9" in datos_json_actuales:
            sec9 = datos_json_actuales["9"]
            
            # Campos técnicos
            if sec9.get("vector_ataque"):
                campos_actualizar.append("VectorAtaque = ?")
                valores.append(sec9["vector_ataque"])
            if sec9.get("vulnerabilidad_explotada"):
                campos_actualizar.append("VulnerabilidadExplotada = ?")
                valores.append(sec9["vulnerabilidad_explotada"])
            if sec9.get("volumen_datos_gb") is not None:
                campos_actualizar.append("VolumenDatosComprometidosGB = ?")
                valores.append(sec9["volumen_datos_gb"])
            if sec9.get("efectos_colaterales"):
                campos_actualizar.append("EfectosColaterales = ?")
                valores.append(sec9["efectos_colaterales"])
            
            # IoCs
            if sec9.get("iocs"):
                iocs = sec9["iocs"]
                if iocs.get("ips_sospechosas"):
                    campos_actualizar.append("IPsSospechosas = ?")
                    valores.append("\\n".join(iocs["ips_sospechosas"]))
                if iocs.get("hashes_malware"):
                    campos_actualizar.append("HashesMalware = ?")
                    valores.append("\\n".join(iocs["hashes_malware"]))
                if iocs.get("dominios_maliciosos"):
                    campos_actualizar.append("DominiosMaliciosos = ?")
                    valores.append("\\n".join(iocs["dominios_maliciosos"]))
                if iocs.get("urls_maliciosas"):
                    campos_actualizar.append("URLsMaliciosas = ?")
                    valores.append("\\n".join(iocs["urls_maliciosas"]))
                if iocs.get("cuentas_comprometidas"):
                    campos_actualizar.append("CuentasComprometidas = ?")
                    valores.append("\\n".join(iocs["cuentas_comprometidas"]))
            
            # Cronología
            if sec9.get("cronologia_detallada"):
                campos_actualizar.append("CronologiaDetallada = ?")
                valores.append(json.dumps(sec9["cronologia_detallada"], ensure_ascii=False))
            
            # Coordinaciones
            if sec9.get("coordinaciones"):
                coord = sec9["coordinaciones"]
                if coord.get("notificacion_regulador") is not None:
                    campos_actualizar.append("NotificacionRegulador = ?")
                    valores.append(1 if coord["notificacion_regulador"] else 0)
                if coord.get("regulador_notificado"):
                    campos_actualizar.append("ReguladorNotificado = ?")
                    valores.append(coord["regulador_notificado"])
                if coord.get("denuncia_policial") is not None:
                    campos_actualizar.append("DenunciaPolicial = ?")
                    valores.append(1 if coord["denuncia_policial"] else 0)
                if coord.get("numero_parte_policial"):
                    campos_actualizar.append("NumeroPartePolicial = ?")
                    valores.append(coord["numero_parte_policial"])
                if coord.get("proveedores_contactados") is not None:
                    campos_actualizar.append("ContactoProveedoresSeguridad = ?")
                    valores.append(1 if coord["proveedores_contactados"] else 0)
                if coord.get("comunicacion_publica") is not None:
                    campos_actualizar.append("ComunicacionPublica = ?")
                    valores.append(1 if coord["comunicacion_publica"] else 0)
            
            # Plan OIV
            if sec9.get("plan_accion_oiv"):
                plan = sec9["plan_accion_oiv"]
                if plan.get("programa_restauracion"):
                    campos_actualizar.append("ProgramaRestauracion = ?")
                    valores.append(plan["programa_restauracion"])
                if plan.get("responsables_administrativos"):
                    campos_actualizar.append("ResponsablesAdministrativos = ?")
                    valores.append(plan["responsables_administrativos"])
                if plan.get("tiempo_restablecimiento_horas") is not None:
                    campos_actualizar.append("TiempoRestablecimientoHoras = ?")
                    valores.append(plan["tiempo_restablecimiento_horas"])
                if plan.get("recursos_necesarios"):
                    campos_actualizar.append("RecursosNecesarios = ?")
                    valores.append(plan["recursos_necesarios"])
                if plan.get("acciones_corto_plazo"):
                    campos_actualizar.append("AccionesCortoPlazo = ?")
                    valores.append(plan["acciones_corto_plazo"])
                if plan.get("acciones_mediano_plazo"):
                    campos_actualizar.append("AccionesMedianoPlazo = ?")
                    valores.append(plan["acciones_mediano_plazo"])
                if plan.get("acciones_largo_plazo"):
                    campos_actualizar.append("AccionesLargoPlazo = ?")
                    valores.append(plan["acciones_largo_plazo"])
            
            # Impacto económico
            if sec9.get("impacto_economico"):
                imp = sec9["impacto_economico"]
                if imp.get("costos_recuperacion") is not None:
                    campos_actualizar.append("CostosRecuperacion = ?")
                    valores.append(imp["costos_recuperacion"])
                if imp.get("perdidas_operativas") is not None:
                    campos_actualizar.append("PerdidasOperativas = ?")
                    valores.append(imp["perdidas_operativas"])
                if imp.get("costos_terceros") is not None:
                    campos_actualizar.append("CostosTerceros = ?")
                    valores.append(imp["costos_terceros"])
            
            # Tracking de reportes
            if sec9.get("tracking_reportes"):
                track = sec9["tracking_reportes"]
                if track.get("alerta_temprana_enviada") is not None:
                    campos_actualizar.append("AlertaTempranaEnviada = ?")
                    valores.append(1 if track["alerta_temprana_enviada"] else 0)
                if track.get("fecha_alerta_temprana"):
                    campos_actualizar.append("FechaAlertaTemprana = ?")
                    valores.append(track["fecha_alerta_temprana"])
                if track.get("informe_preliminar_enviado") is not None:
                    campos_actualizar.append("InformePreliminarEnviado = ?")
                    valores.append(1 if track["informe_preliminar_enviado"] else 0)
                if track.get("fecha_informe_preliminar"):
                    campos_actualizar.append("FechaInformePreliminar = ?")
                    valores.append(track["fecha_informe_preliminar"])
                if track.get("informe_completo_enviado") is not None:
                    campos_actualizar.append("InformeCompletoEnviado = ?")
                    valores.append(1 if track["informe_completo_enviado"] else 0)
                if track.get("fecha_informe_completo"):
                    campos_actualizar.append("FechaInformeCompleto = ?")
                    valores.append(track["fecha_informe_completo"])
                if track.get("plan_accion_enviado") is not None:
                    campos_actualizar.append("PlanAccionEnviado = ?")
                    valores.append(1 if track["plan_accion_enviado"] else 0)
                if track.get("fecha_plan_accion"):
                    campos_actualizar.append("FechaPlanAccion = ?")
                    valores.append(track["fecha_plan_accion"])
                if track.get("informe_final_enviado") is not None:
                    campos_actualizar.append("InformeFinalEnviado = ?")
                    valores.append(1 if track["informe_final_enviado"] else 0)
                if track.get("fecha_informe_final"):
                    campos_actualizar.append("FechaInformeFinal = ?")
                    valores.append(track["fecha_informe_final"])
        
        # Agregar campos de auditoría
        campos_actualizar.append("FechaActualizacion = GETDATE()")
        campos_actualizar.append("ModificadoPor = ?")
        valores.append(current_user.id if hasattr(current_user, 'id') else 'sistema')
        
        # Agregar ID del incidente al final para el WHERE
        valores.append(incidente_id)
        
        # 8. Ejecutar actualización
        if campos_actualizar:
            query = f"""
                UPDATE Incidentes 
                SET {', '.join(campos_actualizar)}
                WHERE IncidenteID = ?
            """
            cursor.execute(query, valores)
            
            # Registrar en auditoría
            cursor.execute("""
                INSERT INTO INCIDENTES_AUDITORIA 
                (IncidenteID, TipoAccion, DescripcionAccion, DatosNuevos, Usuario, FechaAccion)
                VALUES (?, 'ACTUALIZAR_ANCI', 'Actualización de campos ANCI', ?, ?, GETDATE())
            """, (
                incidente_id,
                json.dumps({
                    'campos_actualizados': len(campos_actualizar),
                    'tipo_reporte': tipo_reporte,
                    'validacion_anci': es_valido
                }, ensure_ascii=False),
                current_user.email if hasattr(current_user, 'email') else 'sistema'
            ))
            
            conn.commit()
        
        # 9. Preparar respuesta
        resultado = {
            'success': True,
            'incidente_id': incidente_id,
            'validacion_anci': {
                'es_valido': es_valido,
                'campos_faltantes': campos_faltantes if not es_valido else [],
                'tipo_reporte': tipo_reporte
            },
            'campos_actualizados': len(campos_actualizar) - 2,  # Excluir campos de auditoría
            'estructura_json': {
                'version': datos_json_final['metadata']['version_formato'],
                'timestamp': datos_json_final['metadata']['timestamp_actualizacion'],
                'hash': datos_json_final['metadata']['hash_integridad']
            }
        }
        
        return jsonify(resultado), 200
        
    except Exception as e:
        print(f"Error actualizando incidente ANCI: {e}")
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({
            'error': 'Error interno del servidor',
            'detalles': str(e)
        }), 500
        
    finally:
        if conn:
            conn.close()


def _actualizar_dict_recursivo(original, actualizacion):
    """
    Actualiza recursivamente un diccionario manteniendo valores existentes
    Solo actualiza valores que vienen en la actualización
    """
    for key, value in actualizacion.items():
        if key in original:
            if isinstance(value, dict) and isinstance(original[key], dict):
                _actualizar_dict_recursivo(original[key], value)
            elif value is not None:  # Solo actualizar si el valor no es None
                original[key] = value
        else:
            # Agregar nueva clave si no existe
            original[key] = value


@incidente_anci_actualizar_bp.route('/<int:incidente_id>/cargar-anci', methods=['GET'])
@login_required
def cargar_incidente_anci(incidente_id):
    """
    Carga un incidente ANCI con todos sus campos en formato estructurado
    """
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
        cursor = conn.cursor()
        
        # Obtener datos del incidente
        cursor.execute("""
            SELECT 
                i.IncidenteID, i.DatosIncidente, i.ReporteAnciID,
                i.FechaDeclaracionANCI, i.EstadoActual, i.Titulo,
                e.TipoEmpresa, e.RazonSocial
            FROM Incidentes i
            LEFT JOIN Empresas e ON i.EmpresaID = e.EmpresaID
            WHERE i.IncidenteID = ?
        """, (incidente_id,))
        
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Incidente no encontrado'}), 404
        
        # Verificar que es un incidente ANCI
        if not row[2]:  # ReporteAnciID
            return jsonify({'error': 'Este incidente no ha sido declarado como ANCI'}), 400
        
        # Cargar estructura JSON
        datos_json = None
        if row[1]:  # DatosIncidente
            try:
                datos_json = json.loads(row[1])
            except:
                datos_json = None
        
        # Si no hay JSON válido, crear estructura base y migrar campos
        if not datos_json:
            # Obtener todos los campos de la BD para migración
            cursor.execute("""
                SELECT * FROM Incidentes WHERE IncidenteID = ?
            """, (incidente_id,))
            
            incidente_completo = cursor.fetchone()
            columns = [column[0] for column in cursor.description]
            datos_bd = dict(zip(columns, incidente_completo))
            
            # Crear estructura base y migrar
            datos_json = UnificadorIncidentes.crear_estructura_incidente()
            datos_json = UnificadorIncidentes.migrar_campos_anci(datos_json, datos_bd)
        
        # Obtener resumen de taxonomías
        resumen_taxonomias = UnificadorIncidentes.obtener_resumen_taxonomias(datos_json)
        
        resultado = {
            'success': True,
            'incidente': {
                'id': row[0],
                'reporte_anci_id': row[2],
                'fecha_declaracion_anci': row[3].isoformat() if row[3] else None,
                'estado_actual': row[4],
                'titulo': row[5],
                'tipo_empresa': row[6],
                'razon_social': row[7],
                'estructura_json': datos_json,
                'resumen_taxonomias': resumen_taxonomias
            }
        }
        
        return jsonify(resultado), 200
        
    except Exception as e:
        print(f"Error cargando incidente ANCI: {e}")
        traceback.print_exc()
        return jsonify({
            'error': 'Error interno del servidor',
            'detalles': str(e)
        }), 500
        
    finally:
        if conn:
            conn.close()
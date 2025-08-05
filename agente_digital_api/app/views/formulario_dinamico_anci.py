#!/usr/bin/env python3
"""
API ENDPOINT PARA FORMULARIO DINÁMICO ANCI
==========================================
Este módulo maneja toda la lógica del formulario dinámico que se adapta
automáticamente a cambios en taxonomías y configuración ANCI.
"""

from flask import Blueprint, request, jsonify
from app.database import get_db_connection
from app.utils.auth import login_required
from app.utils.error_handlers import robust_endpoint
import json
import logging

# Crear blueprint
formulario_dinamico_bp = Blueprint('formulario_dinamico', __name__)

@formulario_dinamico_bp.route('/api/formulario-dinamico/configuracion/<int:empresa_id>', methods=['GET'])
@login_required
@robust_endpoint
def obtener_configuracion_dinamica(empresa_id):
    """
    Obtiene la configuración completa del formulario dinámico para una empresa específica.
    Se adapta automáticamente según si la empresa es OIV o PSE.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener información de la empresa
        cursor.execute("""
            SELECT EmpresaID, RazonSocial, TipoEmpresa
            FROM Empresas 
            WHERE EmpresaID = ? AND EstadoActivo = 1
        """, (empresa_id,))
        
        empresa = cursor.fetchone()
        if not empresa:
            return jsonify({'error': 'Empresa no encontrada o inactiva'}), 404
        
        # Generar formulario dinámico usando el procedimiento
        cursor.execute("""
            EXEC sp_GenerarFormularioDinamico 
                @EmpresaID = ?, 
                @IncluirTaxonomias = 1, 
                @OrdenarPor = 'NumeroOrden'
        """, (empresa_id,))
        
        # Obtener secciones del formulario
        secciones = []
        for row in cursor.fetchall():
            seccion = {
                'seccionId': row[0],
                'codigoSeccion': row[1],
                'tipoSeccion': row[2],
                'numeroOrden': row[3],
                'titulo': row[4],
                'descripcion': row[5],
                'camposJSON': json.loads(row[6]) if row[6] else {},
                'colorIndicador': row[7],
                'iconoSeccion': row[8],
                'maxComentarios': row[9],
                'maxArchivos': row[10],
                'maxSizeMB': row[11],
                'esObligatorio': bool(row[12]),
                'tipoEmpresa': row[13],
                'aplicaAEmpresa': bool(row[14]),
                'descripcionTipo': row[15],
                'numeroCampos': row[16]
            }
            secciones.append(seccion)
        
        # Obtener estadísticas del formulario
        cursor.execute("""
            SELECT * FROM vw_EstadisticasFormularioDinamico 
            WHERE TipoEmpresa = ?
        """, (empresa[2],))
        
        estadisticas = cursor.fetchone()
        
        # Respuesta completa
        resultado = {
            'empresa': {
                'id': empresa[0],
                'razonSocial': empresa[1],
                'tipoEmpresa': empresa[2]
            },
            'formulario': {
                'secciones': secciones,
                'totalSecciones': len(secciones),
                'estadisticas': {
                    'seccionesAplicables': estadisticas[2] if estadisticas else 0,
                    'seccionesFijas': estadisticas[3] if estadisticas else 0,
                    'taxonomiasAplicables': estadisticas[4] if estadisticas else 0,
                    'seccionesEspeciales': estadisticas[5] if estadisticas else 0,
                    'taxonomiasDisponibles': estadisticas[6] if estadisticas else 0
                }
            },
            'capacidades': {
                'maxArchivosTotal': len(secciones) * 10,
                'maxComentariosTotal': len(secciones) * 6,
                'maxSizeMBPorArchivo': 10
            },
            'metadata': {
                'timestamp': cursor.execute('SELECT GETDATE()').fetchone()[0].isoformat(),
                'version': '2.0',
                'dinamico': True
            }
        }
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': resultado
        })
        
    except Exception as e:
        logging.error(f"Error obteniendo configuración dinámica: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@formulario_dinamico_bp.route('/api/formulario-dinamico/taxonomias/<int:empresa_id>', methods=['GET'])
@login_required
@robust_endpoint
def obtener_taxonomias_empresa(empresa_id):
    """
    Obtiene las taxonomías aplicables a una empresa específica.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Usar función dinámica para obtener taxonomías
        cursor.execute("""
            SELECT * FROM fn_ObtenerTaxonomiasPorEmpresa(?)
            WHERE Aplica = 1
            ORDER BY Area, Efecto, Categoria
        """, (empresa_id,))
        
        taxonomias = []
        for row in cursor.fetchall():
            taxonomia = {
                'taxonomiaId': row[0],
                'area': row[1],
                'efecto': row[2],
                'subcategoria': row[3],
                'categoria': row[4],
                'aplicaTipoEmpresa': row[5],
                'descripcion': row[6],
                'codigoSeccion': row[7],
                'aplica': bool(row[8])
            }
            taxonomias.append(taxonomia)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'taxonomias': taxonomias,
                'total': len(taxonomias)
            }
        })
        
    except Exception as e:
        logging.error(f"Error obteniendo taxonomías: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@formulario_dinamico_bp.route('/api/formulario-dinamico/sincronizar', methods=['POST'])
@login_required
@robust_endpoint
def sincronizar_taxonomias():
    """
    Sincroniza manualmente las taxonomías con la configuración dinámica.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ejecutar sincronización
        cursor.execute("EXEC sp_SincronizarTaxonomiasDinamicas")
        
        # Obtener estadísticas después de la sincronización
        cursor.execute("""
            SELECT 
                COUNT(*) as TotalSecciones,
                SUM(CASE WHEN TipoSeccion = 'TAXONOMIA' THEN 1 ELSE 0 END) as TotalTaxonomias,
                SUM(CASE WHEN TipoSeccion = 'FIJA' THEN 1 ELSE 0 END) as SeccionesFijas
            FROM ANCI_SECCIONES_CONFIG
            WHERE Activo = 1
        """)
        
        stats = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Taxonomías sincronizadas exitosamente',
            'estadisticas': {
                'totalSecciones': stats[0],
                'totalTaxonomias': stats[1],
                'seccionesFijas': stats[2]
            }
        })
        
    except Exception as e:
        logging.error(f"Error sincronizando taxonomías: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@formulario_dinamico_bp.route('/api/formulario-dinamico/validar/<int:empresa_id>/<int:incidente_id>', methods=['GET'])
@login_required
@robust_endpoint
def validar_formulario_dinamico(empresa_id, incidente_id):
    """
    Valida un incidente usando el sistema dinámico de validación.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ejecutar validación dinámica
        cursor.execute("""
            DECLARE @Resultados NVARCHAR(MAX);
            EXEC sp_ValidarFormularioDinamico 
                @EmpresaID = ?, 
                @IncidenteID = ?, 
                @Resultados = @Resultados OUTPUT;
            SELECT @Resultados as ResultadosJSON;
        """, (empresa_id, incidente_id))
        
        # Obtener resultado JSON
        resultado_json = cursor.fetchone()[0]
        resultados = json.loads(resultado_json) if resultado_json else {}
        
        # Obtener detalle de validaciones
        cursor.nextset()
        validaciones_detalle = []
        for row in cursor.fetchall():
            validacion = {
                'seccion': row[0],
                'campo': row[1],
                'estado': row[2],
                'mensaje': row[3],
                'critico': bool(row[4])
            }
            validaciones_detalle.append(validacion)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'resumen': resultados,
                'validaciones': validaciones_detalle,
                'empresaId': empresa_id,
                'incidenteId': incidente_id
            }
        })
        
    except Exception as e:
        logging.error(f"Error validando formulario dinámico: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@formulario_dinamico_bp.route('/api/formulario-dinamico/guardar/<int:empresa_id>/<int:incidente_id>', methods=['POST'])
@login_required
@robust_endpoint
def guardar_formulario_dinamico(empresa_id, incidente_id):
    """
    Guarda los datos del formulario dinámico.
    """
    try:
        data = request.get_json()
        secciones_data = data.get('secciones', {})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Iterar sobre cada sección y guardar los datos
        for codigo_seccion, datos_seccion in secciones_data.items():
            # Obtener ID de la sección
            cursor.execute("""
                SELECT SeccionID FROM ANCI_SECCIONES_CONFIG 
                WHERE CodigoSeccion = ? AND Activo = 1
            """, (codigo_seccion,))
            
            seccion = cursor.fetchone()
            if not seccion:
                continue
            
            seccion_id = seccion[0]
            
            # Verificar si ya existe registro
            cursor.execute("""
                SELECT DatoID FROM INCIDENTES_SECCIONES_DATOS
                WHERE IncidenteID = ? AND SeccionID = ?
            """, (incidente_id, seccion_id))
            
            existe = cursor.fetchone()
            
            # Convertir datos a JSON
            datos_json = json.dumps(datos_seccion, ensure_ascii=False)
            
            if existe:
                # Actualizar
                cursor.execute("""
                    UPDATE INCIDENTES_SECCIONES_DATOS
                    SET DatosJSON = ?, 
                        FechaActualizacion = GETDATE(),
                        ActualizadoPor = ?
                    WHERE IncidenteID = ? AND SeccionID = ?
                """, (datos_json, request.user.get('username', 'sistema'), 
                      incidente_id, seccion_id))
            else:
                # Insertar
                cursor.execute("""
                    INSERT INTO INCIDENTES_SECCIONES_DATOS
                    (IncidenteID, SeccionID, DatosJSON, EstadoSeccion, 
                     FechaCreacion, ActualizadoPor)
                    VALUES (?, ?, ?, 'COMPLETADO', GETDATE(), ?)
                """, (incidente_id, seccion_id, datos_json, 
                      request.user.get('username', 'sistema')))
        
        # Actualizar campos principales del incidente si están presentes
        campos_principales = {}
        if 'SEC_1' in secciones_data:
            sec1_data = secciones_data['SEC_1']
            campos_principales.update({
                'Titulo': sec1_data.get('titulo'),
                'TipoFlujo': sec1_data.get('tipoFlujo'),
                'Criticidad': sec1_data.get('criticidad'),
                'FechaDeteccion': sec1_data.get('fechaDeteccion'),
                'AnciNombreReportante': sec1_data.get('nombreReportante'),
                'AnciCargoReportante': sec1_data.get('cargoReportante'),
                'AnciCorreoReportante': sec1_data.get('correoReportante'),
                'AnciTelefonoReportante': sec1_data.get('telefonoReportante')
            })
        
        # Actualizar campos del incidente si hay datos principales
        if campos_principales:
            set_clauses = []
            params = []
            
            for campo, valor in campos_principales.items():
                if valor is not None:
                    set_clauses.append(f"{campo} = ?")
                    params.append(valor)
            
            if set_clauses:
                params.append(incidente_id)
                update_query = f"""
                    UPDATE Incidentes 
                    SET {', '.join(set_clauses)}, FechaModificacion = GETDATE()
                    WHERE IncidenteID = ?
                """
                cursor.execute(update_query, params)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Formulario dinámico guardado exitosamente',
            'seccionesGuardadas': len(secciones_data)
        })
        
    except Exception as e:
        logging.error(f"Error guardando formulario dinámico: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@formulario_dinamico_bp.route('/api/formulario-dinamico/cargar/<int:empresa_id>/<int:incidente_id>', methods=['GET'])
@login_required
@robust_endpoint
def cargar_formulario_dinamico(empresa_id, incidente_id):
    """
    Carga los datos existentes de un incidente en formato dinámico.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener datos del incidente
        cursor.execute("""
            SELECT i.*, e.TipoEmpresa
            FROM Incidentes i
            INNER JOIN Empresas e ON i.EmpresaID = e.EmpresaID
            WHERE i.IncidenteID = ? AND i.EmpresaID = ?
        """, (incidente_id, empresa_id))
        
        incidente = cursor.fetchone()
        if not incidente:
            return jsonify({'error': 'Incidente no encontrado'}), 404
        
        # Obtener datos de secciones dinámicas
        cursor.execute("""
            SELECT 
                sc.CodigoSeccion,
                sd.DatosJSON,
                sd.EstadoSeccion,
                sd.PorcentajeCompletado,
                sd.FechaActualizacion
            FROM INCIDENTES_SECCIONES_DATOS sd
            INNER JOIN ANCI_SECCIONES_CONFIG sc ON sd.SeccionID = sc.SeccionID
            WHERE sd.IncidenteID = ?
        """, (incidente_id,))
        
        secciones_data = {}
        for row in cursor.fetchall():
            codigo_seccion = row[0]
            datos_json = json.loads(row[1]) if row[1] else {}
            
            secciones_data[codigo_seccion] = {
                'datos': datos_json,
                'estado': row[2],
                'porcentajeCompletado': row[3],
                'fechaActualizacion': row[4].isoformat() if row[4] else None
            }
        
        # Mapear campos principales a sección 1
        if 'SEC_1' not in secciones_data:
            secciones_data['SEC_1'] = {'datos': {}, 'estado': 'PENDIENTE'}
        
        # Agregar campos principales del incidente
        secciones_data['SEC_1']['datos'].update({
            'titulo': getattr(incidente, 'Titulo', ''),
            'tipoFlujo': getattr(incidente, 'TipoFlujo', ''),
            'criticidad': getattr(incidente, 'Criticidad', ''),
            'fechaDeteccion': getattr(incidente, 'FechaDeteccion', '').isoformat() if getattr(incidente, 'FechaDeteccion', None) else '',
            'nombreReportante': getattr(incidente, 'AnciNombreReportante', ''),
            'cargoReportante': getattr(incidente, 'AnciCargoReportante', ''),
            'correoReportante': getattr(incidente, 'AnciCorreoReportante', ''),
            'telefonoReportante': getattr(incidente, 'AnciTelefonoReportante', '')
        })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'incidente': {
                    'id': incidente_id,
                    'empresaId': empresa_id,
                    'tipoEmpresa': getattr(incidente, 'TipoEmpresa', '')
                },
                'secciones': secciones_data
            }
        })
        
    except Exception as e:
        logging.error(f"Error cargando formulario dinámico: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

# Registrar blueprint
def registrar_formulario_dinamico(app):
    """Registra el blueprint del formulario dinámico"""
    app.register_blueprint(formulario_dinamico_bp)
    print("✅ Blueprint formulario dinámico registrado")
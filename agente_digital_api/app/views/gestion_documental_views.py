from flask import Blueprint, request, jsonify, send_file, current_app
from datetime import datetime, timedelta
import os
import uuid
from werkzeug.utils import secure_filename
import json
import io
from ..modules.core.database import get_db_connection

gestion_documental_bp = Blueprint('gestion_documental', __name__, url_prefix='/api/gestion-documental')

# Configuración
UPLOAD_FOLDER = os.environ.get('DOCUMENTOS_PATH', '/archivos/documentos')
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'xlsx', 'txt', 'json'}

# Estructura de carpetas según especificación ANCI
ESTRUCTURA_CARPETAS = [
    {
        'id': 1,
        'codigo': '00_CONFIGURACION_SISTEMA',
        'nombre': 'Configuración del Sistema',
        'descripcion': 'Configuración y metadatos del cliente',
        'icono': 'ph ph-gear',
        'requerido': True,
        'orden': 0
    },
    {
        'id': 2,
        'codigo': '01_REGISTRO_ANCI',
        'nombre': 'Registro ANCI',
        'descripcion': 'Documentación del registro obligatorio ante ANCI',
        'icono': 'ph ph-identification-badge',
        'requerido': True,
        'orden': 1
    },
    {
        'id': 3,
        'codigo': '02_CLASIFICACION_ENTIDAD',
        'nombre': 'Clasificación Entidad',
        'descripcion': 'Gestión de la clasificación PSE/OIV',
        'icono': 'ph ph-buildings',
        'requerido': True,
        'orden': 2
    },
    {
        'id': 4,
        'codigo': '03_GOBERNANZA_SEGURIDAD',
        'nombre': 'Gobernanza y Seguridad',
        'descripcion': 'Políticas, procedimientos y documentos de gobernanza',
        'icono': 'ph ph-shield-check',
        'requerido': True,
        'orden': 3
    },
    {
        'id': 5,
        'codigo': '04_GESTION_INCIDENTES',
        'nombre': 'Gestión de Incidentes',
        'descripcion': 'Todo lo relacionado con incidentes de ciberseguridad',
        'icono': 'ph ph-warning-circle',
        'requerido': True,
        'orden': 4
    },
    {
        'id': 6,
        'codigo': '05_CONTRATOS_TERCEROS',
        'nombre': 'Contratos con Terceros',
        'descripcion': 'Gestión de contratos con proveedores críticos',
        'icono': 'ph ph-handshake',
        'requerido': True,
        'orden': 5
    },
    {
        'id': 7,
        'codigo': '06_CERTIFICACIONES',
        'nombre': 'Certificaciones',
        'descripcion': 'Gestión de certificaciones técnicas',
        'icono': 'ph ph-certificate',
        'requerido': False,
        'orden': 6
    },
    {
        'id': 8,
        'codigo': '07_AUDITORIAS_EVIDENCIAS',
        'nombre': 'Auditorías y Evidencias',
        'descripcion': 'Auditorías, simulacros y evidencias de cumplimiento',
        'icono': 'ph ph-magnifying-glass',
        'requerido': True,
        'orden': 7
    },
    {
        'id': 9,
        'codigo': '08_CAPACITACION_PERSONAL',
        'nombre': 'Capacitación del Personal',
        'descripcion': 'Programas de capacitación y concientización',
        'icono': 'ph ph-graduation-cap',
        'requerido': True,
        'orden': 8
    },
    {
        'id': 10,
        'codigo': '09_CONTINUIDAD_NEGOCIO',
        'nombre': 'Continuidad del Negocio',
        'descripcion': 'Planes de continuidad y recuperación',
        'icono': 'ph ph-arrows-clockwise',
        'requerido': True,
        'orden': 9
    },
    {
        'id': 11,
        'codigo': '10_COMUNICACION_ANCI',
        'nombre': 'Comunicación ANCI',
        'descripcion': 'Toda la comunicación oficial con ANCI',
        'icono': 'ph ph-envelope',
        'requerido': False,
        'orden': 10
    },
    {
        'id': 12,
        'codigo': '11_RESPALDOS_HISTORICOS',
        'nombre': 'Respaldos Históricos',
        'descripcion': 'Versiones históricas y respaldos',
        'icono': 'ph ph-archive',
        'requerido': False,
        'orden': 11
    }
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def crear_estructura_carpetas(empresa_id, rut_empresa):
    """Crea la estructura de carpetas para una empresa"""
    base_path = os.path.join(UPLOAD_FOLDER, f"CLIENTE_{rut_empresa}")
    
    for carpeta in ESTRUCTURA_CARPETAS:
        carpeta_path = os.path.join(base_path, carpeta['codigo'])
        os.makedirs(carpeta_path, exist_ok=True)
        
        # Crear archivo de configuración inicial
        config_file = os.path.join(carpeta_path, '.config.json')
        if not os.path.exists(config_file):
            with open(config_file, 'w') as f:
                json.dump({
                    'carpeta_id': carpeta['id'],
                    'nombre': carpeta['nombre'],
                    'creada': datetime.now().isoformat(),
                    'empresa_id': empresa_id
                }, f)

@gestion_documental_bp.route('/empresa/<int:empresa_id>', methods=['GET'])
def obtener_info_empresa(empresa_id):
    """Obtiene información de la empresa para gestión documental"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                e.EmpresaID, e.RazonSocial, e.RUT, e.TipoEmpresa,
                e.SectorEsencial, e.FechaCalificacion,
                COUNT(DISTINCT d.DocumentoID) as TotalDocumentos
            FROM Empresas e
            LEFT JOIN DOCUMENTOS_ANCI d ON e.EmpresaID = d.EmpresaID
            WHERE e.EmpresaID = ?
            GROUP BY e.EmpresaID, e.RazonSocial, e.RUT, e.TipoEmpresa, 
                     e.SectorEsencial, e.FechaCalificacion
        """
        cursor.execute(query, empresa_id)
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"error": "Empresa no encontrada"}), 404
        
        empresa = dict(zip([column[0] for column in cursor.description], result))
        
        # Crear estructura de carpetas si no existe
        crear_estructura_carpetas(empresa_id, empresa['RUT'])
        
        conn.close()
        return jsonify(empresa), 200
        
    except Exception as e:
        print(f"Error obteniendo empresa: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@gestion_documental_bp.route('/carpetas/<int:empresa_id>', methods=['GET'])
def obtener_carpetas(empresa_id):
    """Obtiene la estructura de carpetas con estadísticas"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Obtener RUT de la empresa
        cursor.execute("SELECT RUT FROM Empresas WHERE EmpresaID = ?", empresa_id)
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Empresa no encontrada"}), 404
        
        rut_empresa = result.RUT
        base_path = os.path.join(UPLOAD_FOLDER, f"CLIENTE_{rut_empresa}")
        
        carpetas_con_stats = []
        
        for carpeta in ESTRUCTURA_CARPETAS:
            # Contar documentos por carpeta
            query = """
                SELECT COUNT(*) as archivos, 
                       SUM(CASE WHEN FechaVencimiento < GETDATE() THEN 1 ELSE 0 END) as vencidos,
                       SUM(CASE WHEN FechaVencimiento BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE()) THEN 1 ELSE 0 END) as por_vencer
                FROM DOCUMENTOS_ANCI
                WHERE EmpresaID = ? AND CarpetaID = ?
            """
            cursor.execute(query, empresa_id, carpeta['id'])
            stats = cursor.fetchone()
            
            carpeta_info = carpeta.copy()
            carpeta_info['archivos'] = stats.archivos if stats else 0
            carpeta_info['alertas'] = (stats.vencidos + stats.por_vencer) if stats else 0
            
            carpetas_con_stats.append(carpeta_info)
        
        conn.close()
        return jsonify(carpetas_con_stats), 200
        
    except Exception as e:
        print(f"Error obteniendo carpetas: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@gestion_documental_bp.route('/documentos/<int:empresa_id>/<int:carpeta_id>', methods=['GET'])
def obtener_documentos(empresa_id, carpeta_id):
    """Obtiene los documentos de una carpeta específica"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                DocumentoID as id,
                NombreArchivo as nombre,
                TipoDocumento as tipo,
                FechaSubida as fechaSubida,
                FechaVencimiento as fechaVencimiento,
                CASE 
                    WHEN FechaVencimiento IS NULL THEN 'vigente'
                    WHEN FechaVencimiento < GETDATE() THEN 'vencido'
                    WHEN FechaVencimiento BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE()) THEN 'por_vencer'
                    ELSE 'vigente'
                END as estado,
                Descripcion as descripcion,
                SubidoPor as subidoPor
            FROM DOCUMENTOS_ANCI
            WHERE EmpresaID = ? AND CarpetaID = ?
            ORDER BY FechaSubida DESC
        """
        cursor.execute(query, empresa_id, carpeta_id)
        
        documentos = []
        for row in cursor.fetchall():
            doc = dict(zip([column[0] for column in cursor.description], row))
            # Convertir fechas a formato ISO
            if doc['fechaSubida']:
                doc['fechaSubida'] = doc['fechaSubida'].isoformat()
            if doc['fechaVencimiento']:
                doc['fechaVencimiento'] = doc['fechaVencimiento'].isoformat()
            documentos.append(doc)
        
        conn.close()
        return jsonify(documentos), 200
        
    except Exception as e:
        print(f"Error obteniendo documentos: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@gestion_documental_bp.route('/documentos/<int:empresa_id>', methods=['POST'])
def subir_documento(empresa_id):
    """Sube un nuevo documento"""
    if 'archivo' not in request.files:
        return jsonify({"error": "No se encontró archivo"}), 400
    
    archivo = request.files['archivo']
    if archivo.filename == '':
        return jsonify({"error": "No se seleccionó archivo"}), 400
    
    if not allowed_file(archivo.filename):
        return jsonify({"error": "Tipo de archivo no permitido"}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Obtener RUT de la empresa
        cursor.execute("SELECT RUT, RazonSocial FROM Empresas WHERE EmpresaID = ?", empresa_id)
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Empresa no encontrada"}), 404
        
        rut_empresa = result.RUT
        razon_social = result.RazonSocial
        
        # Datos del formulario
        carpeta_id = request.form.get('carpeta_id', type=int)
        tipo_documento = request.form.get('tipo')
        fecha_vencimiento = request.form.get('fecha_vencimiento')
        descripcion = request.form.get('descripcion', '')
        
        # Buscar carpeta
        carpeta = next((c for c in ESTRUCTURA_CARPETAS if c['id'] == carpeta_id), None)
        if not carpeta:
            return jsonify({"error": "Carpeta no válida"}), 400
        
        # Guardar archivo
        filename = secure_filename(archivo.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        carpeta_path = os.path.join(UPLOAD_FOLDER, f"CLIENTE_{rut_empresa}", carpeta['codigo'])
        os.makedirs(carpeta_path, exist_ok=True)
        
        filepath = os.path.join(carpeta_path, unique_filename)
        archivo.save(filepath)
        
        # Guardar en base de datos
        query = """
            INSERT INTO DOCUMENTOS_ANCI (
                EmpresaID, CarpetaID, NombreArchivo, RutaArchivo,
                TipoDocumento, FechaSubida, FechaVencimiento,
                Descripcion, SubidoPor, Hash, Activo
            ) VALUES (?, ?, ?, ?, ?, GETDATE(), ?, ?, ?, ?, 1)
        """
        
        # Calcular hash del archivo
        import hashlib
        with open(filepath, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        cursor.execute(query,
            empresa_id, carpeta_id, filename, filepath,
            tipo_documento, fecha_vencimiento if fecha_vencimiento else None,
            descripcion, 'Sistema', file_hash
        )
        conn.commit()
        
        # Registrar en auditoría
        cursor.execute("""
            INSERT INTO AUDITORIA_DOCUMENTOS (
                DocumentoID, Accion, Usuario, FechaAccion, Detalles
            ) VALUES (SCOPE_IDENTITY(), 'CREAR', ?, GETDATE(), ?)
        """, ('Sistema', f'Documento subido: {filename}'))
        conn.commit()
        
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Documento subido exitosamente",
            "filename": filename
        }), 201
        
    except Exception as e:
        print(f"Error subiendo documento: {e}")
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": "Error interno del servidor"}), 500

@gestion_documental_bp.route('/documentos/<int:documento_id>/ver', methods=['GET'])
def ver_documento(documento_id):
    """Permite ver un documento"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT RutaArchivo, NombreArchivo, TipoDocumento
            FROM DOCUMENTOS_ANCI
            WHERE DocumentoID = ? AND Activo = 1
        """
        cursor.execute(query, documento_id)
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"error": "Documento no encontrado"}), 404
        
        ruta_archivo = result.RutaArchivo
        nombre_archivo = result.NombreArchivo
        
        if not os.path.exists(ruta_archivo):
            return jsonify({"error": "Archivo físico no encontrado"}), 404
        
        # Registrar acceso
        cursor.execute("""
            INSERT INTO AUDITORIA_DOCUMENTOS (
                DocumentoID, Accion, Usuario, FechaAccion
            ) VALUES (?, 'VER', ?, GETDATE())
        """, (documento_id, 'Sistema'))
        conn.commit()
        conn.close()
        
        return send_file(ruta_archivo, as_attachment=False, download_name=nombre_archivo)
        
    except Exception as e:
        print(f"Error viendo documento: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@gestion_documental_bp.route('/documentos/<int:documento_id>/descargar', methods=['GET'])
def descargar_documento(documento_id):
    """Descarga un documento"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT RutaArchivo, NombreArchivo
            FROM DOCUMENTOS_ANCI
            WHERE DocumentoID = ? AND Activo = 1
        """
        cursor.execute(query, documento_id)
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"error": "Documento no encontrado"}), 404
        
        ruta_archivo = result.RutaArchivo
        nombre_archivo = result.NombreArchivo
        
        if not os.path.exists(ruta_archivo):
            return jsonify({"error": "Archivo físico no encontrado"}), 404
        
        # Registrar descarga
        cursor.execute("""
            INSERT INTO AUDITORIA_DOCUMENTOS (
                DocumentoID, Accion, Usuario, FechaAccion
            ) VALUES (?, 'DESCARGAR', ?, GETDATE())
        """, (documento_id, 'Sistema'))
        conn.commit()
        conn.close()
        
        return send_file(ruta_archivo, as_attachment=True, download_name=nombre_archivo)
        
    except Exception as e:
        print(f"Error descargando documento: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@gestion_documental_bp.route('/documentos/<int:documento_id>', methods=['DELETE'])
def eliminar_documento(documento_id):
    """Elimina un documento (soft delete)"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Marcar como inactivo (soft delete)
        query = """
            UPDATE DOCUMENTOS_ANCI 
            SET Activo = 0, FechaEliminacion = GETDATE()
            WHERE DocumentoID = ?
        """
        cursor.execute(query, documento_id)
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Documento no encontrado"}), 404
        
        # Registrar eliminación
        cursor.execute("""
            INSERT INTO AUDITORIA_DOCUMENTOS (
                DocumentoID, Accion, Usuario, FechaAccion
            ) VALUES (?, 'ELIMINAR', ?, GETDATE())
        """, (documento_id, 'Sistema'))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Documento eliminado"}), 200
        
    except Exception as e:
        print(f"Error eliminando documento: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@gestion_documental_bp.route('/metricas/<int:empresa_id>', methods=['GET'])
def obtener_metricas(empresa_id):
    """Obtiene métricas de cumplimiento documental"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Métricas generales
        query = """
            SELECT 
                COUNT(DISTINCT CarpetaID) as carpetas_con_docs,
                COUNT(*) as total_documentos,
                SUM(CASE WHEN FechaVencimiento < GETDATE() THEN 1 ELSE 0 END) as documentos_vencidos,
                SUM(CASE WHEN FechaVencimiento BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE()) THEN 1 ELSE 0 END) as proximos_vencer,
                SUM(CASE WHEN FechaVencimiento IS NULL OR FechaVencimiento > DATEADD(day, 30, GETDATE()) THEN 1 ELSE 0 END) as documentos_vigentes
            FROM DOCUMENTOS_ANCI
            WHERE EmpresaID = ? AND Activo = 1
        """
        cursor.execute(query, empresa_id)
        result = cursor.fetchone()
        
        if result:
            carpetas_con_docs = result.carpetas_con_docs or 0
            total_documentos = result.total_documentos or 0
            documentos_vencidos = result.documentos_vencidos or 0
            proximos_vencer = result.proximos_vencer or 0
            documentos_vigentes = result.documentos_vigentes or 0
        else:
            carpetas_con_docs = 0
            total_documentos = 0
            documentos_vencidos = 0
            proximos_vencer = 0
            documentos_vigentes = 0
        
        # Calcular cumplimiento global
        carpetas_requeridas = len([c for c in ESTRUCTURA_CARPETAS if c['requerido']])
        cumplimiento_global = int((carpetas_con_docs / carpetas_requeridas * 100)) if carpetas_requeridas > 0 else 0
        
        # Contar alertas críticas
        alertas_criticas = documentos_vencidos
        
        metricas = {
            'cumplimientoGlobal': cumplimiento_global,
            'alertasCriticas': alertas_criticas,
            'proximosVencimientos': proximos_vencer,
            'documentosActualizados': documentos_vigentes,
            'totalDocumentos': total_documentos,
            'carpetasConDocumentos': carpetas_con_docs,
            'carpetasRequeridas': carpetas_requeridas
        }
        
        conn.close()
        return jsonify(metricas), 200
        
    except Exception as e:
        print(f"Error obteniendo métricas: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@gestion_documental_bp.route('/alertas/<int:empresa_id>', methods=['GET'])
def obtener_alertas(empresa_id):
    """Obtiene alertas y notificaciones de la empresa"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        alertas = []
        
        # Alertas de documentos vencidos
        query_vencidos = """
            SELECT 
                d.DocumentoID, d.NombreArchivo, d.FechaVencimiento, d.CarpetaID,
                c.nombre as CarpetaNombre
            FROM DOCUMENTOS_ANCI d
            JOIN (VALUES %s) c(id, codigo, nombre) ON d.CarpetaID = c.id
            WHERE d.EmpresaID = ? AND d.Activo = 1 
            AND d.FechaVencimiento < GETDATE()
        """ % ','.join([f"({c['id']}, '{c['codigo']}', '{c['nombre']}')" for c in ESTRUCTURA_CARPETAS])
        
        cursor.execute(query_vencidos, empresa_id)
        
        for row in cursor.fetchall():
            alertas.append({
                'id': f"vencido_{row.DocumentoID}",
                'tipo': 'critica',
                'titulo': 'Documento Vencido',
                'mensaje': f"El documento '{row.NombreArchivo}' en {row.CarpetaNombre} venció el {row.FechaVencimiento.strftime('%d/%m/%Y')}",
                'fecha': row.FechaVencimiento.isoformat(),
                'carpeta_id': row.CarpetaID
            })
        
        # Alertas de documentos por vencer
        query_por_vencer = """
            SELECT 
                d.DocumentoID, d.NombreArchivo, d.FechaVencimiento, d.CarpetaID,
                DATEDIFF(day, GETDATE(), d.FechaVencimiento) as dias_restantes
            FROM DOCUMENTOS_ANCI d
            WHERE d.EmpresaID = ? AND d.Activo = 1 
            AND d.FechaVencimiento BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE())
        """
        
        cursor.execute(query_por_vencer, empresa_id)
        
        for row in cursor.fetchall():
            tipo_alerta = 'alta' if row.dias_restantes <= 7 else 'media'
            alertas.append({
                'id': f"por_vencer_{row.DocumentoID}",
                'tipo': tipo_alerta,
                'titulo': 'Documento Por Vencer',
                'mensaje': f"El documento '{row.NombreArchivo}' vence en {row.dias_restantes} días",
                'fecha': datetime.now().isoformat(),
                'carpeta_id': row.CarpetaID
            })
        
        # Alertas de carpetas sin documentos requeridos
        query_carpetas_vacias = """
            SELECT COUNT(*) FROM DOCUMENTOS_ANCI 
            WHERE EmpresaID = ? AND CarpetaID = ? AND Activo = 1
        """
        
        for carpeta in ESTRUCTURA_CARPETAS:
            if carpeta['requerido']:
                cursor.execute(query_carpetas_vacias, empresa_id, carpeta['id'])
                count = cursor.fetchone()[0]
                if count == 0:
                    alertas.append({
                        'id': f"carpeta_vacia_{carpeta['id']}",
                        'tipo': 'media',
                        'titulo': 'Carpeta Requerida Vacía',
                        'mensaje': f"La carpeta '{carpeta['nombre']}' es obligatoria y no contiene documentos",
                        'fecha': datetime.now().isoformat(),
                        'carpeta_id': carpeta['id']
                    })
        
        # Ordenar alertas por tipo (crítica > alta > media)
        orden_tipo = {'critica': 0, 'alta': 1, 'media': 2, 'baja': 3}
        alertas.sort(key=lambda x: orden_tipo.get(x['tipo'], 99))
        
        conn.close()
        return jsonify(alertas[:20]), 200  # Limitar a 20 alertas más importantes
        
    except Exception as e:
        print(f"Error obteniendo alertas: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@gestion_documental_bp.route('/checklist/<int:empresa_id>/<int:carpeta_id>', methods=['GET'])
def obtener_checklist(empresa_id, carpeta_id):
    """Obtiene el checklist de documentos requeridos para una carpeta"""
    # Definir checklists por carpeta
    checklists = {
        2: [  # 01_REGISTRO_ANCI
            {
                'id': 1,
                'nombre': 'Comprobante de Registro ANCI',
                'descripcion': 'Comprobante oficial del registro en la plataforma ANCI',
                'tipo_documento': 'comprobante_registro',
                'obligatorio': True
            },
            {
                'id': 2,
                'nombre': 'Designación de Encargado (FEA)',
                'descripcion': 'Documento de designación firmado con Firma Electrónica Avanzada',
                'tipo_documento': 'designacion_encargado',
                'obligatorio': True
            },
            {
                'id': 3,
                'nombre': 'Certificado de Vigencia de la Sociedad',
                'descripcion': 'Certificado actualizado de vigencia de la sociedad',
                'tipo_documento': 'certificado_vigencia_sociedad',
                'obligatorio': True
            },
            {
                'id': 4,
                'nombre': 'Certificado de Vigencia de Poderes',
                'descripcion': 'Certificado de vigencia de poderes del representante legal',
                'tipo_documento': 'certificado_vigencia_poderes',
                'obligatorio': True
            }
        ],
        4: [  # 03_GOBERNANZA_SEGURIDAD
            {
                'id': 5,
                'nombre': 'Política General de Seguridad',
                'descripcion': 'Política de seguridad de la información aprobada',
                'tipo_documento': 'politica_seguridad',
                'obligatorio': True
            },
            {
                'id': 6,
                'nombre': 'Manual SGSI',
                'descripcion': 'Manual del Sistema de Gestión de Seguridad de la Información (Solo OIV)',
                'tipo_documento': 'manual_sgsi',
                'obligatorio': False  # Solo para OIV
            },
            {
                'id': 7,
                'nombre': 'Matriz de Riesgos',
                'descripcion': 'Matriz de identificación y evaluación de riesgos',
                'tipo_documento': 'matriz_riesgos',
                'obligatorio': True
            }
        ]
        # ... más checklists por carpeta
    }
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Obtener tipo de empresa
        cursor.execute("SELECT TipoEmpresa FROM Empresas WHERE EmpresaID = ?", empresa_id)
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Empresa no encontrada"}), 404
        
        tipo_empresa = result.TipoEmpresa
        
        # Obtener checklist para la carpeta
        items_checklist = checklists.get(carpeta_id, [])
        
        # Verificar qué documentos ya están subidos
        for item in items_checklist:
            # Si es solo para OIV y la empresa no es OIV, marcar como no requerido
            if item['tipo_documento'] == 'manual_sgsi' and tipo_empresa != 'OIV':
                item['obligatorio'] = False
                item['completado'] = True
                item['documento'] = None
            else:
                query = """
                    SELECT TOP 1 DocumentoID, NombreArchivo, FechaSubida
                    FROM DOCUMENTOS_ANCI
                    WHERE EmpresaID = ? AND CarpetaID = ? 
                    AND TipoDocumento = ? AND Activo = 1
                    ORDER BY FechaSubida DESC
                """
                cursor.execute(query, empresa_id, carpeta_id, item['tipo_documento'])
                doc = cursor.fetchone()
                
                if doc:
                    item['completado'] = True
                    item['documento'] = {
                        'id': doc.DocumentoID,
                        'nombre': doc.NombreArchivo,
                        'fecha': doc.FechaSubida.isoformat(),
                        'tipo': item['tipo_documento']
                    }
                else:
                    item['completado'] = False
                    item['documento'] = None
        
        conn.close()
        return jsonify(items_checklist), 200
        
    except Exception as e:
        print(f"Error obteniendo checklist: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
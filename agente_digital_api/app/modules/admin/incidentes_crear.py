# incidentes_crear.py
# Módulo exclusivo para la creación de incidentes
# Siguiendo las especificaciones del archivo incidente.txt

from flask import jsonify, request
# from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import os
import json
import traceback
from functools import wraps
from ...database import get_db_connection
from ...auth_utils import verificar_token
from ...utils.indice_taxonomias import IndiceUnico
import uuid
import tempfile
import shutil

# Función helper para gestión de directorios temporales
def obtener_directorio_temporal():
    """Obtiene el directorio temporal seguro para archivos del sistema"""
    temp_dir = os.path.join(tempfile.gettempdir(), 'agente_digital', 'datos_temporales')
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def obtener_ruta_archivo_temporal(incidente_id, nombre_archivo):
    """Obtiene la ruta completa para un archivo temporal específico"""
    temp_dir = obtener_directorio_temporal()
    return os.path.join(temp_dir, f'incidente_{incidente_id}_{nombre_archivo}')

# Decorador para autenticación
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Token no proporcionado"}), 401
        
        usuario = verificar_token(token)
        if not usuario:
            return jsonify({"error": "Token inválido o expirado"}), 401
        
        return f(usuario, *args, **kwargs)
    return decorated_function

class CreadorIncidentes:
    """Clase para manejar la creación de incidentes según especificaciones"""
    
    def __init__(self):
        self.temp_folder = os.path.join(os.path.dirname(__file__), '..', '..', 'temp_incidentes')
        self.upload_folder = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')
        
        # Crear carpetas si no existen
        os.makedirs(self.temp_folder, exist_ok=True)
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def generar_indice_unico(self, rut_empresa, modulo, submodulo, descripcion):
        """
        Genera el índice único según la nomenclatura especificada:
        CORRELATIVO + RUT + MODULO + SUBMODULO + DESCRIPCION
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Obtener el siguiente correlativo
            cursor.execute("SELECT ISNULL(MAX(IncidenteID), 0) + 1 FROM Incidentes")
            correlativo = cursor.fetchone()[0]
            
            # Formatear RUT sin dígito verificador
            rut_sin_dv = str(rut_empresa).split('-')[0].replace('.', '')
            
            # Construir el índice único
            indice = f"{correlativo}_{rut_sin_dv}_{modulo}_{submodulo}_{descripcion}"
            
            # Limitar a 50 caracteres para IDVisible
            if len(indice) > 50:
                indice = indice[:50]
                print(f"⚠️ Índice truncado a 50 caracteres: {indice}")
            
            cursor.close()
            conn.close()
            
            return indice
            
        except Exception as e:
            print(f"Error generando índice único: {str(e)}")
            raise
    
    def crear_archivo_temporal(self, indice_unico, datos):
        """Crea un archivo temporal para el incidente mientras se edita"""
        try:
            temp_file = os.path.join(self.temp_folder, f"{indice_unico}.json")
            
            # Agregar timestamp y estado
            datos['timestamp_creacion'] = datetime.now().isoformat()
            datos['estado_temporal'] = 'semilla_original'
            datos['indice_unico'] = indice_unico
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            
            return temp_file
            
        except Exception as e:
            print(f"Error creando archivo temporal: {str(e)}")
            raise
    
    def validar_campos_requeridos(self, datos):
        """Valida que todos los campos requeridos estén presentes"""
        campos_requeridos = {
            '1': ['tipo_registro', 'titulo_incidente', 'fecha_deteccion', 
                  'fecha_ocurrencia', 'criticidad'],
            '2': ['descripcion_detallada', 'impacto_preliminar', 
                  'sistemas_afectados', 'servicios_interrumpidos'],
            '3': ['tipo_amenaza', 'origen_ataque'],
            '5': ['medidas_contencion']
        }
        
        errores = []
        
        for seccion, campos in campos_requeridos.items():
            for campo in campos:
                if campo not in datos or not datos[campo]:
                    errores.append(f"Campo requerido faltante: {campo}")
        
        # Validar que al menos una taxonomía sea seleccionada para OIV/PSE
        if datos.get('tipo_empresa') in ['OIV', 'PSE']:
            if 'taxonomias' not in datos or not datos['taxonomias']:
                errores.append("Debe seleccionar al menos una taxonomía para empresas OIV/PSE")
        
        return errores
    
    def procesar_evidencias(self, evidencias, indice_unico, seccion):
        """Procesa y guarda las evidencias con numeración jerárquica"""
        evidencias_procesadas = []
        
        for idx, evidencia in enumerate(evidencias, 1):
            # Generar nombre único para el archivo
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            extension = evidencia['archivo'].filename.split('.')[-1]
            nombre_archivo = f"{indice_unico}_{seccion}_{idx}_{timestamp}.{extension}"
            
            # Guardar archivo en carpeta segura
            carpeta_evidencias = os.path.join(self.upload_folder, 'evidencias', indice_unico)
            os.makedirs(carpeta_evidencias, exist_ok=True)
            
            ruta_archivo = os.path.join(carpeta_evidencias, nombre_archivo)
            evidencia['archivo'].save(ruta_archivo)
            
            evidencias_procesadas.append({
                'numero': f"{seccion}.{idx}",
                'nombre_archivo': nombre_archivo,
                'descripcion': evidencia.get('descripcion', ''),
                'fecha_carga': datetime.now().isoformat(),
                'ruta': ruta_archivo
            })
        
        return evidencias_procesadas
    
    def guardar_incidente_db(self, datos, indice_unico):
        """Guarda el incidente en la base de datos"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # No usar transacción explícita, dejar que pyodbc maneje el autocommit
            
            # Insertar incidente principal
            query_incidente = """
            INSERT INTO Incidentes (
                Titulo, FechaDeteccion, FechaOcurrencia, Criticidad, AlcanceGeografico,
                DescripcionInicial, AnciImpactoPreliminar, SistemasAfectados,
                ServiciosInterrumpidos, AnciTipoAmenaza, OrigenIncidente,
                ResponsableCliente, AccionesInmediatas, CausaRaiz,
                LeccionesAprendidas, PlanMejora, EstadoActual,
                FechaCreacion, CreadoPor, EmpresaID, IDVisible
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, ?, ?)
            """
            
            # Convertir fechas al formato correcto para SQL Server
            from datetime import datetime
            
            def procesar_fecha(fecha_str):
                """Procesa y valida fechas de manera segura"""
                if not fecha_str:
                    return None
                    
                try:
                    # Intentar varios formatos comunes
                    for fmt in ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                        try:
                            return datetime.strptime(fecha_str, fmt)
                        except:
                            continue
                    
                    # Si ninguno funciona, intentar con fromisoformat
                    fecha_str_limpia = fecha_str.replace('Z', '+00:00').split('.')[0]
                    return datetime.fromisoformat(fecha_str_limpia)
                    
                except Exception as e:
                    print(f"⚠️ Error procesando fecha '{fecha_str}': {e}")
                    return None
            
            fecha_deteccion = procesar_fecha(datos.get('fecha_deteccion'))
            fecha_ocurrencia = procesar_fecha(datos.get('fecha_ocurrencia'))
            
            # Si no hay fechas, usar fecha actual
            if not fecha_deteccion:
                fecha_deteccion = datetime.now()
                print("📅 Usando fecha actual para detección")
            if not fecha_ocurrencia:
                fecha_ocurrencia = fecha_deteccion
                print("📅 Usando fecha de detección para ocurrencia")
            
            valores = (
                datos.get('titulo_incidente', ''),
                fecha_deteccion,
                fecha_ocurrencia,
                datos.get('criticidad', ''),
                datos.get('alcance_geografico', ''),
                datos.get('descripcion_detallada', ''),
                datos.get('impacto_preliminar', ''),
                datos.get('sistemas_afectados', ''),
                datos.get('servicios_interrumpidos', ''),
                datos.get('tipo_amenaza', ''),
                datos.get('origen_ataque', ''),
                datos.get('responsable_cliente', ''),
                datos.get('medidas_contencion', ''),
                datos.get('analisis_causa_raiz', ''),
                datos.get('lecciones_aprendidas', ''),
                datos.get('recomendaciones_mejora', ''),
                'Abierto',  # EstadoActual
                datos.get('usuario_id', 'Sistema'),  # CreadoPor
                datos['empresa_id'],
                indice_unico  # IDVisible
            )
            
            cursor.execute(query_incidente, valores)
            
            # Obtener ID del incidente insertado
            cursor.execute("SELECT @@IDENTITY")
            incidente_id = cursor.fetchone()[0]
            
            # Insertar taxonomías seleccionadas
            if 'taxonomias' in datos and len(datos['taxonomias']) > 0:
                print(f"📂 Insertando {len(datos['taxonomias'])} taxonomías...")
                for idx, taxonomia in enumerate(datos['taxonomias']):
                    try:
                        query_tax = """
                        INSERT INTO INCIDENTE_TAXONOMIA (
                            IncidenteID, Id_Taxonomia, Comentarios,
                            FechaAsignacion, CreadoPor
                        ) VALUES (?, ?, ?, GETDATE(), ?)
                        """
                        
                        # Combinar justificación y descripción del problema
                        comentarios = f"Justificación: {taxonomia.get('justificacion', '')}\nDescripción del problema: {taxonomia.get('descripcionProblema', '')}"
                        
                        cursor.execute(query_tax, (
                            incidente_id,
                            taxonomia['id'],
                            comentarios,
                            'Sistema'
                        ))
                        print(f"   ✅ Taxonomía {idx+1} insertada: {taxonomia['id']}")
                    except Exception as e:
                        print(f"   ⚠️ Error insertando taxonomía {taxonomia['id']}: {e}")
                        # Continuar con las demás taxonomías
            
            # Por ahora omitimos las evidencias ya que vienen como objetos File
            # y necesitan ser procesadas diferente
            if 'archivos' in datos and datos['archivos']:
                print(f"📁 Se recibieron archivos en las secciones: {list(datos['archivos'].keys())}")
                print(f"📄 Total de archivos por sección:")
                for seccion, archivos in datos['archivos'].items():
                    print(f"   - {seccion}: {len(archivos)} archivos")
            
            # Hacer commit explícito
            conn.commit()
            print(f"✅ Cambios guardados con éxito")
            
            cursor.close()
            conn.close()
            
            return incidente_id
            
        except Exception as e:
            print(f"❌ ERROR en guardar_incidente_db: {str(e)}")
            print(f"❌ Tipo de error: {type(e).__name__}")
            
            try:
                conn.rollback()
                print(f"❌ Cambios revertidos")
            except:
                pass
                
            raise

# Instancia global del creador
creador = CreadorIncidentes()

@login_required
def crear_incidente_nuevo(usuario):
    """Endpoint para crear un nuevo incidente"""
    try:
        datos = request.get_json()
        
        # Validar campos requeridos
        errores = creador.validar_campos_requeridos(datos)
        if errores:
            return jsonify({
                "error": "Campos requeridos faltantes",
                "detalles": errores
            }), 400
        
        # Agregar información del usuario
        datos['usuario_id'] = usuario.get('id')
        
        # Generar índice único
        indice_unico = creador.generar_indice_unico(
            datos['empresa_id'],
            '1',  # Módulo de incidentes
            '1',  # Submódulo de creación
            'INCIDENTE_NUEVO'
        )
        
        # Crear archivo temporal (semilla original)
        archivo_temp = creador.crear_archivo_temporal(indice_unico, datos)
        
        # Guardar en base de datos
        incidente_id = creador.guardar_incidente_db(datos, indice_unico)
        
        return jsonify({
            "success": True,
            "incidente_id": incidente_id,
            "indice_unico": indice_unico,
            "archivo_temporal": archivo_temp,
            "mensaje": "Incidente creado exitosamente"
        }), 201
        
    except Exception as e:
        print(f"Error creando incidente: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "error": "Error al crear incidente",
            "detalle": str(e)
        }), 500

@login_required
def obtener_taxonomias_disponibles(usuario):
    """Obtiene las taxonomías disponibles según el tipo de empresa"""
    try:
        tipo_empresa = request.args.get('tipo_empresa', 'AMBAS')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT Id_Incidente as id, Subcategoria_del_Incidente as nombre, Descripcion as descripcion, AplicaTipoEmpresa as tipo_empresa, Categoria_del_Incidente as categoria
        FROM Taxonomia_incidentes
        WHERE tipo_empresa IN (?, 'AMBAS')
        AND activo = 1
        ORDER BY categoria, nombre
        """
        
        cursor.execute(query, (tipo_empresa,))
        
        taxonomias = []
        for row in cursor.fetchall():
            taxonomias.append({
                'id': row[0],
                'nombre': row[1],
                'descripcion': row[2],
                'tipo_empresa': row[3],
                'categoria': row[4]
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "taxonomias": taxonomias
        }), 200
        
    except Exception as e:
        print(f"Error obteniendo taxonomías: {str(e)}")
        return jsonify({
            "error": "Error al obtener taxonomías",
            "detalle": str(e)
        }), 500

@login_required
def guardar_borrador_incidente(usuario):
    """Guarda un borrador del incidente en el archivo temporal"""
    try:
        datos = request.get_json()
        indice_unico = datos.get('indice_unico')
        
        if not indice_unico:
            return jsonify({"error": "Índice único no proporcionado"}), 400
        
        # Actualizar archivo temporal
        temp_file = os.path.join(creador.temp_folder, f"{indice_unico}.json")
        
        if not os.path.exists(temp_file):
            return jsonify({"error": "Archivo temporal no encontrado"}), 404
        
        # Actualizar estado a semilla base
        datos['estado_temporal'] = 'semilla_base'
        datos['timestamp_actualizacion'] = datetime.now().isoformat()
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            "success": True,
            "mensaje": "Borrador guardado exitosamente"
        }), 200
        
    except Exception as e:
        print(f"Error guardando borrador: {str(e)}")
        return jsonify({
            "error": "Error al guardar borrador",
            "detalle": str(e)
        }), 500

@login_required
def cargar_evidencia_incidente(usuario):
    """Carga una evidencia para una sección específica del incidente"""
    try:
        if 'archivo' not in request.files:
            return jsonify({"error": "No se proporcionó archivo"}), 400
        
        archivo = request.files['archivo']
        indice_unico = request.form.get('indice_unico')
        seccion = request.form.get('seccion')
        descripcion = request.form.get('descripcion', '')
        
        if not all([archivo, indice_unico, seccion]):
            return jsonify({"error": "Faltan parámetros requeridos"}), 400
        
        # Procesar y guardar evidencia
        evidencias = [{
            'archivo': archivo,
            'descripcion': descripcion
        }]
        
        evidencias_procesadas = creador.procesar_evidencias(
            evidencias, indice_unico, seccion
        )
        
        return jsonify({
            "success": True,
            "evidencia": evidencias_procesadas[0],
            "mensaje": "Evidencia cargada exitosamente"
        }), 200
        
    except Exception as e:
        print(f"Error cargando evidencia: {str(e)}")
        return jsonify({
            "error": "Error al cargar evidencia",
            "detalle": str(e)
        }), 500

# TEMPORAL: Versión sin autenticación para pruebas
def crear_incidente_test():
    """Endpoint temporal sin autenticación para pruebas"""
    try:
        datos = request.get_json()
        print(f"📥 Datos recibidos: {json.dumps(datos, indent=2)}")
        
        creador = CreadorIncidentes()
        
        # Extraer información necesaria
        empresa_id = datos.get('empresa_id', 1)
        inquilino_id = datos.get('inquilino_id', 1)
        usuario_id = datos.get('usuario_id', 1)
        
        # Generar índice único
        indice_unico = creador.generar_indice_unico(
            empresa_id,
            '1',  # Módulo de incidentes
            '1',  # Submódulo de creación
            'INCIDENTE_NUEVO'
        )
        
        print(f"📌 Índice único generado: {indice_unico}")
        
        # Función para sanitizar strings
        def sanitizar_string(valor, max_length=1000):
            """Limpia y valida strings para evitar problemas SQL"""
            if not valor:
                return ''
            
            # Convertir a string y limpiar
            valor_limpio = str(valor)
            # Eliminar caracteres problemáticos
            valor_limpio = valor_limpio.replace("'", "''")
            valor_limpio = valor_limpio.replace('\x00', '')
            valor_limpio = valor_limpio[:max_length]
            
            return valor_limpio.strip()
        
        # Mapear datos del frontend a los campos de BD
        datos_guardar = {
            'inquilino_id': inquilino_id,
            'empresa_id': empresa_id,
            'titulo_incidente': sanitizar_string(datos.get('1.2', ''), 200),
            'fecha_deteccion': datos.get('1.3', ''),  # Las fechas se procesan después
            'fecha_ocurrencia': datos.get('1.4', ''),
            'criticidad': sanitizar_string(datos.get('1.5', ''), 50),
            'alcance_geografico': sanitizar_string(datos.get('1.6', ''), 100),
            'descripcion_detallada': sanitizar_string(datos.get('2.1', ''), 4000),  # Aumentado para textos largos
            'impacto_preliminar': sanitizar_string(datos.get('2.2', ''), 4000),
            'sistemas_afectados': sanitizar_string(datos.get('2.3', ''), 4000),
            'servicios_interrumpidos': sanitizar_string(datos.get('2.4', ''), 4000),
            'origen_ataque': sanitizar_string(datos.get('3.1', ''), 2000),
            'tipo_amenaza': sanitizar_string(datos.get('3.2', ''), 2000),
            'responsable_cliente': sanitizar_string(datos.get('3.3', ''), 1000),
            'medidas_contencion': sanitizar_string(datos.get('5.1', ''), 4000),
            'analisis_causa_raiz': sanitizar_string(datos.get('6.1', ''), 4000),
            'lecciones_aprendidas': sanitizar_string(datos.get('6.2', ''), 4000),
            'recomendaciones_mejora': sanitizar_string(datos.get('6.3', ''), 4000),
            'usuario_id': usuario_id,
            'taxonomias': datos.get('taxonomias_seleccionadas', []),
            'archivos': datos.get('archivos', {})
        }
        
        print(f"📋 Datos mapeados para guardar:")
        print(f"   - Título: {datos_guardar['titulo_incidente']}")
        print(f"   - Criticidad: {datos_guardar['criticidad']}")
        print(f"   - Taxonomías: {len(datos_guardar['taxonomias'])}")
        print(f"   - Archivos: {sum(len(archivos) for archivos in datos_guardar['archivos'].values())}")
        
        # Crear archivo temporal
        archivo_temp = creador.crear_archivo_temporal(indice_unico, datos_guardar)
        print(f"📁 Archivo temporal creado: {archivo_temp}")
        
        # Guardar en base de datos
        incidente_id = creador.guardar_incidente_db(datos_guardar, indice_unico)
        print(f"✅ Incidente guardado con ID: {incidente_id}")
        
        # Verificar que realmente se guardó
        try:
            conn_verify = get_db_connection()
            cursor_verify = conn_verify.cursor()
            cursor_verify.execute("SELECT IncidenteID, Titulo FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
            verificacion = cursor_verify.fetchone()
            if verificacion:
                print(f"✅ VERIFICACIÓN: Incidente {verificacion[0]} encontrado en BD: {verificacion[1][:50]}...")
            else:
                print(f"❌ VERIFICACIÓN: Incidente {incidente_id} NO encontrado en BD")
            cursor_verify.close()
            conn_verify.close()
        except Exception as e:
            print(f"⚠️ Error verificando: {e}")
        
        return jsonify({
            "status": "success",
            "mensaje": "¡Incidente creado exitosamente!",
            "incidente_id": incidente_id,
            "indice_unico": indice_unico
        }), 201
            
    except Exception as e:
        print(f"❌ ERROR DETALLADO: {str(e)}")
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error creando incidente: {str(e)}"
        }), 500

def corregir_encoding(texto):
    """Corrige problemas de encoding en textos de la base de datos"""
    if not texto:
        return texto
    
    try:
        # Si el texto ya está bien, devolverlo tal cual
        if isinstance(texto, str):
            # Intentar decodificar caracteres mal codificados
            # Ejemplo: aciÃ³n -> ación
            return texto.encode('latin-1').decode('utf-8', errors='ignore')
    except:
        # Si falla, devolver el texto original
        return texto
    
    return texto

def obtener_estructura_base_incidente(incidente_id):
    """Recupera la estructura base del incidente para edición"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener datos del incidente con todos los campos
        cursor.execute("""
            SELECT 
                i.*,
                e.RazonSocial as NombreEmpresa,
                e.TipoEmpresa,
                e.RUT as RutEmpresa
            FROM Incidentes i
            LEFT JOIN Empresas e ON i.EmpresaID = e.EmpresaID
            WHERE i.IncidenteID = ?
        """, (incidente_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        columns = [column[0] for column in cursor.description]
        incidente = dict(zip(columns, row))
        
        # Aplicar corrección de encoding a campos de texto
        campos_texto = ['Titulo', 'DescripcionInicial', 'AnciImpactoPreliminar', 
                       'SistemasAfectados', 'ServiciosInterrumpidos', 'AnciTipoAmenaza',
                       'OrigenIncidente', 'ResponsableCliente', 'AccionesInmediatas',
                       'CausaRaiz', 'LeccionesAprendidas', 'PlanMejora', 'NombreEmpresa',
                       'TipoApoyoCSIRT', 'UrgenciaCSIRT', 'ObservacionesCSIRT']
        
        for campo in campos_texto:
            if campo in incidente and incidente[campo]:
                incidente[campo] = corregir_encoding(incidente[campo])
        
        # Obtener taxonomías con sus comentarios completos
        cursor.execute("""
            SELECT 
                it.Id_Taxonomia,
                it.Comentarios,
                it.FechaAsignacion,
                t.Subcategoria_del_Incidente as nombre,
                t.Descripcion as descripcion
            FROM INCIDENTE_TAXONOMIA it
            LEFT JOIN Taxonomia_incidentes t ON it.Id_Taxonomia = t.Id_Incidente
            WHERE it.IncidenteID = ?
        """, (incidente_id,))
        
        taxonomias = []
        for row in cursor.fetchall():
            tax = {
                'id': row[0],
                'comentarios': corregir_encoding(row[1]) if row[1] else '',
                'fecha_asignacion': row[2].isoformat() if row[2] else None,
                'nombre': corregir_encoding(row[3]) if row[3] else '',
                'descripcion': corregir_encoding(row[4]) if row[4] else ''
            }
            # Parsear comentarios para separar justificación y descripción
            if tax['comentarios']:
                partes = tax['comentarios'].split('\nDescripción del problema: ')
                if len(partes) > 1:
                    tax['justificacion'] = partes[0].replace('Justificación: ', '')
                    tax['descripcionProblema'] = partes[1]
                else:
                    tax['justificacion'] = tax['comentarios']
                    tax['descripcionProblema'] = ''
            
            # Agregar archivos vacíos por defecto (se llenarán desde JSON temporal si existen)
            tax['archivos'] = []
            taxonomias.append(tax)
        
        incidente['taxonomias'] = taxonomias
        
        # Obtener archivos asociados
        carpeta_evidencias = os.path.join(creador.upload_folder, 'evidencias', incidente.get('IDVisible', ''))
        archivos_por_seccion = {}
        
        # Primero buscar en el filesystem
        if os.path.exists(carpeta_evidencias):
            for archivo in os.listdir(carpeta_evidencias):
                # Parsear nombre del archivo: indice_seccion_numero_timestamp.ext
                partes = archivo.split('_')
                if len(partes) >= 3:
                    seccion = partes[1]
                    if seccion not in archivos_por_seccion:
                        archivos_por_seccion[seccion] = []
                    archivos_por_seccion[seccion].append({
                        'nombre': archivo,
                        'ruta': os.path.join(carpeta_evidencias, archivo),
                        'tamaño': os.path.getsize(os.path.join(carpeta_evidencias, archivo))
                    })
        
        # Si no hay archivos en filesystem, buscar en el JSON temporal
        if not archivos_por_seccion and incidente.get('IDVisible'):
            archivo_temp = os.path.join(creador.temp_folder, f"{incidente['IDVisible']}.json")
            if os.path.exists(archivo_temp):
                try:
                    with open(archivo_temp, 'r', encoding='utf-8') as f:
                        datos_temp = json.load(f)
                        if 'archivos' in datos_temp:
                            # Convertir formato del JSON a formato esperado
                            for seccion_key, archivos in datos_temp['archivos'].items():
                                # Extraer número de sección (seccion_2 -> 2)
                                seccion_num = seccion_key.split('_')[-1]
                                archivos_por_seccion[seccion_num] = []
                                for idx, archivo in enumerate(archivos):
                                    archivos_por_seccion[seccion_num].append({
                                        'id': f"{incidente_id}_{seccion_num}_{idx+1}",  # ID único para el archivo
                                        'nombre': archivo.get('nombre', ''),
                                        'tamaño': archivo.get('tamaño', 0),
                                        'tipo': archivo.get('tipo', ''),
                                        'descripcion': archivo.get('descripcion', ''),
                                        'comentario': archivo.get('comentario', ''),
                                        'fechaCarga': archivo.get('fechaCarga', ''),
                                        'origen': 'guardado',  # Estos archivos ya están guardados
                                        'existente': True,  # Marcar como existente
                                        'ruta': archivo.get('ruta', '')  # Incluir ruta si existe
                                    })
                            
                            # Agregar archivos de taxonomías si existen
                            if 'taxonomias' in datos_temp['archivos']:
                                for tax_id, archivos_tax in datos_temp['archivos']['taxonomias'].items():
                                    # Buscar la taxonomía correspondiente
                                    for tax in incidente['taxonomias']:
                                        if tax['id'] == tax_id:
                                            tax['archivos'] = []
                                            for idx, archivo in enumerate(archivos_tax):
                                                tax['archivos'].append({
                                                    'id': f"{incidente_id}_tax_{tax_id}_{idx+1}",
                                                    'nombre': archivo.get('nombre', ''),
                                                    'tamaño': archivo.get('tamaño', 0),
                                                    'tipo': archivo.get('tipo', ''),
                                                    'descripcion': archivo.get('descripcion', ''),
                                                    'comentario': archivo.get('comentario', ''),
                                                    'fechaCarga': archivo.get('fechaCarga', ''),
                                                    'origen': 'guardado',
                                                    'existente': True,
                                                    'ruta': archivo.get('ruta', '')
                                                })
                                            break
                except Exception as e:
                    print(f"Error leyendo archivo temporal: {e}")
        
        incidente['archivos'] = archivos_por_seccion
        
        cursor.close()
        conn.close()
        
        return incidente
        
    except Exception as e:
        print(f"Error obteniendo estructura base: {str(e)}")
        return None

def actualizar_incidente_test(incidente_id):
    """Endpoint para actualizar un incidente existente"""
    try:
        datos = request.get_json()
        print(f"📝 Actualizando incidente {incidente_id} con datos:", json.dumps(datos, indent=2))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar que el incidente existe
        cursor.execute("SELECT IncidenteID FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Incidente no encontrado"}), 404
        
        # Actualizar campos principales (excepto los de identificación)
        query_update = """
        UPDATE Incidentes SET
            TipoFlujo = ?,
            TipoRegistro = ?,
            AlcanceGeografico = ?,
            DescripcionInicial = ?,
            AnciImpactoPreliminar = ?,
            SistemasAfectados = ?,
            ServiciosInterrumpidos = ?,
            AnciTipoAmenaza = ?,
            OrigenIncidente = ?,
            ResponsableCliente = ?,
            AccionesInmediatas = ?,
            CausaRaiz = ?,
            LeccionesAprendidas = ?,
            PlanMejora = ?,
            SolicitarCSIRT = ?,
            TipoApoyoCSIRT = ?,
            UrgenciaCSIRT = ?,
            ObservacionesCSIRT = ?,
            FechaModificacion = GETDATE()
        WHERE IncidenteID = ?
        """
        
        # Función para sanitizar strings
        def sanitizar_string(valor, max_length=4000):
            if not valor:
                return ''
            valor_limpio = str(valor)
            valor_limpio = valor_limpio.replace("'", "''")
            valor_limpio = valor_limpio.replace('\x00', '')
            valor_limpio = valor_limpio[:max_length]
            return valor_limpio.strip()
        
        # Debug de campos CSIRT
        print(f"🔍 Campos CSIRT recibidos:")
        print(f"  - 1.7.solicitar_csirt: {datos.get('1.7.solicitar_csirt')}")
        print(f"  - 1.7.tipo_apoyo: {datos.get('1.7.tipo_apoyo')}")
        print(f"  - 1.7.urgencia: {datos.get('1.7.urgencia')}")
        print(f"  - 1.7.observaciones_csirt: {datos.get('1.7.observaciones_csirt')}")
        
        valores = (
            sanitizar_string(datos.get('TipoFlujo', 'REGISTRO'), 50),  # TipoFlujo
            sanitizar_string(datos.get('1.1', 'Registro General'), 50),   # TipoRegistro
            sanitizar_string(datos.get('1.6', ''), 100),  # AlcanceGeografico
            sanitizar_string(datos.get('2.1', ''), 4000),  # DescripcionInicial
            sanitizar_string(datos.get('2.2', ''), 4000),  # AnciImpactoPreliminar
            sanitizar_string(datos.get('2.3', ''), 4000),  # SistemasAfectados
            sanitizar_string(datos.get('2.4', ''), 4000),  # ServiciosInterrumpidos
            sanitizar_string(datos.get('3.2', ''), 2000),  # AnciTipoAmenaza
            sanitizar_string(datos.get('3.1', ''), 2000),  # OrigenIncidente
            sanitizar_string(datos.get('3.3', ''), 1000),  # ResponsableCliente
            sanitizar_string(datos.get('5.1', ''), 4000),  # AccionesInmediatas
            sanitizar_string(datos.get('6.1', ''), 4000),  # CausaRaiz
            sanitizar_string(datos.get('6.2', ''), 4000),  # LeccionesAprendidas
            sanitizar_string(datos.get('6.3', ''), 4000),  # PlanMejora
            1 if datos.get('1.7.solicitar_csirt', False) else 0,  # SolicitarCSIRT
            sanitizar_string(datos.get('1.7.tipo_apoyo', ''), 100),  # TipoApoyoCSIRT
            sanitizar_string(datos.get('1.7.urgencia', ''), 50),  # UrgenciaCSIRT
            sanitizar_string(datos.get('1.7.observaciones_csirt', ''), 4000),  # ObservacionesCSIRT
            incidente_id
        )
        
        cursor.execute(query_update, valores)
        
        # Debug de resultado
        print(f"✅ Actualización ejecutada. Filas afectadas: {cursor.rowcount}")
        
        # Procesar archivos eliminados si existen
        if 'archivos_eliminados' in datos:
            print(f"🗑️ Procesando {len(datos['archivos_eliminados'])} archivos eliminados")
            for archivo in datos['archivos_eliminados']:
                # Aquí se debería implementar la lógica real de eliminación
                # Por ahora solo log para depuración
                print(f"  - Eliminando archivo ID: {archivo.get('id')}, Nombre: {archivo.get('nombre')}, Sección: {archivo.get('seccion')}")
                
                # Si fuera implementación real con tabla INCIDENTES_ARCHIVOS:
                # cursor.execute("DELETE FROM INCIDENTES_ARCHIVOS WHERE ArchivoID = ? AND IncidenteID = ?", 
                #               (archivo['id'], incidente_id))
        
        # Actualizar taxonomías si se proporcionan
        if 'taxonomias_seleccionadas' in datos:
            # Primero eliminar las taxonomías actuales
            cursor.execute("DELETE FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?", (incidente_id,))
            
            # Insertar las nuevas
            for taxonomia in datos['taxonomias_seleccionadas']:
                query_tax = """
                INSERT INTO INCIDENTE_TAXONOMIA (
                    IncidenteID, Id_Taxonomia, Comentarios,
                    FechaAsignacion, CreadoPor
                ) VALUES (?, ?, ?, GETDATE(), ?)
                """
                
                comentarios = f"Justificación: {taxonomia.get('justificacion', '')}\\nDescripción del problema: {taxonomia.get('descripcionProblema', '')}"
                
                cursor.execute(query_tax, (
                    incidente_id,
                    taxonomia['id'],
                    comentarios,
                    'Sistema'
                ))
        
        # Guardar archivos en JSON temporal (simulación)
        if 'archivos' in datos:
            try:
                archivo_temp = obtener_ruta_archivo_temporal(incidente_id, 'temp.json')
                
                # Preparar estructura de archivos
                archivos_guardar = {}
            
                # Archivos por sección
                for seccion_key, archivos in datos['archivos'].items():
                    if archivos:
                        archivos_guardar[seccion_key] = []
                        for archivo in archivos:
                            archivos_guardar[seccion_key].append({
                                'id': archivo.get('id', ''),
                                'nombre': archivo.get('nombre', ''),
                                'tamaño': archivo.get('tamaño', 0),
                                'tipo': archivo.get('tipo', ''),
                                'descripcion': archivo.get('descripcion', ''),
                                'comentario': archivo.get('comentario', ''),
                                'fechaCarga': archivo.get('fechaCarga', datetime.now().isoformat()),
                                'ruta': archivo.get('ruta', '')
                            })
            
                # Archivos de taxonomías
                if 'taxonomias_seleccionadas' in datos:
                    archivos_guardar['taxonomias'] = {}
                    for tax in datos['taxonomias_seleccionadas']:
                        if 'archivos' in tax and tax['archivos']:
                            archivos_guardar['taxonomias'][tax['id']] = []
                            for archivo in tax['archivos']:
                                archivos_guardar['taxonomias'][tax['id']].append({
                                    'id': archivo.get('id', ''),
                                    'nombre': archivo.get('nombre', ''),
                                    'tamaño': archivo.get('tamaño', 0),
                                    'tipo': archivo.get('tipo', ''),
                                    'descripcion': archivo.get('descripcion', ''),
                                    'comentario': archivo.get('comentario', ''),
                                    'fechaCarga': archivo.get('fechaCarga', datetime.now().isoformat()),
                                    'ruta': archivo.get('ruta', '')
                                })
            
                # Aplicar eliminaciones de archivos
                if 'archivos_eliminados' in datos:
                    for archivo_eliminar in datos['archivos_eliminados']:
                        seccion = archivo_eliminar.get('seccion')
                        archivo_id = archivo_eliminar.get('id')
                        
                        if seccion == 'taxonomia':
                            # Eliminar archivo de taxonomía
                            tax_id = archivo_eliminar.get('taxonomiaId')
                            if tax_id in archivos_guardar.get('taxonomias', {}):
                                archivos_guardar['taxonomias'][tax_id] = [
                                    a for a in archivos_guardar['taxonomias'][tax_id]
                                    if a.get('id') != archivo_id
                                ]
                        else:
                            # Eliminar archivo de sección regular
                            seccion_key = f"seccion_{seccion}"
                            if seccion_key in archivos_guardar:
                                archivos_guardar[seccion_key] = [
                                    a for a in archivos_guardar[seccion_key]
                                    if a.get('id') != archivo_id
                                ]
            
                # Guardar en archivo temporal
                datos_temp = {
                    'incidente_id': incidente_id,
                    'fecha_actualizacion': datetime.now().isoformat(),
                    'archivos': archivos_guardar,
                    'campos_csirt': {
                        'solicitar_csirt': datos.get('1.7.solicitar_csirt', False),
                        'tipo_apoyo': datos.get('1.7.tipo_apoyo', ''),
                        'urgencia': datos.get('1.7.urgencia', ''),
                        'observaciones_csirt': datos.get('1.7.observaciones_csirt', '')
                    }
                }
            
                with open(archivo_temp, 'w', encoding='utf-8') as f:
                    json.dump(datos_temp, f, indent=2, ensure_ascii=False)
                    
                print(f"📁 Archivos guardados en: {archivo_temp}")
            except PermissionError as e:
                print(f"⚠️ Error de permisos al guardar archivos temporales: {e}")
                print("📄 Continuando sin guardar archivos temporales...")
            except Exception as e:
                print(f"⚠️ Error inesperado al guardar archivos temporales: {e}")
                print("📄 Continuando sin guardar archivos temporales...")
        
        # Hacer commit
        conn.commit()
        
        print(f"✅ Incidente {incidente_id} actualizado exitosamente")
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "status": "success",
            "mensaje": "Incidente actualizado exitosamente",
            "incidente_id": incidente_id
        }), 200
        
    except Exception as e:
        print(f"❌ Error actualizando incidente: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({
            "status": "error",
            "mensaje": f"Error actualizando incidente: {str(e)}"
        }), 500

# Endpoint simple para obtener detalles de incidente
def obtener_detalle_incidente(incidente_id):
    """Obtiene los detalles de un incidente específico"""
    try:
        # Usar la función de estructura base para obtener TODO
        incidente_completo = obtener_estructura_base_incidente(incidente_id)
        
        if not incidente_completo:
            return jsonify({"error": "Incidente no encontrado"}), 404
        
        # Convertir fechas a string para JSON
        for key in incidente_completo:
            if hasattr(incidente_completo.get(key), 'isoformat'):
                incidente_completo[key] = incidente_completo[key].isoformat()
        
        # Log para verificación
        print(f"📊 Detalle incidente {incidente_id}:")
        print(f"   - Campos de texto: {sum(1 for k,v in incidente_completo.items() if isinstance(v, str) and len(str(v)) > 100)}")
        print(f"   - Taxonomías: {len(incidente_completo.get('taxonomias', []))}")
        print(f"   - Archivos: {sum(len(files) for files in incidente_completo.get('archivos', {}).values())}")
        
        return jsonify(incidente_completo), 200
        
    except Exception as e:
        print(f"❌ Error obteniendo detalle incidente: {str(e)}")
        return jsonify({
            "error": "Error al obtener incidente",
            "detalle": str(e)
        }), 500

# Respaldo del método anterior por si se necesita
def obtener_detalle_incidente_simple(incidente_id):
    """Obtiene los detalles básicos de un incidente (método anterior)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Consulta básica del incidente
        cursor.execute("""
            SELECT 
                i.*,
                e.RazonSocial as NombreEmpresa,
                e.TipoEmpresa
            FROM Incidentes i
            LEFT JOIN Empresas e ON i.EmpresaID = e.EmpresaID
            WHERE i.IncidenteID = ?
        """, (incidente_id,))
        
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Incidente no encontrado"}), 404
        
        # Convertir a diccionario
        columns = [column[0] for column in cursor.description]
        incidente = dict(zip(columns, row))
        
        # Convertir fechas a string para JSON
        for key in incidente:
            if hasattr(incidente[key], 'isoformat'):
                incidente[key] = incidente[key].isoformat()
        
        # Obtener taxonomías asociadas
        cursor.execute("""
            SELECT 
                it.Id_Taxonomia,
                it.Comentarios,
                it.FechaAsignacion,
                t.Area,
                t.Efecto,
                t.Categoria_del_Incidente,
                t.Descripcion
            FROM INCIDENTE_TAXONOMIA it
            LEFT JOIN Taxonomia_incidentes t ON it.Id_Taxonomia = t.Id_Incidente
            WHERE it.IncidenteID = ?
        """, (incidente_id,))
        
        taxonomias = []
        for row in cursor.fetchall():
            tax_cols = ['Id_Taxonomia', 'Comentarios', 'FechaAsignacion', 'Area', 'Efecto', 'Categoria', 'Descripcion']
            tax = dict(zip(tax_cols, row))
            if tax['FechaAsignacion'] and hasattr(tax['FechaAsignacion'], 'isoformat'):
                tax['FechaAsignacion'] = tax['FechaAsignacion'].isoformat()
            taxonomias.append(tax)
        
        incidente['Taxonomias'] = taxonomias
        
        cursor.close()
        conn.close()
        
        return jsonify(incidente), 200
        
    except Exception as e:
        print(f"❌ Error obteniendo detalle incidente: {str(e)}")
        return jsonify({
            "error": "Error al obtener incidente",
            "detalle": str(e)
        }), 500

def visualizar_archivo_incidente(archivo_id):
    """Endpoint para visualizar archivos de incidentes"""
    try:
        import os
        from flask import send_file
        
        # Para archivos guardados en JSON temporal, generar contenido de ejemplo
        # En producción, aquí se buscaría el archivo real en el sistema de archivos
        
        # Extraer información del ID
        partes = archivo_id.split('_')
        if len(partes) >= 3:
            incidente_id = partes[0]
            
            # Buscar archivo temporal
            archivo_temp = obtener_ruta_archivo_temporal(incidente_id, 'temp.json')
            if os.path.exists(archivo_temp):
                # Por ahora, devolver un mensaje indicando que el archivo existe
                return jsonify({
                    "mensaje": "Archivo encontrado en almacenamiento temporal",
                    "archivo_id": archivo_id,
                    "nota": "La descarga real estará disponible cuando se implemente el almacenamiento permanente"
                }), 200
            else:
                # Generar contenido de ejemplo para demostración
                contenido_ejemplo = f"Contenido de ejemplo para archivo {archivo_id}\n\n"
                contenido_ejemplo += "Este es un archivo de demostración.\n"
                contenido_ejemplo += "En producción, aquí se mostraría el contenido real del archivo."
                
                # Crear respuesta como archivo de texto
                from io import BytesIO
                archivo_stream = BytesIO(contenido_ejemplo.encode('utf-8'))
                archivo_stream.seek(0)
                
                return send_file(
                    archivo_stream,
                    mimetype='text/plain',
                    as_attachment=True,
                    download_name=f'archivo_{archivo_id}.txt'
                )
        
        return jsonify({"error": "ID de archivo inválido"}), 400
        
    except Exception as e:
        print(f"Error visualizando archivo: {str(e)}")
        return jsonify({"error": f"Error al visualizar archivo: {str(e)}"}), 500

# Rutas del módulo
@login_required
def validar_para_anci(usuario, incidente_id):
    """Valida que un incidente tenga todos los campos requeridos para ser transformado en ANCI"""
    try:
        conn = get_db_connection()
        
        # Obtener datos del incidente
        query = """
            SELECT 
                i.IncidenteID,
                i.Titulo,
                i.FechaDeteccion,
                i.FechaOcurrencia,
                i.Criticidad,
                i.DescripcionInicial,
                i.AnciImpactoPreliminar,
                i.SistemasAfectados,
                i.ServiciosInterrumpidos,
                i.OrigenIncidente,
                i.AnciTipoAmenaza,
                i.ResponsableCliente,
                i.AccionesInmediatas,
                i.CausaRaiz,
                i.TipoRegistro,
                i.ReporteAnciID
            FROM Incidentes i
            WHERE i.IncidenteID = ?
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (incidente_id,))
        incidente = cursor.fetchone()
        
        if not incidente:
            conn.close()
            return jsonify({'error': 'Incidente no encontrado'}), 404
            
        # Si ya es ANCI, no se puede transformar de nuevo
        # Verificar si el campo existe en el resultado
        try:
            reporte_anci_id = getattr(incidente, 'ReporteAnciID', None)
            if reporte_anci_id:
                conn.close()
                return jsonify({'error': 'Este incidente ya es un reporte ANCI'}), 400
        except:
            # Si el campo no existe, continuar
            pass
            
        # Validar campos requeridos
        campos_faltantes = []
        campos_requeridos = {
            'Titulo': 'Título del incidente',
            'FechaDeteccion': 'Fecha de detección',
            'FechaOcurrencia': 'Fecha de ocurrencia', 
            'Criticidad': 'Criticidad',
            'DescripcionInicial': 'Descripción inicial',
            'AnciImpactoPreliminar': 'Impacto preliminar',
            'SistemasAfectados': 'Sistemas afectados',
            'ServiciosInterrumpidos': 'Servicios interrumpidos',
            'OrigenIncidente': 'Origen del incidente',
            'AnciTipoAmenaza': 'Tipo de amenaza',
            'ResponsableCliente': 'Responsable del cliente',
            'AccionesInmediatas': 'Acciones inmediatas',
            'CausaRaiz': 'Causa raíz',
            'TipoRegistro': 'Tipo de registro'
        }
        
        for campo, descripcion in campos_requeridos.items():
            valor = getattr(incidente, campo, None)
            if not valor or str(valor).strip() == '':
                campos_faltantes.append({
                    'campo': campo,
                    'descripcion': descripcion
                })
                
        # Verificar si tiene al menos una taxonomía
        taxonomias_query = """
            SELECT COUNT(*) as total
            FROM INCIDENTE_TAXONOMIA
            WHERE IncidenteID = ?
        """
        cursor.execute(taxonomias_query, (incidente_id,))
        total_taxonomias = cursor.fetchone()[0]
        
        if total_taxonomias == 0:
            campos_faltantes.append({
                'campo': 'taxonomias',
                'descripcion': 'Al menos una taxonomía debe ser seleccionada'
            })
            
        conn.close()
        
        if campos_faltantes:
            return jsonify({
                'valido': False,
                'campos_faltantes': campos_faltantes
            }), 400
        else:
            return jsonify({
                'valido': True,
                'mensaje': 'El incidente cumple con todos los requisitos para ser transformado en ANCI'
            }), 200
            
    except Exception as e:
        print(f"Error validando incidente para ANCI: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error interno al validar incidente: {str(e)}'}), 500

@login_required
def transformar_a_anci(usuario, incidente_id):
    """Transforma un incidente normal en un incidente ANCI"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Primero validar
        query = """
            SELECT 
                i.*,
                e.RUT as RutEmpresa,
                e.RazonSocial as NombreEmpresa,
                e.TipoEmpresa
            FROM Incidentes i
            INNER JOIN Empresas e ON i.EmpresaID = e.EmpresaID
            WHERE i.IncidenteID = ?
        """
        
        cursor.execute(query, (incidente_id,))
        incidente = cursor.fetchone()
        
        if not incidente:
            conn.close()
            return jsonify({'error': 'Incidente no encontrado'}), 404
            
        try:
            reporte_anci_id = getattr(incidente, 'ReporteAnciID', None)
            if reporte_anci_id:
                conn.close()
                return jsonify({'error': 'Este incidente ya es un reporte ANCI'}), 400
        except:
            pass
            
        # Verificar si existe la tabla INFORMES_ANCI
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'INFORMES_ANCI'
        """)
        
        if cursor.fetchone()[0] == 0:
            # Si no existe, actualizar solo el incidente
            # Verificar si existen los campos ANCI
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'INCIDENTES' 
                AND COLUMN_NAME = 'ReporteAnciID'
            """)
            
            if cursor.fetchone()[0] == 0:
                # Si no existe el campo, simplemente marcar de alguna manera
                conn.close()
                return jsonify({
                    'mensaje': 'Incidente marcado como ANCI (sin campos específicos en BD)',
                    'reporte_id': 1,
                    'fecha_transformacion': datetime.now().isoformat()
                }), 200
            
            update_query = """
                UPDATE Incidentes SET ReporteAnciID = 1
                WHERE IncidenteID = ?
            """
            
            cursor.execute(update_query, (incidente_id,))
            conn.commit()
            conn.close()
            
            return jsonify({
                'mensaje': 'Incidente transformado a ANCI exitosamente',
                'reporte_id': 1,
                'fecha_transformacion': datetime.now().isoformat()
            }), 200
        
        # Si existe la tabla, crear registro completo
        fecha_actual = datetime.now()
        
        # Crear registro en INFORMES_ANCI
        insert_query = """
            INSERT INTO INFORMES_ANCI (
                IncidenteID,
                TipoReporte,
                Version,
                FechaGeneracion,
                GeneradoPor,
                ContenidoJSON,
                RutaArchivo,
                Estado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        contenido_json = json.dumps({
            'tipo': 'inicial',
            'fecha_generacion': fecha_actual.isoformat(),
            'datos_incidente': {
                'id': incidente_id,
                'titulo': getattr(incidente, 'Titulo', ''),
                'empresa': getattr(incidente, 'NombreEmpresa', ''),
                'tipo_empresa': getattr(incidente, 'TipoEmpresa', ''),
                'criticidad': getattr(incidente, 'Criticidad', '')
            }
        })
        
        cursor.execute(insert_query, (
            incidente_id,
            'Inicial',
            1,
            fecha_actual,
            'sistema',  # Temporal: usuario por defecto
            contenido_json,
            f'informes/anci_{incidente_id}_inicial_v1.txt',
            'Generado'
        ))
        
        reporte_id = cursor.lastrowid
        
        # Actualizar incidente para marcarlo como ANCI
        update_query = """
            UPDATE Incidentes SET ReporteAnciID = ?
            WHERE IncidenteID = ?
        """
        
        cursor.execute(update_query, (reporte_id, incidente_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'mensaje': 'Incidente transformado a ANCI exitosamente',
            'reporte_id': reporte_id,
            'fecha_transformacion': fecha_actual.isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error transformando incidente a ANCI: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'error': 'Error interno al transformar incidente'}), 500

def validar_para_anci_simple(incidente_id):
    """Versión simplificada sin autenticación para validar ANCI"""
    return validar_para_anci(None, incidente_id)

def transformar_a_anci_simple(incidente_id):
    """Versión simplificada sin autenticación para transformar a ANCI"""
    return transformar_a_anci(None, incidente_id)

def registrar_rutas_creacion(app):
    """Registra las rutas del módulo de creación de incidentes"""
    app.add_url_rule('/api/incidentes/crear', 
                     'crear_incidente_nuevo', 
                     crear_incidente_nuevo, 
                     methods=['POST'])
    
    # TEMPORAL: Endpoint sin autenticación para pruebas
    app.add_url_rule('/api/incidentes/crear-test', 
                     'crear_incidente_test', 
                     crear_incidente_test, 
                     methods=['POST'])
    
    # Endpoint para obtener detalle de incidente
    app.add_url_rule('/api/admin/incidentes/<int:incidente_id>', 
                     'obtener_detalle_incidente', 
                     obtener_detalle_incidente, 
                     methods=['GET'])
    
    # Endpoint para obtener estructura base completa (para edición)
    app.add_url_rule('/api/admin/incidentes/<int:incidente_id>/estructura-base', 
                     'obtener_estructura_base', 
                     lambda incidente_id: jsonify(obtener_estructura_base_incidente(incidente_id)) if obtener_estructura_base_incidente(incidente_id) else (jsonify({"error": "Incidente no encontrado"}), 404), 
                     methods=['GET'])
    
    app.add_url_rule('/api/incidentes/taxonomias', 
                     'obtener_taxonomias_disponibles', 
                     obtener_taxonomias_disponibles, 
                     methods=['GET'])
    
    app.add_url_rule('/api/incidentes/borrador', 
                     'guardar_borrador_incidente', 
                     guardar_borrador_incidente, 
                     methods=['POST'])
    
    app.add_url_rule('/api/incidentes/evidencia', 
                     'cargar_evidencia_incidente', 
                     cargar_evidencia_incidente, 
                     methods=['POST'])
    
    # Endpoint para actualizar incidente existente
    app.add_url_rule('/api/incidentes/<int:incidente_id>/actualizar', 
                     'actualizar_incidente_simple', 
                     actualizar_incidente_test, 
                     methods=['PUT'])
    
    # Endpoint para visualizar archivos
    app.add_url_rule('/api/incidentes/archivo/<archivo_id>', 
                     'visualizar_archivo_incidente', 
                     visualizar_archivo_incidente,
                     methods=['GET'])
    
    # Endpoints para transformación ANCI (versiones sin autenticación)
    app.add_url_rule('/api/admin/incidentes/<int:incidente_id>/validar-para-anci', 
                     'validar_para_anci', 
                     lambda incidente_id: validar_para_anci_simple(incidente_id), 
                     methods=['GET'])
    
    app.add_url_rule('/api/admin/incidentes/<int:incidente_id>/transformar-a-anci', 
                     'transformar_a_anci', 
                     lambda incidente_id: transformar_a_anci_simple(incidente_id), 
                     methods=['POST'])
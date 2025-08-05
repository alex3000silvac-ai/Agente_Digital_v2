# __init__.py
"""
Módulo Principal de Gestión de Incidentes
Orquesta todos los submódulos para garantizar formato unificado
Compatible con el flujo completo hasta el informe ANCI
"""

from flask import Blueprint, jsonify, request
from functools import wraps
from datetime import datetime
from typing import Dict, List, Optional
import json
import os

# Importar submódulos
from .unificador import UnificadorIncidentes
from .validador import ValidadorIncidentes
from .gestor_taxonomias import GestorTaxonomias
from .gestor_evidencias import GestorEvidencias

# Importar utilidades del sistema
from ...database import get_db_connection
from ...auth_utils import verificar_token

# Crear Blueprint principal
incidentes_unificado_bp = Blueprint('incidentes_unificado', __name__, 
                                   url_prefix='/api/incidentes/v2')

# Decorador de autenticación
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

class IncidentesManager:
    """
    Gestor principal que coordina todas las operaciones de incidentes
    """
    
    def __init__(self):
        self.unificador = UnificadorIncidentes
        self.validador = ValidadorIncidentes
        self.gestor_taxonomias = GestorTaxonomias()
        self.gestor_evidencias = GestorEvidencias()
        self.ruta_temp = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'temp_incidentes'
        )
        os.makedirs(self.ruta_temp, exist_ok=True)
    
    def crear_incidente(self, datos: Dict, usuario: Dict) -> Dict:
        """
        Crea un nuevo incidente con formato unificado
        
        Args:
            datos: Datos del incidente
            usuario: Información del usuario
            
        Returns:
            Resultado de la operación
        """
        try:
            # 1. Crear estructura unificada
            incidente = self.unificador.crear_estructura_incidente(datos)
            
            # 2. Validar estructura completa
            es_valido, errores = self.validador.validar_incidente_completo(
                incidente, validar_archivos=False
            )
            
            if not es_valido:
                return {
                    "exito": False,
                    "errores": errores,
                    "mensaje": "Datos del incidente no válidos"
                }
            
            # 3. Generar índice único
            indice_unico = self._generar_indice_unico(
                datos.get("empresa_id"),
                incidente["2"]["titulo"]
            )
            
            # 4. Guardar en BD
            resultado_bd = self._guardar_incidente_bd(
                incidente, indice_unico, usuario["id"]
            )
            
            if not resultado_bd["exito"]:
                return resultado_bd
            
            incidente_id = resultado_bd["incidente_id"]
            
            # 5. Crear archivo temporal (semilla original)
            archivo_temp = os.path.join(self.ruta_temp, f"{indice_unico}.json")
            incidente["metadata"]["estado_temporal"] = "semilla_original"
            
            with open(archivo_temp, 'w', encoding='utf-8') as f:
                json.dump(incidente, f, ensure_ascii=False, indent=2)
            
            # 6. Procesar taxonomías si existen
            if incidente["4"]["taxonomias"]["seleccionadas"]:
                for tax in incidente["4"]["taxonomias"]["seleccionadas"]:
                    if tax["estado"] == "activo":
                        self.gestor_taxonomias.asignar_taxonomia_incidente(
                            incidente_id,
                            tax["taxonomia_id"],
                            tax.get("datos", {}).get("comentarios", ""),
                            usuario["id"]
                        )
            
            return {
                "exito": True,
                "incidente_id": incidente_id,
                "indice_unico": indice_unico,
                "mensaje": "Incidente creado correctamente"
            }
            
        except Exception as e:
            return {
                "exito": False,
                "error": str(e),
                "mensaje": "Error creando incidente"
            }
    
    def obtener_incidente_edicion(self, indice_unico: str, usuario: Dict) -> Dict:
        """
        Obtiene incidente para edición con formato unificado
        
        Args:
            indice_unico: Índice único del incidente
            usuario: Información del usuario
            
        Returns:
            Datos del incidente o error
        """
        try:
            # 1. Verificar con diagnóstico
            puede_editar, diagnostico = self.validador.integrar_con_diagnostico(indice_unico)
            
            if not puede_editar:
                # Intentar reparar
                from ..admin.diagnostico_incidentes import diagnosticador
                reparacion = diagnosticador.reparar_estructura(indice_unico)
                
                if not reparacion["exito"]:
                    return {
                        "exito": False,
                        "error": "Incidente no puede ser editado",
                        "diagnostico": diagnostico
                    }
            
            # 2. Obtener de BD
            incidente_bd = self._obtener_incidente_bd(indice_unico)
            if not incidente_bd:
                return {
                    "exito": False,
                    "error": "Incidente no encontrado"
                }
            
            # 3. Cargar o crear estructura temporal
            archivo_temp = os.path.join(self.ruta_temp, f"{indice_unico}.json")
            
            if os.path.exists(archivo_temp):
                # Cargar existente
                with open(archivo_temp, 'r', encoding='utf-8') as f:
                    incidente = json.load(f)
                
                # Actualizar a formato actual si es necesario
                incidente = self.unificador.importar_desde_bd(incidente)
            else:
                # Crear desde BD
                incidente = self._convertir_bd_a_formato(incidente_bd)
            
            # 4. Actualizar estado temporal
            incidente["metadata"]["estado_temporal"] = "en_edicion"
            incidente["metadata"]["timestamp_actualizacion"] = datetime.now().isoformat()
            
            # 5. Sincronizar taxonomías
            resultado_sync = self.gestor_taxonomias.sincronizar_con_json(
                incidente_bd["IncidenteID"], incidente
            )
            
            # 6. Obtener evidencias
            evidencias = self.gestor_evidencias.obtener_evidencias_incidente(
                incidente_bd["IncidenteID"]
            )
            
            # 7. Actualizar evidencias en estructura
            self._actualizar_evidencias_estructura(incidente, evidencias)
            
            # 8. Guardar versión actualizada
            with open(archivo_temp, 'w', encoding='utf-8') as f:
                json.dump(incidente, f, ensure_ascii=False, indent=2)
            
            return {
                "exito": True,
                "incidente": incidente,
                "incidente_id": incidente_bd["IncidenteID"],
                "empresa_id": incidente_bd["EmpresaID"],
                "diagnostico": diagnostico
            }
            
        except Exception as e:
            return {
                "exito": False,
                "error": str(e),
                "mensaje": "Error obteniendo incidente para edición"
            }
    
    def guardar_incidente(self, indice_unico: str, datos: Dict, 
                         usuario: Dict) -> Dict:
        """
        Guarda cambios de un incidente manteniendo formato unificado
        
        Args:
            indice_unico: Índice único del incidente
            datos: Datos actualizados
            usuario: Información del usuario
            
        Returns:
            Resultado de la operación
        """
        try:
            # 1. Validar estructura
            es_valido, errores = self.validador.validar_incidente_completo(
                datos, validar_archivos=False
            )
            
            if not es_valido:
                return {
                    "exito": False,
                    "errores": errores,
                    "mensaje": "Datos no válidos"
                }
            
            # 2. Obtener incidente de BD
            incidente_bd = self._obtener_incidente_bd(indice_unico)
            if not incidente_bd:
                return {
                    "exito": False,
                    "error": "Incidente no encontrado"
                }
            
            # 3. Preparar para guardar
            incidente_guardar = self.unificador.exportar_para_guardar(datos)
            
            # 4. Actualizar en BD
            resultado_update = self._actualizar_incidente_bd(
                incidente_bd["IncidenteID"],
                incidente_guardar,
                usuario["id"]
            )
            
            if not resultado_update["exito"]:
                return resultado_update
            
            # 5. Sincronizar taxonomías
            self.gestor_taxonomias.sincronizar_con_json(
                incidente_bd["IncidenteID"],
                incidente_guardar
            )
            
            # 6. Actualizar archivo temporal
            archivo_temp = os.path.join(self.ruta_temp, f"{indice_unico}.json")
            incidente_guardar["metadata"]["estado_temporal"] = "semilla_base"
            
            with open(archivo_temp, 'w', encoding='utf-8') as f:
                json.dump(incidente_guardar, f, ensure_ascii=False, indent=2)
            
            return {
                "exito": True,
                "incidente_id": incidente_bd["IncidenteID"],
                "mensaje": "Incidente guardado correctamente"
            }
            
        except Exception as e:
            return {
                "exito": False,
                "error": str(e),
                "mensaje": "Error guardando incidente"
            }
    
    def procesar_evidencia(self, indice_unico: str, seccion: str,
                          archivo, usuario: Dict) -> Dict:
        """
        Procesa y guarda una evidencia
        
        Args:
            indice_unico: Índice único del incidente
            seccion: Número de sección
            archivo: Archivo a procesar
            usuario: Información del usuario
            
        Returns:
            Resultado del procesamiento
        """
        try:
            # 1. Obtener incidente
            incidente_bd = self._obtener_incidente_bd(indice_unico)
            if not incidente_bd:
                return {
                    "exito": False,
                    "error": "Incidente no encontrado"
                }
            
            # 2. Procesar archivo
            resultado_archivo = self.gestor_evidencias.procesar_archivo(
                archivo, indice_unico, seccion, usuario["id"]
            )
            
            if not resultado_archivo["exito"]:
                return resultado_archivo
            
            # 3. Guardar en BD
            resultado_bd = self.gestor_evidencias.guardar_evidencia_bd(
                incidente_bd["IncidenteID"],
                resultado_archivo["archivo_info"]
            )
            
            if not resultado_bd["exito"]:
                return resultado_bd
            
            # 4. Actualizar estructura JSON
            archivo_temp = os.path.join(self.ruta_temp, f"{indice_unico}.json")
            if os.path.exists(archivo_temp):
                with open(archivo_temp, 'r', encoding='utf-8') as f:
                    incidente = json.load(f)
                
                # Agregar evidencia según sección
                if seccion == "4":  # Taxonomías requieren UUID
                    # Este caso se maneja diferente
                    pass
                else:
                    incidente = self.unificador.agregar_evidencia_seccion(
                        incidente, seccion, resultado_archivo["archivo_info"]
                    )
                
                with open(archivo_temp, 'w', encoding='utf-8') as f:
                    json.dump(incidente, f, ensure_ascii=False, indent=2)
            
            return {
                "exito": True,
                "evidencia_id": resultado_bd["evidencia_id"],
                "archivo_info": resultado_archivo["archivo_info"],
                "mensaje": "Evidencia procesada correctamente"
            }
            
        except Exception as e:
            return {
                "exito": False,
                "error": str(e),
                "mensaje": "Error procesando evidencia"
            }
    
    def generar_reporte_validacion(self, indice_unico: str) -> Dict:
        """
        Genera reporte de validación completo
        
        Args:
            indice_unico: Índice único del incidente
            
        Returns:
            Reporte detallado
        """
        try:
            # Obtener incidente
            resultado = self.obtener_incidente_edicion(indice_unico, {"id": 0})
            
            if not resultado["exito"]:
                return resultado
            
            incidente = resultado["incidente"]
            
            # Generar reporte
            reporte = self.validador.generar_reporte_validacion(incidente)
            
            # Agregar información adicional
            reporte["indice_unico"] = indice_unico
            reporte["puede_exportar_anci"] = reporte["resumen"]["puede_continuar"]
            
            return {
                "exito": True,
                "reporte": reporte
            }
            
        except Exception as e:
            return {
                "exito": False,
                "error": str(e)
            }
    
    def _generar_indice_unico(self, empresa_id: int, titulo: str) -> str:
        """Genera índice único según formato especificado"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Obtener RUT de empresa
            cursor.execute("""
                SELECT RUT FROM Empresas WHERE EmpresaID = ?
            """, (empresa_id,))
            
            rut_result = cursor.fetchone()
            rut = rut_result[0].replace('-', '').replace('.', '') if rut_result else "00000000"
            
            # Obtener correlativo
            cursor.execute("""
                SELECT ISNULL(MAX(CAST(LEFT(IDVisible, CHARINDEX('_', IDVisible) - 1) AS INT)), 0) + 1
                FROM Incidentes
                WHERE EmpresaID = ?
            """, (empresa_id,))
            
            correlativo = cursor.fetchone()[0]
            
            # Generar descripción desde título
            descripcion = titulo[:30].upper().replace(' ', '_')
            descripcion = ''.join(c for c in descripcion if c.isalnum() or c == '_')
            
            # Formato: CORRELATIVO_RUT_MODULO_SUBMODULO_DESCRIPCION
            indice = f"{correlativo}_{rut}_1_1_{descripcion}"
            
            return indice
            
        except Exception as e:
            # Fallback con timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            return f"1_{timestamp}_1_1_INCIDENTE"
        finally:
            if conn:
                conn.close()
    
    def _guardar_incidente_bd(self, incidente: Dict, indice_unico: str,
                             usuario_id: int) -> Dict:
        """Guarda incidente nuevo en BD"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Preparar JSON
            formato_json = json.dumps(incidente, ensure_ascii=False)
            
            # Insertar incidente
            cursor.execute("""
                INSERT INTO Incidentes (
                    IDVisible, Titulo, Descripcion, FechaIncidente,
                    EstadoActual, EmpresaID, CreadoPor, FechaCreacion,
                    FormatoSemillaJSON, TipoIncidente
                ) VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, ?)
            """, (
                indice_unico,
                incidente["2"]["titulo"],
                incidente["2"]["descripcion"],
                incidente["2"]["fecha_incidente"],
                "abierto",
                incidente.get("empresa_id", 1),  # Default si no viene
                usuario_id,
                formato_json,
                "operacional"
            ))
            
            cursor.execute("SELECT SCOPE_IDENTITY()")
            incidente_id = cursor.fetchone()[0]
            
            conn.commit()
            
            return {
                "exito": True,
                "incidente_id": incidente_id
            }
            
        except Exception as e:
            if conn:
                conn.rollback()
            return {
                "exito": False,
                "error": str(e)
            }
        finally:
            if conn:
                conn.close()
    
    def _obtener_incidente_bd(self, indice_unico: str) -> Optional[Dict]:
        """Obtiene incidente de BD por índice único"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT IncidenteID, IDVisible, Titulo, Descripcion,
                       EmpresaID, FormatoSemillaJSON, EstadoActual
                FROM Incidentes
                WHERE IDVisible = ?
            """, (indice_unico,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "IncidenteID": row[0],
                    "IDVisible": row[1],
                    "Titulo": row[2],
                    "Descripcion": row[3],
                    "EmpresaID": row[4],
                    "FormatoSemillaJSON": row[5],
                    "EstadoActual": row[6]
                }
            
            return None
            
        except Exception as e:
            print(f"Error obteniendo incidente: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def _actualizar_incidente_bd(self, incidente_id: int, incidente: Dict,
                                usuario_id: int) -> Dict:
        """Actualiza incidente en BD"""
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            formato_json = json.dumps(incidente, ensure_ascii=False)
            
            cursor.execute("""
                UPDATE Incidentes SET
                    Titulo = ?,
                    Descripcion = ?,
                    FechaIncidente = ?,
                    FormatoSemillaJSON = ?,
                    ModificadoPor = ?,
                    FechaModificacion = GETDATE()
                WHERE IncidenteID = ?
            """, (
                incidente["2"]["titulo"],
                incidente["2"]["descripcion"], 
                incidente["2"]["fecha_incidente"],
                formato_json,
                usuario_id,
                incidente_id
            ))
            
            conn.commit()
            
            return {"exito": True}
            
        except Exception as e:
            if conn:
                conn.rollback()
            return {
                "exito": False,
                "error": str(e)
            }
        finally:
            if conn:
                conn.close()
    
    def _convertir_bd_a_formato(self, incidente_bd: Dict) -> Dict:
        """Convierte datos de BD a formato unificado"""
        # Si tiene JSON guardado, usarlo
        if incidente_bd.get("FormatoSemillaJSON"):
            try:
                return json.loads(incidente_bd["FormatoSemillaJSON"])
            except:
                pass
        
        # Si no, crear estructura básica
        return self.unificador.crear_estructura_incidente({
            "empresa_id": incidente_bd["EmpresaID"],
            "2": {
                "titulo": incidente_bd["Titulo"],
                "descripcion": incidente_bd["Descripcion"]
            }
        })
    
    def _actualizar_evidencias_estructura(self, incidente: Dict, 
                                         evidencias: List[Dict]) -> None:
        """Actualiza evidencias en la estructura del incidente"""
        # Limpiar evidencias actuales
        for seccion in ["2", "3", "5", "6"]:
            if seccion in incidente and "evidencias" in incidente[seccion]:
                incidente[seccion]["evidencias"]["items"] = []
                incidente[seccion]["evidencias"]["contador"] = 0
        
        # Agregar evidencias desde BD
        for evidencia in evidencias:
            seccion_map = {
                "2.5": "2",
                "3.4": "3",
                "5.2": "5", 
                "6.4": "6"
            }
            
            seccion = seccion_map.get(evidencia["seccion"])
            if seccion and seccion in incidente:
                if "evidencias" in incidente[seccion]:
                    incidente[seccion]["evidencias"]["contador"] += 1
                    incidente[seccion]["evidencias"]["items"].append({
                        "numero": evidencia["seccion"] + "." + 
                                 str(incidente[seccion]["evidencias"]["contador"]),
                        "archivo": evidencia["ruta"],
                        "nombre": evidencia["nombre"],
                        "hash_md5": evidencia["hash_md5"],
                        "tamano_kb": evidencia["tamano_kb"],
                        "fecha_subida": evidencia["fecha_subida"],
                        "estado": "activo"
                    })

# Instancia global del manager
manager = IncidentesManager()

# Endpoints del API

@incidentes_unificado_bp.route('/crear', methods=['POST'])
@login_required
def crear_incidente(usuario):
    """Crea nuevo incidente con formato unificado"""
    try:
        datos = request.get_json()
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        resultado = manager.crear_incidente(datos, usuario)
        
        if resultado["exito"]:
            return jsonify(resultado), 201
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        return jsonify({
            "error": "Error creando incidente",
            "detalle": str(e)
        }), 500

@incidentes_unificado_bp.route('/editar/<indice_unico>', methods=['GET'])
@login_required  
def obtener_para_editar(usuario, indice_unico):
    """Obtiene incidente para edición"""
    try:
        resultado = manager.obtener_incidente_edicion(indice_unico, usuario)
        
        if resultado["exito"]:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
            
    except Exception as e:
        return jsonify({
            "error": "Error obteniendo incidente",
            "detalle": str(e)
        }), 500

@incidentes_unificado_bp.route('/guardar/<indice_unico>', methods=['PUT'])
@login_required
def guardar_incidente(usuario, indice_unico):
    """Guarda cambios en incidente"""
    try:
        datos = request.get_json()
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        resultado = manager.guardar_incidente(indice_unico, datos, usuario)
        
        if resultado["exito"]:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        return jsonify({
            "error": "Error guardando incidente",
            "detalle": str(e)
        }), 500

@incidentes_unificado_bp.route('/evidencia/<indice_unico>/<seccion>', methods=['POST'])
@login_required
def subir_evidencia(usuario, indice_unico, seccion):
    """Sube evidencia a una sección"""
    try:
        if 'archivo' not in request.files:
            return jsonify({"error": "No se recibió archivo"}), 400
        
        archivo = request.files['archivo']
        
        resultado = manager.procesar_evidencia(
            indice_unico, seccion, archivo, usuario
        )
        
        if resultado["exito"]:
            return jsonify(resultado), 201
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        return jsonify({
            "error": "Error procesando evidencia",
            "detalle": str(e)
        }), 500

@incidentes_unificado_bp.route('/validar/<indice_unico>', methods=['GET'])
@login_required
def validar_incidente(usuario, indice_unico):
    """Valida un incidente y genera reporte"""
    try:
        resultado = manager.generar_reporte_validacion(indice_unico)
        
        if resultado["exito"]:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        return jsonify({
            "error": "Error validando incidente",
            "detalle": str(e)
        }), 500

@incidentes_unificado_bp.route('/taxonomias/disponibles', methods=['GET'])
@login_required
def obtener_taxonomias_disponibles(usuario):
    """Obtiene lista de taxonomías disponibles"""
    try:
        taxonomias = manager.gestor_taxonomias.obtener_taxonomias_disponibles()
        
        return jsonify({
            "exito": True,
            "taxonomias": taxonomias,
            "total": len(taxonomias)
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Error obteniendo taxonomías",
            "detalle": str(e)
        }), 500

def registrar_modulo_unificado(app):
    """Registra el módulo unificado en la aplicación Flask"""
    app.register_blueprint(incidentes_unificado_bp)
    print("✅ Módulo unificado de incidentes registrado")
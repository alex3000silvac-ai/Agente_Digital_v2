# diagnostico_incidentes.py
"""
Módulo de Diagnóstico para Incidentes
Identifica problemas en la conexión entre creación y edición de evidencias
Asegura la integridad de datos para poder editar incidentes con todos sus archivos
"""

import os
import json
from datetime import datetime
from flask import Blueprint, jsonify, request
from ...database import get_db_connection
from ...auth_utils import verificar_token
from functools import wraps

diagnostico_bp = Blueprint('diagnostico_incidentes', __name__, url_prefix='/api/admin/diagnostico')

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

class DiagnosticoIncidentes:
    def __init__(self):
        self.ruta_uploads = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')
        self.ruta_temp = os.path.join(os.path.dirname(__file__), '..', '..', 'temp_incidentes')
        self.problemas = []
        self.sugerencias = []
    
    def diagnosticar_incidente(self, indice_unico):
        """
        Diagnóstica un incidente específico para encontrar inconsistencias
        """
        self.problemas = []
        self.sugerencias = []
        resultado = {
            "indice_unico": indice_unico,
            "timestamp": datetime.now().isoformat(),
            "diagnosticos": {}
        }
        
        conn = None
        try:
            conn = get_db_connection()
            if not conn:
                self.problemas.append("No se pudo conectar a la base de datos")
                resultado["error"] = "Error de conexión"
                return resultado
            
            cursor = conn.cursor()
            
            # 1. Verificar existencia en BD
            resultado["diagnosticos"]["bd_principal"] = self._verificar_bd(cursor, indice_unico)
            
            # Si no existe en BD, no continuar
            if not resultado["diagnosticos"]["bd_principal"]["existe"]:
                self.problemas.append(f"Incidente con índice {indice_unico} no existe en BD")
                self.sugerencias.append("Verificar que el índice único sea correcto")
                resultado["problemas"] = self.problemas
                resultado["sugerencias"] = self.sugerencias
                return resultado
            
            incidente_id = resultado["diagnosticos"]["bd_principal"]["incidente_id"]
            
            # 2. Verificar archivos temporales (semillas)
            resultado["diagnosticos"]["archivos_temporales"] = self._verificar_semillas(indice_unico)
            
            # 3. Verificar estructura de carpetas
            resultado["diagnosticos"]["estructura_carpetas"] = self._verificar_estructura_carpetas(indice_unico)
            
            # 4. Verificar evidencias en BD
            resultado["diagnosticos"]["evidencias_bd"] = self._verificar_evidencias_bd(cursor, incidente_id)
            
            # 5. Verificar archivos físicos vs BD
            resultado["diagnosticos"]["archivos_fisicos"] = self._verificar_archivos_fisicos(
                cursor, incidente_id, indice_unico
            )
            
            # 6. Verificar integridad de taxonomías
            resultado["diagnosticos"]["taxonomias"] = self._verificar_taxonomias(cursor, incidente_id)
            
            # 7. Verificar formato del índice único
            resultado["diagnosticos"]["formato_indice"] = self._verificar_formato_indice(indice_unico)
            
            # 8. Generar reporte y soluciones
            resultado["problemas"] = self.problemas
            resultado["sugerencias"] = self.sugerencias
            resultado["puede_editar"] = len(self.problemas) == 0
            
        except Exception as e:
            resultado["error"] = f"Error durante diagnóstico: {str(e)}"
            self.problemas.append(f"Error general: {str(e)}")
            
        finally:
            if conn:
                conn.close()
        
        return resultado
    
    def _verificar_bd(self, cursor, indice_unico):
        """Verifica si el incidente existe en la BD principal"""
        try:
            # Buscar por IDVisible o por indice_unico
            cursor.execute("""
                SELECT IncidenteID, IDVisible, Titulo, EstadoActual, 
                       EmpresaID, FechaCreacion, FechaModificacion,
                       FormatoSemillaJSON, IndiceTaxonomias
                FROM Incidentes 
                WHERE IDVisible = ? OR IncidenteID IN (
                    SELECT id FROM Incidentes WHERE indice_unico = ?
                )
            """, (indice_unico, indice_unico))
            
            resultado = cursor.fetchone()
            
            if resultado:
                return {
                    "existe": True,
                    "incidente_id": resultado[0],
                    "id_visible": resultado[1],
                    "titulo": resultado[2],
                    "estado": resultado[3],
                    "empresa_id": resultado[4],
                    "fecha_creacion": resultado[5].isoformat() if resultado[5] else None,
                    "fecha_modificacion": resultado[6].isoformat() if resultado[6] else None,
                    "tiene_semilla_json": resultado[7] is not None,
                    "tiene_indice_taxonomias": resultado[8] is not None
                }
            else:
                return {"existe": False}
                
        except Exception as e:
            self.problemas.append(f"Error verificando BD principal: {str(e)}")
            return {"existe": False, "error": str(e)}
    
    def _verificar_semillas(self, indice_unico):
        """Verifica archivos de semilla (temporales)"""
        resultado = {
            "semilla_original": False,
            "semilla_base": False,
            "archivo_temporal": False,
            "detalles": {}
        }
        
        # Archivo temporal principal
        archivo_temp = os.path.join(self.ruta_temp, f"{indice_unico}.json")
        if os.path.exists(archivo_temp):
            resultado["archivo_temporal"] = True
            try:
                with open(archivo_temp, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                resultado["detalles"]["temporal"] = {
                    "estado": datos.get("estado_temporal", "desconocido"),
                    "timestamp": datos.get("timestamp_creacion") or datos.get("timestamp_actualizacion"),
                    "secciones": list(datos.keys())
                }
            except Exception as e:
                self.problemas.append(f"Error leyendo archivo temporal: {str(e)}")
        else:
            self.sugerencias.append("Crear archivo temporal para edición segura")
        
        # Verificar semillas en carpeta uploads (legacy)
        ruta_semilla_original = os.path.join(self.ruta_uploads, f"{indice_unico}_semilla_original.json")
        ruta_semilla_base = os.path.join(self.ruta_uploads, f"{indice_unico}_semilla_base.json")
        
        if os.path.exists(ruta_semilla_original):
            resultado["semilla_original"] = True
        
        if os.path.exists(ruta_semilla_base):
            resultado["semilla_base"] = True
        
        return resultado
    
    def _verificar_estructura_carpetas(self, indice_unico):
        """Verifica estructura de carpetas según especificaciones"""
        resultado = {
            "carpeta_principal": False,
            "estructura_correcta": True,
            "secciones": []
        }
        
        # Estructura esperada según incidente.txt
        secciones_esperadas = {
            "2.5": "Descripción y Alcance - Evidencias",
            "3.4": "Análisis Preliminar - Evidencias",
            "4.4": "Taxonomías - Evidencias",
            "5.2": "Acciones Inmediatas - Evidencias",
            "6.4": "Análisis Causa Raíz - Evidencias"
        }
        
        # Carpeta principal del incidente
        carpeta_incidente = os.path.join(self.ruta_uploads, "evidencias", indice_unico)
        
        if os.path.exists(carpeta_incidente):
            resultado["carpeta_principal"] = True
            
            # Verificar subcarpetas por sección
            try:
                contenido = os.listdir(carpeta_incidente)
                for item in contenido:
                    ruta_completa = os.path.join(carpeta_incidente, item)
                    if os.path.isdir(ruta_completa):
                        archivos = os.listdir(ruta_completa)
                        resultado["secciones"].append({
                            "nombre": item,
                            "archivos": len(archivos),
                            "esperada": item in secciones_esperadas
                        })
            except Exception as e:
                self.problemas.append(f"Error leyendo estructura de carpetas: {str(e)}")
                resultado["estructura_correcta"] = False
        else:
            self.problemas.append("No existe carpeta principal de evidencias")
            self.sugerencias.append(f"Crear carpeta: {carpeta_incidente}")
            resultado["estructura_correcta"] = False
        
        return resultado
    
    def _verificar_evidencias_bd(self, cursor, incidente_id):
        """Verifica evidencias en la base de datos"""
        resultado = {
            "total_evidencias": 0,
            "por_seccion": {},
            "evidencias": []
        }
        
        try:
            cursor.execute("""
                SELECT 
                    EvidenciaID, 
                    NombreArchivo, 
                    RutaArchivo, 
                    Descripcion,
                    Seccion, 
                    FechaSubida, 
                    Estado,
                    SubidoPor,
                    Version,
                    TamanoKB
                FROM EvidenciasIncidentes 
                WHERE IncidenteID = ?
                ORDER BY Seccion, FechaSubida
            """, (incidente_id,))
            
            evidencias = cursor.fetchall()
            resultado["total_evidencias"] = len(evidencias)
            
            for ev in evidencias:
                seccion = ev[4] or "sin_seccion"
                
                if seccion not in resultado["por_seccion"]:
                    resultado["por_seccion"][seccion] = 0
                resultado["por_seccion"][seccion] += 1
                
                evidencia_info = {
                    "id": ev[0],
                    "nombre": ev[1],
                    "ruta": ev[2],
                    "descripcion": ev[3],
                    "seccion": seccion,
                    "fecha": ev[5].isoformat() if ev[5] else None,
                    "estado": ev[6],
                    "subido_por": ev[7],
                    "version": ev[8],
                    "tamano_kb": ev[9],
                    "archivo_existe": os.path.exists(ev[2]) if ev[2] else False
                }
                
                resultado["evidencias"].append(evidencia_info)
                
                # Verificar problemas
                if not evidencia_info["archivo_existe"] and ev[2]:
                    self.problemas.append(f"Archivo no encontrado: {ev[2]}")
                    
        except Exception as e:
            self.problemas.append(f"Error verificando evidencias en BD: {str(e)}")
        
        return resultado
    
    def _verificar_archivos_fisicos(self, cursor, incidente_id, indice_unico):
        """Compara archivos físicos con registros en BD"""
        resultado = {
            "archivos_huerfanos": [],  # En disco pero no en BD
            "archivos_faltantes": [],  # En BD pero no en disco
            "archivos_correctos": 0,
            "total_archivos_disco": 0,
            "total_archivos_bd": 0
        }
        
        # Obtener archivos de BD
        archivos_bd = set()
        try:
            cursor.execute("""
                SELECT RutaArchivo FROM EvidenciasIncidentes 
                WHERE IncidenteID = ? AND RutaArchivo IS NOT NULL
            """, (incidente_id,))
            
            for row in cursor.fetchall():
                archivos_bd.add(row[0])
            
            resultado["total_archivos_bd"] = len(archivos_bd)
        except Exception as e:
            self.problemas.append(f"Error obteniendo archivos de BD: {str(e)}")
        
        # Obtener archivos del disco
        archivos_disco = set()
        carpeta_evidencias = os.path.join(self.ruta_uploads, "evidencias", indice_unico)
        
        if os.path.exists(carpeta_evidencias):
            for root, dirs, files in os.walk(carpeta_evidencias):
                for archivo in files:
                    ruta_completa = os.path.join(root, archivo)
                    archivos_disco.add(ruta_completa)
            
            resultado["total_archivos_disco"] = len(archivos_disco)
        
        # Comparar
        for archivo_bd in archivos_bd:
            if os.path.exists(archivo_bd):
                resultado["archivos_correctos"] += 1
            else:
                resultado["archivos_faltantes"].append(archivo_bd)
        
        # Buscar huérfanos (más complejo, requiere normalizar rutas)
        # Por ahora simplificado
        
        if resultado["archivos_faltantes"]:
            self.sugerencias.append("Restaurar archivos faltantes desde backup o eliminar referencias en BD")
        
        return resultado
    
    def _verificar_taxonomias(self, cursor, incidente_id):
        """Verifica integridad de taxonomías asignadas"""
        resultado = {
            "total_taxonomias": 0,
            "taxonomias_validas": 0,
            "taxonomias": []
        }
        
        try:
            cursor.execute("""
                SELECT 
                    it.ID,
                    it.Id_Taxonomia,
                    it.Comentarios,
                    it.FechaAsignacion,
                    t.Id_Incidente,
                    t.Categoria_del_Incidente,
                    t.Subcategoria_del_Incidente
                FROM INCIDENTE_TAXONOMIA it
                LEFT JOIN Taxonomia_incidentes t ON it.Id_Taxonomia = t.Id_Incidente
                WHERE it.IncidenteID = ?
            """, (incidente_id,))
            
            taxonomias = cursor.fetchall()
            resultado["total_taxonomias"] = len(taxonomias)
            
            for tax in taxonomias:
                valida = tax[4] is not None  # Existe en tabla de taxonomías
                if valida:
                    resultado["taxonomias_validas"] += 1
                else:
                    self.problemas.append(f"Taxonomía inválida: {tax[1]}")
                
                resultado["taxonomias"].append({
                    "id": tax[0],
                    "id_taxonomia": tax[1],
                    "comentarios": tax[2],
                    "fecha": tax[3].isoformat() if tax[3] else None,
                    "valida": valida,
                    "categoria": tax[5] if valida else None,
                    "subcategoria": tax[6] if valida else None
                })
                
        except Exception as e:
            self.problemas.append(f"Error verificando taxonomías: {str(e)}")
        
        return resultado
    
    def _verificar_formato_indice(self, indice_unico):
        """Verifica que el índice único siga el formato especificado"""
        # Formato esperado: CORRELATIVO_RUT_MODULO_SUBMODULO_DESCRIPCION
        resultado = {
            "formato_correcto": False,
            "componentes": {},
            "detalles": ""
        }
        
        try:
            partes = indice_unico.split('_')
            
            if len(partes) >= 5:
                resultado["formato_correcto"] = True
                resultado["componentes"] = {
                    "correlativo": partes[0],
                    "rut": partes[1],
                    "modulo": partes[2],
                    "submodulo": partes[3],
                    "descripcion": '_'.join(partes[4:])
                }
                
                # Validaciones adicionales
                if not partes[0].isdigit():
                    resultado["formato_correcto"] = False
                    self.problemas.append("El correlativo debe ser numérico")
                
                if not partes[1].replace('-', '').isdigit():
                    resultado["formato_correcto"] = False
                    self.problemas.append("El RUT debe ser numérico")
                    
            else:
                resultado["formato_correcto"] = False
                resultado["detalles"] = f"Se esperaban al menos 5 partes, se encontraron {len(partes)}"
                self.problemas.append("Formato de índice único incorrecto")
                
        except Exception as e:
            resultado["formato_correcto"] = False
            resultado["detalles"] = str(e)
            self.problemas.append(f"Error analizando formato de índice: {str(e)}")
        
        return resultado
    
    def reparar_estructura(self, indice_unico):
        """Intenta reparar la estructura de carpetas y archivos"""
        reparaciones = {
            "carpetas_creadas": [],
            "archivos_movidos": [],
            "registros_actualizados": [],
            "exito": True
        }
        
        try:
            # Crear estructura de carpetas si no existe
            carpeta_base = os.path.join(self.ruta_uploads, "evidencias", indice_unico)
            if not os.path.exists(carpeta_base):
                os.makedirs(carpeta_base, exist_ok=True)
                reparaciones["carpetas_creadas"].append(carpeta_base)
            
            # Crear carpeta temporal si no existe
            if not os.path.exists(self.ruta_temp):
                os.makedirs(self.ruta_temp, exist_ok=True)
                reparaciones["carpetas_creadas"].append(self.ruta_temp)
            
            # Crear subcarpetas por sección
            secciones = ["2.5", "3.4", "4.4", "5.2", "6.4"]
            for seccion in secciones:
                carpeta_seccion = os.path.join(carpeta_base, seccion)
                if not os.path.exists(carpeta_seccion):
                    os.makedirs(carpeta_seccion, exist_ok=True)
                    reparaciones["carpetas_creadas"].append(carpeta_seccion)
            
        except Exception as e:
            reparaciones["exito"] = False
            reparaciones["error"] = str(e)
        
        return reparaciones

# Instancia global
diagnosticador = DiagnosticoIncidentes()

@diagnostico_bp.route('/incidente/<indice_unico>', methods=['GET'])
@login_required
def diagnosticar_incidente(usuario, indice_unico):
    """Endpoint para diagnosticar un incidente específico"""
    try:
        resultado = diagnosticador.diagnosticar_incidente(indice_unico)
        
        # Agregar información del usuario que ejecutó el diagnóstico
        resultado["diagnosticado_por"] = usuario.get('email', 'desconocido')
        
        return jsonify(resultado), 200
        
    except Exception as e:
        return jsonify({
            "error": "Error ejecutando diagnóstico",
            "detalle": str(e)
        }), 500

@diagnostico_bp.route('/incidente/<indice_unico>/reparar', methods=['POST'])
@login_required
def reparar_incidente(usuario, indice_unico):
    """Endpoint para intentar reparar la estructura de un incidente"""
    try:
        # Primero diagnosticar
        diagnostico = diagnosticador.diagnosticar_incidente(indice_unico)
        
        if not diagnostico.get("diagnosticos", {}).get("bd_principal", {}).get("existe"):
            return jsonify({
                "error": "No se puede reparar: el incidente no existe en la base de datos"
            }), 404
        
        # Intentar reparación
        resultado_reparacion = diagnosticador.reparar_estructura(indice_unico)
        
        # Diagnosticar nuevamente para verificar
        diagnostico_post = diagnosticador.diagnosticar_incidente(indice_unico)
        
        return jsonify({
            "reparacion": resultado_reparacion,
            "diagnostico_previo": {
                "problemas": len(diagnostico.get("problemas", [])),
                "puede_editar": diagnostico.get("puede_editar", False)
            },
            "diagnostico_posterior": {
                "problemas": len(diagnostico_post.get("problemas", [])),
                "puede_editar": diagnostico_post.get("puede_editar", False)
            },
            "reparado_por": usuario.get('email', 'desconocido')
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Error durante reparación",
            "detalle": str(e)
        }), 500

@diagnostico_bp.route('/todos', methods=['GET'])
@login_required
def diagnosticar_todos(usuario):
    """Diagnóstico masivo de todos los incidentes"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión a BD"}), 500
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT IDVisible, Titulo, EstadoActual 
            FROM Incidentes 
            WHERE IDVisible IS NOT NULL
            ORDER BY IncidenteID DESC
        """)
        
        incidentes = cursor.fetchall()
        resultados = []
        resumen = {
            "total": len(incidentes),
            "sin_problemas": 0,
            "con_problemas": 0,
            "criticos": 0
        }
        
        for inc in incidentes:
            indice = inc[0]
            diagnostico = diagnosticador.diagnosticar_incidente(indice)
            
            num_problemas = len(diagnostico.get("problemas", []))
            puede_editar = diagnostico.get("puede_editar", False)
            
            if num_problemas == 0:
                resumen["sin_problemas"] += 1
            else:
                resumen["con_problemas"] += 1
                if not puede_editar:
                    resumen["criticos"] += 1
            
            resultados.append({
                "indice_unico": indice,
                "titulo": inc[1],
                "estado": inc[2],
                "problemas": num_problemas,
                "puede_editar": puede_editar,
                "problemas_detalle": diagnostico.get("problemas", [])[:3]  # Solo primeros 3
            })
        
        conn.close()
        
        return jsonify({
            "resumen": resumen,
            "incidentes": resultados,
            "diagnosticado_por": usuario.get('email', 'desconocido'),
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Error en diagnóstico masivo",
            "detalle": str(e)
        }), 500

# Registrar rutas
def registrar_rutas_diagnostico(app):
    """Registra las rutas del módulo de diagnóstico"""
    app.register_blueprint(diagnostico_bp)
# incidente_unificador.py
"""
Módulo Unificador de Incidentes - Versión Mejorada
Garantiza formato idéntico entre creación, edición y grabado
Maneja correctamente taxonomías múltiples y evidencias jerárquicas
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from ...database import get_db_connection

class IncidenteUnificador:
    """
    Clase que unifica el formato de incidentes entre creación y edición
    Garantiza que el formato sea EXACTAMENTE el mismo en todo el ciclo de vida
    """
    
    def __init__(self):
        self.ruta_uploads = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')
        self.ruta_temp = os.path.join(os.path.dirname(__file__), '..', '..', 'temp_incidentes')
        self.formato_maestro = self._definir_formato_maestro()
    
    def _definir_formato_maestro(self) -> Dict:
        """
        Define EL formato maestro que usarán TODOS los módulos
        Este es EL ÚNICO formato válido en todo el sistema
        """
        return {
            # 1. Identificación General
            "identificacion_general": {
                "tipo_registro": "",
                "titulo_incidente": "",
                "fecha_deteccion": "",
                "fecha_ocurrencia": "",
                "criticidad": "",
                "alcance_geografico": ""
            },
            
            # 2. Descripción y Alcance
            "descripcion_alcance": {
                "descripcion_detallada": "",
                "impacto_preliminar": "",
                "sistemas_afectados": "",
                "servicios_interrumpidos": "",
                "evidencias": []  # Lista de evidencias sección 2.5
            },
            
            # 3. Análisis Preliminar
            "analisis_preliminar": {
                "tipo_amenaza": "",
                "origen_ataque": "",
                "responsable_cliente": "",
                "evidencias": []  # Lista de evidencias sección 3.4
            },
            
            # 4. Clasificación de Taxonomías - ESTRUCTURA MEJORADA
            "taxonomias": {
                "seleccionadas": [
                    # Cada taxonomía es un objeto con su propia lista de evidencias
                    # {
                    #     "id_unico": "uuid",  # ID único interno
                    #     "taxonomia_id": "",  # ID de la tabla Taxonomia_incidentes
                    #     "nombre": "",
                    #     "categoria": "",
                    #     "subcategoria": "",
                    #     "porque_seleccionada": "",
                    #     "observaciones_adicionales": "",
                    #     "numero_orden": 1,  # Para generar 4.4.1, 4.4.2, etc.
                    #     "evidencias": [
                    #         {
                    #             "numero": "4.4.1.1",
                    #             "archivo": "ruta/archivo.pdf",
                    #             "nombre_archivo": "archivo.pdf",
                    #             "descripcion": "Descripción",
                    #             "fecha": "2025-01-17T10:30:00",
                    #             "estado": "activo"  # activo/eliminado
                    #         }
                    #     ]
                    # }
                ],
                "contador": 0,  # Contador para asignar números de orden
                "historial_cambios": []  # Log de cambios en taxonomías
            },
            
            # 5. Acciones Inmediatas
            "acciones_inmediatas": {
                "medidas_contencion": "",
                "evidencias": []  # Lista de evidencias sección 5.2
            },
            
            # 6. Análisis de Causa Raíz
            "causa_raiz": {
                "analisis_causa_raiz": "",
                "lecciones_aprendidas": "",
                "recomendaciones_mejora": "",
                "evidencias": []  # Lista de evidencias sección 6.4
            },
            
            # 7. Resumen de archivos (calculado dinámicamente)
            "resumen_archivos": {
                "total": 0,
                "por_seccion": {},
                "ultima_actualizacion": ""
            },
            
            # Metadatos del sistema
            "_metadatos": {
                "indice_unico": "",
                "incidente_id": None,
                "empresa_id": None,
                "inquilino_id": None,
                "estado": "borrador",  # borrador, final, editando
                "fecha_creacion": "",
                "fecha_modificacion": "",
                "version": 1,
                "tipo_semilla": "original",  # original, base, editando
                "usuario_creacion": "",
                "usuario_modificacion": "",
                "checksum": ""  # Para verificar integridad
            }
        }
    
    def crear_incidente_nuevo(self, datos_entrada: Dict, usuario: Dict) -> Tuple[Dict, str]:
        """
        Crea un nuevo incidente usando EL formato maestro
        
        Returns:
            Tuple[Dict, str]: (incidente en formato maestro, mensaje de éxito/error)
        """
        try:
            print("🎯 Creando incidente en formato maestro...")
            
            # Comenzar con el formato maestro
            incidente = json.loads(json.dumps(self.formato_maestro))  # Deep copy
            
            # Generar índice único
            indice_unico = self._generar_indice_unico(
                datos_entrada.get('empresa_id'),
                datos_entrada.get('inquilino_id')
            )
            
            # Llenar metadatos
            incidente["_metadatos"].update({
                "indice_unico": indice_unico,
                "empresa_id": datos_entrada.get('empresa_id'),
                "inquilino_id": datos_entrada.get('inquilino_id'),
                "fecha_creacion": datetime.now().isoformat(),
                "fecha_modificacion": datetime.now().isoformat(),
                "tipo_semilla": "original",
                "usuario_creacion": usuario.get('email', 'sistema'),
                "usuario_modificacion": usuario.get('email', 'sistema')
            })
            
            # Mapear datos de entrada al formato maestro
            incidente = self._mapear_datos_entrada(incidente, datos_entrada)
            
            # Procesar taxonomías si vienen en los datos
            if 'taxonomias' in datos_entrada and datos_entrada['taxonomias']:
                incidente = self._procesar_taxonomias_entrada(incidente, datos_entrada['taxonomias'])
            
            # Calcular checksum
            incidente["_metadatos"]["checksum"] = self._calcular_checksum(incidente)
            
            # Guardar semilla original
            self._guardar_semilla(incidente, "original")
            
            # Guardar en BD
            incidente_id = self._guardar_en_bd(incidente)
            incidente["_metadatos"]["incidente_id"] = incidente_id
            
            # Actualizar semilla con ID
            self._guardar_semilla(incidente, "original")
            
            print(f"✅ Incidente creado: {indice_unico}")
            return incidente, f"Incidente creado exitosamente: {indice_unico}"
            
        except Exception as e:
            print(f"❌ Error creando incidente: {str(e)}")
            return None, f"Error al crear incidente: {str(e)}"
    
    def cargar_incidente_para_edicion(self, indice_unico: str, usuario: Dict) -> Tuple[Optional[Dict], str]:
        """
        Carga un incidente en EXACTAMENTE el mismo formato para edición
        """
        try:
            print(f"📂 Cargando incidente para edición: {indice_unico}")
            
            # Intentar cargar semilla de edición en curso
            incidente = self._cargar_semilla(indice_unico, "editando")
            
            if not incidente:
                # Intentar cargar semilla base
                incidente = self._cargar_semilla(indice_unico, "base")
            
            if not incidente:
                # Intentar cargar semilla original
                incidente = self._cargar_semilla(indice_unico, "original")
            
            if not incidente:
                # Si no hay semillas, reconstruir desde BD
                incidente = self._reconstruir_desde_bd(indice_unico)
            
            if not incidente:
                return None, f"No se pudo cargar el incidente: {indice_unico}"
            
            # Cargar TODAS las evidencias asociadas desde BD
            incidente = self._sincronizar_evidencias_con_bd(incidente)
            
            # Actualizar resumen de archivos
            incidente = self._actualizar_resumen_archivos(incidente)
            
            # Marcar como editando
            incidente["_metadatos"]["tipo_semilla"] = "editando"
            incidente["_metadatos"]["fecha_modificacion"] = datetime.now().isoformat()
            incidente["_metadatos"]["usuario_modificacion"] = usuario.get('email', 'sistema')
            
            # Guardar copia de trabajo
            self._guardar_semilla(incidente, "editando")
            
            print(f"✅ Incidente cargado para edición en formato maestro")
            return incidente, "Incidente cargado exitosamente"
            
        except Exception as e:
            print(f"❌ Error cargando incidente: {str(e)}")
            return None, f"Error al cargar incidente: {str(e)}"
    
    def guardar_incidente_editado(self, incidente: Dict, usuario: Dict) -> Tuple[Dict, str]:
        """
        Guarda un incidente editado manteniendo EL MISMO formato
        """
        try:
            indice_unico = incidente["_metadatos"]["indice_unico"]
            print(f"💾 Guardando incidente editado: {indice_unico}")
            
            # Validar que sigue el formato maestro
            es_valido, mensaje = self._validar_formato_maestro(incidente)
            if not es_valido:
                return None, f"Formato inválido: {mensaje}"
            
            # Actualizar metadatos
            incidente["_metadatos"]["fecha_modificacion"] = datetime.now().isoformat()
            incidente["_metadatos"]["version"] += 1
            incidente["_metadatos"]["tipo_semilla"] = "base"
            incidente["_metadatos"]["usuario_modificacion"] = usuario.get('email', 'sistema')
            incidente["_metadatos"]["checksum"] = self._calcular_checksum(incidente)
            
            # Actualizar resumen de archivos
            incidente = self._actualizar_resumen_archivos(incidente)
            
            # Guardar en BD
            self._actualizar_en_bd(incidente)
            
            # Guardar taxonomías y evidencias
            self._guardar_taxonomias_en_bd(incidente)
            
            # Guardar como nueva semilla base
            self._guardar_semilla(incidente, "base")
            
            # Limpiar archivo de edición
            self._limpiar_archivo_edicion(indice_unico)
            
            print(f"✅ Incidente guardado manteniendo formato maestro")
            return incidente, "Incidente guardado exitosamente"
            
        except Exception as e:
            print(f"❌ Error guardando incidente: {str(e)}")
            return None, f"Error al guardar incidente: {str(e)}"
    
    def agregar_taxonomia(self, incidente: Dict, taxonomia_data: Dict) -> Dict:
        """
        Agrega una nueva taxonomía al incidente
        """
        # Incrementar contador
        incidente["taxonomias"]["contador"] += 1
        numero_orden = incidente["taxonomias"]["contador"]
        
        # Crear objeto de taxonomía
        nueva_taxonomia = {
            "id_unico": str(uuid.uuid4()),
            "taxonomia_id": taxonomia_data["taxonomia_id"],
            "nombre": taxonomia_data["nombre"],
            "categoria": taxonomia_data.get("categoria", ""),
            "subcategoria": taxonomia_data.get("subcategoria", ""),
            "porque_seleccionada": taxonomia_data["porque_seleccionada"],
            "observaciones_adicionales": taxonomia_data.get("observaciones", ""),
            "numero_orden": numero_orden,
            "evidencias": []
        }
        
        incidente["taxonomias"]["seleccionadas"].append(nueva_taxonomia)
        
        # Registrar en historial
        incidente["taxonomias"]["historial_cambios"].append({
            "accion": "agregar_taxonomia",
            "taxonomia_id": nueva_taxonomia["id_unico"],
            "fecha": datetime.now().isoformat(),
            "detalles": f"Agregada taxonomía: {nueva_taxonomia['nombre']}"
        })
        
        return incidente
    
    def eliminar_taxonomia(self, incidente: Dict, id_unico_taxonomia: str) -> Dict:
        """
        Elimina una taxonomía del incidente (marca como eliminada, no borra físicamente)
        """
        for taxonomia in incidente["taxonomias"]["seleccionadas"]:
            if taxonomia["id_unico"] == id_unico_taxonomia:
                # Marcar evidencias como eliminadas
                for evidencia in taxonomia.get("evidencias", []):
                    evidencia["estado"] = "eliminado"
                
                # Registrar en historial
                incidente["taxonomias"]["historial_cambios"].append({
                    "accion": "eliminar_taxonomia",
                    "taxonomia_id": id_unico_taxonomia,
                    "fecha": datetime.now().isoformat(),
                    "detalles": f"Eliminada taxonomía: {taxonomia['nombre']}"
                })
                
                # Remover de la lista
                incidente["taxonomias"]["seleccionadas"].remove(taxonomia)
                break
        
        return incidente
    
    def agregar_evidencia_taxonomia(self, incidente: Dict, id_unico_taxonomia: str, 
                                   archivo_info: Dict) -> Tuple[Dict, str]:
        """
        Agrega una evidencia a una taxonomía específica
        """
        for taxonomia in incidente["taxonomias"]["seleccionadas"]:
            if taxonomia["id_unico"] == id_unico_taxonomia:
                # Calcular número de evidencia
                num_evidencias_activas = len([e for e in taxonomia["evidencias"] 
                                            if e.get("estado", "activo") == "activo"])
                numero_evidencia = f"4.4.{taxonomia['numero_orden']}.{num_evidencias_activas + 1}"
                
                # Crear objeto de evidencia
                nueva_evidencia = {
                    "numero": numero_evidencia,
                    "archivo": archivo_info["ruta"],
                    "nombre_archivo": archivo_info["nombre"],
                    "descripcion": archivo_info.get("descripcion", ""),
                    "fecha": datetime.now().isoformat(),
                    "estado": "activo",
                    "tamano_kb": archivo_info.get("tamano_kb", 0)
                }
                
                taxonomia["evidencias"].append(nueva_evidencia)
                
                return incidente, numero_evidencia
        
        return incidente, ""
    
    def _procesar_taxonomias_entrada(self, incidente: Dict, taxonomias_entrada: List[Dict]) -> Dict:
        """
        Procesa las taxonomías de entrada y las agrega al incidente
        """
        for tax_data in taxonomias_entrada:
            incidente = self.agregar_taxonomia(incidente, tax_data)
        
        return incidente
    
    def _sincronizar_evidencias_con_bd(self, incidente: Dict) -> Dict:
        """
        Sincroniza las evidencias del incidente con la base de datos
        """
        conn = None
        try:
            conn = get_db_connection()
            if not conn:
                return incidente
            
            cursor = conn.cursor()
            incidente_id = incidente["_metadatos"]["incidente_id"]
            
            if not incidente_id:
                return incidente
            
            # Obtener todas las evidencias de la BD
            cursor.execute("""
                SELECT 
                    EvidenciaID, 
                    NombreArchivo, 
                    RutaArchivo, 
                    Descripcion,
                    Seccion, 
                    FechaSubida, 
                    TamanoKB,
                    numero_evidencia,
                    Estado
                FROM EvidenciasIncidentes 
                WHERE IncidenteID = ?
                ORDER BY Seccion, FechaSubida
            """, (incidente_id,))
            
            evidencias_bd = cursor.fetchall()
            
            # Mapear evidencias a las secciones correctas
            for evidencia in evidencias_bd:
                seccion = evidencia[4]
                evidencia_obj = {
                    "evidencia_id": evidencia[0],
                    "nombre_archivo": evidencia[1],
                    "archivo": evidencia[2],
                    "descripcion": evidencia[3],
                    "fecha": evidencia[5].isoformat() if evidencia[5] else "",
                    "tamano_kb": evidencia[6],
                    "numero": evidencia[7] or seccion,
                    "estado": evidencia[8] or "activo"
                }
                
                # Determinar a qué sección pertenece
                if seccion and seccion.startswith("2.5"):
                    incidente["descripcion_alcance"]["evidencias"].append(evidencia_obj)
                elif seccion and seccion.startswith("3.4"):
                    incidente["analisis_preliminar"]["evidencias"].append(evidencia_obj)
                elif seccion and seccion.startswith("4.4"):
                    # Para taxonomías es más complejo
                    self._asignar_evidencia_a_taxonomia(incidente, evidencia_obj, seccion)
                elif seccion and seccion.startswith("5.2"):
                    incidente["acciones_inmediatas"]["evidencias"].append(evidencia_obj)
                elif seccion and seccion.startswith("6.4"):
                    incidente["causa_raiz"]["evidencias"].append(evidencia_obj)
            
        except Exception as e:
            print(f"Error sincronizando evidencias: {str(e)}")
        finally:
            if conn:
                conn.close()
        
        return incidente
    
    def _asignar_evidencia_a_taxonomia(self, incidente: Dict, evidencia: Dict, seccion: str):
        """
        Asigna una evidencia a la taxonomía correcta basándose en la sección
        """
        # Extraer el número de orden de la sección (ej: 4.4.1.2 -> 1)
        partes = seccion.split('.')
        if len(partes) >= 3:
            try:
                numero_orden = int(partes[2])
                # Buscar la taxonomía con ese número de orden
                for taxonomia in incidente["taxonomias"]["seleccionadas"]:
                    if taxonomia["numero_orden"] == numero_orden:
                        taxonomia["evidencias"].append(evidencia)
                        break
            except ValueError:
                pass
    
    def _actualizar_resumen_archivos(self, incidente: Dict) -> Dict:
        """
        Actualiza el resumen de archivos del incidente
        """
        total = 0
        por_seccion = {}
        
        # Contar evidencias por sección
        secciones = [
            ("2.5", incidente["descripcion_alcance"]["evidencias"]),
            ("3.4", incidente["analisis_preliminar"]["evidencias"]),
            ("5.2", incidente["acciones_inmediatas"]["evidencias"]),
            ("6.4", incidente["causa_raiz"]["evidencias"])
        ]
        
        for seccion, evidencias in secciones:
            activas = [e for e in evidencias if e.get("estado", "activo") == "activo"]
            if activas:
                por_seccion[seccion] = len(activas)
                total += len(activas)
        
        # Contar evidencias de taxonomías
        for taxonomia in incidente["taxonomias"]["seleccionadas"]:
            seccion_tax = f"4.4.{taxonomia['numero_orden']}"
            activas = [e for e in taxonomia.get("evidencias", []) 
                      if e.get("estado", "activo") == "activo"]
            if activas:
                por_seccion[seccion_tax] = len(activas)
                total += len(activas)
        
        incidente["resumen_archivos"] = {
            "total": total,
            "por_seccion": por_seccion,
            "ultima_actualizacion": datetime.now().isoformat()
        }
        
        return incidente
    
    def _generar_indice_unico(self, empresa_id: int, inquilino_id: int) -> str:
        """
        Genera índice único según especificación
        """
        conn = None
        try:
            conn = get_db_connection()
            if not conn:
                # Fallback si no hay conexión
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                return f"1_{timestamp}_1_1_INCIDENTE_TEMPORAL"
            
            cursor = conn.cursor()
            
            # Obtener RUT empresa sin dígito verificador
            cursor.execute("SELECT RUT FROM Empresas WHERE EmpresaID = ?", (empresa_id,))
            resultado = cursor.fetchone()
            
            if resultado and resultado[0]:
                rut = resultado[0].replace('-', '').replace('.', '')
                # Quitar dígito verificador (último carácter)
                rut_sin_dv = rut[:-1] if len(rut) > 1 else "00000000"
            else:
                rut_sin_dv = "00000000"
            
            # Obtener correlativo incremental
            cursor.execute("SELECT ISNULL(MAX(id), 0) + 1 FROM Incidentes")
            correlativo = cursor.fetchone()[0]
            
            # Formato: CORRELATIVO_RUT_MODULO_SUBMODULO_DESCRIPCION
            return f"{correlativo}_{rut_sin_dv}_1_1_INCIDENTE_CIBERSEGURIDAD"
            
        except Exception as e:
            print(f"Error generando índice único: {str(e)}")
            # Fallback
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            return f"1_{timestamp}_1_1_INCIDENTE_ERROR"
        finally:
            if conn:
                conn.close()
    
    def _calcular_checksum(self, incidente: Dict) -> str:
        """
        Calcula un checksum del incidente para verificar integridad
        """
        import hashlib
        # Excluir metadatos del cálculo
        data_sin_meta = {k: v for k, v in incidente.items() if k != "_metadatos"}
        json_str = json.dumps(data_sin_meta, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]
    
    def _guardar_semilla(self, incidente: Dict, tipo: str):
        """
        Guarda archivo de semilla (original, base, editando)
        """
        try:
            indice_unico = incidente["_metadatos"]["indice_unico"]
            
            # Crear directorio de semillas si no existe
            directorio_semillas = os.path.join(self.ruta_temp, "semillas")
            os.makedirs(directorio_semillas, exist_ok=True)
            
            # Nombre del archivo
            nombre_archivo = f"{indice_unico}_semilla_{tipo}.json"
            ruta_archivo = os.path.join(directorio_semillas, nombre_archivo)
            
            # Guardar
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                json.dump(incidente, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Semilla {tipo} guardada: {nombre_archivo}")
            
        except Exception as e:
            print(f"❌ Error guardando semilla {tipo}: {str(e)}")
    
    def _cargar_semilla(self, indice_unico: str, tipo: str) -> Optional[Dict]:
        """
        Carga archivo de semilla
        """
        try:
            directorio_semillas = os.path.join(self.ruta_temp, "semillas")
            nombre_archivo = f"{indice_unico}_semilla_{tipo}.json"
            ruta_archivo = os.path.join(directorio_semillas, nombre_archivo)
            
            if not os.path.exists(ruta_archivo):
                return None
            
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Error cargando semilla {tipo}: {str(e)}")
            return None
    
    def _validar_formato_maestro(self, incidente: Dict) -> Tuple[bool, str]:
        """
        Valida que el incidente cumple con el formato maestro
        """
        try:
            # Verificar secciones principales
            secciones_requeridas = [
                "identificacion_general",
                "descripcion_alcance", 
                "analisis_preliminar",
                "taxonomias",
                "acciones_inmediatas",
                "causa_raiz",
                "_metadatos"
            ]
            
            for seccion in secciones_requeridas:
                if seccion not in incidente:
                    return False, f"Falta sección requerida: {seccion}"
            
            # Verificar estructura de taxonomías
            if "taxonomias" in incidente:
                if "seleccionadas" not in incidente["taxonomias"]:
                    return False, "Falta estructura de taxonomías seleccionadas"
                if not isinstance(incidente["taxonomias"]["seleccionadas"], list):
                    return False, "Taxonomías seleccionadas debe ser una lista"
            
            # Verificar metadatos críticos
            if not incidente["_metadatos"].get("indice_unico"):
                return False, "Falta índice único en metadatos"
            
            return True, "Formato válido"
            
        except Exception as e:
            return False, f"Error validando formato: {str(e)}"
    
    def _guardar_en_bd(self, incidente: Dict) -> int:
        """
        Guarda incidente nuevo en base de datos
        """
        conn = None
        try:
            conn = get_db_connection()
            if not conn:
                raise Exception("No se pudo conectar a la base de datos")
            
            cursor = conn.cursor()
            
            # Insertar en tabla Incidentes
            cursor.execute("""
                INSERT INTO Incidentes (
                    EmpresaID, Titulo, IDVisible, FechaCreacion, FechaDeteccion,
                    CreadoPor, ResponsableCliente, EstadoActual, Criticidad, 
                    TipoFlujo, DescripcionInicial, SistemasAfectados, OrigenIncidente, 
                    AccionesInmediatas, FechaOcurrencia, AlcanceGeografico, 
                    ServiciosInterrumpidos, AnciImpactoPreliminar, AnciTipoAmenaza, 
                    CausaRaiz, LeccionesAprendidas, PlanMejora, FormatoSemillaJSON, 
                    FechaModificacion, IndiceTaxonomias
                ) VALUES (?, ?, ?, GETDATE(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?)
            """, (
                incidente["_metadatos"]["empresa_id"],
                incidente["identificacion_general"]["titulo_incidente"],
                incidente["_metadatos"]["indice_unico"],
                incidente["identificacion_general"]["fecha_deteccion"],
                incidente["_metadatos"]["usuario_creacion"],
                incidente["analisis_preliminar"]["responsable_cliente"],
                "borrador",
                incidente["identificacion_general"]["criticidad"],
                incidente["identificacion_general"]["tipo_registro"],
                incidente["descripcion_alcance"]["descripcion_detallada"],
                incidente["descripcion_alcance"]["sistemas_afectados"],
                incidente["analisis_preliminar"]["origen_ataque"],
                incidente["acciones_inmediatas"]["medidas_contencion"],
                incidente["identificacion_general"]["fecha_ocurrencia"],
                incidente["identificacion_general"]["alcance_geografico"],
                incidente["descripcion_alcance"]["servicios_interrumpidos"],
                incidente["descripcion_alcance"]["impacto_preliminar"],
                incidente["analisis_preliminar"]["tipo_amenaza"],
                incidente["causa_raiz"]["analisis_causa_raiz"],
                incidente["causa_raiz"]["lecciones_aprendidas"],
                incidente["causa_raiz"]["recomendaciones_mejora"],
                json.dumps(incidente, ensure_ascii=False),
                json.dumps(incidente["taxonomias"], ensure_ascii=False)
            ))
            
            # Obtener ID del incidente creado
            cursor.execute("SELECT @@IDENTITY")
            incidente_id = cursor.fetchone()[0]
            
            conn.commit()
            
            return incidente_id
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def _actualizar_en_bd(self, incidente: Dict):
        """
        Actualiza incidente en base de datos
        """
        conn = None
        try:
            conn = get_db_connection()
            if not conn:
                raise Exception("No se pudo conectar a la base de datos")
            
            cursor = conn.cursor()
            incidente_id = incidente["_metadatos"]["incidente_id"]
            
            cursor.execute("""
                UPDATE Incidentes SET
                    Titulo = ?, FechaDeteccion = ?, ResponsableCliente = ?,
                    Criticidad = ?, TipoFlujo = ?, DescripcionInicial = ?,
                    SistemasAfectados = ?, OrigenIncidente = ?, AccionesInmediatas = ?,
                    FechaOcurrencia = ?, AlcanceGeografico = ?, ServiciosInterrumpidos = ?,
                    AnciImpactoPreliminar = ?, AnciTipoAmenaza = ?, CausaRaiz = ?,
                    LeccionesAprendidas = ?, PlanMejora = ?, FormatoSemillaJSON = ?,
                    FechaModificacion = GETDATE(), IndiceTaxonomias = ?
                WHERE IncidenteID = ?
            """, (
                incidente["identificacion_general"]["titulo_incidente"],
                incidente["identificacion_general"]["fecha_deteccion"],
                incidente["analisis_preliminar"]["responsable_cliente"],
                incidente["identificacion_general"]["criticidad"],
                incidente["identificacion_general"]["tipo_registro"],
                incidente["descripcion_alcance"]["descripcion_detallada"],
                incidente["descripcion_alcance"]["sistemas_afectados"],
                incidente["analisis_preliminar"]["origen_ataque"],
                incidente["acciones_inmediatas"]["medidas_contencion"],
                incidente["identificacion_general"]["fecha_ocurrencia"],
                incidente["identificacion_general"]["alcance_geografico"],
                incidente["descripcion_alcance"]["servicios_interrumpidos"],
                incidente["descripcion_alcance"]["impacto_preliminar"],
                incidente["analisis_preliminar"]["tipo_amenaza"],
                incidente["causa_raiz"]["analisis_causa_raiz"],
                incidente["causa_raiz"]["lecciones_aprendidas"],
                incidente["causa_raiz"]["recomendaciones_mejora"],
                json.dumps(incidente, ensure_ascii=False),
                json.dumps(incidente["taxonomias"], ensure_ascii=False),
                incidente_id
            ))
            
            conn.commit()
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def _guardar_taxonomias_en_bd(self, incidente: Dict):
        """
        Guarda las taxonomías y sus evidencias en la BD
        """
        conn = None
        try:
            conn = get_db_connection()
            if not conn:
                return
            
            cursor = conn.cursor()
            incidente_id = incidente["_metadatos"]["incidente_id"]
            
            # Primero eliminar las taxonomías existentes (para simplificar)
            cursor.execute("DELETE FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?", (incidente_id,))
            
            # Insertar las taxonomías activas
            for taxonomia in incidente["taxonomias"]["seleccionadas"]:
                cursor.execute("""
                    INSERT INTO INCIDENTE_TAXONOMIA (
                        IncidenteID, Id_Taxonomia, Comentarios, 
                        FechaAsignacion, CreadoPor
                    ) VALUES (?, ?, ?, GETDATE(), ?)
                """, (
                    incidente_id,
                    taxonomia["taxonomia_id"],
                    json.dumps({
                        "porque_seleccionada": taxonomia["porque_seleccionada"],
                        "observaciones": taxonomia["observaciones_adicionales"],
                        "numero_orden": taxonomia["numero_orden"],
                        "id_unico": taxonomia["id_unico"]
                    }),
                    incidente["_metadatos"]["usuario_modificacion"]
                ))
            
            conn.commit()
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error guardando taxonomías: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def _reconstruir_desde_bd(self, indice_unico: str) -> Optional[Dict]:
        """
        Reconstruye incidente desde BD si no hay semillas
        """
        conn = None
        try:
            conn = get_db_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            
            # Buscar por IDVisible o indice_unico
            cursor.execute("""
                SELECT * FROM Incidentes 
                WHERE IDVisible = ? OR indice_unico = ?
            """, (indice_unico, indice_unico))
            
            resultado = cursor.fetchone()
            if not resultado:
                return None
            
            # Si hay JSON guardado, usarlo
            columnas = [desc[0] for desc in cursor.description]
            
            # Buscar columna FormatoSemillaJSON
            json_index = None
            for i, col in enumerate(columnas):
                if col == 'FormatoSemillaJSON':
                    json_index = i
                    break
            
            if json_index and resultado[json_index]:
                try:
                    incidente = json.loads(resultado[json_index])
                    # Verificar que tenga la estructura correcta
                    if "_metadatos" in incidente:
                        return incidente
                except:
                    pass
            
            # Si no hay JSON o es inválido, reconstruir desde campos
            incidente = json.loads(json.dumps(self.formato_maestro))
            
            # Mapear campos conocidos
            id_index = columnas.index('IncidenteID') if 'IncidenteID' in columnas else 0
            empresa_index = columnas.index('EmpresaID') if 'EmpresaID' in columnas else 1
            titulo_index = columnas.index('Titulo') if 'Titulo' in columnas else 2
            
            incidente["_metadatos"]["incidente_id"] = resultado[id_index]
            incidente["_metadatos"]["empresa_id"] = resultado[empresa_index]
            incidente["_metadatos"]["indice_unico"] = indice_unico
            incidente["identificacion_general"]["titulo_incidente"] = resultado[titulo_index] or ""
            
            # TODO: Mapear más campos según sea necesario
            
            return incidente
            
        except Exception as e:
            print(f"Error reconstruyendo desde BD: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()
    
    def _limpiar_archivo_edicion(self, indice_unico: str):
        """
        Limpia archivo temporal de edición
        """
        try:
            directorio_semillas = os.path.join(self.ruta_temp, "semillas")
            nombre_archivo = f"{indice_unico}_semilla_editando.json"
            ruta_archivo = os.path.join(directorio_semillas, nombre_archivo)
            
            if os.path.exists(ruta_archivo):
                os.remove(ruta_archivo)
                print(f"✅ Archivo de edición limpiado: {nombre_archivo}")
                
        except Exception as e:
            print(f"Error limpiando archivo edición: {str(e)}")
    
    def _mapear_datos_entrada(self, incidente: Dict, datos: Dict) -> Dict:
        """
        Mapea datos de entrada al formato maestro
        """
        # 1. Identificación General
        campos_identificacion = [
            "tipo_registro", "titulo_incidente", "fecha_deteccion",
            "fecha_ocurrencia", "criticidad", "alcance_geografico"
        ]
        for campo in campos_identificacion:
            if campo in datos:
                incidente["identificacion_general"][campo] = datos[campo]
        
        # 2. Descripción y Alcance
        campos_descripcion = [
            "descripcion_detallada", "impacto_preliminar",
            "sistemas_afectados", "servicios_interrumpidos"
        ]
        for campo in campos_descripcion:
            if campo in datos:
                incidente["descripcion_alcance"][campo] = datos[campo]
        
        # 3. Análisis Preliminar
        campos_analisis = [
            "tipo_amenaza", "origen_ataque", "responsable_cliente"
        ]
        for campo in campos_analisis:
            if campo in datos:
                incidente["analisis_preliminar"][campo] = datos[campo]
        
        # 5. Acciones Inmediatas
        if "medidas_contencion" in datos:
            incidente["acciones_inmediatas"]["medidas_contencion"] = datos["medidas_contencion"]
        
        # 6. Causa Raíz
        campos_causa = [
            "analisis_causa_raiz", "lecciones_aprendidas", "recomendaciones_mejora"
        ]
        for campo in campos_causa:
            if campo in datos:
                incidente["causa_raiz"][campo] = datos[campo]
        
        return incidente


# Instancia global del unificador
unificador = IncidenteUnificador()

# Funciones de conveniencia para usar en los módulos existentes
def crear_incidente_unificado(datos_entrada: Dict, usuario: Dict) -> Tuple[Dict, str]:
    """Crea un incidente usando el formato unificado"""
    return unificador.crear_incidente_nuevo(datos_entrada, usuario)

def cargar_incidente_unificado(indice_unico: str, usuario: Dict) -> Tuple[Optional[Dict], str]:
    """Carga un incidente en formato unificado para edición"""
    return unificador.cargar_incidente_para_edicion(indice_unico, usuario)

def guardar_incidente_unificado(incidente: Dict, usuario: Dict) -> Tuple[Dict, str]:
    """Guarda un incidente editado manteniendo el formato unificado"""
    return unificador.guardar_incidente_editado(incidente, usuario)

def agregar_taxonomia_unificada(incidente: Dict, taxonomia_data: Dict) -> Dict:
    """Agrega una taxonomía al incidente"""
    return unificador.agregar_taxonomia(incidente, taxonomia_data)

def eliminar_taxonomia_unificada(incidente: Dict, id_unico_taxonomia: str) -> Dict:
    """Elimina una taxonomía del incidente"""
    return unificador.eliminar_taxonomia(incidente, id_unico_taxonomia)

def agregar_evidencia_taxonomia_unificada(incidente: Dict, id_unico_taxonomia: str, 
                                         archivo_info: Dict) -> Tuple[Dict, str]:
    """Agrega una evidencia a una taxonomía específica"""
    return unificador.agregar_evidencia_taxonomia(incidente, id_unico_taxonomia, archivo_info)
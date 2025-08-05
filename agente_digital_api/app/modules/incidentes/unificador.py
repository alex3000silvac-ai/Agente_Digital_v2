# unificador.py
"""
Módulo Unificador de Formato de Incidentes
Garantiza consistencia entre creación, edición y guardado
Implementa manejo mejorado de taxonomías múltiples con evidencias jerárquicas
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

class UnificadorIncidentes:
    """
    Clase principal para unificar el formato de incidentes
    Asegura que el formato sea idéntico en todo el ciclo de vida
    """
    
    # Versión del formato para control de compatibilidad
    VERSION_FORMATO = "2.0"
    
    # Estructura base del incidente
    ESTRUCTURA_BASE = {
        "metadata": {
            "version_formato": VERSION_FORMATO,
            "timestamp_creacion": None,
            "timestamp_actualizacion": None,
            "estado_temporal": "borrador",  # borrador, semilla_original, semilla_base, en_edicion
            "hash_integridad": None
        },
        
        # Sección 1: Información General
        "1": {
            "tipo_persona": "",
            "nombre_informante": "",
            "rut_informante": "",
            "email_informante": "",
            "telefono_informante": "",
            "region": "",
            "tiene_representante": False,
            "nombre_representante": "",
            "rut_representante": "",
            "email_representante": "",
            "telefono_representante": "",
            # CAMPOS ANCI OBLIGATORIOS
            "empresa": {
                "razon_social": "",
                "rut": "",
                "tipo_entidad": "",  # OIV o PSE
                "sector_esencial": ""
            },
            "contacto_emergencia": {
                "nombre_reportante": "",
                "cargo_reportante": "",
                "telefono_24_7": "",
                "email_oficial_seguridad": ""
            }
        },
        
        # Sección 2: Identificación y Clasificación
        "2": {
            "titulo": "",
            "descripcion": "",
            "fecha_incidente": "",
            "hora_incidente": "",
            "incidente_critico": False,
            "estado_operacional": "",
            "tipo_servicio_afectado": "",
            "impacto_operacional": "",
            "detectado_por": "",
            "descripcion_deteccion": "",
            "evidencias": {
                "contador": 0,
                "items": []
            },
            # CAMPOS ANCI OBLIGATORIOS
            "sistemas_afectados": [],
            "servicios_interrumpidos": "",
            "alcance_geografico": "",
            "duracion_estimada_horas": 0,
            "incidente_en_curso": True,
            "contencion_aplicada": False,
            "descripcion_estado_actual": ""
        },
        
        # Sección 3: Evaluación de Impacto
        "3": {
            "afectacion_servicio": "",
            "cantidad_usuarios_afectados": 0,
            "tipo_usuarios_afectados": "",
            "impacto_economico": "",
            "impacto_reputacional": "",
            "impacto_operativo": "",
            "otros_impactos": "",
            "evidencias": {
                "contador": 0,
                "items": []
            }
        },
        
        # Sección 4: Taxonomías MEJORADA
        "4": {
            "taxonomias": {
                "version_estructura": VERSION_FORMATO,
                "seleccionadas": [],
                "contador_global": 0,
                "ultimo_cambio": None,
                "historial_cambios": []
            }
        },
        
        # Sección 5: Respuesta y Mitigación
        "5": {
            "acciones_inmediatas": "",
            "fecha_inicio_mitigacion": "",
            "hora_inicio_mitigacion": "",
            "medidas_contencion": "",
            "se_activo_protocolo": False,
            "protocolo_activado": "",
            "evidencias": {
                "contador": 0,
                "items": []
            },
            # CAMPOS ANCI OBLIGATORIOS
            "sistemas_aislados": [],
            "solicitar_csirt": False,
            "tipo_apoyo_csirt": ""
        },
        
        # Sección 6: Análisis de Causa
        "6": {
            "analisis_preliminar": "",
            "causa_raiz_identificada": False,
            "descripcion_causa_raiz": "",
            "factores_contribuyentes": "",
            "evidencias": {
                "contador": 0,
                "items": []
            }
        },
        
        # Sección 7: Lecciones Aprendidas
        "7": {
            "acciones_correctivas": "",
            "acciones_preventivas": "",
            "mejoras_procesos": "",
            "actualizacion_documentacion": "",
            "capacitacion_requerida": ""
        },
        
        # Sección 8: Seguimiento
        "8": {
            "responsable_seguimiento": "",
            "fecha_compromiso_acciones": "",
            "metricas_seguimiento": "",
            "periodicidad_revision": "",
            "observaciones_adicionales": ""
        },
        
        # Sección 9: Análisis Técnico ANCI (Nueva sección para campos adicionales)
        "9": {
            "vector_ataque": "",
            "vulnerabilidad_explotada": "",
            "volumen_datos_gb": 0,
            "efectos_colaterales": "",
            "cronologia_detallada": [],
            "iocs": {
                "ips_sospechosas": [],
                "hashes_malware": [],
                "dominios_maliciosos": [],
                "urls_maliciosas": [],
                "cuentas_comprometidas": []
            },
            "coordinaciones": {
                "notificacion_regulador": False,
                "regulador_notificado": "",
                "denuncia_policial": False,
                "numero_parte_policial": "",
                "proveedores_contactados": False,
                "comunicacion_publica": False
            },
            "plan_accion_oiv": {
                "programa_restauracion": "",
                "responsables_administrativos": "",
                "tiempo_restablecimiento_horas": 0,
                "recursos_necesarios": "",
                "acciones_corto_plazo": "",
                "acciones_mediano_plazo": "",
                "acciones_largo_plazo": ""
            },
            "impacto_economico": {
                "costos_recuperacion": 0,
                "perdidas_operativas": 0,
                "costos_terceros": 0
            },
            "tracking_reportes": {
                "alerta_temprana_enviada": False,
                "fecha_alerta_temprana": "",
                "informe_preliminar_enviado": False,
                "fecha_informe_preliminar": "",
                "informe_completo_enviado": False,
                "fecha_informe_completo": "",
                "plan_accion_enviado": False,
                "fecha_plan_accion": "",
                "informe_final_enviado": False,
                "fecha_informe_final": ""
            }
        }
    }
    
    @classmethod
    def crear_estructura_incidente(cls, datos_iniciales: Optional[Dict] = None) -> Dict:
        """
        Crea una nueva estructura de incidente con formato unificado
        
        Args:
            datos_iniciales: Datos opcionales para inicializar el incidente
            
        Returns:
            Dict con la estructura completa del incidente
        """
        import copy
        estructura = copy.deepcopy(cls.ESTRUCTURA_BASE)
        
        # Establecer metadata
        timestamp_actual = datetime.now().isoformat()
        estructura["metadata"]["timestamp_creacion"] = timestamp_actual
        estructura["metadata"]["timestamp_actualizacion"] = timestamp_actual
        
        # Si hay datos iniciales, fusionarlos
        if datos_iniciales:
            estructura = cls._fusionar_datos(estructura, datos_iniciales)
        
        return estructura
    
    @classmethod
    def agregar_taxonomia(cls, incidente: Dict, taxonomia_id: int, 
                         datos_taxonomia: Optional[Dict] = None) -> Dict:
        """
        Agrega una taxonomía con soporte para múltiples selecciones
        
        Args:
            incidente: Estructura del incidente
            taxonomia_id: ID de la taxonomía a agregar
            datos_taxonomia: Datos adicionales de la taxonomía
            
        Returns:
            Incidente actualizado con la nueva taxonomía
        """
        taxonomias = incidente["4"]["taxonomias"]
        
        # Verificar si ya existe
        for tax in taxonomias["seleccionadas"]:
            if tax["taxonomia_id"] == taxonomia_id and tax["estado"] == "activo":
                return incidente  # Ya existe, no duplicar
        
        # Incrementar contador global
        taxonomias["contador_global"] += 1
        numero_orden = taxonomias["contador_global"]
        
        # Crear nueva entrada de taxonomía
        nueva_taxonomia = {
            "id_unico": str(uuid.uuid4()),
            "taxonomia_id": taxonomia_id,
            "numero_orden": numero_orden,
            "estado": "activo",
            "version": 1,
            "fecha_asignacion": datetime.now().isoformat(),
            "datos": datos_taxonomia or {},
            "evidencias": {
                "contador": 0,
                "items": []
            }
        }
        
        # Agregar al historial
        cambio = {
            "timestamp": datetime.now().isoformat(),
            "accion": "agregar_taxonomia",
            "taxonomia_id": taxonomia_id,
            "numero_orden": numero_orden
        }
        taxonomias["historial_cambios"].append(cambio)
        
        # Actualizar timestamp
        taxonomias["ultimo_cambio"] = datetime.now().isoformat()
        taxonomias["seleccionadas"].append(nueva_taxonomia)
        
        return incidente
    
    @classmethod
    def agregar_evidencia_taxonomia(cls, incidente: Dict, taxonomia_uuid: str,
                                   archivo_info: Dict) -> Dict:
        """
        Agrega evidencia a una taxonomía específica con numeración jerárquica
        
        Args:
            incidente: Estructura del incidente
            taxonomia_uuid: UUID único de la taxonomía
            archivo_info: Información del archivo (nombre, ruta, etc.)
            
        Returns:
            Incidente actualizado
        """
        taxonomias = incidente["4"]["taxonomias"]["seleccionadas"]
        
        # Buscar la taxonomía por UUID
        taxonomia = None
        for tax in taxonomias:
            if tax["id_unico"] == taxonomia_uuid and tax["estado"] == "activo":
                taxonomia = tax
                break
        
        if not taxonomia:
            raise ValueError(f"Taxonomía con UUID {taxonomia_uuid} no encontrada")
        
        # Incrementar contador de evidencias
        taxonomia["evidencias"]["contador"] += 1
        numero_evidencia = taxonomia["evidencias"]["contador"]
        
        # Crear numeración jerárquica: 4.4.X.Y
        numero_jerarquico = f"4.4.{taxonomia['numero_orden']}.{numero_evidencia}"
        
        # Crear entrada de evidencia
        nueva_evidencia = {
            "numero": numero_jerarquico,
            "archivo": archivo_info.get("ruta", ""),
            "nombre": archivo_info.get("nombre", ""),
            "hash_md5": archivo_info.get("hash_md5", ""),
            "tamano_kb": archivo_info.get("tamano_kb", 0),
            "tipo_mime": archivo_info.get("tipo_mime", ""),
            "fecha_subida": datetime.now().isoformat(),
            "subido_por": archivo_info.get("subido_por", ""),
            "estado": "verificado" if archivo_info.get("hash_md5") else "pendiente",
            "version": 1
        }
        
        taxonomia["evidencias"]["items"].append(nueva_evidencia)
        taxonomia["version"] += 1
        
        # Actualizar metadata del incidente
        incidente["metadata"]["timestamp_actualizacion"] = datetime.now().isoformat()
        
        return incidente
    
    @classmethod
    def eliminar_taxonomia(cls, incidente: Dict, taxonomia_uuid: str) -> Dict:
        """
        Marca una taxonomía como eliminada (soft delete)
        
        Args:
            incidente: Estructura del incidente
            taxonomia_uuid: UUID de la taxonomía a eliminar
            
        Returns:
            Incidente actualizado
        """
        taxonomias = incidente["4"]["taxonomias"]["seleccionadas"]
        
        for tax in taxonomias:
            if tax["id_unico"] == taxonomia_uuid:
                tax["estado"] = "eliminado"
                tax["fecha_eliminacion"] = datetime.now().isoformat()
                
                # Agregar al historial
                cambio = {
                    "timestamp": datetime.now().isoformat(),
                    "accion": "eliminar_taxonomia",
                    "taxonomia_id": tax["taxonomia_id"],
                    "numero_orden": tax["numero_orden"]
                }
                incidente["4"]["taxonomias"]["historial_cambios"].append(cambio)
                break
        
        return incidente
    
    @classmethod
    def agregar_evidencia_seccion(cls, incidente: Dict, seccion: str,
                                 archivo_info: Dict) -> Dict:
        """
        Agrega evidencia a una sección específica (2, 3, 5, 6)
        
        Args:
            incidente: Estructura del incidente
            seccion: Número de sección ("2", "3", "5", "6")
            archivo_info: Información del archivo
            
        Returns:
            Incidente actualizado
        """
        if seccion not in ["2", "3", "5", "6"]:
            raise ValueError(f"Sección {seccion} no soporta evidencias")
        
        if "evidencias" not in incidente[seccion]:
            raise ValueError(f"Sección {seccion} no tiene estructura de evidencias")
        
        evidencias = incidente[seccion]["evidencias"]
        evidencias["contador"] += 1
        
        # Mapeo de secciones a numeración
        mapeo_seccion = {
            "2": "2.5",
            "3": "3.4",
            "5": "5.2",
            "6": "6.4"
        }
        
        numero_evidencia = f"{mapeo_seccion[seccion]}.{evidencias['contador']}"
        
        nueva_evidencia = {
            "numero": numero_evidencia,
            "archivo": archivo_info.get("ruta", ""),
            "nombre": archivo_info.get("nombre", ""),
            "hash_md5": archivo_info.get("hash_md5", ""),
            "tamano_kb": archivo_info.get("tamano_kb", 0),
            "fecha_subida": datetime.now().isoformat(),
            "subido_por": archivo_info.get("subido_por", ""),
            "estado": "activo"
        }
        
        evidencias["items"].append(nueva_evidencia)
        
        # Actualizar metadata
        incidente["metadata"]["timestamp_actualizacion"] = datetime.now().isoformat()
        
        return incidente
    
    @classmethod
    def validar_estructura(cls, incidente: Dict) -> tuple[bool, List[str]]:
        """
        Valida que el incidente tenga la estructura correcta
        
        Args:
            incidente: Estructura a validar
            
        Returns:
            Tupla (es_valido, lista_errores)
        """
        errores = []
        
        # Validar metadata
        if "metadata" not in incidente:
            errores.append("Falta sección metadata")
        else:
            if incidente["metadata"].get("version_formato") != cls.VERSION_FORMATO:
                errores.append(f"Versión de formato incorrecta")
        
        # Validar secciones principales
        for seccion in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            if seccion not in incidente:
                errores.append(f"Falta sección {seccion}")
        
        # Validar estructura de taxonomías
        if "4" in incidente:
            taxonomias = incidente["4"].get("taxonomias", {})
            if not isinstance(taxonomias.get("seleccionadas"), list):
                errores.append("Taxonomías debe tener lista 'seleccionadas'")
        
        # Validar campos requeridos
        if "1" in incidente:
            if not incidente["1"].get("nombre_informante"):
                errores.append("Nombre del informante es requerido")
            if not incidente["1"].get("email_informante"):
                errores.append("Email del informante es requerido")
        
        if "2" in incidente:
            if not incidente["2"].get("titulo"):
                errores.append("Título del incidente es requerido")
            if not incidente["2"].get("fecha_incidente"):
                errores.append("Fecha del incidente es requerida")
        
        return len(errores) == 0, errores
    
    @classmethod
    def exportar_para_guardar(cls, incidente: Dict) -> Dict:
        """
        Prepara el incidente para ser guardado en BD
        Limpia campos temporales y calcula hash de integridad
        
        Args:
            incidente: Estructura del incidente
            
        Returns:
            Incidente preparado para guardar
        """
        import hashlib
        import copy
        
        # Hacer copia para no modificar original
        incidente_guardar = copy.deepcopy(incidente)
        
        # Actualizar timestamp
        incidente_guardar["metadata"]["timestamp_actualizacion"] = datetime.now().isoformat()
        
        # Calcular hash de integridad
        contenido_hash = json.dumps(incidente_guardar, sort_keys=True)
        hash_integridad = hashlib.sha256(contenido_hash.encode()).hexdigest()
        incidente_guardar["metadata"]["hash_integridad"] = hash_integridad
        
        return incidente_guardar
    
    @classmethod
    def importar_desde_bd(cls, datos_bd: Dict) -> Dict:
        """
        Importa datos desde la BD y los convierte al formato unificado
        
        Args:
            datos_bd: Datos crudos de la BD
            
        Returns:
            Incidente en formato unificado
        """
        # Si ya tiene el formato correcto, validar y devolver
        if datos_bd.get("metadata", {}).get("version_formato") == cls.VERSION_FORMATO:
            es_valido, errores = cls.validar_estructura(datos_bd)
            if es_valido:
                return datos_bd
        
        # Si no, intentar convertir desde formato antiguo
        return cls._convertir_formato_antiguo(datos_bd)
    
    @classmethod
    def _fusionar_datos(cls, estructura: Dict, datos: Dict) -> Dict:
        """
        Fusiona datos en la estructura manteniendo el formato
        """
        for seccion, contenido in datos.items():
            if seccion in estructura and isinstance(contenido, dict):
                estructura[seccion].update(contenido)
        return estructura
    
    @classmethod
    def _convertir_formato_antiguo(cls, datos_antiguos: Dict) -> Dict:
        """
        Convierte datos del formato antiguo al nuevo formato unificado
        """
        # Lógica de conversión específica según el formato antiguo
        # Esta función se implementaría según el formato actual en uso
        estructura = cls.crear_estructura_incidente()
        
        # Mapear campos conocidos
        if "informante" in datos_antiguos:
            estructura["1"].update(datos_antiguos["informante"])
        
        if "incidente" in datos_antiguos:
            estructura["2"].update(datos_antiguos["incidente"])
        
        # Continuar con mapeo según sea necesario...
        
        return estructura
    
    @classmethod
    def migrar_campos_anci(cls, incidente: Dict, datos_bd: Dict) -> Dict:
        """
        Migra campos ANCI desde la BD a la estructura JSON del incidente
        
        Args:
            incidente: Estructura JSON del incidente
            datos_bd: Datos del incidente desde la BD (incluyendo campos ANCI)
            
        Returns:
            Incidente actualizado con campos ANCI
        """
        # Migrar datos de empresa
        if "1" in incidente:
            incidente["1"]["empresa"]["razon_social"] = datos_bd.get("RazonSocial", "")
            incidente["1"]["empresa"]["rut"] = datos_bd.get("RUT", "")
            incidente["1"]["empresa"]["tipo_entidad"] = datos_bd.get("TipoEmpresa", "")
            incidente["1"]["empresa"]["sector_esencial"] = datos_bd.get("SectorEsencial", "")
            
            # Migrar contacto de emergencia
            incidente["1"]["contacto_emergencia"]["nombre_reportante"] = datos_bd.get("NombreReportante", "")
            incidente["1"]["contacto_emergencia"]["cargo_reportante"] = datos_bd.get("CargoReportante", "")
            incidente["1"]["contacto_emergencia"]["telefono_24_7"] = datos_bd.get("TelefonoEmergencia", "")
            incidente["1"]["contacto_emergencia"]["email_oficial_seguridad"] = datos_bd.get("EmailOficialSeguridad", "")
        
        # Migrar campos de estado e impacto
        if "2" in incidente:
            incidente["2"]["sistemas_afectados"] = datos_bd.get("SistemasAfectados", "").split(",") if datos_bd.get("SistemasAfectados") else []
            incidente["2"]["servicios_interrumpidos"] = datos_bd.get("ServiciosInterrumpidos", "")
            incidente["2"]["alcance_geografico"] = datos_bd.get("AlcanceGeografico", "")
            incidente["2"]["duracion_estimada_horas"] = datos_bd.get("DuracionEstimadaHoras", 0) or 0
            incidente["2"]["incidente_en_curso"] = datos_bd.get("IncidenteEnCurso", True)
            incidente["2"]["contencion_aplicada"] = datos_bd.get("ContencionAplicada", False)
            incidente["2"]["descripcion_estado_actual"] = datos_bd.get("DescripcionEstadoActual", "")
        
        # Migrar campos de respuesta
        if "5" in incidente:
            incidente["5"]["sistemas_aislados"] = datos_bd.get("SistemasAislados", "").split(",") if datos_bd.get("SistemasAislados") else []
            incidente["5"]["solicitar_csirt"] = datos_bd.get("SolicitarCSIRT", False)
            incidente["5"]["tipo_apoyo_csirt"] = datos_bd.get("TipoApoyoCSIRT", "")
        
        # Migrar campos técnicos ANCI (sección 9)
        if "9" in incidente:
            incidente["9"]["vector_ataque"] = datos_bd.get("VectorAtaque", "")
            incidente["9"]["vulnerabilidad_explotada"] = datos_bd.get("VulnerabilidadExplotada", "")
            incidente["9"]["volumen_datos_gb"] = datos_bd.get("VolumenDatosComprometidosGB", 0) or 0
            incidente["9"]["efectos_colaterales"] = datos_bd.get("EfectosColaterales", "")
            
            # Migrar IoCs
            incidente["9"]["iocs"]["ips_sospechosas"] = datos_bd.get("IPsSospechosas", "").split("\n") if datos_bd.get("IPsSospechosas") else []
            incidente["9"]["iocs"]["hashes_malware"] = datos_bd.get("HashesMalware", "").split("\n") if datos_bd.get("HashesMalware") else []
            incidente["9"]["iocs"]["dominios_maliciosos"] = datos_bd.get("DominiosMaliciosos", "").split("\n") if datos_bd.get("DominiosMaliciosos") else []
            incidente["9"]["iocs"]["urls_maliciosas"] = datos_bd.get("URLsMaliciosas", "").split("\n") if datos_bd.get("URLsMaliciosas") else []
            incidente["9"]["iocs"]["cuentas_comprometidas"] = datos_bd.get("CuentasComprometidas", "").split("\n") if datos_bd.get("CuentasComprometidas") else []
            
            # Migrar coordinaciones
            incidente["9"]["coordinaciones"]["notificacion_regulador"] = datos_bd.get("NotificacionRegulador", False)
            incidente["9"]["coordinaciones"]["regulador_notificado"] = datos_bd.get("ReguladorNotificado", "")
            incidente["9"]["coordinaciones"]["denuncia_policial"] = datos_bd.get("DenunciaPolicial", False)
            incidente["9"]["coordinaciones"]["numero_parte_policial"] = datos_bd.get("NumeroPartePolicial", "")
            incidente["9"]["coordinaciones"]["proveedores_contactados"] = datos_bd.get("ContactoProveedoresSeguridad", False)
            incidente["9"]["coordinaciones"]["comunicacion_publica"] = datos_bd.get("ComunicacionPublica", False)
            
            # Migrar plan OIV
            incidente["9"]["plan_accion_oiv"]["programa_restauracion"] = datos_bd.get("ProgramaRestauracion", "")
            incidente["9"]["plan_accion_oiv"]["responsables_administrativos"] = datos_bd.get("ResponsablesAdministrativos", "")
            incidente["9"]["plan_accion_oiv"]["tiempo_restablecimiento_horas"] = datos_bd.get("TiempoRestablecimientoHoras", 0) or 0
            incidente["9"]["plan_accion_oiv"]["recursos_necesarios"] = datos_bd.get("RecursosNecesarios", "")
            incidente["9"]["plan_accion_oiv"]["acciones_corto_plazo"] = datos_bd.get("AccionesCortoPlazo", "")
            incidente["9"]["plan_accion_oiv"]["acciones_mediano_plazo"] = datos_bd.get("AccionesMedianoPlazo", "")
            incidente["9"]["plan_accion_oiv"]["acciones_largo_plazo"] = datos_bd.get("AccionesLargoPlazo", "")
            
            # Migrar impacto económico
            incidente["9"]["impacto_economico"]["costos_recuperacion"] = datos_bd.get("CostosRecuperacion", 0) or 0
            incidente["9"]["impacto_economico"]["perdidas_operativas"] = datos_bd.get("PerdidasOperativas", 0) or 0
            incidente["9"]["impacto_economico"]["costos_terceros"] = datos_bd.get("CostosTerceros", 0) or 0
            
            # Migrar tracking de reportes
            incidente["9"]["tracking_reportes"]["alerta_temprana_enviada"] = datos_bd.get("AlertaTempranaEnviada", False)
            incidente["9"]["tracking_reportes"]["fecha_alerta_temprana"] = datos_bd.get("FechaAlertaTemprana", "")
            incidente["9"]["tracking_reportes"]["informe_preliminar_enviado"] = datos_bd.get("InformePreliminarEnviado", False)
            incidente["9"]["tracking_reportes"]["fecha_informe_preliminar"] = datos_bd.get("FechaInformePreliminar", "")
            incidente["9"]["tracking_reportes"]["informe_completo_enviado"] = datos_bd.get("InformeCompletoEnviado", False)
            incidente["9"]["tracking_reportes"]["fecha_informe_completo"] = datos_bd.get("FechaInformeCompleto", "")
            incidente["9"]["tracking_reportes"]["plan_accion_enviado"] = datos_bd.get("PlanAccionEnviado", False)
            incidente["9"]["tracking_reportes"]["fecha_plan_accion"] = datos_bd.get("FechaPlanAccion", "")
            incidente["9"]["tracking_reportes"]["informe_final_enviado"] = datos_bd.get("InformeFinalEnviado", False)
            incidente["9"]["tracking_reportes"]["fecha_informe_final"] = datos_bd.get("FechaInformeFinal", "")
            
            # Migrar cronología si existe
            if datos_bd.get("CronologiaDetallada"):
                try:
                    import json
                    incidente["9"]["cronologia_detallada"] = json.loads(datos_bd["CronologiaDetallada"])
                except:
                    incidente["9"]["cronologia_detallada"] = []
        
        return incidente
    
    @classmethod
    def validar_campos_anci(cls, incidente: Dict, tipo_reporte: str = "alerta_temprana") -> tuple[bool, List[str]]:
        """
        Valida que el incidente tenga todos los campos obligatorios ANCI
        
        Args:
            incidente: Estructura del incidente
            tipo_reporte: Tipo de reporte ANCI a validar
            
        Returns:
            Tupla (es_valido, lista_campos_faltantes)
        """
        campos_faltantes = []
        
        if tipo_reporte == "alerta_temprana":
            # Validar campos de empresa
            if not incidente.get("1", {}).get("empresa", {}).get("razon_social"):
                campos_faltantes.append("Razón Social de la empresa")
            if not incidente.get("1", {}).get("empresa", {}).get("tipo_entidad"):
                campos_faltantes.append("Tipo de entidad (OIV/PSE)")
            if not incidente.get("1", {}).get("empresa", {}).get("sector_esencial"):
                campos_faltantes.append("Sector esencial")
                
            # Validar contacto de emergencia
            contacto = incidente.get("1", {}).get("contacto_emergencia", {})
            if not contacto.get("nombre_reportante"):
                campos_faltantes.append("Nombre del reportante ANCI")
            if not contacto.get("cargo_reportante"):
                campos_faltantes.append("Cargo del reportante")
            if not contacto.get("telefono_24_7"):
                campos_faltantes.append("Teléfono de emergencia 24/7")
            if not contacto.get("email_oficial_seguridad"):
                campos_faltantes.append("Email oficial de seguridad")
                
            # Validar datos del incidente
            if not incidente.get("2", {}).get("descripcion"):
                campos_faltantes.append("Descripción del incidente")
            if not incidente.get("2", {}).get("sistemas_afectados"):
                campos_faltantes.append("Sistemas afectados")
            if not incidente.get("2", {}).get("alcance_geografico"):
                campos_faltantes.append("Alcance geográfico")
                
            # Validar taxonomías
            taxonomias = incidente.get("4", {}).get("taxonomias", {}).get("seleccionadas", [])
            taxonomias_activas = [t for t in taxonomias if t.get("estado") == "activo"]
            if len(taxonomias_activas) == 0:
                campos_faltantes.append("Al menos una taxonomía ANCI")
                
            # Validar estado actual
            if incidente.get("2", {}).get("incidente_en_curso") is None:
                campos_faltantes.append("Estado del incidente (en curso/contenido)")
            if not incidente.get("2", {}).get("descripcion_estado_actual"):
                campos_faltantes.append("Descripción del estado actual")
                
            # Validar medidas de contención
            if not incidente.get("5", {}).get("medidas_contencion"):
                campos_faltantes.append("Medidas de contención aplicadas")
        
        return len(campos_faltantes) == 0, campos_faltantes
    
    @classmethod
    def obtener_resumen_taxonomias(cls, incidente: Dict) -> Dict:
        """
        Obtiene un resumen del estado de las taxonomías
        
        Args:
            incidente: Estructura del incidente
            
        Returns:
            Resumen con estadísticas
        """
        taxonomias = incidente["4"]["taxonomias"]["seleccionadas"]
        
        activas = [t for t in taxonomias if t["estado"] == "activo"]
        total_evidencias = sum(t["evidencias"]["contador"] for t in activas)
        
        return {
            "total_taxonomias": len(activas),
            "total_evidencias": total_evidencias,
            "taxonomias": [
                {
                    "id": t["taxonomia_id"],
                    "numero_orden": t["numero_orden"],
                    "evidencias": t["evidencias"]["contador"]
                }
                for t in activas
            ]
        }
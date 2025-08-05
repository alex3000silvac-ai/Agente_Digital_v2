# validador.py
"""
Módulo de Validación Centralizada para Incidentes
Valida datos según especificaciones de incidente.txt y tablas_bd.txt
Integra con el módulo de diagnóstico para verificación completa
"""

import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import os
import sys

# Agregar ruta para importar módulo de diagnóstico
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ValidadorIncidentes:
    """
    Validador central para todos los datos de incidentes
    """
    
    # Patrones de validación
    PATRON_RUT = re.compile(r'^\d{7,8}-[\dkK]$')
    PATRON_EMAIL = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PATRON_TELEFONO = re.compile(r'^\+?[\d\s\-\(\)]+$')
    PATRON_INDICE_UNICO = re.compile(r'^\d+_\d+_\d+_\d+_[A-Z_]+$')
    
    # Extensiones permitidas para evidencias
    EXTENSIONES_PERMITIDAS = {
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', 
        '.jpeg', '.txt', '.csv', '.zip', '.rar', '.msg', '.eml'
    }
    
    # Tamaño máximo de archivo (en MB)
    TAMANO_MAXIMO_MB = 50
    
    @classmethod
    def validar_incidente_completo(cls, incidente: Dict, 
                                   validar_archivos: bool = True) -> Tuple[bool, List[str]]:
        """
        Valida un incidente completo según todas las reglas
        
        Args:
            incidente: Datos del incidente
            validar_archivos: Si debe validar existencia de archivos físicos
            
        Returns:
            Tupla (es_valido, lista_errores)
        """
        errores = []
        
        # Validar estructura básica
        es_valido_estructura, errores_estructura = cls._validar_estructura(incidente)
        errores.extend(errores_estructura)
        
        # Validar sección 1 - Información del informante
        if "1" in incidente:
            es_valido_1, errores_1 = cls.validar_seccion_1(incidente["1"])
            errores.extend(errores_1)
        
        # Validar sección 2 - Identificación
        if "2" in incidente:
            es_valido_2, errores_2 = cls.validar_seccion_2(incidente["2"])
            errores.extend(errores_2)
        
        # Validar sección 3 - Evaluación
        if "3" in incidente:
            es_valido_3, errores_3 = cls.validar_seccion_3(incidente["3"])
            errores.extend(errores_3)
        
        # Validar sección 4 - Taxonomías
        if "4" in incidente:
            es_valido_4, errores_4 = cls.validar_seccion_4(incidente["4"])
            errores.extend(errores_4)
        
        # Validar sección 5 - Respuesta
        if "5" in incidente:
            es_valido_5, errores_5 = cls.validar_seccion_5(incidente["5"])
            errores.extend(errores_5)
        
        # Validar sección 6 - Análisis
        if "6" in incidente:
            es_valido_6, errores_6 = cls.validar_seccion_6(incidente["6"])
            errores.extend(errores_6)
        
        # Validar archivos si se requiere
        if validar_archivos:
            es_valido_archivos, errores_archivos = cls._validar_archivos_fisicos(incidente)
            errores.extend(errores_archivos)
        
        return len(errores) == 0, errores
    
    @classmethod
    def validar_seccion_1(cls, seccion: Dict) -> Tuple[bool, List[str]]:
        """Valida sección 1 - Información del informante"""
        errores = []
        
        # Campos requeridos
        if not seccion.get("tipo_persona"):
            errores.append("Tipo de persona es requerido")
        elif seccion["tipo_persona"] not in ["natural", "juridica"]:
            errores.append("Tipo de persona debe ser 'natural' o 'juridica'")
        
        if not seccion.get("nombre_informante"):
            errores.append("Nombre del informante es requerido")
        
        # Validar RUT si existe
        if seccion.get("rut_informante"):
            if not cls.PATRON_RUT.match(seccion["rut_informante"]):
                errores.append("RUT del informante tiene formato inválido")
        
        # Validar email
        if not seccion.get("email_informante"):
            errores.append("Email del informante es requerido")
        elif not cls.PATRON_EMAIL.match(seccion["email_informante"]):
            errores.append("Email del informante tiene formato inválido")
        
        # Validar teléfono si existe
        if seccion.get("telefono_informante"):
            if not cls.PATRON_TELEFONO.match(seccion["telefono_informante"]):
                errores.append("Teléfono del informante tiene formato inválido")
        
        # Si tiene representante, validar sus datos
        if seccion.get("tiene_representante"):
            if not seccion.get("nombre_representante"):
                errores.append("Nombre del representante es requerido")
            
            if seccion.get("rut_representante"):
                if not cls.PATRON_RUT.match(seccion["rut_representante"]):
                    errores.append("RUT del representante tiene formato inválido")
            
            if seccion.get("email_representante"):
                if not cls.PATRON_EMAIL.match(seccion["email_representante"]):
                    errores.append("Email del representante tiene formato inválido")
        
        return len(errores) == 0, errores
    
    @classmethod
    def validar_seccion_2(cls, seccion: Dict) -> Tuple[bool, List[str]]:
        """Valida sección 2 - Identificación y clasificación"""
        errores = []
        
        # Campos requeridos
        if not seccion.get("titulo"):
            errores.append("Título del incidente es requerido")
        elif len(seccion["titulo"]) < 10:
            errores.append("Título debe tener al menos 10 caracteres")
        
        if not seccion.get("descripcion"):
            errores.append("Descripción del incidente es requerida")
        elif len(seccion["descripcion"]) < 50:
            errores.append("Descripción debe tener al menos 50 caracteres")
        
        # Validar fecha
        if not seccion.get("fecha_incidente"):
            errores.append("Fecha del incidente es requerida")
        else:
            try:
                fecha = datetime.strptime(seccion["fecha_incidente"], "%Y-%m-%d")
                if fecha > datetime.now():
                    errores.append("Fecha del incidente no puede ser futura")
            except ValueError:
                errores.append("Fecha del incidente tiene formato inválido (YYYY-MM-DD)")
        
        # Validar hora si existe
        if seccion.get("hora_incidente"):
            try:
                datetime.strptime(seccion["hora_incidente"], "%H:%M")
            except ValueError:
                errores.append("Hora del incidente tiene formato inválido (HH:MM)")
        
        # Validar evidencias si existen
        if "evidencias" in seccion:
            es_valido_ev, errores_ev = cls._validar_evidencias_seccion(
                seccion["evidencias"], "2.5"
            )
            errores.extend(errores_ev)
        
        return len(errores) == 0, errores
    
    @classmethod
    def validar_seccion_3(cls, seccion: Dict) -> Tuple[bool, List[str]]:
        """Valida sección 3 - Evaluación de impacto"""
        errores = []
        
        # Validar cantidad de usuarios afectados
        if "cantidad_usuarios_afectados" in seccion:
            try:
                cantidad = int(seccion["cantidad_usuarios_afectados"])
                if cantidad < 0:
                    errores.append("Cantidad de usuarios afectados no puede ser negativa")
            except (ValueError, TypeError):
                errores.append("Cantidad de usuarios afectados debe ser un número")
        
        # Validar evidencias si existen
        if "evidencias" in seccion:
            es_valido_ev, errores_ev = cls._validar_evidencias_seccion(
                seccion["evidencias"], "3.4"
            )
            errores.extend(errores_ev)
        
        return len(errores) == 0, errores
    
    @classmethod
    def validar_seccion_4(cls, seccion: Dict) -> Tuple[bool, List[str]]:
        """Valida sección 4 - Taxonomías con estructura mejorada"""
        errores = []
        
        if "taxonomias" not in seccion:
            errores.append("Estructura de taxonomías no encontrada")
            return False, errores
        
        taxonomias = seccion["taxonomias"]
        
        # Validar estructura básica
        if "seleccionadas" not in taxonomias:
            errores.append("Lista de taxonomías seleccionadas no encontrada")
        
        if not isinstance(taxonomias.get("seleccionadas"), list):
            errores.append("Taxonomías seleccionadas debe ser una lista")
        else:
            # Validar cada taxonomía
            numeros_orden = set()
            for idx, tax in enumerate(taxonomias["seleccionadas"]):
                if tax.get("estado") != "activo":
                    continue  # Saltar eliminadas
                
                # Validar campos requeridos
                if not tax.get("id_unico"):
                    errores.append(f"Taxonomía {idx+1}: falta ID único")
                
                if not tax.get("taxonomia_id"):
                    errores.append(f"Taxonomía {idx+1}: falta ID de taxonomía")
                
                if not tax.get("numero_orden"):
                    errores.append(f"Taxonomía {idx+1}: falta número de orden")
                else:
                    # Verificar números únicos
                    if tax["numero_orden"] in numeros_orden:
                        errores.append(f"Número de orden {tax['numero_orden']} duplicado")
                    numeros_orden.add(tax["numero_orden"])
                
                # Validar evidencias de taxonomía
                if "evidencias" in tax:
                    for ev_idx, evidencia in enumerate(tax["evidencias"].get("items", [])):
                        # Validar numeración jerárquica
                        numero_esperado = f"4.4.{tax['numero_orden']}.{ev_idx+1}"
                        if evidencia.get("numero") != numero_esperado:
                            errores.append(
                                f"Evidencia mal numerada: esperado {numero_esperado}, "
                                f"encontrado {evidencia.get('numero')}"
                            )
        
        return len(errores) == 0, errores
    
    @classmethod
    def validar_seccion_5(cls, seccion: Dict) -> Tuple[bool, List[str]]:
        """Valida sección 5 - Respuesta y mitigación"""
        errores = []
        
        # Si se activó protocolo, debe especificar cuál
        if seccion.get("se_activo_protocolo") and not seccion.get("protocolo_activado"):
            errores.append("Debe especificar qué protocolo se activó")
        
        # Validar fechas
        if seccion.get("fecha_inicio_mitigacion"):
            try:
                datetime.strptime(seccion["fecha_inicio_mitigacion"], "%Y-%m-%d")
            except ValueError:
                errores.append("Fecha de inicio de mitigación tiene formato inválido")
        
        # Validar evidencias
        if "evidencias" in seccion:
            es_valido_ev, errores_ev = cls._validar_evidencias_seccion(
                seccion["evidencias"], "5.2"
            )
            errores.extend(errores_ev)
        
        return len(errores) == 0, errores
    
    @classmethod
    def validar_seccion_6(cls, seccion: Dict) -> Tuple[bool, List[str]]:
        """Valida sección 6 - Análisis de causa"""
        errores = []
        
        # Si identificó causa raíz, debe describirla
        if seccion.get("causa_raiz_identificada") and not seccion.get("descripcion_causa_raiz"):
            errores.append("Debe describir la causa raíz identificada")
        
        # Validar evidencias
        if "evidencias" in seccion:
            es_valido_ev, errores_ev = cls._validar_evidencias_seccion(
                seccion["evidencias"], "6.4"
            )
            errores.extend(errores_ev)
        
        return len(errores) == 0, errores
    
    @classmethod
    def validar_indice_unico(cls, indice_unico: str) -> Tuple[bool, Dict[str, str]]:
        """
        Valida formato del índice único y extrae componentes
        
        Args:
            indice_unico: Índice a validar
            
        Returns:
            Tupla (es_valido, componentes_dict)
        """
        if not cls.PATRON_INDICE_UNICO.match(indice_unico):
            return False, {}
        
        partes = indice_unico.split('_')
        if len(partes) < 5:
            return False, {}
        
        componentes = {
            "correlativo": partes[0],
            "rut": partes[1],
            "modulo": partes[2],
            "submodulo": partes[3],
            "descripcion": '_'.join(partes[4:])
        }
        
        # Validaciones adicionales
        try:
            int(componentes["correlativo"])
            int(componentes["rut"])
            int(componentes["modulo"])
            int(componentes["submodulo"])
        except ValueError:
            return False, {}
        
        return True, componentes
    
    @classmethod
    def validar_archivo_evidencia(cls, archivo_info: Dict) -> Tuple[bool, List[str]]:
        """
        Valida un archivo de evidencia individual
        
        Args:
            archivo_info: Información del archivo
            
        Returns:
            Tupla (es_valido, lista_errores)
        """
        errores = []
        
        # Validar nombre de archivo
        if not archivo_info.get("nombre"):
            errores.append("Nombre de archivo es requerido")
        else:
            # Verificar extensión
            extension = os.path.splitext(archivo_info["nombre"])[1].lower()
            if extension not in cls.EXTENSIONES_PERMITIDAS:
                errores.append(f"Extensión {extension} no permitida")
        
        # Validar tamaño
        if "tamano_kb" in archivo_info:
            tamano_mb = archivo_info["tamano_kb"] / 1024
            if tamano_mb > cls.TAMANO_MAXIMO_MB:
                errores.append(f"Archivo excede el tamaño máximo de {cls.TAMANO_MAXIMO_MB}MB")
        
        # Validar ruta si existe
        if archivo_info.get("ruta"):
            # Verificar que no contenga caracteres peligrosos
            if ".." in archivo_info["ruta"] or archivo_info["ruta"].startswith("/"):
                errores.append("Ruta de archivo contiene caracteres no permitidos")
        
        return len(errores) == 0, errores
    
    @classmethod
    def _validar_estructura(cls, incidente: Dict) -> Tuple[bool, List[str]]:
        """Valida estructura básica del incidente"""
        errores = []
        
        # Verificar secciones principales
        secciones_requeridas = ["1", "2", "3", "4", "5", "6", "7", "8"]
        for seccion in secciones_requeridas:
            if seccion not in incidente:
                errores.append(f"Falta sección {seccion}")
        
        # Verificar metadata
        if "metadata" not in incidente:
            errores.append("Falta sección metadata")
        
        return len(errores) == 0, errores
    
    @classmethod
    def _validar_evidencias_seccion(cls, evidencias: Dict, 
                                   seccion_numero: str) -> Tuple[bool, List[str]]:
        """Valida estructura de evidencias de una sección"""
        errores = []
        
        if "items" not in evidencias:
            errores.append(f"Sección {seccion_numero}: falta lista de evidencias")
            return False, errores
        
        for idx, evidencia in enumerate(evidencias["items"]):
            # Validar numeración
            numero_esperado = f"{seccion_numero}.{idx+1}"
            if evidencia.get("numero") != numero_esperado:
                errores.append(
                    f"Evidencia mal numerada en {seccion_numero}: "
                    f"esperado {numero_esperado}, encontrado {evidencia.get('numero')}"
                )
            
            # Validar archivo
            es_valido, errores_archivo = cls.validar_archivo_evidencia(evidencia)
            if not es_valido:
                for error in errores_archivo:
                    errores.append(f"Sección {seccion_numero}, evidencia {idx+1}: {error}")
        
        return len(errores) == 0, errores
    
    @classmethod
    def _validar_archivos_fisicos(cls, incidente: Dict) -> Tuple[bool, List[str]]:
        """Valida existencia de archivos físicos referenciados"""
        errores = []
        archivos_verificar = []
        
        # Recolectar todos los archivos referenciados
        for seccion in ["2", "3", "5", "6"]:
            if seccion in incidente and "evidencias" in incidente[seccion]:
                for evidencia in incidente[seccion]["evidencias"].get("items", []):
                    if evidencia.get("archivo"):
                        archivos_verificar.append({
                            "seccion": seccion,
                            "numero": evidencia.get("numero"),
                            "ruta": evidencia["archivo"]
                        })
        
        # Archivos de taxonomías
        if "4" in incidente and "taxonomias" in incidente["4"]:
            for tax in incidente["4"]["taxonomias"].get("seleccionadas", []):
                if tax.get("estado") == "activo":
                    for evidencia in tax.get("evidencias", {}).get("items", []):
                        if evidencia.get("archivo"):
                            archivos_verificar.append({
                                "seccion": "4",
                                "numero": evidencia.get("numero"),
                                "ruta": evidencia["archivo"]
                            })
        
        # Verificar existencia
        for archivo in archivos_verificar:
            if not os.path.exists(archivo["ruta"]):
                errores.append(
                    f"Archivo no encontrado: {archivo['numero']} - {archivo['ruta']}"
                )
        
        return len(errores) == 0, errores
    
    @classmethod
    def integrar_con_diagnostico(cls, indice_unico: str) -> Tuple[bool, Dict]:
        """
        Integra validación con módulo de diagnóstico
        
        Args:
            indice_unico: Índice único del incidente
            
        Returns:
            Tupla (puede_proceder, diagnostico_resultado)
        """
        try:
            from ..admin.diagnostico_incidentes import diagnosticador
            
            # Ejecutar diagnóstico
            resultado = diagnosticador.diagnosticar_incidente(indice_unico)
            
            # Determinar si puede proceder
            puede_proceder = resultado.get("puede_editar", False)
            
            return puede_proceder, resultado
            
        except ImportError:
            # Si no está disponible el módulo de diagnóstico
            return True, {"nota": "Módulo de diagnóstico no disponible"}
    
    @classmethod
    def generar_reporte_validacion(cls, incidente: Dict) -> Dict:
        """
        Genera reporte detallado de validación
        
        Args:
            incidente: Datos del incidente
            
        Returns:
            Reporte con detalles por sección
        """
        reporte = {
            "timestamp": datetime.now().isoformat(),
            "secciones": {},
            "resumen": {
                "total_errores": 0,
                "secciones_invalidas": 0,
                "puede_continuar": True
            }
        }
        
        # Validar cada sección
        for seccion in ["1", "2", "3", "4", "5", "6", "7", "8"]:
            if seccion in incidente:
                metodo_validar = getattr(cls, f"validar_seccion_{seccion}", None)
                if metodo_validar:
                    es_valido, errores = metodo_validar(incidente[seccion])
                    reporte["secciones"][seccion] = {
                        "valido": es_valido,
                        "errores": errores,
                        "cantidad_errores": len(errores)
                    }
                    
                    if not es_valido:
                        reporte["resumen"]["secciones_invalidas"] += 1
                    reporte["resumen"]["total_errores"] += len(errores)
        
        # Determinar si puede continuar
        reporte["resumen"]["puede_continuar"] = (
            reporte["resumen"]["secciones_invalidas"] == 0
        )
        
        return reporte
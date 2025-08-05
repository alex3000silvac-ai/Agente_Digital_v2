# gestor_evidencias.py
"""
Gestor de Evidencias para Incidentes
Maneja archivos físicos, validaciones y sincronización con BD
Integrado con el sistema de diagnóstico para verificación de integridad
"""

import os
import shutil
import hashlib
import mimetypes
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from werkzeug.utils import secure_filename
from ...database import get_db_connection

class GestorEvidencias:
    """
    Gestiona todas las operaciones relacionadas con archivos de evidencia
    """
    
    # Configuración de rutas base
    RUTA_BASE_UPLOADS = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
        'uploads'
    )
    RUTA_EVIDENCIAS = os.path.join(RUTA_BASE_UPLOADS, 'evidencias')
    RUTA_TEMPORAL = os.path.join(RUTA_BASE_UPLOADS, 'temp')
    
    # Límites y restricciones
    TAMANO_MAXIMO_MB = 50
    EXTENSIONES_PERMITIDAS = {
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', 
        '.jpeg', '.txt', '.csv', '.zip', '.rar', '.msg', '.eml'
    }
    
    # Mapeo de secciones a carpetas
    SECCION_CARPETA = {
        "2": "2.5",
        "3": "3.4", 
        "4": "4.4",
        "5": "5.2",
        "6": "6.4"
    }
    
    def __init__(self):
        # Crear directorios si no existen
        os.makedirs(self.RUTA_EVIDENCIAS, exist_ok=True)
        os.makedirs(self.RUTA_TEMPORAL, exist_ok=True)
    
    def procesar_archivo(self, archivo, indice_unico: str, seccion: str,
                        usuario_id: int = None) -> Dict:
        """
        Procesa un archivo subido y lo guarda en la ubicación correcta
        
        Args:
            archivo: Objeto archivo de Flask/Werkzeug
            indice_unico: Índice único del incidente
            seccion: Número de sección (2, 3, 4, 5, 6)
            usuario_id: ID del usuario que sube
            
        Returns:
            Información del archivo procesado
        """
        try:
            # Validar archivo
            validacion = self._validar_archivo(archivo)
            if not validacion["valido"]:
                return {
                    "exito": False,
                    "error": validacion["error"]
                }
            
            # Generar nombre seguro
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_original = secure_filename(archivo.filename)
            nombre_base, extension = os.path.splitext(nombre_original)
            nombre_archivo = f"{nombre_base}_{timestamp}{extension}"
            
            # Crear estructura de carpetas
            carpeta_seccion = self.SECCION_CARPETA.get(seccion, seccion)
            ruta_incidente = os.path.join(self.RUTA_EVIDENCIAS, indice_unico, carpeta_seccion)
            os.makedirs(ruta_incidente, exist_ok=True)
            
            # Guardar archivo
            ruta_completa = os.path.join(ruta_incidente, nombre_archivo)
            archivo.save(ruta_completa)
            
            # Calcular hash MD5
            hash_md5 = self._calcular_hash_archivo(ruta_completa)
            
            # Obtener información adicional
            tamano_kb = os.path.getsize(ruta_completa) / 1024
            tipo_mime = mimetypes.guess_type(ruta_completa)[0] or 'application/octet-stream'
            
            return {
                "exito": True,
                "archivo_info": {
                    "nombre": nombre_archivo,
                    "nombre_original": nombre_original,
                    "ruta": ruta_completa,
                    "ruta_relativa": f"evidencias/{indice_unico}/{carpeta_seccion}/{nombre_archivo}",
                    "hash_md5": hash_md5,
                    "tamano_kb": round(tamano_kb, 2),
                    "tipo_mime": tipo_mime,
                    "extension": extension,
                    "seccion": carpeta_seccion,
                    "fecha_subida": datetime.now().isoformat(),
                    "subido_por": usuario_id
                }
            }
            
        except Exception as e:
            return {
                "exito": False,
                "error": f"Error procesando archivo: {str(e)}"
            }
    
    def guardar_evidencia_bd(self, incidente_id: int, archivo_info: Dict,
                            descripcion: str = "", version: int = 1) -> Dict:
        """
        Guarda información de evidencia en la base de datos
        
        Args:
            incidente_id: ID del incidente
            archivo_info: Información del archivo procesado
            descripcion: Descripción opcional
            version: Número de versión
            
        Returns:
            Resultado de la operación
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Insertar en EvidenciasIncidentes
            cursor.execute("""
                INSERT INTO EvidenciasIncidentes (
                    IncidenteID, NombreArchivo, RutaArchivo,
                    Descripcion, Seccion, FechaSubida,
                    SubidoPor, Version, HashMD5,
                    TamanoKB, TipoArchivo, Estado
                ) VALUES (?, ?, ?, ?, ?, GETDATE(), ?, ?, ?, ?, ?, ?)
            """, (
                incidente_id,
                archivo_info["nombre"],
                archivo_info["ruta"],
                descripcion,
                archivo_info["seccion"],
                archivo_info.get("subido_por"),
                version,
                archivo_info["hash_md5"],
                archivo_info["tamano_kb"],
                archivo_info["tipo_mime"],
                "activo"
            ))
            
            cursor.execute("SELECT SCOPE_IDENTITY()")
            evidencia_id = cursor.fetchone()[0]
            
            conn.commit()
            
            return {
                "exito": True,
                "evidencia_id": evidencia_id,
                "mensaje": "Evidencia guardada correctamente"
            }
            
        except Exception as e:
            if conn:
                conn.rollback()
            return {
                "exito": False,
                "error": f"Error guardando en BD: {str(e)}"
            }
        finally:
            if conn:
                conn.close()
    
    def obtener_evidencias_incidente(self, incidente_id: int, 
                                   seccion: Optional[str] = None) -> List[Dict]:
        """
        Obtiene todas las evidencias de un incidente
        
        Args:
            incidente_id: ID del incidente
            seccion: Filtrar por sección específica
            
        Returns:
            Lista de evidencias
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    EvidenciaID, NombreArchivo, RutaArchivo,
                    Descripcion, Seccion, FechaSubida,
                    SubidoPor, Version, HashMD5,
                    TamanoKB, TipoArchivo, Estado
                FROM EvidenciasIncidentes
                WHERE IncidenteID = ?
            """
            
            params = [incidente_id]
            
            if seccion:
                query += " AND Seccion = ?"
                params.append(self.SECCION_CARPETA.get(seccion, seccion))
            
            query += " ORDER BY Seccion, FechaSubida"
            
            cursor.execute(query, params)
            evidencias = []
            
            for row in cursor.fetchall():
                evidencia = {
                    "id": row[0],
                    "nombre": row[1],
                    "ruta": row[2],
                    "descripcion": row[3],
                    "seccion": row[4],
                    "fecha_subida": row[5].isoformat() if row[5] else None,
                    "subido_por": row[6],
                    "version": row[7],
                    "hash_md5": row[8],
                    "tamano_kb": row[9],
                    "tipo_mime": row[10],
                    "estado": row[11],
                    "existe_archivo": os.path.exists(row[2]) if row[2] else False
                }
                evidencias.append(evidencia)
            
            return evidencias
            
        except Exception as e:
            print(f"Error obteniendo evidencias: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def eliminar_evidencia(self, evidencia_id: int, eliminar_fisico: bool = True) -> Dict:
        """
        Elimina una evidencia (BD y opcionalmente archivo físico)
        
        Args:
            evidencia_id: ID de la evidencia
            eliminar_fisico: Si debe eliminar el archivo físico
            
        Returns:
            Resultado de la operación
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Obtener información antes de eliminar
            cursor.execute("""
                SELECT RutaArchivo, NombreArchivo 
                FROM EvidenciasIncidentes 
                WHERE EvidenciaID = ?
            """, (evidencia_id,))
            
            resultado = cursor.fetchone()
            if not resultado:
                return {
                    "exito": False,
                    "error": "Evidencia no encontrada"
                }
            
            ruta_archivo = resultado[0]
            
            # Eliminar de BD
            cursor.execute("""
                DELETE FROM EvidenciasIncidentes WHERE EvidenciaID = ?
            """, (evidencia_id,))
            
            conn.commit()
            
            # Eliminar archivo físico si se requiere
            if eliminar_fisico and ruta_archivo and os.path.exists(ruta_archivo):
                try:
                    os.remove(ruta_archivo)
                except Exception as e:
                    print(f"Error eliminando archivo físico: {e}")
            
            return {
                "exito": True,
                "mensaje": "Evidencia eliminada correctamente"
            }
            
        except Exception as e:
            if conn:
                conn.rollback()
            return {
                "exito": False,
                "error": f"Error eliminando evidencia: {str(e)}"
            }
        finally:
            if conn:
                conn.close()
    
    def copiar_evidencias_incidente(self, origen_id: int, destino_id: int,
                                  indice_destino: str) -> Dict:
        """
        Copia todas las evidencias de un incidente a otro
        
        Args:
            origen_id: ID del incidente origen
            destino_id: ID del incidente destino
            indice_destino: Índice único del incidente destino
            
        Returns:
            Resultado de la operación
        """
        resultado = {
            "copiadas": 0,
            "errores": [],
            "total": 0
        }
        
        try:
            # Obtener evidencias origen
            evidencias = self.obtener_evidencias_incidente(origen_id)
            resultado["total"] = len(evidencias)
            
            for evidencia in evidencias:
                try:
                    # Copiar archivo físico
                    if evidencia["existe_archivo"]:
                        # Crear nueva ruta
                        carpeta_destino = os.path.join(
                            self.RUTA_EVIDENCIAS, 
                            indice_destino, 
                            evidencia["seccion"]
                        )
                        os.makedirs(carpeta_destino, exist_ok=True)
                        
                        nueva_ruta = os.path.join(carpeta_destino, evidencia["nombre"])
                        shutil.copy2(evidencia["ruta"], nueva_ruta)
                        
                        # Copiar registro en BD
                        nuevo_info = evidencia.copy()
                        nuevo_info["ruta"] = nueva_ruta
                        
                        res = self.guardar_evidencia_bd(
                            destino_id,
                            nuevo_info,
                            evidencia.get("descripcion", ""),
                            evidencia.get("version", 1)
                        )
                        
                        if res["exito"]:
                            resultado["copiadas"] += 1
                        else:
                            resultado["errores"].append(res["error"])
                    else:
                        resultado["errores"].append(
                            f"Archivo no existe: {evidencia['nombre']}"
                        )
                        
                except Exception as e:
                    resultado["errores"].append(f"Error copiando {evidencia['nombre']}: {str(e)}")
            
        except Exception as e:
            resultado["errores"].append(f"Error general: {str(e)}")
        
        return resultado
    
    def sincronizar_evidencias(self, incidente_id: int, indice_unico: str) -> Dict:
        """
        Sincroniza evidencias entre BD y sistema de archivos
        
        Args:
            incidente_id: ID del incidente
            indice_unico: Índice único del incidente
            
        Returns:
            Reporte de sincronización
        """
        reporte = {
            "archivos_bd": 0,
            "archivos_disco": 0,
            "sincronizados": 0,
            "faltantes_disco": [],
            "huerfanos_disco": [],
            "reparados": 0
        }
        
        try:
            # Obtener evidencias de BD
            evidencias_bd = self.obtener_evidencias_incidente(incidente_id)
            reporte["archivos_bd"] = len(evidencias_bd)
            
            # Mapear rutas de BD
            rutas_bd = {ev["ruta"]: ev for ev in evidencias_bd if ev["ruta"]}
            
            # Escanear archivos en disco
            carpeta_incidente = os.path.join(self.RUTA_EVIDENCIAS, indice_unico)
            archivos_disco = []
            
            if os.path.exists(carpeta_incidente):
                for root, dirs, files in os.walk(carpeta_incidente):
                    for archivo in files:
                        ruta_completa = os.path.join(root, archivo)
                        archivos_disco.append(ruta_completa)
            
            reporte["archivos_disco"] = len(archivos_disco)
            
            # Verificar archivos faltantes en disco
            for ruta, evidencia in rutas_bd.items():
                if not os.path.exists(ruta):
                    reporte["faltantes_disco"].append({
                        "id": evidencia["id"],
                        "nombre": evidencia["nombre"],
                        "ruta": ruta
                    })
                else:
                    reporte["sincronizados"] += 1
            
            # Verificar archivos huérfanos en disco
            for archivo_disco in archivos_disco:
                if archivo_disco not in rutas_bd:
                    reporte["huerfanos_disco"].append(archivo_disco)
            
        except Exception as e:
            reporte["error"] = str(e)
        
        return reporte
    
    def verificar_integridad_archivo(self, ruta_archivo: str, hash_esperado: str) -> bool:
        """
        Verifica la integridad de un archivo comparando su hash
        
        Args:
            ruta_archivo: Ruta del archivo
            hash_esperado: Hash MD5 esperado
            
        Returns:
            True si el hash coincide
        """
        try:
            if not os.path.exists(ruta_archivo):
                return False
            
            hash_actual = self._calcular_hash_archivo(ruta_archivo)
            return hash_actual == hash_esperado
            
        except Exception:
            return False
    
    def limpiar_archivos_temporales(self, dias_antiguedad: int = 7) -> Dict:
        """
        Limpia archivos temporales antiguos
        
        Args:
            dias_antiguedad: Días de antigüedad para considerar obsoleto
            
        Returns:
            Resultado de limpieza
        """
        resultado = {
            "archivos_eliminados": 0,
            "espacio_liberado_mb": 0,
            "errores": []
        }
        
        try:
            limite = datetime.now().timestamp() - (dias_antiguedad * 24 * 60 * 60)
            
            for archivo in os.listdir(self.RUTA_TEMPORAL):
                ruta_completa = os.path.join(self.RUTA_TEMPORAL, archivo)
                
                try:
                    if os.path.isfile(ruta_completa):
                        tiempo_modificacion = os.path.getmtime(ruta_completa)
                        
                        if tiempo_modificacion < limite:
                            tamano = os.path.getsize(ruta_completa)
                            os.remove(ruta_completa)
                            resultado["archivos_eliminados"] += 1
                            resultado["espacio_liberado_mb"] += tamano / (1024 * 1024)
                            
                except Exception as e:
                    resultado["errores"].append(f"Error con {archivo}: {str(e)}")
            
        except Exception as e:
            resultado["errores"].append(f"Error general: {str(e)}")
        
        return resultado
    
    def _validar_archivo(self, archivo) -> Dict:
        """Valida un archivo antes de procesarlo"""
        if not archivo or archivo.filename == '':
            return {"valido": False, "error": "No se seleccionó archivo"}
        
        # Validar extensión
        extension = os.path.splitext(archivo.filename)[1].lower()
        if extension not in self.EXTENSIONES_PERMITIDAS:
            return {
                "valido": False, 
                "error": f"Extensión {extension} no permitida"
            }
        
        # Validar tamaño (requiere seek para obtener tamaño)
        archivo.seek(0, os.SEEK_END)
        tamano_mb = archivo.tell() / (1024 * 1024)
        archivo.seek(0)  # Volver al inicio
        
        if tamano_mb > self.TAMANO_MAXIMO_MB:
            return {
                "valido": False,
                "error": f"Archivo excede el tamaño máximo de {self.TAMANO_MAXIMO_MB}MB"
            }
        
        return {"valido": True}
    
    def _calcular_hash_archivo(self, ruta_archivo: str) -> str:
        """Calcula el hash MD5 de un archivo"""
        hash_md5 = hashlib.md5()
        with open(ruta_archivo, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def exportar_lista_evidencias(self, incidente_id: int) -> Dict:
        """
        Exporta lista de evidencias para reporte
        
        Args:
            incidente_id: ID del incidente
            
        Returns:
            Datos formateados para exportación
        """
        evidencias = self.obtener_evidencias_incidente(incidente_id)
        
        export_data = {
            "total_evidencias": len(evidencias),
            "tamano_total_mb": sum(ev["tamano_kb"] for ev in evidencias) / 1024,
            "por_seccion": {},
            "detalle": []
        }
        
        # Agrupar por sección
        for evidencia in evidencias:
            seccion = evidencia["seccion"]
            if seccion not in export_data["por_seccion"]:
                export_data["por_seccion"][seccion] = {
                    "cantidad": 0,
                    "tamano_mb": 0
                }
            
            export_data["por_seccion"][seccion]["cantidad"] += 1
            export_data["por_seccion"][seccion]["tamano_mb"] += evidencia["tamano_kb"] / 1024
            
            # Agregar al detalle
            export_data["detalle"].append({
                "seccion": seccion,
                "nombre": evidencia["nombre"],
                "tamano": f"{evidencia['tamano_kb']:.2f}KB",
                "fecha": evidencia["fecha_subida"],
                "tipo": evidencia["tipo_mime"],
                "estado": "OK" if evidencia["existe_archivo"] else "FALTANTE"
            })
        
        return export_data
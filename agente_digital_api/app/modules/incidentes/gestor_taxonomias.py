# gestor_taxonomias.py
"""
Gestor Especializado para Taxonomías (Sección 4)
Maneja la complejidad de múltiples selecciones y evidencias jerárquicas
Compatible con el flujo ANCI y especificaciones del sistema
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from ...database import get_db_connection

class GestorTaxonomias:
    """
    Gestiona todas las operaciones relacionadas con taxonomías
    Mantiene la integridad referencial y numeración jerárquica
    """
    
    def __init__(self):
        self.cache_taxonomias = {}  # Cache temporal para optimización
    
    def obtener_taxonomias_disponibles(self, empresa_id: int = None) -> List[Dict]:
        """
        Obtiene lista de taxonomías disponibles desde la BD
        
        Args:
            empresa_id: ID de empresa para filtrado opcional
            
        Returns:
            Lista de taxonomías disponibles
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Query según tablas_bd.txt
            query = """
                SELECT 
                    Id_Incidente,
                    Categoria_del_Incidente,
                    Subcategoria_del_Incidente,
                    Descripcion,
                    Activo
                FROM Taxonomia_incidentes
                WHERE Activo = 1
                ORDER BY Categoria_del_Incidente, Subcategoria_del_Incidente
            """
            
            cursor.execute(query)
            taxonomias = []
            
            for row in cursor.fetchall():
                taxonomias.append({
                    "id": row[0],
                    "categoria": row[1] or "",
                    "subcategoria": row[2] or "",
                    "descripcion": row[3] or "",
                    "activo": row[4],
                    "texto_completo": f"{row[1]} - {row[2]}" if row[2] else row[1]
                })
            
            return taxonomias
            
        except Exception as e:
            print(f"Error obteniendo taxonomías: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def asignar_taxonomia_incidente(self, incidente_id: int, taxonomia_id: int,
                                   comentarios: str = "", usuario_id: int = None) -> Dict:
        """
        Asigna una taxonomía a un incidente en la BD
        
        Args:
            incidente_id: ID del incidente
            taxonomia_id: ID de la taxonomía
            comentarios: Comentarios opcionales
            usuario_id: ID del usuario que asigna
            
        Returns:
            Resultado de la operación
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verificar si ya existe
            cursor.execute("""
                SELECT ID FROM INCIDENTE_TAXONOMIA 
                WHERE IncidenteID = ? AND Id_Taxonomia = ?
            """, (incidente_id, taxonomia_id))
            
            if cursor.fetchone():
                return {
                    "exito": False,
                    "mensaje": "Taxonomía ya asignada a este incidente"
                }
            
            # Insertar nueva asignación
            cursor.execute("""
                INSERT INTO INCIDENTE_TAXONOMIA (
                    IncidenteID, Id_Taxonomia, Comentarios, 
                    FechaAsignacion, AsignadoPor
                ) VALUES (?, ?, ?, GETDATE(), ?)
            """, (incidente_id, taxonomia_id, comentarios, usuario_id))
            
            # Obtener ID insertado
            cursor.execute("SELECT SCOPE_IDENTITY()")
            nuevo_id = cursor.fetchone()[0]
            
            conn.commit()
            
            return {
                "exito": True,
                "id": nuevo_id,
                "mensaje": "Taxonomía asignada correctamente"
            }
            
        except Exception as e:
            if conn:
                conn.rollback()
            return {
                "exito": False,
                "mensaje": f"Error asignando taxonomía: {str(e)}"
            }
        finally:
            if conn:
                conn.close()
    
    def gestionar_evidencias_taxonomia(self, incidente_id: int, taxonomia_uuid: str,
                                     archivos: List[Dict]) -> Dict:
        """
        Gestiona evidencias específicas de una taxonomía
        
        Args:
            incidente_id: ID del incidente
            taxonomia_uuid: UUID único de la taxonomía en el JSON
            archivos: Lista de archivos a procesar
            
        Returns:
            Resultado con archivos procesados
        """
        resultados = {
            "procesados": [],
            "errores": [],
            "total": len(archivos)
        }
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            for archivo in archivos:
                try:
                    # Insertar en EvidenciasIncidentes
                    cursor.execute("""
                        INSERT INTO EvidenciasIncidentes (
                            IncidenteID, NombreArchivo, RutaArchivo,
                            Descripcion, Seccion, FechaSubida,
                            SubidoPor, TamanoKB, TipoArchivo,
                            TaxonomiaUUID
                        ) VALUES (?, ?, ?, ?, ?, GETDATE(), ?, ?, ?, ?)
                    """, (
                        incidente_id,
                        archivo.get("nombre"),
                        archivo.get("ruta"),
                        archivo.get("descripcion", ""),
                        "4.4",  # Sección para taxonomías
                        archivo.get("subido_por"),
                        archivo.get("tamano_kb", 0),
                        archivo.get("tipo_mime", ""),
                        taxonomia_uuid
                    ))
                    
                    cursor.execute("SELECT SCOPE_IDENTITY()")
                    evidencia_id = cursor.fetchone()[0]
                    
                    resultados["procesados"].append({
                        "evidencia_id": evidencia_id,
                        "archivo": archivo["nombre"],
                        "uuid": taxonomia_uuid
                    })
                    
                except Exception as e:
                    resultados["errores"].append({
                        "archivo": archivo.get("nombre", "desconocido"),
                        "error": str(e)
                    })
            
            conn.commit()
            
        except Exception as e:
            if conn:
                conn.rollback()
            resultados["error_general"] = str(e)
        finally:
            if conn:
                conn.close()
        
        return resultados
    
    def obtener_taxonomias_incidente(self, incidente_id: int) -> List[Dict]:
        """
        Obtiene todas las taxonomías asignadas a un incidente
        
        Args:
            incidente_id: ID del incidente
            
        Returns:
            Lista de taxonomías con sus evidencias
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Obtener taxonomías asignadas
            cursor.execute("""
                SELECT 
                    it.ID,
                    it.Id_Taxonomia,
                    it.Comentarios,
                    it.FechaAsignacion,
                    t.Categoria_del_Incidente,
                    t.Subcategoria_del_Incidente,
                    t.Descripcion
                FROM INCIDENTE_TAXONOMIA it
                INNER JOIN Taxonomia_incidentes t ON it.Id_Taxonomia = t.Id_Incidente
                WHERE it.IncidenteID = ?
                ORDER BY it.FechaAsignacion
            """, (incidente_id,))
            
            taxonomias = []
            for row in cursor.fetchall():
                taxonomia = {
                    "id": row[0],
                    "taxonomia_id": row[1],
                    "comentarios": row[2],
                    "fecha_asignacion": row[3].isoformat() if row[3] else None,
                    "categoria": row[4],
                    "subcategoria": row[5],
                    "descripcion": row[6],
                    "evidencias": []
                }
                
                # Obtener evidencias asociadas
                cursor.execute("""
                    SELECT 
                        EvidenciaID,
                        NombreArchivo,
                        RutaArchivo,
                        FechaSubida,
                        TamanoKB
                    FROM EvidenciasIncidentes
                    WHERE IncidenteID = ? AND Seccion = '4.4'
                    AND TaxonomiaUUID IN (
                        SELECT TaxonomiaUUID FROM TaxonomiaUUIDs
                        WHERE IncidenteTaxonomiaID = ?
                    )
                """, (incidente_id, row[0]))
                
                for ev_row in cursor.fetchall():
                    taxonomia["evidencias"].append({
                        "id": ev_row[0],
                        "nombre": ev_row[1],
                        "ruta": ev_row[2],
                        "fecha": ev_row[3].isoformat() if ev_row[3] else None,
                        "tamano_kb": ev_row[4]
                    })
                
                taxonomias.append(taxonomia)
            
            return taxonomias
            
        except Exception as e:
            print(f"Error obteniendo taxonomías del incidente: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def sincronizar_con_json(self, incidente_id: int, estructura_json: Dict) -> Dict:
        """
        Sincroniza taxonomías entre BD y estructura JSON
        
        Args:
            incidente_id: ID del incidente
            estructura_json: Estructura JSON del incidente
            
        Returns:
            Resultado de sincronización
        """
        resultado = {
            "sincronizadas": 0,
            "agregadas": 0,
            "eliminadas": 0,
            "errores": []
        }
        
        try:
            # Obtener taxonomías de BD
            taxonomias_bd = self.obtener_taxonomias_incidente(incidente_id)
            taxonomias_bd_ids = {t["taxonomia_id"] for t in taxonomias_bd}
            
            # Obtener taxonomías de JSON
            taxonomias_json = estructura_json.get("4", {}).get("taxonomias", {}).get("seleccionadas", [])
            taxonomias_json_activas = [
                t for t in taxonomias_json if t.get("estado") == "activo"
            ]
            taxonomias_json_ids = {t["taxonomia_id"] for t in taxonomias_json_activas}
            
            # Identificar diferencias
            a_agregar = taxonomias_json_ids - taxonomias_bd_ids
            a_eliminar = taxonomias_bd_ids - taxonomias_json_ids
            
            # Agregar nuevas
            for tax_json in taxonomias_json_activas:
                if tax_json["taxonomia_id"] in a_agregar:
                    res = self.asignar_taxonomia_incidente(
                        incidente_id,
                        tax_json["taxonomia_id"],
                        tax_json.get("datos", {}).get("comentarios", "")
                    )
                    if res["exito"]:
                        resultado["agregadas"] += 1
                    else:
                        resultado["errores"].append(res["mensaje"])
            
            # Eliminar obsoletas
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                for tax_id in a_eliminar:
                    cursor.execute("""
                        DELETE FROM INCIDENTE_TAXONOMIA 
                        WHERE IncidenteID = ? AND Id_Taxonomia = ?
                    """, (incidente_id, tax_id))
                    resultado["eliminadas"] += 1
                
                conn.commit()
                
            except Exception as e:
                if conn:
                    conn.rollback()
                resultado["errores"].append(f"Error eliminando: {str(e)}")
            finally:
                if conn:
                    conn.close()
            
            resultado["sincronizadas"] = len(taxonomias_json_ids & taxonomias_bd_ids)
            
        except Exception as e:
            resultado["errores"].append(f"Error general: {str(e)}")
        
        return resultado
    
    def generar_numeracion_jerarquica(self, incidente_json: Dict) -> Dict:
        """
        Genera o regenera numeración jerárquica para evidencias
        
        Args:
            incidente_json: Estructura JSON del incidente
            
        Returns:
            Incidente con numeración actualizada
        """
        taxonomias = incidente_json.get("4", {}).get("taxonomias", {}).get("seleccionadas", [])
        
        for tax in taxonomias:
            if tax.get("estado") != "activo":
                continue
            
            numero_orden = tax.get("numero_orden", 0)
            evidencias = tax.get("evidencias", {}).get("items", [])
            
            # Renumerar evidencias
            for idx, evidencia in enumerate(evidencias):
                evidencia["numero"] = f"4.4.{numero_orden}.{idx + 1}"
        
        return incidente_json
    
    def validar_integridad_taxonomias(self, incidente_json: Dict) -> Tuple[bool, List[str]]:
        """
        Valida integridad de la estructura de taxonomías
        
        Args:
            incidente_json: Estructura JSON del incidente
            
        Returns:
            Tupla (es_valido, lista_errores)
        """
        errores = []
        
        try:
            taxonomias_data = incidente_json.get("4", {}).get("taxonomias", {})
            
            if not isinstance(taxonomias_data.get("seleccionadas"), list):
                errores.append("Estructura de taxonomías inválida")
                return False, errores
            
            taxonomias = taxonomias_data["seleccionadas"]
            numeros_orden_usados = set()
            uuids_usados = set()
            
            for idx, tax in enumerate(taxonomias):
                if tax.get("estado") != "activo":
                    continue
                
                # Validar UUID único
                uuid_tax = tax.get("id_unico")
                if not uuid_tax:
                    errores.append(f"Taxonomía {idx+1}: falta UUID")
                elif uuid_tax in uuids_usados:
                    errores.append(f"UUID duplicado: {uuid_tax}")
                uuids_usados.add(uuid_tax)
                
                # Validar número de orden único
                numero_orden = tax.get("numero_orden")
                if not numero_orden:
                    errores.append(f"Taxonomía {idx+1}: falta número de orden")
                elif numero_orden in numeros_orden_usados:
                    errores.append(f"Número de orden duplicado: {numero_orden}")
                numeros_orden_usados.add(numero_orden)
                
                # Validar evidencias
                evidencias = tax.get("evidencias", {}).get("items", [])
                for ev_idx, evidencia in enumerate(evidencias):
                    numero_esperado = f"4.4.{numero_orden}.{ev_idx+1}"
                    if evidencia.get("numero") != numero_esperado:
                        errores.append(
                            f"Numeración incorrecta: esperado {numero_esperado}, "
                            f"encontrado {evidencia.get('numero')}"
                        )
            
        except Exception as e:
            errores.append(f"Error validando estructura: {str(e)}")
        
        return len(errores) == 0, errores
    
    def exportar_para_anci(self, incidente_id: int) -> Dict:
        """
        Exporta taxonomías en formato requerido para informe ANCI
        
        Args:
            incidente_id: ID del incidente
            
        Returns:
            Datos formateados para ANCI
        """
        taxonomias = self.obtener_taxonomias_incidente(incidente_id)
        
        export_data = {
            "seccion_4": {
                "titulo": "Clasificación del Incidente",
                "taxonomias_aplicadas": len(taxonomias),
                "detalle": []
            }
        }
        
        for idx, tax in enumerate(taxonomias):
            detalle = {
                "numero": f"4.4.{idx+1}",
                "categoria": tax["categoria"],
                "subcategoria": tax["subcategoria"],
                "descripcion": tax["descripcion"],
                "comentarios": tax["comentarios"],
                "evidencias": len(tax["evidencias"]),
                "fecha_asignacion": tax["fecha_asignacion"]
            }
            
            # Agregar resumen de evidencias
            if tax["evidencias"]:
                detalle["evidencias_detalle"] = [
                    {
                        "numero": f"4.4.{idx+1}.{ev_idx+1}",
                        "archivo": ev["nombre"],
                        "tamano": f"{ev['tamano_kb']/1024:.2f}MB" if ev['tamano_kb'] > 1024 else f"{ev['tamano_kb']}KB"
                    }
                    for ev_idx, ev in enumerate(tax["evidencias"])
                ]
            
            export_data["seccion_4"]["detalle"].append(detalle)
        
        return export_data
    
    def limpiar_taxonomias_huerfanas(self) -> Dict:
        """
        Limpia registros de taxonomías sin incidente asociado
        
        Returns:
            Resultado de limpieza
        """
        conn = None
        resultado = {
            "registros_eliminados": 0,
            "errores": []
        }
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Buscar huérfanas
            cursor.execute("""
                SELECT COUNT(*) FROM INCIDENTE_TAXONOMIA it
                WHERE NOT EXISTS (
                    SELECT 1 FROM Incidentes i 
                    WHERE i.IncidenteID = it.IncidenteID
                )
            """)
            
            huerfanas = cursor.fetchone()[0]
            
            if huerfanas > 0:
                # Eliminar huérfanas
                cursor.execute("""
                    DELETE FROM INCIDENTE_TAXONOMIA
                    WHERE IncidenteID NOT IN (
                        SELECT IncidenteID FROM Incidentes
                    )
                """)
                
                resultado["registros_eliminados"] = huerfanas
                conn.commit()
            
        except Exception as e:
            if conn:
                conn.rollback()
            resultado["errores"].append(str(e))
        finally:
            if conn:
                conn.close()
        
        return resultado
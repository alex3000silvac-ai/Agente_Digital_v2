#!/usr/bin/env python3
"""
Módulo para eliminar archivos huérfanos cuando se eliminan evidencias
Asegura que no queden archivos sin referencia en el sistema
"""

import os
import logging
from datetime import datetime
from ...database import get_db_connection

logger = logging.getLogger(__name__)

class LimpiadorArchivosHuerfanos:
    """
    Gestiona la eliminación de archivos físicos cuando se eliminan evidencias
    """
    
    @staticmethod
    def eliminar_archivo_evidencia(evidencia_id: int, incidente_id: int, tipo: str = 'general') -> dict:
        """
        Elimina un archivo de evidencia y su registro en BD
        
        Args:
            evidencia_id: ID de la evidencia
            incidente_id: ID del incidente
            tipo: 'general' o 'taxonomia'
            
        Returns:
            dict con resultado de la operación
        """
        conn = None
        resultado = {
            'success': False,
            'archivo_eliminado': False,
            'registro_eliminado': False,
            'mensaje': '',
            'ruta_archivo': None
        }
        
        try:
            conn = get_db_connection()
            if not conn:
                resultado['mensaje'] = "Error de conexión a BD"
                return resultado
                
            cursor = conn.cursor()
            
            # 1. Obtener información del archivo antes de eliminar
            if tipo == 'general':
                query_info = """
                    SELECT RutaArchivo, NombreArchivo 
                    FROM EvidenciasIncidentes 
                    WHERE EvidenciaID = ? AND IncidenteID = ?
                """
            else:  # taxonomia
                query_info = """
                    SELECT RutaArchivo, NombreArchivo 
                    FROM EVIDENCIAS_TAXONOMIA 
                    WHERE EvidenciaID = ? AND IncidenteID = ?
                """
            
            cursor.execute(query_info, evidencia_id, incidente_id)
            archivo_info = cursor.fetchone()
            
            if not archivo_info:
                resultado['mensaje'] = f"Evidencia {evidencia_id} no encontrada"
                return resultado
            
            ruta_archivo = archivo_info[0]
            nombre_archivo = archivo_info[1]
            resultado['ruta_archivo'] = ruta_archivo
            
            print(f"🗑️ Eliminando archivo: {nombre_archivo}")
            
            # 2. Eliminar archivo físico si existe
            if ruta_archivo and os.path.exists(ruta_archivo):
                try:
                    os.remove(ruta_archivo)
                    resultado['archivo_eliminado'] = True
                    print(f"✅ Archivo físico eliminado: {ruta_archivo}")
                    
                    # Intentar eliminar directorio si está vacío
                    directorio = os.path.dirname(ruta_archivo)
                    try:
                        os.rmdir(directorio)
                        print(f"📁 Directorio vacío eliminado: {directorio}")
                    except:
                        pass  # No está vacío o no se puede eliminar
                        
                except Exception as e:
                    print(f"⚠️ Error eliminando archivo físico: {e}")
                    resultado['mensaje'] = f"Error eliminando archivo: {str(e)}"
            else:
                print(f"⚠️ Archivo no encontrado en disco: {ruta_archivo}")
                resultado['archivo_eliminado'] = True  # Marcar como ok si no existe
            
            # 3. Eliminar registro de BD
            if tipo == 'general':
                query_delete = """
                    DELETE FROM EvidenciasIncidentes 
                    WHERE EvidenciaID = ? AND IncidenteID = ?
                """
            else:  # taxonomia
                # Primero eliminar comentarios asociados
                query_delete_comments = """
                    DELETE FROM COMENTARIOS_TAXONOMIA 
                    WHERE IncidenteID = ? 
                    AND Id_Taxonomia IN (
                        SELECT Id_Taxonomia FROM EVIDENCIAS_TAXONOMIA 
                        WHERE EvidenciaID = ? AND IncidenteID = ?
                    )
                    AND NumeroEvidencia IN (
                        SELECT NumeroEvidencia FROM EVIDENCIAS_TAXONOMIA 
                        WHERE EvidenciaID = ? AND IncidenteID = ?
                    )
                """
                cursor.execute(query_delete_comments, incidente_id, evidencia_id, 
                             incidente_id, evidencia_id, incidente_id)
                
                query_delete = """
                    DELETE FROM EVIDENCIAS_TAXONOMIA 
                    WHERE EvidenciaID = ? AND IncidenteID = ?
                """
            
            cursor.execute(query_delete, evidencia_id, incidente_id)
            registros_eliminados = cursor.rowcount
            
            if registros_eliminados > 0:
                conn.commit()
                resultado['registro_eliminado'] = True
                print(f"✅ Registro eliminado de BD")
            else:
                print(f"⚠️ No se encontró registro para eliminar")
            
            # 4. Registrar en log de auditoría
            try:
                query_audit = """
                    INSERT INTO AuditoriaAdminPlataforma 
                    (UsuarioID, Accion, RecursoAfectado, RecursoID, FechaHora, Detalles)
                    VALUES (?, ?, ?, ?, GETDATE(), ?)
                """
                detalles = f"Eliminada evidencia {nombre_archivo} del incidente {incidente_id}"
                cursor.execute(query_audit, 1, 'ELIMINAR_EVIDENCIA', 
                             'Evidencia', evidencia_id, detalles)
                conn.commit()
            except:
                pass  # No crítico si falla auditoría
            
            resultado['success'] = True
            resultado['mensaje'] = f"Evidencia {nombre_archivo} eliminada correctamente"
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error eliminando evidencia: {e}")
            resultado['mensaje'] = f"Error: {str(e)}"
            
        finally:
            if conn:
                conn.close()
                
        return resultado
    
    @staticmethod
    def limpiar_archivos_huerfanos_masivo(incidente_id: int) -> dict:
        """
        Busca y elimina todos los archivos huérfanos de un incidente
        (archivos en disco sin registro en BD)
        """
        resultado = {
            'archivos_verificados': 0,
            'archivos_huerfanos': 0,
            'archivos_eliminados': 0,
            'errores': []
        }
        
        # Directorio de uploads
        upload_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
            'uploads'
        )
        
        if not os.path.exists(upload_dir):
            return resultado
        
        conn = None
        try:
            conn = get_db_connection()
            if not conn:
                resultado['errores'].append("Error de conexión a BD")
                return resultado
                
            cursor = conn.cursor()
            
            # Obtener todas las rutas de archivos registradas para el incidente
            query_rutas = """
                SELECT RutaArchivo FROM EvidenciasIncidentes WHERE IncidenteID = ?
                UNION
                SELECT RutaArchivo FROM EVIDENCIAS_TAXONOMIA WHERE IncidenteID = ?
            """
            cursor.execute(query_rutas, incidente_id, incidente_id)
            
            rutas_registradas = set()
            for row in cursor.fetchall():
                if row[0]:
                    rutas_registradas.add(row[0])
            
            # Buscar archivos en disco relacionados con el incidente
            patron_incidente = f"incidente_{incidente_id}_"
            
            for root, dirs, files in os.walk(upload_dir):
                for archivo in files:
                    if patron_incidente in archivo:
                        ruta_completa = os.path.join(root, archivo)
                        resultado['archivos_verificados'] += 1
                        
                        # Si no está registrado, es huérfano
                        if ruta_completa not in rutas_registradas:
                            resultado['archivos_huerfanos'] += 1
                            try:
                                os.remove(ruta_completa)
                                resultado['archivos_eliminados'] += 1
                                print(f"🗑️ Archivo huérfano eliminado: {archivo}")
                            except Exception as e:
                                resultado['errores'].append(f"Error eliminando {archivo}: {str(e)}")
            
        except Exception as e:
            resultado['errores'].append(f"Error general: {str(e)}")
            
        finally:
            if conn:
                conn.close()
                
        return resultado
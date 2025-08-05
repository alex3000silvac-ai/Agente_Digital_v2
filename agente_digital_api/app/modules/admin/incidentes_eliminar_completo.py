# incidentes_eliminar_completo.py
# Módulo de eliminación completa de incidentes - No deja rastro

from flask import Blueprint, jsonify
from ...database import get_db_connection
import os
import shutil

incidentes_eliminar_completo_bp = Blueprint('incidentes_eliminar_completo', __name__, url_prefix='/api/admin')

def verificar_tabla_existe(cursor, nombre_tabla):
    """Verifica si una tabla existe en la base de datos"""
    try:
        cursor.execute("""
            SELECT 1 FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'
        """, (nombre_tabla,))
        return cursor.fetchone() is not None
    except:
        return False

def obtener_archivos_incidente(cursor, incidente_id):
    """Obtiene todas las rutas de archivos asociados al incidente"""
    archivos = []
    
    # Archivos de evidencias de incidentes
    if verificar_tabla_existe(cursor, 'EvidenciasIncidentes'):
        cursor.execute("SELECT RutaArchivo FROM EvidenciasIncidentes WHERE IncidenteID = ?", (incidente_id,))
        archivos.extend([row[0] for row in cursor.fetchall() if row[0]])
    
    # Archivos de evidencias de categorías
    if verificar_tabla_existe(cursor, 'EvidenciasIncidenteCategoria'):
        cursor.execute("""
            SELECT eic.RutaArchivo 
            FROM EvidenciasIncidenteCategoria eic
            INNER JOIN IncidentesCategorias ic ON eic.IncidenteCategoriaID = ic.IncidenteCategoriaID
            WHERE ic.IncidenteID = ?
        """, (incidente_id,))
        archivos.extend([row[0] for row in cursor.fetchall() if row[0]])
    
    # Archivos de evidencias de taxonomías
    if verificar_tabla_existe(cursor, 'EVIDENCIAS_TAXONOMIA'):
        cursor.execute("SELECT RutaArchivo FROM EVIDENCIAS_TAXONOMIA WHERE IncidenteID = ?", (incidente_id,))
        archivos.extend([row[0] for row in cursor.fetchall() if row[0]])
    
    return archivos

def eliminar_archivos_fisicos(archivos):
    """Elimina archivos físicos del sistema de archivos"""
    archivos_eliminados = []
    archivos_no_encontrados = []
    
    for archivo in archivos:
        if archivo and os.path.exists(archivo):
            try:
                os.remove(archivo)
                archivos_eliminados.append(archivo)
                
                # También intentar eliminar el directorio si está vacío
                directorio = os.path.dirname(archivo)
                try:
                    os.rmdir(directorio)
                except:
                    pass  # El directorio no está vacío o no se puede eliminar
                    
            except Exception as e:
                print(f"Error eliminando archivo {archivo}: {e}")
        else:
            archivos_no_encontrados.append(archivo)
    
    return archivos_eliminados, archivos_no_encontrados

@incidentes_eliminar_completo_bp.route('/incidentes/<int:incidente_id>/eliminar-completo', methods=['DELETE'])
def eliminar_incidente_completo(incidente_id):
    """Elimina completamente un incidente sin dejar rastro en ninguna tabla"""
    print(f"🔥 INICIANDO ELIMINACIÓN COMPLETA DEL INCIDENTE {incidente_id}")
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            print(f"❌ Error de conexión a la base de datos")
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
            
        cursor = conn.cursor()
        print(f"✅ Conexión a BD establecida correctamente")
        
        # Verificar que el incidente existe
        print(f"🔍 Verificando que el incidente {incidente_id} existe...")
        cursor.execute("SELECT IncidenteID, EmpresaID FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        incidente_data = cursor.fetchone()
        if not incidente_data:
            print(f"❌ Incidente {incidente_id} no encontrado en la BD")
            return jsonify({"error": "Incidente no encontrado"}), 404
        
        empresa_id = incidente_data[1]
        print(f"✅ Incidente {incidente_id} encontrado (EmpresaID: {empresa_id})")
        
        # Obtener información de archivos antes de eliminar
        print(f"📁 Obteniendo archivos asociados al incidente...")
        archivos_a_eliminar = obtener_archivos_incidente(cursor, incidente_id)
        print(f"📁 Archivos encontrados: {len(archivos_a_eliminar)}")
        
        # Configurar autocommit para control manual de transacciones
        print(f"🔄 Iniciando transacción de eliminación...")
        conn.autocommit = False  # Deshabilitar autocommit para control manual
        
        # ORDEN DE ELIMINACIÓN CRÍTICO - De más específico a más general
        tablas_eliminacion = [
            # 1. Primero eliminar comentarios y evidencias de categorías
            ("ComentariosIncidenteCategoria", """
                DELETE FROM ComentariosIncidenteCategoria 
                WHERE IncidenteCategoriaID IN (
                    SELECT IncidenteCategoriaID FROM IncidentesCategorias 
                    WHERE IncidenteID = ?
                )
            """),
            
            ("EvidenciasIncidenteCategoria", """
                DELETE FROM EvidenciasIncidenteCategoria 
                WHERE IncidenteCategoriaID IN (
                    SELECT IncidenteCategoriaID FROM IncidentesCategorias 
                    WHERE IncidenteID = ?
                )
            """),
            
            # 2. Eliminar categorías
            ("IncidentesCategorias", "DELETE FROM IncidentesCategorias WHERE IncidenteID = ?"),
            
            # 3. Eliminar evidencias y comentarios de taxonomías
            ("EVIDENCIAS_TAXONOMIA", "DELETE FROM EVIDENCIAS_TAXONOMIA WHERE IncidenteID = ?"),
            ("COMENTARIOS_TAXONOMIA", "DELETE FROM COMENTARIOS_TAXONOMIA WHERE IncidenteID = ?"),
            
            # 4. Eliminar relaciones incidente-taxonomía
            ("INCIDENTE_TAXONOMIA", "DELETE FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?"),
            
            # 5. Eliminar evidencias del incidente
            ("EvidenciasIncidentes", "DELETE FROM EvidenciasIncidentes WHERE IncidenteID = ?"),
            
            # 6. Eliminar historial
            ("HistorialIncidentes", "DELETE FROM HistorialIncidentes WHERE IncidenteID = ?"),
            
            # 7. Eliminar notificaciones y plazos ANCI
            ("AnciNotificaciones", "DELETE FROM AnciNotificaciones WHERE IncidenteID = ?"),
            ("AnciAutorizaciones", "DELETE FROM AnciAutorizaciones WHERE IncidenteID = ?"),
            ("AnciPlazos", "DELETE FROM AnciPlazos WHERE IncidenteID = ?"),
            
            # 8. Eliminar envíos ANCI relacionados
            ("AnciEnvios", """
                DELETE FROM AnciEnvios 
                WHERE ReporteAnciID IN (
                    SELECT ReporteAnciID FROM ReportesANCI 
                    WHERE IncidenteID = ?
                )
            """),
            
            # 9. Eliminar reportes ANCI
            ("ReportesANCI", "DELETE FROM ReportesANCI WHERE IncidenteID = ?"),
            
            # 10. Buscar y eliminar referencias en auditoría
            ("AuditoriaAccesos", """
                DELETE FROM AuditoriaAccesos 
                WHERE DatosAdicionales LIKE '%IncidenteID":"' + CAST(? AS VARCHAR) + '"%'
                   OR DatosAdicionales LIKE '%incidente_id":' + CAST(? AS VARCHAR) + '%'
            """, True),  # True indica que necesita dos parámetros
            
            ("AuditoriaAdminPlataforma", """
                DELETE FROM AuditoriaAdminPlataforma 
                WHERE RecursoAfectado = 'Incidente' AND RecursoID = ?
            """),
            
            # 11. Limpiar archivos temporales
            ("ArchivosTemporales", """
                DELETE FROM ArchivosTemporales 
                WHERE EntidadTipo = 'Incidente' AND EntidadID = ?
            """),
        ]
        
        eliminaciones_exitosas = []
        
        # Ejecutar eliminaciones
        print(f"🗑️ Iniciando eliminación de {len(tablas_eliminacion)} tipos de tabla...")
        for i, tabla_info in enumerate(tablas_eliminacion, 1):
            if len(tabla_info) == 2:
                tabla, query = tabla_info
                necesita_doble_param = False
            else:
                tabla, query, necesita_doble_param = tabla_info
                
            print(f"🗑️ {i}/{len(tablas_eliminacion)}: Procesando tabla {tabla}...")
            if verificar_tabla_existe(cursor, tabla):
                try:
                    if necesita_doble_param:
                        cursor.execute(query, (incidente_id, incidente_id))
                    else:
                        cursor.execute(query, (incidente_id,))
                    
                    rows_affected = cursor.rowcount
                    if rows_affected > 0:
                        print(f"   ✅ {tabla}: {rows_affected} registros eliminados")
                        eliminaciones_exitosas.append(f"{tabla}: {rows_affected} registros")
                    else:
                        print(f"   ⚪ {tabla}: 0 registros (tabla vacía)")
                except Exception as e:
                    print(f"   ❌ Error al eliminar de {tabla}: {str(e)}")
            else:
                print(f"   ⚠️ {tabla}: Tabla no existe")
        
        # 12. FINALMENTE, eliminar el incidente principal
        print(f"🎯 ELIMINANDO INCIDENTE PRINCIPAL...")
        cursor.execute("DELETE FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        rows_deleted = cursor.rowcount
        print(f"🎯 Incidentes eliminados: {rows_deleted}")
        eliminaciones_exitosas.append(f"Incidentes: {rows_deleted} registro principal")
        
        # Confirmar transacción
        print(f"💾 Confirmando transacción...")
        conn.commit()
        print(f"✅ Transacción confirmada exitosamente")
        
        # Eliminar archivos físicos después de confirmar la transacción
        print(f"📁 Eliminando {len(archivos_a_eliminar)} archivos físicos...")
        archivos_eliminados, archivos_no_encontrados = eliminar_archivos_fisicos(archivos_a_eliminar)
        print(f"📁 Archivos eliminados: {len(archivos_eliminados)}, No encontrados: {len(archivos_no_encontrados)}")
        
        # Limpiar caché si existe
        print(f"🧹 Limpiando archivos temporales...")
        try:
            # Buscar y eliminar archivos temporales relacionados
            temp_folder = os.path.join(os.path.dirname(__file__), '..', '..', 'temp_incidentes')
            if os.path.exists(temp_folder):
                for archivo in os.listdir(temp_folder):
                    if str(incidente_id) in archivo:
                        os.remove(os.path.join(temp_folder, archivo))
                        print(f"🧹 Archivo temporal eliminado: {archivo}")
        except Exception as e:
            print(f"⚠️ Error limpiando archivos temporales: {e}")
        
        print(f"🎉 ELIMINACIÓN COMPLETA EXITOSA DEL INCIDENTE {incidente_id}")
        
        # Retornar respuesta exitosa sin usar jsonify para evitar problemas de contexto
        response_data = {
            "success": True,
            "message": "Incidente eliminado completamente sin dejar rastro",
            "incidente_id": incidente_id,
            "empresa_id": empresa_id,
            "detalles": {
                "tablas_afectadas": eliminaciones_exitosas,
                "archivos_eliminados": len(archivos_eliminados),
                "archivos_no_encontrados": len(archivos_no_encontrados)
            }
        }
        
        # Intentar usar jsonify si estamos en contexto Flask, sino devolver dict
        try:
            return jsonify(response_data), 200
        except RuntimeError:
            # Si no hay contexto Flask, devolver directamente el dict
            print(f"⚠️ Contexto Flask no disponible, devolviendo dict")
            return response_data, 200
        
    except Exception as e:
        if conn:
            try:
                print(f"❌ Error detectado, haciendo ROLLBACK...")
                conn.rollback()
                print(f"💾 ROLLBACK completado")
            except:
                pass
        
        import traceback
        print(f"❌ Error al eliminar incidente completamente: {e}")
        print(traceback.format_exc())
        
        # Manejar error sin jsonify para evitar problemas de contexto
        error_data = {
            "error": "Error al eliminar incidente",
            "detalle": str(e)
        }
        
        try:
            return jsonify(error_data), 500
        except RuntimeError:
            print(f"⚠️ Contexto Flask no disponible para error, devolviendo dict")
            return error_data, 500
        
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

# Endpoint alternativo para compatibilidad
@incidentes_eliminar_completo_bp.route('/incidentes/<int:incidente_id>', methods=['DELETE'])
def eliminar_incidente_redirect(incidente_id):
    """Redirecciona al endpoint de eliminación completa"""
    return eliminar_incidente_completo(incidente_id)
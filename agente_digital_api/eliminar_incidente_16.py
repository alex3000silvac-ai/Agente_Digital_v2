#!/usr/bin/env python3
"""
Script para eliminar manualmente el incidente 16 que está "pegado"
"""

import sys
import os

# Agregar el path del proyecto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db_connection

def eliminar_incidente_manual(incidente_id):
    """Elimina manualmente un incidente específico"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ Error: No se pudo conectar a la base de datos")
            return False
            
        cursor = conn.cursor()
        
        # Verificar que el incidente existe
        cursor.execute("SELECT IncidenteID, Titulo FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        incidente = cursor.fetchone()
        if not incidente:
            print(f"❌ Incidente {incidente_id} no encontrado")
            return False
        
        print(f"🔍 Encontrado incidente {incidente_id}: '{incidente[1]}'")
        
        # Iniciar transacción
        cursor.execute("BEGIN TRANSACTION")
        
        # Lista de tablas a limpiar (en orden específico)
        tablas_limpieza = [
            # Evidencias y comentarios de categorías
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
            
            # Categorías
            ("IncidentesCategorias", "DELETE FROM IncidentesCategorias WHERE IncidenteID = ?"),
            
            # Taxonomías
            ("EVIDENCIAS_TAXONOMIA", "DELETE FROM EVIDENCIAS_TAXONOMIA WHERE IncidenteID = ?"),
            ("COMENTARIOS_TAXONOMIA", "DELETE FROM COMENTARIOS_TAXONOMIA WHERE IncidenteID = ?"),
            ("INCIDENTE_TAXONOMIA", "DELETE FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?"),
            
            # Evidencias del incidente
            ("EvidenciasIncidentes", "DELETE FROM EvidenciasIncidentes WHERE IncidenteID = ?"),
            
            # Historial
            ("HistorialIncidentes", "DELETE FROM HistorialIncidentes WHERE IncidenteID = ?"),
            
            # ANCI relacionados
            ("AnciNotificaciones", "DELETE FROM AnciNotificaciones WHERE IncidenteID = ?"),
            ("AnciAutorizaciones", "DELETE FROM AnciAutorizaciones WHERE IncidenteID = ?"),
            ("AnciPlazos", "DELETE FROM AnciPlazos WHERE IncidenteID = ?"),
            ("AnciEnvios", """
                DELETE FROM AnciEnvios 
                WHERE ReporteAnciID IN (
                    SELECT ReporteAnciID FROM ReportesANCI 
                    WHERE IncidenteID = ?
                )
            """),
            ("ReportesANCI", "DELETE FROM ReportesANCI WHERE IncidenteID = ?"),
            
            # Archivos temporales
            ("ArchivosTemporales", """
                DELETE FROM ArchivosTemporales 
                WHERE EntidadTipo = 'Incidente' AND EntidadID = ?
            """),
        ]
        
        eliminados = []
        
        # Ejecutar eliminaciones
        for tabla, query in tablas_limpieza:
            try:
                # Verificar si la tabla existe
                cursor.execute("""
                    SELECT 1 FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'
                """, (tabla,))
                
                if cursor.fetchone():
                    cursor.execute(query, (incidente_id,))
                    rows_affected = cursor.rowcount
                    if rows_affected > 0:
                        eliminados.append(f"{tabla}: {rows_affected} registros")
                        print(f"  ✅ {tabla}: {rows_affected} registros eliminados")
                else:
                    print(f"  ⚠️ Tabla {tabla} no existe")
                    
            except Exception as e:
                print(f"  ⚠️ Error en {tabla}: {str(e)}")
        
        # Finalmente, eliminar el incidente principal
        cursor.execute("DELETE FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
        eliminados.append(f"Incidentes: 1 registro principal")
        print(f"  ✅ Incidentes: 1 registro principal eliminado")
        
        # Confirmar transacción
        cursor.execute("COMMIT")
        
        print(f"\n🎉 Incidente {incidente_id} eliminado completamente")
        print(f"📊 Resumen de eliminaciones:")
        for eliminacion in eliminados:
            print(f"   - {eliminacion}")
        
        return True
        
    except Exception as e:
        if conn:
            try:
                cursor.execute("ROLLBACK")
                print("🔄 Transacción revertida debido a error")
            except:
                pass
        
        print(f"❌ Error eliminando incidente: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if conn:
            conn.close()

def main():
    """Función principal"""
    incidente_id = 16
    
    print(f"🗑️ ELIMINACIÓN MANUAL DEL INCIDENTE {incidente_id}")
    print("=" * 50)
    
    confirmacion = input(f"¿Está seguro de eliminar el incidente {incidente_id}? (si/no): ")
    if confirmacion.lower() not in ['si', 's', 'yes', 'y']:
        print("❌ Operación cancelada")
        return
    
    if eliminar_incidente_manual(incidente_id):
        print("\n✅ Operación completada exitosamente")
    else:
        print("\n❌ La operación falló")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script de migración para reorganizar archivos existentes en estructura multicliente segura.
Este script debe ejecutarse DESPUÉS de aplicar los cambios en la base de datos.
"""

import os
import shutil
import pyodbc
from pathlib import Path
import logging
from datetime import datetime

# Configuración
BASE_UPLOAD_FOLDER = 'uploads'
LOG_FILE = f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def get_db_connection():
    """Obtiene conexión a la base de datos usando la misma configuración de la app"""
    import sys
    sys.path.append('.')
    
    try:
        # Intentar usar la configuración existente de la aplicación
        from app.database import get_db_connection as app_get_db
        return app_get_db()
    except ImportError:
        # Fallback: usar parámetros manuales
        logging.warning("No se pudo importar configuración de BD de la app, usando configuración manual")
        connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost;"
            "DATABASE=agente_digital_db;"
            "Trusted_Connection=yes;"
        )
        return pyodbc.connect(connection_string)

def create_directory_structure(inquilino_id, empresa_id):
    """Crea la estructura de directorios para una organización"""
    path = os.path.join(BASE_UPLOAD_FOLDER, f"inquilino_{inquilino_id}", f"empresa_{empresa_id}")
    os.makedirs(path, exist_ok=True)
    return path

def migrate_evidencias_cumplimiento(conn, dry_run=False):
    """Migra archivos de evidencias de cumplimiento"""
    logging.info("Iniciando migración de evidencias de cumplimiento...")
    cursor = conn.cursor()
    
    # Obtener todas las evidencias con información de organización
    cursor.execute("""
        SELECT ec.EvidenciaID, ec.RutaArchivo, ec.NombreArchivoAlmacenado,
               ec.InquilinoID, ec.EmpresaID
        FROM dbo.EvidenciasCumplimiento ec
        WHERE ec.InquilinoID IS NOT NULL AND ec.EmpresaID IS NOT NULL
    """)
    
    evidencias = cursor.fetchall()
    migrated = 0
    errors = 0
    
    for evidencia in evidencias:
        evidencia_id, ruta_actual, nombre_archivo, inquilino_id, empresa_id = evidencia
        
        try:
            # Determinar ruta origen
            if os.path.isabs(ruta_actual):
                origen = ruta_actual
            else:
                origen = os.path.join(BASE_UPLOAD_FOLDER, nombre_archivo)
            
            if not os.path.exists(origen):
                logging.warning(f"Archivo no encontrado: {origen} (ID: {evidencia_id})")
                errors += 1
                continue
            
            # Crear nueva estructura
            nueva_carpeta = create_directory_structure(inquilino_id, empresa_id)
            destino = os.path.join(nueva_carpeta, nombre_archivo)
            nueva_ruta_relativa = os.path.join(f"inquilino_{inquilino_id}", f"empresa_{empresa_id}", nombre_archivo)
            
            if not dry_run:
                # Mover archivo
                shutil.move(origen, destino)
                
                # Actualizar BD con nueva ruta
                cursor.execute("""
                    UPDATE dbo.EvidenciasCumplimiento 
                    SET RutaArchivo = ? 
                    WHERE EvidenciaID = ?
                """, (nueva_ruta_relativa, evidencia_id))
                conn.commit()
            
            logging.info(f"Migrado: {nombre_archivo} -> {nueva_ruta_relativa}")
            migrated += 1
            
        except Exception as e:
            logging.error(f"Error migrando evidencia {evidencia_id}: {str(e)}")
            errors += 1
            if not dry_run:
                conn.rollback()
    
    logging.info(f"Evidencias de cumplimiento - Migradas: {migrated}, Errores: {errors}")
    return migrated, errors

def migrate_evidencias_incidentes(conn, dry_run=False):
    """Migra archivos de evidencias de incidentes"""
    logging.info("Iniciando migración de evidencias de incidentes...")
    cursor = conn.cursor()
    
    # Obtener todas las evidencias con información de organización
    cursor.execute("""
        SELECT ei.EvidenciaIncidenteID, ei.RutaArchivo, ei.NombreArchivoAlmacenado,
               ei.InquilinoID, ei.EmpresaID
        FROM dbo.EvidenciasIncidentes ei
        WHERE ei.InquilinoID IS NOT NULL AND ei.EmpresaID IS NOT NULL
    """)
    
    evidencias = cursor.fetchall()
    migrated = 0
    errors = 0
    
    for evidencia in evidencias:
        evidencia_id, ruta_actual, nombre_archivo, inquilino_id, empresa_id = evidencia
        
        try:
            # Determinar ruta origen
            if os.path.isabs(ruta_actual):
                origen = ruta_actual
            else:
                origen = os.path.join(BASE_UPLOAD_FOLDER, nombre_archivo)
            
            if not os.path.exists(origen):
                logging.warning(f"Archivo no encontrado: {origen} (ID: {evidencia_id})")
                errors += 1
                continue
            
            # Crear nueva estructura
            nueva_carpeta = create_directory_structure(inquilino_id, empresa_id)
            destino = os.path.join(nueva_carpeta, nombre_archivo)
            nueva_ruta_relativa = os.path.join(f"inquilino_{inquilino_id}", f"empresa_{empresa_id}", nombre_archivo)
            
            if not dry_run:
                # Mover archivo
                shutil.move(origen, destino)
                
                # Actualizar BD con nueva ruta
                cursor.execute("""
                    UPDATE dbo.EvidenciasIncidentes 
                    SET RutaArchivo = ? 
                    WHERE EvidenciaIncidenteID = ?
                """, (nueva_ruta_relativa, evidencia_id))
                conn.commit()
            
            logging.info(f"Migrado: {nombre_archivo} -> {nueva_ruta_relativa}")
            migrated += 1
            
        except Exception as e:
            logging.error(f"Error migrando evidencia incidente {evidencia_id}: {str(e)}")
            errors += 1
            if not dry_run:
                conn.rollback()
    
    logging.info(f"Evidencias de incidentes - Migradas: {migrated}, Errores: {errors}")
    return migrated, errors

def migrate_evidencias_taxonomia(conn, dry_run=False):
    """Migra archivos de evidencias de taxonomía"""
    logging.info("Iniciando migración de evidencias de taxonomía...")
    cursor = conn.cursor()
    
    # Obtener todas las evidencias con información de organización
    cursor.execute("""
        SELECT ite.ID, ite.RutaArchivo, ite.NombreArchivo,
               ite.InquilinoID, ite.EmpresaID
        FROM dbo.INCIDENTE_TAXONOMIA_EVIDENCIAS ite
        WHERE ite.InquilinoID IS NOT NULL AND ite.EmpresaID IS NOT NULL
    """)
    
    evidencias = cursor.fetchall()
    migrated = 0
    errors = 0
    
    for evidencia in evidencias:
        evidencia_id, ruta_actual, nombre_archivo_original, inquilino_id, empresa_id = evidencia
        
        try:
            # Extraer nombre de archivo almacenado de la ruta actual
            nombre_archivo = os.path.basename(ruta_actual)
            
            # Determinar ruta origen
            if os.path.isabs(ruta_actual):
                origen = ruta_actual
            else:
                origen = os.path.join(BASE_UPLOAD_FOLDER, nombre_archivo)
            
            if not os.path.exists(origen):
                logging.warning(f"Archivo no encontrado: {origen} (ID: {evidencia_id})")
                errors += 1
                continue
            
            # Crear nueva estructura
            nueva_carpeta = create_directory_structure(inquilino_id, empresa_id)
            destino = os.path.join(nueva_carpeta, nombre_archivo)
            nueva_ruta_relativa = os.path.join(f"inquilino_{inquilino_id}", f"empresa_{empresa_id}", nombre_archivo)
            
            if not dry_run:
                # Mover archivo
                shutil.move(origen, destino)
                
                # Actualizar BD con nueva ruta
                cursor.execute("""
                    UPDATE dbo.INCIDENTE_TAXONOMIA_EVIDENCIAS 
                    SET RutaArchivo = ? 
                    WHERE ID = ?
                """, (nueva_ruta_relativa, evidencia_id))
                conn.commit()
            
            logging.info(f"Migrado: {nombre_archivo} -> {nueva_ruta_relativa}")
            migrated += 1
            
        except Exception as e:
            logging.error(f"Error migrando evidencia taxonomía {evidencia_id}: {str(e)}")
            errors += 1
            if not dry_run:
                conn.rollback()
    
    logging.info(f"Evidencias de taxonomía - Migradas: {migrated}, Errores: {errors}")
    return migrated, errors

def cleanup_old_files():
    """Limpia archivos huérfanos en la carpeta raíz de uploads"""
    logging.info("Buscando archivos huérfanos en carpeta raíz...")
    orphaned = 0
    
    for file in os.listdir(BASE_UPLOAD_FOLDER):
        file_path = os.path.join(BASE_UPLOAD_FOLDER, file)
        if os.path.isfile(file_path):
            # Los archivos en la raíz son huérfanos después de la migración
            logging.warning(f"Archivo huérfano encontrado: {file}")
            orphaned += 1
    
    if orphaned > 0:
        logging.warning(f"Se encontraron {orphaned} archivos huérfanos. Revise manualmente antes de eliminar.")
    
    return orphaned

def main():
    """Función principal del script de migración"""
    logging.info("=== INICIANDO MIGRACIÓN DE ARCHIVOS ===")
    
    # Verificar que existe la carpeta base
    if not os.path.exists(BASE_UPLOAD_FOLDER):
        logging.error(f"La carpeta {BASE_UPLOAD_FOLDER} no existe!")
        return
    
    # Preguntar si es una ejecución de prueba
    dry_run = input("¿Ejecutar en modo de prueba (sin mover archivos)? (s/n): ").lower() == 's'
    
    if dry_run:
        logging.info("MODO DE PRUEBA - No se realizarán cambios")
    else:
        confirm = input("ADVERTENCIA: Se moverán archivos y actualizará la BD. ¿Continuar? (si/no): ")
        if confirm.lower() != 'si':
            logging.info("Migración cancelada por el usuario")
            return
    
    try:
        # Conectar a BD
        conn = get_db_connection()
        logging.info("Conexión a base de datos establecida")
        
        # Migrar cada tipo de evidencia
        total_migrated = 0
        total_errors = 0
        
        # Evidencias de cumplimiento
        migrated, errors = migrate_evidencias_cumplimiento(conn, dry_run)
        total_migrated += migrated
        total_errors += errors
        
        # Evidencias de incidentes
        migrated, errors = migrate_evidencias_incidentes(conn, dry_run)
        total_migrated += migrated
        total_errors += errors
        
        # Evidencias de taxonomía
        migrated, errors = migrate_evidencias_taxonomia(conn, dry_run)
        total_migrated += migrated
        total_errors += errors
        
        # Buscar archivos huérfanos
        orphaned = cleanup_old_files()
        
        # Resumen
        logging.info("=== RESUMEN DE MIGRACIÓN ===")
        logging.info(f"Total archivos migrados: {total_migrated}")
        logging.info(f"Total errores: {total_errors}")
        logging.info(f"Archivos huérfanos: {orphaned}")
        logging.info(f"Log guardado en: {LOG_FILE}")
        
        if not dry_run and total_migrated > 0:
            logging.info("Migración completada exitosamente!")
        
    except Exception as e:
        logging.error(f"Error crítico durante la migración: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
"""
Script para insertar archivos de prueba en un incidente
"""

from app.database import get_db_connection
from datetime import datetime
import os

# Configuración
INCIDENTE_ID = 5
UPLOAD_FOLDER = "C:/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api/uploads"

def insertar_archivos_prueba():
    """Inserta archivos de prueba en diferentes secciones"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Primero, verificar que el incidente existe
        cursor.execute("SELECT IncidenteID FROM Incidentes WHERE IncidenteID = ?", (INCIDENTE_ID,))
        if not cursor.fetchone():
            print(f"❌ Incidente {INCIDENTE_ID} no encontrado")
            return
        
        # Crear directorio si no existe
        incidente_dir = os.path.join(UPLOAD_FOLDER, 'incidentes', str(INCIDENTE_ID))
        os.makedirs(incidente_dir, exist_ok=True)
        
        # Archivos de prueba para insertar
        archivos_prueba = [
            {
                'seccion': 2,
                'nombre': 'descripcion_detallada.pdf',
                'tipo': 'application/pdf',
                'tamaño': 245.5,
                'descripcion': 'Descripción detallada del incidente',
                'comentario': 'Documento con el análisis inicial del incidente'
            },
            {
                'seccion': 2,
                'nombre': 'captura_pantalla_error.png',
                'tipo': 'image/png',
                'tamaño': 156.3,
                'descripcion': 'Captura del error',
                'comentario': 'Screenshot tomado al momento del incidente'
            },
            {
                'seccion': 3,
                'nombre': 'analisis_preliminar.docx',
                'tipo': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'tamaño': 89.7,
                'descripcion': 'Análisis preliminar del origen',
                'comentario': 'Primer análisis realizado por el equipo'
            },
            {
                'seccion': 5,
                'nombre': 'plan_accion_inmediata.xlsx',
                'tipo': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'tamaño': 45.2,
                'descripcion': 'Plan de acción detallado',
                'comentario': 'Acciones a tomar en las primeras 24 horas'
            },
            {
                'seccion': 6,
                'nombre': 'lecciones_aprendidas.txt',
                'tipo': 'text/plain',
                'tamaño': 12.8,
                'descripcion': 'Documento de lecciones aprendidas',
                'comentario': 'Resumen de mejoras identificadas'
            }
        ]
        
        print(f"\n🔧 Insertando archivos de prueba para incidente {INCIDENTE_ID}...")
        print("-" * 60)
        
        archivos_insertados = 0
        
        for archivo in archivos_prueba:
            # Crear archivo físico de prueba
            archivo_path = os.path.join(incidente_dir, archivo['nombre'])
            with open(archivo_path, 'w') as f:
                f.write(f"Archivo de prueba: {archivo['nombre']}\n")
                f.write(f"Sección: {archivo['seccion']}\n")
                f.write(f"Fecha: {datetime.now()}\n")
                f.write(f"Descripción: {archivo['descripcion']}\n")
            
            # Insertar en BD
            cursor.execute("""
                INSERT INTO INCIDENTES_ARCHIVOS 
                (IncidenteID, NombreArchivo, TipoArchivo, TamanoKB, RutaArchivo, 
                 SeccionID, Descripcion, Comentario, FechaCarga, SubidoPor, Activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, 1)
            """, (
                INCIDENTE_ID,
                archivo['nombre'],
                archivo['tipo'],
                archivo['tamaño'],
                archivo_path,
                archivo['seccion'],
                archivo['descripcion'],
                archivo['comentario'],
                'sistema_prueba'
            ))
            
            archivos_insertados += 1
            print(f"✅ Archivo insertado: {archivo['nombre']} (Sección {archivo['seccion']})")
        
        # Confirmar cambios
        conn.commit()
        
        print(f"\n✅ Total archivos insertados: {archivos_insertados}")
        
        # Verificar que se insertaron correctamente
        cursor.execute("""
            SELECT COUNT(*) as total, SeccionID 
            FROM INCIDENTES_ARCHIVOS 
            WHERE IncidenteID = ? AND Activo = 1
            GROUP BY SeccionID
            ORDER BY SeccionID
        """, (INCIDENTE_ID,))
        
        print("\n📊 Resumen de archivos por sección:")
        for row in cursor.fetchall():
            print(f"   - Sección {row.SeccionID}: {row.total} archivos")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    insertar_archivos_prueba()
    print("\n🎯 Script completado. Ahora puedes probar la carga del incidente en el frontend.")
"""
Script para insertar archivos con estructura correcta de BD
"""

from app.database import get_db_connection
from datetime import datetime
import os

INCIDENTE_ID = 5
UPLOAD_FOLDER = "C:/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api/uploads"

def insertar_archivos_prueba():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("=" * 70)
        print("INSERTANDO ARCHIVOS CON ESTRUCTURA CORRECTA")
        print("=" * 70)
        
        # 1. Verificar incidente
        cursor.execute("SELECT IncidenteID FROM Incidentes WHERE IncidenteID = ?", (INCIDENTE_ID,))
        if not cursor.fetchone():
            print(f"❌ Incidente {INCIDENTE_ID} no encontrado")
            return
        print(f"✅ Incidente {INCIDENTE_ID} encontrado")
        
        # 2. Limpiar archivos anteriores
        print("\n🧹 Limpiando archivos anteriores...")
        cursor.execute("DELETE FROM INCIDENTES_ARCHIVOS WHERE IncidenteID = ?", (INCIDENTE_ID,))
        print("   ✅ Archivos eliminados")
        
        # 3. Crear directorio
        incidente_dir = os.path.join(UPLOAD_FOLDER, 'incidentes', str(INCIDENTE_ID))
        os.makedirs(incidente_dir, exist_ok=True)
        print(f"\n📁 Directorio creado: {incidente_dir}")
        
        # 4. Archivos de prueba
        archivos_data = [
            # Sección 2 - Descripción del incidente
            {
                'seccion': 2,
                'numero': 1,
                'nombre': 'analisis_inicial.pdf',
                'tipo': 'application/pdf',
                'tamaño': 256,
                'descripcion': 'Análisis inicial del incidente con detalles técnicos'
            },
            {
                'seccion': 2,
                'numero': 2,
                'nombre': 'logs_sistema.txt',
                'tipo': 'text/plain',
                'tamaño': 45,
                'descripcion': 'Logs del sistema durante el incidente'
            },
            
            # Sección 3 - Análisis
            {
                'seccion': 3,
                'numero': 1,
                'nombre': 'diagrama_red_afectada.png',
                'tipo': 'image/png',
                'tamaño': 189,
                'descripcion': 'Diagrama de la red comprometida'
            },
            {
                'seccion': 3,
                'numero': 2,
                'nombre': 'analisis_vulnerabilidad.docx',
                'tipo': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'tamaño': 78,
                'descripcion': 'Análisis detallado de la vulnerabilidad explotada'
            },
            
            # Sección 5 - Acciones inmediatas
            {
                'seccion': 5,
                'numero': 1,
                'nombre': 'plan_contencion.xlsx',
                'tipo': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'tamaño': 34,
                'descripcion': 'Plan de contención y acciones inmediatas'
            },
            {
                'seccion': 5,
                'numero': 2,
                'nombre': 'checklist_respuesta.pdf',
                'tipo': 'application/pdf',
                'tamaño': 23,
                'descripcion': 'Checklist de respuesta ante incidentes'
            },
            
            # Sección 6 - Lecciones aprendidas
            {
                'seccion': 6,
                'numero': 1,
                'nombre': 'informe_lecciones.pdf',
                'tipo': 'application/pdf',
                'tamaño': 156,
                'descripcion': 'Informe completo de lecciones aprendidas'
            },
            {
                'seccion': 6,
                'numero': 2,
                'nombre': 'mejoras_propuestas.docx',
                'tipo': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'tamaño': 89,
                'descripcion': 'Propuestas de mejora para evitar recurrencia'
            }
        ]
        
        print("\n📎 Insertando archivos de prueba...")
        archivos_insertados = 0
        
        for archivo in archivos_data:
            try:
                # Generar nombres
                nombre_servidor = f"INC{INCIDENTE_ID}_S{archivo['seccion']}_N{archivo['numero']}_{archivo['nombre']}"
                archivo_path = os.path.join(incidente_dir, nombre_servidor)
                
                # Crear archivo físico
                with open(archivo_path, 'w', encoding='utf-8') as f:
                    f.write(f"ARCHIVO DE PRUEBA\n")
                    f.write(f"{'=' * 50}\n")
                    f.write(f"Incidente: {INCIDENTE_ID}\n")
                    f.write(f"Sección: {archivo['seccion']}\n")
                    f.write(f"Archivo: {archivo['nombre']}\n")
                    f.write(f"Descripción: {archivo['descripcion']}\n")
                    f.write(f"Fecha: {datetime.now()}\n")
                    f.write(f"{'=' * 50}\n")
                    f.write(f"\nContenido de prueba para simular el archivo real.\n")
                
                # Calcular hash simple
                hash_archivo = f"HASH_{nombre_servidor[:20]}"
                
                # Insertar en BD
                cursor.execute("""
                    INSERT INTO INCIDENTES_ARCHIVOS 
                    (IncidenteID, SeccionID, NumeroArchivo, NombreOriginal, NombreServidor,
                     RutaArchivo, TipoArchivo, TamanoKB, HashArchivo, Descripcion, 
                     FechaSubida, SubidoPor, Activo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, 1)
                """, (
                    INCIDENTE_ID, 
                    archivo['seccion'], 
                    archivo['numero'], 
                    archivo['nombre'], 
                    nombre_servidor,
                    archivo_path, 
                    archivo['tipo'], 
                    archivo['tamaño'], 
                    hash_archivo,
                    archivo['descripcion'],
                    'sistema_prueba'
                ))
                
                archivos_insertados += 1
                print(f"   ✅ {archivo['nombre']} (Sección {archivo['seccion']})")
                
            except Exception as e:
                print(f"   ❌ Error con {archivo['nombre']}: {e}")
        
        # 5. Confirmar cambios
        conn.commit()
        
        # 6. Verificar inserción
        print(f"\n✅ Archivos insertados: {archivos_insertados}")
        
        cursor.execute("""
            SELECT SeccionID, COUNT(*) as total 
            FROM INCIDENTES_ARCHIVOS 
            WHERE IncidenteID = ? AND Activo = 1
            GROUP BY SeccionID
            ORDER BY SeccionID
        """, (INCIDENTE_ID,))
        
        print("\n📊 Resumen por sección:")
        total_archivos = 0
        for row in cursor.fetchall():
            print(f"   - Sección {row[0]}: {row[1]} archivos")
            total_archivos += row[1]
        
        print(f"\n   Total general: {total_archivos} archivos")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error general: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    insertar_archivos_prueba()
    print("\n🎯 Archivos de prueba insertados. Ahora puedes probar en el frontend.")
"""
Script corregido para insertar datos de prueba con estructura correcta
"""

from app.database import get_db_connection
from datetime import datetime
import os

INCIDENTE_ID = 5
UPLOAD_FOLDER = "C:/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api/uploads"

def insertar_datos_prueba():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("=" * 70)
        print("INSERTANDO DATOS DE PRUEBA - ESTRUCTURA CORREGIDA")
        print("=" * 70)
        
        # 1. Verificar que el incidente existe
        cursor.execute("SELECT IncidenteID, EmpresaID FROM Incidentes WHERE IncidenteID = ?", (INCIDENTE_ID,))
        result = cursor.fetchone()
        if not result:
            print(f"❌ Incidente {INCIDENTE_ID} no encontrado")
            return
        
        empresa_id = result[1]
        print(f"✅ Incidente {INCIDENTE_ID} encontrado (Empresa ID: {empresa_id})")
        
        # 2. Limpiar datos anteriores
        print("\n🧹 Limpiando datos anteriores...")
        
        # Limpiar archivos
        cursor.execute("DELETE FROM INCIDENTES_ARCHIVOS WHERE IncidenteID = ?", (INCIDENTE_ID,))
        print("   - Archivos eliminados")
        
        # Limpiar taxonomías
        cursor.execute("DELETE FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?", (INCIDENTE_ID,))
        print("   - Taxonomías eliminadas")
        
        # 3. Insertar archivos de prueba con estructura correcta
        print("\n📎 Insertando archivos de prueba...")
        
        incidente_dir = os.path.join(UPLOAD_FOLDER, 'incidentes', str(INCIDENTE_ID))
        os.makedirs(incidente_dir, exist_ok=True)
        
        archivos_data = [
            # Sección 2
            (2, 1, 'analisis_inicial.pdf', 'application/pdf', 256.8, 'Análisis inicial del incidente'),
            (2, 2, 'evidencia_logs.txt', 'text/plain', 45.2, 'Logs del sistema capturados'),
            
            # Sección 3
            (3, 1, 'diagrama_red.png', 'image/png', 189.5, 'Diagrama de red afectada'),
            (3, 2, 'reporte_vulnerabilidad.docx', 'application/msword', 78.3, 'Reporte de vulnerabilidad'),
            
            # Sección 5
            (5, 1, 'plan_accion.xlsx', 'application/vnd.ms-excel', 34.7, 'Plan de acción inmediata'),
            
            # Sección 6
            (6, 1, 'lecciones_aprendidas.pdf', 'application/pdf', 156.2, 'Documento de lecciones'),
            (6, 2, 'mejoras_propuestas.docx', 'application/msword', 89.4, 'Propuestas de mejora')
        ]
        
        for seccion, numero, nombre, tipo, tamaño, desc in archivos_data:
            archivo_path = os.path.join(incidente_dir, nombre)
            nombre_servidor = f"{INCIDENTE_ID}_{seccion}_{numero}_{nombre}"
            
            # Crear archivo físico
            with open(archivo_path, 'w') as f:
                f.write(f"Archivo de prueba: {nombre}\n")
                f.write(f"Sección: {seccion}\n")
                f.write(f"Descripción: {desc}\n")
                f.write(f"Fecha: {datetime.now()}\n")
            
            # Insertar en BD con estructura correcta
            cursor.execute("""
                INSERT INTO INCIDENTES_ARCHIVOS 
                (IncidenteID, SeccionID, NumeroArchivo, NombreOriginal, NombreServidor,
                 RutaArchivo, TipoArchivo, TamanoKB, Descripcion, FechaSubida, SubidoPor, Activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), 'sistema_prueba', 1)
            """, (INCIDENTE_ID, seccion, numero, nombre, nombre_servidor, 
                  archivo_path, tipo, tamaño, desc))
            
            print(f"   ✅ {nombre} (Sección {seccion}, Archivo #{numero})")
        
        # 4. Insertar taxonomías seleccionadas con justificaciones
        print("\n🏷️ Insertando taxonomías seleccionadas...")
        
        # Primero obtener IDs válidos de taxonomías
        cursor.execute("""
            SELECT TOP 3 TaxonomiaID, Nombre 
            FROM TAXONOMIAS 
            WHERE Activo = 1
        """)
        
        taxonomias_disponibles = cursor.fetchall()
        
        if taxonomias_disponibles:
            for i, (tax_id, tax_nombre) in enumerate(taxonomias_disponibles):
                justificacion = f"Justificación para {tax_nombre}: Esta taxonomía aplica porque se identificó {tax_nombre.lower()} en el incidente."
                descripcion = f"El problema se manifestó como {tax_nombre.lower()} afectando los sistemas críticos de la organización."
                
                cursor.execute("""
                    INSERT INTO INCIDENTE_TAXONOMIA
                    (IncidenteID, TaxonomiaID, Justificacion, DescripcionProblema,
                     FechaAsignacion, AsignadoPor)
                    VALUES (?, ?, ?, ?, GETDATE(), 'sistema_prueba')
                """, (INCIDENTE_ID, tax_id, justificacion, descripcion))
                
                print(f"   ✅ {tax_id} - {tax_nombre}")
                print(f"      - Justificación: {justificacion[:60]}...")
        else:
            print("   ⚠️ No se encontraron taxonomías disponibles")
        
        # 5. Actualizar algunos campos del incidente para completitud
        print("\n📝 Actualizando campos del incidente...")
        
        cursor.execute("""
            UPDATE Incidentes
            SET AccionesInmediatas = 'Se aplicaron medidas de contención inmediatas: 
1. Aislamiento de sistemas comprometidos
2. Cambio de credenciales afectadas
3. Aplicación de parches de seguridad
4. Monitoreo intensivo de logs',
                MedidasContencion = 'Bloqueo de IPs maliciosas, actualización de reglas de firewall',
                CausaRaiz = 'Configuración inadecuada de permisos y falta de segmentación de red',
                LeccionesAprendidas = 'Necesidad de implementar: 1) Revisión periódica de permisos, 2) MFA obligatorio',
                ServiciosInterrumpidos = 'Portal web principal, Sistema de facturación, API de integraciones',
                PlanMejora = 'Implementar nueva arquitectura de seguridad con segmentación mejorada'
            WHERE IncidenteID = ?
        """, (INCIDENTE_ID,))
        
        # Confirmar cambios
        conn.commit()
        
        # 6. Verificar inserción
        print("\n📊 Verificación de datos insertados:")
        
        # Contar archivos
        cursor.execute("""
            SELECT COUNT(*) as total, SeccionID 
            FROM INCIDENTES_ARCHIVOS 
            WHERE IncidenteID = ? AND Activo = 1
            GROUP BY SeccionID
            ORDER BY SeccionID
        """, (INCIDENTE_ID,))
        
        print("\n   Archivos por sección:")
        for row in cursor.fetchall():
            print(f"   - Sección {row.SeccionID}: {row.total} archivos")
        
        # Contar taxonomías
        cursor.execute("""
            SELECT COUNT(*) FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?
        """, (INCIDENTE_ID,))
        
        total_tax = cursor.fetchone()[0]
        print(f"\n   Taxonomías seleccionadas: {total_tax}")
        
        print("\n✅ DATOS DE PRUEBA INSERTADOS EXITOSAMENTE")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    insertar_datos_prueba()
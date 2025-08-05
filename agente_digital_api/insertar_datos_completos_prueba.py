"""
Script para insertar datos completos de prueba en incidente 5
Incluye archivos, taxonomías seleccionadas con justificaciones
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
        print("INSERTANDO DATOS COMPLETOS DE PRUEBA")
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
        
        # 3. Insertar archivos de prueba
        print("\n📎 Insertando archivos de prueba...")
        
        incidente_dir = os.path.join(UPLOAD_FOLDER, 'incidentes', str(INCIDENTE_ID))
        os.makedirs(incidente_dir, exist_ok=True)
        
        archivos_data = [
            # Sección 2
            (2, 'analisis_inicial.pdf', 'application/pdf', 256.8, 'Análisis inicial del incidente', 'Documento con el primer análisis realizado'),
            (2, 'evidencia_logs.txt', 'text/plain', 45.2, 'Logs del sistema', 'Logs capturados durante el incidente'),
            
            # Sección 3
            (3, 'diagrama_red.png', 'image/png', 189.5, 'Diagrama de red afectada', 'Muestra los sistemas comprometidos'),
            (3, 'reporte_vulnerabilidad.docx', 'application/msword', 78.3, 'Reporte de vulnerabilidad', 'Análisis de la vulnerabilidad explotada'),
            
            # Sección 5
            (5, 'plan_accion.xlsx', 'application/vnd.ms-excel', 34.7, 'Plan de acción', 'Acciones inmediatas tomadas'),
            
            # Sección 6
            (6, 'lecciones_aprendidas.pdf', 'application/pdf', 156.2, 'Documento de lecciones', 'Resumen de mejoras identificadas'),
            (6, 'mejoras_propuestas.docx', 'application/msword', 89.4, 'Propuestas de mejora', 'Cambios sugeridos para evitar recurrencia')
        ]
        
        for seccion, nombre, tipo, tamaño, desc, comentario in archivos_data:
            archivo_path = os.path.join(incidente_dir, nombre)
            
            # Crear archivo físico
            with open(archivo_path, 'w') as f:
                f.write(f"Archivo de prueba: {nombre}\n")
                f.write(f"Sección: {seccion}\n")
                f.write(f"Descripción: {desc}\n")
            
            # Insertar en BD
            cursor.execute("""
                INSERT INTO INCIDENTES_ARCHIVOS 
                (IncidenteID, NombreArchivo, TipoArchivo, TamanoKB, RutaArchivo,
                 SeccionID, Descripcion, Comentario, FechaCarga, SubidoPor, Activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), 'sistema_prueba', 1)
            """, (INCIDENTE_ID, nombre, tipo, tamaño, archivo_path, seccion, desc, comentario))
            
            print(f"   ✅ {nombre} (Sección {seccion})")
        
        # 4. Insertar taxonomías seleccionadas con justificaciones
        print("\n🏷️ Insertando taxonomías seleccionadas...")
        
        taxonomias_data = [
            ('INC_CONF_EXCF_FCRA', 
             'Se detectó una filtración de configuraciones críticas en las rutas de la aplicación principal. Los archivos de configuración contenían credenciales y claves API que quedaron expuestas.',
             'El problema se originó por permisos incorrectos en el directorio de configuración. La aplicación web tenía acceso de lectura a archivos que deberían estar protegidos.'),
            
            ('INC_DISP_DENE_DDOS',
             'El servicio sufrió una denegación distribuida que afectó la disponibilidad durante 3 horas. Se identificaron múltiples IPs de origen atacando simultáneamente.',
             'La infraestructura no contaba con protección DDoS adecuada. Los límites de rate limiting eran insuficientes para el volumen de tráfico malicioso.'),
            
            ('INC_CONF_ACCN_CIAU',
             'Se comprometieron credenciales de usuario administrador mediante un ataque de phishing dirigido. El atacante obtuvo acceso privilegiado al sistema.',
             'El usuario administrador cayó en un correo de phishing muy elaborado. No se tenía implementada autenticación de dos factores para cuentas privilegiadas.')
        ]
        
        for tax_id, justificacion, descripcion in taxonomias_data:
            cursor.execute("""
                INSERT INTO INCIDENTE_TAXONOMIA
                (IncidenteID, TaxonomiaID, Justificacion, DescripcionProblema,
                 FechaAsignacion, AsignadoPor)
                VALUES (?, ?, ?, ?, GETDATE(), 'sistema_prueba')
            """, (INCIDENTE_ID, tax_id, justificacion, descripcion))
            
            print(f"   ✅ {tax_id}")
            print(f"      - Justificación: {justificacion[:60]}...")
            print(f"      - Descripción: {descripcion[:60]}...")
        
        # 5. Actualizar algunos campos del incidente para completitud
        print("\n📝 Actualizando campos del incidente...")
        
        cursor.execute("""
            UPDATE Incidentes
            SET AccionesInmediatas = 'Se aplicaron medidas de contención inmediatas: 
1. Aislamiento de sistemas comprometidos
2. Cambio de credenciales afectadas
3. Aplicación de parches de seguridad
4. Monitoreo intensivo de logs',
                MedidasContencion = 'Bloqueo de IPs maliciosas, actualización de reglas de firewall, implementación de rate limiting',
                CausaRaiz = 'Configuración inadecuada de permisos y falta de segmentación de red apropiada',
                LeccionesAprendidas = 'Necesidad de implementar: 1) Revisión periódica de permisos, 2) MFA obligatorio, 3) Segmentación de red mejorada',
                SolucionImplementada = 'Se implementó nueva arquitectura de seguridad con segmentación de red y políticas de acceso mejoradas'
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
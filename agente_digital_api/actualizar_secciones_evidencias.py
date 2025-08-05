#!/usr/bin/env python3
"""
Script para actualizar correctamente las secciones de las evidencias del incidente 17
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db_connection

def actualizar_secciones():
    """Actualiza las secciones de las evidencias"""
    
    incidente_id = 17
    print(f"🔧 ACTUALIZANDO SECCIONES DE EVIDENCIAS DEL INCIDENTE {incidente_id}")
    print("=" * 60)
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ Error de conexión a BD")
            return
            
        cursor = conn.cursor()
        
        # Mapeo de evidencias a secciones basado en el diagnóstico
        actualizaciones = [
            # Sección 2 - Descripción
            (24, 'tablas_bd.txt', '2'),  # ID 24
            (25, 'incidente.txt', '2'),  # ID 25
            # Sección 3 - Análisis
            (26, 'TAXONOMIA_TABLA.txt', '3'),  # ID 26 (uno de los duplicados)
            # Sección 4 - Acciones
            (27, 'README_EMERGENCIA.md', '4'),  # Si existe
            # Sección 5 - Análisis Final
            # Dejar vacío por ahora
        ]
        
        print("\n1️⃣ ACTUALIZANDO SECCIONES...")
        
        # Primero actualizar la sección 3 para el primer TAXONOMIA_TABLA.txt
        cursor.execute("""
            UPDATE EvidenciasIncidentes 
            SET Seccion = '3', Descripcion = 'Análisis de taxonomías'
            WHERE IncidenteID = ? AND EvidenciaID = 26
        """, (incidente_id,))
        print("   ✅ TAXONOMIA_TABLA.txt movido a sección 3 (Análisis)")
        
        # Actualizar secciones generales
        cursor.execute("""
            UPDATE EvidenciasIncidentes 
            SET Seccion = '2'
            WHERE IncidenteID = ? AND EvidenciaID IN (24, 25)
        """, (incidente_id,))
        print("   ✅ Archivos de descripción actualizados a sección 2")
        
        # Verificar si hay README_EMERGENCIA.md
        cursor.execute("""
            SELECT EvidenciaID FROM EvidenciasIncidentes 
            WHERE IncidenteID = ? AND NombreArchivo = 'README_EMERGENCIA.md'
        """, (incidente_id,))
        readme = cursor.fetchone()
        if readme:
            cursor.execute("""
                UPDATE EvidenciasIncidentes 
                SET Seccion = '4', Descripcion = 'Acciones inmediatas'
                WHERE IncidenteID = ? AND EvidenciaID = ?
            """, (incidente_id, readme[0]))
            print("   ✅ README_EMERGENCIA.md movido a sección 4 (Acciones)")
        
        # Eliminar el duplicado de TAXONOMIA_TABLA.txt
        cursor.execute("""
            DELETE FROM EvidenciasIncidentes 
            WHERE IncidenteID = ? AND EvidenciaID = 27
        """, (incidente_id,))
        print("   ✅ Duplicado de TAXONOMIA_TABLA.txt eliminado")
        
        conn.commit()
        
        # 2. VERIFICAR CAMBIOS
        print("\n2️⃣ VERIFICANDO DISTRIBUCIÓN FINAL...")
        cursor.execute("""
            SELECT Seccion, COUNT(*) as Total, 
                   STRING_AGG(NombreArchivo, ', ') as Archivos
            FROM EvidenciasIncidentes 
            WHERE IncidenteID = ?
            GROUP BY Seccion
            ORDER BY Seccion
        """, (incidente_id,))
        
        for row in cursor.fetchall():
            seccion, total, archivos = row
            print(f"   Sección {seccion}: {total} archivos - {archivos}")
        
        # 3. AGREGAR EVIDENCIA DE TAXONOMÍA SI NO EXISTE
        print("\n3️⃣ VERIFICANDO EVIDENCIAS DE TAXONOMÍA...")
        cursor.execute("""
            SELECT COUNT(*) FROM EVIDENCIAS_TAXONOMIA WHERE IncidenteID = ?
        """, (incidente_id,))
        
        num_ev_tax = cursor.fetchone()[0]
        if num_ev_tax == 0:
            print("   ⚠️ No hay evidencias de taxonomía, agregando archivo existente...")
            
            # Obtener la taxonomía asignada
            cursor.execute("""
                SELECT Id_Taxonomia FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?
            """, (incidente_id,))
            taxonomia = cursor.fetchone()
            
            if taxonomia:
                tax_id = taxonomia[0]
                # Asignar TAXONOMIA_TABLA.txt a la taxonomía
                cursor.execute("""
                    INSERT INTO EVIDENCIAS_TAXONOMIA 
                    (IncidenteID, Id_Taxonomia, NumeroEvidencia, NombreArchivo, 
                     RutaArchivo, Descripcion, FechaSubida, SubidoPor)
                    SELECT ?, ?, '4.4.1.1', NombreArchivo, RutaArchivo, 
                           'Evidencia de taxonomía', GETDATE(), 'Sistema'
                    FROM EvidenciasIncidentes
                    WHERE IncidenteID = ? AND NombreArchivo = 'TAXONOMIA_TABLA.txt'
                    AND EvidenciaID = (
                        SELECT MIN(EvidenciaID) FROM EvidenciasIncidentes 
                        WHERE IncidenteID = ? AND NombreArchivo = 'TAXONOMIA_TABLA.txt'
                    )
                """, (incidente_id, tax_id, incidente_id, incidente_id))
                
                if cursor.rowcount > 0:
                    print(f"   ✅ TAXONOMIA_TABLA.txt agregado como evidencia de taxonomía {tax_id}")
                    conn.commit()
        
        print("\n✅ PROCESO COMPLETADO")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    actualizar_secciones()
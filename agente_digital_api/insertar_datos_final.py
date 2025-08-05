"""
Script final para insertar datos de prueba con estructura correcta
"""

from app.database import get_db_connection
from datetime import datetime

INCIDENTE_ID = 5

def insertar_datos_completos():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("=" * 70)
        print("INSERTANDO DATOS COMPLETOS DE PRUEBA - ESTRUCTURA CORRECTA")
        print("=" * 70)
        
        # 1. Verificar incidente
        cursor.execute("SELECT IncidenteID FROM Incidentes WHERE IncidenteID = ?", (INCIDENTE_ID,))
        if not cursor.fetchone():
            print(f"❌ Incidente {INCIDENTE_ID} no encontrado")
            return
        print(f"✅ Incidente {INCIDENTE_ID} encontrado")
        
        # 2. Limpiar datos anteriores
        print("\n🧹 Limpiando datos anteriores...")
        cursor.execute("DELETE FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?", (INCIDENTE_ID,))
        print("   - Taxonomías eliminadas")
        
        # 3. Obtener taxonomías disponibles
        print("\n🔍 Buscando taxonomías disponibles...")
        cursor.execute("""
            SELECT TOP 3 Id_Incidente, Area, Efecto, Descripcion 
            FROM Taxonomia_incidentes
        """)
        
        taxonomias_disponibles = cursor.fetchall()
        
        if not taxonomias_disponibles:
            print("   ⚠️ No se encontraron taxonomías")
        else:
            print(f"   ✅ Encontradas {len(taxonomias_disponibles)} taxonomías")
            
            # 4. Insertar taxonomías con comentarios
            print("\n🏷️ Insertando taxonomías seleccionadas...")
            
            for tax in taxonomias_disponibles:
                id_tax = tax[0]
                area = tax[1]
                efecto = tax[2]
                desc = tax[3]
                
                comentario = f"Esta taxonomía aplica porque se identificó {efecto} en el área de {area}. {desc[:100]}"
                
                cursor.execute("""
                    INSERT INTO INCIDENTE_TAXONOMIA
                    (IncidenteID, Id_Taxonomia, Comentarios, FechaAsignacion, CreadoPor)
                    VALUES (?, ?, ?, GETDATE(), 'sistema_prueba')
                """, (INCIDENTE_ID, id_tax, comentario))
                
                print(f"   ✅ {id_tax} - {area}/{efecto}")
                print(f"      Comentario: {comentario[:60]}...")
        
        # 5. Actualizar campos del incidente
        print("\n📝 Actualizando campos del incidente...")
        
        cursor.execute("""
            UPDATE Incidentes
            SET ServiciosInterrumpidos = 'Portal web, Sistema de facturación, API REST',
                PlanMejora = 'Implementar autenticación multifactor y mejorar monitoreo',
                AnciImpactoPreliminar = 'Impacto medio-alto con afectación a servicios críticos',
                DescripcionInicial = CASE 
                    WHEN DescripcionInicial IS NULL OR DescripcionInicial = '' 
                    THEN 'Incidente de seguridad detectado con impacto en múltiples sistemas'
                    ELSE DescripcionInicial
                END
            WHERE IncidenteID = ?
        """, (INCIDENTE_ID,))
        
        print("   ✅ Campos actualizados")
        
        # 6. Verificar archivos existentes
        cursor.execute("""
            SELECT COUNT(*) as total, SeccionID 
            FROM INCIDENTES_ARCHIVOS 
            WHERE IncidenteID = ? AND Activo = 1
            GROUP BY SeccionID
            ORDER BY SeccionID
        """, (INCIDENTE_ID,))
        
        print("\n📊 Resumen de datos:")
        print("   Archivos por sección:")
        for row in cursor.fetchall():
            print(f"   - Sección {row.SeccionID}: {row.total} archivos")
        
        # Contar taxonomías
        cursor.execute("""
            SELECT COUNT(*) FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?
        """, (INCIDENTE_ID,))
        
        total_tax = cursor.fetchone()[0]
        print(f"\n   Taxonomías seleccionadas: {total_tax}")
        
        # Confirmar cambios
        conn.commit()
        
        print("\n✅ DATOS INSERTADOS EXITOSAMENTE")
        print("   Ahora puedes probar la carga en el frontend")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    insertar_datos_completos()
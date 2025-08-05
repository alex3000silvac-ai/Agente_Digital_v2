"""
Script simplificado para insertar taxonomías de prueba
"""

from app.database import get_db_connection
from datetime import datetime

INCIDENTE_ID = 5

def insertar_taxonomias_prueba():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("=" * 70)
        print("INSERTANDO TAXONOMÍAS DE PRUEBA")
        print("=" * 70)
        
        # Limpiar taxonomías anteriores
        cursor.execute("DELETE FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?", (INCIDENTE_ID,))
        print("✅ Taxonomías anteriores eliminadas")
        
        # Insertar taxonomías directamente con IDs conocidos
        taxonomias_prueba = [
            ('TAX001', 'Se detectó una vulnerabilidad crítica que fue explotada', 'La vulnerabilidad permitió acceso no autorizado'),
            ('TAX002', 'El ataque causó interrupción del servicio', 'Los sistemas estuvieron fuera de línea por 2 horas'),
            ('TAX003', 'Se identificó exfiltración de datos sensibles', 'Datos de configuración fueron comprometidos')
        ]
        
        for tax_id, justificacion, descripcion in taxonomias_prueba:
            try:
                cursor.execute("""
                    INSERT INTO INCIDENTE_TAXONOMIA
                    (IncidenteID, TaxonomiaID, Justificacion, DescripcionProblema,
                     FechaAsignacion, AsignadoPor)
                    VALUES (?, ?, ?, ?, GETDATE(), 'sistema_prueba')
                """, (INCIDENTE_ID, tax_id, justificacion, descripcion))
                print(f"✅ Taxonomía {tax_id} insertada")
            except Exception as e:
                print(f"⚠️ No se pudo insertar {tax_id}: {e}")
        
        conn.commit()
        print("\n✅ Proceso completado")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    insertar_taxonomias_prueba()
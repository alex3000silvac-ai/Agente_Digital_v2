#!/usr/bin/env python3
"""
Corregir los comentarios mal codificados de las taxonomías
"""

def corregir_comentarios():
    """Corregir encoding de comentarios"""
    try:
        print("🔧 CORRIGIENDO COMENTARIOS DE TAXONOMÍAS")
        print("=" * 80)
        
        from app.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Ver el problema actual
        print("\n1️⃣ ESTADO ACTUAL:")
        cursor.execute("""
            SELECT 
                ID,
                IncidenteID,
                Id_Taxonomia,
                Comentarios
            FROM INCIDENTE_TAXONOMIA
            WHERE IncidenteID = 25
        """)
        
        for row in cursor.fetchall():
            print(f"\n   ID: {row[0]}")
            print(f"   Comentarios actuales: {row[3][:100]}...")
            
            # Corregir el encoding
            comentarios_corregidos = row[3].replace('JustificaciÃ³n:', 'Justificación:').replace('DescripciÃ³n del problema:', 'Descripción del problema:')
            
            print(f"   Comentarios corregidos: {comentarios_corregidos[:100]}...")
            
            # Actualizar en la BD
            cursor.execute("""
                UPDATE INCIDENTE_TAXONOMIA
                SET Comentarios = ?
                WHERE ID = ?
            """, (comentarios_corregidos, row[0]))
            
            print("   ✅ Actualizado")
        
        conn.commit()
        
        # 2. Verificar la corrección
        print("\n2️⃣ VERIFICACIÓN DESPUÉS DE LA CORRECCIÓN:")
        cursor.execute("""
            SELECT 
                Id_Taxonomia,
                Comentarios
            FROM INCIDENTE_TAXONOMIA
            WHERE IncidenteID = 25
        """)
        
        for row in cursor.fetchall():
            print(f"\n   Taxonomía: {row[0]}")
            comentarios = row[1]
            
            # Verificar que ahora sí se puede parsear
            if 'Justificación:' in comentarios:
                print("   ✅ Formato correcto detectado")
                
                # Intentar extraer justificación y descripción
                parts = comentarios.split('Justificación:', 1)
                if len(parts) > 1:
                    justif_parts = parts[1].split('\n', 1)
                    justificacion = justif_parts[0].strip()
                    print(f"   Justificación: {justificacion}")
                    
                    if len(justif_parts) > 1 and 'Descripción del problema:' in justif_parts[1]:
                        desc_parts = justif_parts[1].split('Descripción del problema:', 1)
                        if len(desc_parts) > 1:
                            descripcion = desc_parts[1].strip()
                            print(f"   Descripción: {descripcion[:50]}...")
            else:
                print("   ❌ Formato incorrecto")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Corrección completada")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    corregir_comentarios()
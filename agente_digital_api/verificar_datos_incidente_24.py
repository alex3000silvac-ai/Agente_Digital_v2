#!/usr/bin/env python3
"""
Verificar datos completos del incidente 24
"""

def verificar_datos_navegacion():
    """Verificar que el incidente 24 tenga los datos necesarios para navegación"""
    try:
        print("🔍 VERIFICANDO DATOS DE NAVEGACIÓN - INCIDENTE 24")
        print("=" * 70)
        
        from app.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Consultar datos del incidente
        cursor.execute("""
            SELECT 
                I.IncidenteID,
                I.EmpresaID,
                I.Titulo
            FROM Incidentes I
            WHERE I.IncidenteID = 24
        """)
        
        resultado = cursor.fetchone()
        
        if resultado:
            print("\n✅ DATOS DEL INCIDENTE 24:")
            print(f"   IncidenteID: {resultado[0]}")
            print(f"   EmpresaID: {resultado[1]}")
            print(f"   Título: {resultado[2]}")
            
            # Si tiene empresa, buscar el inquilino
            if resultado[1]:
                cursor.execute("""
                    SELECT InquilinoID 
                    FROM Empresas 
                    WHERE EmpresaID = ?
                """, (resultado[1],))
                empresa_data = cursor.fetchone()
                
                if empresa_data:
                    inquilino_id = empresa_data[0]
                    print(f"   InquilinoID: {inquilino_id}")
                    
                    print("\n📋 RUTA DE NAVEGACIÓN CORRECTA:")
                    print(f"   Desde: /incidente-detalle/24")
                    print(f"   Hacia: /inquilino/{inquilino_id}/empresa/{resultado[1]}/incidentes")
                    print(f"   ✅ Navegación debería funcionar con:")
                    print(f"      - InquilinoID: {inquilino_id}")
                    print(f"      - EmpresaID: {resultado[1]}")
                else:
                    print(f"   ❌ No se encontró la empresa {resultado[1]}")
            else:
                print(f"   ❌ El incidente no tiene EmpresaID")
        else:
            print("\n❌ Incidente 24 no encontrado")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_datos_navegacion()
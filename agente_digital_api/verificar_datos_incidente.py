"""
Script para verificar los datos completos del incidente 5
"""

from app.database import get_db_connection
import json

INCIDENTE_ID = 5

def verificar_incidente():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("=" * 70)
        print(f"VERIFICACIÓN COMPLETA DEL INCIDENTE {INCIDENTE_ID}")
        print("=" * 70)
        
        # 1. Datos básicos del incidente
        print("\n📋 DATOS DEL INCIDENTE:")
        cursor.execute("""
            SELECT 
                IncidenteID,
                Titulo,
                DescripcionInicial,
                ServiciosInterrumpidos,
                PlanMejora,
                AccionesInmediatas,
                CausaRaiz,
                LeccionesAprendidas
            FROM Incidentes 
            WHERE IncidenteID = ?
        """, (INCIDENTE_ID,))
        
        incidente = cursor.fetchone()
        if incidente:
            columnas = [col[0] for col in cursor.description]
            for i, col in enumerate(columnas):
                valor = incidente[i]
                if valor and len(str(valor)) > 50:
                    valor = str(valor)[:50] + "..."
                print(f"   - {col}: {valor}")
        
        # 2. Archivos
        print("\n📎 ARCHIVOS ADJUNTOS:")
        cursor.execute("""
            SELECT 
                ArchivoID,
                SeccionID,
                NumeroArchivo,
                NombreOriginal,
                TamanoKB,
                Descripcion,
                FechaSubida
            FROM INCIDENTES_ARCHIVOS 
            WHERE IncidenteID = ? AND Activo = 1
            ORDER BY SeccionID, NumeroArchivo
        """, (INCIDENTE_ID,))
        
        archivos = cursor.fetchall()
        if archivos:
            seccion_actual = None
            for archivo in archivos:
                if archivo[1] != seccion_actual:
                    seccion_actual = archivo[1]
                    print(f"\n   Sección {seccion_actual}:")
                print(f"      - ID:{archivo[0]} | {archivo[3]} ({archivo[4]}KB)")
                print(f"        Desc: {archivo[5]}")
        else:
            print("   ❌ No hay archivos")
        
        # 3. Taxonomías
        print("\n🏷️ TAXONOMÍAS SELECCIONADAS:")
        cursor.execute("""
            SELECT 
                it.Id_Taxonomia,
                ti.Area,
                ti.Efecto,
                it.Comentarios
            FROM INCIDENTE_TAXONOMIA it
            LEFT JOIN Taxonomia_incidentes ti ON it.Id_Taxonomia = ti.Id_Incidente
            WHERE it.IncidenteID = ?
        """, (INCIDENTE_ID,))
        
        taxonomias = cursor.fetchall()
        if taxonomias:
            for tax in taxonomias:
                print(f"   - {tax[0]}")
                print(f"     Área: {tax[1]}")
                print(f"     Efecto: {tax[2]}")
                if tax[3]:
                    print(f"     Comentario: {tax[3][:60]}...")
        else:
            print("   ❌ No hay taxonomías")
        
        # 4. Simular respuesta del endpoint
        print("\n🔄 SIMULACIÓN DE RESPUESTA DEL ENDPOINT:")
        print("   El endpoint debería devolver:")
        print(f"   - {len(archivos)} archivos en total")
        print(f"   - {len(taxonomias)} taxonomías seleccionadas")
        print("   - Archivos organizados por sección")
        
        print("\n✅ Verificación completada")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verificar_incidente()
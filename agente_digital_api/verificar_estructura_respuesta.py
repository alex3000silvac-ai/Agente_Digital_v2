"""
Script para verificar la estructura de respuesta esperada
"""

from app.database import get_db_connection
import json

INCIDENTE_ID = 5

def verificar_estructura():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("=" * 70)
        print("VERIFICACIÓN DE ESTRUCTURA DE RESPUESTA")
        print("=" * 70)
        
        # Simular lo que hace el endpoint
        respuesta = {
            'archivos': {
                'seccion_2': [],
                'seccion_3': [],
                'seccion_5': [],
                'seccion_6': [],
                'taxonomias': {}
            },
            'taxonomias_seleccionadas': [],
            'formData': {}
        }
        
        # 1. Obtener archivos
        cursor.execute("""
            SELECT 
                ArchivoID,
                NombreOriginal,
                TipoArchivo,
                TamanoKB,
                SeccionID,
                FechaSubida,
                SubidoPor,
                Descripcion
            FROM INCIDENTES_ARCHIVOS
            WHERE IncidenteID = ? AND Activo = 1
            ORDER BY SeccionID, FechaSubida
        """, (INCIDENTE_ID,))
        
        archivos_rows = cursor.fetchall()
        
        for row in archivos_rows:
            archivo_data = {
                'id': row[0],
                'nombre': row[1],
                'tipo': row[2],
                'tamaño': row[3] * 1024 if row[3] else 0,
                'fechaCarga': str(row[5]) if row[5] else None,
                'subidoPor': row[6],
                'descripcion': row[7] or '',
                'comentario': '',
                'existente': True,
                'origen': 'guardado'
            }
            
            seccion_id = row[4]
            
            if seccion_id == 2:
                respuesta['archivos']['seccion_2'].append(archivo_data)
            elif seccion_id == 3:
                respuesta['archivos']['seccion_3'].append(archivo_data)
            elif seccion_id == 5:
                respuesta['archivos']['seccion_5'].append(archivo_data)
            elif seccion_id == 6:
                respuesta['archivos']['seccion_6'].append(archivo_data)
        
        print(f"\n📎 ARCHIVOS ENCONTRADOS:")
        for seccion, archivos in respuesta['archivos'].items():
            if isinstance(archivos, list) and len(archivos) > 0:
                print(f"   - {seccion}: {len(archivos)} archivos")
        
        # 2. Obtener taxonomías
        cursor.execute("""
            SELECT 
                it.Id_Taxonomia,
                ti.Id_Incidente as Nombre,
                ti.Area,
                ti.Efecto,
                ti.Categoria_del_Incidente,
                ti.Subcategoria_del_Incidente,
                it.Comentarios,
                it.FechaAsignacion
            FROM INCIDENTE_TAXONOMIA it
            INNER JOIN Taxonomia_incidentes ti ON it.Id_Taxonomia = ti.Id_Incidente
            WHERE it.IncidenteID = ?
        """, (INCIDENTE_ID,))
        
        taxonomias_rows = cursor.fetchall()
        
        for row in taxonomias_rows:
            tax_data = {
                'id': row[0],
                'nombre': row[1],
                'area': row[2],
                'efecto': row[3],
                'categoria': row[4],
                'subcategoria': row[5],
                'justificacion': row[6] or '',
                'descripcionProblema': '',
                'fechaSeleccion': str(row[7]) if row[7] else None,
                'archivos': []
            }
            respuesta['taxonomias_seleccionadas'].append(tax_data)
        
        print(f"\n🏷️ TAXONOMÍAS: {len(respuesta['taxonomias_seleccionadas'])}")
        
        # 3. Estructura esperada por el frontend
        print("\n📋 ESTRUCTURA QUE ESPERA EL FRONTEND:")
        print("   - archivos.seccion_2: Array de archivos")
        print("   - archivos.seccion_3: Array de archivos")
        print("   - archivos.seccion_5: Array de archivos")
        print("   - archivos.seccion_6: Array de archivos")
        print("   - taxonomias_seleccionadas: Array de taxonomías")
        print("   - formData: Objeto con campos del formulario")
        
        # Guardar estructura
        with open('estructura_respuesta.json', 'w', encoding='utf-8') as f:
            json.dump(respuesta, f, indent=2, ensure_ascii=False)
        print("\n💾 Estructura guardada en: estructura_respuesta.json")
        
        print("\n✅ El frontend debe:")
        print("   1. Recibir esta estructura en cargarIncidenteExistente()")
        print("   2. Asignar archivos a archivosSeccion2, archivosSeccion3, etc.")
        print("   3. Asignar taxonomías a taxonomiasSeleccionadas")
        print("   4. Mapear campos del incidente a formData")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verificar_estructura()
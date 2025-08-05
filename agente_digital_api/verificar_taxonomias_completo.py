"""
Script mejorado para verificar taxonomías en la base de datos
"""
import pyodbc
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import get_db_connection

def verificar_taxonomias_incidente(incidente_id):
    """Verifica las taxonomías guardadas para un incidente específico"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print(f"\n{'='*70}")
        print(f"VERIFICANDO TAXONOMÍAS PARA INCIDENTE {incidente_id}")
        print(f"{'='*70}\n")
        
        # 1. Verificar si el incidente existe
        cursor.execute("""
            SELECT IncidenteID, Titulo, EstadoActual, ReporteAnciID
            FROM INCIDENTES
            WHERE IncidenteID = ?
        """, (incidente_id,))
        
        incidente = cursor.fetchone()
        if not incidente:
            print(f"❌ No se encontró el incidente {incidente_id}")
            return
            
        print(f"✅ Incidente encontrado:")
        print(f"   - ID: {incidente[0]}")
        print(f"   - Título: {incidente[1]}")
        print(f"   - Estado: {incidente[2]}")
        print(f"   - ReporteAnciID: {incidente[3]}")
        
        # 2. Verificar tabla INCIDENTE_TAXONOMIA con la estructura correcta
        print(f"\n📋 TAXONOMÍAS EN INCIDENTE_TAXONOMIA:")
        print(f"{'='*70}")
        
        cursor.execute("""
            SELECT 
                it.ID,
                it.IncidenteID,
                it.Id_Taxonomia,
                it.Comentarios,
                it.FechaAsignacion,
                it.CreadoPor,
                t.Id_Incidente,
                t.Area,
                t.Efecto,
                t.Categoria_del_Incidente,
                t.Subcategoria_del_Incidente,
                t.Tipo_del_Incidente,
                t.AplicaTipoEmpresa
            FROM INCIDENTE_TAXONOMIA it
            LEFT JOIN Taxonomia_incidentes t ON it.Id_Taxonomia = t.Id_Incidente
            WHERE it.IncidenteID = ?
            ORDER BY it.FechaAsignacion DESC
        """, (incidente_id,))
        
        columnas = [desc[0] for desc in cursor.description]
        taxonomias = cursor.fetchall()
        
        if not taxonomias:
            print("❌ No hay taxonomías guardadas para este incidente")
        else:
            print(f"✅ Se encontraron {len(taxonomias)} taxonomías:\n")
            
            for idx, tax in enumerate(taxonomias, 1):
                row_dict = dict(zip(columnas, tax))
                
                print(f"{idx}. ID Relación: {row_dict['ID']}")
                print(f"   Id_Taxonomia: {row_dict['Id_Taxonomia']}")
                print(f"   Área: {row_dict['Area']}")
                print(f"   Efecto: {row_dict['Efecto']}")
                print(f"   Categoría: {row_dict['Categoria_del_Incidente']}")
                print(f"   Subcategoría: {row_dict['Subcategoria_del_Incidente']}")
                print(f"   Tipo: {row_dict['Tipo_del_Incidente']}")
                print(f"   Comentarios/Justificación: {row_dict['Comentarios'][:100] + '...' if row_dict['Comentarios'] and len(row_dict['Comentarios']) > 100 else row_dict['Comentarios']}")
                print(f"   Fecha Asignación: {row_dict['FechaAsignacion']}")
                print(f"   Creado Por: {row_dict['CreadoPor']}")
                print(f"   {'-'*50}")
        
        # 3. Verificar cómo el endpoint obtiene las taxonomías
        print(f"\n🔍 QUERY QUE USA EL ENDPOINT:")
        print(f"{'='*70}")
        
        # Esta es la query del endpoint según el código
        cursor.execute("""
            SELECT 
                it.Id_Taxonomia,
                t.Nombre,
                t.Area,
                t.Efecto,
                t.Categoria_del_Incidente,
                t.Subcategoria_del_Incidente,
                t.Tipo_del_Incidente,
                t.Descripcion,
                it.Comentarios as Justificacion,
                NULL as DescripcionProblema,
                it.FechaAsignacion as FechaSeleccion,
                it.CreadoPor as UsuarioSeleccion
            FROM INCIDENTE_TAXONOMIA it
            INNER JOIN Taxonomia_incidentes t ON it.Id_Taxonomia = t.Id_Incidente
            WHERE it.IncidenteID = ?
        """, (incidente_id,))
        
        taxonomias_endpoint = cursor.fetchall()
        columnas_endpoint = [desc[0] for desc in cursor.description]
        
        print("Datos como los devuelve el endpoint:")
        for idx, tax in enumerate(taxonomias_endpoint, 1):
            row_dict = dict(zip(columnas_endpoint, tax))
            print(f"\n{idx}. Taxonomía:")
            print(f"   ID: {row_dict['Id_Taxonomia']} (tipo: {type(row_dict['Id_Taxonomia']).__name__})")
            print(f"   Justificación: {row_dict['Justificacion']}")
            
        # 4. Mostrar formato esperado por el frontend
        print(f"\n📊 FORMATO ESPERADO POR EL FRONTEND:")
        print(f"{'='*70}")
        
        if taxonomias_endpoint:
            tax = taxonomias_endpoint[0]
            row_dict = dict(zip(columnas_endpoint, tax))
            
            formato_frontend = {
                'id': row_dict['Id_Taxonomia'],  # El frontend espera 'id'
                'TaxonomiaID': row_dict['Id_Taxonomia'],
                'nombre': row_dict['Nombre'],
                'area': row_dict['Area'],
                'efecto': row_dict['Efecto'],
                'categoria': row_dict['Categoria_del_Incidente'],
                'subcategoria': row_dict['Subcategoria_del_Incidente'],
                'justificacion': row_dict['Justificacion'],
                'Justificacion': row_dict['Justificacion'],
                'descripcionProblema': row_dict['DescripcionProblema'],
                'fechaSeleccion': row_dict['FechaSeleccion'].isoformat() if row_dict['FechaSeleccion'] else None,
                'usuarioSeleccion': row_dict['UsuarioSeleccion']
            }
            
            print("JSON esperado:")
            print(json.dumps(formato_frontend, indent=2, ensure_ascii=False, default=str))
            
            print(f"\n⚠️ IMPORTANTE:")
            print(f"   - El ID viene como: {row_dict['Id_Taxonomia']} (tipo: {type(row_dict['Id_Taxonomia']).__name__})")
            print(f"   - El frontend lo compara como STRING")
            print(f"   - Necesita normalización de tipos")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    incidente_id = 5
    if len(sys.argv) > 1:
        incidente_id = int(sys.argv[1])
    
    verificar_taxonomias_incidente(incidente_id)
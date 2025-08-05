#!/usr/bin/env python3
"""
Test final de estadísticas
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db_connection

def test_final():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        incidente_id = 5
        print(f"=== ESTADÍSTICAS REALES PARA INCIDENTE {incidente_id} ===\n")
        
        # 1. Archivos
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INCIDENTES_ARCHIVOS 
            WHERE IncidenteID = ? AND Activo = 1
        """, (incidente_id,))
        archivos = cursor.fetchone()[0]
        print(f"Archivos en INCIDENTES_ARCHIVOS: {archivos}")
        
        # Mostrar algunos archivos
        if archivos > 0:
            cursor.execute("""
                SELECT TOP 3 NombreOriginal, Descripcion, FechaSubida
                FROM INCIDENTES_ARCHIVOS 
                WHERE IncidenteID = ? AND Activo = 1
                ORDER BY FechaSubida DESC
            """, (incidente_id,))
            files = cursor.fetchall()
            for f in files:
                print(f"  - {f[0]} ({f[1]}) - {f[2]}")
        
        # 2. Comentarios
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INCIDENTES_COMENTARIOS 
            WHERE IncidenteID = ? AND Activo = 1
        """, (incidente_id,))
        comentarios = cursor.fetchone()[0]
        print(f"\nComentarios en INCIDENTES_COMENTARIOS: {comentarios}")
        
        # 3. Taxonomías
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INCIDENTE_TAXONOMIA 
                WHERE Id_Incidente = ?
            """, (incidente_id,))
            taxonomias = cursor.fetchone()[0]
            print(f"\nTaxonomías seleccionadas: {taxonomias}")
            
            if taxonomias > 0:
                cursor.execute("""
                    SELECT it.Id_Taxonomia, ti.Categoria_del_Incidente, ti.Subcategoria_del_Incidente
                    FROM INCIDENTE_TAXONOMIA it
                    LEFT JOIN TaxonomiaIncidentes ti ON it.Id_Taxonomia = ti.Id_Taxonomia
                    WHERE it.Id_Incidente = ?
                """, (incidente_id,))
                tax_list = cursor.fetchall()
                for t in tax_list:
                    print(f"  - {t[1]} / {t[2]}")
        except:
            print("\nNo se pudieron obtener taxonomías")
        
        # 4. Tipo de empresa
        cursor.execute("""
            SELECT i.EmpresaID, e.TipoEmpresa, e.RazonSocial
            FROM INCIDENTES i
            LEFT JOIN EMPRESAS e ON i.EmpresaID = e.EmpresaID
            WHERE i.IncidenteID = ?
        """, (incidente_id,))
        empresa = cursor.fetchone()
        print(f"\n=== INFORMACIÓN DE EMPRESA ===")
        print(f"EmpresaID: {empresa[0]}")
        print(f"Tipo: {empresa[1]} ⚠️")
        print(f"Razón Social: {empresa[2]}")
        
        # 5. Plazos según tipo
        tipo = empresa[1]
        print(f"\n=== PLAZOS LEGALES PARA {tipo} ===")
        if tipo == 'OIV':
            print("- Informe Preliminar: 24 HORAS")
            print("- Informe Completo: 72 HORAS")
        else:
            print("- Informe Preliminar: 72 HORAS")
            print("- Informe Completo: 72 HORAS")
        
        # 6. Calcular estadísticas finales
        total_evidencias = archivos
        total_comentarios = comentarios
        
        # Comentarios de taxonomías
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM COMENTARIOS_TAXONOMIA 
                WHERE Id_Incidente = ?
            """, (incidente_id,))
            com_tax = cursor.fetchone()[0]
            total_comentarios += com_tax
            print(f"\nComentarios adicionales en taxonomías: {com_tax}")
        except:
            pass
        
        # Evidencias de taxonomías
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM EVIDENCIAS_TAXONOMIA 
                WHERE Id_Incidente = ?
            """, (incidente_id,))
            ev_tax = cursor.fetchone()[0]
            total_evidencias += ev_tax
            print(f"Evidencias adicionales en taxonomías: {ev_tax}")
        except:
            pass
        
        print(f"\n=== ESTADÍSTICAS FINALES ===")
        print(f"Total Evidencias: {total_evidencias}")
        print(f"Total Comentarios: {total_comentarios}")
        print(f"Taxonomías: {taxonomias if 'taxonomias' in locals() else 0}")
        
        # Calcular completitud
        elementos = sum([
            total_evidencias > 0,
            total_comentarios > 0,
            taxonomias > 0 if 'taxonomias' in locals() else False
        ])
        completitud = int((elementos / 3) * 100)
        print(f"Completitud estimada: {completitud}%")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    test_final()
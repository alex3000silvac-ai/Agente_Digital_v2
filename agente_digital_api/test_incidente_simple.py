#!/usr/bin/env python3
"""
Script de prueba simple para verificar la creación de incidentes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db_connection
from datetime import datetime

def test_crear_incidente_directo():
    """Prueba la creación directa de un incidente en la BD"""
    print("="*60)
    print("PRUEBA DE CREACIÓN DIRECTA DE INCIDENTE")
    print("="*60)
    
    conn = get_db_connection()
    if not conn:
        print("❌ Error: No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor()
        
        # Datos de prueba
        titulo = f"Incidente de prueba - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Insertar incidente
        query = """
            INSERT INTO Incidentes (
                Titulo, DescripcionInicial, Criticidad, EstadoActual, FechaCreacion, FechaActualizacion,
                EmpresaID, CreadoPor, FechaDeteccion, TipoFlujo, OrigenIncidente,
                SistemasAfectados, AccionesInmediatas
            ) VALUES (?, ?, ?, ?, GETDATE(), GETDATE(), ?, ?, GETDATE(), ?, ?, ?, ?)
        """
        
        cursor.execute(query,
            titulo,
            "Descripción detallada del incidente de prueba",
            "Alta",
            "Abierto",
            2,  # EmpresaID
            "usuario_prueba",
            "Informativo",
            "Sistema interno",
            "Sistemas afectados de prueba",
            "Acciones inmediatas de prueba"
        )
        
        conn.commit()
        
        # Obtener ID del incidente creado
        cursor.execute("SELECT @@IDENTITY AS IncidenteID")
        row = cursor.fetchone()
        incidente_id = row[0] if row else None
        
        print(f"✅ Incidente creado exitosamente con ID: {incidente_id}")
        
        # Verificar que se creó correctamente
        cursor.execute("""
            SELECT IncidenteID, Titulo, DescripcionInicial, Criticidad, EstadoActual, FechaCreacion
            FROM Incidentes
            WHERE IncidenteID = ?
        """, incidente_id)
        
        incidente = cursor.fetchone()
        if incidente:
            print("\nDatos del incidente creado:")
            print(f"  - ID: {incidente.IncidenteID}")
            print(f"  - Título: {incidente.Titulo}")
            print(f"  - Descripción: {incidente.DescripcionInicial[:50]}...")
            print(f"  - Criticidad: {incidente.Criticidad}")
            print(f"  - Estado: {incidente.EstadoActual}")
            print(f"  - Fecha: {incidente.FechaCreacion}")
        
        # Agregar taxonomía de prueba
        query_taxonomia = """
            INSERT INTO INCIDENTE_TAXONOMIA (IncidenteID, Id_Taxonomia, Comentarios, FechaAsignacion, CreadoPor)
            VALUES (?, ?, ?, GETDATE(), ?)
        """
        cursor.execute(query_taxonomia, incidente_id, "TAX001", "Taxonomía de prueba", "usuario_prueba")
        conn.commit()
        print("\n✅ Taxonomía asociada exitosamente")
        
        # Agregar comentario de prueba
        query_comentario = """
            INSERT INTO COMENTARIOS_TAXONOMIA (IncidenteID, TaxonomiaID, Comentario, Version, FechaCreacion, CreadoPor)
            VALUES (?, ?, ?, ?, GETDATE(), ?)
        """
        cursor.execute(query_comentario, incidente_id, "TAX001", "Comentario de prueba", 1, "usuario_prueba")
        conn.commit()
        print("✅ Comentario agregado exitosamente")
        
        # Verificar integridad
        print("\nVerificando integridad de datos:")
        
        # Contar taxonomías
        cursor.execute("SELECT COUNT(*) as total FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?", incidente_id)
        total_tax = cursor.fetchone().total
        print(f"  - Taxonomías asociadas: {total_tax}")
        
        # Contar comentarios
        cursor.execute("SELECT COUNT(*) as total FROM COMENTARIOS_TAXONOMIA WHERE IncidenteID = ?", incidente_id)
        total_com = cursor.fetchone().total
        print(f"  - Comentarios asociados: {total_com}")
        
        return incidente_id
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        conn.close()

def test_recuperar_incidente(incidente_id):
    """Prueba la recuperación de un incidente con todos sus datos relacionados"""
    print("\n" + "="*60)
    print("PRUEBA DE RECUPERACIÓN DE INCIDENTE")
    print("="*60)
    
    if not incidente_id:
        print("⚠️ No hay ID de incidente para recuperar")
        return
    
    conn = get_db_connection()
    if not conn:
        print("❌ Error: No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor()
        
        # Recuperar incidente completo
        cursor.execute("""
            SELECT 
                i.IncidenteID, i.Titulo, i.DescripcionInicial, i.Criticidad, i.EstadoActual,
                i.FechaCreacion, i.FechaDeteccion, i.TipoFlujo, i.OrigenIncidente,
                i.SistemasAfectados, i.AccionesInmediatas
            FROM Incidentes i
            WHERE i.IncidenteID = ?
        """, incidente_id)
        
        incidente = cursor.fetchone()
        if incidente:
            print("✅ Incidente recuperado exitosamente")
            print(f"\nDatos recuperados:")
            print(f"  - ID: {incidente.IncidenteID}")
            print(f"  - Título: {incidente.Titulo}")
            print(f"  - Criticidad: {incidente.Criticidad}")
            print(f"  - Estado: {incidente.EstadoActual}")
            print(f"  - Tipo Flujo: {incidente.TipoFlujo}")
            print(f"  - Origen: {incidente.OrigenIncidente}")
            
            # Recuperar taxonomías
            cursor.execute("""
                SELECT it.Id_Taxonomia, it.Comentarios, ti.Area, ti.Efecto, ti.Categoria_del_Incidente
                FROM INCIDENTE_TAXONOMIA it
                LEFT JOIN TAXONOMIA_INCIDENTES ti ON it.Id_Taxonomia = ti.Id_Incidente
                WHERE it.IncidenteID = ?
            """, incidente_id)
            
            taxonomias = cursor.fetchall()
            print(f"\n  Taxonomías ({len(taxonomias)}):")
            for tax in taxonomias:
                print(f"    - {tax.Id_Taxonomia}: {tax.Comentarios}")
                if tax.Area:
                    print(f"      Área: {tax.Area}, Categoría: {tax.Categoria_del_Incidente}")
            
            # Recuperar comentarios
            cursor.execute("""
                SELECT ComentarioID, Comentario, FechaCreacion, CreadoPor
                FROM COMENTARIOS_TAXONOMIA
                WHERE IncidenteID = ?
                ORDER BY FechaCreacion DESC
            """, incidente_id)
            
            comentarios = cursor.fetchall()
            print(f"\n  Comentarios ({len(comentarios)}):")
            for com in comentarios:
                print(f"    - {com.Comentario} (por {com.CreadoPor})")
                
        else:
            print("❌ No se pudo recuperar el incidente")
        
    except Exception as e:
        print(f"❌ Error recuperando incidente: {e}")
    finally:
        conn.close()

def main():
    """Función principal"""
    print("PRUEBA SIMPLE DEL MÓDULO DE INCIDENTES")
    print("="*60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Crear incidente
    incidente_id = test_crear_incidente_directo()
    
    # Recuperar incidente
    if incidente_id:
        test_recuperar_incidente(incidente_id)
    
    print("\n" + "="*60)
    print("PRUEBA COMPLETADA")
    print("="*60)

if __name__ == "__main__":
    main()
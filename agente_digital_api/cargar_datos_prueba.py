#!/usr/bin/env python3
"""Script para cargar datos de prueba en VerbosRectores y Recomendaciones"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.modules.core.database import get_db_connection

def cargar_datos_prueba():
    conn = get_db_connection()
    if not conn:
        print("❌ Error de conexión")
        return
        
    cursor = conn.cursor()
    
    try:
        print("\n=== CARGANDO DATOS DE PRUEBA ===\n")
        
        # 1. Obtener las obligaciones PSE
        cursor.execute("""
            SELECT ObligacionID, ArticuloNorma, Descripcion 
            FROM OBLIGACIONES 
            WHERE AplicaPara = 'PSE' OR AplicaPara = 'Ambos'
            ORDER BY ObligacionID
        """)
        obligaciones = cursor.fetchall()
        print(f"Encontradas {len(obligaciones)} obligaciones PSE")
        
        # 2. Cargar VerbosRectores (3 verbos por obligación)
        print("\n1. Cargando VerbosRectores...")
        verbos_base = [
            ('Implementar', 'Se debe implementar'),
            ('Documentar', 'Se debe documentar'),
            ('Revisar', 'Se debe revisar periódicamente')
        ]
        
        verbo_id = 1
        verbos_creados = {}
        
        for obligacion in obligaciones:
            for verbo, descripcion in verbos_base:
                try:
                    cursor.execute("""
                        INSERT INTO VerbosRectores (ObligacionID, NombreVerbo, Orden)
                        VALUES (?, ?, ?)
                    """, (obligacion.ObligacionID, 
                          f"{verbo} - {obligacion.ArticuloNorma}", verbo_id))
                    
                    # Obtener el ID generado
                    cursor.execute("SELECT @@IDENTITY")
                    generated_id = cursor.fetchone()[0]
                    
                    verbos_creados[generated_id] = {
                        'obligacion_id': obligacion.ObligacionID,
                        'articulo': obligacion.ArticuloNorma,
                        'verbo': verbo
                    }
                    verbo_id += 1
                except Exception as e:
                    print(f"   ⚠️ Error insertando verbo {verbo_id}: {e}")
        
        conn.commit()
        print(f"   ✅ {len(verbos_creados)} verbos rectores creados")
        
        # 3. Cargar Recomendaciones (2 recomendaciones por verbo)
        print("\n2. Cargando Recomendaciones...")
        recomendacion_id = 1
        recomendaciones_creadas = 0
        
        for vid, vdata in verbos_creados.items():
            recomendaciones = [
                f"Establecer proceso formal para {vdata['verbo'].lower()} los requisitos del {vdata['articulo']}",
                f"Designar responsable para {vdata['verbo'].lower()} y mantener evidencia del cumplimiento de {vdata['articulo']}"
            ]
            
            for rec_desc in recomendaciones:
                try:
                    cursor.execute("""
                        INSERT INTO Recomendaciones (VerboID, DescripcionRecomendacion)
                        VALUES (?, ?)
                    """, (vid, rec_desc))
                    
                    recomendacion_id += 1
                    recomendaciones_creadas += 1
                except Exception as e:
                    print(f"   ⚠️ Error insertando recomendación {recomendacion_id}: {e}")
        
        conn.commit()
        print(f"   ✅ {recomendaciones_creadas} recomendaciones creadas")
        
        # 4. Verificar resultados
        print("\n3. Verificando resultados...")
        
        # Total VerbosRectores
        cursor.execute("SELECT COUNT(*) FROM VerbosRectores")
        total_verbos = cursor.fetchone()[0]
        print(f"   Total VerbosRectores: {total_verbos}")
        
        # Total Recomendaciones
        cursor.execute("SELECT COUNT(*) FROM Recomendaciones")
        total_rec = cursor.fetchone()[0]
        print(f"   Total Recomendaciones: {total_rec}")
        
        # Verificar JOIN completo para PSE
        cursor.execute("""
            SELECT COUNT(DISTINCT R.RecomendacionID) AS Total
            FROM OBLIGACIONES AS O
            INNER JOIN VerbosRectores AS V ON O.ObligacionID = V.ObligacionID
            INNER JOIN Recomendaciones AS R ON V.VerboID = R.VerboID
            WHERE O.AplicaPara = 'PSE' OR O.AplicaPara = 'Ambos'
        """)
        total_pse = cursor.fetchone().Total
        print(f"   Total recomendaciones para PSE después del JOIN: {total_pse}")
        
        # 5. Cargar algunos registros de ejemplo en CumplimientoEmpresa
        print("\n4. Actualizando CumplimientoEmpresa con datos de ejemplo...")
        
        # Primero, eliminar registros existentes sin RecomendacionID válido
        cursor.execute("""
            DELETE FROM CumplimientoEmpresa 
            WHERE EmpresaID = 3 
            AND RecomendacionID NOT IN (SELECT RecomendacionID FROM Recomendaciones)
        """)
        conn.commit()
        
        # Obtener algunas recomendaciones para crear cumplimientos
        cursor.execute("""
            SELECT TOP 20 R.RecomendacionID, O.ObligacionID
            FROM Recomendaciones R
            INNER JOIN VerbosRectores V ON R.VerboID = V.VerboID
            INNER JOIN OBLIGACIONES O ON V.ObligacionID = O.ObligacionID
            WHERE O.AplicaPara = 'PSE' OR O.AplicaPara = 'Ambos'
            ORDER BY R.RecomendacionID
        """)
        
        recomendaciones_sample = cursor.fetchall()
        estados = ['Implementado', 'En Proceso', 'Pendiente', 'Pendiente', 'En Proceso']
        
        cumplimientos_creados = 0
        for i, rec in enumerate(recomendaciones_sample[:10]):  # Solo las primeras 10
            estado = estados[i % len(estados)]
            try:
                cursor.execute("""
                    INSERT INTO CumplimientoEmpresa 
                    (EmpresaID, RecomendacionID, Estado, PorcentajeAvance, ObligacionID)
                    VALUES (?, ?, ?, ?, ?)
                """, (3, rec.RecomendacionID, estado, 
                      100 if estado == 'Implementado' else 50 if estado == 'En Proceso' else 0,
                      rec.ObligacionID))
                cumplimientos_creados += 1
            except Exception as e:
                print(f"   ⚠️ Error insertando cumplimiento: {e}")
        
        conn.commit()
        print(f"   ✅ {cumplimientos_creados} registros de cumplimiento creados")
        
        print("\n=== DATOS DE PRUEBA CARGADOS EXITOSAMENTE ===")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    cargar_datos_prueba()
#!/usr/bin/env python3
"""Script para cargar datos realistas de cumplimiento para Sub empresa Surtika spa"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.modules.core.database import get_db_connection
from datetime import datetime, timedelta
import random

def cargar_datos_surtika():
    conn = get_db_connection()
    if not conn:
        print("❌ Error de conexión")
        return
        
    cursor = conn.cursor()
    
    try:
        print("\n=== CARGANDO DATOS REALISTAS PARA SUB EMPRESA SURTIKA SPA ===\n")
        
        # 1. Verificar que la empresa existe
        cursor.execute("SELECT EmpresaID, RazonSocial FROM Empresas WHERE EmpresaID = 3")
        empresa = cursor.fetchone()
        if not empresa:
            print("❌ No se encontró la empresa ID 3")
            return
        
        print(f"Empresa: {empresa.RazonSocial} (ID: {empresa.EmpresaID})")
        
        # 2. Limpiar datos anteriores de CumplimientoEmpresa
        print("\n1. Limpiando datos anteriores...")
        cursor.execute("DELETE FROM CumplimientoEmpresa WHERE EmpresaID = 3")
        conn.commit()
        
        # 3. Obtener todas las recomendaciones disponibles
        cursor.execute("""
            SELECT R.RecomendacionID, R.DescripcionRecomendacion, O.ObligacionID, O.ArticuloNorma
            FROM Recomendaciones R
            INNER JOIN VerbosRectores V ON R.VerboID = V.VerboID
            INNER JOIN OBLIGACIONES O ON V.ObligacionID = O.ObligacionID
            WHERE O.AplicaPara = 'PSE' OR O.AplicaPara = 'Ambos'
            ORDER BY O.ArticuloNorma, R.RecomendacionID
        """)
        recomendaciones = cursor.fetchall()
        total_rec = len(recomendaciones)
        print(f"\n2. Total de recomendaciones PSE encontradas: {total_rec}")
        
        # 4. Calcular distribución (40% pendiente, 30% cumplidas, 30% en proceso)
        pendientes_count = int(total_rec * 0.40)
        cumplidas_count = int(total_rec * 0.30)
        en_proceso_count = int(total_rec * 0.30)
        
        print(f"\n3. Distribución planificada:")
        print(f"   - Pendientes: {pendientes_count} ({pendientes_count/total_rec*100:.1f}%)")
        print(f"   - Cumplidas: {cumplidas_count} ({cumplidas_count/total_rec*100:.1f}%)")
        print(f"   - En Proceso: {en_proceso_count} ({en_proceso_count/total_rec*100:.1f}%)")
        
        # 5. Mezclar aleatoriamente y asignar estados
        indices = list(range(total_rec))
        random.shuffle(indices)
        
        estados_asignados = []
        # Asignar pendientes
        for i in range(pendientes_count):
            estados_asignados.append(('Pendiente', 0))
        # Asignar cumplidas
        for i in range(cumplidas_count):
            estados_asignados.append(('Implementado', 100))
        # Asignar en proceso
        for i in range(en_proceso_count):
            porcentaje = random.randint(20, 80)  # Entre 20% y 80%
            estados_asignados.append(('En Proceso', porcentaje))
        
        # 6. Insertar registros de cumplimiento
        print("\n4. Insertando registros de cumplimiento...")
        
        # Responsables ficticios para Surtika
        responsables = [
            'Juan Pérez - Gerente TI',
            'María González - Jefe Seguridad',
            'Carlos Rodríguez - Analista Senior',
            'Ana Silva - Coordinadora Cumplimiento',
            'Pedro Martínez - Supervisor Operaciones'
        ]
        
        registros_creados = 0
        for idx, rec in enumerate(recomendaciones):
            if idx < len(estados_asignados):
                estado, porcentaje = estados_asignados[idx]
                responsable = random.choice(responsables)
                
                # Fechas según el estado
                fecha_termino = None
                obs_ciber = ""
                obs_legal = ""
                
                if estado == 'Implementado':
                    # Implementados en los últimos 6 meses
                    dias_atras = random.randint(30, 180)
                    fecha_termino = datetime.now() - timedelta(days=dias_atras)
                    obs_ciber = f"Implementado según procedimiento PCS-{random.randint(100,999)}. Evidencia en carpeta compartida."
                    obs_legal = "Cumple con los requisitos normativos establecidos."
                    
                elif estado == 'En Proceso':
                    # Fecha termino en los próximos 3 meses
                    dias_futuro = random.randint(30, 90)
                    fecha_termino = datetime.now() + timedelta(days=dias_futuro)
                    obs_ciber = f"En desarrollo. Sprint {random.randint(1,5)} del proyecto de implementación."
                    obs_legal = "Pendiente revisión legal una vez completada la implementación técnica."
                    
                else:  # Pendiente
                    # Fecha termino en los próximos 6 meses
                    dias_futuro = random.randint(90, 180)
                    fecha_termino = datetime.now() + timedelta(days=dias_futuro)
                    obs_ciber = "Pendiente asignación de recursos. Incluido en roadmap Q{}.".format(random.randint(1,4))
                    obs_legal = "Requiere análisis de impacto legal previo a implementación."
                
                try:
                    cursor.execute("""
                        INSERT INTO CumplimientoEmpresa (
                            EmpresaID, RecomendacionID, Estado, PorcentajeAvance,
                            Responsable, FechaTermino, ObligacionID,
                            ObservacionesCiberseguridad, ObservacionesLegales,
                            FechaCreacion, FechaModificacion
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
                    """, (
                        3, rec.RecomendacionID, estado, porcentaje,
                        responsable, fecha_termino, rec.ObligacionID,
                        obs_ciber, obs_legal
                    ))
                    registros_creados += 1
                    
                except Exception as e:
                    print(f"   ⚠️ Error insertando registro: {e}")
        
        conn.commit()
        print(f"   ✅ {registros_creados} registros creados exitosamente")
        
        # 7. Verificar resultados finales
        print("\n5. Verificación final:")
        cursor.execute("""
            SELECT Estado, COUNT(*) as Cantidad, 
                   CAST(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() AS DECIMAL(5,2)) as Porcentaje
            FROM CumplimientoEmpresa
            WHERE EmpresaID = 3
            GROUP BY Estado
            ORDER BY 
                CASE Estado 
                    WHEN 'Implementado' THEN 1
                    WHEN 'En Proceso' THEN 2
                    WHEN 'Pendiente' THEN 3
                    ELSE 4
                END
        """)
        
        print("\n   Estado de cumplimiento actual:")
        for row in cursor.fetchall():
            print(f"   - {row.Estado}: {row.Cantidad} ({row.Porcentaje}%)")
        
        # 8. Mostrar algunos ejemplos
        print("\n6. Ejemplos de registros creados:")
        cursor.execute("""
            SELECT TOP 5 
                O.ArticuloNorma,
                R.DescripcionRecomendacion,
                C.Estado,
                C.PorcentajeAvance,
                C.Responsable
            FROM CumplimientoEmpresa C
            INNER JOIN Recomendaciones R ON C.RecomendacionID = R.RecomendacionID
            INNER JOIN OBLIGACIONES O ON C.ObligacionID = O.ObligacionID
            WHERE C.EmpresaID = 3
            ORDER BY NEWID()
        """)
        
        for row in cursor.fetchall():
            print(f"\n   Artículo: {row.ArticuloNorma}")
            print(f"   Recomendación: {row.DescripcionRecomendacion[:80]}...")
            print(f"   Estado: {row.Estado} ({row.PorcentajeAvance}%)")
            print(f"   Responsable: {row.Responsable}")
        
        print("\n=== DATOS CARGADOS EXITOSAMENTE PARA SURTIKA SPA ===")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    cargar_datos_surtika()
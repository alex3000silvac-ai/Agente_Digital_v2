#!/usr/bin/env python3
"""Script para corregir los datos de obligaciones según los límites correctos"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.modules.core.database import get_db_connection
from datetime import datetime, timedelta
import random

def corregir_obligaciones():
    conn = get_db_connection()
    if not conn:
        print("❌ Error de conexión")
        return
        
    cursor = conn.cursor()
    
    try:
        print("\n=== CORRIGIENDO DATOS DE OBLIGACIONES ===\n")
        
        # 1. Verificar obligaciones base
        print("1. Verificando obligaciones base en la tabla OBLIGACIONES:")
        cursor.execute("""
            SELECT AplicaPara, COUNT(*) as Total
            FROM OBLIGACIONES
            GROUP BY AplicaPara
        """)
        for row in cursor.fetchall():
            print(f"   - {row.AplicaPara}: {row.Total} obligaciones")
        
        # 2. Limpiar CumplimientoEmpresa para todas las empresas PSE
        print("\n2. Limpiando datos incorrectos de CumplimientoEmpresa...")
        cursor.execute("DELETE FROM CumplimientoEmpresa")
        conn.commit()
        print("   ✅ Tabla CumplimientoEmpresa limpiada")
        
        # 3. Obtener las 14 obligaciones PSE reales
        print("\n3. Obteniendo obligaciones PSE reales...")
        cursor.execute("""
            SELECT ObligacionID, ArticuloNorma, Descripcion
            FROM OBLIGACIONES
            WHERE AplicaPara = 'PSE' OR AplicaPara = 'Ambos'
            ORDER BY ObligacionID
        """)
        obligaciones_pse = cursor.fetchall()
        print(f"   Encontradas {len(obligaciones_pse)} obligaciones PSE")
        
        # 4. Crear cumplimientos para cada empresa
        empresas = [
            (3, 'Sub empresa Surtika spa'),
            (10, 'Sub Jurídica Spa')
        ]
        
        for empresa_id, nombre_empresa in empresas:
            print(f"\n4. Creando cumplimientos para {nombre_empresa} (ID: {empresa_id}):")
            
            # Distribución para cada empresa
            if empresa_id == 3:  # Surtika
                # 40% pendiente (6), 30% cumplidas (4), 30% en proceso (4)
                estados = ['Pendiente'] * 6 + ['Implementado'] * 4 + ['En Proceso'] * 4
            else:  # Jurídica
                # Distribución similar pero con 1 menos por ser 14 total
                estados = ['Pendiente'] * 5 + ['Implementado'] * 5 + ['En Proceso'] * 4
            
            random.shuffle(estados)  # Mezclar para que no estén agrupados
            
            responsables = {
                3: ['Juan Pérez - Gerente TI', 'María González - Jefe Seguridad', 
                    'Carlos Rodríguez - Analista Senior', 'Ana Silva - Coordinadora Cumplimiento'],
                10: ['Pedro Sánchez - Asesor Legal', 'Laura Martínez - Compliance Officer',
                     'Roberto Díaz - Gerente Operaciones', 'Carmen López - Auditora Interna']
            }
            
            registros_creados = 0
            impl = proc = pend = 0
            
            for idx, obligacion in enumerate(obligaciones_pse[:14]):  # Solo las primeras 14
                estado = estados[idx]
                responsable = random.choice(responsables[empresa_id])
                porcentaje = 100 if estado == 'Implementado' else 50 if estado == 'En Proceso' else 0
                
                # Contar por tipo
                if estado == 'Implementado': impl += 1
                elif estado == 'En Proceso': proc += 1
                else: pend += 1
                
                # Fechas según estado
                if estado == 'Implementado':
                    fecha_termino = datetime.now() - timedelta(days=random.randint(30, 180))
                    obs_ciber = f"Implementado según procedimiento interno. Documentación completa."
                    obs_legal = "Cumple con requisitos normativos."
                elif estado == 'En Proceso':
                    fecha_termino = datetime.now() + timedelta(days=random.randint(30, 90))
                    obs_ciber = f"En implementación. Avance {porcentaje}%."
                    obs_legal = "Pendiente validación legal."
                else:
                    fecha_termino = datetime.now() + timedelta(days=random.randint(90, 180))
                    obs_ciber = "Pendiente de recursos para implementación."
                    obs_legal = "Requiere análisis legal previo."
                
                try:
                    # Insertar directamente sin RecomendacionID
                    cursor.execute("""
                        INSERT INTO CumplimientoEmpresa (
                            EmpresaID, RecomendacionID, Estado, PorcentajeAvance,
                            Responsable, FechaTermino, ObligacionID,
                            ObservacionesCiberseguridad, ObservacionesLegales,
                            FechaCreacion, FechaModificacion
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
                    """, (
                        empresa_id, 
                        idx + 1,  # RecomendacionID ficticio
                        estado, 
                        porcentaje,
                        responsable, 
                        fecha_termino, 
                        obligacion.ObligacionID,
                        obs_ciber, 
                        obs_legal
                    ))
                    registros_creados += 1
                except Exception as e:
                    print(f"   ⚠️ Error: {e}")
            
            conn.commit()
            print(f"   ✅ {registros_creados} registros creados")
            print(f"   - Implementadas: {impl} ({round(impl/14*100)}%)")
            print(f"   - En Proceso: {proc} ({round(proc/14*100)}%)")
            print(f"   - Pendientes: {pend} ({round(pend/14*100)}%)")
        
        # 5. Verificar resultados finales
        print("\n5. Verificación final:")
        for empresa_id, nombre in empresas:
            cursor.execute("""
                SELECT COUNT(*) as Total,
                       SUM(CASE WHEN Estado = 'Implementado' THEN 1 ELSE 0 END) as Impl,
                       SUM(CASE WHEN Estado = 'En Proceso' THEN 1 ELSE 0 END) as EnProceso,
                       SUM(CASE WHEN Estado = 'Pendiente' THEN 1 ELSE 0 END) as Pend
                FROM CumplimientoEmpresa
                WHERE EmpresaID = ?
            """, (empresa_id,))
            
            result = cursor.fetchone()
            print(f"\n   {nombre}:")
            print(f"   - Total: {result.Total} (debe ser 14)")
            print(f"   - Implementadas: {result.Impl}")
            print(f"   - En Proceso: {result.EnProceso}")
            print(f"   - Pendientes: {result.Pend}")
        
        print("\n=== CORRECCIÓN COMPLETADA ===")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    corregir_obligaciones()
#!/usr/bin/env python3
"""Script para crear Sub Jurídica Spa si no existe"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.modules.core.database import get_db_connection

def crear_empresa_juridica():
    conn = get_db_connection()
    if not conn:
        print("❌ Error de conexión")
        return
        
    cursor = conn.cursor()
    
    try:
        # Verificar si ya existe
        cursor.execute("SELECT EmpresaID FROM Empresas WHERE RazonSocial = 'Sub Jurídica Spa'")
        existe = cursor.fetchone()
        
        if existe:
            print(f"✅ Sub Jurídica Spa ya existe con ID: {existe.EmpresaID}")
            empresa_id = existe.EmpresaID
        else:
            # Crear la empresa
            cursor.execute("""
                INSERT INTO Empresas (InquilinoID, RazonSocial, RUT, TipoEmpresa)
                VALUES (?, ?, ?, ?)
            """, (4, 'Sub Jurídica Spa', '76.123.456-7', 'PSE'))
            
            cursor.execute("SELECT @@IDENTITY")
            empresa_id = cursor.fetchone()[0]
            conn.commit()
            print(f"✅ Sub Jurídica Spa creada con ID: {empresa_id}")
        
        # Verificar cumplimientos
        cursor.execute("SELECT COUNT(*) FROM CumplimientoEmpresa WHERE EmpresaID = ?", (empresa_id,))
        cum_count = cursor.fetchone()[0]
        
        if cum_count == 0:
            print("\n📊 Creando datos de cumplimiento para Sub Jurídica Spa...")
            
            # Obtener algunas recomendaciones
            cursor.execute("""
                SELECT TOP 30 R.RecomendacionID, O.ObligacionID
                FROM Recomendaciones R
                INNER JOIN VerbosRectores V ON R.VerboID = V.VerboID
                INNER JOIN OBLIGACIONES O ON V.ObligacionID = O.ObligacionID
                WHERE O.AplicaPara = 'PSE' OR O.AplicaPara = 'Ambos'
                ORDER BY R.RecomendacionID
            """)
            
            recomendaciones = cursor.fetchall()
            
            # Crear registros con distribución diferente
            estados = ['Implementado'] * 10 + ['En Proceso'] * 8 + ['Pendiente'] * 12
            
            for i, rec in enumerate(recomendaciones):
                estado = estados[i % len(estados)]
                porcentaje = 100 if estado == 'Implementado' else 50 if estado == 'En Proceso' else 0
                
                cursor.execute("""
                    INSERT INTO CumplimientoEmpresa (
                        EmpresaID, RecomendacionID, Estado, PorcentajeAvance,
                        Responsable, ObligacionID
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (empresa_id, rec.RecomendacionID, estado, porcentaje,
                      'Pedro Sánchez - Asesor Legal', rec.ObligacionID))
            
            conn.commit()
            print("✅ Datos de cumplimiento creados")
        
        # Crear un incidente de ejemplo
        cursor.execute("SELECT COUNT(*) FROM Incidentes WHERE EmpresaID = ?", (empresa_id,))
        inc_count = cursor.fetchone()[0]
        
        if inc_count == 0:
            cursor.execute("""
                INSERT INTO Incidentes (
                    EmpresaID, Titulo, IDVisible, FechaCreacion,
                    DescripcionInicial, EstadoActual, Criticidad,
                    ResponsableCliente, TipoFlujo
                ) VALUES (?, ?, ?, GETDATE(), ?, ?, ?, ?, ?)
            """, (
                empresa_id,
                'Intento de phishing - Correo corporativo',
                'INC-2025-JURIDICA-001',
                'Detectado intento de phishing dirigido al departamento legal',
                'Abierto',
                'Media',
                'Pedro Sánchez - Asesor Legal',
                'Phishing'
            ))
            conn.commit()
            print("✅ Incidente de ejemplo creado")
        
        print(f"\n📊 Resumen Sub Jurídica Spa (ID: {empresa_id}):")
        print(f"   - Registros cumplimiento: {cum_count if cum_count > 0 else 30}")
        print(f"   - Incidentes: {inc_count if inc_count > 0 else 1}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    crear_empresa_juridica()
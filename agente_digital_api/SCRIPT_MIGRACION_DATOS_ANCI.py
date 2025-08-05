#!/usr/bin/env python3
"""
Script de migración para actualizar incidentes existentes con campos ANCI
Migra datos desde campos individuales de la BD al JSON estructurado
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db_connection
from app.modules.incidentes.unificador import UnificadorIncidentes
import json
from datetime import datetime
import traceback

def migrar_incidentes_anci():
    """
    Migra todos los incidentes ANCI existentes al nuevo formato
    """
    conn = None
    total_procesados = 0
    total_exitosos = 0
    total_errores = 0
    errores_detalle = []
    
    try:
        print("🚀 INICIANDO MIGRACIÓN DE INCIDENTES ANCI")
        print("=" * 50)
        
        conn = get_db_connection()
        if not conn:
            print("❌ Error: No se pudo conectar a la base de datos")
            return
        
        cursor = conn.cursor()
        
        # 1. Obtener todos los incidentes que son ANCI
        print("📋 Buscando incidentes ANCI...")
        cursor.execute("""
            SELECT 
                i.IncidenteID, i.Titulo, i.ReporteAnciID, i.DatosIncidente,
                e.TipoEmpresa, e.RazonSocial
            FROM Incidentes i
            LEFT JOIN Empresas e ON i.EmpresaID = e.EmpresaID
            WHERE i.ReporteAnciID IS NOT NULL
            ORDER BY i.IncidenteID
        """)
        
        incidentes = cursor.fetchall()
        total_incidentes = len(incidentes)
        
        if total_incidentes == 0:
            print("ℹ️ No se encontraron incidentes ANCI para migrar")
            return
        
        print(f"✅ Encontrados {total_incidentes} incidentes ANCI")
        print("")
        
        # 2. Procesar cada incidente
        for idx, (incidente_id, titulo, reporte_anci_id, datos_json_actual, tipo_empresa, razon_social) in enumerate(incidentes, 1):
            try:
                print(f"📌 [{idx}/{total_incidentes}] Procesando incidente {incidente_id}: {titulo[:50]}...")
                total_procesados += 1
                
                # Obtener todos los campos del incidente
                cursor.execute("SELECT * FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
                incidente_completo = cursor.fetchone()
                columns = [column[0] for column in cursor.description]
                datos_bd = dict(zip(columns, incidente_completo))
                
                # Verificar si ya tiene JSON válido
                estructura_json = None
                json_existente_valido = False
                
                if datos_json_actual:
                    try:
                        estructura_json = json.loads(datos_json_actual)
                        # Verificar versión
                        if estructura_json.get('metadata', {}).get('version_formato') == UnificadorIncidentes.VERSION_FORMATO:
                            json_existente_valido = True
                            print(f"   ✓ JSON existente válido (v{UnificadorIncidentes.VERSION_FORMATO})")
                    except:
                        estructura_json = None
                
                # Si no hay JSON válido, crear nueva estructura
                if not json_existente_valido:
                    print("   → Creando nueva estructura JSON...")
                    estructura_json = UnificadorIncidentes.crear_estructura_incidente()
                
                # Migrar campos ANCI desde la BD
                print("   → Migrando campos ANCI...")
                estructura_json = UnificadorIncidentes.migrar_campos_anci(estructura_json, datos_bd)
                
                # Validar campos obligatorios
                es_valido, campos_faltantes = UnificadorIncidentes.validar_campos_anci(estructura_json, 'alerta_temprana')
                
                if not es_valido:
                    print(f"   ⚠️ Faltan {len(campos_faltantes)} campos obligatorios:")
                    for campo in campos_faltantes[:3]:  # Mostrar solo los primeros 3
                        print(f"      - {campo}")
                    if len(campos_faltantes) > 3:
                        print(f"      ... y {len(campos_faltantes) - 3} más")
                
                # Preparar JSON para guardar
                estructura_final = UnificadorIncidentes.exportar_para_guardar(estructura_json)
                json_string = json.dumps(estructura_final, ensure_ascii=False)
                
                # Actualizar en la BD
                cursor.execute("""
                    UPDATE Incidentes 
                    SET DatosIncidente = ?,
                        FechaActualizacion = GETDATE(),
                        ModificadoPor = 'SCRIPT_MIGRACION'
                    WHERE IncidenteID = ?
                """, (json_string, incidente_id))
                
                # Registrar en auditoría
                cursor.execute("""
                    INSERT INTO INCIDENTES_AUDITORIA 
                    (IncidenteID, TipoAccion, DescripcionAccion, DatosNuevos, Usuario, FechaAccion)
                    VALUES (?, 'MIGRACION_ANCI', 'Migración automática de campos ANCI', ?, 'SCRIPT_MIGRACION', GETDATE())
                """, (
                    incidente_id,
                    json.dumps({
                        'version_anterior': 'sin_version' if not json_existente_valido else 'actualizado',
                        'version_nueva': UnificadorIncidentes.VERSION_FORMATO,
                        'campos_validos': es_valido,
                        'campos_faltantes': len(campos_faltantes) if not es_valido else 0
                    }, ensure_ascii=False)
                ))
                
                print(f"   ✅ Migrado exitosamente")
                total_exitosos += 1
                
            except Exception as e:
                total_errores += 1
                error_msg = f"Incidente {incidente_id}: {str(e)}"
                errores_detalle.append(error_msg)
                print(f"   ❌ Error: {str(e)}")
                traceback.print_exc()
                
                # Continuar con el siguiente incidente
                continue
        
        # 3. Confirmar cambios
        if total_exitosos > 0:
            print("\n🔄 Confirmando cambios en la base de datos...")
            conn.commit()
            print("✅ Cambios confirmados")
        
        # 4. Mostrar resumen
        print("\n" + "=" * 50)
        print("📊 RESUMEN DE LA MIGRACIÓN")
        print("=" * 50)
        print(f"Total incidentes procesados: {total_procesados}")
        print(f"✅ Migrados exitosamente: {total_exitosos}")
        print(f"❌ Con errores: {total_errores}")
        
        if errores_detalle:
            print("\n⚠️ DETALLE DE ERRORES:")
            for error in errores_detalle[:10]:  # Mostrar máximo 10 errores
                print(f"   - {error}")
            if len(errores_detalle) > 10:
                print(f"   ... y {len(errores_detalle) - 10} errores más")
        
        # 5. Verificación adicional
        if total_exitosos > 0:
            print("\n🔍 VERIFICACIÓN DE DATOS MIGRADOS")
            cursor.execute("""
                SELECT COUNT(*) 
                FROM Incidentes 
                WHERE ReporteAnciID IS NOT NULL 
                AND DatosIncidente IS NOT NULL
                AND DatosIncidente LIKE '%"version_formato":"2.0"%'
            """)
            total_con_json_v2 = cursor.fetchone()[0]
            print(f"✅ Incidentes ANCI con JSON v2.0: {total_con_json_v2}")
        
        print("\n✨ MIGRACIÓN COMPLETADA")
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO EN LA MIGRACIÓN: {str(e)}")
        traceback.print_exc()
        if conn:
            conn.rollback()
            print("🔙 Se revirtieron todos los cambios")
    
    finally:
        if conn:
            conn.close()
            print("\n🔒 Conexión cerrada")


def verificar_migracion():
    """
    Verifica el estado de la migración y muestra estadísticas
    """
    conn = None
    try:
        print("\n📊 VERIFICACIÓN DE ESTADO DE MIGRACIÓN ANCI")
        print("=" * 50)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total de incidentes ANCI
        cursor.execute("SELECT COUNT(*) FROM Incidentes WHERE ReporteAnciID IS NOT NULL")
        total_anci = cursor.fetchone()[0]
        print(f"Total incidentes ANCI: {total_anci}")
        
        # Con JSON válido
        cursor.execute("""
            SELECT COUNT(*) 
            FROM Incidentes 
            WHERE ReporteAnciID IS NOT NULL 
            AND DatosIncidente IS NOT NULL
            AND DatosIncidente LIKE '%"version_formato":"2.0"%'
        """)
        con_json_v2 = cursor.fetchone()[0]
        print(f"Con JSON v2.0: {con_json_v2}")
        
        # Sin JSON o con versión antigua
        sin_json = total_anci - con_json_v2
        print(f"Sin JSON válido: {sin_json}")
        
        if sin_json > 0:
            print(f"\n⚠️ Hay {sin_json} incidentes ANCI que necesitan migración")
        else:
            print("\n✅ Todos los incidentes ANCI están migrados correctamente")
        
        # Mostrar algunos ejemplos
        print("\n📋 Ejemplos de incidentes ANCI:")
        cursor.execute("""
            SELECT TOP 5
                IncidenteID, Titulo, ReporteAnciID,
                CASE 
                    WHEN DatosIncidente LIKE '%"version_formato":"2.0"%' THEN 'Migrado v2.0'
                    WHEN DatosIncidente IS NOT NULL THEN 'JSON antiguo'
                    ELSE 'Sin JSON'
                END as EstadoJSON
            FROM Incidentes
            WHERE ReporteAnciID IS NOT NULL
            ORDER BY IncidenteID DESC
        """)
        
        for row in cursor.fetchall():
            print(f"   - ID {row[0]}: {row[1][:40]}... [{row[3]}]")
        
    except Exception as e:
        print(f"❌ Error en verificación: {str(e)}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "verificar":
        verificar_migracion()
    else:
        print("Este script migrará todos los incidentes ANCI al nuevo formato JSON v2.0")
        print("Esto actualizará el campo DatosIncidente con la estructura completa.")
        print("")
        respuesta = input("¿Desea continuar? (s/n): ")
        
        if respuesta.lower() == 's':
            migrar_incidentes_anci()
        else:
            print("Migración cancelada")
            print("\nPuede ejecutar 'python SCRIPT_MIGRACION_DATOS_ANCI.py verificar' para ver el estado actual")
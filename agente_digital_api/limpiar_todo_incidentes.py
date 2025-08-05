#!/usr/bin/env python3
"""
Script para limpiar TODOS los incidentes y archivos del sistema
ADVERTENCIA: Este script eliminará PERMANENTEMENTE todos los datos
"""

import sys
import os
import shutil
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db_connection

def limpiar_sistema_completo():
    """Elimina todos los incidentes y archivos del sistema"""
    
    print("⚠️  ADVERTENCIA: LIMPIEZA TOTAL DEL SISTEMA")
    print("=" * 60)
    print("Este script eliminará PERMANENTEMENTE:")
    print("- TODOS los incidentes de la base de datos")
    print("- TODAS las evidencias y archivos")
    print("- TODAS las carpetas de archivos")
    print("- TODOS los comentarios y datos relacionados")
    print("=" * 60)
    
    respuesta = input("\n¿Está ABSOLUTAMENTE SEGURO? Escriba 'SI ELIMINAR TODO' para continuar: ")
    
    if respuesta != "SI ELIMINAR TODO":
        print("❌ Operación cancelada")
        return
    
    # Confirmación adicional
    respuesta2 = input("\n¿Segunda confirmación? Escriba 'CONFIRMO' para proceder: ")
    if respuesta2 != "CONFIRMO":
        print("❌ Operación cancelada")
        return
    
    print("\n🗑️ INICIANDO LIMPIEZA TOTAL...")
    
    conn = None
    estadisticas = {
        'incidentes': 0,
        'evidencias': 0,
        'archivos_fisicos': 0,
        'carpetas': 0,
        'taxonomias': 0,
        'comentarios': 0
    }
    
    try:
        # PASO 1: OBTENER RUTAS DE ARCHIVOS ANTES DE ELIMINAR
        print("\n1️⃣ Obteniendo rutas de archivos...")
        conn = get_db_connection()
        if not conn:
            print("❌ Error de conexión a BD")
            return
            
        cursor = conn.cursor()
        
        # Obtener todas las rutas de archivos
        rutas_archivos = []
        
        # Evidencias de incidentes
        cursor.execute("SELECT DISTINCT RutaArchivo FROM EvidenciasIncidentes WHERE RutaArchivo IS NOT NULL")
        rutas_archivos.extend([row[0] for row in cursor.fetchall()])
        
        # Evidencias de taxonomías
        cursor.execute("SELECT DISTINCT RutaArchivo FROM EVIDENCIAS_TAXONOMIA WHERE RutaArchivo IS NOT NULL")
        rutas_archivos.extend([row[0] for row in cursor.fetchall()])
        
        # Si existe la nueva tabla de archivos
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'INCIDENTES_ARCHIVOS'
        """)
        if cursor.fetchone()[0] > 0:
            cursor.execute("SELECT DISTINCT RutaArchivo FROM INCIDENTES_ARCHIVOS WHERE RutaArchivo IS NOT NULL")
            rutas_archivos.extend([row[0] for row in cursor.fetchall()])
        
        print(f"   ✅ Encontradas {len(rutas_archivos)} rutas de archivos")
        
        # PASO 2: CONTAR REGISTROS ANTES DE ELIMINAR
        print("\n2️⃣ Contando registros a eliminar...")
        
        # Contar incidentes
        cursor.execute("SELECT COUNT(*) FROM Incidentes")
        estadisticas['incidentes'] = cursor.fetchone()[0]
        
        # Contar evidencias
        cursor.execute("SELECT COUNT(*) FROM EvidenciasIncidentes")
        estadisticas['evidencias'] = cursor.fetchone()[0]
        
        # Contar taxonomías
        cursor.execute("SELECT COUNT(*) FROM INCIDENTE_TAXONOMIA")
        estadisticas['taxonomias'] = cursor.fetchone()[0]
        
        # Contar comentarios
        cursor.execute("SELECT COUNT(*) FROM COMENTARIOS_TAXONOMIA")
        estadisticas['comentarios'] = cursor.fetchone()[0]
        
        print(f"   📊 Incidentes: {estadisticas['incidentes']}")
        print(f"   📊 Evidencias: {estadisticas['evidencias']}")
        print(f"   📊 Taxonomías: {estadisticas['taxonomias']}")
        print(f"   📊 Comentarios: {estadisticas['comentarios']}")
        
        # PASO 3: ELIMINAR DE LA BASE DE DATOS
        print("\n3️⃣ Eliminando registros de la base de datos...")
        
        # Orden de eliminación respetando foreign keys
        tablas_eliminar = [
            # Nuevas tablas del sistema dinámico (si existen)
            ('INCIDENTES_ARCHIVOS', 'IncidenteID'),
            ('INCIDENTES_COMENTARIOS', 'IncidenteID'),
            ('INCIDENTES_SECCIONES_DATOS', 'IncidenteID'),
            ('INCIDENTES_AUDITORIA', 'IncidenteID'),
            
            # Tablas existentes
            ('COMENTARIOS_TAXONOMIA', 'IncidenteID'),
            ('EVIDENCIAS_TAXONOMIA', 'IncidenteID'),
            ('INCIDENTE_TAXONOMIA', 'IncidenteID'),
            ('EvidenciasIncidentes', 'IncidenteID'),
            ('HistorialIncidentes', 'IncidenteID'),
            ('Incidentes', None)  # Tabla principal al final
        ]
        
        for tabla, columna in tablas_eliminar:
            try:
                # Verificar si la tabla existe
                cursor.execute(f"""
                    SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = '{tabla}'
                """)
                
                if cursor.fetchone()[0] > 0:
                    # Contar registros antes
                    cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                    count_antes = cursor.fetchone()[0]
                    
                    if count_antes > 0:
                        # Eliminar todos los registros
                        cursor.execute(f"DELETE FROM {tabla}")
                        print(f"   ✅ {tabla}: {count_antes} registros eliminados")
                    else:
                        print(f"   ⚪ {tabla}: Sin registros")
                else:
                    print(f"   ⚪ {tabla}: No existe")
                    
            except Exception as e:
                print(f"   ⚠️ Error en {tabla}: {e}")
        
        # Confirmar cambios en BD
        conn.commit()
        print("   ✅ Base de datos limpiada")
        
        # PASO 4: ELIMINAR ARCHIVOS FÍSICOS
        print("\n4️⃣ Eliminando archivos físicos...")
        
        for ruta in rutas_archivos:
            try:
                if os.path.exists(ruta):
                    os.remove(ruta)
                    estadisticas['archivos_fisicos'] += 1
                    print(f"   🗑️ Eliminado: {os.path.basename(ruta)}")
            except Exception as e:
                print(f"   ⚠️ Error eliminando {ruta}: {e}")
        
        # PASO 5: ELIMINAR CARPETAS DE ARCHIVOS
        print("\n5️⃣ Eliminando estructura de carpetas...")
        
        # Rutas base donde se guardan archivos
        rutas_base = [
            '/archivos',
            'C:/archivos',
            'C:/Archivos',
            './archivos',
            '../archivos',
            os.environ.get('ARCHIVOS_PATH', '/archivos')
        ]
        
        for ruta_base in rutas_base:
            if os.path.exists(ruta_base):
                print(f"   📁 Procesando: {ruta_base}")
                
                # Listar carpetas de empresas
                try:
                    for item in os.listdir(ruta_base):
                        if item.startswith('empresa_'):
                            carpeta_empresa = os.path.join(ruta_base, item)
                            if os.path.isdir(carpeta_empresa):
                                # Eliminar toda la carpeta de la empresa
                                shutil.rmtree(carpeta_empresa)
                                estadisticas['carpetas'] += 1
                                print(f"   🗑️ Eliminada carpeta: {item}")
                except Exception as e:
                    print(f"   ⚠️ Error procesando {ruta_base}: {e}")
        
        # PASO 6: RESETEAR SECUENCIAS/IDENTITY (SQL Server)
        print("\n6️⃣ Reseteando contadores de identidad...")
        
        tablas_resetear = [
            'Incidentes',
            'EvidenciasIncidentes',
            'INCIDENTE_TAXONOMIA',
            'COMENTARIOS_TAXONOMIA',
            'EVIDENCIAS_TAXONOMIA'
        ]
        
        for tabla in tablas_resetear:
            try:
                cursor.execute(f"""
                    IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{tabla}')
                    BEGIN
                        DBCC CHECKIDENT ('{tabla}', RESEED, 0)
                    END
                """)
                print(f"   ✅ Contador reseteado: {tabla}")
            except Exception as e:
                print(f"   ⚠️ Error reseteando {tabla}: {e}")
        
        conn.commit()
        
        # MOSTRAR RESUMEN
        print("\n" + "=" * 60)
        print("✅ LIMPIEZA COMPLETADA")
        print("=" * 60)
        print(f"📊 Incidentes eliminados: {estadisticas['incidentes']}")
        print(f"📊 Evidencias eliminadas: {estadisticas['evidencias']}")
        print(f"📊 Archivos físicos eliminados: {estadisticas['archivos_fisicos']}")
        print(f"📊 Carpetas eliminadas: {estadisticas['carpetas']}")
        print(f"📊 Taxonomías eliminadas: {estadisticas['taxonomias']}")
        print(f"📊 Comentarios eliminados: {estadisticas['comentarios']}")
        
        # Crear log de la operación
        log_file = f"limpieza_total_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        with open(log_file, 'w') as f:
            f.write(f"LIMPIEZA TOTAL DEL SISTEMA\n")
            f.write(f"Fecha: {datetime.now()}\n")
            f.write(f"Incidentes: {estadisticas['incidentes']}\n")
            f.write(f"Evidencias: {estadisticas['evidencias']}\n")
            f.write(f"Archivos: {estadisticas['archivos_fisicos']}\n")
            f.write(f"Carpetas: {estadisticas['carpetas']}\n")
        
        print(f"\n📄 Log guardado en: {log_file}")
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
            
    finally:
        if conn:
            conn.close()
        
        print("\n🏁 Proceso finalizado")


if __name__ == "__main__":
    print("\n🧹 SCRIPT DE LIMPIEZA TOTAL DEL SISTEMA")
    print("=" * 60)
    print("⚠️  ADVERTENCIA: Este script es DESTRUCTIVO")
    print("⚠️  No hay forma de deshacer esta operación")
    print("=" * 60)
    
    limpiar_sistema_completo()
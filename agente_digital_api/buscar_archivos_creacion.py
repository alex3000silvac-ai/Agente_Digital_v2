#!/usr/bin/env python3
"""
Buscar TODOS los archivos relacionados con el incidente 25
incluyendo archivos inactivos o históricos
"""

def buscar_todos_archivos():
    """Buscar archivos en todas las tablas posibles"""
    try:
        print("🔍 BÚSQUEDA EXHAUSTIVA DE ARCHIVOS - INCIDENTE 25")
        print("=" * 80)
        
        from app.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. INCIDENTES_ARCHIVOS (incluyendo inactivos)
        print("\n1️⃣ TABLA INCIDENTES_ARCHIVOS (TODOS, incluyendo inactivos):")
        cursor.execute("""
            SELECT 
                ArchivoID,
                SeccionID,
                NombreOriginal,
                NombreServidor,
                RutaArchivo,
                TamanoKB,
                FechaSubida,
                Activo
            FROM INCIDENTES_ARCHIVOS
            WHERE IncidenteID = 25
            ORDER BY ArchivoID DESC
        """)
        
        archivos_incidente = cursor.fetchall()
        
        if archivos_incidente:
            print(f"\n   ✅ Encontrados {len(archivos_incidente)} archivos (activos e inactivos):")
            for archivo in archivos_incidente:
                estado = "ACTIVO" if archivo[7] else "INACTIVO/ELIMINADO"
                print(f"\n   📄 ARCHIVO ID: {archivo[0]} - {estado}")
                print(f"      Sección: {archivo[1]}")
                print(f"      Nombre Original: {archivo[2]}")
                print(f"      Nombre Servidor: {archivo[3]}")
                print(f"      Ruta: {archivo[4]}")
                print(f"      Tamaño: {archivo[5]} KB")
                print(f"      Fecha Subida: {archivo[6]}")
                if not archivo[7]:
                    print(f"      ❌ Estado: INACTIVO/ELIMINADO")
        else:
            print("\n   ❌ NO HAY ARCHIVOS en INCIDENTES_ARCHIVOS")
        
        # 2. EVIDENCIAS_TAXONOMIA
        print("\n2️⃣ TABLA EVIDENCIAS_TAXONOMIA:")
        cursor.execute("""
            SELECT 
                EvidenciaID,
                TaxonomiaID,
                NombreArchivo,
                NombreArchivoOriginal,
                RutaArchivo,
                TamanoArchivo,
                FechaSubida,
                SubidoPor,
                Activo
            FROM EVIDENCIAS_TAXONOMIA
            WHERE IncidenteID = 25
            ORDER BY FechaSubida DESC
        """)
        
        archivos_taxonomia = cursor.fetchall()
        
        if archivos_taxonomia:
            print(f"\n   ✅ Encontrados {len(archivos_taxonomia)} archivos:")
            for archivo in archivos_taxonomia:
                estado = "ACTIVO" if archivo[8] else "INACTIVO"
                print(f"\n   📄 EVIDENCIA ID: {archivo[0]} - {estado}")
                print(f"      Taxonomía: {archivo[1]}")
                print(f"      Nombre: {archivo[2]}")
                print(f"      Nombre Original: {archivo[3]}")
                print(f"      Ruta: {archivo[4]}")
                print(f"      Tamaño: {archivo[5]} bytes")
                print(f"      Fecha: {archivo[6]}")
                print(f"      Subido Por: {archivo[7]}")
        else:
            print("\n   ❌ NO HAY ARCHIVOS en EVIDENCIAS_TAXONOMIA")
        
        # 3. Verificar el proceso de creación
        print("\n3️⃣ VERIFICANDO PROCESO DE CREACIÓN:")
        
        # Buscar en logs o auditoría
        cursor.execute("""
            SELECT TOP 10
                TipoAccion,
                DescripcionAccion,
                DatosNuevos,
                Usuario,
                FechaAccion
            FROM INCIDENTES_AUDITORIA
            WHERE IncidenteID = 25
            ORDER BY FechaAccion ASC
        """)
        
        auditorias = cursor.fetchall()
        
        if auditorias:
            print(f"\n   📋 Historial de auditoría:")
            for audit in auditorias:
                print(f"\n   - {audit[4]}: {audit[0]} - {audit[1]}")
                if audit[2]:
                    print(f"     Datos: {audit[2][:100]}...")
        
        # 4. Verificar archivos físicos en el sistema
        print("\n4️⃣ VERIFICANDO SISTEMA DE ARCHIVOS:")
        import os
        
        # Rutas posibles donde podrían estar los archivos
        rutas_verificar = [
            '/uploads/incidentes/25/',
            'uploads/incidentes/25/',
            './uploads/incidentes/25/',
            '../uploads/incidentes/25/',
        ]
        
        for ruta in rutas_verificar:
            if os.path.exists(ruta):
                archivos = os.listdir(ruta)
                if archivos:
                    print(f"\n   ✅ Archivos encontrados en {ruta}:")
                    for archivo in archivos:
                        print(f"      - {archivo}")
                else:
                    print(f"\n   📁 Directorio {ruta} existe pero está vacío")
            else:
                print(f"\n   ❌ Directorio {ruta} no existe")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    buscar_todos_archivos()
#!/usr/bin/env python3
"""
Script para verificar la estructura de la tabla Incidentes y comparar 
campos utilizados en INSERT vs SELECT queries
"""

import pyodbc
import sys
import os

# Agregar el directorio actual al path para importar database
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db_connection

def verificar_estructura_incidentes():
    """Verifica la estructura actual de la tabla Incidentes"""
    print("=" * 60)
    print("VERIFICANDO ESTRUCTURA DE LA TABLA INCIDENTES")
    print("=" * 60)
    
    conn = get_db_connection()
    if not conn:
        print("❌ Error: No se pudo conectar a la base de datos")
        return None
    
    try:
        cursor = conn.cursor()
        
        # Obtener estructura de la tabla
        cursor.execute("""
            SELECT 
                COLUMN_NAME, 
                DATA_TYPE, 
                IS_NULLABLE,
                CHARACTER_MAXIMUM_LENGTH,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'Incidentes'
            ORDER BY ORDINAL_POSITION
        """)
        
        columnas = cursor.fetchall()
        
        if not columnas:
            print("❌ Error: La tabla Incidentes no existe o no tiene columnas")
            return None
        
        print(f"✅ Tabla Incidentes encontrada con {len(columnas)} columnas:")
        print("")
        
        campos_disponibles = []
        for col in columnas:
            nombre = col[0]
            tipo = col[1]
            nullable = col[2]
            longitud = col[3] if col[3] else ""
            default = col[4] if col[4] else ""
            
            campos_disponibles.append(nombre)
            print(f"  📋 {nombre:<25} | {tipo:<15} | {'NULL' if nullable == 'YES' else 'NOT NULL':<8} | {str(longitud):<10} | {default}")
        
        print("")
        return campos_disponibles
        
    except Exception as e:
        print(f"❌ Error verificando estructura: {e}")
        return None
    finally:
        conn.close()

def analizar_mapeo_campos():
    """Analiza el mapeo de campos definido en admin_views.py"""
    print("=" * 60)
    print("ANALIZANDO MAPEO DE CAMPOS")
    print("=" * 60)
    
    # Mapeo según admin_views.py
    mapeo_campos = {
        'EstadoActual': 'Estado',
        'Criticidad': 'Severidad',
        'TipoFlujo': 'TipoIncidente',
        'DescripcionInicial': 'Descripcion',
        'IncidenteID': 'IncidenteID',
        'Titulo': 'Titulo',
        'IDVisible': 'IDVisible',
        'FechaCreacion': 'FechaCreacion',
        'FechaDeteccion': 'FechaDeteccion',
        'FechaCierre': 'FechaCierre',
        'CreadoPor': 'CreadoPor',
        'ResponsableCliente': 'ResponsableCliente',
        'SistemasAfectados': 'SistemasAfectados',
        'OrigenIncidente': 'OrigenIncidente',
        'AccionesInmediatas': 'AccionesInmediatas',
        'EmpresaID': 'EmpresaID',
        'TipoEmpresa': 'TipoEmpresa',
        'EmpresaAfectada': 'EmpresaAfectada'
    }
    
    print("📝 Mapeo de campos definido en MAPEO_CAMPOS_INCIDENTES:")
    print("")
    for campo_bd, campo_frontend in mapeo_campos.items():
        print(f"  🔄 {campo_bd:<25} → {campo_frontend}")
    
    print("")
    return mapeo_campos

def analizar_campos_insert():
    """Analiza los campos utilizados en queries INSERT"""
    print("=" * 60)
    print("ANALIZANDO CAMPOS EN INSERT QUERIES")
    print("=" * 60)
    
    # Según la línea 5141-5142 en admin_views.py
    campos_insert = [
        'EmpresaID',
        'Titulo', 
        'DescripcionInicial',
        'EstadoActual',
        'Criticidad',
        'FechaCreacion',  # Se genera con GETDATE()
        'CreadoPor',
        'TipoFlujo',
        'FechaDeteccion',
        'FechaOcurrencia'
    ]
    
    print("📝 Campos utilizados en INSERT INTO Incidentes:")
    print("")
    for campo in campos_insert:
        print(f"  ✏️  {campo}")
    
    print("")
    return campos_insert

def analizar_campos_update():
    """Analiza los campos utilizados en queries UPDATE"""
    print("=" * 60)
    print("ANALIZANDO CAMPOS EN UPDATE QUERIES")
    print("=" * 60)
    
    # Según mapeo_campos_completo en líneas 4639-4668
    campos_update = [
        'Titulo',
        'DescripcionInicial',
        'EstadoActual',
        'Criticidad',
        'TipoFlujo',
        'ResponsableCliente',
        'SistemasAfectados',
        'OrigenIncidente',
        'AccionesInmediatas',
        'FechaDeteccion',
        'FechaCierre',
        'ObservacionesAdicionales',
        'FechaActualizacion'  # Se genera con GETDATE()
    ]
    
    print("📝 Campos utilizados en UPDATE Incidentes:")
    print("")
    for campo in campos_update:
        print(f"  ✏️  {campo}")
    
    print("")
    return campos_update

def comparar_campos(campos_bd, mapeo_campos, campos_insert, campos_update):
    """Compara los campos disponibles con los utilizados"""
    print("=" * 60)
    print("COMPARACIÓN DE CAMPOS")
    print("=" * 60)
    
    print("🔍 ANÁLISIS DE CAMPOS FALTANTES EN SELECT:")
    print("")
    
    # Campos que se insertan pero no están en el mapeo para SELECT
    campos_mapeo = set(mapeo_campos.keys())
    campos_insert_set = set(campos_insert)
    campos_update_set = set(campos_update)
    campos_bd_set = set(campos_bd)
    
    print("1. Campos que se insertan pero NO están en el mapeo SELECT:")
    insert_no_mapeo = campos_insert_set - campos_mapeo
    for campo in sorted(insert_no_mapeo):
        if campo in campos_bd_set:
            print(f"   ❌ {campo} - EXISTE en BD pero NO en mapeo SELECT")
        else:
            print(f"   ⚠️  {campo} - NO EXISTE en BD")
    
    print("")
    print("2. Campos que se actualizan pero NO están en el mapeo SELECT:")
    update_no_mapeo = campos_update_set - campos_mapeo
    for campo in sorted(update_no_mapeo):
        if campo in campos_bd_set:
            print(f"   ❌ {campo} - EXISTE en BD pero NO en mapeo SELECT")
        else:
            print(f"   ⚠️  {campo} - NO EXISTE en BD")
    
    print("")
    print("3. Campos en mapeo SELECT que NO existen en BD:")
    mapeo_no_bd = campos_mapeo - campos_bd_set
    for campo in sorted(mapeo_no_bd):
        print(f"   ❌ {campo} - En mapeo pero NO EXISTE en BD")
    
    print("")
    print("4. Campos importantes que podrían faltar:")
    campos_importantes = [
        'ResponsableCliente',
        'SistemasAfectados', 
        'OrigenIncidente',
        'AccionesInmediatas',
        'FechaOcurrencia',
        'ObservacionesAdicionales',
        'FechaActualizacion'
    ]
    
    for campo in campos_importantes:
        if campo in campos_bd_set:
            if campo not in campos_mapeo:
                print(f"   ⚠️  {campo} - EXISTE en BD pero NO en mapeo SELECT")
            else:
                print(f"   ✅ {campo} - EXISTE en BD y EN mapeo SELECT")
        else:
            print(f"   ❌ {campo} - NO EXISTE en BD")

def generar_correcciones():
    """Genera las correcciones sugeridas"""
    print("=" * 60)
    print("CORRECCIONES SUGERIDAS")
    print("=" * 60)
    
    print("📝 Para corregir las consultas SELECT, actualizar MAPEO_CAMPOS_INCIDENTES:")
    print("")
    
    mapeo_corregido = {
        'EstadoActual': 'Estado',
        'Criticidad': 'Severidad',
        'TipoFlujo': 'TipoIncidente',
        'DescripcionInicial': 'Descripcion',
        'IncidenteID': 'IncidenteID',
        'Titulo': 'Titulo',
        'IDVisible': 'IDVisible',
        'FechaCreacion': 'FechaCreacion',
        'FechaDeteccion': 'FechaDeteccion',
        'FechaCierre': 'FechaCierre',
        'FechaOcurrencia': 'FechaOcurrencia',  # AGREGADO
        'CreadoPor': 'CreadoPor',
        'ResponsableCliente': 'ResponsableCliente',  # AGREGADO
        'SistemasAfectados': 'SistemasAfectados',  # AGREGADO
        'OrigenIncidente': 'OrigenIncidente',  # AGREGADO
        'AccionesInmediatas': 'AccionesInmediatas',  # AGREGADO
        'ObservacionesAdicionales': 'ObservacionesAdicionales',  # AGREGADO
        'FechaActualizacion': 'FechaActualizacion',  # AGREGADO
        'EmpresaID': 'EmpresaID',
        'InquilinoID': 'InquilinoID',  # AGREGADO si existe
        'TipoEmpresa': 'TipoEmpresa',
        'EmpresaAfectada': 'EmpresaAfectada'
    }
    
    print("MAPEO_CAMPOS_INCIDENTES = {")
    for campo_bd, campo_frontend in mapeo_corregido.items():
        print(f"    '{campo_bd}': '{campo_frontend}',")
    print("}")
    
    print("")
    print("📝 Verificar también que las consultas SELECT incluyan todos los campos necesarios")
    print("📝 Los campos OrigenIncidente, SistemasAfectados, AccionesInmediatas y ResponsableCliente")
    print("   son especialmente importantes para el funcionamiento del frontend")

def main():
    """Función principal"""
    print("🔍 VERIFICACIÓN DE CONSULTAS SQL DE INCIDENTES")
    print("=" * 60)
    
    # 1. Verificar estructura de BD
    campos_bd = verificar_estructura_incidentes()
    if not campos_bd:
        return
    
    # 2. Analizar mapeo actual
    mapeo_campos = analizar_mapeo_campos()
    
    # 3. Analizar campos INSERT
    campos_insert = analizar_campos_insert()
    
    # 4. Analizar campos UPDATE
    campos_update = analizar_campos_update()
    
    # 5. Comparar campos
    comparar_campos(campos_bd, mapeo_campos, campos_insert, campos_update)
    
    # 6. Generar correcciones
    generar_correcciones()
    
    print("")
    print("=" * 60)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    main()
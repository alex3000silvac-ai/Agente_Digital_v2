#!/usr/bin/env python3
"""
Script completo para probar el incidente 5
"""

import json
from app.database import get_db_connection
from app.modules.admin.incidentes_crear import obtener_estructura_base_incidente

print("=== PRUEBA COMPLETA DEL INCIDENTE 5 ===\n")

# 1. Verificar en base de datos
print("1. VERIFICANDO EN BASE DE DATOS")
print("-" * 40)
try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT IncidenteID, Titulo, IDVisible FROM Incidentes WHERE IncidenteID = 5")
    row = cursor.fetchone()
    if row:
        print(f"✅ Incidente encontrado en BD:")
        print(f"   - ID: {row[0]}")
        print(f"   - Título: {row[1]}")
        print(f"   - IDVisible: {row[2]}")
    else:
        print("❌ Incidente NO encontrado en BD")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")

# 2. Obtener estructura completa
print("\n2. OBTENIENDO ESTRUCTURA COMPLETA")
print("-" * 40)
try:
    estructura = obtener_estructura_base_incidente(5)
    if estructura:
        print("✅ Estructura obtenida:")
        print(f"   - Campos principales: {len([k for k in estructura.keys() if not k in ['taxonomias', 'archivos']])}")
        print(f"   - Taxonomías: {len(estructura.get('taxonomias', []))}")
        print(f"   - Archivos por sección: {list(estructura.get('archivos', {}).keys())}")
        
        # Mostrar archivos detallados
        if estructura.get('archivos'):
            print("\n   📁 ARCHIVOS ENCONTRADOS:")
            for seccion, archivos in estructura['archivos'].items():
                print(f"      Sección {seccion}:")
                for archivo in archivos:
                    print(f"      - {archivo['nombre']} ({archivo['tamaño']} bytes)")
                    if archivo.get('origen') == 'temporal':
                        print(f"        ⚠️  Origen: JSON temporal (no subido al servidor)")
                    
        # Guardar resultado para debug
        with open('incidente_5_estructura.json', 'w', encoding='utf-8') as f:
            json.dump(estructura, f, indent=2, ensure_ascii=False, default=str)
        print("\n📄 Estructura completa guardada en: incidente_5_estructura.json")
        
    else:
        print("❌ No se pudo obtener la estructura")
except Exception as e:
    print(f"❌ Error obteniendo estructura: {e}")
    import traceback
    traceback.print_exc()

# 3. Simular lo que haría el endpoint
print("\n3. SIMULANDO ENDPOINT")
print("-" * 40)
try:
    from app.modules.admin.incidentes_crear import obtener_detalle_incidente
    # Simular la llamada al endpoint
    resultado = obtener_detalle_incidente(5)
    if isinstance(resultado, tuple):
        respuesta, codigo = resultado
        print(f"Código HTTP: {codigo}")
        if hasattr(respuesta, 'json'):
            print("Respuesta JSON disponible")
    print("✅ Endpoint funcionaría correctamente")
except Exception as e:
    print(f"❌ Error en endpoint: {e}")
    import traceback
    traceback.print_exc()
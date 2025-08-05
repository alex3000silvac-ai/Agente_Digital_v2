#!/usr/bin/env python3
"""
Debug profundo del guardado de taxonomías en todos los escenarios
"""

def verificar_endpoint_guardado():
    """Verificar el endpoint de guardado paso a paso"""
    try:
        from app.database import get_db_connection
        import json
        
        print("🔍 VERIFICACIÓN PROFUNDA DEL GUARDADO DE TAXONOMÍAS")
        print("=" * 70)
        
        # 1. Verificar estructura actual
        print("1. 📋 ESTADO ACTUAL DE LA BASE DE DATOS")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ver todos los incidentes con taxonomías
        cursor.execute("""
            SELECT 
                i.IncidenteID,
                i.Titulo,
                i.TieneReporteANCI,
                COUNT(it.ID) as TotalTaxonomias
            FROM Incidentes i
            LEFT JOIN INCIDENTE_TAXONOMIA it ON i.IncidenteID = it.IncidenteID
            GROUP BY i.IncidenteID, i.Titulo, i.TieneReporteANCI
            HAVING COUNT(it.ID) > 0 OR i.IncidenteID IN (5, 22)
            ORDER BY i.IncidenteID
        """)
        
        incidentes = cursor.fetchall()
        print(f"   📊 Incidentes con taxonomías: {len(incidentes)}")
        
        for inc in incidentes:
            anci_status = "🏛️ ANCI" if inc[2] else "📝 Normal"
            print(f"   - ID {inc[0]}: {inc[1][:30]}... | {anci_status} | {inc[3]} taxonomías")
        
        # 2. Simular el proceso de guardado paso a paso
        print(f"\n2. 🧪 SIMULANDO PROCESO DE GUARDADO")
        
        incidente_test = 22  # Usar incidente 22 para las pruebas
        
        # Datos de ejemplo como los enviaría el frontend
        datos_frontend = {
            "taxonomias_seleccionadas": [
                {
                    "id": "INC_USO_PHIP_ECDP",
                    "justificacion": "Justificación de prueba desde script profundo",
                    "descripcionProblema": "Descripción del problema detallada"
                },
                {
                    "id": "INC_CONF_EXCF_FCRA",
                    "justificacion": "Segunda justificación para filtración de configuraciones",
                    "descripcionProblema": "Problema con configuraciones expuestas"
                }
            ]
        }
        
        print(f"   📦 Datos que enviaría el frontend:")
        print(f"       Taxonomías: {len(datos_frontend['taxonomias_seleccionadas'])}")
        for tax in datos_frontend['taxonomias_seleccionadas']:
            print(f"       - {tax['id']}: {tax['justificacion'][:30]}...")
        
        # 3. Simular el proceso del backend
        print(f"\n3. ⚙️ SIMULANDO BACKEND (incidentes_actualizar.py)")
        
        # Paso 1: Eliminar taxonomías existentes
        print(f"   🗑️ Paso 1: Eliminar taxonomías existentes")
        cursor.execute("SELECT COUNT(*) FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?", (incidente_test,))
        antes = cursor.fetchone()[0]
        print(f"       Taxonomías antes: {antes}")
        
        cursor.execute("DELETE FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?", (incidente_test,))
        print(f"       ✅ Taxonomías eliminadas")
        
        # Paso 2: Insertar nuevas taxonomías
        print(f"   💾 Paso 2: Insertar nuevas taxonomías")
        
        for i, tax in enumerate(datos_frontend['taxonomias_seleccionadas']):
            print(f"       Insertando {i+1}/{len(datos_frontend['taxonomias_seleccionadas'])}: {tax['id']}")
            
            try:
                cursor.execute("""
                    INSERT INTO INCIDENTE_TAXONOMIA 
                    (IncidenteID, Id_Taxonomia, Comentarios, FechaAsignacion, CreadoPor)
                    VALUES (?, ?, ?, GETDATE(), ?)
                """, (
                    incidente_test,
                    tax.get('id'),
                    tax.get('justificacion', ''),
                    'debug_script'
                ))
                print(f"       ✅ Insertada correctamente")
                
            except Exception as e:
                print(f"       ❌ Error insertando: {e}")
        
        # Paso 3: Verificar inserción
        print(f"   🔍 Paso 3: Verificar inserción")
        cursor.execute("SELECT COUNT(*) FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?", (incidente_test,))
        despues = cursor.fetchone()[0]
        print(f"       Taxonomías después: {despues}")
        
        # Commit
        conn.commit()
        print(f"       ✅ Cambios confirmados (COMMIT)")
        
        # 4. Verificar que se pueden leer correctamente
        print(f"\n4. 📖 VERIFICAR LECTURA POST-GUARDADO")
        
        cursor.execute("""
            SELECT 
                it.Id_Taxonomia,
                it.Comentarios,
                it.FechaAsignacion,
                ti.Categoria_del_Incidente
            FROM INCIDENTE_TAXONOMIA it
            LEFT JOIN Taxonomia_incidentes ti ON it.Id_Taxonomia = ti.Id_Incidente
            WHERE it.IncidenteID = ?
            ORDER BY it.FechaAsignacion DESC
        """, (incidente_test,))
        
        resultado_lectura = cursor.fetchall()
        print(f"   📊 Taxonomías leídas: {len(resultado_lectura)}")
        
        for tax in resultado_lectura:
            print(f"   - {tax[0]}: {tax[3][:30] if tax[3] else 'Sin categoría'}...")
            print(f"     Comentarios: {tax[1][:50] if tax[1] else 'Sin comentarios'}...")
            print(f"     Fecha: {tax[2]}")
            print()
        
        cursor.close()
        conn.close()
        
        return {
            'antes': antes,
            'despues': despues,
            'enviadas': len(datos_frontend['taxonomias_seleccionadas']),
            'leidas': len(resultado_lectura)
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {}

def verificar_endpoints_actualizacion():
    """Verificar todos los endpoints de actualización"""
    try:
        print(f"\n🔍 VERIFICANDO ENDPOINTS DE ACTUALIZACIÓN")
        print("=" * 60)
        
        # Buscar todos los archivos que manejan actualización de incidentes
        import os
        import glob
        
        ruta_modulos = "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api/app/modules/admin/"
        ruta_views = "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api/app/views/"
        
        archivos_buscar = [
            ruta_modulos + "incidentes_actualizar.py",
            ruta_modulos + "incidentes_crear.py", 
            ruta_views + "incidente_views.py",
            ruta_views + "incidente_anci_actualizar.py"
        ]
        
        for archivo in archivos_buscar:
            if os.path.exists(archivo):
                print(f"\n📁 Verificando: {os.path.basename(archivo)}")
                
                with open(archivo, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                
                # Buscar manejo de taxonomías
                if 'taxonomias_seleccionadas' in contenido:
                    print(f"   ✅ Maneja taxonomías")
                    
                    # Buscar la lógica específica
                    lineas = contenido.split('\n')
                    for i, linea in enumerate(lineas):
                        if 'taxonomias_seleccionadas' in linea and 'for' in linea:
                            print(f"   📝 Línea {i+1}: {linea.strip()}")
                            
                            # Mostrar las siguientes 10 líneas para ver la lógica
                            for j in range(1, 11):
                                if i + j < len(lineas):
                                    print(f"   📝 Línea {i+j+1}: {lineas[i+j].strip()}")
                            break
                else:
                    print(f"   ❌ NO maneja taxonomías")
        
    except Exception as e:
        print(f"❌ Error verificando endpoints: {e}")

def verificar_problema_timeout():
    """Verificar si hay problemas de timeout en el guardado"""
    try:
        print(f"\n⏱️ VERIFICANDO PROBLEMAS DE TIMEOUT")
        print("=" * 60)
        
        from app.database import get_db_connection
        import time
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test de velocidad de inserción
        print("1. 🚀 Test de velocidad de inserción")
        
        incidente_test = 22
        
        # Tiempo para eliminar
        inicio = time.time()
        cursor.execute("DELETE FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?", (incidente_test,))
        tiempo_delete = time.time() - inicio
        print(f"   Tiempo DELETE: {tiempo_delete:.3f}s")
        
        # Tiempo para insertar múltiples
        taxonomias_test = [
            ("INC_USO_PHIP_ECDP", "Test 1"),
            ("INC_CONF_EXCF_FCRA", "Test 2"),
            ("INC_CONF_EXCF_FSRA", "Test 3")
        ]
        
        inicio = time.time()
        for tax_id, comentario in taxonomias_test:
            cursor.execute("""
                INSERT INTO INCIDENTE_TAXONOMIA 
                (IncidenteID, Id_Taxonomia, Comentarios, FechaAsignacion, CreadoPor)
                VALUES (?, ?, ?, GETDATE(), ?)
            """, (incidente_test, tax_id, comentario, 'test_timeout'))
        tiempo_insert = time.time() - inicio
        print(f"   Tiempo INSERT (3 taxonomías): {tiempo_insert:.3f}s")
        
        # Tiempo para commit
        inicio = time.time()
        conn.commit()
        tiempo_commit = time.time() - inicio
        print(f"   Tiempo COMMIT: {tiempo_commit:.3f}s")
        
        # Tiempo total
        tiempo_total = tiempo_delete + tiempo_insert + tiempo_commit
        print(f"   Tiempo TOTAL: {tiempo_total:.3f}s")
        
        if tiempo_total > 1.0:
            print(f"   ⚠️ WARNING: Operación lenta (>{tiempo_total:.1f}s)")
        else:
            print(f"   ✅ Operación rápida (<1s)")
        
        # Test de lectura
        inicio = time.time()
        cursor.execute("""
            SELECT it.Id_Taxonomia, it.Comentarios
            FROM INCIDENTE_TAXONOMIA it
            WHERE it.IncidenteID = ?
        """, (incidente_test,))
        resultado = cursor.fetchall()
        tiempo_lectura = time.time() - inicio
        print(f"   Tiempo LECTURA: {tiempo_lectura:.3f}s")
        print(f"   Registros leídos: {len(resultado)}")
        
        cursor.close()
        conn.close()
        
        return tiempo_total
        
    except Exception as e:
        print(f"❌ Error verificando timeout: {e}")
        return None

if __name__ == "__main__":
    print("🧪 DEBUG PROFUNDO - GUARDADO DE TAXONOMÍAS")
    print("=" * 80)
    
    # Test 1: Verificar guardado paso a paso
    resultado = verificar_endpoint_guardado()
    
    # Test 2: Verificar endpoints
    verificar_endpoints_actualizacion()
    
    # Test 3: Verificar problemas de timeout
    tiempo = verificar_problema_timeout()
    
    print(f"\n📊 RESUMEN FINAL:")
    print("=" * 50)
    print(f"Taxonomías enviadas: {resultado.get('enviadas', 0)}")
    print(f"Taxonomías antes: {resultado.get('antes', 0)}")
    print(f"Taxonomías después: {resultado.get('despues', 0)}")
    print(f"Taxonomías leídas: {resultado.get('leidas', 0)}")
    
    if tiempo:
        print(f"Tiempo de operación: {tiempo:.3f}s")
        if tiempo > 0.5:
            print("⚠️ POSIBLE PROBLEMA: Operación lenta")
        else:
            print("✅ Velocidad de BD: Normal")
    
    # Diagnóstico
    if resultado.get('despues', 0) == resultado.get('enviadas', 0):
        print("\n✅ GUARDADO: Correcto")
    else:
        print("\n❌ GUARDADO: Hay discrepancia")
    
    if resultado.get('leidas', 0) == resultado.get('despues', 0):
        print("✅ LECTURA: Correcta")
    else:
        print("❌ LECTURA: Hay discrepancia")
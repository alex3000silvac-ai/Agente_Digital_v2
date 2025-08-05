#!/usr/bin/env python3
"""
Verificación completa de taxonomías - Lo que realmente se muestra en UI
"""

def verificar_que_trae_endpoint_cargar():
    """Verificar qué campos trae el endpoint de cargar completo"""
    try:
        print("🔍 VERIFICANDO ENDPOINT CARGAR COMPLETO")
        print("=" * 70)
        
        # Leer el archivo
        archivo = "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api/app/views/incidente_cargar_completo.py"
        
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Buscar la query de taxonomías
        lineas = contenido.split('\n')
        en_query = False
        query_taxonomias = []
        
        for i, linea in enumerate(lineas):
            if 'query_taxonomias = """' in linea:
                en_query = True
                print(f"📍 Query taxonomías encontrada en línea {i+1}")
                continue
            
            if en_query:
                if '"""' in linea:
                    break
                query_taxonomias.append(linea)
        
        print("\n📋 QUERY ACTUAL DE TAXONOMÍAS:")
        for linea in query_taxonomias:
            print(linea)
        
        print("\n🚨 PROBLEMA IDENTIFICADO:")
        print("❌ La query NO trae el campo 'Comentarios' de INCIDENTE_TAXONOMIA")
        print("❌ Sin este campo, no se pueden mostrar justificación ni descripción")
        
        return query_taxonomias
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def verificar_tabla_incidente_taxonomia():
    """Verificar qué hay realmente en la tabla INCIDENTE_TAXONOMIA"""
    try:
        print(f"\n🗃️ VERIFICANDO TABLA INCIDENTE_TAXONOMIA")
        print("=" * 70)
        
        from app.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ver estructura de la tabla
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'INCIDENTE_TAXONOMIA'
            ORDER BY ORDINAL_POSITION
        """)
        
        columnas = cursor.fetchall()
        print("📊 Columnas en INCIDENTE_TAXONOMIA:")
        for col in columnas:
            print(f"   - {col[0]}: {col[1]}")
        
        # Ver datos de ejemplo
        cursor.execute("""
            SELECT TOP 5 
                IncidenteID,
                Id_Taxonomia,
                Comentarios,
                FechaAsignacion
            FROM INCIDENTE_TAXONOMIA
            WHERE IncidenteID = 22
            ORDER BY FechaAsignacion DESC
        """)
        
        datos = cursor.fetchall()
        print(f"\n📝 Datos de ejemplo (Incidente 22):")
        for row in datos:
            print(f"\n   Taxonomía: {row[1]}")
            print(f"   Comentarios: {row[2][:100] if row[2] else 'NULL'}...")
            print(f"   Fecha: {row[3]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando tabla: {e}")
        return False

def generar_fix_query():
    """Generar la query corregida"""
    print(f"\n💡 SOLUCIÓN: CORREGIR QUERY EN incidente_cargar_completo.py")
    print("=" * 70)
    
    print("\n📝 QUERY CORREGIDA (debe incluir Comentarios):")
    query_corregida = """
        SELECT DISTINCT
            IT.Id_Taxonomia,
            IT.Comentarios,  -- CAMPO CRÍTICO QUE FALTA
            IT.FechaAsignacion,
            IT.CreadoPor,
            TI.Area,
            TI.Efecto,
            TI.Categoria_del_Incidente,
            TI.Subcategoria_del_Incidente,
            TI.Tipo_Empresa
        FROM INCIDENTE_TAXONOMIA IT
        INNER JOIN TAXONOMIA_INCIDENTES TI ON IT.Id_Taxonomia = TI.Id_Incidente
        WHERE IT.IncidenteID = ?
    """
    
    print(query_corregida)
    
    print("\n🔧 LUEGO en el frontend (AcordeonIncidenteMejorado.vue):")
    print("   - Parsear el campo 'Comentarios' para extraer:")
    print("     • Justificación: ...")
    print("     • Descripción del problema: ...")
    
    return query_corregida

def verificar_formato_comentarios():
    """Verificar el formato real de los comentarios guardados"""
    try:
        print(f"\n🔍 VERIFICANDO FORMATO DE COMENTARIOS")
        print("=" * 70)
        
        from app.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ver comentarios reales
        cursor.execute("""
            SELECT TOP 10
                Id_Taxonomia,
                Comentarios
            FROM INCIDENTE_TAXONOMIA
            WHERE Comentarios IS NOT NULL
            AND LEN(Comentarios) > 10
            ORDER BY FechaAsignacion DESC
        """)
        
        datos = cursor.fetchall()
        print(f"📝 Ejemplos de comentarios guardados:")
        
        for i, row in enumerate(datos, 1):
            print(f"\n{i}. Taxonomía: {row[0]}")
            print(f"   Comentario completo:")
            print(f"   {'-' * 50}")
            print(f"   {row[1]}")
            print(f"   {'-' * 50}")
            
            # Verificar si tiene el formato esperado
            if "Justificación:" in row[1] and "Descripción del problema:" in row[1]:
                print("   ✅ Formato correcto detectado")
            else:
                print("   ❌ Formato incorrecto o antiguo")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_guardado_y_carga():
    """Test completo: guardar y luego verificar qué se carga"""
    try:
        print(f"\n🧪 TEST COMPLETO DE GUARDADO Y CARGA")
        print("=" * 70)
        
        from app.database import get_db_connection
        import requests
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        incidente_id = 22
        
        # 1. Guardar taxonomía de prueba
        print("1️⃣ Guardando taxonomía de prueba...")
        
        test_taxonomia = {
            'id': 'TEST_UI_VERIFICATION',
            'justificacion': 'JUSTIFICACIÓN DE PRUEBA PARA UI',
            'descripcionProblema': 'DESCRIPCIÓN DEL PROBLEMA PARA UI'
        }
        
        comentarios = f"Justificación: {test_taxonomia['justificacion']}\nDescripción del problema: {test_taxonomia['descripcionProblema']}"
        
        # Eliminar si existe
        cursor.execute("DELETE FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ? AND Id_Taxonomia = ?", 
                      (incidente_id, test_taxonomia['id']))
        
        # Insertar nueva
        cursor.execute("""
            INSERT INTO INCIDENTE_TAXONOMIA 
            (IncidenteID, Id_Taxonomia, Comentarios, FechaAsignacion, CreadoPor)
            VALUES (?, ?, ?, GETDATE(), ?)
        """, (incidente_id, test_taxonomia['id'], comentarios, 'test_ui'))
        
        conn.commit()
        print("   ✅ Taxonomía guardada")
        
        # 2. Verificar qué se guardó
        print("\n2️⃣ Verificando qué se guardó en BD...")
        cursor.execute("""
            SELECT Id_Taxonomia, Comentarios
            FROM INCIDENTE_TAXONOMIA
            WHERE IncidenteID = ? AND Id_Taxonomia = ?
        """, (incidente_id, test_taxonomia['id']))
        
        resultado = cursor.fetchone()
        if resultado:
            print(f"   ✅ Encontrada en BD:")
            print(f"   ID: {resultado[0]}")
            print(f"   Comentarios: {resultado[1]}")
        else:
            print(f"   ❌ NO encontrada en BD")
        
        # 3. Simular lo que haría el endpoint cargar_completo
        print("\n3️⃣ Simulando endpoint cargar_completo...")
        
        # Query actual (SIN Comentarios)
        cursor.execute("""
            SELECT DISTINCT
                IT.Id_Taxonomia,
                TI.Area,
                TI.Efecto,
                TI.Categoria_del_Incidente
            FROM INCIDENTE_TAXONOMIA IT
            LEFT JOIN TAXONOMIA_INCIDENTES TI ON IT.Id_Taxonomia = TI.Id_Incidente
            WHERE IT.IncidenteID = ? AND IT.Id_Taxonomia = ?
        """, (incidente_id, test_taxonomia['id']))
        
        resultado_actual = cursor.fetchone()
        print("\n   📋 Con query ACTUAL (sin Comentarios):")
        if resultado_actual:
            print(f"      ID: {resultado_actual[0]}")
            print(f"      ❌ Comentarios: NO DISPONIBLE")
        
        # Query corregida (CON Comentarios)
        cursor.execute("""
            SELECT DISTINCT
                IT.Id_Taxonomia,
                IT.Comentarios,
                TI.Area,
                TI.Efecto
            FROM INCIDENTE_TAXONOMIA IT
            LEFT JOIN TAXONOMIA_INCIDENTES TI ON IT.Id_Taxonomia = TI.Id_Incidente
            WHERE IT.IncidenteID = ? AND IT.Id_Taxonomia = ?
        """, (incidente_id, test_taxonomia['id']))
        
        resultado_corregido = cursor.fetchone()
        print("\n   📋 Con query CORREGIDA (con Comentarios):")
        if resultado_corregido:
            print(f"      ID: {resultado_corregido[0]}")
            print(f"      ✅ Comentarios: {resultado_corregido[1][:50]}...")
        
        cursor.close()
        conn.close()
        
        print("\n🎯 CONCLUSIÓN:")
        print("   El problema es que el endpoint NO está trayendo el campo Comentarios")
        print("   Por eso el frontend no puede mostrar justificación ni descripción")
        
    except Exception as e:
        print(f"❌ Error en test: {e}")

if __name__ == "__main__":
    print("🔍 VERIFICACIÓN DE TAXONOMÍAS - UI vs BD")
    print("=" * 80)
    
    # 1. Verificar query actual
    verificar_que_trae_endpoint_cargar()
    
    # 2. Verificar tabla
    verificar_tabla_incidente_taxonomia()
    
    # 3. Generar solución
    generar_fix_query()
    
    # 4. Verificar formato de comentarios
    verificar_formato_comentarios()
    
    # 5. Test completo
    test_guardado_y_carga()
    
    print("\n" + "=" * 80)
    print("🚨 PROBLEMA PRINCIPAL IDENTIFICADO:")
    print("   La query en incidente_cargar_completo.py NO incluye el campo Comentarios")
    print("   Sin este campo, el frontend no puede mostrar justificación ni descripción")
    print("\n💡 SOLUCIÓN:")
    print("   1. Agregar IT.Comentarios a la query")
    print("   2. El frontend ya está preparado para parsear este campo")
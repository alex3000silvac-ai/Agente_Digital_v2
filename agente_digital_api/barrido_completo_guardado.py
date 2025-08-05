#!/usr/bin/env python3
"""
Barrido completo para verificar que TODOS los campos se guarden correctamente
Incluye: Sección 2, Sección 4 (taxonomías), Sección 5.2.2, Sección 7, etc.
"""

def buscar_url_guardado_frontend():
    """Buscar la URL exacta que usa el frontend para guardar"""
    try:
        print("🔍 BUSCANDO URL DE GUARDADO DEL FRONTEND")
        print("=" * 60)
        
        archivo_componente = "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_ui/src/components/AcordeonIncidenteMejorado.vue"
        
        with open(archivo_componente, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Buscar función guardarIncidente
        lineas = contenido.split('\n')
        en_funcion_guardar = False
        
        for i, linea in enumerate(lineas):
            if 'async function guardarIncidente' in linea:
                en_funcion_guardar = True
                print(f"📍 Función guardarIncidente encontrada en línea {i+1}")
                print()
            
            if en_funcion_guardar and ('fetch(' in linea or 'axios' in linea or 'POST' in linea or 'PUT' in linea):
                print(f"🌐 Línea {i+1}: {linea.strip()}")
                
                # Mostrar contexto de 5 líneas antes y después
                for j in range(max(0, i-5), min(len(lineas), i+6)):
                    marca = ">>> " if j == i else "    "
                    print(f"   {marca}{j+1:4d}: {lineas[j].strip()}")
                print()
                
            # Salir de la función cuando termine
            if en_funcion_guardar and linea.strip().startswith('} ') and 'catch' in linea:
                break
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verificar_mapeo_campos_completo():
    """Verificar el mapeo completo de todos los campos del formulario"""
    try:
        print(f"\n🗺️ VERIFICANDO MAPEO COMPLETO DE CAMPOS")
        print("=" * 60)
        
        # Verificar incidentes_actualizar.py
        archivo_actualizar = "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api/app/modules/admin/incidentes_actualizar.py"
        
        with open(archivo_actualizar, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Buscar el mapeo de campos
        lineas = contenido.split('\n')
        en_mapeo = False
        
        for i, linea in enumerate(lineas):
            if 'mapeo_campos = {' in linea:
                en_mapeo = True
                print(f"📋 Mapeo de campos encontrado en línea {i+1}")
                print()
            
            if en_mapeo:
                if linea.strip().startswith("'") and ':' in linea:
                    campo_frontend = linea.split("'")[1]
                    campo_backend = linea.split(':')[1].strip().replace("'", "").replace(",", "")
                    print(f"   {campo_frontend:25} → {campo_backend}")
                
                if linea.strip() == '}':
                    break
        
        # Verificar campos específicos mencionados por el usuario
        print(f"\n🎯 VERIFICANDO CAMPOS ESPECÍFICOS MENCIONADOS:")
        campos_verificar = [
            "2.", "5.2.2", "7.", "taxonomias"
        ]
        
        for campo in campos_verificar:
            encontrados = [linea for linea in lineas if campo in linea and "'" in linea]
            print(f"\n📍 Campo {campo}:")
            if encontrados:
                for linea in encontrados[:3]:  # Mostrar máximo 3 coincidencias
                    print(f"   {linea.strip()}")
            else:
                print(f"   ❌ NO ENCONTRADO")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando mapeo: {e}")
        return False

def verificar_guardado_seccion_especifica(seccion):
    """Verificar guardado de una sección específica"""
    try:
        print(f"\n🔍 VERIFICANDO GUARDADO DE SECCIÓN {seccion}")
        print("=" * 50)
        
        from app.database import get_db_connection
        
        # Datos de prueba para verificar
        datos_test = {
            f"{seccion}.1": f"Valor de prueba para {seccion}.1",
            f"{seccion}.2": f"Valor de prueba para {seccion}.2",
            f"{seccion}.3": f"Valor de prueba para {seccion}.3",
        }
        
        if seccion == "5.2":
            datos_test["5.2.2"] = "Valor específico para 5.2.2"
        
        print(f"📦 Datos de prueba:")
        for campo, valor in datos_test.items():
            print(f"   {campo}: {valor}")
        
        # Verificar mapeo en incidentes_actualizar.py
        archivo_actualizar = "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api/app/modules/admin/incidentes_actualizar.py"
        
        with open(archivo_actualizar, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        encontrado_mapeo = False
        for campo in datos_test.keys():
            if f"'{campo}'" in contenido:
                encontrado_mapeo = True
                # Buscar a qué columna se mapea
                lineas = contenido.split('\n')
                for linea in lineas:
                    if f"'{campo}'" in linea and ':' in linea:
                        columna_bd = linea.split(':')[1].strip().replace("'", "").replace(",", "")
                        print(f"   ✅ {campo} → {columna_bd}")
                        break
        
        if not encontrado_mapeo:
            print(f"   ❌ NO se encontró mapeo para campos de sección {seccion}")
        
        return encontrado_mapeo
        
    except Exception as e:
        print(f"❌ Error verificando sección {seccion}: {e}")
        return False

def verificar_estructura_bd_incidentes():
    """Verificar estructura de la tabla Incidentes para asegurar que existen las columnas"""
    try:
        print(f"\n🗃️ VERIFICANDO ESTRUCTURA DE BD - TABLA INCIDENTES")
        print("=" * 60)
        
        from app.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener estructura de la tabla
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'Incidentes'
            ORDER BY ORDINAL_POSITION
        """)
        
        columnas = cursor.fetchall()
        print(f"📊 Total columnas en tabla Incidentes: {len(columnas)}")
        print()
        
        # Buscar columnas específicas mencionadas por el usuario
        columnas_buscar = [
            'Descripcion', 'DescripcionInicial', 'DescripcionBreve',
            'SistemasAfectados', 'AccionesInmediatas', 'CausaRaiz',
            'LeccionesAprendidas', 'ProximosPasos', 'MedidasPreventivas'
        ]
        
        print("🎯 COLUMNAS RELACIONADAS CON SECCIONES:")
        for col_buscar in columnas_buscar:
            encontrada = False
            for col in columnas:
                if col_buscar.lower() in col[0].lower():
                    print(f"   ✅ {col[0]:30} | {col[1]:15} | {'NULL' if col[3] == 'YES' else 'NOT NULL'}")
                    encontrada = True
                    break
            if not encontrada:
                print(f"   ❌ {col_buscar:30} | NO ENCONTRADA")
        
        print(f"\n📋 TODAS LAS COLUMNAS:")
        for col in columnas:
            print(f"   {col[0]:30} | {col[1]:15} | {'NULL' if col[3] == 'YES' else 'NOT NULL'}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando estructura BD: {e}")
        return False

def test_guardado_real():
    """Test real de guardado para verificar qué se pierde"""
    try:
        print(f"\n💾 TEST REAL DE GUARDADO")
        print("=" * 50)
        
        from app.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        incidente_test = 22
        
        # Datos de prueba completos como los enviaría el frontend
        datos_completos = {
            '1.1': 'TipoRegistro Test',
            '1.2': 'Título Test Completo',
            '2.1': 'Descripción inicial de la sección 2',
            '2.2': 'Sistemas afectados de la sección 2',
            '5.1': 'Causa raíz de la sección 5',
            '5.2': 'Solución implementada de la sección 5',
            '5.2.2': 'Campo específico 5.2.2 que no se graba',
            '6.1': 'Fecha resolución de la sección 6',
            '7.1': 'Campo de la sección 7 que no se traspasa',
            'taxonomias_seleccionadas': [
                {
                    'id': 'INC_USO_PHIP_ECDP',
                    'justificacion': 'Justificación completa de test',
                    'descripcionProblema': 'Descripción del problema completa'
                }
            ]
        }
        
        print("📦 Datos de prueba enviados:")
        for campo, valor in datos_completos.items():
            if campo != 'taxonomias_seleccionadas':
                print(f"   {campo}: {valor}")
        print(f"   taxonomias_seleccionadas: {len(datos_completos['taxonomias_seleccionadas'])} elementos")
        
        # Simular proceso de incidentes_actualizar.py
        print(f"\n⚙️ Simulando proceso de guardado...")
        
        # Mapeo de campos (copiado de incidentes_actualizar.py)
        mapeo_campos = {
            '1.1': 'TipoRegistro',
            '1.2': 'Titulo',
            '2.1': 'DescripcionInicial',
            '2.2': 'SistemasAfectados',
            '5.1': 'CausaRaiz',
            '5.2': 'SolucionImplementada',
            '6.1': 'FechaResolucion',
            # Verificar si 5.2.2 y 7.1 están mapeados
        }
        
        campos_actualizar = []
        valores = []
        
        for campo_form, campo_bd in mapeo_campos.items():
            if campo_form in datos_completos:
                print(f"   ✅ Mapeando {campo_form} → {campo_bd}")
                campos_actualizar.append(f"{campo_bd} = ?")
                valores.append(datos_completos[campo_form])
            else:
                print(f"   ⚠️ Campo {campo_form} no está en datos enviados")
        
        # Verificar campos que no se mapean
        campos_no_mapeados = []
        for campo in datos_completos.keys():
            if campo not in mapeo_campos and campo != 'taxonomias_seleccionadas':
                campos_no_mapeados.append(campo)
                print(f"   ❌ Campo {campo} NO tiene mapeo en backend")
        
        if campos_no_mapeados:
            print(f"\n🚨 CAMPOS SIN MAPEAR: {campos_no_mapeados}")
            print(f"🔧 SOLUCIÓN: Agregar estos campos al mapeo_campos en incidentes_actualizar.py")
        
        # Probar actualización real
        if campos_actualizar:
            campos_actualizar.append("FechaActualizacion = GETDATE()")
            campos_actualizar.append("ModificadoPor = ?")
            valores.extend(['test_user', incidente_test])
            
            query = f"""
                UPDATE Incidentes 
                SET {', '.join(campos_actualizar)}
                WHERE IncidenteID = ?
            """
            
            print(f"\n📝 Query generada:")
            print(f"   {query}")
            print(f"   Valores: {valores[:5]}...")  # Mostrar solo primeros 5
            
            # NO ejecutar realmente, solo simular
            print(f"   ✅ Query preparada correctamente")
        
        cursor.close()
        conn.close()
        
        return {
            'total_campos': len(datos_completos),
            'campos_mapeados': len(campos_actualizar) - 2,  # -2 por campos de auditoría
            'campos_sin_mapear': len(campos_no_mapeados)
        }
        
    except Exception as e:
        print(f"❌ Error en test guardado: {e}")
        return {}

if __name__ == "__main__":
    print("🧪 BARRIDO COMPLETO DE GUARDADO")
    print("=" * 80)
    
    # 1. Buscar URL de guardado del frontend
    buscar_url_guardado_frontend()
    
    # 2. Verificar mapeo de campos
    verificar_mapeo_campos_completo()
    
    # 3. Verificar secciones específicas
    secciones_verificar = ["2", "5.2", "7"]
    for seccion in secciones_verificar:
        verificar_guardado_seccion_especifica(seccion)
    
    # 4. Verificar estructura de BD
    verificar_estructura_bd_incidentes()
    
    # 5. Test real de guardado
    resultado = test_guardado_real()
    
    print(f"\n📊 RESUMEN FINAL:")
    print("=" * 50)
    if resultado:
        print(f"Total campos enviados: {resultado.get('total_campos', 0)}")
        print(f"Campos mapeados: {resultado.get('campos_mapeados', 0)}")
        print(f"Campos sin mapear: {resultado.get('campos_sin_mapear', 0)}")
        
        if resultado.get('campos_sin_mapear', 0) > 0:
            print("🚨 PROBLEMA: Hay campos que no se están guardando")
            print("💡 SOLUCIÓN: Ampliar mapeo_campos en incidentes_actualizar.py")
        else:
            print("✅ Todos los campos están mapeados correctamente")
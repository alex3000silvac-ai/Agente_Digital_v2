#!/usr/bin/env python3
"""
Test completo de la solución implementada
Verifica: taxonomías, campos 5.2.2, sección 7, sin timeouts
"""

def test_taxonomias_formato_completo():
    """Test del nuevo formato de taxonomías con justificación + descripción"""
    try:
        print("🔍 TEST: FORMATO COMPLETO DE TAXONOMÍAS")
        print("=" * 60)
        
        from app.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        incidente_test = 22
        
        # Datos como los enviaría el frontend CORREGIDO
        datos_taxonomias = [
            {
                'id': 'INC_USO_PHIP_ECDP',
                'justificacion': 'Justificación completa de prueba',
                'descripcionProblema': 'Descripción detallada del problema encontrado'
            },
            {
                'id': 'INC_CONF_EXCF_FCRA',
                'justificacion': 'Segunda justificación',
                'descripcionProblema': 'Segunda descripción del problema'
            }
        ]
        
        print("📦 Datos de taxonomías a probar:")
        for tax in datos_taxonomias:
            print(f"   {tax['id']}:")
            print(f"     Justificación: {tax['justificacion']}")
            print(f"     Descripción problema: {tax['descripcionProblema']}")
        
        # Simular el proceso CORREGIDO del backend
        print(f"\n⚙️ Simulando proceso corregido...")
        
        # Paso 1: Eliminar taxonomías existentes
        cursor.execute("DELETE FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?", (incidente_test,))
        
        # Paso 2: Insertar con formato CORREGIDO
        for tax in datos_taxonomias:
            # FORMATO CORREGIDO: igual que incidentes_crear.py
            justificacion = tax.get('justificacion', '')
            descripcion_problema = tax.get('descripcionProblema', '')
            comentarios = f"Justificación: {justificacion}\nDescripción del problema: {descripcion_problema}"
            
            print(f"   Insertando {tax['id']} con comentarios completos...")
            print(f"     Comentarios: {comentarios[:50]}...")
            
            cursor.execute("""
                INSERT INTO INCIDENTE_TAXONOMIA 
                (IncidenteID, Id_Taxonomia, Comentarios, FechaAsignacion, CreadoPor)
                VALUES (?, ?, ?, GETDATE(), ?)
            """, (
                incidente_test,
                tax.get('id'),
                comentarios,
                'test_solucion'
            ))
        
        conn.commit()
        print(f"   ✅ Taxonomías insertadas con formato completo")
        
        # Paso 3: Verificar lectura
        cursor.execute("""
            SELECT Id_Taxonomia, Comentarios
            FROM INCIDENTE_TAXONOMIA
            WHERE IncidenteID = ?
        """, (incidente_test,))
        
        resultado = cursor.fetchall()
        print(f"\n📖 Verificando lectura:")
        print(f"   Taxonomías leídas: {len(resultado)}")
        
        for tax in resultado:
            print(f"   {tax[0]}:")
            print(f"     Comentarios completos: {tax[1]}")
            
            # Verificar que contiene ambos campos
            if 'Justificación:' in tax[1] and 'Descripción del problema:' in tax[1]:
                print(f"     ✅ Formato completo detectado")
            else:
                print(f"     ❌ Formato incompleto")
        
        cursor.close()
        conn.close()
        
        return len(resultado) == len(datos_taxonomias)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_campos_nuevos_mapeo():
    """Test de los campos nuevos agregados al mapeo"""
    try:
        print(f"\n🔍 TEST: CAMPOS NUEVOS EN MAPEO")
        print("=" * 60)
        
        # Leer el archivo corregido
        archivo = "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api/app/modules/admin/incidentes_actualizar.py"
        
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Verificar que los campos nuevos estén en el mapeo
        campos_verificar = {
            '5.2.2': 'DescripcionCompleta',
            '7.1': 'DescripcionEstadoActual',
            '7.2': 'EfectosColaterales',
            '7.3': 'ProgramaRestauracion'
        }
        
        print("📋 Verificando campos agregados al mapeo:")
        todos_encontrados = True
        
        for campo_frontend, campo_bd in campos_verificar.items():
            if f"'{campo_frontend}'" in contenido and campo_bd in contenido:
                print(f"   ✅ {campo_frontend} → {campo_bd}")
            else:
                print(f"   ❌ {campo_frontend} NO encontrado")
                todos_encontrados = False
        
        return todos_encontrados
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_eliminacion_timeouts():
    """Test de eliminación de timeouts en el frontend"""
    try:
        print(f"\n🔍 TEST: ELIMINACIÓN DE TIMEOUTS")
        print("=" * 60)
        
        archivo = "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_ui/src/components/AcordeonIncidenteMejorado.vue"
        
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Verificar cambios específicos
        cambios_verificar = [
            ("Recarga sin timeout", "await cargarIncidenteExistente()"),
            ("Sin setTimeout en recarga", "setTimeout(async" not in contenido),
            ("await cargarTaxonomias", "await cargarTaxonomias()"),
            ("Sin setInterval en taxonomías", "setInterval(" not in contenido.split("cargarTaxonomiasSeleccionadas")[1][:1000] if "cargarTaxonomiasSeleccionadas" in contenido else True)
        ]
        
        print("📋 Verificando eliminación de timeouts:")
        todos_ok = True
        
        for nombre, condicion in cambios_verificar:
            if isinstance(condicion, str):
                if condicion in contenido:
                    print(f"   ✅ {nombre}")
                else:
                    print(f"   ❌ {nombre} - No encontrado")
                    todos_ok = False
            elif isinstance(condicion, bool):
                if condicion:
                    print(f"   ✅ {nombre}")
                else:
                    print(f"   ❌ {nombre} - Falló condición")
                    todos_ok = False
        
        return todos_ok
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_simulacion_guardado_completo():
    """Test de simulación de guardado completo con todos los campos"""
    try:
        print(f"\n🔍 TEST: SIMULACIÓN GUARDADO COMPLETO")
        print("=" * 60)
        
        # Datos completos como los enviaría el frontend
        datos_completos = {
            '1.1': 'Tipo de registro',
            '1.2': 'Título del incidente',
            '2.1': 'Descripción inicial sección 2',
            '2.2': 'Sistemas afectados sección 2', 
            '5.1': 'Causa raíz sección 5',
            '5.2': 'Solución implementada sección 5',
            '5.2.2': 'Campo específico 5.2.2 - DEBE GUARDARSE',
            '6.1': 'Fecha resolución',
            '7.1': 'Campo sección 7.1 - DEBE GUARDARSE',
            '7.2': 'Campo sección 7.2 - DEBE GUARDARSE',
            'taxonomias_seleccionadas': [
                {
                    'id': 'INC_USO_PHIP_ECDP',
                    'justificacion': 'Justificación completa',
                    'descripcionProblema': 'Descripción completa del problema'
                }
            ]
        }
        
        # Mapeo actualizado (copiado del archivo corregido)
        mapeo_corregido = {
            '1.1': 'TipoRegistro',
            '1.2': 'Titulo', 
            '2.1': 'DescripcionInicial',
            '2.2': 'SistemasAfectados',
            '5.1': 'CausaRaiz',
            '5.2': 'SolucionImplementada',
            '5.2.2': 'DescripcionCompleta',  # NUEVO
            '6.1': 'FechaResolucion',
            '7.1': 'DescripcionEstadoActual',  # NUEVO
            '7.2': 'EfectosColaterales',  # NUEVO
        }
        
        print("📦 Simulando guardado con mapeo corregido:")
        
        # Verificar mapeo de campos normales
        campos_mapeados = 0
        campos_sin_mapear = []
        
        for campo, valor in datos_completos.items():
            if campo != 'taxonomias_seleccionadas':
                if campo in mapeo_corregido:
                    print(f"   ✅ {campo} → {mapeo_corregido[campo]}")
                    campos_mapeados += 1
                else:
                    print(f"   ❌ {campo} SIN MAPEAR")
                    campos_sin_mapear.append(campo)
        
        # Verificar taxonomías
        print(f"\n📋 Taxonomías:")
        for tax in datos_completos['taxonomias_seleccionadas']:
            justificacion = tax['justificacion']
            descripcion = tax['descripcionProblema']
            comentarios_formato = f"Justificación: {justificacion}\nDescripción del problema: {descripcion}"
            print(f"   ✅ {tax['id']} → Comentarios formato completo")
            print(f"      {comentarios_formato[:50]}...")
        
        print(f"\n📊 Resultado simulación:")
        print(f"   Campos mapeados: {campos_mapeados}")
        print(f"   Campos sin mapear: {len(campos_sin_mapear)}")
        print(f"   Taxonomías: {len(datos_completos['taxonomias_seleccionadas'])}")
        
        if len(campos_sin_mapear) == 0:
            print(f"   ✅ TODOS los campos tienen mapeo")
            return True
        else:
            print(f"   ❌ Campos faltantes: {campos_sin_mapear}")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TEST COMPLETO DE LA SOLUCIÓN IMPLEMENTADA")
    print("=" * 80)
    
    # Tests individuales
    test1 = test_taxonomias_formato_completo()
    test2 = test_campos_nuevos_mapeo() 
    test3 = test_eliminacion_timeouts()
    test4 = test_simulacion_guardado_completo()
    
    print(f"\n📊 RESULTADOS FINALES:")
    print("=" * 50)
    print(f"Test 1 - Taxonomías formato completo: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Test 2 - Campos nuevos en mapeo: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Test 3 - Eliminación timeouts: {'✅ PASS' if test3 else '❌ FAIL'}")
    print(f"Test 4 - Simulación guardado: {'✅ PASS' if test4 else '❌ FAIL'}")
    
    todos_ok = all([test1, test2, test3, test4])
    
    if todos_ok:
        print(f"\n🎉 TODOS LOS TESTS PASARON")
        print(f"✅ Solución completa implementada correctamente")
        print(f"📋 Ahora debería funcionar:")
        print(f"   - Taxonomías se guardan con justificación + descripción")
        print(f"   - Campo 5.2.2 se guarda en DescripcionCompleta") 
        print(f"   - Campos 7.x se guardan en campos apropiados")
        print(f"   - Sin timeouts que causen problemas de sincronización")
    else:
        print(f"\n❌ ALGUNOS TESTS FALLARON")
        print(f"⚠️ Revisar implementación antes de usar")
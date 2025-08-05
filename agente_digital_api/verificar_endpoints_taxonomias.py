#!/usr/bin/env python3
"""
Verificar qué endpoint maneja cada escenario de taxonomías
"""

def analizar_endpoints_taxonomias():
    """Analizar cada endpoint que maneja taxonomías"""
    try:
        print("🔍 ANÁLISIS DE ENDPOINTS DE TAXONOMÍAS")
        print("=" * 70)
        
        # 1. incidentes_crear.py - Para CREACIÓN de incidencias semilla
        print("1. 📝 CREACIÓN DE INCIDENCIA SEMILLA")
        print("   Endpoint: incidentes_crear.py")
        print("   Ruta: /api/incidentes/crear")
        print("   Método: POST")
        print("   Lógica de taxonomías:")
        print("   - Línea 848: for taxonomia in datos['taxonomias_seleccionadas']:")
        print("   - Línea 856: comentarios = f\"Justificación: {taxonomia.get('justificacion', '')}\\nDescripción del problema: {taxonomia.get('descripcionProblema', '')}\"")
        print("   - Usa: taxonomia.get('justificacion', '') y taxonomia.get('descripcionProblema', '')")
        print("   ✅ FORMATO: Combina justificación + descripción en comentarios")
        print()
        
        # 2. incidentes_actualizar.py - Para EDICIÓN de incidencias normales
        print("2. ✏️ EDICIÓN DE INCIDENCIA NORMAL")
        print("   Endpoint: incidentes_actualizar.py")
        print("   Ruta: /api/incidentes/<id>/actualizar")
        print("   Método: PUT")
        print("   Lógica de taxonomías:")
        print("   - Línea 138: for tax in datos['taxonomias_seleccionadas']:")
        print("   - Línea 146: tax.get('justificacion', '')")
        print("   - Usa: SOLO tax.get('justificacion', '')")
        print("   ⚠️ FORMATO: Solo justificación, NO incluye descripcionProblema")
        print()
        
        # 3. incidente_views.py - Para otros escenarios
        print("3. 🔄 OTROS ESCENARIOS")
        print("   Endpoint: incidente_views.py")
        print("   Rutas: Varias")
        print("   Lógica de taxonomías:")
        print("   - Línea 124: for taxonomia in taxonomias_seleccionadas:")
        print("   - Línea 129: taxonomia['Id_Taxonomia'], taxonomia.get('Comentarios', '')")
        print("   - Usa: taxonomia['Id_Taxonomia'] y taxonomia.get('Comentarios', '')")
        print("   ⚠️ FORMATO: Espera campos diferentes (Id_Taxonomia, Comentarios)")
        print()
        
        # 4. Identificar la inconsistencia
        print("🚨 INCONSISTENCIAS ENCONTRADAS:")
        print("=" * 50)
        print("❌ PROBLEMA 1: Nombres de campos inconsistentes")
        print("   - incidentes_crear.py usa: 'justificacion' + 'descripcionProblema'")
        print("   - incidentes_actualizar.py usa: 'justificacion'")
        print("   - incidente_views.py usa: 'Id_Taxonomia' + 'Comentarios'")
        print()
        print("❌ PROBLEMA 2: Formato de comentarios inconsistente")
        print("   - incidentes_crear.py: 'Justificación: X\\nDescripción del problema: Y'")
        print("   - incidentes_actualizar.py: Solo la justificación")
        print("   - incidente_views.py: Campo 'Comentarios' directo")
        print()
        print("❌ PROBLEMA 3: Estructura de datos esperada diferente")
        print("   - Frontend envía: {id: 'XXX', justificacion: 'YYY', descripcionProblema: 'ZZZ'}")
        print("   - incidente_views.py espera: {Id_Taxonomia: 'XXX', Comentarios: 'YYY'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verificar_frontend_urls():
    """Verificar qué URLs usa el frontend para cada escenario"""
    try:
        print(f"\n🌐 VERIFICACIÓN DE URLs DEL FRONTEND")
        print("=" * 60)
        
        # Buscar en el archivo del componente
        archivo_componente = "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_ui/src/components/AcordeonIncidenteMejorado.vue"
        
        with open(archivo_componente, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Buscar URLs de fetch
        import re
        urls_encontradas = re.findall(r'fetch\([\'"`]([^\'"`]+)[\'"`]', contenido)
        
        print("📡 URLs encontradas en el componente:")
        for i, url in enumerate(urls_encontradas, 1):
            print(f"   {i}. {url}")
        
        # Buscar específicamente la URL de guardado
        lineas = contenido.split('\n')
        for i, linea in enumerate(lineas):
            if 'fetch(' in linea and ('incidente' in linea.lower() or 'actualizar' in linea.lower() or 'crear' in linea.lower()):
                print(f"\n📍 Línea {i+1}: {linea.strip()}")
                
                # Mostrar contexto
                for j in range(max(0, i-2), min(len(lineas), i+3)):
                    marca = ">>> " if j == i else "    "
                    print(f"   {marca}Línea {j+1}: {lineas[j].strip()}")
                print()
        
        return urls_encontradas
        
    except Exception as e:
        print(f"❌ Error verificando frontend: {e}")
        return []

def generar_solucion():
    """Generar la solución para los problemas encontrados"""
    print(f"\n💡 SOLUCIÓN PROPUESTA")
    print("=" * 60)
    
    print("🎯 OBJETIVO: Unificar la lógica de taxonomías en todos los endpoints")
    print()
    
    print("📋 PASOS A SEGUIR:")
    print("1. ✅ Estandarizar formato de datos del frontend")
    print("   - Usar siempre: {id: 'XXX', justificacion: 'YYY', descripcionProblema: 'ZZZ'}")
    print()
    
    print("2. ✅ Estandarizar formato de comentarios en BD")
    print("   - Usar siempre: 'Justificación: X\\nDescripción del problema: Y'")
    print("   - O crear campos separados si es necesario")
    print()
    
    print("3. ✅ Corregir incidentes_actualizar.py")
    print("   - Cambiar línea 146 para incluir descripcionProblema")
    print("   - Usar el mismo formato que incidentes_crear.py")
    print()
    
    print("4. ✅ Corregir incidente_views.py")
    print("   - Adaptar para usar el formato estándar del frontend")
    print("   - Mapear correctamente los campos")
    print()
    
    print("5. ✅ Verificar y corregir todas las consultas de lectura")
    print("   - Asegurar que parse correctamente el formato de comentarios")
    print("   - Separar justificación y descripciónProblema al leer")

if __name__ == "__main__":
    print("🧪 VERIFICACIÓN DE ENDPOINTS DE TAXONOMÍAS")
    print("=" * 80)
    
    # Análisis de endpoints
    analizar_endpoints_taxonomias()
    
    # Verificación del frontend
    urls = verificar_frontend_urls()
    
    # Generar solución
    generar_solucion()
    
    print(f"\n📊 CONCLUSIÓN:")
    print("=" * 50)
    print("🚨 PROBLEMA IDENTIFICADO: Múltiples endpoints con lógica inconsistente")
    print("💊 SOLUCIÓN: Estandarizar formato de datos y lógica de guardado")
    print("🎯 PRIORIDAD: Corregir incidentes_actualizar.py primero (más usado)")
    print("⚡ URGENCIA: ALTA - Esto explica por qué las taxonomías no se guardan correctamente")
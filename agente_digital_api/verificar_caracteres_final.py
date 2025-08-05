#!/usr/bin/env python3
"""
Script para verificar si quedan caracteres problemáticos
"""

def verificar_caracteres():
    file_path = "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_ui/src/components/ModuloAcompanamiento.vue"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar caracteres problemáticos
    problematicos = {
        'Comilla simple izquierda (')': ''',
        'Comilla simple derecha (')': ''',
        'Comilla doble izquierda (")': '"',
        'Comilla doble derecha (")': '"',
        'Guión corto (–)': '–',
        'Guión largo (—)': '—',
        'Puntos suspensivos (…)': '…',
        'Check (✓)': '✓',
        'Reloj (⏰)': '⏰',
        'Warning (⚠)': '⚠',
        'Flecha (→)': '→'
    }
    
    encontrados = []
    for nombre, char in problematicos.items():
        count = content.count(char)
        if count > 0:
            encontrados.append((nombre, count))
    
    if encontrados:
        print("❌ Se encontraron los siguientes caracteres problemáticos:")
        for nombre, count in encontrados:
            print(f"  - {nombre}: {count} ocurrencias")
        return False
    else:
        print("✅ No se encontraron caracteres problemáticos")
        print("✅ El archivo está limpio y listo para usar")
        return True

if __name__ == "__main__":
    verificar_caracteres()
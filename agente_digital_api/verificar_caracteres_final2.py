#!/usr/bin/env python3
"""
Script para verificar si quedan caracteres problemáticos
"""

def verificar_caracteres():
    file_path = "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_ui/src/components/ModuloAcompanamiento.vue"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar caracteres problemáticos usando sus códigos Unicode
    problematicos = [
        ('Comilla simple izquierda', '\u2018'),  # '
        ('Comilla simple derecha', '\u2019'),    # '
        ('Comilla doble izquierda', '\u201C'),   # "
        ('Comilla doble derecha', '\u201D'),     # "
        ('Guión corto', '\u2013'),               # –
        ('Guión largo', '\u2014'),               # —
        ('Puntos suspensivos', '\u2026'),        # …
        ('Check', '\u2713'),                     # ✓
        ('Reloj', '\u23F0'),                     # ⏰
        ('Warning', '\u26A0'),                   # ⚠
        ('Flecha derecha', '\u2192')             # →
    ]
    
    encontrados = []
    for nombre, char in problematicos:
        count = content.count(char)
        if count > 0:
            encontrados.append((nombre, char, count))
    
    if encontrados:
        print("❌ Se encontraron los siguientes caracteres problemáticos:")
        for nombre, char, count in encontrados:
            print(f"  - {nombre} ({char}): {count} ocurrencias")
        return False
    else:
        print("✅ No se encontraron caracteres problemáticos")
        print("✅ El archivo está limpio y listo para usar")
        return True

if __name__ == "__main__":
    verificar_caracteres()
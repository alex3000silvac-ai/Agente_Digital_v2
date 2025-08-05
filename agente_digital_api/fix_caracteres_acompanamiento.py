#!/usr/bin/env python3
"""
Script para corregir caracteres irregulares en ModuloAcompanamiento.vue
"""
import re

def fix_caracteres_irregulares():
    # Ruta del archivo
    file_path = "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_ui/src/components/ModuloAcompanamiento.vue"
    
    # Leer el archivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Guardar copia de respaldo
    with open(file_path + '.backup_caracteres', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Reemplazos de caracteres problemáticos
    replacements = {
        # Comillas tipográficas a comillas normales
        ''': "'",
        ''': "'",
        '"': '"',
        '"': '"',
        
        # Guiones largos a guiones normales
        '–': '-',
        '—': '-',
        
        # Puntos suspensivos
        '…': '...',
        
        # Otros símbolos especiales ya fueron reemplazados manualmente
        # '✓': '<i class="ph ph-check"></i>',
        # '⏰': '<i class="ph ph-clock"></i>',
        # '⚠': '<i class="ph ph-warning"></i>',
        # '→': '<i class="ph ph-arrow-right"></i>',
    }
    
    # Aplicar reemplazos
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Escribir el archivo corregido
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Caracteres irregulares corregidos exitosamente")
    print(f"📄 Backup guardado en: {file_path}.backup_caracteres")
    
    # Mostrar resumen de cambios
    print("\n📊 Resumen de cambios:")
    for old, new in replacements.items():
        print(f"  - '{old}' → '{new}'")

if __name__ == "__main__":
    fix_caracteres_irregulares()
#!/usr/bin/env python3
"""
Script completo para corregir caracteres irregulares en ModuloAcompanamiento.vue
"""

def fix_caracteres():
    # Ruta del archivo
    file_path = "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_ui/src/components/ModuloAcompanamiento.vue"
    
    try:
        # Leer el archivo
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Contar caracteres problemáticos antes
        count_before = {
            'left_single': content.count('''),
            'right_single': content.count('''),
            'left_double': content.count('"'),
            'right_double': content.count('"'),
            'en_dash': content.count('–'),
            'em_dash': content.count('—'),
            'ellipsis': content.count('…')
        }
        
        print("📊 Caracteres problemáticos encontrados:")
        total = sum(count_before.values())
        if total > 0:
            for char, count in count_before.items():
                if count > 0:
                    print(f"  - {char}: {count} ocurrencias")
        else:
            print("  ✅ No se encontraron caracteres problemáticos")
            return
        
        # Reemplazar caracteres
        # Comillas simples
        content = content.replace(''', "'")
        content = content.replace(''', "'")
        
        # Comillas dobles
        content = content.replace('"', '"')
        content = content.replace('"', '"')
        
        # Guiones
        content = content.replace('–', '-')
        content = content.replace('—', '-')
        
        # Puntos suspensivos
        content = content.replace('…', '...')
        
        # Escribir el archivo corregido
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("\n✅ Archivo corregido exitosamente")
        print(f"📄 Total de caracteres reemplazados: {total}")
        
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {file_path}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    fix_caracteres()
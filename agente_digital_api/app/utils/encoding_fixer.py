#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para corregir problemas de encoding en datos
Convierte texto mal codificado a UTF-8 correcto
"""

import re

class EncodingFixer:
    """
    Corrige problemas comunes de encoding UTF-8/Latin-1
    """
    
    @classmethod
    def get_replacements(cls):
        """
        Retorna el mapa de reemplazos evitando problemas de caracteres
        """
        replacements = {
            # Vocales con tilde minusculas
            'Ã¡': 'á',
            'Ã©': 'é', 
            'Ã­': 'í',
            'Ã³': 'ó',
            'Ãº': 'ú',
            # Vocales con tilde mayusculas  
            'Ã': 'Á',
            'Ã‰': 'É',
            'Ã': 'Í',
            'Ã"': 'Ó',
            'Ãš': 'Ú',
            # Enie minuscula
            'Ã±': 'ñ',
            # U con dieresis
            'Ã¼': 'ü',
            'Ãœ': 'Ü',
            # Signos
            'Â¿': '¿',
            'Â¡': '¡',
            # Comillas curvas
            'â€œ': '"',
            'â€': '"',
            # Comillas simples
            'â€™': "'",
            'â€˜': "'",
            # Guiones
            'â€"': '—',
            'â€"': '–',
            # Puntos suspensivos
            'â€¦': '…',
            # Palabras comunes mal codificadas
            'Ã³n': 'ón',
            'Ã¡s': 'ás',
            'Ã­a': 'ía',
            'ciÃ³n': 'ción',
            'tambiÃ©n': 'también',
            'mÃ¡s': 'más',
            'asÃ­': 'así',
            'categorÃ­a': 'categoría',
            'taxonomÃ­as': 'taxonomías',
            'informaciÃ³n': 'información',
            'secciÃ³n': 'sección',
            'descripciÃ³n': 'descripción',
            'exfiltraciÃ³n': 'exfiltración',
            'configuraciÃ³n': 'configuración',
            'aplicaciÃ³n': 'aplicación',
            'exposiciÃ³n': 'exposición',
            'gestiÃ³n': 'gestión',
            'validaciÃ³n': 'validación',
            'implementaciÃ³n': 'implementación',
            'documentaciÃ³n': 'documentación',
            'autenticaciÃ³n': 'autenticación',
            'actualizaciÃ³n': 'actualización',
            'eliminaciÃ³n': 'eliminación',
            'integraciÃ³n': 'integración',
            'mitigaciÃ³n': 'mitigación',
            'detecciÃ³n': 'detección',
            'prevenciÃ³n': 'prevención',
            'evaluaciÃ³n': 'evaluación',
            'remediaciÃ³n': 'remediación',
            'investigaciÃ³n': 'investigación',
            'clasificaciÃ³n': 'clasificación',
            'notificaciÃ³n': 'notificación'
        }
        
        # Agregar Ñ mayuscula usando Unicode
        replacements['Ã\u0091'] = 'Ñ'
        
        return replacements
    
    @classmethod
    def fix_text(cls, text):
        """
        Corrige el encoding de un texto
        """
        if not text or not isinstance(text, str):
            return text
        
        # Obtener reemplazos
        replacements = cls.get_replacements()
        
        # Aplicar reemplazos conocidos
        fixed_text = text
        for bad, good in replacements.items():
            fixed_text = fixed_text.replace(bad, good)
        
        # Intentar decodificar/recodificar si aún hay problemas
        try:
            # Si todavía tiene caracteres extraños, intentar fix más agresivo
            if 'Ã' in fixed_text or 'â€' in fixed_text:
                # Intentar interpretar como latin-1 y convertir a utf-8
                try:
                    bytes_text = fixed_text.encode('latin-1', errors='ignore')
                    fixed_text = bytes_text.decode('utf-8', errors='ignore')
                except:
                    pass
        except:
            pass
        
        return fixed_text
    
    @classmethod
    def fix_dict(cls, data):
        """
        Corrige recursivamente todos los strings en un diccionario
        """
        if isinstance(data, dict):
            return {k: cls.fix_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.fix_dict(item) for item in data]
        elif isinstance(data, str):
            return cls.fix_text(data)
        else:
            return data
    
    @classmethod
    def fix_database_row(cls, row_dict):
        """
        Corrige una fila completa de base de datos
        """
        return cls.fix_dict(row_dict)
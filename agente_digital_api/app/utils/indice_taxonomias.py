# indice_taxonomias.py
# Módulo de índice único para taxonomías

class IndiceUnico:
    """Clase para generar índices únicos"""
    
    @staticmethod
    def generar():
        """Genera un índice único simple"""
        import uuid
        return str(uuid.uuid4())[:8]
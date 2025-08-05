#!/usr/bin/env python3
"""
Punto de entrada para Railway
"""
import os
import sys

# Agregar el directorio de la API al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agente_digital_api'))

# Importar y crear la aplicación
from agente_digital_api.app import create_app

# Crear la aplicación
application = create_app()
app = application

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
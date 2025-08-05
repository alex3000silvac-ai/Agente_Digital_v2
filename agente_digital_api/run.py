#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Archivo principal para ejecutar la aplicación Flask API
Configurado para desarrollo y producción
"""

import sys
import os

# Agregar el directorio actual al path para las importaciones
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Función principal para ejecutar la aplicación"""
    try:
        # Importar y crear la aplicación
        from app import create_app
        
        # Detectar entorno
        flask_env = os.environ.get('FLASK_ENV', 'development').lower()
        
        if flask_env == 'production':
            print("ADVERTENCIA: Ejecutando en modo desarrollo")
            print("Para producción, usar Gunicorn: ./start_gunicorn.sh")
            print("=" * 50)
            
        print("Iniciando Agente Digital API...")
        print(f"Entorno: {flask_env}")
        print("Servidor: http://localhost:5000")
        
        if flask_env != 'production':
            print("Modo: Desarrollo (Debug)")
        
        print("=" * 40)
        
        app = create_app()
        
        # Configuración basada en entorno
        if flask_env == 'production':
            # En producción, NO usar el servidor de desarrollo
            print("ERROR: No usar run.py en producción")
            print("Usar Gunicorn: ./start_gunicorn.sh")
            sys.exit(1)
        else:
            # Desarrollo
            app.run(
                host='127.0.0.1',  # Solo localhost en desarrollo
                port=5000, 
                debug=True,
                use_reloader=True,
                threaded=True
            )
        
    except ImportError as e:
        print(f"Error de importación: {e}")
        print("Ejecuta primero: python test_imports.py")
        print("O instala dependencias: pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
        sys.exit(1)

# Variable para Gunicorn
app = None

def get_app():
    """Función para Gunicorn - crear la aplicación"""
    global app
    if app is None:
        from app import create_app
        app = create_app()
    return app

# Para Gunicorn
app = get_app()

if __name__ == '__main__':
    main()
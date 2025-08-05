#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script to verify Flask server status and start if needed"""

import os
import sys
import requests
import subprocess
import time

def check_port_5000():
    """Check if port 5000 is responding"""
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=2)
        return True, response.status_code
    except requests.exceptions.ConnectionError:
        return False, None
    except Exception as e:
        return False, str(e)

def main():
    print("=== Verificación del servidor Flask ===")
    print(f"Directorio actual: {os.getcwd()}")
    
    # Check if server is running
    is_running, status = check_port_5000()
    
    if is_running:
        print(f"✅ El servidor Flask está corriendo en el puerto 5000")
        print(f"   Estado HTTP: {status}")
    else:
        print("❌ El servidor Flask NO está corriendo en el puerto 5000")
        print("   Para iniciar el servidor, ejecuta:")
        print("   python3 run.py")
        print("\n   Nota: Hay un error de registro duplicado de blueprint 'informes_anci_completo'")
        print("   que necesita ser corregido en app/__init__.py")
    
    # Check for Python processes
    print("\n=== Procesos Python actuales ===")
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        python_processes = [line for line in result.stdout.split('\n') if 'python' in line.lower() and 'grep' not in line]
        if python_processes:
            for proc in python_processes[:5]:  # Show first 5
                print(proc[:120] + "..." if len(proc) > 120 else proc)
        else:
            print("No se encontraron procesos Python relacionados con Flask")
    except Exception as e:
        print(f"Error al verificar procesos: {e}")

if __name__ == "__main__":
    main()
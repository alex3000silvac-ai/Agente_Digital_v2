#!/usr/bin/env python3
"""
Script para instalar dependencias faltantes para desarrollo
"""

import subprocess
import sys
import os

def install_package(package):
    """Instalar un paquete usando pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} instalado correctamente")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Error instalando {package}")
        return False

def main():
    print("🔧 Instalando dependencias faltantes para Agente Digital...")
    
    # Lista de dependencias críticas
    critical_packages = [
        "python-dotenv>=1.0.0",
        "cryptography>=41.0.0",
        "python-magic>=0.4.27",
        "pyotp>=2.8.0",
        "qrcode[pil]>=7.4.2",
        "bleach>=6.0.0",
        "marshmallow>=3.20.0"
    ]
    
    # Dependencias para testing
    testing_packages = [
        "pytest>=7.4.0",
        "pytest-flask>=1.2.0",
        "pytest-cov>=4.1.0",
        "pytest-mock>=3.11.1",
        "pytest-asyncio>=0.21.1",
        "factory-boy>=3.3.0",
        "faker>=19.6.0",
        "coverage>=7.3.0"
    ]
    
    # Dependencias para performance testing
    performance_packages = [
        "locust>=2.17.0",
        "requests>=2.31.0",
        "psutil>=5.9.0"
    ]
    
    all_packages = critical_packages + testing_packages + performance_packages
    
    # Instalar cada paquete
    failed_packages = []
    for package in all_packages:
        if not install_package(package):
            failed_packages.append(package)
    
    # Resumen
    print("\n" + "="*50)
    print("📊 RESUMEN DE INSTALACIÓN")
    print("="*50)
    
    installed_count = len(all_packages) - len(failed_packages)
    print(f"✅ Paquetes instalados: {installed_count}/{len(all_packages)}")
    
    if failed_packages:
        print("❌ Paquetes fallidos:")
        for package in failed_packages:
            print(f"   - {package}")
    else:
        print("🎉 Todas las dependencias instaladas correctamente!")
    
    # Instalar python-magic-bin para Windows si es necesario
    if os.name == 'nt':  # Windows
        print("\n🔧 Detectado Windows, instalando python-magic-bin...")
        install_package("python-magic-bin>=0.4.14")
    
    print("\n🚀 ¡Listo! Ahora puedes ejecutar la aplicación sin errores.")

if __name__ == "__main__":
    main()
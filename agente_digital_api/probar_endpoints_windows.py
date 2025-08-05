#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 PRUEBA DE ENDPOINTS DESDE WINDOWS
Valida que el servidor puede leer los datos creados
"""

import requests
import json
from datetime import datetime

# URL del servidor (desde Windows)
BASE_URL = "http://localhost:5000"

def log(mensaje: str, nivel: str = "INFO"):
    """Registra mensajes con timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {nivel}: {mensaje}")

def probar_endpoint(url: str, descripcion: str):
    """Prueba un endpoint específico"""
    try:
        log("* Probando: {descripcion}")
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            log(f"[OK] {descripcion}: {len(data) if isinstance(data, list) else 'OK'} registros")
            return True, data
        else:
            log(f"[ERROR] {descripcion}: HTTP {response.status_code}", "ERROR")
            return False, None
            
    except Exception as e:
        log(f"❌ {descripcion}: {e}", "ERROR")
        return False, None

def main():
    """Función principal de pruebas"""
    log("* INICIANDO PRUEBAS DE ENDPOINTS")
    log("=" * 50)
    
    # Lista de endpoints a probar
    endpoints = [
        (f"{BASE_URL}/api/admin/inquilinos", "Listar Inquilinos"),
        (f"{BASE_URL}/api/admin/empresas", "Listar Empresas"),
        (f"{BASE_URL}/api/admin/inquilinos/3/empresas", "Empresas del Inquilino 3"),
        (f"{BASE_URL}/api/admin/empresas/2/incidentes", "Incidentes de Empresa 2"),
    ]
    
    resultados = []
    
    for url, desc in endpoints:
        exito, data = probar_endpoint(url, desc)
        resultados.append((desc, exito, data))
        
    # Resumen
    log("\n" + "=" * 50)
    log("* RESUMEN DE PRUEBAS")
    log("=" * 50)
    
    exitosos = sum(1 for _, exito, _ in resultados if exito)
    total = len(resultados)
    
    for desc, exito, data in resultados:
        estado = "[OK]" if exito else "[ERROR]"
        log(f"{estado} {desc}")
        
        # Mostrar algunos datos de ejemplo
        if exito and data and isinstance(data, list) and len(data) > 0:
            primer_item = data[0]
            if isinstance(primer_item, dict):
                # Mostrar las primeras 2 claves del primer item
                claves = list(primer_item.keys())[:2]
                ejemplo = {k: primer_item[k] for k in claves}
                log(f"    Ejemplo: {ejemplo}")
    
    log(f"\n* Resultado: {exitosos}/{total} endpoints funcionando")
    
    if exitosos == total:
        log("[OK] ¡TODOS LOS ENDPOINTS FUNCIONAN CORRECTAMENTE!")
        log("[OK] El sistema está listo para ambiente productivo")
    else:
        log("[ADVERTENCIA] Algunos endpoints presentan problemas")
        log("[INFO] Se requiere depuración adicional")

if __name__ == "__main__":
    main()
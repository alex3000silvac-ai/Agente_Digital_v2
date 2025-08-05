#!/usr/bin/env python3
"""
Script para validar que el sistema está listo para la migración de archivos.
"""

import os
import sys
from pathlib import Path

def check_backup():
    """Verificar que existe backup"""
    backup_dirs = [d for d in os.listdir('.') if d.startswith('backup_')]
    if not backup_dirs:
        return False, "No se encontró directorio de backup"
    
    latest_backup = max(backup_dirs)
    backup_files = os.listdir(latest_backup)
    
    expected_files = ['uploads_backup_', 'admin_views_original_', 'MANIFEST_']
    for expected in expected_files:
        if not any(f.startswith(expected) for f in backup_files):
            return False, f"Falta archivo de backup: {expected}*"
    
    return True, f"Backup válido encontrado: {latest_backup}"

def check_secure_code():
    """Verificar que el código seguro está en uso"""
    admin_views_path = 'app/admin_views.py'
    if not os.path.exists(admin_views_path):
        return False, "No se encontró app/admin_views.py"
    
    with open(admin_views_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar indicadores de código seguro
    security_indicators = [
        'get_user_organization',
        'verify_file_access',
        'requires_organization',
        'get_secure_upload_path',
        'BASE_UPLOAD_FOLDER'
    ]
    
    for indicator in security_indicators:
        if indicator not in content:
            return False, f"Función de seguridad no encontrada: {indicator}"
    
    return True, "Código seguro está implementado"

def check_uploads_directory():
    """Verificar estado de la carpeta uploads"""
    uploads_path = 'uploads'
    if not os.path.exists(uploads_path):
        return False, "Carpeta uploads no encontrada"
    
    # Contar archivos en raíz
    root_files = [f for f in os.listdir(uploads_path) if os.path.isfile(os.path.join(uploads_path, f))]
    
    # Verificar si ya hay estructura de inquilinos
    subdirs = [d for d in os.listdir(uploads_path) if os.path.isdir(os.path.join(uploads_path, d))]
    inquilino_dirs = [d for d in subdirs if d.startswith('inquilino_')]
    
    if inquilino_dirs:
        return True, f"Estructura segura ya implementada: {len(inquilino_dirs)} inquilinos, {len(root_files)} archivos en raíz"
    else:
        return True, f"Lista para migración: {len(root_files)} archivos en raíz"

def check_sql_readiness():
    """Verificar que los scripts SQL están listos"""
    sql_script = 'scripts_seguridad_archivos_multicliente.sql'
    if not os.path.exists(sql_script):
        return False, "Script SQL no encontrado"
    
    # Verificar contenido básico
    with open(sql_script, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_statements = [
        'ALTER TABLE dbo.EvidenciasCumplimiento ADD InquilinoID',
        'ALTER TABLE dbo.EvidenciasIncidentes ADD InquilinoID',
        'ALTER TABLE dbo.INCIDENTE_TAXONOMIA_EVIDENCIAS ADD InquilinoID'
    ]
    
    for statement in required_statements:
        if statement not in content:
            return False, f"Statement SQL faltante: {statement}"
    
    return True, "Scripts SQL están preparados (deben ejecutarse manualmente)"

def check_migration_script():
    """Verificar que el script de migración está listo"""
    migration_script = 'migrate_files_to_secure_structure.py'
    if not os.path.exists(migration_script):
        return False, "Script de migración no encontrado"
    
    run_script = 'run_migration.sh'
    if not os.path.exists(run_script):
        return False, "Script de ejecución no encontrado"
    
    return True, "Scripts de migración están listos"

def main():
    """Función principal de validación"""
    print("=== VALIDACIÓN DE PREPARACIÓN PARA MIGRACIÓN ===")
    print()
    
    checks = [
        ("Backup completo", check_backup),
        ("Código seguro implementado", check_secure_code),
        ("Carpeta uploads", check_uploads_directory),
        ("Scripts SQL preparados", check_sql_readiness),
        ("Scripts de migración", check_migration_script)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            passed, message = check_func()
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}: {message}")
            
            if not passed:
                all_passed = False
                
        except Exception as e:
            print(f"❌ {check_name}: Error - {str(e)}")
            all_passed = False
    
    print()
    
    if all_passed:
        print("🎉 SISTEMA LISTO PARA MIGRACIÓN")
        print()
        print("📋 PASOS SIGUIENTES:")
        print("1. Ejecutar scripts SQL en la base de datos:")
        print("   - Abrir SQL Server Management Studio")
        print("   - Ejecutar: scripts_seguridad_archivos_multicliente.sql")
        print()
        print("2. Ejecutar migración de archivos:")
        print("   ./run_migration.sh")
        print()
        print("3. Validar funcionalidad post-migración")
        
    else:
        print("⚠️  SISTEMA NO ESTÁ LISTO")
        print()
        print("🔧 CORRIJA LOS ERRORES ANTES DE CONTINUAR")
        print("   Revise los elementos marcados con ❌")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
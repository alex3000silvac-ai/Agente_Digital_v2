# validation_suite.py
# Suite de validación continua para prevenir errores futuros

import sys
import traceback
from typing import List, Dict, Any
from datetime import datetime

def validate_syntax(file_path: str) -> Dict[str, Any]:
    """Valida la sintaxis Python de un archivo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        compile(source, file_path, 'exec')
        return {
            "status": "valid",
            "file": file_path,
            "message": "Sintaxis Python válida"
        }
    except SyntaxError as e:
        return {
            "status": "error",
            "file": file_path,
            "message": f"Error de sintaxis: {e}",
            "line": e.lineno,
            "column": e.offset
        }
    except Exception as e:
        return {
            "status": "error",
            "file": file_path,
            "message": f"Error al validar: {e}"
        }

def validate_imports(file_path: str) -> Dict[str, Any]:
    """Valida que las importaciones estén disponibles"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        import_errors = []
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line.startswith('from ') or line.startswith('import '):
                try:
                    exec(line)
                except ImportError as e:
                    import_errors.append({
                        "line": i,
                        "import": line,
                        "error": str(e)
                    })
                except Exception:
                    pass  # Otras excepciones no importan para esta validación
        
        if import_errors:
            return {
                "status": "warning",
                "file": file_path,
                "message": f"Problemas de importación encontrados",
                "errors": import_errors
            }
        else:
            return {
                "status": "valid",
                "file": file_path,
                "message": "Todas las importaciones válidas"
            }
    except Exception as e:
        return {
            "status": "error",
            "file": file_path,
            "message": f"Error validando importaciones: {e}"
        }

def validate_flask_routes(file_path: str) -> Dict[str, Any]:
    """Valida que no haya rutas duplicadas en archivos Flask"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        import re
        
        # Buscar decoradores de rutas
        route_pattern = r'@\w+\.route\([\'"]([^\'"]+)[\'"]'
        routes = re.findall(route_pattern, content)
        
        # Buscar funciones duplicadas
        function_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        functions = re.findall(function_pattern, content)
        
        # Encontrar duplicados
        route_counts = {}
        for route in routes:
            route_counts[route] = route_counts.get(route, 0) + 1
        
        function_counts = {}
        for func in functions:
            function_counts[func] = function_counts.get(func, 0) + 1
        
        duplicated_routes = {k: v for k, v in route_counts.items() if v > 1}
        duplicated_functions = {k: v for k, v in function_counts.items() if v > 1}
        
        issues = []
        if duplicated_routes:
            issues.append(f"Rutas duplicadas: {duplicated_routes}")
        if duplicated_functions:
            issues.append(f"Funciones duplicadas: {duplicated_functions}")
        
        if issues:
            return {
                "status": "error",
                "file": file_path,
                "message": "Duplicados encontrados",
                "issues": issues
            }
        else:
            return {
                "status": "valid",
                "file": file_path,
                "message": f"Sin duplicados. {len(routes)} rutas, {len(functions)} funciones"
            }
    except Exception as e:
        return {
            "status": "error",
            "file": file_path,
            "message": f"Error validando rutas: {e}"
        }

def run_validation_suite(files: List[str]) -> Dict[str, Any]:
    """Ejecuta toda la suite de validación"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_files": len(files),
        "results": [],
        "summary": {
            "valid": 0,
            "warnings": 0,
            "errors": 0
        }
    }
    
    for file_path in files:
        print(f"🔍 Validando: {file_path}")
        
        # Validaciones múltiples para cada archivo
        validations = [
            validate_syntax(file_path),
            validate_imports(file_path),
            validate_flask_routes(file_path)
        ]
        
        file_result = {
            "file": file_path,
            "validations": validations
        }
        
        # Determinar estado general del archivo
        has_errors = any(v["status"] == "error" for v in validations)
        has_warnings = any(v["status"] == "warning" for v in validations)
        
        if has_errors:
            file_result["overall_status"] = "error"
            results["summary"]["errors"] += 1
        elif has_warnings:
            file_result["overall_status"] = "warning"
            results["summary"]["warnings"] += 1
        else:
            file_result["overall_status"] = "valid"
            results["summary"]["valid"] += 1
        
        results["results"].append(file_result)
    
    return results

if __name__ == "__main__":
    # Archivos críticos a validar
    critical_files = [
        "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api/app/admin_views.py",
        "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api/app/views/empresas_views.py",
        "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api/app/views/incidentes_views.py",
        "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api/app/views/cumplimiento_views.py",
        "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api/app/views/health_views.py",
        "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api/app/db_validator.py",
        "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api/app/error_handlers.py"
    ]
    
    print("🧪 INICIANDO SUITE DE VALIDACIÓN CONTINUA")
    print("=" * 50)
    
    results = run_validation_suite(critical_files)
    
    print("\n📊 RESUMEN DE VALIDACIÓN:")
    print(f"✅ Archivos válidos: {results['summary']['valid']}")
    print(f"⚠️ Archivos con advertencias: {results['summary']['warnings']}")
    print(f"❌ Archivos con errores: {results['summary']['errors']}")
    
    # Mostrar detalles de errores
    for file_result in results["results"]:
        if file_result["overall_status"] == "error":
            print(f"\n❌ ERRORES EN: {file_result['file']}")
            for validation in file_result["validations"]:
                if validation["status"] == "error":
                    print(f"  - {validation['message']}")
    
    # Código de salida para CI/CD
    sys.exit(0 if results['summary']['errors'] == 0 else 1)
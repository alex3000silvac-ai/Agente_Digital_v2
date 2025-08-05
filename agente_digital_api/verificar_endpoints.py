#!/usr/bin/env python3
"""
Script para verificar todos los endpoints registrados en la aplicación
"""

from app import create_app

app = create_app()

print("=== ENDPOINTS REGISTRADOS ===\n")

# Obtener todas las reglas ordenadas por endpoint
rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)

# Filtrar solo endpoints de incidentes
print("ENDPOINTS DE INCIDENTES:")
print("-" * 80)
for rule in rules:
    if 'incidente' in rule.rule.lower():
        methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"{rule.rule:<50} {methods:<10} -> {rule.endpoint}")

print("\n\nENDPOINTS ADMIN:")
print("-" * 80)
for rule in rules:
    if '/api/admin/' in rule.rule:
        methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"{rule.rule:<50} {methods:<10} -> {rule.endpoint}")

# Verificar específicamente el endpoint problemático
print("\n\nBUSCANDO ENDPOINT ESPECÍFICO: /api/admin/incidentes/<id>")
print("-" * 80)
for rule in rules:
    if '/api/admin/incidentes/' in rule.rule and '<int:' in rule.rule:
        print(f"✅ ENCONTRADO: {rule.rule} -> {rule.endpoint}")
        print(f"   Métodos: {', '.join(rule.methods)}")
        print(f"   Función: {app.view_functions.get(rule.endpoint)}")
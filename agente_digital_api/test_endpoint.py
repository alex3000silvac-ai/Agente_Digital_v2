#!/usr/bin/env python3
"""Test directo del endpoint"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Simular el entorno Flask
from app import create_app
from flask import Flask

# Crear la aplicación
app = create_app()

# Simular una petición
with app.test_client() as client:
    print("Haciendo petición a /api/admin/empresas/3/dashboard-stats...")
    response = client.get('/api/admin/empresas/3/dashboard-stats')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.get_json()}")
#!/usr/bin/env python3
"""Test simple para verificar que la app puede iniciar"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Agente Digital - Test OK"

@app.route('/health')
def health():
    return {"status": "ok"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
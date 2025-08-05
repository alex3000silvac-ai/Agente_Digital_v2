# gunicorn_config.py
# Configuración de Gunicorn para Agente Digital

import multiprocessing
import os

# Configuración del servidor
bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1  # Fórmula recomendada
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
timeout = 120
keepalive = 5

# Configuración de procesos
daemon = False
pidfile = "/tmp/agentedigital_gunicorn.pid"
user = None  # Se configurará por supervisor
group = None
tmp_upload_dir = None

# Logging
accesslog = "/home/agentedigital/logs/gunicorn_access.log"
errorlog = "/home/agentedigital/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Configuración de seguridad
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# Configuración de performance
worker_tmp_dir = "/dev/shm"  # Usar memoria compartida para mejor performance
graceful_timeout = 30
reload = False  # No usar en producción

# Variables de entorno
raw_env = [
    'FLASK_ENV=production',
]

# Hooks para startup/shutdown
def on_starting(server):
    server.log.info("Iniciando Agente Digital con Gunicorn")

def on_reload(server):
    server.log.info("Recargando configuración de Gunicorn")

def when_ready(server):
    server.log.info("Agente Digital listo para recibir conexiones")

def worker_int(worker):
    worker.log.info("Worker interrumpido por SIGINT")

def pre_fork(server, worker):
    server.log.info("Worker %s iniciando", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker %s iniciado", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker %s abortado", worker.pid)
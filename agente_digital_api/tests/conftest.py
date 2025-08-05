# tests/conftest.py
# Configuración global de pytest y fixtures compartidos

import pytest
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config_testing import TestingConfig

@pytest.fixture(scope="session")
def app():
    """Fixture de aplicación Flask para toda la sesión de testing"""
    
    # Configurar variables de entorno para testing
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'true'
    
    # Crear aplicación con configuración de testing
    app = create_app(TestingConfig)
    
    # Configurar contexto de aplicación
    with app.app_context():
        yield app

@pytest.fixture(scope="function")
def client(app):
    """Fixture de cliente de testing para cada test"""
    return app.test_client()

@pytest.fixture(scope="function")
def runner(app):
    """Fixture de runner CLI para cada test"""
    return app.test_cli_runner()

@pytest.fixture(scope="function")
def temp_dir():
    """Fixture de directorio temporal para cada test"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="function")
def mock_db():
    """Fixture de base de datos mock"""
    with patch('app.database.get_db_connection') as mock_conn:
        # Configurar mock de conexión
        mock_connection = Mock()
        mock_cursor = Mock()
        
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        mock_cursor.fetchall.return_value = []
        mock_cursor.execute.return_value = None
        
        mock_conn.return_value = mock_connection
        
        yield {
            'connection': mock_connection,
            'cursor': mock_cursor,
            'get_connection': mock_conn
        }

@pytest.fixture(scope="function")
def mock_redis():
    """Fixture de Redis mock"""
    with patch('redis.Redis') as mock_redis_class:
        mock_redis_instance = Mock()
        
        # Configurar métodos básicos de Redis
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = None
        mock_redis_instance.set.return_value = True
        mock_redis_instance.delete.return_value = 1
        mock_redis_instance.exists.return_value = False
        mock_redis_instance.ttl.return_value = -1
        mock_redis_instance.expire.return_value = True
        
        mock_redis_class.return_value = mock_redis_instance
        
        yield mock_redis_instance

@pytest.fixture(scope="function")
def sample_user_data():
    """Fixture con datos de usuario de ejemplo"""
    return {
        'user_id': 1,
        'username': 'testuser',
        'email': 'test@example.com',
        'nombre': 'Usuario Test',
        'apellido': 'Apellido Test',
        'empresa_id': 1,
        'inquilino_id': 1,
        'role': 'user',
        'activo': True
    }

@pytest.fixture(scope="function")
def sample_empresa_data():
    """Fixture con datos de empresa de ejemplo"""
    return {
        'empresa_id': 1,
        'nombre': 'Empresa Test S.A.',
        'rut': '12345678-9',
        'direccion': 'Dirección Test 123',
        'telefono': '+56912345678',
        'email': 'contacto@empresatest.cl',
        'inquilino_id': 1,
        'activo': True
    }

@pytest.fixture(scope="function")
def sample_incidente_data():
    """Fixture con datos de incidente de ejemplo"""
    return {
        'titulo': 'Incidente de Prueba',
        'descripcion': 'Descripción detallada del incidente de prueba',
        'criticidad': 'Media',
        'estado': 'Abierto',
        'empresa_id': 1,
        'usuario_creador_id': 1,
        'fecha_creacion': '2024-07-06 10:00:00'
    }

@pytest.fixture(scope="function")
def auth_headers(sample_user_data):
    """Fixture con headers de autenticación para tests"""
    # En un escenario real, aquí generarías un JWT válido
    # Para testing, usamos un header mock
    return {
        'Authorization': 'Bearer test-jwt-token',
        'Content-Type': 'application/json'
    }

@pytest.fixture(scope="function")
def admin_headers():
    """Fixture con headers de administrador para tests"""
    return {
        'Authorization': 'Bearer admin-jwt-token',
        'Content-Type': 'application/json',
        'X-Admin-Key': 'test-admin-key'
    }

@pytest.fixture
def mock_file_upload():
    """Fixture para mock de archivo subido"""
    from io import BytesIO
    from werkzeug.datastructures import FileStorage
    
    file_content = b"Este es el contenido de un archivo de prueba"
    file_like = BytesIO(file_content)
    
    return FileStorage(
        stream=file_like,
        filename="test_file.txt",
        content_type="text/plain",
        content_length=len(file_content)
    )

@pytest.fixture
def mock_email():
    """Fixture para mock de envío de emails"""
    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        mock_server.starttls.return_value = None
        mock_server.login.return_value = None
        mock_server.sendmail.return_value = {}
        
        yield mock_server

# Fixtures para testing de performance
@pytest.fixture
def performance_timer():
    """Fixture para medir tiempo de ejecución"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()

# Fixtures para testing de seguridad
@pytest.fixture
def malicious_payloads():
    """Fixture con payloads maliciosos para testing de seguridad"""
    return {
        'sql_injection': [
            "'; DROP TABLE usuarios; --",
            "1' OR '1'='1",
            "admin'--",
            "1; SELECT * FROM usuarios",
            "' UNION SELECT password FROM usuarios--"
        ],
        'xss': [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "'\"><script>alert('XSS')</script>"
        ],
        'path_traversal': [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ],
        'command_injection': [
            "; ls -la",
            "| cat /etc/passwd",
            "&& whoami",
            "`id`",
            "$(cat /etc/passwd)"
        ]
    }

# Helpers para testing
class TestHelpers:
    """Clase con métodos helper para testing"""
    
    @staticmethod
    def assert_response_ok(response):
        """Assert que la respuesta es exitosa"""
        assert response.status_code in [200, 201, 204], f"Response status: {response.status_code}, Data: {response.get_data()}"
    
    @staticmethod
    def assert_response_error(response, expected_status=400):
        """Assert que la respuesta es un error"""
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"
    
    @staticmethod
    def assert_json_contains(response, key, value=None):
        """Assert que el JSON de respuesta contiene una clave específica"""
        json_data = response.get_json()
        assert json_data is not None, "Response is not JSON"
        assert key in json_data, f"Key '{key}' not found in response"
        if value is not None:
            assert json_data[key] == value, f"Expected {value}, got {json_data[key]}"
    
    @staticmethod
    def assert_security_headers(response):
        """Assert que la respuesta tiene headers de seguridad"""
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options'
        ]
        
        for header in security_headers:
            assert header in response.headers, f"Security header '{header}' missing"

@pytest.fixture
def helpers():
    """Fixture con métodos helper para testing"""
    return TestHelpers

# Configuración para diferentes tipos de tests
def pytest_configure(config):
    """Configuración global de pytest"""
    # Configurar logging para tests
    import logging
    logging.getLogger("app").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

def pytest_collection_modifyitems(config, items):
    """Modificar items de tests antes de ejecutar"""
    for item in items:
        # Marcar tests lentos automáticamente
        if "slow" in item.name or "performance" in item.name:
            item.add_marker(pytest.mark.slow)
        
        # Marcar tests de base de datos
        if "db" in item.name or "database" in item.name:
            item.add_marker(pytest.mark.database)
        
        # Marcar tests de API
        if "api" in item.name or item.fspath.basename.startswith("test_api"):
            item.add_marker(pytest.mark.api)

# Cleanup después de todos los tests
@pytest.fixture(scope="session", autouse=True)
def cleanup():
    """Cleanup automático después de todos los tests"""
    yield
    
    # Limpiar archivos temporales
    temp_dirs = ['/tmp/agentedigital_test_uploads', '/tmp/agentedigital_test.log']
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            try:
                if os.path.isdir(temp_dir):
                    shutil.rmtree(temp_dir)
                else:
                    os.remove(temp_dir)
            except OSError:
                pass
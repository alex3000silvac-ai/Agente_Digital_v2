# Guía de Testing - Agente Digital

## 🧪 Estrategia de Testing Comprehensivo

Esta guía describe la estrategia de testing implementada para asegurar la calidad, seguridad y rendimiento del sistema Agente Digital.

---

## 📋 Tipos de Tests Implementados

### 1. Tests Unitarios (`tests/unit/`)
**Objetivo:** Verificar funcionamiento de componentes individuales

**Cobertura:**
- ✅ Creación y configuración de aplicación
- ✅ Validadores de seguridad
- ✅ Funciones de utilidad
- ✅ Modelos de datos
- ✅ Lógica de negocio

**Ejemplos:**
```bash
# Ejecutar solo tests unitarios
pytest tests/unit/ -v

# Tests específicos
pytest tests/unit/test_app_creation.py::TestAppCreation::test_app_creation_with_testing_config -v
```

### 2. Tests de Integración (`tests/integration/`)
**Objetivo:** Verificar interacción entre componentes

**Cobertura:**
- ✅ Endpoints de API
- ✅ Configuración CORS
- ✅ Manejo de errores
- ✅ Headers de seguridad
- ✅ Performance básica

**Ejemplos:**
```bash
# Ejecutar tests de integración
pytest tests/integration/ -v

# Tests de API específicos
pytest tests/integration/test_api_endpoints.py -v
```

### 3. Tests de Seguridad (`tests/security/`)
**Objetivo:** Detectar vulnerabilidades y verificar medidas de seguridad

**Cobertura:**
- ✅ Prevención de SQL Injection
- ✅ Prevención de XSS
- ✅ Prevención de Path Traversal
- ✅ Prevención de Command Injection
- ✅ Seguridad de autenticación
- ✅ Validación de entrada
- ✅ Headers de seguridad

**Ejemplos:**
```bash
# Ejecutar tests de seguridad
pytest tests/security/ -v

# Tests específicos de vulnerabilidades
pytest tests/security/test_security_vulnerabilities.py::TestSQLInjectionPrevention -v
```

### 4. Tests de Performance (`tests/performance/`)
**Objetivo:** Verificar rendimiento y escalabilidad

**Cobertura:**
- ✅ Tiempo de respuesta de endpoints
- ✅ Requests concurrentes
- ✅ Uso de memoria
- ✅ Detección de memory leaks
- ✅ Tests de carga básicos

**Ejemplos:**
```bash
# Ejecutar tests de performance
pytest tests/performance/ -v

# Tests de carga específicos
pytest tests/performance/test_basic_performance.py::TestLoadTesting -v
```

---

## 🛠️ Configuración del Entorno de Testing

### Estructura de Archivos
```
tests/
├── conftest.py                     # Configuración global y fixtures
├── pytest.ini                     # Configuración de pytest
├── unit/
│   ├── test_app_creation.py       # Tests de creación de app
│   └── test_security_validators.py # Tests de validadores
├── integration/
│   └── test_api_endpoints.py      # Tests de endpoints API
├── security/
│   └── test_security_vulnerabilities.py # Tests de seguridad
├── performance/
│   └── test_basic_performance.py  # Tests de performance
└── fixtures/                      # Datos de prueba
```

### Configuración de pytest (`pytest.ini`)
```ini
[tool:pytest]
testpaths = tests
markers =
    unit: Tests unitarios
    integration: Tests de integración
    security: Tests de seguridad
    performance: Tests de rendimiento
    slow: Tests que tardan más de 1 segundo
    database: Tests que requieren conexión a base de datos

addopts = 
    --strict-markers
    --verbose
    --cov=app
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=80
```

### Fixtures Disponibles (`conftest.py`)
- `app`: Aplicación Flask configurada para testing
- `client`: Cliente de testing Flask
- `mock_db`: Base de datos mockeada
- `mock_redis`: Redis mockeado
- `sample_user_data`: Datos de usuario de ejemplo
- `auth_headers`: Headers de autenticación
- `malicious_payloads`: Payloads maliciosos para tests de seguridad
- `performance_timer`: Timer para medir performance

---

## ⚡ Ejecución de Tests

### Comandos Básicos

```bash
# Ejecutar todos los tests
pytest

# Ejecutar con verbose
pytest -v

# Ejecutar tests específicos por marca
pytest -m unit
pytest -m integration  
pytest -m security
pytest -m performance

# Ejecutar tests específicos por archivo
pytest tests/unit/test_app_creation.py
pytest tests/security/test_security_vulnerabilities.py

# Ejecutar test específico
pytest tests/unit/test_app_creation.py::TestAppCreation::test_app_has_required_config

# Ejecutar tests excluyendo lentos
pytest -m "not slow"

# Ejecutar solo tests rápidos
pytest -m "not slow and not performance"
```

### Ejecución con Coverage

```bash
# Ejecutar con reporte de cobertura
pytest --cov=app --cov-report=html

# Ver reporte en navegador
open htmlcov/index.html

# Reporte en terminal
pytest --cov=app --cov-report=term-missing

# Fallar si cobertura es menor a 80%
pytest --cov=app --cov-fail-under=80
```

### Ejecución Paralela (si pytest-xdist está disponible)

```bash
# Ejecutar en paralelo con múltiples workers
pytest -n auto

# Ejecutar con número específico de workers
pytest -n 4
```

---

## 📊 Métricas de Calidad

### Objetivos de Cobertura
- **Cobertura general:** ≥ 80%
- **Código crítico:** ≥ 95%
- **Módulos de seguridad:** 100%
- **Endpoints API:** ≥ 90%

### Métricas de Performance
- **Health endpoint:** < 50ms
- **API endpoints:** < 500ms
- **Requests concurrentes:** 100+ RPS
- **Memory leaks:** < 5MB crecimiento en 100 requests

### Criterios de Seguridad
- ✅ 0 vulnerabilidades SQL injection
- ✅ 0 vulnerabilidades XSS  
- ✅ 0 path traversal
- ✅ 0 command injection
- ✅ Headers de seguridad presentes
- ✅ Validación de entrada robusta

---

## 🔧 Testing en Diferentes Entornos

### Entorno de Desarrollo Local

```bash
# Con dependencias completas
export FLASK_ENV=development
pytest

# Sin dependencias avanzadas (modo fallback)
export FLASK_ENV=testing
pytest
```

### Entorno de CI/CD

```bash
# Para GitHub Actions / Jenkins
export FLASK_ENV=testing
export CI=true
pytest -v --junitxml=test-results.xml --cov=app --cov-report=xml
```

### Testing de Producción (Smoke Tests)

```bash
# Tests básicos en producción
pytest tests/integration/test_api_endpoints.py::TestHealthEndpoints -v
```

---

## 🐛 Debugging de Tests

### Ejecutar Tests con Debug

```bash
# Ejecutar con output completo
pytest -s -v

# Parar en primer fallo
pytest -x

# Parar después de N fallos
pytest --maxfail=3

# Ejecutar último test fallido
pytest --lf

# Ejecutar tests fallidos y nuevos
pytest --ff
```

### Logging en Tests

```python
import logging

def test_with_logging(caplog):
    with caplog.at_level(logging.INFO):
        # Tu código de test
        pass
    
    assert "Expected log message" in caplog.text
```

### Debugging de Performance

```python
def test_performance_debug(client, performance_timer):
    performance_timer.start()
    response = client.get('/api/slow-endpoint')
    performance_timer.stop()
    
    print(f"Response time: {performance_timer.elapsed:.3f}s")
    
    # Agregar breakpoint si es muy lento
    if performance_timer.elapsed > 1.0:
        import pdb; pdb.set_trace()
```

---

## 📈 Reportes y Análisis

### Reporte de Cobertura HTML
```bash
pytest --cov=app --cov-report=html
# Abre htmlcov/index.html para ver reporte detallado
```

### Reporte de Performance
```bash
# Con reporte de duración de tests
pytest --durations=10

# Tests más lentos
pytest --durations=0
```

### Análisis de Fallos
```bash
# Reporte detallado de fallos
pytest --tb=long

# Reporte con líneas de código
pytest --tb=line

# Sin traceback
pytest --tb=no
```

---

## 🔄 Integración con CI/CD

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        export FLASK_ENV=testing
        pytest -v --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

### Jenkins Pipeline
```groovy
pipeline {
    agent any
    
    stages {
        stage('Test') {
            steps {
                sh '''
                    export FLASK_ENV=testing
                    python -m pytest -v --junitxml=test-results.xml --cov=app --cov-report=xml
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                    publishCoverage adapters: [coberturaAdapter('coverage.xml')]
                }
            }
        }
    }
}
```

---

## 🚀 Tests de Carga Avanzados

### Con Locust (opcional)
```python
# locustfile.py
from locust import HttpUser, task, between

class AgenteDigitalUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def health_check(self):
        self.client.get("/health")
    
    @task(1)  
    def api_endpoints(self):
        self.client.get("/api/admin/inquilinos")
```

```bash
# Ejecutar test de carga
locust -f locustfile.py --host=http://localhost:5000
```

---

## 🎯 Best Practices

### Escribir Tests Efectivos

1. **AAA Pattern (Arrange, Act, Assert)**
```python
def test_user_creation():
    # Arrange
    user_data = {"name": "Test User", "email": "test@example.com"}
    
    # Act
    response = client.post('/api/users', json=user_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()['name'] == "Test User"
```

2. **Tests Independientes**
```python
# ❌ Malo - tests dependientes
def test_create_user():
    global user_id
    user_id = create_user()

def test_update_user():
    update_user(user_id)  # Depende del test anterior

# ✅ Bueno - tests independientes
def test_create_user(sample_user_data):
    user_id = create_user(sample_user_data)
    assert user_id is not None

def test_update_user(sample_user_data):
    user_id = create_user(sample_user_data)
    result = update_user(user_id, {"name": "Updated"})
    assert result.success
```

3. **Nombres Descriptivos**
```python
# ❌ Malo
def test_user():
    pass

# ✅ Bueno  
def test_create_user_with_valid_data_returns_201():
    pass

def test_create_user_with_invalid_email_returns_400():
    pass
```

4. **Mocking Apropiado**
```python
def test_send_email(mock_email):
    # No enviar emails reales en tests
    with patch('app.email_service.send_email') as mock_send:
        mock_send.return_value = True
        
        result = send_welcome_email("test@example.com")
        
        assert result is True
        mock_send.assert_called_once()
```

### Mantenimiento de Tests

1. **Revisar tests fallidos regularmente**
2. **Actualizar tests cuando cambie la funcionalidad**
3. **Eliminar tests obsoletos**
4. **Mantener fixtures actualizadas**
5. **Documentar tests complejos**

---

## 📞 Soporte y Recursos

### Documentación Adicional
- [pytest Documentation](https://docs.pytest.org/)
- [Flask Testing](https://flask.palletsprojects.com/en/2.0.x/testing/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

### Comandos de Resolución de Problemas

```bash
# Limpiar cache de pytest
pytest --cache-clear

# Ejecutar tests sin cache
pytest -p no:cacheprovider

# Verbose máximo para debugging
pytest -vvv

# Ver configuración de pytest
pytest --collect-only

# Listar todos los marcadores
pytest --markers
```

---

## ✅ Checklist de Testing

### Antes de Commit
- [ ] Todos los tests pasan localmente
- [ ] Cobertura ≥ 80%
- [ ] Tests de seguridad pasan
- [ ] No hay tests skipped sin justificación
- [ ] Performance tests dentro de límites

### Antes de Release
- [ ] Suite completa de tests ejecutada
- [ ] Tests de integración completos
- [ ] Tests de carga ejecutados
- [ ] Security scanning completado
- [ ] Smoke tests en staging

### Monitoreo Continuo
- [ ] Tests ejecutándose en CI/CD
- [ ] Métricas de cobertura monitoreadas
- [ ] Performance tracking activo
- [ ] Security tests automatizados
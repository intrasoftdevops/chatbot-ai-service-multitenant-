# 🧪 Guía de Testing - Chatbot AI Service Multi-Tenant

## 📋 Descripción

Esta guía explica cómo ejecutar y mantener los tests del sistema de clasificación de intenciones políticas. Los tests validan todas las 12 categorías de intenciones y sus acciones correspondientes.

## 🏗️ Estructura de Tests

```
tests/
├── conftest.py                    # Configuración y fixtures de pytest
├── test_intent_classification.py  # Tests de clasificación de intenciones
├── test_action_handlers.py        # Tests de manejadores de acciones
├── test_tenant_integration.py     # Tests de integración con tenants
├── test_api_endpoints.py          # Tests de endpoints de la API
└── __init__.py                    # Package marker
```

## 🎯 Categorías de Tests

### Tests Unitarios
- **Clasificación de Intenciones**: Valida que cada categoría se clasifique correctamente
- **Manejadores de Acciones**: Verifica que las acciones se ejecuten según la intención
- **Configuración de Tenants**: Prueba diferentes configuraciones por tenant

### Tests de Integración
- **Flujo Completo**: Clasificación + Acción + Respuesta
- **Multi-Tenant**: Diferentes tenants con configuraciones específicas
- **APIs**: Endpoints de la API con mocks y casos reales

## 🚀 Ejecutar Tests

### Instalación de Dependencias
```bash
# Instalar dependencias de testing
python run_tests.py --install-deps

# O manualmente
pip install pytest pytest-asyncio pytest-cov httpx fastapi[all]
```

### Ejecución Básica
```bash
# Ejecutar todos los tests
python run_tests.py

# Tests con output detallado
python run_tests.py --verbose

# Tests con reporte de cobertura
python run_tests.py --coverage
```

### Tipos de Tests Específicos
```bash
# Solo tests unitarios
python run_tests.py --type unit

# Solo tests de integración
python run_tests.py --type integration

# Tests rápidos (sin tests lentos)
python run_tests.py --type fast

# Tests específicos
python run_tests.py --type specific
```

### Ejecución Directa con pytest
```bash
# Tests específicos
pytest tests/test_intent_classification.py::TestIntentClassification::test_malicious_intent_classification -v

# Tests con marcadores
pytest -m "not slow" -v
pytest -m integration -v
pytest -m unit -v

# Tests con cobertura
pytest --cov=chatbot_ai_service --cov-report=html
```

## 📊 Categorías de Intenciones Validadas

| Categoría | Test Cases | Validaciones |
|-----------|------------|--------------|
| **malicioso** | 4 ejemplos | Clasificación correcta, bloqueo de usuario |
| **cita_campaña** | 5 ejemplos | Redirección a Calendly |
| **saludo_apoyo** | 5 ejemplos | Respuesta de gratitud, compartir links |
| **publicidad_info** | 4 ejemplos | Redirección a formularios |
| **conocer_candidato** | 5 ejemplos | Redirección a DQBot, notificación ciudad |
| **actualizacion_datos** | 4 ejemplos | Actualización dinámica de datos |
| **solicitud_funcional** | 4 ejemplos | Info de puntos/tribu/referidos |
| **colaboracion_voluntariado** | 4 ejemplos | Clasificación por áreas (9 opciones) |
| **quejas** | 4 ejemplos | Registro en base de datos |
| **lider** | 4 ejemplos | Registro en base de datos de leads |
| **atencion_humano** | 4 ejemplos | Redirección a voluntario humano |
| **atencion_equipo_interno** | 4 ejemplos | Validación permisos, BackOffice |

## 🔧 Configuración de Tests

### Fixtures Principales
- **sample_messages**: Mensajes de ejemplo para cada categoría
- **sample_tenant_configs**: Configuraciones de tenant (activo, inactivo, sin IA, sin links)
- **mock_tenant_service**: Mock del servicio de tenants
- **mock_ai_service**: Mock del servicio de IA
- **mock_firebase_config**: Mock de configuración de Firebase

### Marcadores de Tests
- `@pytest.mark.unit`: Tests unitarios
- `@pytest.mark.integration`: Tests de integración
- `@pytest.mark.slow`: Tests que toman más tiempo
- `@pytest.mark.ai`: Tests que requieren servicios de IA
- `@pytest.mark.firebase`: Tests que requieren conexión a Firebase

## 📈 Métricas de Cobertura

### Objetivos de Cobertura
- **Líneas de código**: > 90%
- **Funciones**: > 95%
- **Clases**: > 90%
- **Branches**: > 85%

### Generar Reporte de Cobertura
```bash
# HTML report
pytest --cov=chatbot_ai_service --cov-report=html

# Terminal report
pytest --cov=chatbot_ai_service --cov-report=term-missing

# XML report (para CI/CD)
pytest --cov=chatbot_ai_service --cov-report=xml
```

## 🐛 Debugging Tests

### Tests Failing
```bash
# Ver detalles del error
pytest tests/test_intent_classification.py::test_malicious_intent_classification -v -s

# Ver solo el primer test que falla
pytest -x

# Ver output de print statements
pytest -s
```

### Logs Detallados
```bash
# Con logs de la aplicación
pytest --log-cli-level=DEBUG

# Con logs específicos
pytest --log-cli-level=INFO --log-cli-format="%(asctime)s [%(levelname)8s] %(message)s"
```

## 🔄 CI/CD Integration

### GitHub Actions (ejemplo)
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
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run tests
        run: pytest --cov=chatbot_ai_service --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## 📝 Escribir Nuevos Tests

### Estructura de un Test
```python
@pytest.mark.asyncio
async def test_new_intent_category(self, intent_classification_service):
    """Test para nueva categoría de intención"""
    request = ClassificationRequest(
        message="Mensaje de ejemplo",
        tenant_id="test_tenant",
        user_context={"phone": "+573001234567"}
    )
    
    classification = await intent_classification_service.classify_intent(request)
    
    assert classification.category == IntentCategory.NUEVA_CATEGORIA
    assert classification.confidence > 0.5
    assert classification.action.action_type == "nueva_accion"
```

### Mejores Prácticas
1. **Usar fixtures** para configuración común
2. **Mockear servicios externos** (Firebase, IA)
3. **Testear casos edge** (tenant inactivo, errores)
4. **Validar tanto éxito como fallos**
5. **Usar nombres descriptivos** para tests
6. **Agrupar tests relacionados** en clases

## 🚨 Troubleshooting

### Problemas Comunes

#### ImportError
```bash
# Agregar path del proyecto
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src/main/python"
```

#### Tests Asyncio
```python
# Usar pytest-asyncio
pip install pytest-asyncio
```

#### Mock Issues
```python
# Verificar que el mock está configurado correctamente
from unittest.mock import AsyncMock, patch
```

## 📊 Resultados Esperados

### Ejecución Exitosa
```
========================= test session starts =========================
tests/test_intent_classification.py::TestIntentClassification::test_malicious_intent_classification PASSED
tests/test_intent_classification.py::TestIntentClassification::test_campaign_appointment_classification PASSED
...
========================= 48 passed in 2.34s =========================
```

### Cobertura Objetivo
```
Name                                                    Stmts   Miss  Cover
---------------------------------------------------------------------
chatbot_ai_service/services/intent_classification_service.py     95      5    95%
chatbot_ai_service/services/action_handler_service.py           120     12    90%
chatbot_ai_service/controllers/classification_controller.py      85      8    91%
---------------------------------------------------------------------
TOTAL                                                             300     25    92%
```

¡Los tests están listos para validar todo el sistema de clasificación de intenciones políticas! 🎯


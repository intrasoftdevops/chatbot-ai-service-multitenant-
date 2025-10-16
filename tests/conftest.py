"""
Configuración de pytest para los tests del sistema de clasificación de intenciones
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
import os
import sys

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'main', 'python'))

@pytest.fixture(scope="session")
def event_loop():
    """Crear un event loop para toda la sesión de tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_messages():
    """Mensajes de ejemplo para testing"""
    return {
        "malicious": [
            "Son unos ladrones",
            "Esto es una estafa",
            "Van a perder las elecciones",
            "Spam spam spam"
        ],
        "appointment": [
            "Quiero agendar una cita con el candidato",
            "¿Cuándo pueden visitar mi barrio?",
            "Necesito coordinar una reunión",
            "¿Pueden venir a mi casa?"
        ],
        "support": [
            "Hola, apoyo al candidato",
            "Cuenten conmigo",
            "Vamos a ganar",
            "Candidato para presidente"
        ],
        "advertising": [
            "Necesito material publicitario",
            "¿Tienen afiches?",
            "Quiero difundir la campaña",
            "¿Cómo consigo volantes?"
        ],
        "know_candidate": [
            "¿Quién es el candidato?",
            "¿Cuáles son sus propuestas?",
            "¿Qué ha hecho el candidato?",
            "Quiero conocer más del candidato"
        ],
        "data_update": [
            "Quiero cambiar mi teléfono",
            "Mi dirección cambió",
            "Actualizar mis datos",
            "Corregir mi información"
        ],
        "functional": [
            "¿Cómo voy?",
            "¿Cuántos puntos tengo?",
            "Link de mi tribu",
            "¿Cómo funciona esto?"
        ],
        "volunteer": [
            "Quiero ser voluntario",
            "¿Cómo puedo ayudar?",
            "Me ofrezco para la campaña",
            "¿Necesitan ayuda?"
        ],
        "complaint": [
            "No me gusta esto",
            "Esto está mal",
            "Tengo una queja",
            "No estoy de acuerdo"
        ],
        "leader": [
            "Soy líder comunal",
            "Represento a mi barrio",
            "Soy dirigente político",
            "Lidero una organización"
        ],
        "human_attention": [
            "Quiero hablar con una persona",
            "¿Hay alguien disponible?",
            "Necesito atención humana",
            "¿Puedo hablar con un agente?"
        ],
        "internal_team": [
            "¿Cuánta gente hay en Chocó?",
            "¿Cuántos voluntarios hay en Bogotá?",
            "Necesito reportes",
            "Estadísticas de mi zona"
        ]
    }

@pytest.fixture
def sample_tenant_configs():
    """Configuraciones de tenant de ejemplo"""
    from chatbot_ai_service.models.tenant_models import (
        TenantConfig, TenantStatus, BrandingConfig, FeaturesConfig, 
        IntegrationsConfig, AIConfig
    )
    
    return {
        "active_tenant": TenantConfig(
            tenant_id="active_tenant",
            tenant_type="political",
            client_project_id="active_project",
            status=TenantStatus.ACTIVE,
            branding=BrandingConfig(
                welcome_message="¡Bienvenido a nuestra campaña activa!",
                primary_color="#1E40AF",
                secondary_color="#3B82F6"
            ),
            features=FeaturesConfig(
                ai_enabled=True,
                analytics_enabled=True,
                referrals_enabled=True
            ),
            integrations=IntegrationsConfig(
                wati={"api_token": "wati_token_active"}
            ),
            ai_config=AIConfig(
                model="gemini-pro",
                temperature=0.7,
                max_tokens=1000,
                enable_rag=True
            ),
            link_calendly="https://calendly.com/active-tenant",
            link_forms="https://forms.gle/active-tenant"
        ),
        
        "inactive_tenant": TenantConfig(
            tenant_id="inactive_tenant",
            tenant_type="political",
            client_project_id="inactive_project",
            status=TenantStatus.INACTIVE,
            branding=BrandingConfig(
                welcome_message="Campaña inactiva",
                primary_color="#6B7280"
            ),
            features=FeaturesConfig(
                ai_enabled=False,
                analytics_enabled=False
            )
        ),
        
        "tenant_no_ai": TenantConfig(
            tenant_id="tenant_no_ai",
            tenant_type="political",
            client_project_id="no_ai_project",
            status=TenantStatus.ACTIVE,
            features=FeaturesConfig(
                ai_enabled=False,
                analytics_enabled=True
            )
        ),
        
        "tenant_no_links": TenantConfig(
            tenant_id="tenant_no_links",
            tenant_type="political",
            client_project_id="no_links_project",
            status=TenantStatus.ACTIVE,
            features=FeaturesConfig(
                ai_enabled=True,
                analytics_enabled=True
            ),
            link_calendly=None,
            link_forms=None
        )
    }

@pytest.fixture
def mock_firebase_config():
    """Mock de configuración de Firebase"""
    config = Mock()
    config.firestore = Mock()
    config.project_id = "test-project"
    config.database_id = "(default)"
    config.get_tenant_config_collection.return_value = "clientes"
    config.get_conversations_collection.return_value = "conversations"
    config.get_classifications_collection.return_value = "classifications"
    return config

@pytest.fixture
def mock_tenant_service(sample_tenant_configs):
    """Mock del servicio de tenants"""
    service = AsyncMock()
    
    async def get_tenant_config(tenant_id):
        return sample_tenant_configs.get(tenant_id)
    
    async def is_tenant_active(tenant_id):
        config = sample_tenant_configs.get(tenant_id)
        return config and config.status == TenantStatus.ACTIVE
    
    service.get_tenant_config.side_effect = get_tenant_config
    service.is_tenant_active.side_effect = is_tenant_active
    
    return service

@pytest.fixture
def mock_ai_service():
    """Mock del servicio de IA"""
    service = AsyncMock()
    
    # Mock de respuesta de IA genérica
    ai_response = Mock()
    ai_response.intent = "general"
    ai_response.confidence = 0.8
    ai_response.entities = {}
    ai_response.fallback = False
    
    service.classify_intent.return_value = ai_response
    service.extract_user_data.return_value = Mock(
        extracted_data={},
        confidence=0.5,
        fallback=True
    )
    
    return service

@pytest.fixture
def mock_conversation_service():
    """Mock del servicio de conversaciones"""
    service = AsyncMock()
    
    # Mock de conversación
    conversation = Mock()
    conversation.conversation_id = "test_conv_123"
    conversation.tenant_id = "test_tenant"
    conversation.session_id = "test_session"
    conversation.phone = "+573001234567"
    conversation.messages = []
    conversation.current_state = "NEW"
    conversation.is_active = True
    conversation.message_count = 0
    
    service.get_or_create_conversation.return_value = conversation
    service.add_message_to_conversation.return_value = True
    service.update_conversation_state.return_value = True
    service.get_conversation_history.return_value = []
    service.get_active_conversations_by_tenant.return_value = [conversation]
    service.get_conversations_by_phone.return_value = [conversation]
    service.get_conversation_stats.return_value = {
        "tenant_id": "test_tenant",
        "total_conversations": 1,
        "total_messages": 0,
        "active_conversations": 1
    }
    
    return service

@pytest.fixture
def sample_user_context():
    """Contexto de usuario de ejemplo"""
    return {
        "user_id": "user_123",
        "phone": "+573001234567",
        "name": "Juan",
        "lastname": "Pérez",
        "city": "Medellín",
        "state": "NEW"
    }

@pytest.fixture
def sample_classification_requests(sample_user_context):
    """Requests de clasificación de ejemplo"""
    return {
        "malicious": {
            "message": "Son unos ladrones, esto es una estafa",
            "tenant_id": "active_tenant",
            "user_context": sample_user_context
        },
        "appointment": {
            "message": "Quiero agendar una cita con el candidato",
            "tenant_id": "active_tenant",
            "user_context": sample_user_context
        },
        "support": {
            "message": "Hola, apoyo completamente al candidato",
            "tenant_id": "active_tenant",
            "user_context": sample_user_context
        },
        "advertising": {
            "message": "Necesito material publicitario",
            "tenant_id": "active_tenant",
            "user_context": sample_user_context
        }
    }

# Configuración de pytest
def pytest_configure(config):
    """Configuración adicional de pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )

def pytest_collection_modifyitems(config, items):
    """Modificar items de colección de tests"""
    for item in items:
        # Marcar tests de integración
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Marcar tests unitarios
        if "test_" in item.name and "integration" not in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Marcar tests lentos
        if any(keyword in item.name for keyword in ["slow", "performance", "load"]):
            item.add_marker(pytest.mark.slow)


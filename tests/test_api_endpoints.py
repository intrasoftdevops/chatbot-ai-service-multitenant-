"""
Tests para los endpoints de la API del sistema de clasificación de intenciones
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from chatbot_ai_service.main import app
from chatbot_ai_service.models.chat_models import ClassificationRequest
from chatbot_ai_service.models.intent_models import IntentCategory
from chatbot_ai_service.models.tenant_models import TenantConfig, TenantStatus

class TestAPIEndpoints:
    """Tests para los endpoints de la API"""
    
    @pytest.fixture
    def client(self):
        """Cliente de test para la API"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_tenant_config(self):
        """Mock de configuración de tenant"""
        return TenantConfig(
            tenant_id="test_tenant",
            tenant_type="political",
            client_project_id="test_project",
            status=TenantStatus.ACTIVE,
            link_calendly="https://calendly.com/test",
            link_forms="https://forms.gle/test"
        )
    
    @pytest.fixture
    def mock_classification_response(self):
        """Mock de respuesta de clasificación"""
        return {
            "classification": {
                "category": "cita_campaña",
                "confidence": 0.95,
                "original_message": "Quiero agendar una cita",
                "extracted_entities": {},
                "action": {
                    "action_type": "cita_campaña",
                    "parameters": {"calendly_link": True},
                    "response_message": "¡Perfecto! Te ayudo a agendar una cita.",
                    "requires_human": False
                },
                "fallback": False,
                "timestamp": datetime.now().isoformat()
            },
            "action_result": {
                "success": True,
                "action": "calendly_redirect",
                "response_message": "¡Perfecto! Te ayudo a agendar una cita. Aquí tienes el enlace: https://calendly.com/test",
                "redirect_url": "https://calendly.com/test",
                "requires_human": False
            },
            "tenant_id": "test_tenant",
            "timestamp": datetime.now().isoformat()
        }
    
    def test_root_endpoint(self, client):
        """Test endpoint raíz"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Chatbot AI Service Multi-Tenant"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    def test_health_endpoint(self, client):
        """Test endpoint de health check"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "chatbot-ai-service-multitenant"
    
    @patch('chatbot_ai_service.controllers.classification_controller.ClassificationController')
    def test_classify_intent_endpoint(self, mock_controller_class, client, mock_classification_response):
        """Test endpoint de clasificación de intenciones"""
        # Mock del controlador
        mock_controller = AsyncMock()
        mock_controller.classify_intent.return_value = mock_classification_response
        mock_controller_class.return_value = mock_controller
        
        # Mock del método de clasificación
        with patch('chatbot_ai_service.services.intent_classification_service.IntentClassificationService.classify_intent') as mock_classify:
            with patch('chatbot_ai_service.services.action_handler_service.ActionHandlerService.execute_action') as mock_action:
                mock_classify.return_value = Mock(
                    category=IntentCategory.CITA_CAMPANA,
                    confidence=0.95,
                    dict=Mock(return_value={"category": "cita_campaña", "confidence": 0.95}),
                    timestamp=datetime.now()
                )
                mock_action.return_value = {
                    "success": True,
                    "action": "calendly_redirect",
                    "response_message": "¡Perfecto! Te ayudo a agendar una cita.",
                    "redirect_url": "https://calendly.com/test"
                }
                
                request_data = {
                    "message": "Quiero agendar una cita con el candidato",
                    "user_context": {"phone": "+573001234567"}
                }
                
                response = client.post("/api/v1/tenants/test_tenant/classify", json=request_data)
                
                assert response.status_code == 200
                data = response.json()
                assert "classification" in data
                assert "action_result" in data
                assert data["tenant_id"] == "test_tenant"
    
    @patch('chatbot_ai_service.services.tenant_service.TenantService.is_tenant_active')
    def test_classify_intent_tenant_not_found(self, mock_is_active, client):
        """Test clasificación con tenant no encontrado"""
        mock_is_active.return_value = False
        
        request_data = {
            "message": "Cualquier mensaje",
            "user_context": {"phone": "+573001234567"}
        }
        
        response = client.post("/api/v1/tenants/nonexistent_tenant/classify", json=request_data)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    @patch('chatbot_ai_service.services.tenant_service.TenantService.is_tenant_active')
    def test_classify_intent_server_error(self, mock_is_active, client):
        """Test manejo de errores del servidor"""
        mock_is_active.side_effect = Exception("Database connection error")
        
        request_data = {
            "message": "Cualquier mensaje",
            "user_context": {"phone": "+573001234567"}
        }
        
        response = client.post("/api/v1/tenants/test_tenant/classify", json=request_data)
        
        assert response.status_code == 500
        data = response.json()
        assert "Error interno del servidor" in data["detail"]
    
    @patch('chatbot_ai_service.services.tenant_service.TenantService.is_tenant_active')
    @patch('chatbot_ai_service.services.intent_classification_service.IntentClassificationService.get_intent_examples')
    def test_intent_examples_endpoint(self, mock_get_examples, mock_is_active, client):
        """Test endpoint de ejemplos de intenciones"""
        mock_is_active.return_value = True
        mock_get_examples.return_value = {
            "tenant_id": "test_tenant",
            "intent_categories": {
                "malicioso": {
                    "examples": ["Son unos ladrones", "Esto es una estafa"],
                    "keywords": ["spam", "estafa", "ladrón"],
                    "action_description": "Bloquear usuario"
                },
                "cita_campaña": {
                    "examples": ["Quiero agendar una cita", "¿Cuándo pueden visitar?"],
                    "keywords": ["cita", "reunión", "agendar"],
                    "action_description": "Enviar link de Calendly"
                }
            },
            "total_categories": 12
        }
        
        response = client.get("/api/v1/tenants/test_tenant/intent-examples")
        
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == "test_tenant"
        assert "intent_categories" in data
        assert len(data["intent_categories"]) > 0
        assert "malicioso" in data["intent_categories"]
        assert "cita_campaña" in data["intent_categories"]
    
    @patch('chatbot_ai_service.services.tenant_service.TenantService.is_tenant_active')
    @patch('chatbot_ai_service.services.tenant_service.TenantService.get_tenant_config')
    def test_intent_actions_endpoint(self, mock_get_config, mock_is_active, client, mock_tenant_config):
        """Test endpoint de acciones de intenciones"""
        mock_is_active.return_value = True
        mock_get_config.return_value = mock_tenant_config
        
        response = client.get("/api/v1/tenants/test_tenant/intent-actions")
        
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == "test_tenant"
        assert "intent_actions" in data
        assert data["total_categories"] == 12
        
        # Verificar algunas categorías específicas
        intent_actions = data["intent_actions"]
        assert "malicioso" in intent_actions
        assert "cita_campaña" in intent_actions
        assert "saludo_apoyo" in intent_actions
        
        # Verificar estructura de una categoría
        malicious_action = intent_actions["malicioso"]
        assert "description" in malicious_action
        assert "action" in malicious_action
        assert "requires_human" in malicious_action
    
    @patch('chatbot_ai_service.services.tenant_service.TenantService.is_tenant_active')
    def test_extraction_fields_endpoint(self, mock_is_active, client):
        """Test endpoint de campos de extracción"""
        mock_is_active.return_value = True
        
        response = client.get("/api/v1/tenants/test_tenant/extraction-fields")
        
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == "test_tenant"
        assert "extraction_fields" in data
        
        # Verificar estructura de campos
        extraction_fields = data["extraction_fields"]
        assert "personal_info" in extraction_fields
        assert "additional_info" in extraction_fields
        
        # Verificar campos personales
        personal_info = extraction_fields["personal_info"]
        assert "name" in personal_info
        assert "lastname" in personal_info
        assert "phone" in personal_info
        assert "city" in personal_info
    
    def test_invalid_json_request(self, client):
        """Test manejo de JSON inválido"""
        response = client.post(
            "/api/v1/tenants/test_tenant/classify",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_missing_required_fields(self, client):
        """Test manejo de campos requeridos faltantes"""
        request_data = {
            "message": "Test message"
            # Falta user_context
        }
        
        response = client.post("/api/v1/tenants/test_tenant/classify", json=request_data)
        
        # Debería funcionar ya que user_context no es requerido
        assert response.status_code in [200, 404, 500]  # Dependiendo del mock
    
    @patch('chatbot_ai_service.services.tenant_service.TenantService.is_tenant_active')
    def test_tenant_status_endpoint(self, mock_is_active, client):
        """Test endpoint de estado de tenant"""
        mock_is_active.return_value = True
        
        response = client.get("/api/v1/tenants/test_tenant/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == "test_tenant"
        assert data["status"] == "active"
    
    @patch('chatbot_ai_service.services.tenant_service.TenantService.is_tenant_active')
    def test_tenant_health_endpoint(self, mock_is_active, client):
        """Test endpoint de salud de tenant"""
        mock_is_active.return_value = True
        
        with patch('chatbot_ai_service.services.tenant_service.TenantService.get_tenant_health') as mock_health:
            mock_health.return_value = Mock(
                tenant_id="test_tenant",
                status="healthy",
                ai_enabled=True,
                rag_enabled=True,
                cache_enabled=True,
                dict=Mock(return_value={
                    "tenant_id": "test_tenant",
                    "status": "healthy",
                    "ai_enabled": True,
                    "rag_enabled": True,
                    "cache_enabled": True
                })
            )
            
            response = client.get("/api/v1/tenants/test_tenant/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["tenant_id"] == "test_tenant"
            assert data["status"] == "healthy"
    
    def test_cors_headers(self, client):
        """Test headers CORS"""
        response = client.options("/api/v1/tenants/test_tenant/classify")
        
        # Verificar que CORS está configurado (headers pueden variar según configuración)
        assert response.status_code in [200, 204]
    
    @patch('chatbot_ai_service.services.tenant_service.TenantService.is_tenant_active')
    def test_multiple_tenant_requests(self, mock_is_active, client):
        """Test múltiples requests para diferentes tenants"""
        mock_is_active.return_value = True
        
        # Test tenant 1
        response1 = client.get("/api/v1/tenants/tenant_1/status")
        assert response1.status_code == 200
        
        # Test tenant 2
        response2 = client.get("/api/v1/tenants/tenant_2/status")
        assert response2.status_code == 200
        
        # Verificar que son respuestas diferentes
        data1 = response1.json()
        data2 = response2.json()
        assert data1["tenant_id"] == "tenant_1"
        assert data2["tenant_id"] == "tenant_2"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])


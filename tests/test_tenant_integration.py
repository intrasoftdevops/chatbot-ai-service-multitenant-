"""
Tests de integración completa con tenants para el sistema de clasificación
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from chatbot_ai_service.models.intent_models import IntentCategory
from chatbot_ai_service.models.chat_models import ClassificationRequest
from chatbot_ai_service.services.intent_classification_service import IntentClassificationService
from chatbot_ai_service.services.action_handler_service import ActionHandlerService
from chatbot_ai_service.services.tenant_service import TenantService
from chatbot_ai_service.services.ai_service import AIService
from chatbot_ai_service.config.firebase_config import FirebaseConfig
from chatbot_ai_service.models.tenant_models import (
    TenantConfig, TenantStatus, BrandingConfig, FeaturesConfig, 
    IntegrationsConfig, AIConfig
)

class TestTenantIntegration:
    """Tests de integración completa con tenants"""
    
    @pytest.fixture
    def mock_firebase_config(self):
        """Mock de la configuración de Firebase"""
        config = Mock(spec=FirebaseConfig)
        config.firestore = Mock()
        return config
    
    @pytest.fixture
    def create_tenant_config(self):
        """Helper para crear configuraciones de tenant"""
        def _create_config(tenant_id: str, **kwargs):
            return TenantConfig(
                tenant_id=tenant_id,
                tenant_type="political",
                client_project_id=f"{tenant_id}_project",
                status=TenantStatus.ACTIVE,
                branding=BrandingConfig(
                    welcome_message=f"¡Bienvenido a {tenant_id}!",
                    primary_color="#1E40AF",
                    secondary_color="#3B82F6"
                ),
                features=FeaturesConfig(
                    ai_enabled=True,
                    analytics_enabled=True,
                    referrals_enabled=True
                ),
                integrations=IntegrationsConfig(
                    wati={"api_token": f"wati_token_{tenant_id}"}
                ),
                ai_config=AIConfig(
                    model="gemini-pro",
                    temperature=0.7,
                    max_tokens=1000,
                    enable_rag=True
                ),
                link_calendly=f"https://calendly.com/{tenant_id}",
                link_forms=f"https://forms.gle/{tenant_id}",
                **kwargs
            )
        return _create_config
    
    @pytest.fixture
    def mock_tenant_service(self, create_tenant_config):
        """Mock del servicio de tenants con múltiples configuraciones"""
        service = AsyncMock(spec=TenantService)
        
        # Configurar diferentes tenants
        tenant_configs = {
            "tenant_1": create_tenant_config("tenant_1"),
            "tenant_2": create_tenant_config("tenant_2", 
                branding=BrandingConfig(
                    welcome_message="¡Hola desde tenant 2!",
                    primary_color="#DC2626"
                )
            ),
            "tenant_inactive": create_tenant_config("tenant_inactive", 
                status=TenantStatus.INACTIVE
            ),
            "tenant_no_ai": create_tenant_config("tenant_no_ai",
                features=FeaturesConfig(
                    ai_enabled=False,
                    analytics_enabled=True
                )
            )
        }
        
        async def get_tenant_config(tenant_id):
            return tenant_configs.get(tenant_id)
        
        async def is_tenant_active(tenant_id):
            config = tenant_configs.get(tenant_id)
            return config and config.status == TenantStatus.ACTIVE
        
        service.get_tenant_config.side_effect = get_tenant_config
        service.is_tenant_active.side_effect = is_tenant_active
        
        return service
    
    @pytest.fixture
    def mock_ai_service(self):
        """Mock del servicio de IA"""
        service = AsyncMock()
        
        # Mock de respuesta de IA genérica
        ai_response = Mock()
        ai_response.intent = "general"
        ai_response.confidence = 0.8
        ai_response.entities = {}
        ai_response.fallback = False
        
        service.classify_intent.return_value = ai_response
        
        return service
    
    @pytest.fixture
    def intent_classification_service(self, mock_tenant_service, mock_ai_service):
        """Servicio de clasificación de intenciones"""
        return IntentClassificationService(mock_tenant_service, mock_ai_service)
    
    @pytest.fixture
    def action_handler_service(self, mock_tenant_service, mock_firebase_config):
        """Servicio de manejo de acciones"""
        return ActionHandlerService(mock_tenant_service, mock_firebase_config)
    
    @pytest.mark.asyncio
    async def test_tenant_specific_classification(self, intent_classification_service):
        """Test clasificación específica por tenant"""
        # Test con tenant activo
        request = ClassificationRequest(
            message="Quiero agendar una cita",
            tenant_id="tenant_1",
            user_context={"phone": "+573001234567"}
        )
        
        classification = await intent_classification_service.classify_intent(request)
        
        assert classification.category == IntentCategory.CITA_CAMPANA
        assert classification.confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_inactive_tenant_handling(self, intent_classification_service):
        """Test manejo de tenant inactivo"""
        request = ClassificationRequest(
            message="Cualquier mensaje",
            tenant_id="tenant_inactive",
            user_context={"phone": "+573001234567"}
        )
        
        classification = await intent_classification_service.classify_intent(request)
        
        # Debería usar fallback
        assert classification.fallback
        assert classification.category == IntentCategory.SOLICITUD_FUNCIONAL
    
    @pytest.mark.asyncio
    async def test_nonexistent_tenant_handling(self, intent_classification_service):
        """Test manejo de tenant inexistente"""
        request = ClassificationRequest(
            message="Cualquier mensaje",
            tenant_id="nonexistent_tenant",
            user_context={"phone": "+573001234567"}
        )
        
        classification = await intent_classification_service.classify_intent(request)
        
        # Debería usar fallback
        assert classification.fallback
        assert classification.category == IntentCategory.SOLICITUD_FUNCIONAL
    
    @pytest.mark.asyncio
    async def test_tenant_specific_branding(self, action_handler_service, create_tenant_config):
        """Test uso de branding específico por tenant"""
        # Crear clasificación para tenant 1
        classification = Mock()
        classification.category = IntentCategory.SALUDO_APOYO
        classification.original_message = "Hola, apoyo la campaña"
        classification.extracted_entities = {"phone": "+573001234567"}
        classification.action = Mock()
        classification.action.response_message = "Respuesta base"
        classification.action.parameters = {"share_link": True, "points_rules": True}
        
        # Tenant con branding específico
        tenant_config = create_tenant_config("tenant_2")
        
        result = await action_handler_service._handle_support_greeting_action(classification, tenant_config)
        
        assert result["success"] is True
        assert "tenant 2" in result["response_message"]
    
    @pytest.mark.asyncio
    async def test_tenant_specific_links(self, action_handler_service, create_tenant_config):
        """Test uso de links específicos por tenant"""
        # Crear clasificación para cita
        classification = Mock()
        classification.category = IntentCategory.CITA_CAMPANA
        classification.original_message = "Quiero agendar una cita"
        classification.extracted_entities = {"phone": "+573001234567"}
        classification.action = Mock()
        classification.action.response_message = "Respuesta base"
        classification.action.parameters = {"calendly_link": True}
        
        # Tenant con links específicos
        tenant_config = create_tenant_config("tenant_1")
        
        result = await action_handler_service._handle_campaign_appointment_action(classification, tenant_config)
        
        assert result["success"] is True
        assert "tenant_1" in result["redirect_url"]
        assert result["redirect_url"] == "https://calendly.com/tenant_1"
    
    @pytest.mark.asyncio
    async def test_tenant_without_links(self, action_handler_service, create_tenant_config):
        """Test manejo de tenant sin links configurados"""
        # Crear clasificación para cita
        classification = Mock()
        classification.category = IntentCategory.CITA_CAMPANA
        classification.original_message = "Quiero agendar una cita"
        classification.extracted_entities = {"phone": "+573001234567"}
        classification.action = Mock()
        classification.action.response_message = "Respuesta base"
        classification.action.parameters = {"calendly_link": True}
        
        # Tenant sin links
        tenant_config = create_tenant_config("tenant_no_links")
        tenant_config.link_calendly = None
        tenant_config.link_forms = None
        
        result = await action_handler_service._handle_campaign_appointment_action(classification, tenant_config)
        
        assert result["success"] is True
        assert result["redirect_url"] == "https://calendly.com/candidato"  # Link por defecto
    
    @pytest.mark.asyncio
    async def test_multiple_tenants_same_message(self, intent_classification_service):
        """Test que diferentes tenants manejen el mismo mensaje correctamente"""
        message = "Quiero agendar una cita con el candidato"
        
        # Test con tenant 1
        request_1 = ClassificationRequest(
            message=message,
            tenant_id="tenant_1",
            user_context={"phone": "+573001234567"}
        )
        
        classification_1 = await intent_classification_service.classify_intent(request_1)
        assert classification_1.category == IntentCategory.CITA_CAMPANA
        
        # Test con tenant 2
        request_2 = ClassificationRequest(
            message=message,
            tenant_id="tenant_2",
            user_context={"phone": "+573001234567"}
        )
        
        classification_2 = await intent_classification_service.classify_intent(request_2)
        assert classification_2.category == IntentCategory.CITA_CAMPANA
        
        # Ambas clasificaciones deberían ser exitosas
        assert classification_1.confidence > 0.5
        assert classification_2.confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_tenant_configuration_validation(self, mock_tenant_service):
        """Test validación de configuración de tenant"""
        # Test tenant activo
        is_active = await mock_tenant_service.is_tenant_active("tenant_1")
        assert is_active is True
        
        # Test tenant inactivo
        is_active = await mock_tenant_service.is_tenant_active("tenant_inactive")
        assert is_active is False
        
        # Test tenant inexistente
        is_active = await mock_tenant_service.is_tenant_active("nonexistent")
        assert is_active is False
    
    @pytest.mark.asyncio
    async def test_tenant_specific_ai_config(self, mock_tenant_service):
        """Test configuración de IA específica por tenant"""
        tenant_config = await mock_tenant_service.get_tenant_config("tenant_1")
        
        assert tenant_config is not None
        assert tenant_config.ai_config is not None
        assert tenant_config.ai_config.model == "gemini-pro"
        assert tenant_config.ai_config.temperature == 0.7
        assert tenant_config.ai_config.enable_rag is True
    
    @pytest.mark.asyncio
    async def test_tenant_specific_features(self, mock_tenant_service):
        """Test funcionalidades específicas por tenant"""
        # Test tenant con IA habilitada
        tenant_config = await mock_tenant_service.get_tenant_config("tenant_1")
        assert tenant_config.features.ai_enabled is True
        
        # Test tenant sin IA
        tenant_config_no_ai = await mock_tenant_service.get_tenant_config("tenant_no_ai")
        assert tenant_config_no_ai.features.ai_enabled is False
    
    @pytest.mark.asyncio
    async def test_error_handling_across_tenants(self, intent_classification_service):
        """Test manejo de errores a través de diferentes tenants"""
        # Simular error en el servicio de IA
        with patch.object(intent_classification_service.ai_service, 'classify_intent', side_effect=Exception("AI Service Error")):
            request = ClassificationRequest(
                message="Cualquier mensaje",
                tenant_id="tenant_1",
                user_context={"phone": "+573001234567"}
            )
            
            classification = await intent_classification_service.classify_intent(request)
            
            # Debería manejar el error graciosamente
            assert classification.fallback is True
            assert classification.category == IntentCategory.SOLICITUD_FUNCIONAL
    
    @pytest.mark.asyncio
    async def test_concurrent_tenant_requests(self, intent_classification_service):
        """Test manejo de requests concurrentes para diferentes tenants"""
        async def classify_for_tenant(tenant_id: str):
            request = ClassificationRequest(
                message="Quiero agendar una cita",
                tenant_id=tenant_id,
                user_context={"phone": "+573001234567"}
            )
            return await intent_classification_service.classify_intent(request)
        
        # Ejecutar requests concurrentes
        tasks = [
            classify_for_tenant("tenant_1"),
            classify_for_tenant("tenant_2"),
            classify_for_tenant("tenant_1")  # Mismo tenant, diferente request
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Todos deberían ser exitosos
        for result in results:
            assert result.category == IntentCategory.CITA_CAMPANA
            assert result.confidence > 0.5
    
    def test_intent_examples_consistency(self, intent_classification_service):
        """Test consistencia de ejemplos de intenciones"""
        examples = intent_classification_service._intent_examples
        
        # Verificar que todas las categorías tienen ejemplos
        assert len(examples) == 12
        
        # Verificar que cada categoría tiene al menos 3 ejemplos
        for category, intent_example in examples.items():
            assert len(intent_example.examples) >= 3
            assert len(intent_example.keywords) >= 2
            assert len(intent_example.action_description) > 0
    
    def test_action_configurations_consistency(self, intent_classification_service):
        """Test consistencia de configuraciones de acciones"""
        action_configs = intent_classification_service._action_configurations
        
        # Verificar que todas las categorías tienen configuraciones
        assert len(action_configs) == 12
        
        # Verificar que cada configuración tiene parámetros válidos
        for category, config in action_configs.items():
            assert isinstance(config, dict)
            assert len(config) > 0
            
            # Verificar que tiene al menos un parámetro de acción
            has_action_param = any(
                key in config for key in 
                ['block_user', 'redirect_url', 'response_message', 'register_complaint']
            )
            assert has_action_param

if __name__ == "__main__":
    pytest.main([__file__, "-v"])


"""
Tests de integración para el sistema de clasificación de intenciones políticas
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from chatbot_ai_service.models.intent_models import IntentCategory, IntentClassification, IntentAction
from chatbot_ai_service.models.chat_models import ClassificationRequest
from chatbot_ai_service.services.intent_classification_service import IntentClassificationService
from chatbot_ai_service.services.action_handler_service import ActionHandlerService
from chatbot_ai_service.services.tenant_service import TenantService
from chatbot_ai_service.models.tenant_models import TenantConfig, TenantStatus, BrandingConfig, FeaturesConfig

class TestIntentClassification:
    """Tests para el sistema de clasificación de intenciones"""
    
    @pytest.fixture
    def mock_tenant_service(self):
        """Mock del servicio de tenants"""
        service = AsyncMock(spec=TenantService)
        
        # Configuración de tenant mock
        tenant_config = TenantConfig(
            tenant_id="test_tenant",
            tenant_type="political",
            client_project_id="test_project",
            status=TenantStatus.ACTIVE,
            branding=BrandingConfig(
                welcome_message="¡Bienvenido a nuestra campaña!",
                primary_color="#1E40AF"
            ),
            features=FeaturesConfig(
                ai_enabled=True,
                analytics_enabled=True
            ),
            link_calendly="https://calendly.com/test",
            link_forms="https://forms.gle/test"
        )
        
        service.get_tenant_config.return_value = tenant_config
        service.is_tenant_active.return_value = True
        
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
        """Servicio de clasificación de intenciones para testing"""
        return IntentClassificationService(mock_tenant_service, mock_ai_service)
    
    @pytest.mark.asyncio
    async def test_malicious_intent_classification(self, intent_classification_service):
        """Test clasificación de intenciones maliciosas"""
        request = ClassificationRequest(
            message="Son unos ladrones, esto es una estafa",
            tenant_id="test_tenant",
            user_context={"phone": "+573001234567"}
        )
        
        classification = await intent_classification_service.classify_intent(request)
        
        assert classification.category == IntentCategory.MALICIOSO
        assert classification.confidence > 0.5
        assert classification.action.action_type == "malicioso"
        assert "block_user" in classification.action.parameters
    
    @pytest.mark.asyncio
    async def test_campaign_appointment_classification(self, intent_classification_service):
        """Test clasificación de solicitudes de cita de campaña"""
        request = ClassificationRequest(
            message="Quiero agendar una cita con el candidato para la próxima semana",
            tenant_id="test_tenant",
            user_context={"phone": "+573001234567"}
        )
        
        classification = await intent_classification_service.classify_intent(request)
        
        assert classification.category == IntentCategory.CITA_CAMPANA
        assert classification.confidence > 0.5
        assert "calendly_link" in classification.action.parameters
        assert classification.action.redirect_url is not None
    
    @pytest.mark.asyncio
    async def test_support_greeting_classification(self, intent_classification_service):
        """Test clasificación de saludos de apoyo"""
        request = ClassificationRequest(
            message="Hola, apoyo completamente al candidato para presidente",
            tenant_id="test_tenant",
            user_context={"phone": "+573001234567"}
        )
        
        classification = await intent_classification_service.classify_intent(request)
        
        assert classification.category == IntentCategory.SALUDO_APOYO
        assert classification.confidence > 0.5
        assert "share_link" in classification.action.parameters
        assert classification.action.parameters["points_rules"]
    
    @pytest.mark.asyncio
    async def test_advertising_info_classification(self, intent_classification_service):
        """Test clasificación de solicitudes de publicidad"""
        request = ClassificationRequest(
            message="Necesito material publicitario para difundir la campaña",
            tenant_id="test_tenant",
            user_context={"phone": "+573001234567"}
        )
        
        classification = await intent_classification_service.classify_intent(request)
        
        assert classification.category == IntentCategory.PUBLICIDAD_INFO
        assert classification.confidence > 0.5
        assert "forms_link" in classification.action.parameters
        assert classification.action.redirect_url is not None
    
    @pytest.mark.asyncio
    async def test_know_candidate_classification(self, intent_classification_service):
        """Test clasificación de solicitudes para conocer al candidato"""
        request = ClassificationRequest(
            message="¿Quién es el candidato? ¿Cuáles son sus propuestas?",
            tenant_id="test_tenant",
            user_context={"phone": "+573001234567"}
        )
        
        classification = await intent_classification_service.classify_intent(request)
        
        assert classification.category == IntentCategory.CONOCER_CANDIDATO
        assert classification.confidence > 0.5
        assert classification.action.parameters["redirect_to_dqbot"]
        assert classification.action.parameters["city_notification"]
    
    @pytest.mark.asyncio
    async def test_data_update_classification(self, intent_classification_service):
        """Test clasificación de solicitudes de actualización de datos"""
        request = ClassificationRequest(
            message="Quiero cambiar mi teléfono y actualizar mi dirección",
            tenant_id="test_tenant",
            user_context={"phone": "+573001234567"}
        )
        
        classification = await intent_classification_service.classify_intent(request)
        
        assert classification.category == IntentCategory.ACTUALIZACION_DATOS
        assert classification.confidence > 0.5
        assert classification.action.parameters["dynamic_update"]
        assert "data_fields" in classification.action.parameters
    
    @pytest.mark.asyncio
    async def test_functional_request_classification(self, intent_classification_service):
        """Test clasificación de solicitudes funcionales"""
        request = ClassificationRequest(
            message="¿Cómo voy? ¿Cuántos puntos tengo?",
            tenant_id="test_tenant",
            user_context={"phone": "+573001234567"}
        )
        
        classification = await intent_classification_service.classify_intent(request)
        
        assert classification.category == IntentCategory.SOLICITUD_FUNCIONAL
        assert classification.confidence > 0.5
        assert classification.action.parameters["functional_response"]
        assert "available_queries" in classification.action.parameters
    
    @pytest.mark.asyncio
    async def test_volunteer_collaboration_classification(self, intent_classification_service):
        """Test clasificación de ofrecimientos de voluntariado"""
        request = ClassificationRequest(
            message="Quiero ser voluntario y ayudar en la campaña",
            tenant_id="test_tenant",
            user_context={"phone": "+573001234567"}
        )
        
        classification = await intent_classification_service.classify_intent(request)
        
        assert classification.category == IntentCategory.COLABORACION_VOLUNTARIADO
        assert classification.confidence > 0.5
        assert classification.action.parameters["collaboration_classification"]
        assert "collaboration_areas" in classification.action.parameters
        assert len(classification.action.parameters["collaboration_areas"]) == 9
    
    @pytest.mark.asyncio
    async def test_complaint_classification(self, intent_classification_service):
        """Test clasificación de quejas"""
        request = ClassificationRequest(
            message="No me gusta esto, tengo una queja sobre el proceso",
            tenant_id="test_tenant",
            user_context={"phone": "+573001234567"}
        )
        
        classification = await intent_classification_service.classify_intent(request)
        
        assert classification.category == IntentCategory.QUEJAS
        assert classification.confidence > 0.5
        assert classification.action.parameters["register_complaint"]
        assert classification.action.parameters["complaint_classification"]
    
    @pytest.mark.asyncio
    async def test_leader_classification(self, intent_classification_service):
        """Test clasificación de líderes comunitarios"""
        request = ClassificationRequest(
            message="Soy líder comunal de mi barrio y quiero coordinar acciones",
            tenant_id="test_tenant",
            user_context={"phone": "+573001234567"}
        )
        
        classification = await intent_classification_service.classify_intent(request)
        
        assert classification.category == IntentCategory.LIDER
        assert classification.confidence > 0.5
        assert classification.action.parameters["register_lead"]
        assert classification.action.parameters["lead_database"]
    
    @pytest.mark.asyncio
    async def test_human_attention_classification(self, intent_classification_service):
        """Test clasificación de solicitudes de atención humana"""
        request = ClassificationRequest(
            message="Quiero hablar con una persona, esto no lo entiendo",
            tenant_id="test_tenant",
            user_context={"phone": "+573001234567"}
        )
        
        classification = await intent_classification_service.classify_intent(request)
        
        assert classification.category == IntentCategory.ATENCION_HUMANO
        assert classification.confidence > 0.5
        assert classification.action.requires_human
        assert classification.action.parameters["default_team"]
    
    @pytest.mark.asyncio
    async def test_internal_team_classification(self, intent_classification_service):
        """Test clasificación de solicitudes del equipo interno"""
        request = ClassificationRequest(
            message="¿Cuánta gente hay en Chocó? Necesito estadísticas",
            tenant_id="test_tenant",
            user_context={"phone": "+573001234567"}
        )
        
        classification = await intent_classification_service.classify_intent(request)
        
        assert classification.category == IntentCategory.ATENCION_EQUIPO_INTERNO
        assert classification.confidence > 0.5
        assert classification.action.requires_permission
        assert classification.action.parameters["backoffice_connection"]
    
    @pytest.mark.asyncio
    async def test_fallback_classification(self, intent_classification_service):
        """Test clasificación de fallback para mensajes ambiguos"""
        request = ClassificationRequest(
            message="Mensaje ambiguo que no se puede clasificar claramente",
            tenant_id="test_tenant",
            user_context={"phone": "+573001234567"}
        )
        
        classification = await intent_classification_service.classify_intent(request)
        
        # Debería usar fallback a solicitud funcional
        assert classification.category == IntentCategory.SOLICITUD_FUNCIONAL
        assert classification.fallback
    
    @pytest.mark.asyncio
    async def test_tenant_not_found(self, intent_classification_service):
        """Test manejo cuando tenant no existe"""
        # Configurar mock para retornar None
        intent_classification_service.tenant_service.get_tenant_config.return_value = None
        
        request = ClassificationRequest(
            message="Cualquier mensaje",
            tenant_id="nonexistent_tenant",
            user_context={"phone": "+573001234567"}
        )
        
        classification = await intent_classification_service.classify_intent(request)
        
        # Debería usar fallback
        assert classification.fallback
        assert classification.category == IntentCategory.SOLICITUD_FUNCIONAL
    
    def test_intent_examples_structure(self, intent_classification_service):
        """Test estructura de ejemplos de intenciones"""
        examples = intent_classification_service._intent_examples
        
        # Verificar que todas las categorías tienen ejemplos
        assert len(examples) == 12
        
        for category in IntentCategory:
            assert category in examples
            intent_example = examples[category]
            
            # Verificar estructura de cada ejemplo
            assert hasattr(intent_example, 'category')
            assert hasattr(intent_example, 'examples')
            assert hasattr(intent_example, 'keywords')
            assert hasattr(intent_example, 'action_description')
            
            # Verificar que hay ejemplos y keywords
            assert len(intent_example.examples) > 0
            assert len(intent_example.keywords) > 0
            assert len(intent_example.action_description) > 0
    
    def test_action_configurations_structure(self, intent_classification_service):
        """Test estructura de configuraciones de acciones"""
        action_configs = intent_classification_service._action_configurations
        
        # Verificar que todas las categorías tienen configuraciones
        assert len(action_configs) == 12
        
        for category in IntentCategory:
            assert category in action_configs
            config = action_configs[category]
            
            # Verificar que es un diccionario
            assert isinstance(config, dict)
            
            # Verificar que tiene al menos una configuración
            assert len(config) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])


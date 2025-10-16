"""
Tests para los manejadores de acciones del sistema de clasificación de intenciones
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from chatbot_ai_service.models.intent_models import IntentCategory, IntentClassification, IntentAction
from chatbot_ai_service.models.chat_models import ClassificationRequest
from chatbot_ai_service.services.action_handler_service import ActionHandlerService
from chatbot_ai_service.services.tenant_service import TenantService
from chatbot_ai_service.config.firebase_config import FirebaseConfig
from chatbot_ai_service.models.tenant_models import TenantConfig, TenantStatus, BrandingConfig, FeaturesConfig

class TestActionHandlers:
    """Tests para los manejadores de acciones"""
    
    @pytest.fixture
    def mock_tenant_service(self):
        """Mock del servicio de tenants"""
        service = AsyncMock(spec=TenantService)
        
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
            link_calendly="https://calendly.com/test-tenant",
            link_forms="https://forms.gle/test-tenant"
        )
        
        service.get_tenant_config.return_value = tenant_config
        service.is_tenant_active.return_value = True
        
        return service
    
    @pytest.fixture
    def mock_firebase_config(self):
        """Mock de la configuración de Firebase"""
        config = Mock(spec=FirebaseConfig)
        config.firestore = Mock()
        return config
    
    @pytest.fixture
    def action_handler_service(self, mock_tenant_service, mock_firebase_config):
        """Servicio de manejo de acciones para testing"""
        return ActionHandlerService(mock_tenant_service, mock_firebase_config)
    
    def create_test_classification(self, category: IntentCategory, message: str) -> IntentClassification:
        """Helper para crear clasificaciones de test"""
        action = IntentAction(
            action_type=category.value,
            parameters={},
            response_message="Test response message",
            requires_human=False
        )
        
        return IntentClassification(
            category=category,
            confidence=0.9,
            original_message=message,
            extracted_entities={"phone": "+573001234567"},
            action=action,
            fallback=False,
            timestamp=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_malicious_action_handler(self, action_handler_service, mock_tenant_service):
        """Test manejo de acciones maliciosas"""
        classification = self.create_test_classification(
            IntentCategory.MALICIOSO,
            "Son unos ladrones, esto es una estafa"
        )
        
        tenant_config = await mock_tenant_service.get_tenant_config("test_tenant")
        
        with patch.object(action_handler_service, '_update_user_permissions') as mock_update:
            with patch.object(action_handler_service, '_log_incident') as mock_log:
                result = await action_handler_service._handle_malicious_action(classification, tenant_config)
                
                assert result["success"] is True
                assert result["action"] == "user_blocked"
                assert result["blocked_user"] is True
                assert result["database_updated"] is True
                
                # Verificar que se llamaron los métodos de actualización y logging
                mock_update.assert_called_once()
                mock_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_campaign_appointment_action_handler(self, action_handler_service, mock_tenant_service):
        """Test manejo de acciones de cita de campaña"""
        classification = self.create_test_classification(
            IntentCategory.CITA_CAMPANA,
            "Quiero agendar una cita con el candidato"
        )
        
        tenant_config = await mock_tenant_service.get_tenant_config("test_tenant")
        
        result = await action_handler_service._handle_campaign_appointment_action(classification, tenant_config)
        
        assert result["success"] is True
        assert result["action"] == "calendly_redirect"
        assert "calendly.com/test-tenant" in result["response_message"]
        assert result["redirect_url"] == "https://calendly.com/test-tenant"
        assert result["requires_human"] is False
    
    @pytest.mark.asyncio
    async def test_support_greeting_action_handler(self, action_handler_service, mock_tenant_service):
        """Test manejo de acciones de saludo de apoyo"""
        classification = self.create_test_classification(
            IntentCategory.SALUDO_APOYO,
            "Hola, apoyo completamente al candidato"
        )
        
        tenant_config = await mock_tenant_service.get_tenant_config("test_tenant")
        
        result = await action_handler_service._handle_support_greeting_action(classification, tenant_config)
        
        assert result["success"] is True
        assert result["action"] == "support_response"
        assert "Bienvenido a nuestra campaña" in result["response_message"]
        assert result["points_rules_enabled"] is True
        assert "share_links" in result
    
    @pytest.mark.asyncio
    async def test_advertising_info_action_handler(self, action_handler_service, mock_tenant_service):
        """Test manejo de acciones de solicitud de publicidad"""
        classification = self.create_test_classification(
            IntentCategory.PUBLICIDAD_INFO,
            "Necesito material publicitario"
        )
        
        tenant_config = await mock_tenant_service.get_tenant_config("test_tenant")
        
        result = await action_handler_service._handle_advertising_info_action(classification, tenant_config)
        
        assert result["success"] is True
        assert result["action"] == "forms_redirect"
        assert "forms.gle/test-tenant" in result["response_message"]
        assert result["redirect_url"] == "https://forms.gle/test-tenant"
        assert result["requires_human"] is False
    
    @pytest.mark.asyncio
    async def test_know_candidate_action_handler(self, action_handler_service, mock_tenant_service):
        """Test manejo de acciones para conocer al candidato"""
        classification = self.create_test_classification(
            IntentCategory.CONOCER_CANDIDATO,
            "¿Quién es el candidato? ¿Cuáles son sus propuestas?"
        )
        
        tenant_config = await mock_tenant_service.get_tenant_config("test_tenant")
        
        result = await action_handler_service._handle_know_candidate_action(classification, tenant_config)
        
        assert result["success"] is True
        assert result["action"] == "dqbot_redirect"
        assert "DQBot" in result["response_message"]
        assert "ciudad" in result["response_message"]
        assert result["redirect_to_dqbot"] is True
        assert result["city_notification_enabled"] is True
    
    @pytest.mark.asyncio
    async def test_data_update_action_handler(self, action_handler_service, mock_tenant_service):
        """Test manejo de acciones de actualización de datos"""
        classification = self.create_test_classification(
            IntentCategory.ACTUALIZACION_DATOS,
            "Quiero cambiar mi teléfono"
        )
        
        tenant_config = await mock_tenant_service.get_tenant_config("test_tenant")
        
        result = await action_handler_service._handle_data_update_action(classification, tenant_config)
        
        assert result["success"] is True
        assert result["action"] == "data_update"
        assert "actualizar" in result["response_message"].lower()
        assert "available_fields" in result
        assert result["dynamic_update"] is True
    
    @pytest.mark.asyncio
    async def test_functional_request_action_handler(self, action_handler_service, mock_tenant_service):
        """Test manejo de acciones de solicitudes funcionales"""
        classification = self.create_test_classification(
            IntentCategory.SOLICITUD_FUNCIONAL,
            "¿Cómo voy? ¿Cuántos puntos tengo?"
        )
        
        tenant_config = await mock_tenant_service.get_tenant_config("test_tenant")
        
        result = await action_handler_service._handle_functional_request_action(classification, tenant_config)
        
        assert result["success"] is True
        assert result["action"] == "functional_response"
        assert "puntos" in result["response_message"] or "ranking" in result["response_message"]
        assert "query_type" in result
        assert "available_queries" in result
    
    @pytest.mark.asyncio
    async def test_volunteer_collaboration_action_handler(self, action_handler_service, mock_tenant_service):
        """Test manejo de acciones de colaboración voluntaria"""
        classification = self.create_test_classification(
            IntentCategory.COLABORACION_VOLUNTARIADO,
            "Quiero ser voluntario"
        )
        
        tenant_config = await mock_tenant_service.get_tenant_config("test_tenant")
        
        result = await action_handler_service._handle_volunteer_collaboration_action(classification, tenant_config)
        
        assert result["success"] is True
        assert result["action"] == "volunteer_classification"
        assert "colaborar" in result["response_message"].lower()
        assert "collaboration_areas" in result
        assert len(result["collaboration_areas"]) == 9
        assert result["requires_follow_up"] is True
    
    @pytest.mark.asyncio
    async def test_complaint_action_handler(self, action_handler_service, mock_tenant_service):
        """Test manejo de acciones de quejas"""
        classification = self.create_test_classification(
            IntentCategory.QUEJAS,
            "No me gusta esto, tengo una queja"
        )
        
        tenant_config = await mock_tenant_service.get_tenant_config("test_tenant")
        
        with patch.object(action_handler_service, '_log_incident') as mock_log:
            result = await action_handler_service._handle_complaint_action(classification, tenant_config)
            
            assert result["success"] is True
            assert result["action"] == "complaint_registered"
            assert "feedback" in result["response_message"].lower()
            assert result["complaint_logged"] is True
            
            # Verificar que se registró la queja
            mock_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_leader_action_handler(self, action_handler_service, mock_tenant_service):
        """Test manejo de acciones de líderes"""
        classification = self.create_test_classification(
            IntentCategory.LIDER,
            "Soy líder comunal de mi barrio"
        )
        
        tenant_config = await mock_tenant_service.get_tenant_config("test_tenant")
        
        with patch.object(action_handler_service, '_register_lead') as mock_register:
            result = await action_handler_service._handle_leader_action(classification, tenant_config)
            
            assert result["success"] is True
            assert result["action"] == "leader_registered"
            assert "líder" in result["response_message"].lower()
            assert result["lead_registered"] is True
            
            # Verificar que se registró el lead
            mock_register.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_human_attention_action_handler(self, action_handler_service, mock_tenant_service):
        """Test manejo de acciones de atención humana"""
        classification = self.create_test_classification(
            IntentCategory.ATENCION_HUMANO,
            "Quiero hablar con una persona"
        )
        
        tenant_config = await mock_tenant_service.get_tenant_config("test_tenant")
        
        result = await action_handler_service._handle_human_attention_action(classification, tenant_config)
        
        assert result["success"] is True
        assert result["action"] == "human_redirect"
        assert "voluntario" in result["response_message"].lower()
        assert result["requires_human"] is True
        assert result["default_team"] is True
    
    @pytest.mark.asyncio
    async def test_internal_team_action_handler(self, action_handler_service, mock_tenant_service):
        """Test manejo de acciones del equipo interno"""
        classification = self.create_test_classification(
            IntentCategory.ATENCION_EQUIPO_INTERNO,
            "¿Cuánta gente hay en Chocó?"
        )
        
        tenant_config = await mock_tenant_service.get_tenant_config("test_tenant")
        
        result = await action_handler_service._handle_internal_team_action(classification, tenant_config)
        
        assert result["success"] is True
        assert result["action"] == "internal_info_request"
        assert "permisos" in result["response_message"].lower()
        assert result["requires_permission"] is True
        assert result["backoffice_connection"] is True
    
    @pytest.mark.asyncio
    async def test_fallback_action_handler(self, action_handler_service, mock_tenant_service):
        """Test manejo de acciones de fallback"""
        classification = self.create_test_classification(
            IntentCategory.SOLICITUD_FUNCIONAL,
            "Mensaje ambiguo"
        )
        
        tenant_config = await mock_tenant_service.get_tenant_config("test_tenant")
        
        result = await action_handler_service._handle_fallback_action(classification, tenant_config)
        
        assert result["success"] is True
        assert result["action"] == "fallback"
        assert result["fallback"] is True
    
    def test_determine_functional_query_type(self, action_handler_service):
        """Test determinación de tipo de consulta funcional"""
        # Test puntos
        result = action_handler_service._determine_functional_query_type("¿Cuántos puntos tengo?")
        assert result == "points"
        
        # Test tribu
        result = action_handler_service._determine_functional_query_type("Link de mi tribu")
        assert result == "tribe"
        
        # Test referidos
        result = action_handler_service._determine_functional_query_type("¿Cuántas personas tengo debajo?")
        assert result == "referrals"
        
        # Test general
        result = action_handler_service._determine_functional_query_type("¿Cómo funciona esto?")
        assert result == "general"
    
    @pytest.mark.asyncio
    async def test_execute_action_integration(self, action_handler_service, mock_tenant_service):
        """Test integración completa de ejecución de acciones"""
        classification = self.create_test_classification(
            IntentCategory.CITA_CAMPANA,
            "Quiero agendar una cita"
        )
        
        tenant_config = await mock_tenant_service.get_tenant_config("test_tenant")
        
        result = await action_handler_service.execute_action(classification, tenant_config)
        
        assert result["success"] is True
        assert "action" in result
        assert "response_message" in result
    
    @pytest.mark.asyncio
    async def test_action_error_handling(self, action_handler_service, mock_tenant_service):
        """Test manejo de errores en acciones"""
        # Crear una clasificación con categoría inválida
        classification = self.create_test_classification(
            IntentCategory.SOLICITUD_FUNCIONAL,  # Usar categoría válida pero simular error
            "Mensaje de test"
        )
        
        tenant_config = await mock_tenant_service.get_tenant_config("test_tenant")
        
        # Simular error en el método
        with patch.object(action_handler_service, '_handle_functional_request_action', side_effect=Exception("Test error")):
            result = await action_handler_service.execute_action(classification, tenant_config)
            
            assert result["success"] is False
            assert "error" in result
            assert "Test error" in result["error"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])


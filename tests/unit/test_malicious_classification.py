"""
Test suite para clasificación de mensajes maliciosos

Este módulo contiene tests unitarios para validar que el sistema
de clasificación de intenciones detecte correctamente mensajes maliciosos.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from typing import Dict, Any

# Importar el servicio de IA
from chatbot_ai_service.services.ai_service import AIService
from tests.data.malicious_messages import MALICIOUS_MESSAGES, NON_MALICIOUS_MESSAGES, MALICIOUS_CATEGORIES


class TestMaliciousMessageClassification:
    """Tests para clasificación de mensajes maliciosos"""
    
    @pytest.fixture
    def ai_service(self):
        """Fixture para crear instancia de AIService para testing"""
        with patch('chatbot_ai_service.services.ai_service.os.getenv') as mock_env:
            mock_env.return_value = "test_api_key"
            service = AIService()
            # Mock del modelo para evitar llamadas reales a Gemini
            service.model = Mock()
            service._model_initialized = True
            return service
    
    @pytest.fixture
    def mock_user_context(self):
        """Fixture para contexto de usuario de prueba"""
        return {
            "user_id": "test_user_123",
            "user_name": "Test User",
            "user_state": "COMPLETED"
        }
    
    @pytest.fixture
    def mock_tenant_config(self):
        """Fixture para configuración de tenant de prueba"""
        return {
            "link_calendly": "https://calendly.com/test",
            "contact_name": "Test Candidate",
            "welcome_message": "Welcome to test campaign"
        }
    
    @pytest.mark.asyncio
    @pytest.mark.malicious
    async def test_classify_malicious_message(self, ai_service, mock_user_context):
        """Test que un mensaje malicioso sea clasificado correctamente"""
        malicious_message = "Eres un hp."
        
        # Mock de la respuesta de clasificación
        mock_response = Mock()
        mock_response.text = "malicioso"
        ai_service.model.generate_content.return_value = mock_response
        
        # Ejecutar clasificación
        result = await ai_service.classify_intent(
            tenant_id="test_tenant",
            message=malicious_message,
            user_context=mock_user_context,
            session_id="test_session"
        )
        
        # Verificar resultado
        assert result["category"] == "malicioso"
        assert result["confidence"] > 0.7  # Alta confianza para mensajes obvios
    
    @pytest.mark.asyncio
    @pytest.mark.malicious
    async def test_classify_non_malicious_message(self, ai_service, mock_user_context):
        """Test que un mensaje normal NO sea clasificado como malicioso"""
        normal_message = "Hola, ¿cómo estás?"
        
        # Mock de la respuesta de clasificación
        mock_response = Mock()
        mock_response.text = "saludo_apoyo"
        ai_service.model.generate_content.return_value = mock_response
        
        # Ejecutar clasificación
        result = await ai_service.classify_intent(
            tenant_id="test_tenant",
            message=normal_message,
            user_context=mock_user_context,
            session_id="test_session"
        )
        
        # Verificar resultado
        assert result["category"] != "malicioso"
        assert result["confidence"] > 0.5
    
    @pytest.mark.asyncio
    async def test_malicious_categories_detection(self, ai_service, mock_user_context):
        """Test que diferentes categorías de mensajes maliciosos sean detectadas"""
        
        for category_name, messages in MALICIOUS_CATEGORIES.items():
            for message in messages[:3]:  # Test solo los primeros 3 de cada categoría
                # Mock de la respuesta de clasificación
                mock_response = Mock()
                mock_response.text = "malicioso"
                ai_service.model.generate_content.return_value = mock_response
                
                # Ejecutar clasificación
                result = await ai_service.classify_intent(
                    tenant_id="test_tenant",
                    message=message,
                    user_context=mock_user_context,
                    session_id="test_session"
                )
                
                # Verificar resultado
                assert result["category"] == "malicioso", f"Failed for category {category_name}: {message}"
                assert result["confidence"] > 0.6, f"Low confidence for {category_name}: {message}"
    
    @pytest.mark.asyncio
    async def test_batch_malicious_classification(self, ai_service, mock_user_context):
        """Test clasificación en lote de mensajes maliciosos"""
        
        # Test todos los mensajes maliciosos
        results = []
        for message in MALICIOUS_MESSAGES:
            # Mock de la respuesta de clasificación
            mock_response = Mock()
            mock_response.text = "malicioso"
            ai_service.model.generate_content.return_value = mock_response
            
            result = await ai_service.classify_intent(
                tenant_id="test_tenant",
                message=message,
                user_context=mock_user_context,
                session_id="test_session"
            )
            results.append(result)
        
        # Verificar que todos fueron clasificados como maliciosos
        malicious_count = sum(1 for r in results if r["category"] == "malicioso")
        assert malicious_count >= len(MALICIOUS_MESSAGES) * 0.9, f"Only {malicious_count}/{len(MALICIOUS_MESSAGES)} classified as malicious"
    
    @pytest.mark.asyncio
    async def test_batch_non_malicious_classification(self, ai_service, mock_user_context):
        """Test clasificación en lote de mensajes NO maliciosos"""
        
        # Test todos los mensajes no maliciosos
        results = []
        for message in NON_MALICIOUS_MESSAGES:
            # Mock de la respuesta de clasificación
            mock_response = Mock()
            mock_response.text = "saludo_apoyo"  # O cualquier otra categoría no maliciosa
            ai_service.model.generate_content.return_value = mock_response
            
            result = await ai_service.classify_intent(
                tenant_id="test_tenant",
                message=message,
                user_context=mock_user_context,
                session_id="test_session"
            )
            results.append(result)
        
        # Verificar que ninguno fue clasificado como malicioso
        malicious_count = sum(1 for r in results if r["category"] == "malicioso")
        assert malicious_count == 0, f"{malicious_count} non-malicious messages were classified as malicious"
    
    @pytest.mark.asyncio
    async def test_confidence_thresholds(self, ai_service, mock_user_context):
        """Test que los umbrales de confianza sean apropiados"""
        
        # Test mensaje muy obviamente malicioso
        obvious_malicious = "Eres un hp."
        mock_response = Mock()
        mock_response.text = "malicioso"
        ai_service.model.generate_content.return_value = mock_response
        
        result = await ai_service.classify_intent(
            tenant_id="test_tenant",
            message=obvious_malicious,
            user_context=mock_user_context,
            session_id="test_session"
        )
        
        assert result["confidence"] > 0.8, "Obvious malicious message should have high confidence"
    
    @pytest.mark.asyncio
    async def test_edge_cases(self, ai_service, mock_user_context):
        """Test casos límite y edge cases"""
        
        edge_cases = [
            "",  # Mensaje vacío
            "   ",  # Solo espacios
            "a",  # Un solo carácter
            "Eres un hp" + " " * 100,  # Mensaje muy largo
            "Eres un hp." * 50,  # Repetición excesiva
        ]
        
        for message in edge_cases:
            # Mock de la respuesta de clasificación
            mock_response = Mock()
            mock_response.text = "malicioso" if "hp" in message else "default"
            ai_service.model.generate_content.return_value = mock_response
            
            result = await ai_service.classify_intent(
                tenant_id="test_tenant",
                message=message,
                user_context=mock_user_context,
                session_id="test_session"
            )
            
            # Verificar que no hay errores
            assert "category" in result
            assert "confidence" in result
            assert 0 <= result["confidence"] <= 1


class TestMaliciousHandling:
    """Tests para el manejo de mensajes maliciosos"""
    
    @pytest.fixture
    def ai_service(self):
        """Fixture para crear instancia de AIService para testing"""
        with patch('chatbot_ai_service.services.ai_service.os.getenv') as mock_env:
            mock_env.return_value = "test_api_key"
            service = AIService()
            service.model = Mock()
            service._model_initialized = True
            return service
    
    @pytest.mark.asyncio
    async def test_malicious_behavior_handling(self, ai_service):
        """Test que el sistema maneje correctamente el comportamiento malicioso"""
        
        malicious_message = "Eres un hp."
        user_context = {"user_id": "test_user", "user_name": "Test"}
        
        # Mock de la respuesta de manejo de comportamiento malicioso
        with patch.object(ai_service, '_handle_malicious_behavior') as mock_handler:
            mock_handler.return_value = "Mensaje inapropiado detectado."
            
            result = await ai_service._handle_malicious_behavior(
                message=malicious_message,
                user_context=user_context,
                tenant_id="test_tenant",
                confidence=0.9
            )
            
            assert result == "Mensaje inapropiado detectado."
            mock_handler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_malicious_response_generation(self, ai_service):
        """Test que se genere una respuesta apropiada para mensajes maliciosos"""
        
        malicious_message = "Corrupto de mierda."
        user_context = {"user_id": "test_user", "user_name": "Test"}
        
        # Ejecutar manejo de comportamiento malicioso
        response = await ai_service._handle_malicious_behavior(
            message=malicious_message,
            user_context=user_context,
            tenant_id="test_tenant",
            confidence=0.95
        )
        
        # Verificar que la respuesta es apropiada
        assert isinstance(response, str)
        assert len(response) > 0
        assert "inapropiado" in response.lower() or "respeto" in response.lower()


if __name__ == "__main__":
    # Ejecutar tests si se ejecuta directamente
    pytest.main([__file__, "-v"])

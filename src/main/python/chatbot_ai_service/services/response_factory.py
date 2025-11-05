"""
Factory para creación de respuestas del sistema
"""

import logging
from datetime import datetime

from chatbot_ai_service.models.chat_models import ChatRequest, ChatResponse, ClassificationResponse, DataExtractionResponse
from chatbot_ai_service.models.tenant_models import TenantConfig

logger = logging.getLogger(__name__)

class ResponseFactory:
    """Factory para creación de respuestas del sistema"""
    
    @staticmethod
    def create_error_response(request: ChatRequest, error_message: str) -> ChatResponse:
        """Crea una respuesta de error"""
        return ChatResponse(
            response=f"Error: {error_message}",
            session_id=request.session_id,
            tenant_id=request.tenant_id,
            confidence=0.0,
            processing_time=0.0,
            timestamp=datetime.now()
        )
    
    @staticmethod
    def create_fallback_response(request: ChatRequest, tenant_config: TenantConfig) -> ChatResponse:
        """Crea una respuesta de fallback"""
        fallback_message = "Hola! ¿En qué puedo ayudarte?"
        
        if tenant_config.branding and tenant_config.branding.welcome_message:
            fallback_message = tenant_config.branding.welcome_message
        
        return ChatResponse(
            response=fallback_message,
            session_id=request.session_id,
            tenant_id=request.tenant_id,
            confidence=0.5,
            processing_time=0.0,
            timestamp=datetime.now()
        )
    
    @staticmethod
    def create_classification_error_response(processing_time: float) -> ClassificationResponse:
        """Crea una respuesta de error para clasificación"""
        return ClassificationResponse(
            intent="general",
            confidence=0.0,
            fallback=True,
            processing_time=processing_time
        )
    
    @staticmethod
    def create_extraction_error_response(processing_time: float) -> DataExtractionResponse:
        """Crea una respuesta de error para extracción de datos"""
        return DataExtractionResponse(
            extracted_data={},
            confidence=0.0,
            fallback=True,
            processing_time=processing_time
        )

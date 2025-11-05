"""
Servicio de IA refactorizado para el servicio multi-tenant
Integra con Gemini AI y LlamaIndex para RAG conversacional
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from chatbot_ai_service.models.chat_models import (
    ChatRequest, ChatResponse, ClassificationRequest, ClassificationResponse,
    DataExtractionRequest, DataExtractionResponse, UserState
)
from chatbot_ai_service.models.tenant_models import TenantConfig
from chatbot_ai_service.services.tenant_service import TenantService
from chatbot_ai_service.services.ai_model_service import AIModelService
from chatbot_ai_service.services.conversation_context_service import ConversationContextService
from chatbot_ai_service.services.ai_response_service import AIResponseService
from chatbot_ai_service.services.data_extraction_service import DataExtractionService
from chatbot_ai_service.services.response_factory import ResponseFactory

logger = logging.getLogger(__name__)

class AIService:
    """Servicio de IA multi-tenant"""
    
    def __init__(self, tenant_service: TenantService):
        self.tenant_service = tenant_service
        self.ai_model_service = AIModelService()
        self.conversation_context_service = ConversationContextService()
        self.ai_response_service = AIResponseService()
        self.data_extraction_service = DataExtractionService()
        self.response_factory = ResponseFactory()
    
    async def process_chat_message(self, request: ChatRequest) -> ChatResponse:
        """
        Procesa un mensaje de chat usando IA específica del tenant
        """
        start_time = time.time()
        
        try:
            logger.info(f"Procesando mensaje para tenant {request.tenant_id}, sesión {request.session_id}")
            
            # Obtener configuración del tenant
            tenant_config = await self.tenant_service.get_tenant_config(request.tenant_id)
            if not tenant_config:
                return self.response_factory.create_error_response(request, "Tenant no encontrado o inactivo")
            
            # Verificar si la IA está habilitada
            if not tenant_config.features or not tenant_config.features.ai_enabled:
                return self.response_factory.create_fallback_response(request, tenant_config)
            
            # Obtener modelo de IA específico del tenant
            ai_model = await self.ai_model_service.get_tenant_ai_model(request.tenant_id, tenant_config)
            if not ai_model:
                return self.response_factory.create_error_response(request, "Error al cargar modelo de IA")
            
            # Preparar contexto de conversación
            conversation_context = await self.conversation_context_service.build_conversation_context(
                request, tenant_config
            )
            
            # Generar respuesta usando IA
            ai_response = await self.ai_response_service.generate_ai_response(
                ai_model, request.query, conversation_context, tenant_config
            )
            
            # Extraer datos del usuario si es necesario
            extracted_data = await self.data_extraction_service.extract_user_data(
                request, ai_response, tenant_config
            )
            
            # Determinar nuevo estado del usuario
            new_user_state = await self.data_extraction_service.determine_user_state(
                request, ai_response, extracted_data
            )
            
            processing_time = time.time() - start_time
            
            return ChatResponse(
                response=ai_response,
                session_id=request.session_id,
                tenant_id=request.tenant_id,
                user_state=new_user_state,
                extracted_data=extracted_data,
                confidence=0.8,  # TODO: Implementar cálculo de confianza
                processing_time=processing_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error al procesar mensaje para tenant {request.tenant_id}: {e}")
            return self.response_factory.create_error_response(request, str(e))
    
    async def classify_intent(self, request: ClassificationRequest) -> ClassificationResponse:
        """
        Clasifica la intención de un mensaje
        """
        start_time = time.time()
        
        try:
            logger.info(f"Clasificando intención para tenant {request.tenant_id}")
            
            # Obtener configuración del tenant
            tenant_config = await self.tenant_service.get_tenant_config(request.tenant_id)
            if not tenant_config:
                return self.response_factory.create_classification_error_response(time.time() - start_time)
            
            # Usar IA para clasificación
            ai_model = await self.ai_model_service.get_tenant_ai_model(request.tenant_id, tenant_config)
            if not ai_model:
                return self.response_factory.create_classification_error_response(time.time() - start_time)
            
            # Preparar prompt para clasificación
            classification_prompt = self.ai_response_service.build_classification_prompt(
                request.message, tenant_config
            )
            
            # Generar clasificación
            response = ai_model.generate_content(classification_prompt)
            intent_data = self.ai_response_service.parse_classification_response(response.text)
            
            return ClassificationResponse(
                intent=intent_data.get("intent", "general"),
                confidence=intent_data.get("confidence", 0.5),
                entities=intent_data.get("entities", {}),
                suggested_actions=intent_data.get("suggested_actions", []),
                fallback=False,
                processing_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error al clasificar intención para tenant {request.tenant_id}: {e}")
            return self.response_factory.create_classification_error_response(time.time() - start_time)
    
    async def extract_user_data(self, request: DataExtractionRequest) -> DataExtractionResponse:
        """
        Extrae datos del usuario desde un mensaje
        """
        start_time = time.time()
        
        try:
            logger.info(f"Extrayendo datos para tenant {request.tenant_id}")
            
            # Obtener configuración del tenant
            tenant_config = await self.tenant_service.get_tenant_config(request.tenant_id)
            if not tenant_config:
                return self.response_factory.create_extraction_error_response(time.time() - start_time)
            
            # Usar IA para extracción
            ai_model = await self.ai_model_service.get_tenant_ai_model(request.tenant_id, tenant_config)
            if not ai_model:
                return self.response_factory.create_extraction_error_response(time.time() - start_time)
            
            # Preparar prompt para extracción
            extraction_prompt = self.ai_response_service.build_extraction_prompt(
                request.message, request.expected_fields, tenant_config
            )
            
            # Generar extracción
            response = ai_model.generate_content(extraction_prompt)
            extraction_data = self.ai_response_service.parse_extraction_response(response.text)
            
            return DataExtractionResponse(
                extracted_data=extraction_data.get("data", {}),
                confidence=extraction_data.get("confidence", 0.5),
                missing_fields=extraction_data.get("missing_fields", []),
                suggestions=extraction_data.get("suggestions", {}),
                fallback=False,
                processing_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error al extraer datos para tenant {request.tenant_id}: {e}")
            return self.response_factory.create_extraction_error_response(time.time() - start_time)
    
    async def process_simple_prompt(self, prompt: str, tenant_config: TenantConfig, use_documentation: bool = True) -> str:
        """
        Procesa un prompt simple con IA contextual
        
        Args:
            prompt: Prompt a procesar
            tenant_config: Configuración del tenant
            use_documentation: Si debe cargar documentación del bucket
            
        Returns:
            Respuesta de la IA
        """
        try:
            logger.info(f"Procesando prompt simple para tenant {tenant_config.tenant_id}")
            
            # Obtener modelo de IA
            ai_model = await self.ai_model_service.get_tenant_ai_model(tenant_config.tenant_id, tenant_config)
            if not ai_model:
                return "Lo siento, no puedo procesar tu solicitud en este momento."
            
            # Si use_documentation es True, cargar documentación del tenant
            documentation_context = ""
            if use_documentation and tenant_config.ai_config and tenant_config.ai_config.get("documentation_bucket_url"):
                # Aquí podrías cargar documentación del bucket
                # Por ahora, dejarlo vacío
                pass
            
            # Generar respuesta
            full_prompt = f"{documentation_context}\n\n{prompt}" if documentation_context else prompt
            response = ai_model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 500
                }
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error al procesar prompt simple: {e}")
            return "Lo siento, hubo un error al procesar tu solicitud."
"""
Manejador de acciones de información y publicidad
"""

import logging
from typing import Dict, Any

from chatbot_ai_service.models.intent_models import IntentClassification
from chatbot_ai_service.models.tenant_models import TenantConfig

logger = logging.getLogger(__name__)

class InformationActionHandler:
    """Manejador para acciones de información y publicidad"""
    
    async def handle_informative_answer_from_documents(self, classification: IntentClassification, tenant_config: TenantConfig) -> Dict[str, Any]:
        """Responde usando RAG con documentos del bucket del tenant.

        Usa el orquestador RAG para recuperar documentos y generar una respuesta
        fundamentada. Si falla, retorna success=False para permitir fallbacks.
        """
        try:
            # Cargar RAG con Gemini y servicios ya integrados
            from chatbot_ai_service.clients.gemini_client import GeminiClient
            from chatbot_ai_service.orchestrators.rag_orchestrator import RAGOrchestrator

            gemini = GeminiClient()
            rag = RAGOrchestrator(gemini_client=gemini)

            tenant_id = getattr(classification, 'tenant_id', None) or tenant_config.tenant_id
            query = getattr(classification, 'original_message', None) or getattr(classification, 'message', None) or ""

            if not tenant_id or not query:
                return {"success": False, "error": "tenant_id o query vacíos"}

            # Incluir contexto mínimo (historial se agrega dentro si está disponible)
            response_text = await rag.process_query_simple(
                query=query,
                tenant_id=str(tenant_id),
                user_context={},
                tenant_config=getattr(tenant_config, '__dict__', None) or {}
            )

            if response_text and isinstance(response_text, str):
                return {
                    "success": True,
                    "action": "rag_answer",
                    "response_message": response_text,
                    "requires_human": False
                }

            return {"success": False, "error": "Respuesta vacía de RAG"}

        except Exception as e:
            logger.error(f"Error en RAG (información desde documentos): {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def handle_advertising_info_action(classification: IntentClassification, tenant_config: TenantConfig) -> Dict[str, Any]:
        """Maneja solicitudes de material publicitario"""
        try:
            # Obtener link de formularios desde configuración del tenant
            forms_link = tenant_config.link_forms
            
            if not forms_link:
                forms_link = "https://forms.gle/publicidad-candidato"  # Link por defecto
            
            response_message = f"{classification.action.response_message} {forms_link}"
            
            return {
                "success": True,
                "action": "forms_redirect",
                "response_message": response_message,
                "redirect_url": forms_link,
                "requires_human": False
            }
            
        except Exception as e:
            logger.error(f"Error al manejar solicitud de publicidad: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def handle_know_candidate_action(classification: IntentClassification, tenant_config: TenantConfig) -> Dict[str, Any]:
        """Maneja solicitudes para conocer al candidato"""
        try:
            response_message = classification.action.response_message
            
            # Agregar información sobre notificaciones de ciudad
            city_notification = "Te avisaremos cuando el candidato visite tu ciudad para que puedas conocerlo en persona."
            response_message += f" {city_notification}"
            
            return {
                "success": True,
                "action": "dqbot_redirect",
                "response_message": response_message,
                "redirect_to_dqbot": True,
                "city_notification_enabled": True
            }
            
        except Exception as e:
            logger.error(f"Error al manejar solicitud de conocer al candidato: {e}")
            return {"success": False, "error": str(e)}

"""
Servicio refactorizado para manejar acciones específicas según las intenciones clasificadas
"""

import logging
from typing import Dict, Any

from chatbot_ai_service.models.intent_models import IntentClassification, IntentCategory
from chatbot_ai_service.models.tenant_models import TenantConfig
from chatbot_ai_service.services.tenant_service import TenantService
from chatbot_ai_service.config.firebase_config import FirebaseConfig

# Importar manejadores específicos
from chatbot_ai_service.services.action_handlers.malicious_action_handler import MaliciousActionHandler
from chatbot_ai_service.services.action_handlers.appointment_action_handler import AppointmentActionHandler
from chatbot_ai_service.services.action_handlers.information_action_handler import InformationActionHandler
from chatbot_ai_service.services.action_handlers.data_action_handler import DataActionHandler
from chatbot_ai_service.services.action_handlers.collaboration_action_handler import CollaborationActionHandler
from chatbot_ai_service.services.action_handlers.support_action_handler import SupportActionHandler

logger = logging.getLogger(__name__)

class ActionHandlerServiceRefactored:
    """Servicio refactorizado para ejecutar acciones específicas según intenciones"""
    
    def __init__(self, tenant_service: TenantService, firebase_config: FirebaseConfig):
        self.tenant_service = tenant_service
        self.firebase_config = firebase_config
        
        # Inicializar manejadores específicos
        self.malicious_handler = MaliciousActionHandler(firebase_config)
        self.appointment_handler = AppointmentActionHandler()
        self.information_handler = InformationActionHandler()
        self.data_handler = DataActionHandler()
        self.collaboration_handler = CollaborationActionHandler()
        self.support_handler = SupportActionHandler(firebase_config)
    
    async def execute_action(self, classification: IntentClassification, tenant_config: TenantConfig) -> Dict[str, Any]:
        """
        Ejecuta la acción correspondiente según la clasificación de intención
        """
        try:
            logger.info(f"Ejecutando acción para intención {classification.category} en tenant {classification.original_message}")
            
            action_type = classification.category
            
            if action_type == IntentCategory.MALICIOSO:
                return await self.malicious_handler.handle_malicious_action(classification, tenant_config)
            
            elif action_type == IntentCategory.CITA_CAMPANA:
                return await self.appointment_handler.handle_campaign_appointment_action(classification, tenant_config)
            
            elif action_type == IntentCategory.SALUDO_APOYO:
                # Intento 1: RAG con documentos del bucket (respuesta coherente)
                try:
                    rag_resp = await self.information_handler.handle_informative_answer_from_documents(classification, tenant_config)
                    if rag_resp and rag_resp.get("success") and rag_resp.get("response_message"):
                        return rag_resp
                except Exception as _e:
                    logger.warning(f"SALUDO_APOYO RAG fallback: {_e}")
                # Intento 2: saludo por defecto
                return await self.appointment_handler.handle_support_greeting_action(classification, tenant_config)
            
            elif action_type == IntentCategory.PUBLICIDAD_INFO:
                return await self.information_handler.handle_advertising_info_action(classification, tenant_config)
            
            elif action_type == IntentCategory.CONOCER_CANDIDATO:
                return await self.information_handler.handle_know_candidate_action(classification, tenant_config)
            
            elif action_type == IntentCategory.ACTUALIZACION_DATOS:
                return await self.data_handler.handle_data_update_action(classification, tenant_config)
            
            elif action_type == IntentCategory.SOLICITUD_FUNCIONAL:
                return await self.data_handler.handle_functional_request_action(classification, tenant_config)
            
            elif action_type == IntentCategory.COLABORACION_VOLUNTARIADO:
                return await self.collaboration_handler.handle_volunteer_collaboration_action(classification, tenant_config)
            
            elif action_type == IntentCategory.QUEJAS:
                return await self.support_handler.handle_complaint_action(classification, tenant_config)
            
            elif action_type == IntentCategory.LIDER:
                return await self.support_handler.handle_leader_action(classification, tenant_config)
            
            elif action_type == IntentCategory.ATENCION_HUMANO:
                return await self.support_handler.handle_human_attention_action(classification, tenant_config)
            
            elif action_type == IntentCategory.ATENCION_EQUIPO_INTERNO:
                return await self.support_handler.handle_internal_team_action(classification, tenant_config)
            
            else:
                return await self._handle_fallback_action(classification, tenant_config)
                
        except Exception as e:
            logger.error(f"Error al ejecutar acción para intención {classification.category}: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": "Lo siento, no pude procesar tu solicitud. ¿Puedes intentar de nuevo?"
            }
    
    async def _handle_fallback_action(self, classification: IntentClassification, tenant_config: TenantConfig) -> Dict[str, Any]:
        """Maneja acciones de fallback"""
        return {
            "success": True,
            "action": "fallback",
            "response_message": classification.action.response_message,
            "fallback": True
        }

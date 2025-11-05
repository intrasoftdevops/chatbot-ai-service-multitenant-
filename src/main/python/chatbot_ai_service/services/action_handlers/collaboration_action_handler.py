"""
Manejador de acciones de colaboración y voluntariado
"""

import logging
from typing import Dict, Any

from chatbot_ai_service.models.intent_models import IntentClassification
from chatbot_ai_service.models.tenant_models import TenantConfig

logger = logging.getLogger(__name__)

class CollaborationActionHandler:
    """Manejador para acciones de colaboración y voluntariado"""
    
    @staticmethod
    async def handle_volunteer_collaboration_action(classification: IntentClassification, tenant_config: TenantConfig) -> Dict[str, Any]:
        """Maneja ofrecimientos de colaboración y voluntariado"""
        try:
            response_message = classification.action.response_message
            
            collaboration_areas = classification.action.parameters.get("collaboration_areas", [])
            
            # Formatear áreas de colaboración
            areas_text = "\n".join([f"{i+1}. {area}" for i, area in enumerate(collaboration_areas)])
            response_message += f"\n\n{areas_text}"
            
            return {
                "success": True,
                "action": "volunteer_classification",
                "response_message": response_message,
                "collaboration_areas": collaboration_areas,
                "requires_follow_up": True
            }
            
        except Exception as e:
            logger.error(f"Error al manejar colaboración de voluntarios: {e}")
            return {"success": False, "error": str(e)}

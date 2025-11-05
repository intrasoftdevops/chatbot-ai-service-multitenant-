"""
Servicio para extracción de datos de usuario
"""

import logging
from typing import Dict, Any, Optional

from chatbot_ai_service.models.chat_models import ChatRequest, UserState
from chatbot_ai_service.models.tenant_models import TenantConfig

logger = logging.getLogger(__name__)

class DataExtractionService:
    """Servicio para extracción de datos de usuario"""
    
    @staticmethod
    async def extract_user_data(request: ChatRequest, ai_response: str, tenant_config: TenantConfig) -> Dict[str, Any]:
        """Extrae datos del usuario desde la respuesta de IA"""
        # TODO: Implementar lógica de extracción basada en el estado del usuario
        # Por ahora retorna un diccionario vacío
        return {}
    
    @staticmethod
    async def determine_user_state(request: ChatRequest, ai_response: str, extracted_data: Dict[str, Any]) -> Optional[UserState]:
        """Determina el nuevo estado del usuario"""
        # TODO: Implementar lógica de transición de estados
        # Por ahora retorna None
        return None

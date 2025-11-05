"""
Manejador de acciones de datos y funcionalidades
"""

import logging
from typing import Dict, Any

from chatbot_ai_service.models.intent_models import IntentClassification
from chatbot_ai_service.models.tenant_models import TenantConfig

logger = logging.getLogger(__name__)

class DataActionHandler:
    """Manejador para acciones de datos y funcionalidades"""
    
    @staticmethod
    async def handle_data_update_action(classification: IntentClassification, tenant_config: TenantConfig) -> Dict[str, Any]:
        """Maneja solicitudes de actualización de datos"""
        try:
            response_message = classification.action.response_message
            
            # Obtener campos disponibles para actualización
            available_fields = classification.action.parameters.get("data_fields", [])
            
            return {
                "success": True,
                "action": "data_update",
                "response_message": response_message,
                "available_fields": available_fields,
                "dynamic_update": True
            }
            
        except Exception as e:
            logger.error(f"Error al manejar actualización de datos: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def handle_functional_request_action(classification: IntentClassification, tenant_config: TenantConfig) -> Dict[str, Any]:
        """Maneja solicitudes funcionales del sistema"""
        try:
            # Determinar tipo de consulta funcional
            query_type = DataActionHandler._determine_functional_query_type(classification.original_message)
            
            response_message = classification.action.response_message
            
            if query_type == "points":
                response_message += " Aquí están tus puntos y ranking actual."
            elif query_type == "tribe":
                response_message += " Aquí tienes el link de tu tribu."
            elif query_type == "referrals":
                response_message += " Te muestro cuántas personas tienes debajo."
            
            return {
                "success": True,
                "action": "functional_response",
                "response_message": response_message,
                "query_type": query_type,
                "available_queries": classification.action.parameters.get("available_queries", [])
            }
            
        except Exception as e:
            logger.error(f"Error al manejar solicitud funcional: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _determine_functional_query_type(message: str) -> str:
        """Determina el tipo de consulta funcional"""
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ["puntos", "puntaje", "ranking"]):
            return "points"
        elif any(keyword in message_lower for keyword in ["tribu", "link"]):
            return "tribe"
        elif any(keyword in message_lower for keyword in ["debajo", "referidos", "personas"]):
            return "referrals"
        else:
            return "general"

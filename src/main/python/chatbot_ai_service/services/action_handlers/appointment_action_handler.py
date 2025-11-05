"""
Manejador de acciones de citas y campaña
"""

import logging
from typing import Dict, Any

from chatbot_ai_service.models.intent_models import IntentClassification
from chatbot_ai_service.models.tenant_models import TenantConfig

logger = logging.getLogger(__name__)

class AppointmentActionHandler:
    """Manejador para acciones de citas y campaña"""
    
    @staticmethod
    async def handle_campaign_appointment_action(classification: IntentClassification, tenant_config: TenantConfig) -> Dict[str, Any]:
        """Maneja solicitudes de citas de campaña"""
        try:
            # Obtener link de Calendly desde configuración del tenant
            calendly_link = tenant_config.link_calendly
            
            if not calendly_link:
                calendly_link = "https://calendly.com/candidato"  # Link por defecto
            
            response_message = f"{classification.action.response_message} {calendly_link}"
            
            return {
                "success": True,
                "action": "calendly_redirect",
                "response_message": response_message,
                "redirect_url": calendly_link,
                "requires_human": False
            }
            
        except Exception as e:
            logger.error(f"Error al manejar solicitud de cita: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def handle_support_greeting_action(classification: IntentClassification, tenant_config: TenantConfig) -> Dict[str, Any]:
        """Maneja saludos y muestras de apoyo"""
        try:
            # Personalizar mensaje según configuración del tenant
            response_message = classification.action.response_message
            
            if tenant_config.branding and tenant_config.branding.welcome_message:
                response_message = f"{tenant_config.branding.welcome_message} {response_message}"
            
            # Preparar links para compartir
            share_links = {
                "main_link": tenant_config.link_forms or "https://candidato.com",
                "points_rules": "https://candidato.com/puntos"
            }
            
            return {
                "success": True,
                "action": "support_response",
                "response_message": response_message,
                "share_links": share_links,
                "points_rules_enabled": True
            }
            
        except Exception as e:
            logger.error(f"Error al manejar saludo de apoyo: {e}")
            return {"success": False, "error": str(e)}

"""
Servicio para construcción de contexto de conversación
"""

import logging
from typing import Dict, Any

from chatbot_ai_service.models.chat_models import ChatRequest
from chatbot_ai_service.models.tenant_models import TenantConfig

logger = logging.getLogger(__name__)

class ConversationContextService:
    """Servicio para construcción de contexto de conversación"""
    
    @staticmethod
    async def build_conversation_context(request: ChatRequest, tenant_config: TenantConfig) -> str:
        """Construye el contexto de conversación"""
        context_parts = []
        
        # Contexto de documentación del tenant (prioridad alta)
        if request.documentation_context and request.documentation_context.strip():
            context_parts.append("=== INFORMACIÓN ESPECÍFICA DEL TENANT ===")
            context_parts.append(request.documentation_context)
            context_parts.append("=== FIN INFORMACIÓN ESPECÍFICA ===")
            context_parts.append("")  # Línea en blanco para separar
        
        # Contexto del tenant (branding)
        if tenant_config.branding:
            context_parts.append(f"Eres un asistente para {tenant_config.branding.welcome_message}")
            if tenant_config.branding.contact_name:
                context_parts.append(f"El nombre del contacto es: {tenant_config.branding.contact_name}")
            if tenant_config.branding.greeting_message:
                context_parts.append(f"Mensaje de saludo: {tenant_config.branding.greeting_message}")
        
        # Contexto del usuario
        user_context = request.user_context
        if user_context:
            if user_context.get("name"):
                context_parts.append(f"El usuario se llama {user_context['name']}")
            if user_context.get("state"):
                context_parts.append(f"Estado actual del usuario: {user_context['state']}")
            if user_context.get("phone"):
                context_parts.append(f"Teléfono del usuario: {user_context['phone']}")
        
        # Configuración del tenant (links, etc.)
        if request.tenant_config:
            tenant_info = request.tenant_config
            if tenant_info.get("link_calendly"):
                context_parts.append(f"Link de Calendly: {tenant_info['link_calendly']}")
            if tenant_info.get("link_forms"):
                context_parts.append(f"Link de formularios: {tenant_info['link_forms']}")
            if tenant_info.get("numero_whatsapp"):
                context_parts.append(f"Número de WhatsApp: {tenant_info['numero_whatsapp']}")
        
        # Prompts personalizados del tenant
        if tenant_config.ai_config and tenant_config.ai_config.custom_prompts:
            context_parts.append("=== PROMPTS PERSONALIZADOS ===")
            for key, prompt in tenant_config.ai_config.custom_prompts.items():
                context_parts.append(f"{key}: {prompt}")
        
        # Instrucciones generales
        context_parts.append("")
        context_parts.append("=== INSTRUCCIONES ===")
        context_parts.append("- Responde de manera natural y conversacional")
        context_parts.append("- Usa la información específica del tenant cuando sea relevante")
        context_parts.append("- Si no tienes información específica, responde de manera general pero útil")
        context_parts.append("- Mantén un tono profesional pero amigable")
        context_parts.append("- Si el usuario pregunta algo que no sabes, admítelo y ofrece ayuda alternativa")
        
        return "\n".join(context_parts)

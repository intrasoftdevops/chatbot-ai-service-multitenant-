"""
Servicios de gestión de contexto para IA
"""
import logging
import json
import re

logger = logging.getLogger(__name__)

def create_tenant_context(tenant_id: str, tenant_config: dict, documentation: str = "") -> dict:
    """
    Crea el contexto del tenant para la IA.
    
    Args:
        tenant_id: ID del tenant
        tenant_config: Configuración del tenant
        documentation: Documentación del tenant
        
    Returns:
        Contexto del tenant estructurado
    """
    try:
        logger.info(f"DEBUG - Creando contexto para tenant: {tenant_id}")
        
        # Extraer información de la configuración del tenant
        tenant_name = tenant_config.get("tenant_name", "el candidato")
        candidate_name = tenant_config.get("candidate_name", "el candidato")
        campaign_info = tenant_config.get("campaign_info", "")
        
        # Crear el contexto estructurado
        context = {
            "tenant_id": tenant_id,
            "tenant_name": tenant_name,
            "candidate_name": candidate_name,
            "campaign_info": campaign_info,
            "documentation": documentation,
            "calendly_link": tenant_config.get("calendly_link", ""),
            "forms_link": tenant_config.get("forms_link", ""),
            "privacy_url": tenant_config.get("privacy_url", ""),
            "branding": tenant_config.get("branding", {}),
            "integrations": tenant_config.get("integrations", {})
        }
        
        logger.info(f"DEBUG - Contexto creado: {json.dumps(context, indent=2)}")
        return context
        
    except Exception as e:
        logger.error(f"Error creando contexto del tenant: {str(e)}")
        return {
            "tenant_id": tenant_id,
            "tenant_name": "el candidato",
            "candidate_name": "el candidato",
            "campaign_info": "",
            "documentation": documentation,
            "calendly_link": "",
            "forms_link": "",
            "privacy_url": "",
            "branding": {},
            "integrations": {}
        }

def enrich_prompt_with_context(prompt: str, tenant_context: dict) -> str:
    """
    Enriquece un prompt con el contexto del tenant.
    
    Args:
        prompt: El prompt original
        tenant_context: Contexto del tenant
        
    Returns:
        Prompt enriquecido con contexto
    """
    try:
        logger.info(f"DEBUG - Enriqueciendo prompt con contexto del tenant")
        
        # Obtener información del contexto
        tenant_name = tenant_context.get("tenant_name", "el candidato")
        candidate_name = tenant_context.get("candidate_name", "el candidato")
        campaign_info = tenant_context.get("campaign_info", "")
        documentation = tenant_context.get("documentation", "")
        
        # Crear el prompt enriquecido
        enriched_prompt = f"""
Eres un asistente virtual especializado en campañas políticas para {tenant_name}.
Tu objetivo es ayudar a los ciudadanos con información sobre la campaña de {candidate_name}.

CONTEXTO DE LA CAMPAÑA:
{campaign_info}

DOCUMENTACIÓN DISPONIBLE:
{documentation}

PROMPT DEL USUARIO:
{prompt}

INSTRUCCIONES:
- Responde de manera profesional, amigable y contextualizada
- Usa la información de la campaña para personalizar tu respuesta
- Si no tienes información específica, sé honesto pero mantén el tono positivo
- Incluye detalles relevantes sobre {candidate_name} y sus propuestas
- Mantén un tono que inspire confianza y apoyo

RESPUESTA:
"""
        
        logger.info(f"DEBUG - Prompt enriquecido creado")
        return enriched_prompt
        
    except Exception as e:
        logger.error(f"Error enriqueciendo prompt: {str(e)}")
        return prompt

def extract_context_from_documentation(documentation: str) -> dict:
    """
    Extrae información contextual de la documentación del tenant.
    
    Args:
        documentation: Documentación del tenant
        
    Returns:
        Información contextual extraída
    """
    try:
        logger.info(f"DEBUG - Extrayendo contexto de documentación")
        
        # Inicializar el contexto extraído
        extracted_context = {
            "candidate_info": "",
            "campaign_goals": "",
            "key_proposals": "",
            "contact_info": "",
            "important_dates": "",
            "volunteer_info": ""
        }
        
        if not documentation or documentation.strip() == "":
            logger.info("DEBUG - No hay documentación disponible")
            return extracted_context
        
        # Extraer información del candidato
        candidate_patterns = [
            r"(?:candidato|nombre|name)[\s:]+([^\n]+)",
            r"(?:soy|es|llamo)[\s:]+([^\n]+)",
            r"(?:mi nombre es|me llamo)[\s:]+([^\n]+)"
        ]
        
        for pattern in candidate_patterns:
            match = re.search(pattern, documentation, re.IGNORECASE)
            if match:
                extracted_context["candidate_info"] = match.group(1).strip()
                break
        
        # Extraer objetivos de la campaña
        goals_patterns = [
            r"(?:objetivos|metas|goals)[\s:]+([^\n]+)",
            r"(?:queremos|buscamos|nuestro objetivo)[\s:]+([^\n]+)",
            r"(?:la campaña busca|el objetivo es)[\s:]+([^\n]+)"
        ]
        
        for pattern in goals_patterns:
            match = re.search(pattern, documentation, re.IGNORECASE)
            if match:
                extracted_context["campaign_goals"] = match.group(1).strip()
                break
        
        # Extraer propuestas clave
        proposals_patterns = [
            r"(?:propuestas|proposals)[\s:]+([^\n]+)",
            r"(?:nuestras propuestas|las propuestas son)[\s:]+([^\n]+)",
            r"(?:prometemos|nos comprometemos)[\s:]+([^\n]+)"
        ]
        
        for pattern in proposals_patterns:
            match = re.search(pattern, documentation, re.IGNORECASE)
            if match:
                extracted_context["key_proposals"] = match.group(1).strip()
                break
        
        # Extraer información de contacto
        contact_patterns = [
            r"(?:contacto|contact)[\s:]+([^\n]+)",
            r"(?:teléfono|phone)[\s:]+([^\n]+)",
            r"(?:email|correo)[\s:]+([^\n]+)"
        ]
        
        for pattern in contact_patterns:
            match = re.search(pattern, documentation, re.IGNORECASE)
            if match:
                extracted_context["contact_info"] = match.group(1).strip()
                break
        
        # Extraer fechas importantes
        dates_patterns = [
            r"(?:fechas|dates|importantes)[\s:]+([^\n]+)",
            r"(?:eventos|events)[\s:]+([^\n]+)",
            r"(?:calendario|calendar)[\s:]+([^\n]+)"
        ]
        
        for pattern in dates_patterns:
            match = re.search(pattern, documentation, re.IGNORECASE)
            if match:
                extracted_context["important_dates"] = match.group(1).strip()
                break
        
        # Extraer información de voluntarios
        volunteer_patterns = [
            r"(?:voluntarios|volunteers)[\s:]+([^\n]+)",
            r"(?:cómo ayudar|how to help)[\s:]+([^\n]+)",
            r"(?:participar|participate)[\s:]+([^\n]+)"
        ]
        
        for pattern in volunteer_patterns:
            match = re.search(pattern, documentation, re.IGNORECASE)
            if match:
                extracted_context["volunteer_info"] = match.group(1).strip()
                break
        
        logger.info(f"DEBUG - Contexto extraído: {json.dumps(extracted_context, indent=2)}")
        return extracted_context
        
    except Exception as e:
        logger.error(f"Error extrayendo contexto de documentación: {str(e)}")
        return {
            "candidate_info": "",
            "campaign_goals": "",
            "key_proposals": "",
            "contact_info": "",
            "important_dates": "",
            "volunteer_info": ""
        }

def merge_contexts(base_context: dict, extracted_context: dict) -> dict:
    """
    Fusiona el contexto base con el contexto extraído de la documentación.
    
    Args:
        base_context: Contexto base del tenant
        extracted_context: Contexto extraído de la documentación
        
    Returns:
        Contexto fusionado
    """
    try:
        logger.info(f"DEBUG - Fusionando contextos")
        
        # Crear el contexto fusionado
        merged_context = base_context.copy()
        
        # Fusionar información del candidato
        if extracted_context.get("candidate_info"):
            merged_context["candidate_info"] = extracted_context["candidate_info"]
        
        # Fusionar objetivos de la campaña
        if extracted_context.get("campaign_goals"):
            merged_context["campaign_goals"] = extracted_context["campaign_goals"]
        
        # Fusionar propuestas clave
        if extracted_context.get("key_proposals"):
            merged_context["key_proposals"] = extracted_context["key_proposals"]
        
        # Fusionar información de contacto
        if extracted_context.get("contact_info"):
            merged_context["contact_info"] = extracted_context["contact_info"]
        
        # Fusionar fechas importantes
        if extracted_context.get("important_dates"):
            merged_context["important_dates"] = extracted_context["important_dates"]
        
        # Fusionar información de voluntarios
        if extracted_context.get("volunteer_info"):
            merged_context["volunteer_info"] = extracted_context["volunteer_info"]
        
        logger.info(f"DEBUG - Contexto fusionado: {json.dumps(merged_context, indent=2)}")
        return merged_context
        
    except Exception as e:
        logger.error(f"Error fusionando contextos: {str(e)}")
        return base_context

def create_conversation_context(conversation_history: list, tenant_context: dict) -> dict:
    """
    Crea el contexto de la conversación para la IA.
    
    Args:
        conversation_history: Historial de la conversación
        tenant_context: Contexto del tenant
        
    Returns:
        Contexto de la conversación
    """
    try:
        logger.info(f"DEBUG - Creando contexto de conversación")
        
        # Crear el contexto de la conversación
        conversation_context = {
            "tenant_context": tenant_context,
            "conversation_history": conversation_history,
            "last_message": conversation_history[-1] if conversation_history else None,
            "message_count": len(conversation_history),
            "conversation_summary": create_conversation_summary(conversation_history)
        }
        
        logger.info(f"DEBUG - Contexto de conversación creado")
        return conversation_context
        
    except Exception as e:
        logger.error(f"Error creando contexto de conversación: {str(e)}")
        return {
            "tenant_context": tenant_context,
            "conversation_history": conversation_history,
            "last_message": None,
            "message_count": 0,
            "conversation_summary": ""
        }

def create_conversation_summary(conversation_history: list) -> str:
    """
    Crea un resumen de la conversación.
    
    Args:
        conversation_history: Historial de la conversación
        
    Returns:
        Resumen de la conversación
    """
    try:
        if not conversation_history:
            return "No hay historial de conversación"
        
        # Crear un resumen básico
        summary_parts = []
        
        # Contar tipos de mensajes
        user_messages = [msg for msg in conversation_history if msg.get("direction") == "INBOUND"]
        bot_messages = [msg for msg in conversation_history if msg.get("direction") == "OUTBOUND"]
        
        summary_parts.append(f"Conversación con {len(user_messages)} mensajes del usuario y {len(bot_messages)} respuestas del bot")
        
        # Identificar temas principales
        topics = []
        for msg in user_messages:
            content = msg.get("content", "").lower()
            if any(word in content for word in ["candidato", "propuestas", "campaña"]):
                topics.append("información sobre la campaña")
            elif any(word in content for word in ["cita", "agendar", "reunión"]):
                topics.append("agendamiento de citas")
            elif any(word in content for word in ["voluntario", "ayudar", "colaborar"]):
                topics.append("voluntariado")
            elif any(word in content for word in ["publicidad", "material"]):
                topics.append("material publicitario")
        
        if topics:
            unique_topics = list(set(topics))
            summary_parts.append(f"Temas discutidos: {', '.join(unique_topics)}")
        
        return ". ".join(summary_parts)
        
    except Exception as e:
        logger.error(f"Error creando resumen de conversación: {str(e)}")
        return "Error al crear resumen de conversación"

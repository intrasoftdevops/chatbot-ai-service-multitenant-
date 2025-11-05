"""
Servicios de procesamiento de respuestas de IA
"""
import logging
import json
import re

logger = logging.getLogger(__name__)

def process_ai_response(response: str, intent: str, tenant_context: dict) -> str:
    """
    Procesa la respuesta de la IA según la intención y contexto.
    
    Args:
        response: Respuesta de la IA
        intent: Intención detectada
        tenant_context: Contexto del tenant
        
    Returns:
        Respuesta procesada
    """
    try:
        logger.info(f"DEBUG - Procesando respuesta de IA para intención: {intent}")
        
        # Procesar según la intención
        if intent == "cita_campaña":
            return process_cita_response(response, tenant_context)
        elif intent == "publicidad_info":
            return process_publicidad_response(response, tenant_context)
        elif intent == "conocer_candidato":
            return process_candidato_response(response, tenant_context)
        elif intent == "colaboracion_voluntariado":
            return process_voluntariado_response(response, tenant_context)
        elif intent == "quejas":
            return process_quejas_response(response, tenant_context)
        elif intent == "lider":
            return process_lider_response(response, tenant_context)
        elif intent == "atencion_humano":
            return process_atencion_humano_response(response, tenant_context)
        elif intent == "solicitud_funcional":
            return process_funcional_response(response, tenant_context)
        elif intent == "actualizacion_datos":
            return process_actualizacion_response(response, tenant_context)
        elif intent == "atencion_equipo_interno":
            return process_equipo_interno_response(response, tenant_context)
        elif intent == "malicioso":
            return process_malicioso_response(response, tenant_context)
        else:
            return process_general_response(response, tenant_context)
        
    except Exception as e:
        logger.error(f"Error procesando respuesta de IA: {str(e)}")
        return "Lo siento, no pude procesar tu solicitud en este momento."

def process_cita_response(response: str, tenant_context: dict) -> str:
    """
    Procesa respuesta para solicitudes de citas.
    """
    try:
        logger.info(f"DEBUG - Procesando respuesta de cita")
        
        # Obtener link de Calendly del contexto
        calendly_link = tenant_context.get("calendly_link", "")
        
        if calendly_link:
            return f"¡Perfecto! 📅 Aquí tienes el link para agendar tu cita:\n\n{calendly_link}\n\n" \
                   f"¿Necesitas ayuda con algo más?"
        else:
            return f"¡Perfecto! 📅 Te ayudo a agendar tu cita. " \
                   f"¿Podrías proporcionarme tu información de contacto para coordinar?"
        
    except Exception as e:
        logger.error(f"Error procesando respuesta de cita: {str(e)}")
        return "¡Perfecto! 📅 Te ayudo a agendar tu cita. ¿Necesitas ayuda con algo más?"

def process_publicidad_response(response: str, tenant_context: dict) -> str:
    """
    Procesa respuesta para solicitudes de material publicitario.
    """
    try:
        logger.info(f"DEBUG - Procesando respuesta de publicidad")
        
        # Obtener link de formularios del contexto
        forms_link = tenant_context.get("forms_link", "")
        
        if forms_link:
            return f"¡Perfecto! 📋 Aquí tienes el formulario para solicitar material publicitario:\n\n{forms_link}\n\n" \
                   f"¿Necesitas ayuda con algo más?"
        else:
            return f"¡Perfecto! 📋 Te ayudo con el material publicitario. " \
                   f"¿Qué tipo de material necesitas específicamente?"
        
    except Exception as e:
        logger.error(f"Error procesando respuesta de publicidad: {str(e)}")
        return "¡Perfecto! 📋 Te ayudo con el material publicitario. ¿Necesitas ayuda con algo más?"

def process_candidato_response(response: str, tenant_context: dict) -> str:
    """
    Procesa respuesta para información sobre el candidato.
    """
    try:
        logger.info(f"DEBUG - Procesando respuesta de candidato")
        
        # Obtener información del candidato del contexto
        candidate_name = tenant_context.get("candidate_name", "el candidato")
        campaign_info = tenant_context.get("campaign_info", "")
        
        if campaign_info:
            return f"¡Genial! 🤖 Aquí tienes información sobre {candidate_name}:\n\n{campaign_info}\n\n" \
                   f"¿Te gustaría conocer más sobre sus propuestas específicas?"
        else:
            return f"¡Genial! 🤖 Te ayudo con información sobre {candidate_name}. " \
                   f"¿Qué aspecto específico te interesa conocer?"
        
    except Exception as e:
        logger.error(f"Error procesando respuesta de candidato: {str(e)}")
        return "¡Genial! 🤖 Te ayudo con información sobre el candidato. ¿Necesitas ayuda con algo más?"

def process_voluntariado_response(response: str, tenant_context: dict) -> str:
    """
    Procesa respuesta para solicitudes de voluntariado.
    """
    try:
        logger.info(f"DEBUG - Procesando respuesta de voluntariado")
        
        # Obtener información de voluntarios del contexto
        volunteer_info = tenant_context.get("volunteer_info", "")
        candidate_name = tenant_context.get("candidate_name", "el candidato")
        
        if volunteer_info:
            return f"¡Excelente! 🙌 Nos encanta que quieras ser parte del equipo de {candidate_name}.\n\n" \
                   f"Áreas de voluntariado disponibles:\n{volunteer_info}\n\n" \
                   f"¿En qué área te gustaría colaborar?"
        else:
            return f"¡Excelente! 🙌 Nos encanta que quieras ser parte del equipo de {candidate_name}. " \
                   f"¿En qué área te gustaría colaborar? Tenemos oportunidades en redes sociales, " \
                   f"comunicaciones, logística y territorial."
        
    except Exception as e:
        logger.error(f"Error procesando respuesta de voluntariado: {str(e)}")
        return "¡Excelente! 🙌 Nos encanta que quieras ser parte del equipo. ¿En qué área te gustaría colaborar?"

def process_quejas_response(response: str, tenant_context: dict) -> str:
    """
    Procesa respuesta para quejas y reclamos.
    """
    try:
        logger.info(f"DEBUG - Procesando respuesta de quejas")
        
        return f"Lamento mucho que hayas tenido una experiencia negativa. 😔 " \
               f"Tu feedback es muy importante para nosotros. " \
               f"¿Podrías contarme más detalles sobre el problema para poder ayudarte mejor?"
        
    except Exception as e:
        logger.error(f"Error procesando respuesta de quejas: {str(e)}")
        return "Lamento mucho que hayas tenido una experiencia negativa. ¿Podrías contarme más detalles?"

def process_lider_response(response: str, tenant_context: dict) -> str:
    """
    Procesa respuesta para líderes comunitarios.
    """
    try:
        logger.info(f"DEBUG - Procesando respuesta de líder")
        
        candidate_name = tenant_context.get("candidate_name", "el candidato")
        
        return f"¡Fantástico! 🏆 Como líder comunitario, tu apoyo es crucial para la campaña de {candidate_name}. " \
               f"¿Te gustaría coordinar alguna actividad en tu comunidad o necesitas material específico?"
        
    except Exception as e:
        logger.error(f"Error procesando respuesta de líder: {str(e)}")
        return "¡Fantástico! 🏆 Como líder comunitario, tu apoyo es crucial. ¿Te gustaría coordinar alguna actividad?"

def process_atencion_humano_response(response: str, tenant_context: dict) -> str:
    """
    Procesa respuesta para solicitudes de atención humana.
    """
    try:
        logger.info(f"DEBUG - Procesando respuesta de atención humana")
        
        candidate_name = tenant_context.get("candidate_name", "el candidato")
        
        return f"Entiendo que prefieres hablar con una persona. 👥 " \
               f"Te voy a conectar con uno de nuestros voluntarios del equipo de {candidate_name}. " \
               f"¿Podrías esperar un momento?"
        
    except Exception as e:
        logger.error(f"Error procesando respuesta de atención humana: {str(e)}")
        return "Entiendo que prefieres hablar con una persona. Te voy a conectar con uno de nuestros voluntarios."

def process_funcional_response(response: str, tenant_context: dict) -> str:
    """
    Procesa respuesta para solicitudes funcionales.
    """
    try:
        logger.info(f"DEBUG - Procesando respuesta funcional")
        
        return f"¡Perfecto! 📊 Te ayudo con la información de tu cuenta. " \
               f"¿Te gustaría saber sobre tus puntos, tu tribu o tus referidos?"
        
    except Exception as e:
        logger.error(f"Error procesando respuesta funcional: {str(e)}")
        return "¡Perfecto! 📊 Te ayudo con la información de tu cuenta. ¿Qué necesitas saber?"

def process_actualizacion_response(response: str, tenant_context: dict) -> str:
    """
    Procesa respuesta para solicitudes de actualización de datos.
    """
    try:
        logger.info(f"DEBUG - Procesando respuesta de actualización")
        
        return f"¡Por supuesto! 📝 Te ayudo a actualizar tu información. " \
               f"¿Qué datos necesitas modificar?"
        
    except Exception as e:
        logger.error(f"Error procesando respuesta de actualización: {str(e)}")
        return "¡Por supuesto! 📝 Te ayudo a actualizar tu información. ¿Qué datos necesitas modificar?"

def process_equipo_interno_response(response: str, tenant_context: dict) -> str:
    """
    Procesa respuesta para solicitudes del equipo interno.
    """
    try:
        logger.info(f"DEBUG - Procesando respuesta de equipo interno")
        
        return f"Entiendo que necesitas información interna. 🔒 " \
               f"Voy a validar tus permisos y conectar contigo con el BackOffice."
        
    except Exception as e:
        logger.error(f"Error procesando respuesta de equipo interno: {str(e)}")
        return "Entiendo que necesitas información interna. Voy a validar tus permisos."

def process_malicioso_response(response: str, tenant_context: dict) -> str:
    """
    Procesa respuesta para mensajes maliciosos.
    """
    try:
        logger.info(f"DEBUG - Procesando respuesta maliciosa")
        
        candidate_name = tenant_context.get("candidate_name", "el candidato")
        
        return f"Lo siento, pero no puedo ayudarte con ese tipo de solicitudes. " \
               f"Si tienes alguna consulta legítima sobre la campaña de {candidate_name}, " \
               f"estaré encantado de ayudarte."
        
    except Exception as e:
        logger.error(f"Error procesando respuesta maliciosa: {str(e)}")
        return "Lo siento, pero no puedo ayudarte con ese tipo de solicitudes."

def process_general_response(response: str, tenant_context: dict) -> str:
    """
    Procesa respuesta para consultas generales.
    """
    try:
        logger.info(f"DEBUG - Procesando respuesta general")
        
        candidate_name = tenant_context.get("candidate_name", "el candidato")
        
        return f"¡Gracias por tu consulta! 😊 " \
               f"Estoy aquí para ayudarte con información sobre la campaña de {candidate_name}. " \
               f"¿Hay algo específico en lo que pueda asistirte?"
        
    except Exception as e:
        logger.error(f"Error procesando respuesta general: {str(e)}")
        return "¡Gracias por tu consulta! 😊 ¿En qué puedo ayudarte?"

def enhance_response_with_context(response: str, tenant_context: dict) -> str:
    """
    Enriquece la respuesta con información del contexto del tenant.
    
    Args:
        response: Respuesta original
        tenant_context: Contexto del tenant
        
    Returns:
        Respuesta enriquecida
    """
    try:
        logger.info(f"DEBUG - Enriqueciendo respuesta con contexto")
        
        # Obtener información del contexto
        candidate_name = tenant_context.get("candidate_name", "el candidato")
        tenant_name = tenant_context.get("tenant_name", "la campaña")
        
        # Reemplazar placeholders genéricos con información específica
        enhanced_response = response.replace("el candidato", candidate_name)
        enhanced_response = enhanced_response.replace("la campaña", tenant_name)
        
        # Agregar información de contacto si está disponible
        contact_info = tenant_context.get("contact_info", "")
        if contact_info and "contacto" not in enhanced_response.lower():
            enhanced_response += f"\n\n📞 Información de contacto:\n{contact_info}"
        
        logger.info(f"DEBUG - Respuesta enriquecida: {enhanced_response}")
        return enhanced_response
        
    except Exception as e:
        logger.error(f"Error enriqueciendo respuesta: {str(e)}")
        return response

def validate_response_quality(response: str) -> Dict[str, any]:
    """
    Valida la calidad de la respuesta generada.
    
    Args:
        response: Respuesta a validar
        
    Returns:
        Diccionario con métricas de calidad
    """
    try:
        logger.info(f"DEBUG - Validando calidad de respuesta")
        
        quality_metrics = {
            "word_count": len(response.split()),
            "has_greeting": bool(re.search(r'(hola|hi|hello|buenos|buenas)', response, re.IGNORECASE)),
            "has_emoji": bool(re.search(r'[😀-🙏]', response)),
            "has_question": bool(re.search(r'\?', response)),
            "has_contact_info": bool(re.search(r'(contacto|teléfono|email|whatsapp)', response, re.IGNORECASE)),
            "is_too_short": len(response.split()) < 5,
            "is_too_long": len(response.split()) > 200,
            "quality_score": 0.0
        }
        
        # Calcular puntuación de calidad
        quality_factors = [
            quality_metrics["has_greeting"],
            quality_metrics["has_emoji"],
            quality_metrics["has_question"],
            not quality_metrics["is_too_short"],
            not quality_metrics["is_too_long"]
        ]
        
        quality_score = sum(quality_factors) / len(quality_factors)
        quality_metrics["quality_score"] = quality_score
        
        logger.info(f"DEBUG - Métricas de calidad: {json.dumps(quality_metrics, indent=2)}")
        return quality_metrics
        
    except Exception as e:
        logger.error(f"Error validando calidad de respuesta: {str(e)}")
        return {
            "word_count": 0,
            "has_greeting": False,
            "has_emoji": False,
            "has_question": False,
            "has_contact_info": False,
            "is_too_short": True,
            "is_too_long": False,
            "quality_score": 0.0
        }

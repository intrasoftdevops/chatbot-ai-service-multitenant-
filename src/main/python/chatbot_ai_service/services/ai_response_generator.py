"""
Servicios de generación de respuestas usando IA
"""
import logging
import json
import re

logger = logging.getLogger(__name__)

def generate_contextual_response(prompt: str, tenant_context: dict) -> str:
    """
    Genera una respuesta contextualizada usando IA.
    
    Args:
        prompt: El prompt del usuario
        tenant_context: Contexto del tenant (documentación, branding, etc.)
        
    Returns:
        Respuesta generada por la IA
    """
    try:
        logger.info(f"DEBUG - Generando respuesta contextual para prompt: '{prompt}'")
        
        # Crear un prompt enriquecido con el contexto del tenant
        enriched_prompt = create_enriched_prompt(prompt, tenant_context)
        
        # Simular respuesta de IA (en un sistema real usarías GPT o similar)
        response = process_response_generation_with_ai(enriched_prompt, tenant_context)
        
        logger.info(f"DEBUG - Respuesta generada: '{response}'")
        return response
        
    except Exception as e:
        logger.error(f"Error generando respuesta contextual: {str(e)}")
        return "Lo siento, no pude procesar tu solicitud en este momento."

def create_enriched_prompt(prompt: str, tenant_context: dict) -> str:
    """
    Crea un prompt enriquecido con el contexto del tenant.
    """
    try:
        # Obtener información del tenant
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
        
        return enriched_prompt
        
    except Exception as e:
        logger.error(f"Error creando prompt enriquecido: {str(e)}")
        return prompt

def process_response_generation_with_ai(enriched_prompt: str, tenant_context: dict) -> str:
    """
    Procesa la generación de respuestas usando IA.
    En un sistema real, aquí conectarías con GPT, Claude, o similar.
    """
    try:
        logger.info(f"DEBUG - Procesando generación de respuesta con contexto del tenant")
        
        # Extraer el prompt original del usuario
        user_prompt = ""
        if "PROMPT DEL USUARIO:" in enriched_prompt:
            start = enriched_prompt.find("PROMPT DEL USUARIO:") + len("PROMPT DEL USUARIO:")
            end = enriched_prompt.find("\n\nINSTRUCCIONES:", start)
            if end > start:
                user_prompt = enriched_prompt[start:end].strip()
        
        if not user_prompt:
            user_prompt = enriched_prompt
        
        logger.info(f"DEBUG - Prompt del usuario extraído: '{user_prompt}'")
        
        # Obtener información del tenant
        tenant_name = tenant_context.get("tenant_name", "el candidato")
        candidate_name = tenant_context.get("candidate_name", "el candidato")
        campaign_info = tenant_context.get("campaign_info", "")
        
        # Lógica simple de generación de respuestas basada en patrones
        user_prompt_lower = user_prompt.lower()
        
        # Respuestas para saludos
        if any(word in user_prompt_lower for word in ["hola", "hi", "hello", "buenos", "buenas"]):
            return f"¡Hola! 👋 ¡Muchas gracias por tu apoyo a la campaña de {candidate_name}! " \
                   f"Tu respaldo es fundamental para lograr el cambio que necesitamos. " \
                   f"¿En qué puedo ayudarte hoy?"
        
        # Respuestas para información sobre el candidato
        if any(word in user_prompt_lower for word in ["candidato", "conocer", "trayectoria", "propuestas", "quién es", "quien es"]):
            return f"¡Genial! 🤖 Aquí tienes información sobre {candidate_name}:\n\n" \
                   f"{campaign_info}\n\n" \
                   f"¿Te gustaría conocer más sobre sus propuestas específicas?"
        
        # Respuestas para citas
        if any(word in user_prompt_lower for word in ["cita", "agendar", "reunión", "calendly"]):
            calendly_link = tenant_context.get("calendly_link", "Link no disponible")
            return f"¡Perfecto! 📅 Aquí tienes el link para agendar tu cita:\n\n{calendly_link}"
        
        # Respuestas para material publicitario
        if any(word in user_prompt_lower for word in ["publicidad", "material", "volantes", "pancartas"]):
            forms_link = tenant_context.get("forms_link", "Link no disponible")
            return f"¡Perfecto! 📋 Aquí tienes el formulario para solicitar material publicitario:\n\n{forms_link}"
        
        # Respuestas para voluntariado
        if any(word in user_prompt_lower for word in ["voluntario", "ayudar", "colaborar", "participar"]):
            return f"¡Excelente! 🙌 Nos encanta que quieras ser parte del equipo de {candidate_name}. " \
                   f"¿En qué área te gustaría colaborar? " \
                   f"Tenemos oportunidades en redes sociales, comunicaciones, logística y territorial."
        
        # Respuestas para quejas
        if any(word in user_prompt_lower for word in ["queja", "reclamo", "problema", "mal servicio"]):
            return f"Lamento mucho que hayas tenido una experiencia negativa. 😔 " \
                   f"Tu feedback es muy importante para nosotros. " \
                   f"¿Podrías contarme más detalles sobre el problema para poder ayudarte mejor?"
        
        # Respuestas para líderes
        if any(word in user_prompt_lower for word in ["líder", "liderazgo", "comunidad", "barrio", "vereda"]):
            return f"¡Fantástico! 🏆 Como líder comunitario, tu apoyo es crucial para la campaña de {candidate_name}. " \
                   f"¿Te gustaría coordinar alguna actividad en tu comunidad o necesitas material específico?"
        
        # Respuestas para atención humana
        if any(word in user_prompt_lower for word in ["humano", "persona", "agente", "operador"]):
            return f"Entiendo que prefieres hablar con una persona. 👥 " \
                   f"Te voy a conectar con uno de nuestros voluntarios del equipo de {candidate_name}. " \
                   f"¿Podrías esperar un momento?"
        
        # Respuestas para información funcional
        if any(word in user_prompt_lower for word in ["cómo voy", "mis puntos", "mi tribu", "referidos"]):
            return f"¡Perfecto! 📊 Te ayudo con la información de tu cuenta. " \
                   f"¿Te gustaría saber sobre tus puntos, tu tribu o tus referidos?"
        
        # Respuesta genérica
        return f"¡Gracias por tu consulta! 😊 " \
               f"Estoy aquí para ayudarte con información sobre la campaña de {candidate_name}. " \
               f"¿Hay algo específico en lo que pueda asistirte?"
        
    except Exception as e:
        logger.error(f"Error en procesamiento de generación de respuesta: {str(e)}")
        return "Lo siento, no pude procesar tu solicitud en este momento."

def generate_intent_response(intent: str, tenant_context: dict) -> str:
    """
    Genera una respuesta específica para una intención detectada.
    
    Args:
        intent: La intención detectada
        tenant_context: Contexto del tenant
        
    Returns:
        Respuesta generada para la intención
    """
    try:
        logger.info(f"DEBUG - Generando respuesta para intención: '{intent}'")
        
        # Obtener información del tenant
        candidate_name = tenant_context.get("candidate_name", "el candidato")
        
        # Mapeo de intenciones a respuestas
        intent_responses = {
            "saludo_apoyo": f"¡Hola! 👋 ¡Muchas gracias por tu apoyo a la campaña de {candidate_name}! " \
                           f"Tu respaldo es fundamental para lograr el cambio que necesitamos. " \
                           f"¿En qué puedo ayudarte hoy?",
            
            "conocer_candidato": f"¡Genial! 🤖 Aquí tienes información sobre {candidate_name}:\n\n" \
                                f"{tenant_context.get('campaign_info', 'Información no disponible')}\n\n" \
                                f"¿Te gustaría conocer más sobre sus propuestas específicas?",
            
            "cita_campaña": f"¡Perfecto! 📅 Aquí tienes el link para agendar tu cita:\n\n" \
                           f"{tenant_context.get('calendly_link', 'Link no disponible')}",
            
            "publicidad_info": f"¡Perfecto! 📋 Aquí tienes el formulario para solicitar material publicitario:\n\n" \
                              f"{tenant_context.get('forms_link', 'Link no disponible')}",
            
            "colaboracion_voluntariado": f"¡Excelente! 🙌 Nos encanta que quieras ser parte del equipo de {candidate_name}. " \
                                        f"¿En qué área te gustaría colaborar? " \
                                        f"Tenemos oportunidades en redes sociales, comunicaciones, logística y territorial.",
            
            "quejas": f"Lamento mucho que hayas tenido una experiencia negativa. 😔 " \
                     f"Tu feedback es muy importante para nosotros. " \
                     f"¿Podrías contarme más detalles sobre el problema para poder ayudarte mejor?",
            
            "lider": f"¡Fantástico! 🏆 Como líder comunitario, tu apoyo es crucial para la campaña de {candidate_name}. " \
                    f"¿Te gustaría coordinar alguna actividad en tu comunidad o necesitas material específico?",
            
            "atencion_humano": f"Entiendo que prefieres hablar con una persona. 👥 " \
                              f"Te voy a conectar con uno de nuestros voluntarios del equipo de {candidate_name}. " \
                              f"¿Podrías esperar un momento?",
            
            "solicitud_funcional": f"¡Perfecto! 📊 Te ayudo con la información de tu cuenta. " \
                                  f"¿Te gustaría saber sobre tus puntos, tu tribu o tus referidos?",
            
            "actualizacion_datos": f"¡Por supuesto! 📝 Te ayudo a actualizar tu información. " \
                                  f"¿Qué datos necesitas modificar?",
            
            "atencion_equipo_interno": f"Entiendo que necesitas información interna. 🔒 " \
                                      f"Voy a validar tus permisos y conectar contigo con el BackOffice.",
            
            "malicioso": f"Lo siento, pero no puedo ayudarte con ese tipo de solicitudes. " \
                        f"Si tienes alguna consulta legítima sobre la campaña de {candidate_name}, estaré encantado de ayudarte.",
            
            "general_query": f"¡Gracias por tu consulta! 😊 " \
                            f"Estoy aquí para ayudarte con información sobre la campaña de {candidate_name}. " \
                            f"¿Hay algo específico en lo que pueda asistirte?"
        }
        
        # Obtener la respuesta para la intención
        response = intent_responses.get(intent, intent_responses["general_query"])
        
        logger.info(f"DEBUG - Respuesta generada para intención '{intent}': '{response}'")
        return response
        
    except Exception as e:
        logger.error(f"Error generando respuesta para intención: {str(e)}")
        return "Lo siento, no pude procesar tu solicitud en este momento."

def generate_registration_prompt(user_state: str, tenant_context: dict) -> str:
    """
    Genera un prompt de registro contextualizado según el estado del usuario.
    
    Args:
        user_state: El estado actual del usuario en el registro
        tenant_context: Contexto del tenant
        
    Returns:
        Prompt de registro generado
    """
    try:
        logger.info(f"DEBUG - Generando prompt de registro para estado: '{user_state}'")
        
        # Obtener información del tenant
        candidate_name = tenant_context.get("candidate_name", "el candidato")
        
        # Mapeo de estados a prompts
        state_prompts = {
            "WAITING_NAME": f"¡Hola! 👋 Bienvenido al chatbot de {candidate_name}.\n\n" \
                           f"Para comenzar, necesito algunos datos básicos:\n\n" \
                           f"¿Cuál es tu nombre?",
            
            "WAITING_LASTNAME": f"Perfecto! 😊\n\n" \
                               f"Ahora necesito tu apellido:",
            
            "WAITING_CITY": f"Excelente! 👍\n\n" \
                           f"¿En qué ciudad vives?",
            
            "WAITING_REFERRAL_CODE": f"¡Genial! 📍\n\n" \
                                    f"¿Tienes un código de referido?",
            
            "WAITING_REFERRAL_CODE_INPUT": f"¡Perfecto! 🎯\n\n" \
                                          f"Por favor escribe tu código de referido:",
            
            "WAITING_TERMS_ACCEPTANCE": f"¡Perfecto! 🎯\n\n" \
                                       f"¿Aceptas los términos y condiciones?"
        }
        
        # Obtener el prompt para el estado
        prompt = state_prompts.get(user_state, state_prompts["WAITING_NAME"])
        
        logger.info(f"DEBUG - Prompt de registro generado: '{prompt}'")
        return prompt
        
    except Exception as e:
        logger.error(f"Error generando prompt de registro: {str(e)}")
        return "¡Hola! ¿En qué puedo ayudarte?"

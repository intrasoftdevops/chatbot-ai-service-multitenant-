from typing import Dict
import logging

logger = logging.getLogger(__name__)

class ResponseGenerator:
    """
    Generador de respuestas basado en la clasificación de intenciones políticas
    """
    
    @staticmethod
    def generate_response(classification: Dict, tenant_id: str, tenant_config: dict = None) -> str:
        """
        Genera una respuesta apropiada basada en la clasificación de intención
        """
        intent = classification["intent"]
        confidence = classification["confidence"]
        
        # Obtener links del tenant si están disponibles
        calendly_link = None
        forms_link = None
        
        if tenant_config:
            calendly_link = tenant_config.get("link_calendly")
            forms_link = tenant_config.get("link_forms")
        
        responses = {
            "malicioso": "Lo siento, no puedo procesar ese tipo de mensajes. Por favor, mantén un tono respetuoso.",
            "cita_campaña": f"¡Perfecto! Te voy a enviar el link de Calendly para que puedas agendar una cita con nuestro equipo. 📅\n\n{calendly_link if calendly_link else 'Link no disponible'}",
            "saludo_apoyo": "¡Muchas gracias por tu apoyo! 🙏 Es muy importante para nosotros. ¿Te gustaría conocer más sobre cómo puedes ayudar compartiendo nuestro link?",
            "publicidad_info": f"Excelente pregunta sobre material publicitario. Te voy a enviar el formulario para que puedas solicitarlo. 📋\n\n{forms_link if forms_link else 'Link no disponible'}",
            "conocer_candidato": "¡Genial que quieras conocer más sobre nuestro candidato! Te voy a conectar con nuestro bot especializado que tiene toda su información. 🤖",
            "actualizacion_datos": "Por supuesto, puedo ayudarte a actualizar tus datos. ¿Qué información necesitas modificar?",
            "solicitud_funcional": "Te ayudo con información sobre tu progreso. Puedo mostrarte tus puntos, tu tribu y cómo van tus referidos. 📊",
            "colaboracion_voluntariado": "¡Excelente que quieras colaborar! Te voy a clasificar según tu área de interés: Redes sociales, Comunicaciones, Temas programáticos, Logística, etc.",
            "quejas": "Lamento que tengas una queja. Voy a registrar tu comentario para que nuestro equipo pueda revisarlo y mejorar. 📝",
            "lider": "Interesante que seas líder comunitario. Te voy a registrar en nuestra base de datos de leads para futuras coordinaciones. 👥",
            "atencion_humano": "Entiendo que necesitas hablar con una persona. Te voy a conectar con un voluntario de nuestro equipo. 👤",
            "atencion_equipo_interno": "Como miembro del equipo interno, voy a validar tus permisos y conectarte con el BackOffice. 🔐",
            "general_query": "Hola! ¿En qué más puedo ayudarte?"
        }
        
        base_response = responses.get(intent, responses["general_query"])
        
        return base_response
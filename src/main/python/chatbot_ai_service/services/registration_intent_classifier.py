"""
Servicio de clasificación de intenciones de registro

Clasifica mensajes de usuarios en proceso de registro en categorías específicas
(saludo_apoyo, publicidad_info, cita_campaña, conocer_candidato, etc.)
"""

import logging
from typing import Dict, Tuple
import google.generativeai as genai
import os

logger = logging.getLogger(__name__)

class RegistrationIntentClassifier:
    """Clasificador de intenciones durante el registro"""
    
    # Intenciones disponibles
    INTENTS = [
        "saludo_apoyo",
        "publicidad_info",
        "cita_campaña",
        "conocer_candidato",
        "registration",
        "general_query"
    ]
    
    def __init__(self):
        """Inicializa el clasificador de intenciones"""
        # Configurar API de Google Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            logger.warning("GOOGLE_API_KEY no configurada, usando solo clasificación de fallback")
            self.model = None
    
    async def classify_intent(self, message: str, tenant_id: str) -> Tuple[str, float, str]:
        """
        Clasifica la intención de un mensaje durante el registro
        
        Args:
            message: Mensaje del usuario
            tenant_id: ID del tenant
            
        Returns:
            Tuple con (intent: str, confidence: float, suggested_response: str)
        """
        try:
            # Crear prompt de clasificación
            classification_prompt = self._create_classification_prompt(message)
            
            # Intentar clasificación con IA
            if self.model:
                try:
                    response = self.model.generate_content(
                        classification_prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.1,
                            max_output_tokens=50
                        )
                    )
                    
                    ai_response = response.text.strip().lower()
                    
                    # Verificar si la respuesta es una intención válida
                    for intent in self.INTENTS:
                        if intent in ai_response:
                            suggested_response = self._get_suggested_response(intent)
                            return (intent, 0.85, suggested_response)
                    
                except Exception as e:
                    logger.warning(f"Error en clasificación con IA: {e}, usando fallback")
            
            # Fallback a clasificación por keywords
            intent = self._fallback_classification(message)
            suggested_response = self._get_suggested_response(intent)
            return (intent, 0.6, suggested_response)
            
        except Exception as e:
            logger.error(f"Error al clasificar intención: {e}")
            # En caso de error, retornar general_query
            return ("general_query", 0.3, "¿En qué puedo ayudarte?")
    
    def _create_classification_prompt(self, message: str) -> str:
        """Crea un prompt para clasificar la intención"""
        intents_desc = ", ".join(self.INTENTS)
        
        return (
            f"Clasifica la intención del siguiente mensaje del usuario. "
            f"Opciones: {intents_desc}. "
            f"Mensaje: \"{message}\"\n\n"
            f"Responde ÚNICAMENTE con el nombre de la intención, sin explicaciones."
        )
    
    def _fallback_classification(self, message: str) -> str:
        """Clasificación de fallback usando keywords"""
        
        lower_message = message.lower()
        
        # Keywords para cada intención
        saludo_keywords = ["hola", "hi", "hello", "buenos días", "buenas tardes", "buenas noches", 
                          "saludos", "apoyo", "cuenta conmigo", "estoy contigo"]
        
        publicidad_keywords = ["material", "publicidad", "volantes", "afiches", "pancartas", 
                              "propaganda", "stickers", "camisetas"]
        
        cita_keywords = ["cita", "reunión", "reunion", "encuentro", "agendar", "calendario", 
                        "calendly", "meeting", "verse", "conocernos"]
        
        candidato_keywords = ["candidato", "propuesta", "plan", "gobierno", "trayectoria", 
                             "experiencia", "quien es", "quién es", "que propone"]
        
        # Verificar keywords en orden de prioridad
        if any(keyword in lower_message for keyword in cita_keywords):
            return "cita_campaña"
        
        if any(keyword in lower_message for keyword in publicidad_keywords):
            return "publicidad_info"
        
        if any(keyword in lower_message for keyword in candidato_keywords):
            return "conocer_candidato"
        
        if any(keyword in lower_message for keyword in saludo_keywords):
            return "saludo_apoyo"
        
        # Por defecto
        return "general_query"
    
    def _get_suggested_response(self, intent: str) -> str:
        """Obtiene una respuesta sugerida basada en la intención"""
        
        responses = {
            "saludo_apoyo": (
                "¡Hola! 👋 Muchas gracias por tu apoyo. 🎉\n\n"
                "Tu respaldo es muy importante para nosotros. Te invito a:\n\n"
                "📤 Compartir nuestro link con tus amigos y familiares\n"
                "🎯 Conocer las reglas de juego y cómo sumar puntos apoyando la campaña\n\n"
                "¿Te gustaría conocer más sobre cómo participar y ganar puntos?"
            ),
            
            "publicidad_info": (
                "¡Perfecto! 📋 Para solicitar material publicitario, por favor completa el formulario que te compartiré.\n\n"
                "[NEEDS_FORMS_LINK]"
            ),
            
            "cita_campaña": (
                "¡Perfecto! 📅 Para agendar una cita puedes usar nuestro calendario en línea que te compartiré.\n\n"
                "[NEEDS_CALENDLY_LINK]"
            ),
            
            "conocer_candidato": (
                "¡Genial! 🤖 Con gusto te cuento sobre nuestro candidato, sus propuestas y trayectoria. "
                "¿Hay algún tema específico que te interese conocer?"
            ),
            
            "general_query": "¿En qué puedo ayudarte?"
        }
        
        return responses.get(intent, "¿En qué puedo ayudarte?")
    
    def is_information_intent(self, intent: str) -> bool:
        """Verifica si es una intención de información (no de registro directo)"""
        information_intents = ["saludo_apoyo", "publicidad_info", "cita_campaña", "conocer_candidato"]
        return intent in information_intents


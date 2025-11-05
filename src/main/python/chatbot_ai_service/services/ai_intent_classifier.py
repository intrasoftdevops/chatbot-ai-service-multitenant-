"""
Servicios de clasificación de intenciones usando IA
"""
import logging
import json
import re

logger = logging.getLogger(__name__)

def classify_intent_with_ai(message: str, tenant_context: dict) -> dict:
    """
    Clasifica la intención del mensaje usando IA.
    
    Args:
        message: El mensaje del usuario
        tenant_context: Contexto del tenant
        
    Returns:
        Dict con la intención clasificada y metadatos
    """
    try:
        logger.info(f"DEBUG - Clasificando intención para mensaje: '{message}'")
        
        # Crear un prompt específico para clasificación de intenciones
        classification_prompt = create_intent_classification_prompt(message, tenant_context)
        
        # Simular respuesta de IA (en un sistema real usarías GPT o similar)
        response = process_intent_classification_with_ai(classification_prompt, message)
        
        # Parsear la respuesta JSON
        try:
            result = json.loads(response)
            logger.info(f"DEBUG - Intención clasificada: {result}")
            return result
        except json.JSONDecodeError as e:
            logger.warn(f"Error al parsear JSON de clasificación: {e}")
            return {
                "intent": "general_query",
                "confidence": 0.1,
                "action_taken": "Respuesta genérica",
                "metadata": {"reason": "Error parsing AI response"}
            }
            
    except Exception as e:
        logger.error(f"Error clasificando intención: {str(e)}")
        return {
            "intent": "general_query",
            "confidence": 0.1,
            "action_taken": "Respuesta genérica",
            "metadata": {"reason": "Error in classification"}
        }

def create_intent_classification_prompt(message: str, tenant_context: dict) -> str:
    """
    Crea un prompt específico para clasificación de intenciones.
    """
    try:
        # Obtener información del tenant
        candidate_name = tenant_context.get("candidate_name", "el candidato")
        
        # Crear el prompt de clasificación
        prompt = f"""
Eres un clasificador de intenciones para un chatbot político de {candidate_name}.
Tu tarea es clasificar el mensaje del usuario en una de las 12 categorías políticas.

MENSAJE: "{message}"

CATEGORÍAS DISPONIBLES:
1. malicioso - Mensajes de spam, ataques, odio, insultos, provocación
2. cita_campaña - Solicitudes de citas, agendamiento, reuniones, Calendly
3. saludo_apoyo - Saludos, expresiones de apoyo, buenos deseos
4. publicidad_info - Solicitudes de material publicitario, volantes, pancartas
5. conocer_candidato - Preguntas sobre el candidato, trayectoria, propuestas
6. actualizacion_datos - Solicitudes de actualización de datos personales
7. solicitud_funcional - Consultas sobre funcionalidades del sistema
8. colaboracion_voluntariado - Interés en ser voluntario, colaborar, participar
9. quejas - Quejas, reclamos, problemas con el servicio
10. lider - Líderes comunitarios, barrios, veredas, asociaciones
11. atencion_humano - Solicitudes de hablar con una persona real
12. atencion_equipo_interno - Solicitudes de información interna del equipo

INSTRUCCIONES:
- Analiza el mensaje cuidadosamente
- Identifica la intención principal del usuario
- Asigna la categoría más apropiada
- Calcula un nivel de confianza (0.0 a 1.0)
- Responde SOLO con JSON válido

FORMATO DE RESPUESTA:
{{
    "intent": "categoria_detectada",
    "confidence": 0.0 a 1.0,
    "action_taken": "Acción recomendada",
    "metadata": {{
        "reason": "Explicación de la clasificación",
        "keywords": ["palabras", "clave", "detectadas"]
    }}
}}

EJEMPLOS:
- "Hola, quiero agendar una cita" → {{"intent": "cita_campaña", "confidence": 0.9, "action_taken": "Enviar link de Calendly", "metadata": {{"reason": "Solicitud clara de cita", "keywords": ["cita", "agendar"]}}}}
- "Hola, te apoyo" → {{"intent": "saludo_apoyo", "confidence": 0.8, "action_taken": "Responder con gratitud", "metadata": {{"reason": "Saludo con expresión de apoyo", "keywords": ["hola", "apoyo"]}}}}
- "Quiero conocer al candidato" → {{"intent": "conocer_candidato", "confidence": 0.9, "action_taken": "Proporcionar información del candidato", "metadata": {{"reason": "Solicitud de información sobre el candidato", "keywords": ["conocer", "candidato"]}}}}

RESPUESTA:
"""
        
        return prompt
        
    except Exception as e:
        logger.error(f"Error creando prompt de clasificación: {str(e)}")
        return f"Clasifica este mensaje: {message}"

def process_intent_classification_with_ai(prompt: str, message: str) -> str:
    """
    Procesa la clasificación de intenciones usando IA.
    En un sistema real, aquí conectarías con GPT, Claude, o similar.
    """
    try:
        logger.info(f"DEBUG - Procesando clasificación de intención para: '{message}'")
        
        message_lower = message.lower()
        
        # Lógica simple de clasificación basada en patrones
        # Patrones para cada categoría
        patterns = {
            "malicioso": [
                "spam", "ataque", "odio", "insulto", "provocación", "troll",
                "basura", "mierda", "idiota", "estúpido", "pendejo", "hijo de puta",
                "no sirves", "inútil", "corrupto", "ladrón", "mentiroso"
            ],
            "cita_campaña": [
                "cita", "agendar", "reunión", "encuentro", "calendly", "disponible",
                "cuándo", "dónde", "coordinamos", "quedamos", "nos vemos",
                "tengo tiempo", "me interesa conocer"
            ],
            "saludo_apoyo": [
                "hola", "buenos días", "buenas tardes", "buenas noches",
                "apoyo", "adelante", "éxito", "buena suerte", "te apoyo",
                "estoy contigo", "vamos", "fuerza", "ánimo"
            ],
            "publicidad_info": [
                "publicidad", "material", "volantes", "pancartas", "posters",
                "información", "folletos", "difusión", "propaganda", "merchandising"
            ],
            "conocer_candidato": [
                "candidato", "conocer", "trayectoria", "propuestas",
                "historial", "experiencia", "biografía", "quién es", "información personal",
                "quien eres", "quien sos", "que eres", "qué eres", "eres", "sos",
                "presentate", "cuéntame de ti", "hablame de ti", "quien es el candidato",
                "que es el candidato", "qué es el candidato", "información del candidato"
            ],
            "actualizacion_datos": [
                "actualizar", "cambiar", "corregir", "modificar", "mi número",
                "mi dirección", "mi nombre", "mis datos", "información incorrecta"
            ],
            "solicitud_funcional": [
                "cómo voy", "mis puntos", "mi tribu", "referidos", "estadísticas",
                "funciona", "cómo usar", "explicar", "ayuda", "tutorial"
            ],
            "colaboracion_voluntariado": [
                "voluntario", "ayudar", "colaborar", "trabajar", "participar",
                "sumarme", "unirme", "equipo", "redes sociales", "comunicaciones",
                "logística", "territorial", "elecciones"
            ],
            "quejas": [
                "queja", "reclamo", "problema", "mal servicio", "no funciona",
                "error", "fallo", "disgusto", "insatisfecho", "molesto"
            ],
            "lider": [
                "líder", "liderazgo", "comunidad", "barrio", "vereda", "corregimiento",
                "junta", "asociación", "gremio", "sindicato", "grupo"
            ],
            "atencion_humano": [
                "humano", "persona", "agente", "operador", "hablar con alguien",
                "atención", "servicio al cliente", "representante"
            ],
            "atencion_equipo_interno": [
                "equipo interno", "campaña", "staff", "trabajadores", "empleados",
                "información interna", "datos", "estadísticas", "reportes"
            ]
        }
        
        # Contar coincidencias por categoría
        scores = {}
        matched_keywords = {}
        
        for intent, intent_patterns in patterns.items():
            score = 0
            keywords = []
            for pattern in intent_patterns:
                if pattern in message_lower:
                    score += 1
                    keywords.append(pattern)
            scores[intent] = score
            matched_keywords[intent] = keywords
        
        # Encontrar la categoría con mayor puntuación
        if not any(scores.values()):
            # Si no hay coincidencias, clasificar como general
            return json.dumps({
                "intent": "general_query",
                "confidence": 0.1,
                "action_taken": "Respuesta genérica",
                "metadata": {
                    "reason": "No patterns matched",
                    "keywords": []
                }
            })
        
        best_intent = max(scores, key=scores.get)
        confidence = min(scores[best_intent] / len(patterns[best_intent]), 1.0)
        
        # Acciones recomendadas
        actions = {
            "malicioso": "Bloquear usuario y desactivar comunicaciones",
            "cita_campaña": "Enviar link de Calendly",
            "saludo_apoyo": "Responder con gratitud e invitar a compartir link",
            "publicidad_info": "Enviar forms para solicitar publicidad",
            "conocer_candidato": "Proporcionar información del candidato",
            "actualizacion_datos": "Permitir actualización dinámica de datos",
            "solicitud_funcional": "Proporcionar información funcional",
            "colaboracion_voluntariado": "Clasificar usuario según área de colaboración",
            "quejas": "Registrar en base de datos con clasificación",
            "lider": "Registrar en base de datos de leads",
            "atencion_humano": "Redireccionar a voluntario del Default Team",
            "atencion_equipo_interno": "Validar permisos y conectar con BackOffice",
            "general_query": "Respuesta genérica"
        }
        
        result = {
            "intent": best_intent,
            "confidence": confidence,
            "action_taken": actions.get(best_intent, "Acción no definida"),
            "metadata": {
                "reason": f"Matched {scores[best_intent]} patterns",
                "keywords": matched_keywords[best_intent],
                "scores": scores
            }
        }
        
        logger.info(f"DEBUG - Resultado de clasificación: {result}")
        return json.dumps(result)
        
    except Exception as e:
        logger.error(f"Error en procesamiento de clasificación: {str(e)}")
        return json.dumps({
            "intent": "general_query",
            "confidence": 0.1,
            "action_taken": "Respuesta genérica",
            "metadata": {
                "reason": "Error in processing",
                "keywords": []
            }
        })

def validate_intent_classification(classification_result: dict) -> bool:
    """
    Valida si el resultado de la clasificación es válido.
    
    Args:
        classification_result: Resultado de la clasificación
        
    Returns:
        True si es válido, False si no
    """
    try:
        # Verificar que tenga los campos requeridos
        required_fields = ["intent", "confidence", "action_taken", "metadata"]
        if not all(field in classification_result for field in required_fields):
            return False
        
        # Verificar que la intención sea válida
        valid_intents = [
            "malicioso", "cita_campaña", "saludo_apoyo", "publicidad_info",
            "conocer_candidato", "actualizacion_datos", "solicitud_funcional",
            "colaboracion_voluntariado", "quejas", "lider", "atencion_humano",
            "atencion_equipo_interno", "general_query"
        ]
        
        if classification_result["intent"] not in valid_intents:
            return False
        
        # Verificar que la confianza esté en el rango válido
        confidence = classification_result["confidence"]
        if not isinstance(confidence, (int, float)) or not 0.0 <= confidence <= 1.0:
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validando clasificación: {str(e)}")
        return False

def get_intent_confidence_threshold() -> float:
    """
    Obtiene el umbral de confianza para las clasificaciones.
    
    Returns:
        Umbral de confianza (0.0 a 1.0)
    """
    return 0.6  # 60% de confianza mínima

def is_high_confidence_classification(classification_result: dict) -> bool:
    """
    Verifica si la clasificación tiene alta confianza.
    
    Args:
        classification_result: Resultado de la clasificación
        
    Returns:
        True si tiene alta confianza, False si no
    """
    try:
        confidence = classification_result.get("confidence", 0.0)
        threshold = get_intent_confidence_threshold()
        return confidence >= threshold
    except Exception as e:
        logger.error(f"Error verificando confianza: {str(e)}")
        return False

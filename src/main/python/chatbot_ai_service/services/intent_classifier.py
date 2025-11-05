"""
Clasificador de intenciones políticas
"""
from typing import Dict
from .intent_patterns import INTENT_PATTERNS, INTENT_ACTIONS

class PoliticalIntentClassifier:
    """
    Sistema de clasificación de intenciones políticas
    Basado en las 12 categorías definidas por el usuario
    """
    
    INTENT_PATTERNS = INTENT_PATTERNS
    INTENT_ACTIONS = INTENT_ACTIONS
    
    @classmethod
    def classify_intent(cls, message: str, user_context: dict = None) -> Dict:
        """
        Clasifica el mensaje en una de las 12 categorías políticas
        """
        message_lower = message.lower()
        
        # Contar coincidencias por categoría
        scores = {}
        for intent, patterns in cls.INTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if pattern in message_lower:
                    score += 1
            scores[intent] = score
        
        # Encontrar la categoría con mayor puntuación
        if not any(scores.values()):
            # Si no hay coincidencias, clasificar como general
            return {
                "intent": "general_query",
                "confidence": 0.1,
                "action_taken": "Respuesta genérica",
                "metadata": {"reason": "No patterns matched"}
            }
        
        best_intent = max(scores, key=scores.get)
        confidence = min(scores[best_intent] / len(cls.INTENT_PATTERNS[best_intent]), 1.0)
        
        return {
            "intent": best_intent,
            "confidence": confidence,
            "action_taken": cls.INTENT_ACTIONS.get(best_intent, "Acción no definida"),
            "metadata": {
                "scores": scores,
                "matched_patterns": scores[best_intent]
            }
        }
    
    @classmethod
    def classify_intent_with_context(cls, message: str, user_context: dict) -> dict:
        """
        Clasifica la intención considerando el contexto de la conversación
        """
        # Obtener historial de mensajes si está disponible
        recent_messages = user_context.get("recent_messages", [])
        conversation_context = user_context.get("conversation_context", {})
        
        # Clasificación base
        base_classification = cls.classify_intent(message, user_context)
        
        # Ajustar confianza basado en el contexto
        context_adjustment = 0.0
        
        # Si hay mensajes recientes, analizar el patrón de conversación
        if recent_messages:
            # Buscar patrones de continuación de conversación
            last_user_message = None
            for msg in reversed(recent_messages):
                if msg.get("direction") == "INBOUND":
                    last_user_message = msg.get("content", "").lower()
                    break
            
            if last_user_message:
                # Si el mensaje actual parece una continuación, aumentar confianza
                continuation_keywords = ["sí", "no", "ok", "vale", "perfecto", "gracias", "claro", "entiendo"]
                if any(keyword in message.lower() for keyword in continuation_keywords):
                    context_adjustment += 0.2
                
                # Si hay coherencia temática, aumentar confianza
                if base_classification["intent"] in ["cita_campaña", "publicidad_info", "conocer_candidato"]:
                    context_adjustment += 0.1
        
        # Ajustar confianza final
        adjusted_confidence = min(base_classification["confidence"] + context_adjustment, 1.0)
        base_classification["confidence"] = adjusted_confidence
        
        # Agregar información de contexto a metadata
        base_classification["metadata"]["context_used"] = len(recent_messages) > 0
        base_classification["metadata"]["context_adjustment"] = context_adjustment
        base_classification["metadata"]["message_count"] = user_context.get("message_count", 0)
        
        return base_classification

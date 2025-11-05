"""
Servicio para generación de respuestas de IA
"""

import logging
from typing import Dict, Any, List
import google.generativeai as genai

from chatbot_ai_service.models.tenant_models import TenantConfig

logger = logging.getLogger(__name__)

class AIResponseService:
    """Servicio para generación de respuestas de IA"""
    
    @staticmethod
    async def generate_ai_response(model: genai.GenerativeModel, query: str, context: str, tenant_config: TenantConfig) -> str:
        """Genera respuesta usando IA"""
        try:
            # Construir prompt completo
            full_prompt = f"""
{context}

Usuario: {query}

Asistente:"""
            
            response = model.generate_content(full_prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error al generar respuesta de IA: {e}")
            return "Lo siento, no pude procesar tu mensaje. ¿Podrías intentar de nuevo?"
    
    @staticmethod
    def build_classification_prompt(message: str, tenant_config: TenantConfig) -> str:
        """Construye prompt para clasificación de intenciones"""
        return f"""
Analiza la siguiente intención del usuario y clasifícala:

Mensaje: "{message}"

Clasifica como uno de estos tipos:
- greeting (saludo)
- question (pregunta)
- complaint (queja)
- compliment (elogio)
- request_info (solicitar información)
- registration (registro)
- referral (referido)
- general (general)

Responde en formato JSON:
{{
    "intent": "tipo_de_intencion",
    "confidence": 0.8,
    "entities": {{}},
    "suggested_actions": []
}}
"""
    
    @staticmethod
    def build_extraction_prompt(message: str, expected_fields: List[str], tenant_config: TenantConfig) -> str:
        """Construye prompt para extracción de datos"""
        fields_str = ", ".join(expected_fields) if expected_fields else "nombre, apellido, ciudad"
        
        return f"""
Extrae los siguientes datos del mensaje del usuario:

Mensaje: "{message}"

Campos esperados: {fields_str}

Responde en formato JSON:
{{
    "data": {{
        "campo": "valor_extraido"
    }},
    "confidence": 0.8,
    "missing_fields": [],
    "suggestions": {{}}
}}
"""
    
    @staticmethod
    def parse_classification_response(response_text: str) -> Dict[str, Any]:
        """Parsea la respuesta de clasificación"""
        try:
            import json
            return json.loads(response_text)
        except:
            return {"intent": "general", "confidence": 0.5}
    
    @staticmethod
    def parse_extraction_response(response_text: str) -> Dict[str, Any]:
        """Parsea la respuesta de extracción"""
        try:
            import json
            return json.loads(response_text)
        except:
            return {"data": {}, "confidence": 0.5}

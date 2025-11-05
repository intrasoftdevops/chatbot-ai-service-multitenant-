import re
import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class ReferralDetectionService:
    """
    Servicio para detectar códigos de referido en mensajes usando IA
    """
    
    async def detect_referral_code(self, message: str, tenant_id: str) -> Dict:
        """
        Detecta códigos de referido en un mensaje (método async para compatibilidad con FastAPI)
        
        Args:
            message: Mensaje del usuario
            tenant_id: ID del tenant
            
        Returns:
            Dict con referral_code, referred_by_phone y confidence
        """
        return self.detect_referral_with_ai(message)
    
    @staticmethod
    def detect_referral_with_ai(message: str) -> dict:
        """
        Usa IA para detectar códigos de referido en mensajes iniciales.
        
        Args:
            message: El mensaje del usuario
            
        Returns:
            Dict con referral_code, referred_by_phone y confidence
        """
        try:
            logger.info(f"DEBUG - Detectando referido en mensaje: '{message}'")
            
            # Crear un prompt específico para detección de referidos
            detection_prompt = f"""
Eres un detector inteligente de códigos de referido para un sistema de registro político.
Tu tarea es identificar si un mensaje contiene un código de referido válido.

MENSAJE: "{message}"

PATRONES A BUSCAR:
1. Códigos alfanuméricos de 8 caracteres (ej: ABC12345, XYZ98765)
2. Mensajes que mencionen "referido por" seguido de un código
3. Mensajes que mencionen "código" seguido de un código
4. Números de teléfono en formato +57, +1, etc.

INSTRUCCIONES:
- Si detectas un código de referido alfanumérico de 8 caracteres, extráelo
- Si detectas un número de teléfono, extráelo (formato completo con +)
- Responde SOLO con JSON válido
- Si no encuentras nada, devuelve valores null

FORMATO DE RESPUESTA:
{{
    "referral_code": "ABC12345" o null,
    "referred_by_phone": "+573001234567" o null,
    "confidence": 0.0 a 1.0
}}

EJEMPLOS:
- "Hola, vengo referido por ABC12345" → {{"referral_code": "ABC12345", "referred_by_phone": null, "confidence": 0.9}}
- "Mi código es XYZ98765" → {{"referral_code": "XYZ98765", "referred_by_phone": null, "confidence": 0.8}}
- "ABC12345" → {{"referral_code": "ABC12345", "referred_by_phone": null, "confidence": 0.7}}
- "Hola, quiero agendar una cita" → {{"referral_code": null, "referred_by_phone": null, "confidence": 0.0}}

RESPUESTA:
"""
            
            # Simular respuesta de IA (en un sistema real usarías GPT o similar)
            response = ReferralDetectionService.process_referral_detection_with_ai(detection_prompt, message)
            
            # Parsear la respuesta JSON
            try:
                result = json.loads(response)
                logger.info(f"DEBUG - Resultado de detección: {result}")
                return result
            except json.JSONDecodeError as e:
                logger.warn(f"Error al parsear JSON de detección: {e}")
                return {"referral_code": None, "referred_by_phone": None, "confidence": 0.0}
                
        except Exception as e:
            logger.error(f"Error en detección de referidos: {str(e)}")
            return {"referral_code": None, "referred_by_phone": None, "confidence": 0.0}

    @staticmethod
    def process_referral_detection_with_ai(prompt: str, message: str) -> str:
        """
        Procesa la detección de referidos usando IA.
        En un sistema real, aquí conectarías con GPT, Claude, o similar.
        """
        try:
            logger.info(f"DEBUG - Procesando detección de referido para: '{message}'")
            
            # Lógica simple de detección basada en patrones
            # Patrones para códigos de referido (8 caracteres alfanuméricos)
            # Buscar códigos que contengan tanto letras como números (más probable que sean códigos reales)
            referral_pattern = re.compile(r'\b[A-Za-z0-9]{8}\b')
            all_matches = referral_pattern.findall(message.upper())
            
            # Filtrar palabras comunes que no son códigos
            exclude_words = {'REFERIDO', 'CODIGO', 'CODIGO', 'HOLA', 'CITA', 'AGENDA', 'QUIERO', 'NECESITO', 'POR', 'ES', 'MI', 'EL', 'LA', 'LOS', 'LAS', 'DE', 'EN', 'CON', 'PARA', 'QUE', 'SE', 'UN', 'UNA'}
            referral_matches = [match for match in all_matches if match not in exclude_words]
            
            # Patrones para números de teléfono
            phone_pattern = re.compile(r'\+\d{10,15}')
            phone_matches = phone_pattern.findall(message)
            
            # Patrones para mensajes que mencionan referidos
            referral_mention_pattern = re.compile(r'(?:referido\s+por|código|codigo|referido)', re.IGNORECASE)
            has_referral_mention = bool(referral_mention_pattern.search(message))
            
            result = {
                "referral_code": None,
                "referred_by_phone": None,
                "confidence": 0.0
            }
            
            # Si encuentra códigos de referido
            if referral_matches:
                # Tomar el primer código encontrado
                code = referral_matches[0]
                result["referral_code"] = code
                result["confidence"] = 0.9 if has_referral_mention else 0.7
                logger.info(f"DEBUG - Código de referido detectado: '{code}' con confianza {result['confidence']}")
            
            # Si encuentra números de teléfono
            if phone_matches:
                # Tomar el primer número encontrado
                phone = phone_matches[0]
                result["referred_by_phone"] = phone
                if result["confidence"] == 0.0:  # Solo si no hay código de referido
                    result["confidence"] = 0.6
                logger.info(f"DEBUG - Teléfono de referido detectado: '{phone}'")
            
            # Si no encuentra nada específico pero el mensaje es muy corto y parece un código
            if not referral_matches and not phone_matches and len(message.strip()) == 8:
                # Verificar si es alfanumérico
                if message.strip().isalnum():
                    result["referral_code"] = message.strip().upper()
                    result["confidence"] = 0.6
                    logger.info(f"DEBUG - Mensaje corto detectado como código: '{message.strip().upper()}'")
            
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"Error en procesamiento de detección: {str(e)}")
            return '{"referral_code": null, "referred_by_phone": null, "confidence": 0.0}'

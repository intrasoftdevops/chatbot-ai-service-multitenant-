"""
Servicios de validación usando IA
"""
import re
import json
import logging

logger = logging.getLogger(__name__)

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
        response = process_referral_detection_with_ai(detection_prompt, message)
        
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

def validate_data_with_ai(query: str) -> str:
    """
    Usa IA para validar si una respuesta es un dato válido.
    
    Args:
        query: El prompt de validación que incluye la respuesta del usuario y el tipo de dato
        
    Returns:
        "VALID" si es un dato válido, "INVALID" si no lo es
    """
    try:
        # Extraer la respuesta del usuario del prompt
        if "'" in query:
            # Buscar texto entre comillas simples
            start = query.find("'") + 1
            end = query.find("'", start)
            if end > start:
                user_response = query[start:end]
            else:
                user_response = query
        else:
            user_response = query
        
        # Crear un prompt específico para validación
        validation_prompt = f"""
Eres un validador de datos para un sistema de registro. Tu tarea es determinar si la respuesta del usuario es un dato válido.

RESPUESTA DEL USUARIO: "{user_response}"

CONTEXTO: {query}

INSTRUCCIONES:
- Si la respuesta es un dato real y válido (nombre, apellido, ciudad, etc.), responde SOLO: VALID
- Si la respuesta es un saludo, confirmación genérica, pregunta, o no es un dato válido, responde SOLO: INVALID

Ejemplos de INVALID: "hola", "ok", "vale", "sí", "entendido", "¿qué?", "no sé"
Ejemplos de VALID: "Juan", "García", "Medellín", "ABC123", "sí" (solo para aceptación de términos)

RESPUESTA (solo VALID o INVALID):
"""
        
        # Simular respuesta de IA (en un sistema real usarías GPT o similar)
        response = process_validation_with_ai(validation_prompt)
        
        # Limpiar la respuesta
        clean_response = response.strip().upper()
        
        if clean_response == "VALID":
            return "VALID"
        else:
            return "INVALID"
            
    except Exception as e:
        logger.error(f"Error en validación con IA: {str(e)}")
        return "INVALID"

def process_validation_with_ai(prompt: str) -> str:
    """
    Procesa la validación usando IA.
    En un sistema real, aquí conectarías con GPT, Claude, o similar.
    """
    try:
        logger.info(f"DEBUG - Prompt recibido: {prompt}")
        
        # Extraer la respuesta del usuario del prompt
        user_response = ""
        if "'" in prompt:
            # Buscar texto entre comillas simples
            start = prompt.find("'") + 1
            end = prompt.find("'", start)
            if end > start:
                user_response = prompt[start:end].strip()
                logger.info(f"DEBUG - Respuesta extraída de comillas: '{user_response}'")
        
        # Si no encontramos comillas, buscar después de "RESPUESTA DEL USUARIO:"
        if not user_response and "RESPUESTA DEL USUARIO:" in prompt:
            start = prompt.find("RESPUESTA DEL USUARIO:") + len("RESPUESTA DEL USUARIO:")
            end = prompt.find("\n", start)
            if end > start:
                user_response = prompt[start:end].replace('"', '').strip()
                logger.info(f"DEBUG - Respuesta extraída de RESPUESTA DEL USUARIO: '{user_response}'")
        
        # Si aún no encontramos la respuesta, usar todo el prompt como fallback
        if not user_response:
            user_response = prompt.strip()
            logger.info(f"DEBUG - Usando prompt completo como respuesta: '{user_response}'")
        
        user_response_lower = user_response.lower()
        logger.info(f"DEBUG - Respuesta final a validar: '{user_response_lower}'")
        
        # Lógica simple de validación basada en patrones
        if any(word in user_response_lower for word in ["hola", "hi", "hello", "buenos", "buenas"]):
            logger.info(f"DEBUG - Rechazado por saludo: '{user_response_lower}'")
            return "INVALID"
        
        if any(word in user_response_lower for word in ["ok", "okay", "vale", "entendido", "comprendo", "perfecto"]):
            logger.info(f"DEBUG - Rechazado por confirmación genérica: '{user_response_lower}'")
            return "INVALID"
        
        if any(word in user_response_lower for word in ["gracias", "thanks", "de nada", "por favor"]):
            return "INVALID"
        
        if any(word in user_response_lower for word in ["claro", "exacto", "correcto", "bueno", "bien"]):
            return "INVALID"
        
        if any(word in user_response_lower for word in ["¿qué?", "que", "como", "ayuda", "help"]):
            return "INVALID"
        
        if any(word in user_response_lower for word in ["no sé", "no se", "no entiendo", "no comprendo"]):
            return "INVALID"
        
        # Si contiene nombres comunes colombianos/latinoamericanos
        if any(name in user_response_lower for name in ["juan", "maría", "carlos", "ana", "luis", "carmen", "pedro", "laura", "santiago", "diego", "andrés", "alejandro", "fernando", "ricardo", "miguel", "antonio", "rafael", "manuel", "francisco"]):
            return "VALID"
        
        # Si contiene apellidos comunes
        if any(lastname in user_response_lower for lastname in ["garcía", "lópez", "rodríguez", "gonzález", "martínez", "hernández", "pérez", "sánchez", "ramírez", "cruz", "morales", "gutiérrez", "ruiz", "díaz", "herrera", "jiménez", "moreno", "muñoz", "álvarez"]):
            return "VALID"
        
        # Si contiene ciudades colombianas
        if any(city in user_response_lower for city in ["medellín", "bogotá", "cali", "barranquilla", "cartagena", "bucaramanga", "pereira", "santa marta", "ibagué", "pasto", "manizales", "neiva", "villavicencio", "armenia", "popayán", "valledupar", "montería", "tunja", "florencia"]):
            return "VALID"
        
        # Si es "sí" o "no" para términos (solo si es exactamente eso)
        if user_response_lower.strip() in ["sí", "si", "yes", "no", "n"]:
            return "VALID"
        
        # Si es muy corto (menos de 2 caracteres), probablemente no es válido
        if len(user_response.strip()) < 2:
            logger.info(f"DEBUG - Rechazado por ser demasiado corto: '{user_response_lower}'")
            return "INVALID"
        
        # Si contiene palabras genéricas comunes que no son datos válidos
        generic_words = ["test", "prueba", "ejemplo", "demo", "simple", "básico", "normal", "común", "típico", "regular"]
        
        # Excepción: códigos de prueba válidos específicos
        valid_test_codes = ["testcode", "test123", "demo123", "prueba123"]
        
        # Si es un código de prueba válido específico, aceptarlo
        if user_response_lower in valid_test_codes:
            logger.info(f"DEBUG - Aceptado como código de prueba válido: '{user_response_lower}'")
            return "VALID"
        
        # Si contiene palabras genéricas pero no es un código de prueba válido
        if any(word in user_response_lower for word in generic_words) and user_response_lower not in valid_test_codes:
            logger.info(f"DEBUG - Rechazado por palabra genérica: '{user_response_lower}'")
            return "INVALID"
        
        # Si parece un código alfanumérico válido (mínimo 3 caracteres, no solo números, y no contiene palabras genéricas)
        if len(user_response.strip()) >= 3 and any(char.isalpha() for char in user_response) and not any(word in user_response_lower for word in generic_words):
            logger.info(f"DEBUG - Aceptado como código alfanumérico: '{user_response_lower}'")
            return "VALID"
        
        # Por defecto, si no coincide con patrones específicos, considerar inválido por seguridad
        logger.info(f"DEBUG - Rechazado por defecto: '{user_response_lower}'")
        return "INVALID"
        
    except Exception as e:
        logger.error(f"Error en procesamiento de validación: {str(e)}")
        return "INVALID"

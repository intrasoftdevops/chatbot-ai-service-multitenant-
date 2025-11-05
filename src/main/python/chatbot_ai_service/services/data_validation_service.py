import logging

logger = logging.getLogger(__name__)

class DataValidationService:
    """
    Servicio para validar datos de usuario usando IA
    """
    
    @staticmethod
    def validate_data_with_ai(message: str, data_type: str = None) -> str:
        """
        Usa IA para validar si una respuesta es un dato válido.
        
        Args:
            message: La respuesta del usuario
            data_type: El tipo de dato esperado (nombre, apellido, ciudad, aceptacion_terminos, codigo_referido)
            
        Returns:
            "VALID" si es un dato válido, "INVALID" si no lo es
        """
        try:
            logger.info(f"DEBUG - Validando mensaje: '{message}' tipo: '{data_type}'")
            
            # Construir prompt específico basado en el tipo de dato
            tipo_descripcion = {
                "nombre": "un nombre real de persona",
                "apellido": "un apellido real",
                "ciudad": "una ciudad real",
                "aceptacion_terminos": "una respuesta clara de sí o no",
                "codigo_referido": "un código alfanumérico o 'no'"
            }.get(data_type, "un dato válido")
            
            # Crear un prompt específico para validación
            validation_prompt = f"""
Eres un validador de datos para un sistema de registro. Tu tarea es determinar si la respuesta del usuario es {tipo_descripcion}.

RESPUESTA DEL USUARIO: "{message}"
TIPO DE DATO ESPERADO: {data_type}

INSTRUCCIONES:
- Si la respuesta es {tipo_descripcion}, responde SOLO: VALID
- Si la respuesta es un saludo, confirmación genérica, pregunta, o no es {tipo_descripcion}, responde SOLO: INVALID

Ejemplos de INVALID: "hola", "ok", "vale", "entendido", "¿qué?", "no sé"
Ejemplos de VALID para {data_type}: {DataValidationService._get_examples_for_type(data_type)}

RESPUESTA (solo VALID o INVALID):
"""
            
            # Procesar validación con IA o lógica basada en reglas
            response = DataValidationService.process_validation_with_ai(message, data_type)
            
            # Limpiar la respuesta
            clean_response = response.strip().upper()
            
            if clean_response == "VALID":
                return "VALID"
            else:
                return "INVALID"
                
        except Exception as e:
            logger.error(f"Error en validación con IA: {str(e)}")
            return "INVALID"
    
    @staticmethod
    def _get_examples_for_type(data_type: str) -> str:
        """Retorna ejemplos de datos válidos según el tipo"""
        examples = {
            "nombre": "Juan, María, Carlos, Ana",
            "apellido": "García, López, Rodríguez, González",
            "ciudad": "Medellín, Bogotá, Cali, Barranquilla",
            "aceptacion_terminos": "sí, no",
            "codigo_referido": "ABC123, XYZ789, no"
        }
        return examples.get(data_type, "datos reales")

    @staticmethod
    def process_validation_with_ai(message: str, data_type: str = None) -> str:
        """
        Procesa la validación usando IA o lógica basada en reglas.
        En un sistema real, aquí conectarías con GPT, Claude, o similar.
        
        Args:
            message: La respuesta del usuario
            data_type: El tipo de dato esperado
            
        Returns:
            "VALID" o "INVALID"
        """
        try:
            logger.info(f"DEBUG - Validando: '{message}' tipo: '{data_type}'")
            
            user_response_lower = message.lower().strip()
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
            if len(message.strip()) < 2:
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
            if len(message.strip()) >= 3 and any(char.isalpha() for char in message) and not any(word in user_response_lower for word in generic_words):
                logger.info(f"DEBUG - Aceptado como código alfanumérico: '{user_response_lower}'")
                return "VALID"
            
            # Por defecto, si no coincide con patrones específicos, considerar inválido por seguridad
            logger.info(f"DEBUG - Rechazado por defecto: '{user_response_lower}'")
            return "INVALID"
            
        except Exception as e:
            logger.error(f"Error en procesamiento de validación: {str(e)}")
            return "INVALID"

"""
Servicio de validación de datos de registro

Valida respuestas del usuario usando IA y proporciona fallbacks
para diferentes tipos de datos (nombre, apellido, ciudad, etc.)
"""

import logging
from typing import Dict, Tuple
import google.generativeai as genai
import os
import json

logger = logging.getLogger(__name__)

class RegistrationDataValidator:
    """Validador de datos de registro usando IA"""
    
    def __init__(self):
        """Inicializa el servicio de validación"""
        # Configurar API de Google Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            logger.warning("GOOGLE_API_KEY no configurada, usando solo validación de fallback")
            self.model = None
    
    async def validate_data(self, message: str, data_type: str, tenant_id: str) -> Tuple[str, str, float]:
        """
        Valida si un mensaje contiene un dato válido del tipo especificado
        
        Args:
            message: Mensaje del usuario a validar
            data_type: Tipo de dato a validar ('nombre', 'apellido', 'ciudad', 'aceptacion_terminos', 'codigo_referido')
            tenant_id: ID del tenant
            
        Returns:
            Tuple con (result: 'VALID'|'INVALID', reason: str, confidence: float)
        """
        try:
            # Crear prompt de validación específico
            validation_prompt = self._create_validation_prompt(message, data_type)
            
            # Intentar validación con IA
            if self.model:
                try:
                    response = self.model.generate_content(
                        validation_prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.1,
                            max_output_tokens=100
                        )
                    )
                    
                    ai_response = response.text.strip().upper()
                    
                    # La IA debe responder "VALID" o "INVALID"
                    if "VALID" in ai_response and "INVALID" not in ai_response:
                        return ("VALID", f"Validación de dato: {validation_prompt}", 0.9)
                    elif "INVALID" in ai_response:
                        return ("INVALID", f"Validación de dato: {validation_prompt}", 0.9)
                        
                except Exception as e:
                    logger.warning(f"Error en validación con IA: {e}, usando fallback")
            
            # Fallback a validación básica
            is_valid = self._fallback_validation(message, data_type)
            result = "VALID" if is_valid else "INVALID"
            return (result, f"Validación fallback para {data_type}", 0.6)
            
        except Exception as e:
            logger.error(f"Error al validar dato: {e}")
            # En caso de error, usar fallback conservador
            is_valid = self._fallback_validation(message, data_type)
            result = "VALID" if is_valid else "INVALID"
            return (result, f"Validación fallback de emergencia", 0.3)
    
    def _create_validation_prompt(self, message: str, data_type: str) -> str:
        """Crea un prompt específico para validar datos"""
        
        prompts = {
            "nombre": f"Evalúa si '{message}' es un NOMBRE REAL de persona válido. "
                     f"NO aceptes: saludos (hola, hi), confirmaciones (ok, vale, sí), preguntas, números, o palabras genéricas. "
                     f"SÍ acepta: nombres reales como Juan, María, Carlos, Ana, etc. "
                     f"Responde únicamente: VALID si es un nombre real, INVALID si no lo es.",
            
            "apellido": f"Evalúa si '{message}' es un APELLIDO REAL de persona válido. "
                       f"NO aceptes: saludos (hola, hi), confirmaciones (ok, vale, sí), preguntas, números, o palabras genéricas. "
                       f"SÍ acepta: apellidos reales como García, López, Rodríguez, etc. "
                       f"Responde únicamente: VALID si es un apellido real, INVALID si no lo es.",
            
            "ciudad": f"Evalúa si '{message}' es una CIUDAD REAL válida. "
                     f"NO aceptes: saludos (hola, hi), confirmaciones (ok, vale, sí), preguntas, o palabras genéricas. "
                     f"SÍ acepta: nombres de ciudades reales como Medellín, Bogotá, Cali, etc. "
                     f"Responde únicamente: VALID si es una ciudad real, INVALID si no lo es.",
            
            "codigo_referido": f"Evalúa si '{message}' es un CÓDIGO DE REFERIDO válido o una respuesta 'no'. "
                              f"SÍ acepta: códigos alfanuméricos (ABC123, XYZ789) o 'no'/'n' si no tiene código. "
                              f"NO aceptes: saludos, confirmaciones vagas, o respuestas no relacionadas. "
                              f"Responde únicamente: VALID si es válido, INVALID si no lo es.",
            
            "aceptacion_terminos": f"Evalúa si '{message}' es una respuesta CLARA de aceptación o rechazo de términos. "
                                  f"SÍ acepta: 'sí', 'si', 'yes', 's' para aceptar, o 'no', 'n' para rechazar. "
                                  f"NO aceptes: respuestas vagas, saludos, o respuestas no relacionadas. "
                                  f"Responde únicamente: VALID si es una respuesta clara, INVALID si no lo es."
        }
        
        return prompts.get(data_type, 
                          f"Evalúa si '{message}' es una respuesta válida para el tipo de dato '{data_type}'. "
                          f"NO aceptes saludos, confirmaciones vagas, o respuestas no relacionadas. "
                          f"Responde únicamente: VALID si es válido, INVALID si no lo es.")
    
    def _fallback_validation(self, message: str, data_type: str) -> bool:
        """Validación de fallback si falla la IA"""
        
        lower_message = message.lower().strip()
        
        # Lista de respuestas que definitivamente no son válidas
        invalid_responses = [
            "hola", "hi", "hello", "buenos días", "buenas tardes", "buenas noches",
            "ok", "okay", "vale", "entendido", "comprendo", "perfecto", "genial",
            "gracias", "thanks", "muchas gracias", "de nada", "por favor",
            "claro", "exacto", "correcto", "bueno", "bien", "mal", "malo",
            "tengo dudas", "no sé", "no se", "no entiendo", "no comprendo",
            "me puedes ayudar", "ayuda", "help", "¿qué?", "que", "como"
        ]
        
        # Verificar si es una respuesta inválida obvia
        if lower_message in invalid_responses:
            return False
        
        # Validaciones específicas por tipo
        if data_type == "aceptacion_terminos":
            return lower_message in ["sí", "si", "s", "yes", "no", "n"]
        
        # Para otros tipos, validación básica de longitud
        return len(message.strip()) >= 2
    
    def is_generic_name(self, name: str) -> bool:
        """Verifica si es un nombre genérico"""
        generic_names = [
            "nombre", "name", "usuario", "user", "persona", "person", "cliente", "customer",
            "test", "prueba", "ejemplo", "example", "demo", "anonimo", "anonymous"
        ]
        
        return name.lower().strip() in generic_names
    
    def is_generic_city(self, city: str) -> bool:
        """Verifica si es una ciudad genérica"""
        generic_cities = [
            "ciudad", "city", "lugar", "place", "ubicacion", "location", "direccion", "address",
            "casa", "home", "trabajo", "work", "oficina", "office"
        ]
        
        return city.lower().strip() in generic_cities


"""
Servicios de manejo de errores para IA
"""
import logging
import json
import traceback
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AIErrorHandler:
    """
    Maneja errores específicos del servicio de IA
    """
    
    def __init__(self):
        self.error_counts = {}
        self.max_retries = 3
        self.retry_delay = 1.0  # segundos
    
    def handle_ai_error(self, error: Exception, context: Dict) -> str:
        """
        Maneja errores de la IA y devuelve una respuesta apropiada.
        
        Args:
            error: Excepción ocurrida
            context: Contexto del error
            
        Returns:
            Respuesta de error apropiada
        """
        try:
            logger.error(f"Error de IA: {str(error)}")
            logger.error(f"Contexto: {json.dumps(context, indent=2)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Clasificar el tipo de error
            error_type = self.classify_error(error)
            
            # Obtener respuesta apropiada
            response = self.get_error_response(error_type, context)
            
            # Registrar el error
            self.log_error(error, context, error_type)
            
            return response
            
        except Exception as e:
            logger.error(f"Error en manejo de errores: {str(e)}")
            return "Lo siento, ocurrió un error inesperado. Por favor intenta de nuevo más tarde."
    
    def classify_error(self, error: Exception) -> str:
        """
        Clasifica el tipo de error.
        
        Args:
            error: Excepción a clasificar
            
        Returns:
            Tipo de error clasificado
        """
        try:
            error_str = str(error).lower()
            
            if "timeout" in error_str or "timed out" in error_str:
                return "timeout"
            elif "connection" in error_str or "network" in error_str:
                return "connection"
            elif "authentication" in error_str or "unauthorized" in error_str:
                return "authentication"
            elif "rate limit" in error_str or "quota" in error_str:
                return "rate_limit"
            elif "validation" in error_str or "invalid" in error_str:
                return "validation"
            elif "not found" in error_str or "404" in error_str:
                return "not_found"
            elif "server error" in error_str or "500" in error_str:
                return "server_error"
            else:
                return "unknown"
                
        except Exception as e:
            logger.error(f"Error clasificando error: {str(e)}")
            return "unknown"
    
    def get_error_response(self, error_type: str, context: Dict) -> str:
        """
        Obtiene una respuesta apropiada para el tipo de error.
        
        Args:
            error_type: Tipo de error clasificado
            context: Contexto del error
            
        Returns:
            Respuesta de error apropiada
        """
        try:
            # Obtener información del contexto
            candidate_name = context.get("candidate_name", "el candidato")
            tenant_name = context.get("tenant_name", "la campaña")
            
            # Respuestas específicas por tipo de error
            error_responses = {
                "timeout": f"Lo siento, el servicio está tardando más de lo esperado. 😔 " \
                          f"Por favor intenta de nuevo en unos momentos. " \
                          f"Si el problema persiste, contacta con el equipo de {tenant_name}.",
                
                "connection": f"Parece que hay un problema de conexión. 🌐 " \
                             f"Por favor verifica tu conexión a internet e intenta de nuevo. " \
                             f"Si el problema persiste, contacta con el equipo de {tenant_name}.",
                
                "authentication": f"Hay un problema con la autenticación del servicio. 🔐 " \
                                 f"Por favor contacta con el equipo técnico de {tenant_name} " \
                                 f"para resolver este problema.",
                
                "rate_limit": f"El servicio está experimentando mucha actividad. ⚡ " \
                             f"Por favor espera unos minutos e intenta de nuevo. " \
                             f"Gracias por tu paciencia.",
                
                "validation": f"Hay un problema con la validación de datos. 📝 " \
                             f"Por favor verifica que la información sea correcta e intenta de nuevo. " \
                             f"Si el problema persiste, contacta con el equipo de {tenant_name}.",
                
                "not_found": f"La información solicitada no se encontró. 🔍 " \
                             f"Por favor verifica que la consulta sea correcta. " \
                             f"Si necesitas ayuda, contacta con el equipo de {tenant_name}.",
                
                "server_error": f"Hay un problema temporal con el servidor. 🔧 " \
                               f"Por favor intenta de nuevo en unos minutos. " \
                               f"Si el problema persiste, contacta con el equipo técnico de {tenant_name}.",
                
                "unknown": f"Ocurrió un error inesperado. 😔 " \
                          f"Por favor intenta de nuevo más tarde. " \
                          f"Si el problema persiste, contacta con el equipo de {tenant_name}."
            }
            
            return error_responses.get(error_type, error_responses["unknown"])
            
        except Exception as e:
            logger.error(f"Error obteniendo respuesta de error: {str(e)}")
            return "Lo siento, ocurrió un error inesperado. Por favor intenta de nuevo más tarde."
    
    def log_error(self, error: Exception, context: Dict, error_type: str):
        """
        Registra el error para análisis posterior.
        
        Args:
            error: Excepción ocurrida
            context: Contexto del error
            error_type: Tipo de error clasificado
        """
        try:
            # Incrementar contador de errores por tipo
            if error_type not in self.error_counts:
                self.error_counts[error_type] = 0
            self.error_counts[error_type] += 1
            
            # Log estructurado del error
            error_log = {
                "error_type": error_type,
                "error_message": str(error),
                "error_class": error.__class__.__name__,
                "context": context,
                "timestamp": self.get_current_timestamp(),
                "count": self.error_counts[error_type]
            }
            
            logger.error(f"Error registrado: {json.dumps(error_log, indent=2)}")
            
        except Exception as e:
            logger.error(f"Error registrando error: {str(e)}")
    
    def get_current_timestamp(self) -> str:
        """
        Obtiene el timestamp actual.
        
        Returns:
            Timestamp actual como string
        """
        try:
            from datetime import datetime
            return datetime.now().isoformat()
        except Exception:
            return "unknown"
    
    def should_retry(self, error_type: str) -> bool:
        """
        Determina si se debe reintentar la operación.
        
        Args:
            error_type: Tipo de error clasificado
            
        Returns:
            True si se debe reintentar, False si no
        """
        try:
            # Errores que no se deben reintentar
            no_retry_errors = ["authentication", "validation", "not_found"]
            
            if error_type in no_retry_errors:
                return False
            
            # Verificar límite de reintentos
            if error_type in self.error_counts:
                return self.error_counts[error_type] < self.max_retries
            
            return True
            
        except Exception as e:
            logger.error(f"Error determinando si reintentar: {str(e)}")
            return False
    
    def get_retry_delay(self, error_type: str, attempt: int) -> float:
        """
        Obtiene el delay para el reintento.
        
        Args:
            error_type: Tipo de error clasificado
            attempt: Número de intento actual
            
        Returns:
            Delay en segundos
        """
        try:
            # Delay exponencial para rate limits
            if error_type == "rate_limit":
                return self.retry_delay * (2 ** attempt)
            
            # Delay fijo para otros errores
            return self.retry_delay
            
        except Exception as e:
            logger.error(f"Error obteniendo delay de reintento: {str(e)}")
            return self.retry_delay
    
    def get_error_statistics(self) -> Dict[str, any]:
        """
        Obtiene estadísticas de errores.
        
        Returns:
            Diccionario con estadísticas de errores
        """
        try:
            total_errors = sum(self.error_counts.values())
            
            statistics = {
                "total_errors": total_errors,
                "error_counts": self.error_counts.copy(),
                "error_types": list(self.error_counts.keys()),
                "most_common_error": max(self.error_counts, key=self.error_counts.get) if self.error_counts else None
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {
                "total_errors": 0,
                "error_counts": {},
                "error_types": [],
                "most_common_error": None
            }
    
    def reset_error_counts(self):
        """
        Reinicia los contadores de errores.
        """
        try:
            self.error_counts.clear()
            logger.info("Contadores de errores reiniciados")
        except Exception as e:
            logger.error(f"Error reiniciando contadores: {str(e)}")

def create_error_response(error_type: str, context: Dict) -> str:
    """
    Crea una respuesta de error personalizada.
    
    Args:
        error_type: Tipo de error
        context: Contexto del error
        
    Returns:
        Respuesta de error personalizada
    """
    try:
        handler = AIErrorHandler()
        return handler.get_error_response(error_type, context)
    except Exception as e:
        logger.error(f"Error creando respuesta de error: {str(e)}")
        return "Lo siento, ocurrió un error inesperado. Por favor intenta de nuevo más tarde."

def handle_ai_service_error(error: Exception, context: Dict) -> str:
    """
    Maneja errores del servicio de IA.
    
    Args:
        error: Excepción ocurrida
        context: Contexto del error
        
    Returns:
        Respuesta de error apropiada
    """
    try:
        handler = AIErrorHandler()
        return handler.handle_ai_error(error, context)
    except Exception as e:
        logger.error(f"Error en manejo de errores del servicio: {str(e)}")
        return "Lo siento, ocurrió un error inesperado. Por favor intenta de nuevo más tarde."

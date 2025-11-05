"""
Servicios de logging para IA
"""
import logging
import json
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class AILoggingService:
    """
    Servicio de logging especializado para IA
    """
    
    def __init__(self):
        self.setup_logging()
        self.log_buffer = []
        self.max_buffer_size = 1000
    
    def setup_logging(self):
        """
        Configura el sistema de logging.
        """
        try:
            # Configurar formato de logging
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # Configurar handler para consola
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.INFO)
            
            # Configurar handler para archivo
            file_handler = logging.FileHandler('ai_service.log')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)
            
            # Configurar logger principal
            ai_logger = logging.getLogger('ai_service')
            ai_logger.setLevel(logging.DEBUG)
            ai_logger.addHandler(console_handler)
            ai_logger.addHandler(file_handler)
            
            # Evitar duplicación de logs
            ai_logger.propagate = False
            
        except Exception as e:
            print(f"Error configurando logging: {str(e)}")
    
    def log_request(self, tenant_id: str, message: str, context: Dict):
        """
        Registra una solicitud de IA.
        
        Args:
            tenant_id: ID del tenant
            message: Mensaje del usuario
            context: Contexto de la solicitud
        """
        try:
            log_entry = {
                "type": "request",
                "tenant_id": tenant_id,
                "message": message,
                "context": context,
                "timestamp": self.get_current_timestamp(),
                "level": "INFO"
            }
            
            self._log_entry(log_entry)
            
        except Exception as e:
            logger.error(f"Error registrando solicitud: {str(e)}")
    
    def log_response(self, tenant_id: str, response: str, intent: str, confidence: float):
        """
        Registra una respuesta de IA.
        
        Args:
            tenant_id: ID del tenant
            response: Respuesta generada
            intent: Intención detectada
            confidence: Nivel de confianza
        """
        try:
            log_entry = {
                "type": "response",
                "tenant_id": tenant_id,
                "response": response,
                "intent": intent,
                "confidence": confidence,
                "timestamp": self.get_current_timestamp(),
                "level": "INFO"
            }
            
            self._log_entry(log_entry)
            
        except Exception as e:
            logger.error(f"Error registrando respuesta: {str(e)}")
    
    def log_error(self, tenant_id: str, error: Exception, context: Dict):
        """
        Registra un error de IA.
        
        Args:
            tenant_id: ID del tenant
            error: Excepción ocurrida
            context: Contexto del error
        """
        try:
            log_entry = {
                "type": "error",
                "tenant_id": tenant_id,
                "error_message": str(error),
                "error_class": error.__class__.__name__,
                "traceback": traceback.format_exc(),
                "context": context,
                "timestamp": self.get_current_timestamp(),
                "level": "ERROR"
            }
            
            self._log_entry(log_entry)
            
        except Exception as e:
            logger.error(f"Error registrando error: {str(e)}")
    
    def log_performance(self, tenant_id: str, operation: str, duration: float, metadata: Dict = None):
        """
        Registra métricas de rendimiento.
        
        Args:
            tenant_id: ID del tenant
            operation: Operación realizada
            duration: Duración en segundos
            metadata: Metadatos adicionales
        """
        try:
            log_entry = {
                "type": "performance",
                "tenant_id": tenant_id,
                "operation": operation,
                "duration": duration,
                "metadata": metadata or {},
                "timestamp": self.get_current_timestamp(),
                "level": "INFO"
            }
            
            self._log_entry(log_entry)
            
        except Exception as e:
            logger.error(f"Error registrando rendimiento: {str(e)}")
    
    def log_intent_classification(self, tenant_id: str, message: str, intent: str, confidence: float, patterns_matched: List[str]):
        """
        Registra clasificación de intenciones.
        
        Args:
            tenant_id: ID del tenant
            message: Mensaje clasificado
            intent: Intención detectada
            confidence: Nivel de confianza
            patterns_matched: Patrones que coincidieron
        """
        try:
            log_entry = {
                "type": "intent_classification",
                "tenant_id": tenant_id,
                "message": message,
                "intent": intent,
                "confidence": confidence,
                "patterns_matched": patterns_matched,
                "timestamp": self.get_current_timestamp(),
                "level": "DEBUG"
            }
            
            self._log_entry(log_entry)
            
        except Exception as e:
            logger.error(f"Error registrando clasificación: {str(e)}")
    
    def log_data_validation(self, tenant_id: str, data_type: str, user_input: str, is_valid: bool, validation_reason: str):
        """
        Registra validación de datos.
        
        Args:
            tenant_id: ID del tenant
            data_type: Tipo de dato validado
            user_input: Entrada del usuario
            is_valid: Si es válido o no
            validation_reason: Razón de la validación
        """
        try:
            log_entry = {
                "type": "data_validation",
                "tenant_id": tenant_id,
                "data_type": data_type,
                "user_input": user_input,
                "is_valid": is_valid,
                "validation_reason": validation_reason,
                "timestamp": self.get_current_timestamp(),
                "level": "DEBUG"
            }
            
            self._log_entry(log_entry)
            
        except Exception as e:
            logger.error(f"Error registrando validación: {str(e)}")
    
    def log_referral_detection(self, tenant_id: str, message: str, referral_code: str, referred_by_phone: str, confidence: float):
        """
        Registra detección de referidos.
        
        Args:
            tenant_id: ID del tenant
            message: Mensaje analizado
            referral_code: Código de referido detectado
            referred_by_phone: Teléfono del referidor
            confidence: Nivel de confianza
        """
        try:
            log_entry = {
                "type": "referral_detection",
                "tenant_id": tenant_id,
                "message": message,
                "referral_code": referral_code,
                "referred_by_phone": referred_by_phone,
                "confidence": confidence,
                "timestamp": self.get_current_timestamp(),
                "level": "INFO"
            }
            
            self._log_entry(log_entry)
            
        except Exception as e:
            logger.error(f"Error registrando detección de referido: {str(e)}")
    
    def log_context_loading(self, tenant_id: str, context_source: str, context_size: int, load_duration: float):
        """
        Registra carga de contexto.
        
        Args:
            tenant_id: ID del tenant
            context_source: Fuente del contexto
            context_size: Tamaño del contexto
            load_duration: Duración de la carga
        """
        try:
            log_entry = {
                "type": "context_loading",
                "tenant_id": tenant_id,
                "context_source": context_source,
                "context_size": context_size,
                "load_duration": load_duration,
                "timestamp": self.get_current_timestamp(),
                "level": "DEBUG"
            }
            
            self._log_entry(log_entry)
            
        except Exception as e:
            logger.error(f"Error registrando carga de contexto: {str(e)}")
    
    def _log_entry(self, log_entry: Dict):
        """
        Registra una entrada de log.
        
        Args:
            log_entry: Entrada de log a registrar
        """
        try:
            # Agregar al buffer
            self.log_buffer.append(log_entry)
            
            # Limpiar buffer si es necesario
            if len(self.log_buffer) > self.max_buffer_size:
                self.log_buffer = self.log_buffer[-self.max_buffer_size:]
            
            # Log según el nivel
            level = log_entry.get("level", "INFO")
            message = json.dumps(log_entry, indent=2)
            
            if level == "ERROR":
                logger.error(message)
            elif level == "WARNING":
                logger.warning(message)
            elif level == "DEBUG":
                logger.debug(message)
            else:
                logger.info(message)
                
        except Exception as e:
            logger.error(f"Error registrando entrada de log: {str(e)}")
    
    def get_current_timestamp(self) -> str:
        """
        Obtiene el timestamp actual.
        
        Returns:
            Timestamp actual como string
        """
        try:
            return datetime.now().isoformat()
        except Exception:
            return "unknown"
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de los logs.
        
        Returns:
            Diccionario con estadísticas de logs
        """
        try:
            if not self.log_buffer:
                return {
                    "total_entries": 0,
                    "entry_types": {},
                    "error_count": 0,
                    "warning_count": 0,
                    "info_count": 0,
                    "debug_count": 0
                }
            
            # Contar tipos de entradas
            entry_types = {}
            error_count = 0
            warning_count = 0
            info_count = 0
            debug_count = 0
            
            for entry in self.log_buffer:
                entry_type = entry.get("type", "unknown")
                entry_types[entry_type] = entry_types.get(entry_type, 0) + 1
                
                level = entry.get("level", "INFO")
                if level == "ERROR":
                    error_count += 1
                elif level == "WARNING":
                    warning_count += 1
                elif level == "INFO":
                    info_count += 1
                elif level == "DEBUG":
                    debug_count += 1
            
            return {
                "total_entries": len(self.log_buffer),
                "entry_types": entry_types,
                "error_count": error_count,
                "warning_count": warning_count,
                "info_count": info_count,
                "debug_count": debug_count
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {
                "total_entries": 0,
                "entry_types": {},
                "error_count": 0,
                "warning_count": 0,
                "info_count": 0,
                "debug_count": 0
            }
    
    def clear_log_buffer(self):
        """
        Limpia el buffer de logs.
        """
        try:
            self.log_buffer.clear()
            logger.info("Buffer de logs limpiado")
        except Exception as e:
            logger.error(f"Error limpiando buffer: {str(e)}")
    
    def export_logs(self, filename: str = None) -> str:
        """
        Exporta los logs a un archivo.
        
        Args:
            filename: Nombre del archivo (opcional)
            
        Returns:
            Ruta del archivo exportado
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"ai_logs_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.log_buffer, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Logs exportados a {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error exportando logs: {str(e)}")
            return None

# Instancia global del servicio de logging
ai_logging_service = AILoggingService()

def log_ai_request(tenant_id: str, message: str, context: Dict):
    """
    Función de conveniencia para registrar solicitudes de IA.
    """
    ai_logging_service.log_request(tenant_id, message, context)

def log_ai_response(tenant_id: str, response: str, intent: str, confidence: float):
    """
    Función de conveniencia para registrar respuestas de IA.
    """
    ai_logging_service.log_response(tenant_id, response, intent, confidence)

def log_ai_error(tenant_id: str, error: Exception, context: Dict):
    """
    Función de conveniencia para registrar errores de IA.
    """
    ai_logging_service.log_error(tenant_id, error, context)

def log_ai_performance(tenant_id: str, operation: str, duration: float, metadata: Dict = None):
    """
    Función de conveniencia para registrar métricas de rendimiento.
    """
    ai_logging_service.log_performance(tenant_id, operation, duration, metadata)

"""
Servicio refactorizado de métricas para IA
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any

from chatbot_ai_service.services.metrics.performance_metrics_service import PerformanceMetricsService
from chatbot_ai_service.services.metrics.intent_metrics_service import IntentMetricsService
from chatbot_ai_service.services.metrics.error_metrics_service import ErrorMetricsService
from chatbot_ai_service.services.metrics.tenant_metrics_service import TenantMetricsService

logger = logging.getLogger(__name__)

class AIMetricsServiceRefactored:
    """
    Servicio refactorizado de métricas para el servicio de IA
    """
    
    def __init__(self):
        self.performance_service = PerformanceMetricsService()
        self.intent_service = IntentMetricsService()
        self.error_service = ErrorMetricsService()
        self.tenant_service = TenantMetricsService()
    
    def record_request(self, tenant_id: str, message_length: int, intent: str = None):
        """Registra una solicitud de IA"""
        try:
            self.tenant_service.record_request(tenant_id, message_length, intent)
            logger.debug(f"Request registrada para tenant {tenant_id}, intent: {intent}")
        except Exception as e:
            logger.error(f"Error registrando solicitud: {str(e)}")
    
    def record_response(self, tenant_id: str, response_length: int, processing_time: float, intent: str = None):
        """Registra una respuesta de IA"""
        try:
            self.tenant_service.record_response(tenant_id, response_length, processing_time, intent)
            self.performance_service.record_response_time(processing_time)
            logger.debug(f"Response registrada para tenant {tenant_id}, tiempo: {processing_time:.3f}s")
        except Exception as e:
            logger.error(f"Error registrando respuesta: {str(e)}")
    
    def record_error(self, tenant_id: str, error_type: str, error_message: str):
        """Registra un error de IA"""
        try:
            self.tenant_service.record_error(tenant_id, error_type, error_message)
            self.error_service.record_error(tenant_id, error_type, error_message)
            logger.debug(f"Error registrado para tenant {tenant_id}, tipo: {error_type}")
        except Exception as e:
            logger.error(f"Error registrando error: {str(e)}")
    
    def record_intent_classification(self, tenant_id: str, intent: str, confidence: float, processing_time: float):
        """Registra clasificación de intenciones"""
        try:
            self.tenant_service.record_intent_classification(tenant_id, intent, confidence, processing_time)
            self.intent_service.record_intent_classification(tenant_id, intent, confidence, processing_time)
            logger.debug(f"Clasificación registrada para tenant {tenant_id}, intent: {intent}, confianza: {confidence}")
        except Exception as e:
            logger.error(f"Error registrando clasificación: {str(e)}")
    
    def record_data_validation(self, tenant_id: str, data_type: str, is_valid: bool, processing_time: float):
        """Registra validación de datos"""
        try:
            self.tenant_service.record_data_validation(tenant_id, data_type, is_valid, processing_time)
            logger.debug(f"Validación registrada para tenant {tenant_id}, tipo: {data_type}, válido: {is_valid}")
        except Exception as e:
            logger.error(f"Error registrando validación: {str(e)}")
    
    def record_referral_detection(self, tenant_id: str, referral_code: str, confidence: float, processing_time: float):
        """Registra detección de referidos"""
        try:
            self.tenant_service.record_referral_detection(tenant_id, referral_code, confidence, processing_time)
            logger.debug(f"Detección de referido registrada para tenant {tenant_id}, código: {referral_code}")
        except Exception as e:
            logger.error(f"Error registrando detección de referido: {str(e)}")
    
    def get_general_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas generales del servicio"""
        try:
            # Obtener métricas de rendimiento
            performance_metrics = self.performance_service.get_performance_metrics()
            uptime_metrics = self.performance_service.get_uptime()
            
            # Obtener métricas de intenciones
            intent_metrics = self.intent_service.get_intent_metrics()
            
            # Obtener métricas de errores
            error_metrics = self.error_service.get_error_metrics()
            
            # Obtener métricas de tenants
            active_tenants = self.tenant_service.get_active_tenants_count()
            
            # Calcular métricas básicas
            total_requests = len(self.tenant_service.tenant_requests)
            total_responses = len(self.tenant_service.tenant_responses)
            total_errors = len(self.tenant_service.error_service.error_logs)
            
            # Calcular tasa de error
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            
            return {
                **uptime_metrics,
                "total_requests": total_requests,
                "total_responses": total_responses,
                "total_errors": total_errors,
                "error_rate": error_rate,
                "avg_response_time": performance_metrics.get("avg_response_time", 0),
                "total_intent_classifications": intent_metrics.get("total_intents", 0),
                "most_common_intent": intent_metrics.get("most_common_intent"),
                "total_error_count": error_metrics.get("total_errors", 0),
                "most_common_error": error_metrics.get("most_common_error"),
                "active_tenants": active_tenants
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas generales: {str(e)}")
            return {}
    
    def get_tenant_metrics(self, tenant_id: str) -> Dict[str, Any]:
        """Obtiene métricas específicas de un tenant"""
        return self.tenant_service.get_tenant_metrics(tenant_id)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de rendimiento"""
        return self.performance_service.get_performance_metrics()
    
    def get_intent_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de intenciones"""
        return self.intent_service.get_intent_metrics()
    
    def get_error_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de errores"""
        return self.error_service.get_error_metrics()
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Obtiene todas las métricas disponibles"""
        try:
            return {
                "general": self.get_general_metrics(),
                "performance": self.get_performance_metrics(),
                "intents": self.get_intent_metrics(),
                "errors": self.get_error_metrics(),
                "tenants": self.tenant_service.get_all_tenant_metrics()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo todas las métricas: {str(e)}")
            return {}
    
    def reset_metrics(self):
        """Reinicia todas las métricas"""
        try:
            self.performance_service.reset_performance_metrics()
            self.intent_service.reset_intent_metrics()
            self.error_service.reset_error_metrics()
            self.tenant_service.reset_tenant_metrics()
            logger.info("Métricas reiniciadas")
        except Exception as e:
            logger.error(f"Error reiniciando métricas: {str(e)}")
    
    def export_metrics(self, filename: str = None) -> str:
        """Exporta las métricas a un archivo JSON"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"ai_metrics_{timestamp}.json"
            
            metrics_data = self.get_all_metrics()
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Métricas exportadas a {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error exportando métricas: {str(e)}")
            return None

# Instancia global del servicio de métricas refactorizado
ai_metrics_service_refactored = AIMetricsServiceRefactored()

# Funciones de conveniencia
def record_ai_request(tenant_id: str, message_length: int, intent: str = None):
    """Función de conveniencia para registrar solicitudes de IA"""
    ai_metrics_service_refactored.record_request(tenant_id, message_length, intent)

def record_ai_response(tenant_id: str, response_length: int, processing_time: float, intent: str = None):
    """Función de conveniencia para registrar respuestas de IA"""
    ai_metrics_service_refactored.record_response(tenant_id, response_length, processing_time, intent)

def record_ai_error(tenant_id: str, error_type: str, error_message: str):
    """Función de conveniencia para registrar errores de IA"""
    ai_metrics_service_refactored.record_error(tenant_id, error_type, error_message)

def record_ai_intent_classification(tenant_id: str, intent: str, confidence: float, processing_time: float):
    """Función de conveniencia para registrar clasificaciones de intención"""
    ai_metrics_service_refactored.record_intent_classification(tenant_id, intent, confidence, processing_time)

def record_ai_data_validation(tenant_id: str, data_type: str, is_valid: bool, processing_time: float):
    """Función de conveniencia para registrar validaciones de datos"""
    ai_metrics_service_refactored.record_data_validation(tenant_id, data_type, is_valid, processing_time)

def record_ai_referral_detection(tenant_id: str, referral_code: str, confidence: float, processing_time: float):
    """Función de conveniencia para registrar detecciones de referidos"""
    ai_metrics_service_refactored.record_referral_detection(tenant_id, referral_code, confidence, processing_time)

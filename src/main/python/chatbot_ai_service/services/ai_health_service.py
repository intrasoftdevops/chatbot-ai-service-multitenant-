"""
Servicio refactorizado de monitoreo de salud para IA
"""

import logging
import time
from typing import Dict, Any, List

from chatbot_ai_service.services.health.system_metrics_service import SystemMetricsService
from chatbot_ai_service.services.health.performance_metrics_service import PerformanceMetricsService
from chatbot_ai_service.services.health.tenant_metrics_service import TenantMetricsService
from chatbot_ai_service.services.health.health_alerts_service import HealthAlertsService
from chatbot_ai_service.services.health.health_history_service import HealthHistoryService, HealthStatus

logger = logging.getLogger(__name__)

class AIHealthServiceRefactored:
    """
    Servicio refactorizado de monitoreo de salud para IA
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.error_count = 0
        
        # Inicializar servicios especializados
        self.system_metrics = SystemMetricsService()
        self.performance_metrics = PerformanceMetricsService()
        self.tenant_metrics = TenantMetricsService()
        self.health_alerts = HealthAlertsService()
        self.health_history = HealthHistoryService()
        
        logger.info("Servicio de monitoreo de salud refactorizado inicializado")
    
    def check_health(self) -> HealthStatus:
        """Verifica el estado de salud del servicio"""
        try:
            current_time = time.time()
            uptime = current_time - self.start_time
            
            # Obtener métricas del sistema
            memory_usage = self.system_metrics.get_memory_usage()
            cpu_usage = self.system_metrics.get_cpu_usage()
            
            # Calcular métricas de rendimiento
            response_time_avg = self.performance_metrics.calculate_avg_response_time()
            cache_hit_rate = self.performance_metrics.calculate_cache_hit_rate()
            
            # Contar tenants activos
            active_tenants = self.tenant_metrics.count_active_tenants()
            
            # Determinar estado de salud
            status = self._determine_health_status(
                memory_usage, cpu_usage, response_time_avg, 
                cache_hit_rate, active_tenants
            )
            
            # Crear estado de salud
            health_status = HealthStatus(
                status=status,
                timestamp=current_time,
                uptime=uptime,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                error_count=self.error_count,
                response_time_avg=response_time_avg,
                cache_hit_rate=cache_hit_rate,
                active_tenants=active_tenants,
                details=self._get_health_details()
            )
            
            # Agregar al historial
            self.health_history.add_to_history(health_status)
            
            logger.debug(f"Estado de salud verificado: {status}")
            return health_status
            
        except Exception as e:
            logger.error(f"Error verificando estado de salud: {str(e)}")
            return self._create_error_health_status(str(e))
    
    def _determine_health_status(self, memory_usage: float, cpu_usage: float, 
                               response_time_avg: float, cache_hit_rate: float, 
                               active_tenants: int) -> str:
        """Determina el estado de salud basado en las métricas"""
        try:
            # Verificar condiciones críticas
            if (memory_usage > 95.0 or cpu_usage > 95.0 or 
                response_time_avg > 10.0 or active_tenants == 0):
                return "unhealthy"
            
            # Verificar condiciones de degradación
            if (not self.system_metrics.is_memory_healthy(memory_usage) or 
                not self.system_metrics.is_cpu_healthy(cpu_usage) or 
                not self.performance_metrics.is_response_time_healthy(response_time_avg) or
                not self.performance_metrics.is_cache_healthy(cache_hit_rate)):
                return "degraded"
            
            return "healthy"
            
        except Exception as e:
            logger.error(f"Error determinando estado de salud: {str(e)}")
            return "unhealthy"
    
    def _get_health_details(self) -> Dict[str, Any]:
        """Obtiene detalles adicionales del estado de salud"""
        try:
            details = {
                "system_info": self.system_metrics.get_system_info(),
                "thresholds": {
                    "memory_threshold": self.system_metrics.memory_threshold,
                    "cpu_threshold": self.system_metrics.cpu_threshold,
                    "response_time_threshold": self.performance_metrics.response_time_threshold,
                    "cache_hit_rate_threshold": self.performance_metrics.cache_hit_rate_threshold
                },
                "recent_errors": self.health_history.get_recent_errors(),
                "performance_trends": self.performance_metrics.get_performance_trends(self.health_history.health_history)
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error obteniendo detalles de salud: {str(e)}")
            return {}
    
    def _create_error_health_status(self, error_message: str) -> HealthStatus:
        """Crea un estado de salud de error"""
        try:
            return HealthStatus(
                status="unhealthy",
                timestamp=time.time(),
                uptime=time.time() - self.start_time,
                memory_usage=0.0,
                cpu_usage=0.0,
                error_count=self.error_count + 1,
                response_time_avg=0.0,
                cache_hit_rate=0.0,
                active_tenants=0,
                details={"error": error_message}
            )
        except Exception as e:
            logger.error(f"Error creando estado de salud de error: {str(e)}")
            return HealthStatus(
                status="unhealthy",
                timestamp=time.time(),
                uptime=0.0,
                memory_usage=0.0,
                cpu_usage=0.0,
                error_count=0,
                response_time_avg=0.0,
                cache_hit_rate=0.0,
                active_tenants=0,
                details={"error": "Unknown error"}
            )
    
    def record_response_time(self, response_time: float):
        """Registra un tiempo de respuesta"""
        self.performance_metrics.record_response_time(response_time)
    
    def record_error(self):
        """Registra un error"""
        self.error_count += 1
    
    def get_health_history(self, hours: int = 24) -> List[HealthStatus]:
        """Obtiene el historial de salud de las últimas N horas"""
        return self.health_history.get_health_history(hours)
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen del estado de salud"""
        try:
            current_health = self.check_health()
            return self.health_history.get_health_summary(current_health)
        except Exception as e:
            logger.error(f"Error obteniendo resumen de salud: {str(e)}")
            return {}
    
    def is_healthy(self) -> bool:
        """Verifica si el servicio está saludable"""
        try:
            current_health = self.check_health()
            return current_health.status == "healthy"
        except Exception as e:
            logger.error(f"Error verificando si está saludable: {str(e)}")
            return False
    
    def get_health_alerts(self) -> List[Dict[str, Any]]:
        """Obtiene alertas de salud"""
        try:
            current_health = self.check_health()
            return self.health_alerts.get_health_alerts(current_health)
        except Exception as e:
            logger.error(f"Error obteniendo alertas de salud: {str(e)}")
            return []

# Instancia global del servicio de salud refactorizado
ai_health_service_refactored = AIHealthServiceRefactored()

# Funciones de conveniencia
def check_ai_health() -> HealthStatus:
    """Función de conveniencia para verificar el estado de salud de IA"""
    return ai_health_service_refactored.check_health()

def is_ai_healthy() -> bool:
    """Función de conveniencia para verificar si IA está saludable"""
    return ai_health_service_refactored.is_healthy()

def get_ai_health_summary() -> Dict[str, Any]:
    """Función de conveniencia para obtener el resumen de salud de IA"""
    return ai_health_service_refactored.get_health_summary()

def get_ai_health_alerts() -> List[Dict[str, Any]]:
    """Función de conveniencia para obtener alertas de salud de IA"""
    return ai_health_service_refactored.get_health_alerts()

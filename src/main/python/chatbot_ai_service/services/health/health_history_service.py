"""
Servicio de historial de salud
"""

import logging
import time
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class HealthStatus:
    """Estado de salud del servicio"""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: float
    uptime: float
    memory_usage: float
    cpu_usage: float
    error_count: int
    response_time_avg: float
    cache_hit_rate: float
    active_tenants: int
    details: Dict[str, Any]

class HealthHistoryService:
    """Servicio para historial de salud"""
    
    def __init__(self, max_history_size: int = 100):
        self.health_history: List[HealthStatus] = []
        self.max_history_size = max_history_size
    
    def add_to_history(self, health_status: HealthStatus):
        """Agrega un estado de salud al historial"""
        try:
            self.health_history.append(health_status)
            
            # Mantener solo el tamaño máximo del historial
            if len(self.health_history) > self.max_history_size:
                self.health_history = self.health_history[-self.max_history_size:]
                
        except Exception as e:
            logger.error(f"Error agregando al historial: {str(e)}")
    
    def get_health_history(self, hours: int = 24) -> List[HealthStatus]:
        """Obtiene el historial de salud de las últimas N horas"""
        try:
            cutoff_time = time.time() - (hours * 3600)
            return [status for status in self.health_history 
                   if status.timestamp >= cutoff_time]
        except Exception as e:
            logger.error(f"Error obteniendo historial de salud: {str(e)}")
            return []
    
    def get_health_summary(self, current_health: HealthStatus) -> Dict[str, Any]:
        """Obtiene un resumen del estado de salud"""
        try:
            # Calcular estadísticas del historial
            if self.health_history:
                healthy_count = sum(1 for status in self.health_history 
                                  if status.status == "healthy")
                degraded_count = sum(1 for status in self.health_history 
                                   if status.status == "degraded")
                unhealthy_count = sum(1 for status in self.health_history 
                                    if status.status == "unhealthy")
                
                total_checks = len(self.health_history)
                health_percentage = (healthy_count / total_checks * 100) if total_checks > 0 else 0
            else:
                healthy_count = degraded_count = unhealthy_count = 0
                health_percentage = 0
            
            return {
                "current_status": current_health.status,
                "uptime_hours": current_health.uptime / 3600,
                "memory_usage": current_health.memory_usage,
                "cpu_usage": current_health.cpu_usage,
                "response_time_avg": current_health.response_time_avg,
                "cache_hit_rate": current_health.cache_hit_rate,
                "active_tenants": current_health.active_tenants,
                "error_count": current_health.error_count,
                "health_percentage": health_percentage,
                "total_checks": len(self.health_history),
                "healthy_checks": healthy_count,
                "degraded_checks": degraded_count,
                "unhealthy_checks": unhealthy_count
            }
        except Exception as e:
            logger.error(f"Error obteniendo resumen de salud: {str(e)}")
            return {}
    
    def get_recent_errors(self) -> List[Dict[str, Any]]:
        """Obtiene errores recientes"""
        try:
            # Importar el servicio de logging
            from ..ai_logging_service import ai_logging_service
            
            stats = ai_logging_service.get_log_statistics()
            return [
                {
                    "error_count": stats.get('error_count', 0),
                    "warning_count": stats.get('warning_count', 0),
                    "total_entries": stats.get('total_entries', 0)
                }
            ]
        except Exception as e:
            logger.error(f"Error obteniendo errores recientes: {str(e)}")
            return []

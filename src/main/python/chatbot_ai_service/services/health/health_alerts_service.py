"""
Servicio de alertas de salud
"""

import logging
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class HealthAlert:
    """Alerta de salud"""
    type: str
    level: str  # "warning", "critical"
    message: str
    value: float
    threshold: float

class HealthAlertsService:
    """Servicio para alertas de salud"""
    
    def __init__(self):
        self.memory_threshold = 80.0
        self.cpu_threshold = 80.0
        self.response_time_threshold = 5.0
        self.cache_hit_rate_threshold = 50.0
    
    def get_health_alerts(self, health_status) -> List[Dict[str, Any]]:
        """Obtiene alertas de salud"""
        try:
            alerts = []
            
            # Verificar alertas de memoria
            if health_status.memory_usage > self.memory_threshold:
                alerts.append({
                    "type": "memory",
                    "level": "warning" if health_status.memory_usage < 90 else "critical",
                    "message": f"Alto uso de memoria: {health_status.memory_usage:.1f}%",
                    "value": health_status.memory_usage,
                    "threshold": self.memory_threshold
                })
            
            # Verificar alertas de CPU
            if health_status.cpu_usage > self.cpu_threshold:
                alerts.append({
                    "type": "cpu",
                    "level": "warning" if health_status.cpu_usage < 90 else "critical",
                    "message": f"Alto uso de CPU: {health_status.cpu_usage:.1f}%",
                    "value": health_status.cpu_usage,
                    "threshold": self.cpu_threshold
                })
            
            # Verificar alertas de tiempo de respuesta
            if health_status.response_time_avg > self.response_time_threshold:
                alerts.append({
                    "type": "response_time",
                    "level": "warning" if health_status.response_time_avg < 10 else "critical",
                    "message": f"Tiempo de respuesta alto: {health_status.response_time_avg:.2f}s",
                    "value": health_status.response_time_avg,
                    "threshold": self.response_time_threshold
                })
            
            # Verificar alertas de caché
            if health_status.cache_hit_rate < self.cache_hit_rate_threshold:
                alerts.append({
                    "type": "cache",
                    "level": "warning",
                    "message": f"Baja tasa de aciertos del caché: {health_status.cache_hit_rate:.1f}%",
                    "value": health_status.cache_hit_rate,
                    "threshold": self.cache_hit_rate_threshold
                })
            
            # Verificar alertas de errores
            if health_status.error_count > 0:
                alerts.append({
                    "type": "errors",
                    "level": "warning" if health_status.error_count < 10 else "critical",
                    "message": f"Errores detectados: {health_status.error_count}",
                    "value": health_status.error_count,
                    "threshold": 0
                })
            
            return alerts
        except Exception as e:
            logger.error(f"Error obteniendo alertas de salud: {str(e)}")
            return []

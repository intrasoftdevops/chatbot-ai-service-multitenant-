"""
Servicio de métricas de rendimiento
"""

import logging
import time
from typing import Dict, Any, List
from collections import deque

logger = logging.getLogger(__name__)

class PerformanceMetricsService:
    """Servicio para métricas de rendimiento"""
    
    def __init__(self):
        self.response_times = deque(maxlen=1000)  # Mantener últimos 1000 tiempos
        self.response_time_threshold = 5.0  # 5 segundos
        self.cache_hit_rate_threshold = 50.0  # 50%
    
    def record_response_time(self, response_time: float):
        """Registra un tiempo de respuesta"""
        try:
            self.response_times.append(response_time)
            logger.debug(f"Tiempo de respuesta registrado: {response_time:.3f}s")
        except Exception as e:
            logger.error(f"Error registrando tiempo de respuesta: {str(e)}")
    
    def calculate_avg_response_time(self) -> float:
        """Calcula el tiempo promedio de respuesta"""
        try:
            if not self.response_times:
                return 0.0
            
            # Usar solo los últimos 100 tiempos de respuesta
            recent_times = list(self.response_times)[-100:]
            return sum(recent_times) / len(recent_times)
        except Exception as e:
            logger.error(f"Error calculando tiempo promedio de respuesta: {str(e)}")
            return 0.0
    
    def calculate_cache_hit_rate(self) -> float:
        """Calcula la tasa de aciertos del caché"""
        try:
            # Importar el servicio de caché
            from ..ai_cache_service import ai_cache_service
            
            stats = ai_cache_service.get_stats()
            return stats.get('hit_rate', 0.0)
        except Exception as e:
            logger.error(f"Error calculando tasa de aciertos del caché: {str(e)}")
            return 0.0
    
    def is_response_time_healthy(self, response_time: float) -> bool:
        """Verifica si el tiempo de respuesta es saludable"""
        return response_time <= self.response_time_threshold
    
    def is_cache_healthy(self, cache_hit_rate: float) -> bool:
        """Verifica si la tasa de aciertos del caché es saludable"""
        return cache_hit_rate >= self.cache_hit_rate_threshold
    
    def get_performance_trends(self, health_history: List) -> Dict[str, str]:
        """Obtiene tendencias de rendimiento"""
        try:
            if len(health_history) < 2:
                return {"trend": "insufficient_data"}
            
            # Comparar con el estado anterior
            current = health_history[-1]
            previous = health_history[-2]
            
            trends = {
                "response_time_trend": "stable",
                "cache_hit_rate_trend": "stable"
            }
            
            # Analizar tendencias
            if current.response_time_avg > previous.response_time_avg + 0.5:
                trends["response_time_trend"] = "increasing"
            elif current.response_time_avg < previous.response_time_avg - 0.5:
                trends["response_time_trend"] = "decreasing"
            
            if current.cache_hit_rate > previous.cache_hit_rate + 5:
                trends["cache_hit_rate_trend"] = "increasing"
            elif current.cache_hit_rate < previous.cache_hit_rate - 5:
                trends["cache_hit_rate_trend"] = "decreasing"
            
            return trends
        except Exception as e:
            logger.error(f"Error obteniendo tendencias de rendimiento: {str(e)}")
            return {"trend": "error"}

"""
Servicio de métricas de rendimiento
"""

import logging
import time
from typing import Dict, Any
from collections import deque

logger = logging.getLogger(__name__)

class PerformanceMetricsService:
    """Servicio para métricas de rendimiento"""
    
    def __init__(self):
        self.response_times = deque(maxlen=1000)  # Mantener últimos 1000 tiempos
        self.start_time = time.time()
    
    def record_response_time(self, processing_time: float):
        """Registra tiempo de respuesta"""
        try:
            self.response_times.append(processing_time)
            logger.debug(f"Tiempo de respuesta registrado: {processing_time:.3f}s")
        except Exception as e:
            logger.error(f"Error registrando tiempo de respuesta: {str(e)}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de rendimiento"""
        try:
            if not self.response_times:
                return {
                    "avg_response_time": 0,
                    "min_response_time": 0,
                    "max_response_time": 0,
                    "p95_response_time": 0,
                    "p99_response_time": 0
                }
            
            sorted_times = sorted(self.response_times)
            n = len(sorted_times)
            
            return {
                "avg_response_time": sum(sorted_times) / n,
                "min_response_time": min(sorted_times),
                "max_response_time": max(sorted_times),
                "p95_response_time": sorted_times[int(n * 0.95)] if n > 0 else 0,
                "p99_response_time": sorted_times[int(n * 0.99)] if n > 0 else 0,
                "total_measurements": n
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas de rendimiento: {str(e)}")
            return {}
    
    def get_uptime(self) -> Dict[str, float]:
        """Obtiene tiempo de actividad"""
        try:
            current_time = time.time()
            uptime = current_time - self.start_time
            
            return {
                "uptime_seconds": uptime,
                "uptime_hours": uptime / 3600
            }
        except Exception as e:
            logger.error(f"Error obteniendo tiempo de actividad: {str(e)}")
            return {"uptime_seconds": 0, "uptime_hours": 0}
    
    def reset_performance_metrics(self):
        """Reinicia métricas de rendimiento"""
        try:
            self.response_times.clear()
            self.start_time = time.time()
            logger.info("Métricas de rendimiento reiniciadas")
        except Exception as e:
            logger.error(f"Error reiniciando métricas de rendimiento: {str(e)}")

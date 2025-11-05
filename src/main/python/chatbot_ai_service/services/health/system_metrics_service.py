"""
Servicio de métricas del sistema
"""

import logging
import psutil
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SystemMetricsService:
    """Servicio para métricas del sistema"""
    
    def __init__(self):
        self.memory_threshold = 80.0  # 80%
        self.cpu_threshold = 80.0     # 80%
    
    def get_memory_usage(self) -> float:
        """Obtiene el uso de memoria del proceso"""
        try:
            process = psutil.Process()
            memory_percent = process.memory_percent()
            return memory_percent
        except Exception as e:
            logger.error(f"Error obteniendo uso de memoria: {str(e)}")
            return 0.0
    
    def get_cpu_usage(self) -> float:
        """Obtiene el uso de CPU del proceso"""
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent(interval=1)
            return cpu_percent
        except Exception as e:
            logger.error(f"Error obteniendo uso de CPU: {str(e)}")
            return 0.0
    
    def get_system_info(self) -> Dict[str, Any]:
        """Obtiene información del sistema"""
        try:
            return {
                "platform": psutil.platform(),
                "python_version": psutil.sys.version,
                "process_id": psutil.Process().pid,
                "memory_threshold": self.memory_threshold,
                "cpu_threshold": self.cpu_threshold
            }
        except Exception as e:
            logger.error(f"Error obteniendo información del sistema: {str(e)}")
            return {}
    
    def is_memory_healthy(self, memory_usage: float) -> bool:
        """Verifica si el uso de memoria es saludable"""
        return memory_usage <= self.memory_threshold
    
    def is_cpu_healthy(self, cpu_usage: float) -> bool:
        """Verifica si el uso de CPU es saludable"""
        return cpu_usage <= self.cpu_threshold

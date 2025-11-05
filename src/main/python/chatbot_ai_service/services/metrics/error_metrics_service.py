"""
Servicio de métricas de errores
"""

import logging
import time
from typing import Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

class ErrorMetricsService:
    """Servicio para métricas de errores"""
    
    def __init__(self):
        self.error_metrics = defaultdict(int)
        self.error_logs = []
    
    def record_error(self, tenant_id: str, error_type: str, error_message: str):
        """Registra un error"""
        try:
            timestamp = time.time()
            
            # Métricas generales
            self.error_logs.append({
                'timestamp': timestamp,
                'tenant_id': tenant_id,
                'error_type': error_type,
                'error_message': error_message
            })
            
            # Métricas de errores
            self.error_metrics[error_type] += 1
            
            logger.debug(f"Error registrado para tenant {tenant_id}, tipo: {error_type}")
            
        except Exception as e:
            logger.error(f"Error registrando error: {str(e)}")
    
    def get_error_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de errores"""
        try:
            total_errors = sum(self.error_metrics.values())
            
            # Calcular distribución de errores
            error_distribution = {}
            for error_type, count in self.error_metrics.items():
                error_distribution[error_type] = {
                    "count": count,
                    "percentage": (count / total_errors * 100) if total_errors > 0 else 0
                }
            
            return {
                "total_errors": total_errors,
                "unique_error_types": len(self.error_metrics),
                "error_distribution": error_distribution,
                "most_common_error": max(self.error_metrics, key=self.error_metrics.get) if self.error_metrics else None
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas de errores: {str(e)}")
            return {}
    
    def get_error_logs(self) -> list:
        """Obtiene todos los logs de errores"""
        return self.error_logs.copy()
    
    def reset_error_metrics(self):
        """Reinicia métricas de errores"""
        try:
            self.error_metrics.clear()
            self.error_logs.clear()
            logger.info("Métricas de errores reiniciadas")
        except Exception as e:
            logger.error(f"Error reiniciando métricas de errores: {str(e)}")

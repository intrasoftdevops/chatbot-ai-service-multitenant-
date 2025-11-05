"""
Servicio de métricas de tenant para salud
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TenantMetricsService:
    """Servicio para métricas de tenant"""
    
    def __init__(self):
        self.active_tenants = 0
    
    def count_active_tenants(self) -> int:
        """Cuenta el número de tenants activos"""
        try:
            # Importar el servicio de métricas
            from ..ai_metrics_service import ai_metrics_service
            
            metrics = ai_metrics_service.get_general_metrics()
            self.active_tenants = metrics.get('active_tenants', 0)
            return self.active_tenants
        except Exception as e:
            logger.error(f"Error contando tenants activos: {str(e)}")
            return 0
    
    def is_tenants_healthy(self) -> bool:
        """Verifica si el número de tenants es saludable"""
        return self.active_tenants > 0

"""
Servicio de métricas de intenciones
"""

import logging
import time
from typing import Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

class IntentMetricsService:
    """Servicio para métricas de intenciones"""
    
    def __init__(self):
        self.intent_metrics = defaultdict(int)
        self.intent_classifications = []
    
    def record_intent_classification(self, tenant_id: str, intent: str, confidence: float, processing_time: float):
        """Registra clasificación de intenciones"""
        try:
            timestamp = time.time()
            
            # Métricas generales
            self.intent_classifications.append({
                'timestamp': timestamp,
                'tenant_id': tenant_id,
                'intent': intent,
                'confidence': confidence,
                'processing_time': processing_time
            })
            
            # Métricas de intención
            self.intent_metrics[intent] += 1
            
            logger.debug(f"Clasificación registrada para tenant {tenant_id}, intent: {intent}, confianza: {confidence}")
            
        except Exception as e:
            logger.error(f"Error registrando clasificación: {str(e)}")
    
    def get_intent_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de intenciones"""
        try:
            total_intents = sum(self.intent_metrics.values())
            
            # Calcular distribución de intenciones
            intent_distribution = {}
            for intent, count in self.intent_metrics.items():
                intent_distribution[intent] = {
                    "count": count,
                    "percentage": (count / total_intents * 100) if total_intents > 0 else 0
                }
            
            return {
                "total_intents": total_intents,
                "unique_intents": len(self.intent_metrics),
                "intent_distribution": intent_distribution,
                "most_common_intent": max(self.intent_metrics, key=self.intent_metrics.get) if self.intent_metrics else None
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas de intenciones: {str(e)}")
            return {}
    
    def get_intent_classifications(self) -> list:
        """Obtiene todas las clasificaciones de intenciones"""
        return self.intent_classifications.copy()
    
    def reset_intent_metrics(self):
        """Reinicia métricas de intenciones"""
        try:
            self.intent_metrics.clear()
            self.intent_classifications.clear()
            logger.info("Métricas de intenciones reiniciadas")
        except Exception as e:
            logger.error(f"Error reiniciando métricas de intenciones: {str(e)}")

"""
Servicio de métricas por tenant
"""

import logging
import time
from typing import Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

class TenantMetricsService:
    """Servicio para métricas por tenant"""
    
    def __init__(self):
        self.tenant_metrics = defaultdict(lambda: defaultdict(int))
        self.tenant_requests = []
        self.tenant_responses = []
        self.tenant_data_validations = []
        self.tenant_referral_detections = []
    
    def record_request(self, tenant_id: str, message_length: int, intent: str = None):
        """Registra una solicitud de tenant"""
        try:
            timestamp = time.time()
            
            # Métricas generales
            self.tenant_requests.append({
                'timestamp': timestamp,
                'tenant_id': tenant_id,
                'message_length': message_length,
                'intent': intent
            })
            
            # Métricas por tenant
            self.tenant_metrics[tenant_id]['requests'] += 1
            self.tenant_metrics[tenant_id]['total_message_length'] += message_length
            
            # Métricas de intención
            if intent:
                self.tenant_metrics[tenant_id]['intents'][intent] += 1
            
            logger.debug(f"Request registrada para tenant {tenant_id}, intent: {intent}")
            
        except Exception as e:
            logger.error(f"Error registrando solicitud: {str(e)}")
    
    def record_response(self, tenant_id: str, response_length: int, processing_time: float, intent: str = None):
        """Registra una respuesta de tenant"""
        try:
            timestamp = time.time()
            
            # Métricas generales
            self.tenant_responses.append({
                'timestamp': timestamp,
                'tenant_id': tenant_id,
                'response_length': response_length,
                'processing_time': processing_time,
                'intent': intent
            })
            
            # Métricas por tenant
            self.tenant_metrics[tenant_id]['responses'] += 1
            self.tenant_metrics[tenant_id]['total_response_length'] += response_length
            self.tenant_metrics[tenant_id]['total_processing_time'] += processing_time
            
            logger.debug(f"Response registrada para tenant {tenant_id}, tiempo: {processing_time:.3f}s")
            
        except Exception as e:
            logger.error(f"Error registrando respuesta: {str(e)}")
    
    def record_error(self, tenant_id: str, error_type: str, error_message: str):
        """Registra un error de tenant"""
        try:
            # Métricas por tenant
            self.tenant_metrics[tenant_id]['errors'] += 1
            self.tenant_metrics[tenant_id]['error_types'][error_type] += 1
            
            logger.debug(f"Error registrado para tenant {tenant_id}, tipo: {error_type}")
            
        except Exception as e:
            logger.error(f"Error registrando error: {str(e)}")
    
    def record_intent_classification(self, tenant_id: str, intent: str, confidence: float, processing_time: float):
        """Registra clasificación de intención de tenant"""
        try:
            # Métricas por tenant
            self.tenant_metrics[tenant_id]['intent_classifications'] += 1
            self.tenant_metrics[tenant_id]['intents'][intent] += 1
            
            logger.debug(f"Clasificación registrada para tenant {tenant_id}, intent: {intent}")
            
        except Exception as e:
            logger.error(f"Error registrando clasificación: {str(e)}")
    
    def record_data_validation(self, tenant_id: str, data_type: str, is_valid: bool, processing_time: float):
        """Registra validación de datos de tenant"""
        try:
            timestamp = time.time()
            
            # Métricas generales
            self.tenant_data_validations.append({
                'timestamp': timestamp,
                'tenant_id': tenant_id,
                'data_type': data_type,
                'is_valid': is_valid,
                'processing_time': processing_time
            })
            
            # Métricas por tenant
            self.tenant_metrics[tenant_id]['data_validations'] += 1
            if is_valid:
                self.tenant_metrics[tenant_id]['valid_data'] += 1
            else:
                self.tenant_metrics[tenant_id]['invalid_data'] += 1
            
            logger.debug(f"Validación registrada para tenant {tenant_id}, tipo: {data_type}, válido: {is_valid}")
            
        except Exception as e:
            logger.error(f"Error registrando validación: {str(e)}")
    
    def record_referral_detection(self, tenant_id: str, referral_code: str, confidence: float, processing_time: float):
        """Registra detección de referido de tenant"""
        try:
            timestamp = time.time()
            
            # Métricas generales
            self.tenant_referral_detections.append({
                'timestamp': timestamp,
                'tenant_id': tenant_id,
                'referral_code': referral_code,
                'confidence': confidence,
                'processing_time': processing_time
            })
            
            # Métricas por tenant
            self.tenant_metrics[tenant_id]['referral_detections'] += 1
            
            logger.debug(f"Detección de referido registrada para tenant {tenant_id}, código: {referral_code}")
            
        except Exception as e:
            logger.error(f"Error registrando detección de referido: {str(e)}")
    
    def get_tenant_metrics(self, tenant_id: str) -> Dict[str, Any]:
        """Obtiene métricas específicas de un tenant"""
        try:
            if tenant_id not in self.tenant_metrics:
                return {}
            
            tenant_data = self.tenant_metrics[tenant_id]
            
            # Calcular métricas del tenant
            requests = tenant_data.get('requests', 0)
            responses = tenant_data.get('responses', 0)
            errors = tenant_data.get('errors', 0)
            
            avg_response_time = 0
            if tenant_data.get('total_processing_time', 0) > 0 and responses > 0:
                avg_response_time = tenant_data['total_processing_time'] / responses
            
            avg_message_length = 0
            if tenant_data.get('total_message_length', 0) > 0 and requests > 0:
                avg_message_length = tenant_data['total_message_length'] / requests
            
            avg_response_length = 0
            if tenant_data.get('total_response_length', 0) > 0 and responses > 0:
                avg_response_length = tenant_data['total_response_length'] / responses
            
            return {
                "tenant_id": tenant_id,
                "requests": requests,
                "responses": responses,
                "errors": errors,
                "error_rate": (errors / requests * 100) if requests > 0 else 0,
                "avg_response_time": avg_response_time,
                "avg_message_length": avg_message_length,
                "avg_response_length": avg_response_length,
                "intent_classifications": tenant_data.get('intent_classifications', 0),
                "data_validations": tenant_data.get('data_validations', 0),
                "referral_detections": tenant_data.get('referral_detections', 0),
                "valid_data": tenant_data.get('valid_data', 0),
                "invalid_data": tenant_data.get('invalid_data', 0),
                "intents": dict(tenant_data.get('intents', {})),
                "error_types": dict(tenant_data.get('error_types', {}))
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas del tenant {tenant_id}: {str(e)}")
            return {}
    
    def get_all_tenant_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene métricas de todos los tenants"""
        try:
            return {tenant_id: self.get_tenant_metrics(tenant_id) for tenant_id in self.tenant_metrics.keys()}
        except Exception as e:
            logger.error(f"Error obteniendo métricas de todos los tenants: {str(e)}")
            return {}
    
    def get_active_tenants_count(self) -> int:
        """Obtiene número de tenants activos"""
        return len(self.tenant_metrics)
    
    def reset_tenant_metrics(self):
        """Reinicia métricas de tenants"""
        try:
            self.tenant_metrics.clear()
            self.tenant_requests.clear()
            self.tenant_responses.clear()
            self.tenant_data_validations.clear()
            self.tenant_referral_detections.clear()
            logger.info("Métricas de tenants reiniciadas")
        except Exception as e:
            logger.error(f"Error reiniciando métricas de tenants: {str(e)}")

"""
Servicios de configuración para IA
"""
import logging
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AIConfiguration:
    """
    Configuración del servicio de IA
    """
    # Configuración general
    max_response_length: int = 500
    max_context_length: int = 4000
    default_confidence_threshold: float = 0.6
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Configuración de intenciones
    intent_confidence_threshold: float = 0.6
    enable_intent_fallback: bool = True
    intent_fallback_response: str = "No pude entender tu solicitud. ¿Podrías reformularla?"
    
    # Configuración de validación
    enable_data_validation: bool = True
    validation_confidence_threshold: float = 0.7
    strict_validation: bool = False
    
    # Configuración de referidos
    enable_referral_detection: bool = True
    referral_confidence_threshold: float = 0.8
    max_referral_code_length: int = 20
    
    # Configuración de contexto
    enable_context_loading: bool = True
    context_cache_ttl: int = 3600  # 1 hora
    max_context_size: int = 10000
    
    # Configuración de rendimiento
    enable_performance_monitoring: bool = True
    performance_log_interval: int = 100  # Log cada 100 operaciones
    slow_operation_threshold: float = 2.0  # 2 segundos
    
    # Configuración de logging
    enable_detailed_logging: bool = True
    log_level: str = "INFO"
    log_retention_days: int = 30
    
    # Configuración de métricas
    enable_metrics: bool = True
    metrics_export_interval: int = 3600  # 1 hora
    max_metrics_buffer_size: int = 10000
    
    # Configuración de errores
    enable_error_recovery: bool = True
    max_consecutive_errors: int = 5
    error_cooldown_period: int = 300  # 5 minutos
    
    # Configuración de tenant
    default_tenant_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.default_tenant_config is None:
            self.default_tenant_config = {
                "candidate_name": "el candidato",
                "tenant_name": "la campaña",
                "campaign_info": "",
                "calendly_link": "",
                "forms_link": "",
                "privacy_url": ""
            }

class AIConfigurationService:
    """
    Servicio de configuración para IA
    """
    
    def __init__(self):
        self.config = AIConfiguration()
        self.tenant_configs = {}
        self.load_configuration()
    
    def load_configuration(self):
        """
        Carga la configuración desde variables de entorno y archivos.
        """
        try:
            # Cargar desde variables de entorno
            self._load_from_environment()
            
            # Cargar desde archivo de configuración si existe
            config_file = os.getenv('AI_CONFIG_FILE', 'ai_config.json')
            if os.path.exists(config_file):
                self._load_from_file(config_file)
            
            logger.info("Configuración de IA cargada exitosamente")
            
        except Exception as e:
            logger.error(f"Error cargando configuración: {str(e)}")
            # Usar configuración por defecto
            self.config = AIConfiguration()
    
    def _load_from_environment(self):
        """
        Carga configuración desde variables de entorno.
        """
        try:
            # Configuración general
            if os.getenv('AI_MAX_RESPONSE_LENGTH'):
                self.config.max_response_length = int(os.getenv('AI_MAX_RESPONSE_LENGTH'))
            
            if os.getenv('AI_MAX_CONTEXT_LENGTH'):
                self.config.max_context_length = int(os.getenv('AI_MAX_CONTEXT_LENGTH'))
            
            if os.getenv('AI_DEFAULT_CONFIDENCE_THRESHOLD'):
                self.config.default_confidence_threshold = float(os.getenv('AI_DEFAULT_CONFIDENCE_THRESHOLD'))
            
            if os.getenv('AI_MAX_RETRIES'):
                self.config.max_retries = int(os.getenv('AI_MAX_RETRIES'))
            
            if os.getenv('AI_RETRY_DELAY'):
                self.config.retry_delay = float(os.getenv('AI_RETRY_DELAY'))
            
            # Configuración de intenciones
            if os.getenv('AI_INTENT_CONFIDENCE_THRESHOLD'):
                self.config.intent_confidence_threshold = float(os.getenv('AI_INTENT_CONFIDENCE_THRESHOLD'))
            
            if os.getenv('AI_ENABLE_INTENT_FALLBACK'):
                self.config.enable_intent_fallback = os.getenv('AI_ENABLE_INTENT_FALLBACK').lower() == 'true'
            
            if os.getenv('AI_INTENT_FALLBACK_RESPONSE'):
                self.config.intent_fallback_response = os.getenv('AI_INTENT_FALLBACK_RESPONSE')
            
            # Configuración de validación
            if os.getenv('AI_ENABLE_DATA_VALIDATION'):
                self.config.enable_data_validation = os.getenv('AI_ENABLE_DATA_VALIDATION').lower() == 'true'
            
            if os.getenv('AI_VALIDATION_CONFIDENCE_THRESHOLD'):
                self.config.validation_confidence_threshold = float(os.getenv('AI_VALIDATION_CONFIDENCE_THRESHOLD'))
            
            if os.getenv('AI_STRICT_VALIDATION'):
                self.config.strict_validation = os.getenv('AI_STRICT_VALIDATION').lower() == 'true'
            
            # Configuración de referidos
            if os.getenv('AI_ENABLE_REFERRAL_DETECTION'):
                self.config.enable_referral_detection = os.getenv('AI_ENABLE_REFERRAL_DETECTION').lower() == 'true'
            
            if os.getenv('AI_REFERRAL_CONFIDENCE_THRESHOLD'):
                self.config.referral_confidence_threshold = float(os.getenv('AI_REFERRAL_CONFIDENCE_THRESHOLD'))
            
            if os.getenv('AI_MAX_REFERRAL_CODE_LENGTH'):
                self.config.max_referral_code_length = int(os.getenv('AI_MAX_REFERRAL_CODE_LENGTH'))
            
            # Configuración de contexto
            if os.getenv('AI_ENABLE_CONTEXT_LOADING'):
                self.config.enable_context_loading = os.getenv('AI_ENABLE_CONTEXT_LOADING').lower() == 'true'
            
            if os.getenv('AI_CONTEXT_CACHE_TTL'):
                self.config.context_cache_ttl = int(os.getenv('AI_CONTEXT_CACHE_TTL'))
            
            if os.getenv('AI_MAX_CONTEXT_SIZE'):
                self.config.max_context_size = int(os.getenv('AI_MAX_CONTEXT_SIZE'))
            
            # Configuración de rendimiento
            if os.getenv('AI_ENABLE_PERFORMANCE_MONITORING'):
                self.config.enable_performance_monitoring = os.getenv('AI_ENABLE_PERFORMANCE_MONITORING').lower() == 'true'
            
            if os.getenv('AI_PERFORMANCE_LOG_INTERVAL'):
                self.config.performance_log_interval = int(os.getenv('AI_PERFORMANCE_LOG_INTERVAL'))
            
            if os.getenv('AI_SLOW_OPERATION_THRESHOLD'):
                self.config.slow_operation_threshold = float(os.getenv('AI_SLOW_OPERATION_THRESHOLD'))
            
            # Configuración de logging
            if os.getenv('AI_ENABLE_DETAILED_LOGGING'):
                self.config.enable_detailed_logging = os.getenv('AI_ENABLE_DETAILED_LOGGING').lower() == 'true'
            
            if os.getenv('AI_LOG_LEVEL'):
                self.config.log_level = os.getenv('AI_LOG_LEVEL')
            
            if os.getenv('AI_LOG_RETENTION_DAYS'):
                self.config.log_retention_days = int(os.getenv('AI_LOG_RETENTION_DAYS'))
            
            # Configuración de métricas
            if os.getenv('AI_ENABLE_METRICS'):
                self.config.enable_metrics = os.getenv('AI_ENABLE_METRICS').lower() == 'true'
            
            if os.getenv('AI_METRICS_EXPORT_INTERVAL'):
                self.config.metrics_export_interval = int(os.getenv('AI_METRICS_EXPORT_INTERVAL'))
            
            if os.getenv('AI_MAX_METRICS_BUFFER_SIZE'):
                self.config.max_metrics_buffer_size = int(os.getenv('AI_MAX_METRICS_BUFFER_SIZE'))
            
            # Configuración de errores
            if os.getenv('AI_ENABLE_ERROR_RECOVERY'):
                self.config.enable_error_recovery = os.getenv('AI_ENABLE_ERROR_RECOVERY').lower() == 'true'
            
            if os.getenv('AI_MAX_CONSECUTIVE_ERRORS'):
                self.config.max_consecutive_errors = int(os.getenv('AI_MAX_CONSECUTIVE_ERRORS'))
            
            if os.getenv('AI_ERROR_COOLDOWN_PERIOD'):
                self.config.error_cooldown_period = int(os.getenv('AI_ERROR_COOLDOWN_PERIOD'))
            
        except Exception as e:
            logger.error(f"Error cargando configuración desde variables de entorno: {str(e)}")
    
    def _load_from_file(self, config_file: str):
        """
        Carga configuración desde archivo JSON.
        
        Args:
            config_file: Ruta del archivo de configuración
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Actualizar configuración con datos del archivo
            for key, value in config_data.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            logger.info(f"Configuración cargada desde {config_file}")
            
        except Exception as e:
            logger.error(f"Error cargando configuración desde archivo {config_file}: {str(e)}")
    
    def get_configuration(self) -> AIConfiguration:
        """
        Obtiene la configuración actual.
        
        Returns:
            Configuración actual
        """
        return self.config
    
    def update_configuration(self, new_config: Dict[str, Any]):
        """
        Actualiza la configuración con nuevos valores.
        
        Args:
            new_config: Nuevos valores de configuración
        """
        try:
            for key, value in new_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    logger.info(f"Configuración actualizada: {key} = {value}")
                else:
                    logger.warning(f"Clave de configuración no encontrada: {key}")
            
        except Exception as e:
            logger.error(f"Error actualizando configuración: {str(e)}")
    
    def get_tenant_configuration(self, tenant_id: str) -> Dict[str, Any]:
        """
        Obtiene la configuración específica de un tenant.
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            Configuración del tenant
        """
        try:
            if tenant_id in self.tenant_configs:
                return self.tenant_configs[tenant_id]
            
            # Usar configuración por defecto si no existe configuración específica
            return self.config.default_tenant_config.copy()
            
        except Exception as e:
            logger.error(f"Error obteniendo configuración del tenant {tenant_id}: {str(e)}")
            return self.config.default_tenant_config.copy()
    
    def set_tenant_configuration(self, tenant_id: str, config: Dict[str, Any]):
        """
        Establece la configuración específica de un tenant.
        
        Args:
            tenant_id: ID del tenant
            config: Configuración del tenant
        """
        try:
            self.tenant_configs[tenant_id] = config.copy()
            logger.info(f"Configuración del tenant {tenant_id} actualizada")
            
        except Exception as e:
            logger.error(f"Error estableciendo configuración del tenant {tenant_id}: {str(e)}")
    
    def validate_configuration(self) -> List[str]:
        """
        Valida la configuración actual.
        
        Returns:
            Lista de errores de validación
        """
        try:
            errors = []
            
            # Validar valores numéricos
            if self.config.max_response_length <= 0:
                errors.append("max_response_length debe ser mayor que 0")
            
            if self.config.max_context_length <= 0:
                errors.append("max_context_length debe ser mayor que 0")
            
            if not 0 <= self.config.default_confidence_threshold <= 1:
                errors.append("default_confidence_threshold debe estar entre 0 y 1")
            
            if not 0 <= self.config.intent_confidence_threshold <= 1:
                errors.append("intent_confidence_threshold debe estar entre 0 y 1")
            
            if not 0 <= self.config.validation_confidence_threshold <= 1:
                errors.append("validation_confidence_threshold debe estar entre 0 y 1")
            
            if not 0 <= self.config.referral_confidence_threshold <= 1:
                errors.append("referral_confidence_threshold debe estar entre 0 y 1")
            
            if self.config.max_retries < 0:
                errors.append("max_retries debe ser mayor o igual que 0")
            
            if self.config.retry_delay < 0:
                errors.append("retry_delay debe ser mayor o igual que 0")
            
            if self.config.context_cache_ttl <= 0:
                errors.append("context_cache_ttl debe ser mayor que 0")
            
            if self.config.max_context_size <= 0:
                errors.append("max_context_size debe ser mayor que 0")
            
            if self.config.performance_log_interval <= 0:
                errors.append("performance_log_interval debe ser mayor que 0")
            
            if self.config.slow_operation_threshold <= 0:
                errors.append("slow_operation_threshold debe ser mayor que 0")
            
            if self.config.log_retention_days <= 0:
                errors.append("log_retention_days debe ser mayor que 0")
            
            if self.config.metrics_export_interval <= 0:
                errors.append("metrics_export_interval debe ser mayor que 0")
            
            if self.config.max_metrics_buffer_size <= 0:
                errors.append("max_metrics_buffer_size debe ser mayor que 0")
            
            if self.config.max_consecutive_errors < 0:
                errors.append("max_consecutive_errors debe ser mayor o igual que 0")
            
            if self.config.error_cooldown_period <= 0:
                errors.append("error_cooldown_period debe ser mayor que 0")
            
            # Validar nivel de log
            valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if self.config.log_level not in valid_log_levels:
                errors.append(f"log_level debe ser uno de: {', '.join(valid_log_levels)}")
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validando configuración: {str(e)}")
            return [f"Error validando configuración: {str(e)}"]
    
    def export_configuration(self, filename: str = None) -> str:
        """
        Exporta la configuración a un archivo JSON.
        
        Args:
            filename: Nombre del archivo (opcional)
            
        Returns:
            Ruta del archivo exportado
        """
        try:
            if not filename:
                filename = 'ai_config_export.json'
            
            # Convertir configuración a diccionario
            config_dict = {
                'general': {
                    'max_response_length': self.config.max_response_length,
                    'max_context_length': self.config.max_context_length,
                    'default_confidence_threshold': self.config.default_confidence_threshold,
                    'max_retries': self.config.max_retries,
                    'retry_delay': self.config.retry_delay
                },
                'intents': {
                    'intent_confidence_threshold': self.config.intent_confidence_threshold,
                    'enable_intent_fallback': self.config.enable_intent_fallback,
                    'intent_fallback_response': self.config.intent_fallback_response
                },
                'validation': {
                    'enable_data_validation': self.config.enable_data_validation,
                    'validation_confidence_threshold': self.config.validation_confidence_threshold,
                    'strict_validation': self.config.strict_validation
                },
                'referrals': {
                    'enable_referral_detection': self.config.enable_referral_detection,
                    'referral_confidence_threshold': self.config.referral_confidence_threshold,
                    'max_referral_code_length': self.config.max_referral_code_length
                },
                'context': {
                    'enable_context_loading': self.config.enable_context_loading,
                    'context_cache_ttl': self.config.context_cache_ttl,
                    'max_context_size': self.config.max_context_size
                },
                'performance': {
                    'enable_performance_monitoring': self.config.enable_performance_monitoring,
                    'performance_log_interval': self.config.performance_log_interval,
                    'slow_operation_threshold': self.config.slow_operation_threshold
                },
                'logging': {
                    'enable_detailed_logging': self.config.enable_detailed_logging,
                    'log_level': self.config.log_level,
                    'log_retention_days': self.config.log_retention_days
                },
                'metrics': {
                    'enable_metrics': self.config.enable_metrics,
                    'metrics_export_interval': self.config.metrics_export_interval,
                    'max_metrics_buffer_size': self.config.max_metrics_buffer_size
                },
                'errors': {
                    'enable_error_recovery': self.config.enable_error_recovery,
                    'max_consecutive_errors': self.config.max_consecutive_errors,
                    'error_cooldown_period': self.config.error_cooldown_period
                },
                'tenants': self.tenant_configs
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuración exportada a {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error exportando configuración: {str(e)}")
            return None

# Instancia global del servicio de configuración
ai_configuration_service = AIConfigurationService()

def get_ai_configuration() -> AIConfiguration:
    """
    Función de conveniencia para obtener la configuración de IA.
    """
    return ai_configuration_service.get_configuration()

def get_tenant_configuration(tenant_id: str) -> Dict[str, Any]:
    """
    Función de conveniencia para obtener la configuración de un tenant.
    """
    return ai_configuration_service.get_tenant_configuration(tenant_id)

def update_ai_configuration(new_config: Dict[str, Any]):
    """
    Función de conveniencia para actualizar la configuración de IA.
    """
    ai_configuration_service.update_configuration(new_config)

def validate_ai_configuration() -> List[str]:
    """
    Función de conveniencia para validar la configuración de IA.
    """
    return ai_configuration_service.validate_configuration()

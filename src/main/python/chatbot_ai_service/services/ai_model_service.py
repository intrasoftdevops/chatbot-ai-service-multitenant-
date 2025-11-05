"""
Servicio para manejo de modelos de IA específicos por tenant
"""

import logging
from typing import Dict, Optional
import google.generativeai as genai

from chatbot_ai_service.models.tenant_models import TenantConfig

logger = logging.getLogger(__name__)

class AIModelService:
    """Servicio para gestión de modelos de IA por tenant"""
    
    def __init__(self):
        self._gemini_models: Dict[str, genai.GenerativeModel] = {}
    
    async def get_tenant_ai_model(self, tenant_id: str, tenant_config: TenantConfig) -> Optional[genai.GenerativeModel]:
        """Obtiene o crea el modelo de IA para un tenant específico"""
        try:
            if tenant_id in self._gemini_models:
                return self._gemini_models[tenant_id]
            
            # Configurar Gemini para el tenant
            ai_config = tenant_config.ai_config
            if not ai_config:
                ai_config = tenant_config.ai_config  # Usar configuración por defecto
            
            # Configurar modelo Gemini
            model_name = ai_config.model if ai_config else "gemini-pro"
            model = genai.GenerativeModel(model_name)
            
            # Configurar parámetros
            generation_config = genai.types.GenerationConfig(
                temperature=ai_config.temperature if ai_config else 0.7,
                max_output_tokens=ai_config.max_tokens if ai_config else 1000,
            )
            
            model.generation_config = generation_config
            
            # Guardar modelo
            self._gemini_models[tenant_id] = model
            
            logger.info(f"Modelo de IA configurado para tenant {tenant_id}: {model_name}")
            return model
            
        except Exception as e:
            logger.error(f"Error al configurar modelo de IA para tenant {tenant_id}: {e}")
            return None
    
    def clear_tenant_model(self, tenant_id: str):
        """Limpia el modelo de un tenant específico"""
        if tenant_id in self._gemini_models:
            del self._gemini_models[tenant_id]
            logger.info(f"Modelo de IA eliminado para tenant {tenant_id}")
    
    def get_available_models(self) -> Dict[str, str]:
        """Retorna los modelos disponibles por tenant"""
        return {tenant_id: str(model) for tenant_id, model in self._gemini_models.items()}

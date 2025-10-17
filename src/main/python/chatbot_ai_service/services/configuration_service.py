"""
Servicio de configuración simplificado para el Chatbot AI Service

Este servicio NO maneja Firebase directamente, sino que recibe la configuración
del proyecto Political Referrals via HTTP cuando es necesario.
"""
import logging
from typing import Optional, Dict, Any
import httpx
import os

logger = logging.getLogger(__name__)

class ConfigurationService:
    """Servicio para obtener configuración de tenants desde el proyecto Java"""
    
    def __init__(self):
        self.java_service_url = os.getenv("POLITICAL_REFERRALS_SERVICE_URL", "http://localhost:8080")
        logger.info(f"ConfigurationService inicializado con URL: {self.java_service_url}")
        self._config_cache = {}  # Cache simple de configuraciones
    
    def get_tenant_config(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la configuración de un tenant desde el servicio Java
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            Configuración del tenant como dict o None si no existe
        """
        try:
            # Verificar cache
            if tenant_id in self._config_cache:
                logger.debug(f"Retornando configuración de tenant {tenant_id} desde cache")
                return self._config_cache[tenant_id]
            
            logger.info(f"Obteniendo configuración desde servicio Java para tenant: {tenant_id}")
            
            # Llamar al servicio Java para obtener configuración
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{self.java_service_url}/api/v1/tenants/{tenant_id}")
                
                if response.status_code == 200:
                    config = response.json()
                    # Guardar en cache
                    self._config_cache[tenant_id] = config
                    logger.info(f"Configuración obtenida exitosamente para tenant: {tenant_id}")
                    return config
                else:
                    logger.warning(f"No se pudo obtener configuración para tenant {tenant_id}: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error obteniendo configuración del tenant {tenant_id}: {str(e)}")
            return None
    
    def clear_cache(self, tenant_id: Optional[str] = None):
        """
        Limpia el cache de configuraciones
        
        Args:
            tenant_id: ID del tenant específico a limpiar, o None para limpiar todo
        """
        if tenant_id:
            self._config_cache.pop(tenant_id, None)
            logger.info(f"Cache limpiado para tenant: {tenant_id}")
        else:
            self._config_cache.clear()
            logger.info("Cache completo limpiado")
    
    def get_ai_config(self, tenant_id: str) -> Dict[str, Any]:
        """
        Obtiene solo la configuración de IA para un tenant
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            Configuración de IA
        """
        config = self.get_tenant_config(tenant_id)
        if config and "aiConfig" in config:
            return config["aiConfig"]
        
        # Configuración por defecto
        return {
            "model": "gemini-1.5-flash",
            "temperature": 0.7,
            "maxTokens": 1000,
            "enableContext": True
        }
    
    def get_branding_config(self, tenant_id: str) -> Dict[str, Any]:
        """
        Obtiene solo la configuración de branding para un tenant
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            Configuración de branding
        """
        config = self.get_tenant_config(tenant_id)
        if config and "branding" in config:
            return config["branding"]
        
        # Configuración por defecto
        return {
            "welcomeMessage": "¡Hola! ¿En qué puedo ayudarte?",
            "contactName": "Asistente"
        }


# Instancia global para compatibilidad
configuration_service = ConfigurationService()

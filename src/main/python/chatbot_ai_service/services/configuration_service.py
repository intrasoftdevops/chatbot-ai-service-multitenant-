"""
Servicio de configuración simplificado para el Chatbot AI Service

Este servicio NO maneja Firebase directamente, sino que recibe la configuración
del proyecto Political Referrals via HTTP cuando es necesario.
"""
import logging
import time
from typing import Optional, Dict, Any
import httpx
import os

logger = logging.getLogger(__name__)

class ConfigurationService:
    """Servicio para obtener configuración de tenants desde el proyecto Java"""
    
    def __init__(self):
        self.java_service_url = os.getenv("POLITICAL_REFERRALS_SERVICE_URL", "http://localhost:8080")
        logger.info(f"ConfigurationService inicializado con URL: {self.java_service_url}")
        # 🚀 OPTIMIZACIÓN: Cache más agresivo con TTL
        self._config_cache = {}
        self._cache_timestamps = {}  # Para TTL
        self._cache_ttl = 300  # 5 minutos TTL
        self._max_cache_size = 100  # Máximo 100 tenants en cache
    
    def get_tenant_config(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la configuración de un tenant desde el servicio Java
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            Configuración del tenant como dict o None si no existe
        """
        try:
            # 🚀 OPTIMIZACIÓN: Verificar cache con TTL
            if tenant_id in self._config_cache:
                cache_time = self._cache_timestamps.get(tenant_id, 0)
                current_time = time.time()
                if current_time - cache_time < self._cache_ttl:
                    logger.debug(f"✅ Configuración obtenida desde cache para tenant: {tenant_id}")
                    return self._config_cache[tenant_id]
                else:
                    # Cache expirado, limpiar
                    del self._config_cache[tenant_id]
                    del self._cache_timestamps[tenant_id]
            
            logger.info(f"Obteniendo configuración desde servicio Java para tenant: {tenant_id}")
            
            # Llamar al servicio Java para obtener configuración
            headers = {
                "User-Agent": "Chatbot-AI-Service/1.0",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            url = f"{self.java_service_url}/api/tenants/{tenant_id}/config"
            logger.info(f"Llamando a URL: {url}")
            
            with httpx.Client(timeout=10.0, headers=headers) as client:  # 🚀 Reducido timeout
                response = client.get(url)
                logger.info(f"Respuesta recibida: status={response.status_code}")
                
                if response.status_code == 200:
                    config = response.json()
                    # Normalizar configuración del Java a Python
                    config = self._normalize_java_config(config)
                    # Guardar en cache con timestamp
                    self._config_cache[tenant_id] = config
                    self._cache_timestamps[tenant_id] = time.time()
                    
                    # Limpiar cache si excede tamaño máximo
                    self._cleanup_cache()
                    
                    logger.info(f"✅ Configuración obtenida exitosamente para tenant: {tenant_id}")
                    return config
                else:
                    logger.warning(f"No se pudo obtener configuración para tenant {tenant_id}: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error obteniendo configuración del tenant {tenant_id}: {str(e)}")
            return None
    
    def _normalize_java_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza la configuración del Java (camelCase) a Python (snake_case)
        
        Args:
            config: Configuración del Java
            
        Returns:
            Configuración normalizada para Python
        """
        try:
            normalized = config.copy()
            
            # Normalizar aiConfig -> ai_config
            if "aiConfig" in normalized:
                normalized["ai_config"] = normalized.pop("aiConfig")
            
            # Normalizar otros campos si es necesario
            if "watiApiToken" in normalized:
                normalized["wati_api_token"] = normalized.pop("watiApiToken")
            
            if "watiApiEndpoint" in normalized:
                normalized["wati_api_endpoint"] = normalized.pop("watiApiEndpoint")
            
            if "watiTenantId" in normalized:
                normalized["wati_tenant_id"] = normalized.pop("watiTenantId")
            
            # 🔧 FIX: Normalizar numeroWhatsapp -> numero_whatsapp
            if "numeroWhatsapp" in normalized:
                normalized["numero_whatsapp"] = normalized.pop("numeroWhatsapp")
            
            logger.info(f"Configuración normalizada: {list(normalized.keys())}")
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizando configuración: {str(e)}")
            return config
    
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
        if config and "ai_config" in config:
            return config["ai_config"]
        
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
    
    def _cleanup_cache(self):
        """Limpia el cache si excede el tamaño máximo"""
        if len(self._config_cache) > self._max_cache_size:
            # Eliminar entradas más antiguas
            sorted_items = sorted(self._cache_timestamps.items(), key=lambda x: x[1])
            items_to_remove = len(self._config_cache) - self._max_cache_size + 10  # Limpiar 10 extras
            
            for tenant_id, _ in sorted_items[:items_to_remove]:
                if tenant_id in self._config_cache:
                    del self._config_cache[tenant_id]
                if tenant_id in self._cache_timestamps:
                    del self._cache_timestamps[tenant_id]
            
            logger.debug(f"Cache limpiado: {items_to_remove} entradas eliminadas")


# Instancia global para compatibilidad
configuration_service = ConfigurationService()

"""
Servicio de cache inteligente con contexto de usuario
Optimiza respuestas basadas en contexto e intención del usuario
"""
import logging
import time
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from chatbot_ai_service.services.cache_service import cache_service

logger = logging.getLogger(__name__)

class IntelligentCacheService:
    """Servicio de cache inteligente con contexto de usuario"""
    
    def __init__(self):
        self._context_cache = {}  # Cache por contexto + intención
        self._user_context_cache = {}  # Cache por usuario específico
        self._response_templates = {}  # Templates de respuesta personalizados
        
    def _generate_cache_key(self, tenant_id: str, user_context: Dict[str, Any], 
                           intention: str, query: str) -> str:
        """Genera clave de cache basada en contexto e intención"""
        # Crear hash del contexto relevante
        context_str = f"{tenant_id}:{intention}:{user_context.get('name', '')}:{user_context.get('city', '')}"
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        return f"intelligent:{context_str}:{query_hash}"
    
    def get_cached_response(self, tenant_id: str, user_context: Dict[str, Any], 
                           intention: str, query: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene respuesta desde cache inteligente
        
        Args:
            tenant_id: ID del tenant
            user_context: Contexto del usuario (nombre, ciudad, etc.)
            intention: Intención detectada
            query: Consulta del usuario
            
        Returns:
            Respuesta cacheada o None
        """
        try:
            cache_key = self._generate_cache_key(tenant_id, user_context, intention, query)
            
            # Buscar en cache de contexto
            if cache_key in self._context_cache:
                cached_data = self._context_cache[cache_key]
                
                # Verificar si el cache no ha expirado (1 hora)
                if time.time() - cached_data["timestamp"] < 3600:
                    logger.info(f"🎯 Cache hit inteligente para {tenant_id}: {intention}")
                    return cached_data["response"]
                else:
                    # Cache expirado, limpiar
                    del self._context_cache[cache_key]
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo cache inteligente: {str(e)}")
            return None
    
    def cache_response(self, tenant_id: str, user_context: Dict[str, Any], 
                      intention: str, query: str, response: Dict[str, Any]):
        """
        Guarda respuesta en cache inteligente
        
        Args:
            tenant_id: ID del tenant
            user_context: Contexto del usuario
            intention: Intención detectada
            query: Consulta del usuario
            response: Respuesta generada
        """
        try:
            cache_key = self._generate_cache_key(tenant_id, user_context, intention, query)
            
            self._context_cache[cache_key] = {
                "response": response,
                "timestamp": time.time(),
                "tenant_id": tenant_id,
                "intention": intention,
                "user_context": user_context
            }
            
            logger.info(f"💾 Respuesta cacheada inteligentemente para {tenant_id}: {intention}")
            
        except Exception as e:
            logger.error(f"Error guardando cache inteligente: {str(e)}")
    
    def get_personalized_template(self, tenant_id: str, user_context: Dict[str, Any], 
                                 intention: str) -> Optional[str]:
        """
        Obtiene template personalizado para el usuario
        
        Args:
            tenant_id: ID del tenant
            user_context: Contexto del usuario
            intention: Intención detectada
            
        Returns:
            Template personalizado o None
        """
        try:
            user_key = f"{tenant_id}:{user_context.get('name', '')}:{user_context.get('city', '')}"
            
            if user_key in self._response_templates:
                templates = self._response_templates[user_key]
                return templates.get(intention)
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo template personalizado: {str(e)}")
            return None
    
    def cache_personalized_template(self, tenant_id: str, user_context: Dict[str, Any], 
                                  intention: str, template: str):
        """
        Guarda template personalizado para el usuario
        
        Args:
            tenant_id: ID del tenant
            user_context: Contexto del usuario
            intention: Intención detectada
            template: Template personalizado
        """
        try:
            user_key = f"{tenant_id}:{user_context.get('name', '')}:{user_context.get('city', '')}"
            
            if user_key not in self._response_templates:
                self._response_templates[user_key] = {}
            
            self._response_templates[user_key][intention] = template
            
            logger.info(f"📝 Template personalizado guardado para {user_key}: {intention}")
            
        except Exception as e:
            logger.error(f"Error guardando template personalizado: {str(e)}")
    
    def personalize_response(self, base_response: str, user_context: Dict[str, Any], 
                           tenant_config: Dict[str, Any]) -> str:
        """
        Personaliza respuesta basada en contexto del usuario
        
        Args:
            base_response: Respuesta base
            user_context: Contexto del usuario
            tenant_config: Configuración del tenant
            
        Returns:
            Respuesta personalizada
        """
        try:
            personalized = base_response
            
            # Personalizar con nombre del usuario
            if user_context.get("name"):
                name = user_context["name"].title()
                personalized = personalized.replace("{name}", name)
                personalized = personalized.replace("{user_name}", name)
            
            # Personalizar con ciudad del usuario
            if user_context.get("city"):
                city = user_context["city"].title()
                personalized = personalized.replace("{city}", city)
                personalized = personalized.replace("{user_city}", city)
            
            # Personalizar con configuración del tenant
            if tenant_config.get("branding", {}).get("contactName"):
                contact_name = tenant_config["branding"]["contactName"]
                personalized = personalized.replace("{contact_name}", contact_name)
            
            return personalized
            
        except Exception as e:
            logger.error(f"Error personalizando respuesta: {str(e)}")
            return base_response
    
    def clear_tenant_cache(self, tenant_id: str):
        """Limpia cache de un tenant específico"""
        try:
            # Limpiar cache de contexto
            keys_to_remove = [k for k in self._context_cache.keys() if k.startswith(f"intelligent:{tenant_id}:")]
            for key in keys_to_remove:
                del self._context_cache[key]
            
            # Limpiar templates personalizados
            keys_to_remove = [k for k in self._response_templates.keys() if k.startswith(f"{tenant_id}:")]
            for key in keys_to_remove:
                del self._response_templates[key]
            
            logger.info(f"🗑️ Cache inteligente limpiado para tenant {tenant_id}")
            
        except Exception as e:
            logger.error(f"Error limpiando cache inteligente: {str(e)}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache inteligente"""
        return {
            "context_cache_size": len(self._context_cache),
            "personalized_templates": len(self._response_templates),
            "total_users": len(set(k.split(':')[1] for k in self._response_templates.keys())),
            "cache_hit_ratio": "N/A"  # Se calcularía con métricas adicionales
        }

# Instancia global
intelligent_cache_service = IntelligentCacheService()

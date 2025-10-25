"""
Servicio de caché para respuestas de IA usando Redis

Este servicio proporciona:
- Caché de respuestas por tenant + query + intent
- TTL configurable por tipo de intención
- Invalidación de caché por tenant
- Estadísticas de hit rate
- Fallback graceful si Redis no está disponible
"""

import hashlib
import json
import logging
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

class CacheService:
    """Servicio de caché para respuestas de IA"""
    
    def __init__(self):
        # 🚀 OPTIMIZACIÓN CRÍTICA: Habilitar Redis por defecto para mejor rendimiento
        self.enabled = os.getenv("REDIS_ENABLED", "true").lower() == "true"
        self.client = None
        
        if self.enabled:
            try:
                import redis
                self.client = redis.Redis(
                    host=os.getenv("REDIS_HOST", "localhost"),
                    port=int(os.getenv("REDIS_PORT", "6379")),
                    db=int(os.getenv("REDIS_DB", "0")),
                    password=os.getenv("REDIS_PASSWORD", None) if os.getenv("REDIS_PASSWORD") else None,
                    decode_responses=True,
                    socket_connect_timeout=1,  # Reducido para conexión más rápida
                    socket_timeout=1,          # Reducido para operaciones más rápidas
                    retry_on_timeout=True,     # Reintentar en timeout
                    health_check_interval=30   # Verificar salud cada 30 segundos
                )
                # Test connection
                self.client.ping()
                logger.info("✅ Redis conectado exitosamente - Caché habilitado para mejor rendimiento")
            except ImportError:
                logger.warning("⚠️ Redis no instalado, usando caché en memoria")
                self.enabled = False
                self._memory_cache = {}  # Fallback a caché en memoria
            except Exception as e:
                logger.warning(f"⚠️ Redis no disponible: {e}, usando caché en memoria")
                self.enabled = False
                self._memory_cache = {}  # Fallback a caché en memoria
        else:
            logger.info("ℹ️ Caché Redis deshabilitado, usando caché en memoria")
            self._memory_cache = {}  # Fallback a caché en memoria
    
    def _generate_cache_key(self, tenant_id: str, query: str, intent: str = None) -> str:
        """
        Genera una key única para el caché
        
        Args:
            tenant_id: ID del tenant
            query: Query del usuario
            intent: Intención clasificada (opcional)
            
        Returns:
            Key única para Redis
        """
        # Normalizar query (lowercase, trim, remover espacios extras)
        normalized_query = ' '.join(query.lower().strip().split())
        
        # Crear hash para queries largas (>100 chars)
        if len(normalized_query) > 100:
            query_hash = hashlib.md5(normalized_query.encode()).hexdigest()
            key_parts = [tenant_id, intent or "general", query_hash]
        else:
            # Para queries cortas, usar directamente
            key_parts = [tenant_id, intent or "general", normalized_query]
        
        return f"chat_response:{':'.join(key_parts)}"
    
    def get_cached_response(
        self, 
        tenant_id: str, 
        query: str, 
        intent: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene una respuesta del caché
        
        Args:
            tenant_id: ID del tenant
            query: Query del usuario
            intent: Intención clasificada
            
        Returns:
            Respuesta cacheada o None si no existe
        """
        if not self.enabled:
            return None
        
        try:
            key = self._generate_cache_key(tenant_id, query, intent)
            cached = self.client.get(key)
            
            if cached:
                logger.info(f"✅ Cache HIT para tenant {tenant_id} | intent={intent}")
                return json.loads(cached)
            
            logger.debug(f"❌ Cache MISS para tenant {tenant_id} | intent={intent}")
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo del caché: {e}")
            return None
    
    def cache_response(
        self,
        tenant_id: str,
        query: str,
        response: Dict[str, Any],
        intent: str = None,
        ttl: int = None
    ):
        """
        Guarda una respuesta en caché
        
        Args:
            tenant_id: ID del tenant
            query: Query del usuario
            response: Respuesta a cachear
            intent: Intención clasificada
            ttl: Time to live en segundos (opcional)
        """
        if not self.enabled:
            return
        
        try:
            key = self._generate_cache_key(tenant_id, query, intent)
            
            # TTL por tipo de intención
            if ttl is None:
                ttl = self._get_ttl_for_intent(intent)
            
            # No cachear si TTL es 0
            if ttl == 0:
                logger.debug(f"⏭️ No cacheando intent={intent} (TTL=0)")
                return
            
            self.client.setex(
                key,
                ttl,
                json.dumps(response, ensure_ascii=False)
            )
            
            logger.debug(f"💾 Respuesta cacheada para tenant {tenant_id} | intent={intent} | TTL={ttl}s")
            
        except Exception as e:
            logger.error(f"Error guardando en caché: {e}")
    
    def _get_ttl_for_intent(self, intent: str) -> int:
        """
        Determina el TTL según el tipo de intención
        
        Args:
            intent: Tipo de intención
            
        Returns:
            TTL en segundos
        """
        ttl_map = {
            # Información estática - cachear por más tiempo
            "conocer_candidato": 3600,          # 1 hora
            "saludo_apoyo": 1800,               # 30 min
            "colaboracion_voluntariado": 1800,  # 30 min
            
            # Información semi-estática
            "cita_campaña": 900,                # 15 min
            "solicitud_funcional": 600,         # 10 min
            
            # No cachear - requieren atención personalizada
            "quejas": 0,
            "malicioso": 0,
            "atencion_humano": 0,
            "atencion_equipo_interno": 0,
            "registration_response": 0,
            "actualizacion_datos": 0,
        }
        
        return ttl_map.get(intent, 600)  # Default: 10 min
    
    def invalidate_tenant_cache(self, tenant_id: str):
        """
        Invalida todo el caché de un tenant
        
        Args:
            tenant_id: ID del tenant
        """
        if not self.enabled:
            return
        
        try:
            pattern = f"chat_response:{tenant_id}:*"
            keys = list(self.client.scan_iter(match=pattern))
            
            if keys:
                self.client.delete(*keys)
                logger.info(f"🗑️ Cache invalidado para tenant {tenant_id} ({len(keys)} keys)")
            else:
                logger.debug(f"ℹ️ No hay cache para invalidar en tenant {tenant_id}")
                
        except Exception as e:
            logger.error(f"Error invalidando caché: {e}")
    
    def invalidate_intent_cache(self, tenant_id: str, intent: str):
        """
        Invalida el caché de un intent específico de un tenant
        
        Args:
            tenant_id: ID del tenant
            intent: Intención a invalidar
        """
        if not self.enabled:
            return
        
        try:
            pattern = f"chat_response:{tenant_id}:{intent}:*"
            keys = list(self.client.scan_iter(match=pattern))
            
            if keys:
                self.client.delete(*keys)
                logger.info(f"🗑️ Cache invalidado para tenant {tenant_id} | intent={intent} ({len(keys)} keys)")
                
        except Exception as e:
            logger.error(f"Error invalidando caché de intent: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del caché
        
        Returns:
            Diccionario con estadísticas
        """
        if not self.enabled:
            return {"enabled": False}
        
        try:
            info = self.client.info("stats")
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            total = hits + misses
            
            hit_rate = round((hits / total) * 100, 2) if total > 0 else 0.0
            
            return {
                "enabled": True,
                "hits": hits,
                "misses": misses,
                "total_requests": total,
                "hit_rate_percent": hit_rate
            }
        except Exception as e:
            logger.error(f"Error obteniendo stats: {e}")
            return {"enabled": True, "error": str(e)}
    
    def clear_all_cache(self):
        """Limpia todo el caché (usar con precaución)"""
        if not self.enabled:
            return
        
        try:
            pattern = "chat_response:*"
            keys = list(self.client.scan_iter(match=pattern))
            
            if keys:
                self.client.delete(*keys)
                logger.warning(f"🗑️ TODO el cache limpiado ({len(keys)} keys)")
                
        except Exception as e:
            logger.error(f"Error limpiando todo el caché: {e}")


# Instancia global
cache_service = CacheService()


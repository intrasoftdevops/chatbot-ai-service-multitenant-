"""
Configuración de caché para el servicio de IA multi-tenant
"""

import os
import redis
from typing import Optional

class CacheConfig:
    """Configuración de caché Redis para el servicio multi-tenant"""
    
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self.password = os.getenv("REDIS_PASSWORD")
        self._redis_client: Optional[redis.Redis] = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Inicializa el cliente de Redis"""
        try:
            self._redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Probar conexión
            self._redis_client.ping()
            print(f"✅ Redis conectado correctamente en {self.host}:{self.port}")
            
        except Exception as e:
            print(f"⚠️ Redis no disponible: {e}")
            self._redis_client = None
    
    @property
    def redis(self) -> Optional[redis.Redis]:
        """Obtiene el cliente de Redis"""
        return self._redis_client
    
    def is_available(self) -> bool:
        """Verifica si Redis está disponible"""
        return self._redis_client is not None
    
    def get_tenant_cache_key(self, tenant_id: str, key: str) -> str:
        """Genera una clave de caché para un tenant específico"""
        return f"tenant:{tenant_id}:{key}"
    
    def get_conversation_cache_key(self, tenant_id: str, session_id: str) -> str:
        """Genera una clave de caché para una conversación"""
        return f"tenant:{tenant_id}:conversation:{session_id}"
    
    def get_ai_cache_key(self, tenant_id: str, query_hash: str) -> str:
        """Genera una clave de caché para respuestas de IA"""
        return f"tenant:{tenant_id}:ai:{query_hash}"


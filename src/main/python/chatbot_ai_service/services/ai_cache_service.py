"""
Servicios de caché para IA
"""
import logging
import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from collections import OrderedDict

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """
    Entrada de caché
    """
    key: str
    value: Any
    timestamp: float
    ttl: float
    access_count: int = 0
    last_access: float = 0.0
    
    def is_expired(self) -> bool:
        """
        Verifica si la entrada ha expirado.
        
        Returns:
            True si ha expirado, False si no
        """
        return time.time() - self.timestamp > self.ttl
    
    def is_stale(self, max_age: float) -> bool:
        """
        Verifica si la entrada está obsoleta.
        
        Args:
            max_age: Edad máxima en segundos
            
        Returns:
            True si está obsoleta, False si no
        """
        return time.time() - self.timestamp > max_age
    
    def touch(self):
        """
        Actualiza el timestamp de último acceso.
        """
        self.last_access = time.time()
        self.access_count += 1

class AICacheService:
    """
    Servicio de caché para IA
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 3600.0):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.hit_count = 0
        self.miss_count = 0
        self.eviction_count = 0
        
        # Configuración de limpieza
        self.cleanup_interval = 300  # 5 minutos
        self.last_cleanup = time.time()
        
        logger.info(f"Servicio de caché inicializado con tamaño máximo {max_size} y TTL {default_ttl}s")
    
    def _generate_key(self, prefix: str, *args) -> str:
        """
        Genera una clave de caché única.
        
        Args:
            prefix: Prefijo de la clave
            *args: Argumentos para generar la clave
            
        Returns:
            Clave única generada
        """
        try:
            # Crear string de argumentos
            args_str = json.dumps(args, sort_keys=True, ensure_ascii=False)
            
            # Generar hash MD5
            hash_obj = hashlib.md5(args_str.encode('utf-8'))
            hash_hex = hash_obj.hexdigest()
            
            return f"{prefix}:{hash_hex}"
            
        except Exception as e:
            logger.error(f"Error generando clave de caché: {str(e)}")
            return f"{prefix}:{int(time.time())}"
    
    def _cleanup_expired(self):
        """
        Limpia entradas expiradas del caché.
        """
        try:
            current_time = time.time()
            
            # Solo limpiar si ha pasado el intervalo de limpieza
            if current_time - self.last_cleanup < self.cleanup_interval:
                return
            
            expired_keys = []
            for key, entry in self.cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
                self.eviction_count += 1
            
            self.last_cleanup = current_time
            
            if expired_keys:
                logger.debug(f"Limpiadas {len(expired_keys)} entradas expiradas del caché")
                
        except Exception as e:
            logger.error(f"Error limpiando caché: {str(e)}")
    
    def _evict_lru(self):
        """
        Evicta la entrada menos recientemente usada.
        """
        try:
            if not self.cache:
                return
            
            # Encontrar la entrada con menor last_access
            lru_key = min(self.cache.keys(), key=lambda k: self.cache[k].last_access)
            del self.cache[lru_key]
            self.eviction_count += 1
            
            logger.debug(f"Evictada entrada LRU: {lru_key}")
            
        except Exception as e:
            logger.error(f"Error evictando entrada LRU: {str(e)}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del caché.
        
        Args:
            key: Clave del caché
            
        Returns:
            Valor del caché o None si no existe
        """
        try:
            # Limpiar entradas expiradas
            self._cleanup_expired()
            
            if key not in self.cache:
                self.miss_count += 1
                return None
            
            entry = self.cache[key]
            
            # Verificar si ha expirado
            if entry.is_expired():
                del self.cache[key]
                self.miss_count += 1
                self.eviction_count += 1
                return None
            
            # Actualizar acceso
            entry.touch()
            
            # Mover al final (más reciente)
            self.cache.move_to_end(key)
            
            self.hit_count += 1
            return entry.value
            
        except Exception as e:
            logger.error(f"Error obteniendo del caché: {str(e)}")
            self.miss_count += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """
        Establece un valor en el caché.
        
        Args:
            key: Clave del caché
            value: Valor a almacenar
            ttl: Tiempo de vida en segundos (opcional)
            
        Returns:
            True si se almacenó correctamente, False si no
        """
        try:
            # Limpiar entradas expiradas
            self._cleanup_expired()
            
            # Usar TTL por defecto si no se especifica
            if ttl is None:
                ttl = self.default_ttl
            
            # Crear entrada de caché
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                ttl=ttl
            )
            
            # Verificar si necesitamos evictar
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()
            
            # Almacenar entrada
            self.cache[key] = entry
            
            # Mover al final (más reciente)
            self.cache.move_to_end(key)
            
            logger.debug(f"Valor almacenado en caché: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error estableciendo en caché: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Elimina una entrada del caché.
        
        Args:
            key: Clave del caché
            
        Returns:
            True si se eliminó correctamente, False si no
        """
        try:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Entrada eliminada del caché: {key}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error eliminando del caché: {str(e)}")
            return False
    
    def clear(self):
        """
        Limpia todo el caché.
        """
        try:
            self.cache.clear()
            self.hit_count = 0
            self.miss_count = 0
            self.eviction_count = 0
            logger.info("Caché limpiado completamente")
            
        except Exception as e:
            logger.error(f"Error limpiando caché: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del caché.
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            total_requests = self.hit_count + self.miss_count
            hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hit_count": self.hit_count,
                "miss_count": self.miss_count,
                "hit_rate": hit_rate,
                "eviction_count": self.eviction_count,
                "total_requests": total_requests
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del caché: {str(e)}")
            return {}
    
    def get_cache_entry(self, key: str) -> Optional[CacheEntry]:
        """
        Obtiene una entrada completa del caché.
        
        Args:
            key: Clave del caché
            
        Returns:
            Entrada del caché o None si no existe
        """
        try:
            if key in self.cache:
                entry = self.cache[key]
                if not entry.is_expired():
                    return entry
                else:
                    del self.cache[key]
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo entrada del caché: {str(e)}")
            return None
    
    def get_all_keys(self) -> List[str]:
        """
        Obtiene todas las claves del caché.
        
        Returns:
            Lista de claves
        """
        try:
            return list(self.cache.keys())
            
        except Exception as e:
            logger.error(f"Error obteniendo claves del caché: {str(e)}")
            return []
    
    def get_entries_by_prefix(self, prefix: str) -> List[CacheEntry]:
        """
        Obtiene todas las entradas que coinciden con un prefijo.
        
        Args:
            prefix: Prefijo a buscar
            
        Returns:
            Lista de entradas que coinciden
        """
        try:
            entries = []
            for key, entry in self.cache.items():
                if key.startswith(prefix) and not entry.is_expired():
                    entries.append(entry)
            return entries
            
        except Exception as e:
            logger.error(f"Error obteniendo entradas por prefijo: {str(e)}")
            return []
    
    def cleanup_stale_entries(self, max_age: float):
        """
        Limpia entradas obsoletas.
        
        Args:
            max_age: Edad máxima en segundos
        """
        try:
            stale_keys = []
            for key, entry in self.cache.items():
                if entry.is_stale(max_age):
                    stale_keys.append(key)
            
            for key in stale_keys:
                del self.cache[key]
                self.eviction_count += 1
            
            if stale_keys:
                logger.info(f"Limpiadas {len(stale_keys)} entradas obsoletas del caché")
                
        except Exception as e:
            logger.error(f"Error limpiando entradas obsoletas: {str(e)}")

# Instancias globales del servicio de caché
ai_cache_service = AICacheService()

def get_from_cache(key: str) -> Optional[Any]:
    """
    Función de conveniencia para obtener del caché.
    """
    return ai_cache_service.get(key)

def set_in_cache(key: str, value: Any, ttl: Optional[float] = None) -> bool:
    """
    Función de conveniencia para establecer en caché.
    """
    return ai_cache_service.set(key, value, ttl)

def delete_from_cache(key: str) -> bool:
    """
    Función de conveniencia para eliminar del caché.
    """
    return ai_cache_service.delete(key)

def clear_cache():
    """
    Función de conveniencia para limpiar el caché.
    """
    ai_cache_service.clear()

def get_cache_stats() -> Dict[str, Any]:
    """
    Función de conveniencia para obtener estadísticas del caché.
    """
    return ai_cache_service.get_stats()

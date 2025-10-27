"""
Servicio de Identidad del Tenant con persistencia Firestore

Gestiona la identidad y personalidad de cada candidato de forma persistente.
Los datos se mantienen entre reinicios del servicio.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from chatbot_ai_service.config.firebase_config import get_firebase_config
from chatbot_ai_service.models.tenant_models import TenantIdentity
from google.cloud import firestore

logger = logging.getLogger(__name__)


class TenantIdentityService:
    """Servicio para gestionar identidades de tenants con Firestore"""
    
    def __init__(self):
        firebase = get_firebase_config()
        self.db = firebase.get_firestore()
        self._cache = {}  # Cache en RAM para rápido acceso
        logger.info("✅ TenantIdentityService inicializado con Firestore")
    
    async def get_tenant_identity(self, tenant_id: str) -> Optional[TenantIdentity]:
        """
        Obtiene la identidad del tenant desde Firestore o cache
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            TenantIdentity o None si no existe
        """
        # Primero intentar cache en RAM
        if tenant_id in self._cache:
            logger.debug(f"✅ Identidad en cache para tenant {tenant_id}")
            return self._cache[tenant_id]
        
        # Si no está en cache, leer de Firestore
        try:
            doc_ref = self.db.collection('tenant_identities').document(tenant_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                identity = TenantIdentity.from_dict(data)
                
                # Guardar en cache
                self._cache[tenant_id] = identity
                
                logger.info(f"✅ Identidad cargada desde Firestore para tenant {tenant_id}: {identity.candidate_name}")
                return identity
            else:
                logger.warning(f"⚠️ No existe identidad para tenant {tenant_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error leyendo identidad desde Firestore para tenant {tenant_id}: {e}")
            return None
    
    async def save_tenant_identity(self, tenant_id: str, identity: TenantIdentity) -> bool:
        """
        Guarda la identidad del tenant en Firestore
        
        Args:
            tenant_id: ID del tenant
            identity: Objeto TenantIdentity
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            # Preparar datos con timestamps
            data = identity.to_dict()
            data['updated_at'] = firestore.SERVER_TIMESTAMP
            if 'created_at' not in data or not data['created_at']:
                data['created_at'] = firestore.SERVER_TIMESTAMP
            
            # Guardar en Firestore
            doc_ref = self.db.collection('tenant_identities').document(tenant_id)
            doc_ref.set(data, merge=False)
            
            # Actualizar cache
            self._cache[tenant_id] = identity
            
            logger.info(f"✅ Identidad guardada en Firestore para tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando identidad en Firestore para tenant {tenant_id}: {e}")
            return False
    
    async def update_tenant_identity(self, tenant_id: str, updates: Dict[str, Any]) -> bool:
        """
        Actualiza parcialmente la identidad del tenant
        
        Args:
            tenant_id: ID del tenant
            updates: Diccionario con campos a actualizar
            
        Returns:
            True si se actualizó exitosamente
        """
        try:
            # Agregar timestamp de actualización
            updates['updated_at'] = firestore.SERVER_TIMESTAMP
            
            # Actualizar en Firestore
            doc_ref = self.db.collection('tenant_identities').document(tenant_id)
            doc_ref.update(updates)
            
            # Invalidar cache para forzar recarga
            if tenant_id in self._cache:
                del self._cache[tenant_id]
            
            logger.info(f"✅ Identidad actualizada en Firestore para tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error actualizando identidad en Firestore para tenant {tenant_id}: {e}")
            return False
    
    async def delete_tenant_identity(self, tenant_id: str) -> bool:
        """
        Elimina la identidad del tenant
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            True si se eliminó exitosamente
        """
        try:
            # Eliminar de Firestore
            doc_ref = self.db.collection('tenant_identities').document(tenant_id)
            doc_ref.delete()
            
            # Eliminar de cache
            if tenant_id in self._cache:
                del self._cache[tenant_id]
            
            logger.info(f"✅ Identidad eliminada para tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error eliminando identidad para tenant {tenant_id}: {e}")
            return False
    
    async def list_all_tenant_identities(self) -> list[str]:
        """
        Lista todos los tenant_ids que tienen identidad
        
        Returns:
            Lista de tenant_ids
        """
        try:
            docs = self.db.collection('tenant_identities').stream()
            tenant_ids = [doc.id for doc in docs]
            
            logger.info(f"✅ Listados {len(tenant_ids)} tenant identities")
            return tenant_ids
            
        except Exception as e:
            logger.error(f"❌ Error listando identidades: {e}")
            return []
    
    def clear_cache(self):
        """Limpia el cache en RAM"""
        self._cache.clear()
        logger.info("✅ Cache de identidades limpiado")


# Instancia global del servicio
_tenant_identity_service_instance = None


def get_tenant_identity_service() -> TenantIdentityService:
    """
    Obtiene la instancia singleton del servicio
    
    Returns:
        TenantIdentityService
    """
    global _tenant_identity_service_instance
    if _tenant_identity_service_instance is None:
        _tenant_identity_service_instance = TenantIdentityService()
    return _tenant_identity_service_instance

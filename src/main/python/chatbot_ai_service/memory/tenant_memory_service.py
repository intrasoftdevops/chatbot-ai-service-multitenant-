"""
Servicio de Memoria del Tenant con persistencia Firestore

Gestiona la memoria y contexto aprendido de cada candidato de forma persistente.
Los datos se mantienen entre reinicios del servicio.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from chatbot_ai_service.config.firebase_config import get_firebase_config
from chatbot_ai_service.models.tenant_models import TenantMemory, ConversationSummary
from google.cloud import firestore

logger = logging.getLogger(__name__)


class TenantMemoryService:
    """Servicio para gestionar memoria de tenants con Firestore"""
    
    def __init__(self):
        firebase = get_firebase_config()
        self.db = firebase.get_firestore()
        self._cache = {}  # Cache en RAM para rápido acceso
        logger.info("✅ TenantMemoryService inicializado con Firestore")
    
    async def get_tenant_memory(self, tenant_id: str) -> Optional[TenantMemory]:
        """
        Obtiene la memoria del tenant desde Firestore o cache
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            TenantMemory o None si no existe
        """
        # Primero intentar cache en RAM
        if tenant_id in self._cache:
            logger.debug(f"✅ Memoria en cache para tenant {tenant_id}")
            return self._cache[tenant_id]
        
        # Si no está en cache, leer de Firestore
        try:
            doc_ref = self.db.collection('tenant_memory').document(tenant_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                memory = TenantMemory.from_dict(data)
                
                # Guardar en cache
                self._cache[tenant_id] = memory
                
                logger.info(f"✅ Memoria cargada desde Firestore para tenant {tenant_id}")
                return memory
            else:
                logger.warning(f"⚠️ No existe memoria para tenant {tenant_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error leyendo memoria desde Firestore para tenant {tenant_id}: {e}")
            return None
    
    async def save_tenant_memory(self, tenant_id: str, memory: TenantMemory) -> bool:
        """
        Guarda la memoria del tenant en Firestore
        
        Args:
            tenant_id: ID del tenant
            memory: Objeto TenantMemory
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            # Preparar datos con timestamps
            data = memory.to_dict()
            data['last_updated'] = firestore.SERVER_TIMESTAMP
            if 'created_at' not in data or not data['created_at']:
                data['created_at'] = firestore.SERVER_TIMESTAMP
            
            # Guardar en Firestore
            doc_ref = self.db.collection('tenant_memory').document(tenant_id)
            doc_ref.set(data, merge=False)
            
            # Actualizar cache
            self._cache[tenant_id] = memory
            
            logger.info(f"✅ Memoria guardada en Firestore para tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando memoria en Firestore para tenant {tenant_id}: {e}")
            return False
    
    async def update_tenant_memory_incremental(self, tenant_id: str, updates: Dict[str, Any]) -> bool:
        """
        Actualiza la memoria del tenant de forma incremental
        
        Args:
            tenant_id: ID del tenant
            updates: Diccionario con campos a actualizar
            
        Returns:
            True si se actualizó exitosamente
        """
        try:
            # Agregar timestamp de actualización
            updates['last_updated'] = firestore.SERVER_TIMESTAMP
            
            # Actualizar en Firestore
            doc_ref = self.db.collection('tenant_memory').document(tenant_id)
            doc_ref.update(updates)
            
            # Invalidar cache para forzar recarga
            if tenant_id in self._cache:
                del self._cache[tenant_id]
            
            logger.info(f"✅ Memoria actualizada incrementalmente para tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error actualizando memoria para tenant {tenant_id}: {e}")
            return False
    
    async def add_conversation_summary(self, tenant_id: str, summary: ConversationSummary) -> bool:
        """
        Agrega un resumen de conversación a la memoria
        
        Args:
            tenant_id: ID del tenant
            summary: Resumen de conversación
            
        Returns:
            True si se agregó exitosamente
        """
        try:
            # Obtener memoria actual
            memory = await self.get_tenant_memory(tenant_id)
            
            # Si no existe memoria, crear nueva
            if not memory:
                memory = TenantMemory(
                    tenant_id=tenant_id,
                    created_at=datetime.now()
                )
            
            # Agregar resumen
            memory.recent_conversations.append(summary)
            
            # Mantener solo los últimos 50 resúmenes
            if len(memory.recent_conversations) > 50:
                memory.recent_conversations = memory.recent_conversations[-50:]
            
            # Actualizar estadísticas
            memory.total_conversations += 1
            memory.last_updated = datetime.now()
            
            # Guardar
            return await self.save_tenant_memory(tenant_id, memory)
            
        except Exception as e:
            logger.error(f"❌ Error agregando resumen de conversación para tenant {tenant_id}: {e}")
            return False
    
    async def add_common_question(self, tenant_id: str, question: str) -> bool:
        """
        Agrega una pregunta común a la memoria
        
        Args:
            tenant_id: ID del tenant
            question: Pregunta común
            
        Returns:
            True si se agregó exitosamente
        """
        try:
            # Obtener memoria actual
            memory = await self.get_tenant_memory(tenant_id)
            
            # Si no existe memoria, crear nueva
            if not memory:
                memory = TenantMemory(tenant_id=tenant_id)
            
            # Agregar pregunta (sin duplicados)
            if question not in memory.common_questions:
                memory.common_questions.append(question)
                
                # Mantener solo las últimas 20 preguntas
                if len(memory.common_questions) > 20:
                    memory.common_questions = memory.common_questions[-20:]
                
                # Guardar
                return await self.save_tenant_memory(tenant_id, memory)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error agregando pregunta común para tenant {tenant_id}: {e}")
            return False
    
    async def add_popular_topic(self, tenant_id: str, topic: str) -> bool:
        """
        Agrega un tema popular a la memoria
        
        Args:
            tenant_id: ID del tenant
            topic: Tema popular
            
        Returns:
            True si se agregó exitosamente
        """
        try:
            # Obtener memoria actual
            memory = await self.get_tenant_memory(tenant_id)
            
            # Si no existe memoria, crear nueva
            if not memory:
                memory = TenantMemory(tenant_id=tenant_id)
            
            # Agregar tema (sin duplicados)
            if topic not in memory.popular_topics:
                memory.popular_topics.append(topic)
                
                # Mantener solo los últimos 15 temas
                if len(memory.popular_topics) > 15:
                    memory.popular_topics = memory.popular_topics[-15:]
                
                # Guardar
                return await self.save_tenant_memory(tenant_id, memory)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error agregando tema popular para tenant {tenant_id}: {e}")
            return False
    
    def clear_cache(self):
        """Limpia el cache en RAM"""
        self._cache.clear()
        logger.info("✅ Cache de memoria limpiado")


# Instancia global del servicio
_tenant_memory_service_instance = None


def get_tenant_memory_service() -> TenantMemoryService:
    """
    Obtiene la instancia singleton del servicio
    
    Returns:
        TenantMemoryService
    """
    global _tenant_memory_service_instance
    if _tenant_memory_service_instance is None:
        _tenant_memory_service_instance = TenantMemoryService()
    return _tenant_memory_service_instance

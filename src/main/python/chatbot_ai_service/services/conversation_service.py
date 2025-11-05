"""
Servicio de gestión de conversaciones para el servicio de IA multi-tenant
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from google.cloud import firestore

from chatbot_ai_service.models.chat_models import (
    Conversation, Message, MessageRole, ConversationPlatform, UserState
)
from chatbot_ai_service.config.firebase_config import FirebaseConfig
from chatbot_ai_service.services.tenant_service import TenantService

logger = logging.getLogger(__name__)

class ConversationService:
    """Servicio para gestión de conversaciones multi-tenant"""
    
    def __init__(self, firebase_config: FirebaseConfig, tenant_service: TenantService):
        self.firestore = firebase_config.firestore
        self.tenant_service = tenant_service
        self.conversations_collection = firebase_config.get_conversations_collection()
    
    async def get_or_create_conversation(
        self, 
        tenant_id: str, 
        session_id: str, 
        phone: str, 
        platform: ConversationPlatform = ConversationPlatform.WHATSAPP
    ) -> Conversation:
        """
        Obtiene o crea una conversación para un tenant específico
        """
        try:
            # Verificar que el tenant existe
            if not await self.tenant_service.is_tenant_active(tenant_id):
                raise ValueError(f"Tenant {tenant_id} no está activo")
            
            # Buscar conversación existente
            existing_conversation = await self._find_conversation_by_session(tenant_id, session_id)
            
            if existing_conversation:
                logger.info(f"Conversación encontrada para tenant {tenant_id}, sesión {session_id}")
                return existing_conversation
            
            # Crear nueva conversación
            conversation_id = str(uuid.uuid4())
            
            conversation = Conversation(
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                session_id=session_id,
                phone=phone,
                platform=platform,
                messages=[],
                current_state=UserState.NEW,
                context={},
                created_at=datetime.now(),
                updated_at=datetime.now(),
                last_activity=datetime.now()
            )
            
            # Guardar en Firestore
            await self._save_conversation(conversation)
            
            logger.info(f"Nueva conversación creada para tenant {tenant_id}, sesión {session_id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Error al obtener/crear conversación para tenant {tenant_id}: {e}")
            raise
    
    async def add_message_to_conversation(
        self, 
        tenant_id: str, 
        session_id: str, 
        role: MessageRole, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Agrega un mensaje a una conversación existente
        """
        try:
            # Obtener conversación
            conversation = await self._find_conversation_by_session(tenant_id, session_id)
            if not conversation:
                logger.warning(f"Conversación no encontrada para agregar mensaje: tenant {tenant_id}, sesión {session_id}")
                return False
            
            # Crear mensaje
            message = Message(
                role=role,
                content=content,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
            # Agregar mensaje a la conversación
            conversation.messages.append(message)
            conversation.updated_at = datetime.now()
            conversation.last_activity = datetime.now()
            
            # Guardar cambios
            await self._save_conversation(conversation)
            
            logger.info(f"Mensaje agregado a conversación para tenant {tenant_id}, sesión {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error al agregar mensaje a conversación para tenant {tenant_id}: {e}")
            return False
    
    async def update_conversation_state(
        self, 
        tenant_id: str, 
        session_id: str, 
        new_state: UserState,
        context_updates: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Actualiza el estado de una conversación
        """
        try:
            # Obtener conversación
            conversation = await self._find_conversation_by_session(tenant_id, session_id)
            if not conversation:
                logger.warning(f"Conversación no encontrada para actualizar estado: tenant {tenant_id}, sesión {session_id}")
                return False
            
            # Actualizar estado y contexto
            conversation.current_state = new_state
            conversation.updated_at = datetime.now()
            
            if context_updates:
                conversation.context.update(context_updates)
            
            # Guardar cambios
            await self._save_conversation(conversation)
            
            logger.info(f"Estado de conversación actualizado para tenant {tenant_id}, sesión {session_id}: {new_state}")
            return True
            
        except Exception as e:
            logger.error(f"Error al actualizar estado de conversación para tenant {tenant_id}: {e}")
            return False
    
    async def get_conversation_history(
        self, 
        tenant_id: str, 
        session_id: str, 
        limit: int = 10
    ) -> List[Message]:
        """
        Obtiene el historial de mensajes de una conversación
        """
        try:
            conversation = await self._find_conversation_by_session(tenant_id, session_id)
            if not conversation:
                return []
            
            # Retornar últimos N mensajes
            messages = conversation.messages[-limit:] if len(conversation.messages) > limit else conversation.messages
            return messages
            
        except Exception as e:
            logger.error(f"Error al obtener historial de conversación para tenant {tenant_id}: {e}")
            return []
    
    async def get_active_conversations_by_tenant(self, tenant_id: str) -> List[Conversation]:
        """
        Obtiene todas las conversaciones activas de un tenant
        """
        try:
            # Verificar que el tenant existe
            if not await self.tenant_service.is_tenant_active(tenant_id):
                return []
            
            # Consultar conversaciones activas (últimas 24 horas)
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            conversations_ref = self.firestore.collection(self.conversations_collection)
            query = conversations_ref.where("tenant_id", "==", tenant_id).where("last_activity", ">=", cutoff_time)
            
            docs = query.get()
            conversations = []
            
            for doc in docs:
                conversation_data = doc.to_dict()
                conversation = Conversation(**conversation_data)
                conversations.append(conversation)
            
            logger.info(f"Encontradas {len(conversations)} conversaciones activas para tenant {tenant_id}")
            return conversations
            
        except Exception as e:
            logger.error(f"Error al obtener conversaciones activas para tenant {tenant_id}: {e}")
            return []
    
    async def get_conversations_by_phone(self, tenant_id: str, phone: str) -> List[Conversation]:
        """
        Obtiene todas las conversaciones de un número de teléfono para un tenant
        """
        try:
            conversations_ref = self.firestore.collection(self.conversations_collection)
            query = conversations_ref.where("tenant_id", "==", tenant_id).where("phone", "==", phone)
            
            docs = query.get()
            conversations = []
            
            for doc in docs:
                conversation_data = doc.to_dict()
                conversation = Conversation(**conversation_data)
                conversations.append(conversation)
            
            logger.info(f"Encontradas {len(conversations)} conversaciones para teléfono {phone} en tenant {tenant_id}")
            return conversations
            
        except Exception as e:
            logger.error(f"Error al obtener conversaciones por teléfono para tenant {tenant_id}: {e}")
            return []
    
    async def get_conversation_stats(self, tenant_id: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de conversaciones para un tenant
        """
        try:
            conversations_ref = self.firestore.collection(self.conversations_collection)
            query = conversations_ref.where("tenant_id", "==", tenant_id)
            
            docs = query.get()
            
            total_conversations = len(docs)
            total_messages = 0
            active_conversations = 0
            state_counts = {}
            
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            for doc in docs:
                conversation_data = doc.to_dict()
                
                # Contar mensajes
                messages = conversation_data.get("messages", [])
                total_messages += len(messages)
                
                # Verificar si está activa
                last_activity = conversation_data.get("last_activity")
                if last_activity and last_activity >= cutoff_time:
                    active_conversations += 1
                
                # Contar estados
                state = conversation_data.get("current_state", "NEW")
                state_counts[state] = state_counts.get(state, 0) + 1
            
            return {
                "tenant_id": tenant_id,
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "active_conversations": active_conversations,
                "average_messages_per_conversation": total_messages / total_conversations if total_conversations > 0 else 0,
                "state_distribution": state_counts,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error al obtener estadísticas de conversaciones para tenant {tenant_id}: {e}")
            return {"error": str(e)}
    
    async def _find_conversation_by_session(self, tenant_id: str, session_id: str) -> Optional[Conversation]:
        """Busca una conversación por session_id y tenant_id"""
        try:
            conversations_ref = self.firestore.collection(self.conversations_collection)
            query = conversations_ref.where("tenant_id", "==", tenant_id).where("session_id", "==", session_id)
            
            docs = query.limit(1).get()
            
            if not docs:
                return None
            
            conversation_data = docs[0].to_dict()
            return Conversation(**conversation_data)
            
        except Exception as e:
            logger.error(f"Error al buscar conversación por sesión: {e}")
            return None
    
    async def _save_conversation(self, conversation: Conversation) -> bool:
        """Guarda una conversación en Firestore"""
        try:
            doc_ref = self.firestore.collection(self.conversations_collection).document(conversation.conversation_id)
            doc_ref.set(conversation.dict())
            return True
            
        except Exception as e:
            logger.error(f"Error al guardar conversación: {e}")
            return False


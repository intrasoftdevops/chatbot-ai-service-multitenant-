"""
Servicio para gestión de sesiones y contexto persistente

Mantiene el contexto de los documentos cargados y el historial de conversación
para proporcionar respuestas más fluidas y contextuales.
"""
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

@dataclass
class Message:
    """Representa un mensaje en la conversación"""
    timestamp: float
    role: str  # 'user' o 'assistant'
    content: str
    message_type: str = "text"  # 'text', 'system', 'context'
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class SessionContext:
    """Representa el contexto de una sesión de chat"""
    session_id: str
    tenant_id: str
    user_id: Optional[str]
    messages: List[Message]
    document_context: str
    last_activity: float
    created_at: float
    user_context: Dict[str, Any]
    
    def __post_init__(self):
        if self.user_context is None:
            self.user_context = {}

class SessionContextService:
    """Servicio para gestionar sesiones y contexto persistente"""
    
    def __init__(self):
        self._sessions: Dict[str, SessionContext] = {}
        self._session_ttl = 1200  # 20 minutos en segundos
        self._session_warning_ttl = 900  # 15 minutos para enviar advertencia
        self._max_messages_per_session = 50
        self._max_context_length = 4000  # caracteres
        self._warning_sent: Dict[str, bool] = {}  # Para evitar enviar múltiples advertencias
    
    def create_session(self, session_id: str, tenant_id: str, user_id: Optional[str] = None, 
                      user_context: Dict[str, Any] = None) -> SessionContext:
        """Crea una nueva sesión de chat"""
        current_time = time.time()
        
        session = SessionContext(
            session_id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
            messages=[],
            document_context="",
            last_activity=current_time,
            created_at=current_time,
            user_context=user_context or {}
        )
        
        self._sessions[session_id] = session
        logger.info(f"Sesión creada: {session_id} para tenant {tenant_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Obtiene una sesión existente"""
        self._cleanup_expired_sessions()
        return self._sessions.get(session_id)
    
    def add_message(self, session_id: str, role: str, content: str, 
                   message_type: str = "text", metadata: Dict[str, Any] = None) -> bool:
        """Agrega un mensaje a la sesión"""
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"No se encontró sesión: {session_id}")
            return False
        
        message = Message(
            timestamp=time.time(),
            role=role,
            content=content,
            message_type=message_type,
            metadata=metadata or {}
        )
        
        session.messages.append(message)
        session.last_activity = time.time()
        
        # Si es un mensaje del usuario, resetear la advertencia de timeout
        if role == "user":
            self.reset_session_warning(session_id)
        
        # Limitar número de mensajes
        if len(session.messages) > self._max_messages_per_session:
            session.messages = session.messages[-self._max_messages_per_session:]
        
        logger.debug(f"Mensaje agregado a sesión {session_id}: {role} - {len(content)} caracteres")
        return True
    
    def update_document_context(self, session_id: str, document_context: str) -> bool:
        """Actualiza el contexto de documentos para la sesión"""
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"No se encontró sesión: {session_id}")
            return False
        
        # Limitar longitud del contexto
        if len(document_context) > self._max_context_length:
            document_context = document_context[:self._max_context_length] + "..."
        
        session.document_context = document_context
        session.last_activity = time.time()
        
        logger.info(f"Contexto de documentos actualizado para sesión {session_id}: {len(document_context)} caracteres")
        return True
    
    def update_user_context(self, session_id: str, user_context: Dict[str, Any]) -> bool:
        """Actualiza el contexto del usuario para la sesión"""
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"No se encontró sesión: {session_id}")
            return False
        
        session.user_context.update(user_context)
        session.last_activity = time.time()
        
        logger.debug(f"Contexto de usuario actualizado para sesión {session_id}")
        return True
    
    def get_conversation_history(self, session_id: str, max_messages: int = 10) -> List[Message]:
        """Obtiene el historial de conversación de la sesión"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        # Retornar los últimos mensajes
        return session.messages[-max_messages:] if session.messages else []
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Obtiene un resumen de la sesión"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        return {
            "session_id": session.session_id,
            "tenant_id": session.tenant_id,
            "user_id": session.user_id,
            "message_count": len(session.messages),
            "has_document_context": bool(session.document_context),
            "document_context_length": len(session.document_context),
            "last_activity": datetime.fromtimestamp(session.last_activity).isoformat(),
            "created_at": datetime.fromtimestamp(session.created_at).isoformat(),
            "user_context": session.user_context
        }
    
    def build_context_for_ai(self, session_id: str) -> str:
        """Construye el contexto completo para la IA"""
        session = self.get_session(session_id)
        if not session:
            return ""
        
        context_parts = []
        
        # 1. Contexto de documentos
        if session.document_context:
            context_parts.append("=== INFORMACIÓN ESPECÍFICA DE LA CAMPAÑA ===")
            context_parts.append(session.document_context)
            context_parts.append("")
        
        # 2. Historial de conversación
        recent_messages = self.get_conversation_history(session_id, max_messages=5)
        if recent_messages:
            context_parts.append("=== HISTORIAL DE CONVERSACIÓN ===")
            for msg in recent_messages:
                if msg.role == "user":
                    context_parts.append(f"Usuario: {msg.content}")
                elif msg.role == "assistant":
                    context_parts.append(f"Asistente: {msg.content}")
            context_parts.append("")
        
        # 3. Contexto del usuario
        if session.user_context:
            context_parts.append("=== INFORMACIÓN DEL USUARIO ===")
            for key, value in session.user_context.items():
                if value:  # Solo incluir valores no vacíos
                    context_parts.append(f"{key}: {value}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def clear_session(self, session_id: str) -> bool:
        """Limpia una sesión específica"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Sesión limpiada: {session_id}")
            return True
        return False
    
    def clear_tenant_sessions(self, tenant_id: str) -> int:
        """Limpia todas las sesiones de un tenant"""
        sessions_to_remove = [
            session_id for session_id, session in self._sessions.items()
            if session.tenant_id == tenant_id
        ]
        
        for session_id in sessions_to_remove:
            del self._sessions[session_id]
        
        logger.info(f"Sesiones limpiadas para tenant {tenant_id}: {len(sessions_to_remove)}")
        return len(sessions_to_remove)
    
    def clear_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """Limpia todas las sesiones de un usuario específico"""
        sessions_to_remove = [
            session_id for session_id, session in self._sessions.items()
            if session.tenant_id == tenant_id and session.user_id == user_id
        ]
        
        for session_id in sessions_to_remove:
            del self._sessions[session_id]
            # También limpiar la advertencia si existe
            self._warning_sent.pop(session_id, None)
        
        if sessions_to_remove:
            logger.info(f"✅ Sesiones limpiadas para tenant {tenant_id} user {user_id}: {len(sessions_to_remove)}")
        else:
            logger.debug(f"No se encontraron sesiones para limpiar: tenant {tenant_id} user {user_id}")
        
        return len(sessions_to_remove)
    
    def _cleanup_expired_sessions(self):
        """Limpia sesiones expiradas"""
        current_time = time.time()
        expired_sessions = [
            session_id for session_id, session in self._sessions.items()
            if current_time - session.last_activity > self._session_ttl
        ]
        
        for session_id in expired_sessions:
            del self._sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Sesiones expiradas limpiadas: {len(expired_sessions)}")
    
    def get_active_sessions(self, tenant_id: str = None) -> List[Dict[str, Any]]:
        """Obtiene sesiones activas"""
        self._cleanup_expired_sessions()
        
        sessions = []
        for session in self._sessions.values():
            if tenant_id is None or session.tenant_id == tenant_id:
                sessions.append(self.get_session_summary(session.session_id))
        
        return sessions
    
    def get_session_stats(self, tenant_id: str = None) -> Dict[str, Any]:
        """Obtiene estadísticas de sesiones"""
        active_sessions = self.get_active_sessions(tenant_id)
        
        total_messages = sum(session["message_count"] for session in active_sessions)
        sessions_with_context = sum(1 for session in active_sessions if session["has_document_context"])
        
        return {
            "total_sessions": len(active_sessions),
            "total_messages": total_messages,
            "sessions_with_context": sessions_with_context,
            "average_messages_per_session": total_messages / len(active_sessions) if active_sessions else 0,
            "tenant_id": tenant_id
        }
    
    def check_session_timeout(self, session_id: str) -> Dict[str, Any]:
        """Verifica si una sesión necesita advertencia o cierre por timeout"""
        session = self.get_session(session_id)
        if not session:
            return {"status": "not_found", "action": None}
        
        current_time = time.time()
        time_since_activity = current_time - session.last_activity
        
        # Si han pasado más de 20 minutos, cerrar sesión
        if time_since_activity > self._session_ttl:
            self.clear_session(session_id)
            return {
                "status": "expired", 
                "action": "close_session",
                "message": "Tu sesión ha expirado por inactividad. Para continuar nuestra conversación, envía un nuevo mensaje."
            }
        
        # Si han pasado más de 15 minutos, enviar advertencia
        elif time_since_activity > self._session_warning_ttl:
            if not self._warning_sent.get(session_id, False):
                self._warning_sent[session_id] = True
                return {
                    "status": "warning", 
                    "action": "send_warning",
                    "message": "Tu sesión se cerrará en 5 minutos por inactividad. Si quieres continuar nuestra conversación, envía un mensaje ahora."
                }
        
        return {"status": "active", "action": None}
    
    def reset_session_warning(self, session_id: str):
        """Resetea la advertencia de sesión cuando el usuario envía un mensaje"""
        self._warning_sent[session_id] = False
    
    def get_session_timeout_info(self, session_id: str) -> Dict[str, Any]:
        """Obtiene información sobre el timeout de la sesión"""
        session = self.get_session(session_id)
        if not session:
            return {"time_remaining": 0, "status": "not_found"}
        
        current_time = time.time()
        time_since_activity = current_time - session.last_activity
        time_remaining = max(0, self._session_ttl - time_since_activity)
        
        return {
            "time_remaining": time_remaining,
            "time_remaining_minutes": int(time_remaining / 60),
            "status": "active" if time_remaining > 0 else "expired",
            "last_activity": session.last_activity,
            "session_created": session.created_at
        }


# Instancia global
session_context_service = SessionContextService()

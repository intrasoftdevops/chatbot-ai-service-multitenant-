"""
Modelos de datos para Tenants

Define los modelos de datos para la identidad, memoria y configuración
de cada tenant (candidato político).
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TenantStatus(str, Enum):
    """Estado del tenant"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


@dataclass
class TenantIdentity:
    """
    Identidad del tenant (candidato político)
    Almacena información permanente sobre quién es el candidato
    """
    tenant_id: str
    candidate_name: str
    campaign_name: str
    contact_name: str  # Nombre para guardar en WhatsApp
    
    # Personalidad y estilo
    personality_traits: List[str] = field(default_factory=list)
    communication_style: str = "professional"  # professional, friendly, formal, casual
    tone: str = "neutral"  # neutral, enthusiastic, calm, assertive
    
    # Información del candidato
    bio: Optional[str] = None
    position: Optional[str] = None  # Cargo que busca
    party: Optional[str] = None
    
    # Configuración de respuestas
    greeting_style: str = "warm"  # warm, formal, casual
    goodbye_style: str = "friendly"  # friendly, formal, enthusiastic
    
    # Preferencias de contenido
    preferred_topics: List[str] = field(default_factory=list)
    key_proposals: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario"""
        # Helper para convertir datetime a ISO format o retornar string si ya es string
        def to_iso_or_str(dt):
            if dt is None:
                return None
            elif isinstance(dt, str):
                return dt
            elif hasattr(dt, 'isoformat'):
                return dt.isoformat()
            else:
                return str(dt)
        
        return {
            "tenant_id": self.tenant_id,
            "candidate_name": self.candidate_name,
            "campaign_name": self.campaign_name,
            "contact_name": self.contact_name,
            "personality_traits": self.personality_traits,
            "communication_style": self.communication_style,
            "tone": self.tone,
            "bio": self.bio,
            "position": self.position,
            "party": self.party,
            "greeting_style": self.greeting_style,
            "goodbye_style": self.goodbye_style,
            "preferred_topics": self.preferred_topics,
            "key_proposals": self.key_proposals,
            "created_at": to_iso_or_str(self.created_at),
            "updated_at": to_iso_or_str(self.updated_at)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TenantIdentity":
        """Crea el modelo desde un diccionario"""
        return cls(
            tenant_id=data.get("tenant_id"),
            candidate_name=data.get("candidate_name"),
            campaign_name=data.get("campaign_name"),
            contact_name=data.get("contact_name", data.get("candidate_name")),
            personality_traits=data.get("personality_traits", []),
            communication_style=data.get("communication_style", "professional"),
            tone=data.get("tone", "neutral"),
            bio=data.get("bio"),
            position=data.get("position"),
            party=data.get("party"),
            greeting_style=data.get("greeting_style", "warm"),
            goodbye_style=data.get("goodbye_style", "friendly"),
            preferred_topics=data.get("preferred_topics", []),
            key_proposals=data.get("key_proposals", [])
        )


@dataclass
class ConversationSummary:
    """Resumen de una conversación"""
    conversation_id: str
    user_phone: str
    topics: List[str] = field(default_factory=list)
    key_points: List[str] = field(default_factory=list)
    sentiment: str = "neutral"  # positive, neutral, negative
    needs_attention: bool = False
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario"""
        # Helper para convertir datetime a ISO format o retornar string si ya es string
        def to_iso_or_str(dt):
            if dt is None:
                return None
            elif isinstance(dt, str):
                return dt
            elif hasattr(dt, 'isoformat'):
                return dt.isoformat()
            else:
                return str(dt)
        
        return {
            "conversation_id": self.conversation_id,
            "user_phone": self.user_phone,
            "topics": self.topics,
            "key_points": self.key_points,
            "sentiment": self.sentiment,
            "needs_attention": self.needs_attention,
            "timestamp": to_iso_or_str(self.timestamp)
        }


@dataclass
class TenantMemory:
    """
    Memoria persistente del tenant
    Almacena información aprendida sobre interacciones y preferencias
    """
    tenant_id: str
    
    # Resúmenes de conversaciones
    recent_conversations: List[ConversationSummary] = field(default_factory=list)
    
    # Hechos clave aprendidos
    key_facts: Dict[str, Any] = field(default_factory=dict)
    
    # Preferencias aprendidas
    preferences_learned: Dict[str, Any] = field(default_factory=dict)
    
    # Frases comunes identificadas
    common_questions: List[str] = field(default_factory=list)
    
    # Temas más discutidos
    popular_topics: List[str] = field(default_factory=list)
    
    # Estadísticas
    total_conversations: int = 0
    total_messages: int = 0
    average_sentiment: float = 0.0
    
    # Metadata
    last_updated: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario"""
        # Helper para convertir datetime a ISO format o retornar string si ya es string
        def to_iso_or_str(dt):
            if dt is None:
                return None
            elif isinstance(dt, str):
                return dt
            elif hasattr(dt, 'isoformat'):
                return dt.isoformat()
            else:
                return str(dt)
        
        return {
            "tenant_id": self.tenant_id,
            "recent_conversations": [c.to_dict() for c in self.recent_conversations],
            "key_facts": self.key_facts,
            "preferences_learned": self.preferences_learned,
            "common_questions": self.common_questions,
            "popular_topics": self.popular_topics,
            "total_conversations": self.total_conversations,
            "total_messages": self.total_messages,
            "average_sentiment": self.average_sentiment,
            "last_updated": to_iso_or_str(self.last_updated),
            "created_at": to_iso_or_str(self.created_at)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TenantMemory":
        """Crea el modelo desde un diccionario"""
        conversations = [
            ConversationSummary(**c) if isinstance(c, dict) else c 
            for c in data.get("recent_conversations", [])
        ]
        
        return cls(
            tenant_id=data.get("tenant_id"),
            recent_conversations=conversations,
            key_facts=data.get("key_facts", {}),
            preferences_learned=data.get("preferences_learned", {}),
            common_questions=data.get("common_questions", []),
            popular_topics=data.get("popular_topics", []),
            total_conversations=data.get("total_conversations", 0),
            total_messages=data.get("total_messages", 0),
            average_sentiment=data.get("average_sentiment", 0.0)
        )


@dataclass
class TenantKnowledgeGraph:
    """
    Grafo de conocimiento del tenant
    Relaciones entre entidades y conceptos importantes
    """
    tenant_id: str
    
    # Entidades principales
    entities: List[Dict[str, Any]] = field(default_factory=list)
    
    # Relaciones entre entidades
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    
    # Conceptos importantes
    key_concepts: List[str] = field(default_factory=list)
    
    # Metadata
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario"""
        # Helper para convertir datetime a ISO format o retornar string si ya es string
        def to_iso_or_str(dt):
            if dt is None:
                return None
            elif isinstance(dt, str):
                return dt
            elif hasattr(dt, 'isoformat'):
                return dt.isoformat()
            else:
                return str(dt)
        
        return {
            "tenant_id": self.tenant_id,
            "entities": self.entities,
            "relationships": self.relationships,
            "key_concepts": self.key_concepts,
            "last_updated": to_iso_or_str(self.last_updated)
        }

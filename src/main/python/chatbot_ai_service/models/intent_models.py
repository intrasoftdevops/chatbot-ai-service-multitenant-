from pydantic import BaseModel
from typing import Dict, List, Optional

class ChatRequest(BaseModel):
    tenant_id: Optional[str] = None  # Se asigna desde la URL
    query: str  # Cambiar de 'message' a 'query' para consistencia
    user_context: dict = {}
    tenant_config: Optional[dict] = None  # Configuración del tenant (links, etc.)

class ChatResponse(BaseModel):
    tenant_id: str
    response: str
    intent: str = "unknown"
    action_taken: str = "none"
    confidence: float = 0.0

class IntentClassificationRequest(BaseModel):
    tenant_id: str
    message: str
    user_context: dict = {}

class IntentClassificationResponse(BaseModel):
    tenant_id: str
    intent: str
    confidence: float
    action_taken: str
    metadata: dict = {}

class ValidationRequest(BaseModel):
    query: str
    tenant_id: Optional[str] = None

class ValidationResponse(BaseModel):
    result: str  # "VALID" or "INVALID"
    reason: Optional[str] = None

class ReferralDetectionRequest(BaseModel):
    query: str
    tenant_id: Optional[str] = None

class ReferralDetectionResponse(BaseModel):
    referral_code: Optional[str] = None
    referred_by_phone: Optional[str] = None
    confidence: float = 0.0
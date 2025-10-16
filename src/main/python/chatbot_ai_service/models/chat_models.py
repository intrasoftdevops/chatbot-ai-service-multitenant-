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
    message: str
    user_context: dict = {}
    tenant_id: Optional[str] = None  # Opcional porque viene en la URL

class IntentClassificationResponse(BaseModel):
    tenant_id: str
    intent: str
    confidence: float
    action_taken: str
    metadata: dict = {}

class ValidationRequest(BaseModel):
    message: str  # Cambiado de "query" a "message" para coincidir con Java
    data_type: str  # Tipo de dato a validar (nombre, apellido, ciudad, etc.)
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


class SimplePromptRequest(BaseModel):
    tenant_id: Optional[str] = None  # Se asigna desde la URL
    prompt: str
    use_documentation: bool = True  # Si debe cargar documentación del bucket
    user_context: Optional[dict] = None  # NUEVO: contexto opcional con historial
    
class SimplePromptResponse(BaseModel):
    tenant_id: str
    response: str
    processing_time: float = 0.0

class ClassificationRequest(BaseModel):
    tenant_id: Optional[str] = None  # Se asigna desde la URL
    message: str
    user_context: Optional[dict] = {}
    session_id: Optional[str] = None

class ClassificationResponse(BaseModel):
    tenant_id: str
    intent: str
    confidence: float
    original_message: str  # Campo requerido por el servicio Java
    suggested_response: Optional[str] = None
    metadata: dict = {}

class DataExtractionRequest(BaseModel):
    tenant_id: Optional[str] = None  # Se asigna desde la URL
    message: str
    extraction_type: str  # 'full' o campo específico como 'name', 'city', etc.
    user_context: Optional[dict] = {}

class DataExtractionResponse(BaseModel):
    tenant_id: str
    extracted_data: dict
    confidence: float = 0.0
    metadata: dict = {}

class DataValidationRequest(BaseModel):
    tenant_id: Optional[str] = None  # Se asigna desde la URL
    message: str
    data_type: str  # 'nombre', 'apellido', 'ciudad', 'aceptacion_terminos', 'codigo_referido'
    
class DataValidationResponse(BaseModel):
    tenant_id: str
    result: str  # 'VALID' o 'INVALID'
    reason: Optional[str] = None
    confidence: float = 0.0
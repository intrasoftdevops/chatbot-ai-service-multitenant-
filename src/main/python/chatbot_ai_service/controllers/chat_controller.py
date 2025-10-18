"""
Controlador simplificado para chat en el servicio de IA
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from chatbot_ai_service.services.ai_service import ai_service
from chatbot_ai_service.services.document_context_service import document_context_service
from chatbot_ai_service.services.session_context_service import session_context_service

logger = logging.getLogger(__name__)

# Modelos de request/response simplificados
class ChatRequest(BaseModel):
    query: str
    session_id: str
    user_context: Optional[Dict[str, Any]] = {}
    maintain_context: bool = True  # Mantener contexto de sesión
    tenant_config: Optional[Dict[str, Any]] = None  # Configuración del tenant

class ChatResponse(BaseModel):
    response: str
    processing_time: Optional[float] = None
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    intent: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None

class ClassificationRequest(BaseModel):
    message: str
    user_context: Optional[Dict[str, Any]] = {}
    session_id: Optional[str] = None

class ClassificationResponse(BaseModel):
    category: str
    confidence: float
    original_message: str
    error: Optional[str] = None

class DataExtractionRequest(BaseModel):
    message: str
    data_type: str

class DataExtractionResponse(BaseModel):
    extracted_data: Dict[str, Any]
    error: Optional[str] = None

class DataValidationRequest(BaseModel):
    data: str
    data_type: str

class DataValidationResponse(BaseModel):
    is_valid: bool
    data_type: str
    error: Optional[str] = None

class NormalizeCityRequest(BaseModel):
    city: str

class NormalizeCityResponse(BaseModel):
    city: str
    state: Optional[str] = None
    country: Optional[str] = None

class RegistrationAnalysisRequest(BaseModel):
    message: str
    user_context: Optional[Dict[str, Any]] = {}
    session_id: Optional[str] = None
    current_state: Optional[str] = None

class RegistrationAnalysisResponse(BaseModel):
    type: str
    value: Optional[str] = None
    confidence: float

class ReferralCodeDetectionRequest(BaseModel):
    message: str

class ReferralCodeDetectionResponse(BaseModel):
    code: Optional[str] = None
    reason: str
    original_message: str
    error: Optional[str] = None

class DocumentLoadRequest(BaseModel):
    documentation_bucket_url: str

class DocumentLoadResponse(BaseModel):
    success: bool
    document_count: Optional[int] = None
    message: str
    error: Optional[str] = None

class DocumentInfoResponse(BaseModel):
    tenant_id: str
    bucket_url: Optional[str] = None
    document_count: Optional[int] = None
    loaded_at: Optional[str] = None
    error: Optional[str] = None

# Crear router
router = APIRouter()

@router.post("/tenants/{tenant_id}/chat", response_model=ChatResponse)
async def process_chat_message(tenant_id: str, request: ChatRequest):
    """
    Procesa un mensaje de chat para un tenant específico
    """
    try:
        logger.info(f"Procesando mensaje de chat para tenant: {tenant_id}")
        
        # Procesar mensaje con IA y contexto de sesión
        result = await ai_service.process_chat_message(
            tenant_id=tenant_id,
            query=request.query,
            user_context=request.user_context,
            session_id=request.session_id if request.maintain_context else None,
            tenant_config=request.tenant_config
        )
        # Loggear intención devuelta por el servicio de IA
        try:
            logger.info(
                f"🧠 Intent devuelto: {result.get('intent')} (confianza: {result.get('confidence')}) | "
                f"tenant={tenant_id} | session={result.get('session_id')} | query='{request.query[:200]}'"
            )
        except Exception:
            pass

        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Error procesando mensaje de chat para tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tenants/{tenant_id}/classify", response_model=ClassificationResponse)
async def classify_intent(tenant_id: str, request: ClassificationRequest):
    """
    Clasifica la intención de un mensaje para un tenant específico
    """
    try:
        logger.info(f"Clasificando intención para tenant: {tenant_id}")
        
        # Clasificar intención con IA
        result = await ai_service.classify_intent(
            tenant_id=tenant_id,
            message=request.message,
            user_context=request.user_context,
            session_id=request.session_id
        )
        # Loggear categoría devuelta por el clasificador
        try:
            logger.info(
                f"🧠 Clasificación: {result.get('category')} (confianza: {result.get('confidence')}) | "
                f"tenant={tenant_id} | mensaje='{request.message[:200]}'"
            )
        except Exception:
            pass

        return ClassificationResponse(**result)
        
    except Exception as e:
        logger.error(f"Error clasificando intención para tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tenants/{tenant_id}/extract-data", response_model=DataExtractionResponse)
async def extract_data(tenant_id: str, request: DataExtractionRequest):
    """
    Extrae datos específicos de un mensaje para un tenant específico
    """
    try:
        logger.info(f"Extrayendo {request.data_type} para tenant: {tenant_id}")
        
        # Extraer datos con IA
        result = await ai_service.extract_data(
            tenant_id=tenant_id,
            message=request.message,
            data_type=request.data_type
        )
        
        return DataExtractionResponse(**result)
        
    except Exception as e:
        logger.error(f"Error extrayendo {request.data_type} para tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tenants/{tenant_id}/validate-data", response_model=DataValidationResponse)
async def validate_data(tenant_id: str, request: DataValidationRequest):
    """
    Valida datos de entrada para un tenant específico
    """
    try:
        logger.info(f"Validando {request.data_type} para tenant: {tenant_id}")
        
        # Validar datos
        result = await ai_service.validate_data(
            tenant_id=tenant_id,
            data=request.data,
            data_type=request.data_type
        )
        
        return DataValidationResponse(**result)
        
    except Exception as e:
        logger.error(f"Error validando {request.data_type} para tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tenants/{tenant_id}/normalize-city", response_model=NormalizeCityResponse)
async def normalize_city(tenant_id: str, request: NormalizeCityRequest):
    """
    Normaliza una ciudad y detecta su departamento usando IA
    """
    try:
        logger.info(f"Normalizando ciudad para tenant: {tenant_id}")
        result = await ai_service.normalize_location(request.city)
        return NormalizeCityResponse(**result)
    except Exception as e:
        logger.error(f"Error normalizando ciudad para tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tenants/{tenant_id}/analyze-registration", response_model=RegistrationAnalysisResponse)
async def analyze_registration(tenant_id: str, request: RegistrationAnalysisRequest):
    """
    Analiza un mensaje para determinar si contiene un dato de registro (name/lastname/city) o es información general.
    """
    try:
        logger.info(f"Analizando registro para tenant: {tenant_id}")
        result = await ai_service.analyze_registration(
            tenant_id=tenant_id,
            message=request.message,
            user_context=request.user_context,
            session_id=request.session_id,
            current_state=request.current_state
        )
        return RegistrationAnalysisResponse(**result)
    except Exception as e:
        logger.error(f"Error analizando registro para tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tenants/{tenant_id}/detect-referral-code", response_model=ReferralCodeDetectionResponse)
async def detect_referral_code(tenant_id: str, request: ReferralCodeDetectionRequest):
    """
    Detecta si un mensaje contiene un código de referido usando IA
    """
    try:
        logger.info(f"Detectando código de referido para tenant: {tenant_id}")
        
        # Detectar código con IA
        result = await ai_service.detect_referral_code(
            tenant_id=tenant_id,
            message=request.message
        )
        
        return ReferralCodeDetectionResponse(**result)
        
    except Exception as e:
        logger.error(f"Error detectando código de referido para tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tenants/{tenant_id}/load-documents", response_model=DocumentLoadResponse)
async def load_tenant_documents(tenant_id: str, request: DocumentLoadRequest):
    """
    Carga documentos del bucket del tenant para proporcionar contexto a la IA
    """
    try:
        logger.info(f"Cargando documentos para tenant: {tenant_id}")
        
        # Cargar documentos
        success = await document_context_service.load_tenant_documents(
            tenant_id=tenant_id,
            documentation_bucket_url=request.documentation_bucket_url
        )
        
        if success:
            # Obtener información de los documentos cargados
            doc_info = document_context_service.get_tenant_document_info(tenant_id)
            document_count = doc_info.get("document_count", 0) if doc_info else 0
            
            return DocumentLoadResponse(
                success=True,
                document_count=document_count,
                message=f"Documentos cargados exitosamente: {document_count} documentos"
            )
        else:
            return DocumentLoadResponse(
                success=False,
                message="No se pudieron cargar los documentos"
            )
        
    except Exception as e:
        logger.error(f"Error cargando documentos para tenant {tenant_id}: {str(e)}")
        return DocumentLoadResponse(
            success=False,
            error=str(e),
            message="Error interno del servidor"
        )

@router.get("/tenants/{tenant_id}/documents/info", response_model=DocumentInfoResponse)
async def get_tenant_document_info(tenant_id: str):
    """
    Obtiene información sobre los documentos cargados para un tenant
    """
    try:
        doc_info = document_context_service.get_tenant_document_info(tenant_id)
        
        if doc_info:
            return DocumentInfoResponse(
                tenant_id=tenant_id,
                bucket_url=doc_info.get("bucket_url"),
                document_count=doc_info.get("document_count"),
                loaded_at=str(doc_info.get("loaded_at", "N/A"))
            )
        else:
            return DocumentInfoResponse(
                tenant_id=tenant_id,
                message="No hay documentos cargados para este tenant"
            )
        
    except Exception as e:
        logger.error(f"Error obteniendo información de documentos para tenant {tenant_id}: {str(e)}")
        return DocumentInfoResponse(
            tenant_id=tenant_id,
            error=str(e)
        )

@router.delete("/tenants/{tenant_id}/documents")
async def clear_tenant_documents(tenant_id: str):
    """
    Limpia el cache de documentos para un tenant específico
    """
    try:
        document_context_service.clear_tenant_cache(tenant_id)
        return {
            "success": True,
            "message": f"Cache de documentos limpiado para tenant {tenant_id}"
        }
        
    except Exception as e:
        logger.error(f"Error limpiando cache de documentos para tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINTS DE GESTIÓN DE SESIONES =====

class SessionInfoResponse(BaseModel):
    session_id: str
    tenant_id: str
    user_id: Optional[str] = None
    message_count: int
    has_document_context: bool
    document_context_length: int
    last_activity: str
    created_at: str
    user_context: Dict[str, Any]

class SessionStatsResponse(BaseModel):
    total_sessions: int
    total_messages: int
    sessions_with_context: int
    average_messages_per_session: float
    tenant_id: str

@router.get("/tenants/{tenant_id}/sessions/{session_id}/info", response_model=SessionInfoResponse)
async def get_session_info(tenant_id: str, session_id: str):
    """
    Obtiene información sobre una sesión específica
    """
    try:
        session_summary = session_context_service.get_session_summary(session_id)
        
        if not session_summary:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        if session_summary.get("tenant_id") != tenant_id:
            raise HTTPException(status_code=403, detail="Sesión no pertenece al tenant")
        
        return SessionInfoResponse(**session_summary)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo información de sesión {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tenants/{tenant_id}/sessions/stats", response_model=SessionStatsResponse)
async def get_session_stats(tenant_id: str):
    """
    Obtiene estadísticas de sesiones para un tenant
    """
    try:
        stats = session_context_service.get_session_stats(tenant_id)
        return SessionStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de sesiones para tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tenants/{tenant_id}/sessions")
async def get_active_sessions(tenant_id: str):
    """
    Obtiene todas las sesiones activas para un tenant
    """
    try:
        sessions = session_context_service.get_active_sessions(tenant_id)
        return {
            "tenant_id": tenant_id,
            "active_sessions": sessions,
            "count": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo sesiones activas para tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tenants/{tenant_id}/sessions/{session_id}")
async def clear_session(tenant_id: str, session_id: str):
    """
    Limpia una sesión específica
    """
    try:
        # Verificar que la sesión pertenece al tenant
        session = session_context_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        if session.tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="Sesión no pertenece al tenant")
        
        success = session_context_service.clear_session(session_id)
        
        if success:
            return {"success": True, "message": f"Sesión {session_id} limpiada exitosamente"}
        else:
            raise HTTPException(status_code=500, detail="Error limpiando sesión")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error limpiando sesión {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tenants/{tenant_id}/sessions")
async def clear_all_sessions(tenant_id: str):
    """
    Limpia todas las sesiones de un tenant
    """
    try:
        cleared_count = session_context_service.clear_tenant_sessions(tenant_id)
        
        return {
            "success": True, 
            "message": f"Se limpiaron {cleared_count} sesiones para tenant {tenant_id}"
        }
        
    except Exception as e:
        logger.error(f"Error limpiando sesiones para tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    Health check del servicio de IA
    """
    return {
        "status": "healthy",
        "service": "chatbot-ai-service",
        "version": "1.0.0"
    }
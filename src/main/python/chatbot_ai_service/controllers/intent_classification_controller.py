"""
Controlador de Clasificación de Intenciones
==========================================

Maneja la clasificación de intenciones y análisis de registro
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from chatbot_ai_service.services.ai_service import ai_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["intent-classification"])

@router.post("/tenants/{tenant_id}/classify")
async def classify_intent(tenant_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clasifica la intención de un mensaje
    """
    try:
        logger.info(f"🎯 Clasificando intención para tenant: {tenant_id}")
        
        message = request.get("message", "").strip()
        user_context = request.get("user_context", {})
        
        if not message:
            raise HTTPException(status_code=400, detail="Message parameter is required")
        
        logger.info(f"📝 Mensaje a clasificar: '{message[:50]}...'")
        
        # Clasificar con el servicio de IA
        classification_result = await ai_service.classify_intent(tenant_id, message, user_context)
        
        # 🔧 FIX: classify_intent devuelve "category", no "classification"
        return {
            "category": classification_result.get("category", "general_query"),  # 🔧 FIX: Usar "category" directamente
            "confidence": classification_result.get("confidence", 0.0),
            "processing_time": classification_result.get("processing_time", 0.0),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error clasificando intención: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clasificando intención: {str(e)}")

@router.post("/tenants/{tenant_id}/analyze-registration")
async def analyze_registration(tenant_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza un mensaje durante el proceso de registro
    """
    try:
        logger.info(f"🎯 Analizando registro para tenant: {tenant_id}")
        
        message = request.get("message", "").strip()
        user_context = request.get("user_context", {})
        current_state = request.get("current_state", "")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message parameter is required")
        
        logger.info(f"📝 Mensaje de registro: '{message[:50]}...'")
        logger.info(f"📊 Estado actual: {current_state}")
        
        # Analizar con el servicio de IA
        analysis_result = await ai_service.analyze_registration_message(tenant_id, message, user_context, current_state)
        
        return {
            "type": analysis_result.get("type", "other"),
            "value": analysis_result.get("value"),
            "confidence": analysis_result.get("confidence", 0.0),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error analizando registro: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analizando registro: {str(e)}")

@router.post("/tenants/{tenant_id}/detect-referral-code")
async def detect_referral_code(tenant_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detecta códigos de referido en un mensaje
    """
    try:
        logger.info(f"🎯 Detectando código de referido para tenant: {tenant_id}")
        
        message = request.get("message", "").strip()
        user_context = request.get("user_context", {})
        
        if not message:
            raise HTTPException(status_code=400, detail="Message parameter is required")
        
        logger.info(f"📝 Mensaje a analizar: '{message[:50]}...'")
        
        # Detectar código con el servicio de IA
        detection_result = await ai_service.detect_referral_code(tenant_id, message)
        
        logger.info(f"🔍 DEBUG Controller: detection_result completo: {detection_result}")
        
        # El servicio Python devuelve "code", pero el controller debe devolver "referral_code"
        detected_code = detection_result.get("code")
        logger.info(f"🔍 DEBUG Controller: código extraído 'code': '{detected_code}'")
        
        return {
            "referral_code": detected_code,
            "confidence": detection_result.get("confidence", 0.0),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error detectando código de referido: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error detectando código de referido: {str(e)}")

@router.post("/tenants/{tenant_id}/validate-data")
async def validate_data(tenant_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida datos de usuario (nombre, apellido, ciudad, etc.)
    """
    try:
        logger.info(f"🎯 Validando datos para tenant: {tenant_id}")
        
        data = request.get("data", "").strip()
        data_type = request.get("data_type", "").strip()
        
        if not data or not data_type:
            raise HTTPException(status_code=400, detail="Data and data_type parameters are required")
        
        logger.info(f"📝 Validando {data_type}: '{data[:50]}...'")
        
        # Validar con el servicio de IA
        validation_result = await ai_service.validate_user_data(tenant_id, data, data_type)
        
        return {
            "is_valid": validation_result.get("is_valid", False),
            "confidence": validation_result.get("confidence", 0.0),
            "suggestions": validation_result.get("suggestions", []),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error validando datos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error validando datos: {str(e)}")

@router.post("/tenants/{tenant_id}/is-question")
async def is_question_endpoint(tenant_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verifica si un mensaje es una pregunta o consulta usando IA
    """
    try:
        message = request.get("message", "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message parameter is required")
        
        logger.info(f"🔍 Verificando si el mensaje es una pregunta: '{message[:50]}...'")
        
        # Verificar con el servicio de IA
        is_question_result = await ai_service.is_question_message(tenant_id, message)
        
        return {
            "is_question": is_question_result.get("is_question", False),
            "confidence": is_question_result.get("confidence", 0.0),
            "reason": is_question_result.get("reason"),
            "success": True
        }
    except Exception as e:
        logger.error(f"Error verificando si es pregunta: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error verificando si es pregunta: {str(e)}")

@router.post("/tenants/{tenant_id}/extract-user-name")
async def extract_user_name_endpoint(tenant_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrae el nombre del usuario de un mensaje que contiene código de referido
    """
    try:
        message = request.get("message", "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message parameter is required")
        
        logger.info(f"📝 Extrayendo nombre del usuario del mensaje: '{message[:50]}...'")
        
        # Extraer nombre con el servicio de IA
        extraction_result = await ai_service.extract_user_name_from_message(tenant_id, message)
        
        return {
            "name": extraction_result.get("name"),
            "is_valid": extraction_result.get("is_valid", False),
            "confidence": extraction_result.get("confidence", 0.0),
            "reason": extraction_result.get("reason"),
            "success": True
        }
    except Exception as e:
        logger.error(f"Error extrayendo nombre del usuario: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extrayendo nombre del usuario: {str(e)}")

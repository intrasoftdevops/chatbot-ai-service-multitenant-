"""
Controlador de Chat
==================

Maneja las peticiones de chat y procesa los marcadores FOLLOWUP_MESSAGE
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import time
import re

from chatbot_ai_service.services.ai_service import AIService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["chat"])

@router.post("/tenants/{tenant_id}/chat")
async def process_chat_message(tenant_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Procesa un mensaje de chat y maneja los marcadores FOLLOWUP_MESSAGE
    """
    try:
        logger.info(f"🎯 Procesando mensaje de chat para tenant: {tenant_id}")
        
        # Extraer datos del request
        query = request.get("query", "").strip()
        user_context = request.get("user_context", {})
        session_id = request.get("session_id")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")
        
        logger.info(f"📝 Mensaje recibido: '{query[:50]}...'")
        logger.info(f"👤 Usuario: {user_context.get('user_id', 'unknown')}")
        
        # Procesar mensaje con el servicio de IA
        ai_service = AIService()
        ai_response = await ai_service.process_chat_message(tenant_id, query, user_context, session_id)
        
        # NUEVO ENFOQUE: Usar followup_message directamente del servicio de IA
        clean_response = ai_response.get("response", "")
        followup_message = ai_response.get("followup_message", "")
        
        logger.info(f"📤 NUEVO ENFOQUE: Respuesta principal: {len(clean_response)} caracteres")
        logger.info(f"📤 NUEVO ENFOQUE: Followup message: {len(followup_message)} caracteres")
        
        # Construir respuesta final
        response = {
            "response": clean_response,
            "followup_message": followup_message,
            "processing_time": ai_response.get("processing_time", 0),
            "tenant_id": tenant_id,
            "session_id": session_id or f"session_{user_context.get('user_id', 'unknown')}",
            "intent": ai_response.get("intent", "unknown"),
            "confidence": ai_response.get("confidence", 0.8),
            "error": ai_response.get("error")
        }
        
        logger.info(f"✅ Respuesta procesada - followup_message: {bool(followup_message)}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error procesando mensaje de chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando mensaje: {str(e)}")

def process_followup_markers(response_text: str) -> Dict[str, str]:
    """
    Procesa los marcadores FOLLOWUP_MESSAGE_START y FOLLOWUP_MESSAGE_END
    para extraer el mensaje de seguimiento
    
    Args:
        response_text: Texto de respuesta que puede contener marcadores
        
    Returns:
        Dict con 'clean_response' y 'followup_message'
    """
    try:
        if not response_text:
            return {"clean_response": "", "followup_message": ""}
        
        # Patrón para encontrar el contenido entre marcadores
        pattern = r'<<<FOLLOWUP_MESSAGE_START>>>(.*?)<<<FOLLOWUP_MESSAGE_END>>>'
        match = re.search(pattern, response_text, re.DOTALL)
        
        if match:
            # Extraer el mensaje de seguimiento
            followup_message = match.group(1).strip()
            
            # Remover los marcadores del texto de respuesta
            clean_response = re.sub(pattern, '', response_text, flags=re.DOTALL).strip()
            
            logger.info(f"📤 Marcador FOLLOWUP_MESSAGE detectado y extraído")
            logger.info(f"📝 Mensaje de seguimiento extraído: '{followup_message[:100]}...'")
            logger.info(f"🧹 Respuesta limpia: '{clean_response[:100]}...'")
            
            return {
                "clean_response": clean_response,
                "followup_message": followup_message
            }
        else:
            # Verificar si hay marcador de inicio sin cierre (error)
            if "<<<FOLLOWUP_MESSAGE_START>>>" in response_text:
                logger.warning("⚠️ Marcador FOLLOWUP_MESSAGE sin cierre detectado; no se alterará la respuesta ni se enviará segundo mensaje")
                logger.warning(f"⚠️ Vista previa desde el marcador: {response_text[response_text.find('<<<FOLLOWUP_MESSAGE_START>>>'):response_text.find('<<<FOLLOWUP_MESSAGE_START>>>') + 100]}")
            
            return {
                "clean_response": response_text,
                "followup_message": ""
            }
            
    except Exception as e:
        logger.error(f"❌ Error procesando marcadores FOLLOWUP_MESSAGE: {str(e)}")
        return {
            "clean_response": response_text,
            "followup_message": ""
        }

@router.get("/tenants/{tenant_id}/conversations/{session_id}/history")
async def get_conversation_history(tenant_id: str, session_id: str) -> Dict[str, Any]:
    """
    Obtiene el historial de conversación (placeholder)
    """
    return {
        "tenant_id": tenant_id,
        "session_id": session_id,
        "messages": [],
        "status": "placeholder"
    }

@router.get("/tenants/{tenant_id}/conversations/active")
async def get_active_conversations(tenant_id: str) -> Dict[str, Any]:
    """
    Obtiene conversaciones activas (placeholder)
    """
    return {
        "tenant_id": tenant_id,
        "active_conversations": [],
        "status": "placeholder"
    }

@router.get("/tenants/{tenant_id}/conversations/phone/{phone}")
async def get_conversation_by_phone(tenant_id: str, phone: str) -> Dict[str, Any]:
    """
    Obtiene conversación por teléfono (placeholder)
    """
    return {
        "tenant_id": tenant_id,
        "phone": phone,
        "conversation": None,
        "status": "placeholder"
    }

@router.get("/tenants/{tenant_id}/conversations/stats")
async def get_conversation_stats(tenant_id: str) -> Dict[str, Any]:
    """
    Obtiene estadísticas de conversaciones (placeholder)
    """
    return {
        "tenant_id": tenant_id,
        "stats": {
            "total_conversations": 0,
            "active_conversations": 0,
            "total_messages": 0
        },
        "status": "placeholder"
    }

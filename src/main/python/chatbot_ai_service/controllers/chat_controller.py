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
from chatbot_ai_service.services.optimized_ai_service import OptimizedAIService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["chat"])

@router.post("/tenants/{tenant_id}/chat")
async def process_chat_message(tenant_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Procesa un mensaje de chat y maneja los marcadores FOLLOWUP_MESSAGE
    """
    try:
        logger.info(f"🎯 [CONTROLLER] INICIANDO procesamiento de chat para tenant: {tenant_id}")
        logger.info(f"🎯 [CONTROLLER] Request recibido: {type(request)} con keys: {list(request.keys()) if isinstance(request, dict) else 'No es dict'}")
        
        # Extraer datos del request
        query = request.get("query", "").strip()
        conversation_history = request.get("conversation_history", "")
        user_context = request.get("user_context", {})
        tenant_config = request.get("tenant_config", {})
        session_id = request.get("session_id")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")
        
        logger.info(f"📝 Mensaje recibido: '{query[:50]}...'")
        logger.info(f"👤 Usuario: {user_context.get('user_id', 'unknown')}")
        logger.info(f"🔧 Configuración del tenant recibida: {bool(tenant_config)}")
        
        # Procesar mensaje con el servicio de IA optimizado
        logger.info(f"🚀 Usando servicio de IA optimizado...")
        logger.info(f"🔍 DEBUG: Parámetros enviados:")
        logger.info(f"   - tenant_id: {tenant_id}")
        logger.info(f"   - query: '{query}'")
        logger.info(f"   - user_context: {user_context}")
        logger.info(f"   - session_id: {session_id}")
        logger.info(f"   - tenant_config keys: {list(tenant_config.keys()) if tenant_config else 'None'}")
        
        # Usar servicio optimizado
        logger.info(f"🚀 [CONTROLLER] Iniciando OptimizedAIService para tenant {tenant_id}")
        logger.info(f"🔍 [CONTROLLER] tenant_config recibido: {tenant_config}")
        logger.info(f"🔍 [CONTROLLER] tenant_config type: {type(tenant_config)}")
        logger.info(f"🔍 [CONTROLLER] tenant_config keys: {list(tenant_config.keys()) if tenant_config else 'None'}")
        
        logger.info(f"🔧 [CONTROLLER] Creando AIService base...")
        base_ai_service = AIService()
        logger.info(f"🔧 [CONTROLLER] AIService base creado exitosamente")
        
        logger.info(f"🔧 [CONTROLLER] Creando OptimizedAIService...")
        optimized_ai_service = OptimizedAIService(base_ai_service)
        logger.info(f"🔧 [CONTROLLER] OptimizedAIService creado exitosamente, iniciando procesamiento...")
        
        try:
            logger.info(f"🚀 [CONTROLLER] Llamando a process_chat_message_optimized...")
            # 🔧 MEJORA: Mejorar query con historial de conversación si existe
            enhanced_query = query
            if conversation_history:
                logger.info(f"🔧 [CONTROLLER] conversation_history presente, longitud: {len(conversation_history)}")
                logger.info(f"🔧 [CONTROLLER] Primeros 200 caracteres de historial: '{conversation_history[:200]}...'")
                enhanced_query = f"Historial de conversación:\n{conversation_history}\n\nPregunta actual del usuario: {query}"
                logger.info(f"🔧 [CONTROLLER] enhanced_query construido, longitud: {len(enhanced_query)}")
                logger.info(f"🔧 [CONTROLLER] Primeros 200 caracteres de enhanced_query: '{enhanced_query[:200]}...'")
            else:
                logger.info(f"🔧 [CONTROLLER] No hay conversation_history, usando query original")
            
            ai_response = await optimized_ai_service.process_chat_message_optimized(
                tenant_id, enhanced_query, user_context, session_id, tenant_config
            )
            logger.info(f"✅ [CONTROLLER] OptimizedAIService completado exitosamente")
        except Exception as e:
            logger.error(f"❌ [CONTROLLER] Error en OptimizedAIService: {str(e)}")
            logger.error(f"❌ [CONTROLLER] Traceback: {e}", exc_info=True)
            # Fallback al servicio básico
            logger.info(f"🔄 [CONTROLLER] Fallback al AIService básico...")
            ai_response = await base_ai_service.process_chat_message(
                tenant_id, query, user_context, session_id, tenant_config
            )
        
        logger.info(f"🔍 DEBUG: Respuesta recibida del ai_service:")
        logger.info(f"   - Tipo: {type(ai_response)}")
        logger.info(f"   - Keys: {list(ai_response.keys()) if isinstance(ai_response, dict) else 'No es dict'}")
        logger.info(f"   - Response length: {len(ai_response.get('response', '')) if isinstance(ai_response, dict) else 'N/A'}")
        logger.info(f"   - Intent: {ai_response.get('intent', 'N/A') if isinstance(ai_response, dict) else 'N/A'}")
        logger.info(f"   - Confidence: {ai_response.get('confidence', 'N/A') if isinstance(ai_response, dict) else 'N/A'}")
        logger.info(f"🔍 DEBUG: Contenido completo de la respuesta: {ai_response}")
        
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

@router.post("/tenants/{tenant_id}/preload-documents")
async def preload_tenant_documents(tenant_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Precarga documentos del tenant para RAG
    """
    try:
        logger.info(f"📚 Precargando documentos para tenant: {tenant_id}")
        
        # Extraer datos del request
        documentation_bucket_url = request.get("documentation_bucket_url")
        
        if not documentation_bucket_url:
            raise HTTPException(status_code=400, detail="documentation_bucket_url parameter is required")
        
        logger.info(f"📚 URL del bucket: {documentation_bucket_url}")
        
        # Usar el servicio de documentos para precargar
        from chatbot_ai_service.services.document_context_service import document_context_service
        
        success = await document_context_service.load_tenant_documents(tenant_id, documentation_bucket_url)
        
        if success:
            logger.info(f"✅ Documentos precargados exitosamente para tenant {tenant_id}")
            return {
                "success": True,
                "message": f"Documentos precargados para tenant {tenant_id}",
                "tenant_id": tenant_id,
                "bucket_url": documentation_bucket_url
            }
        else:
            logger.warning(f"⚠️ No se pudieron precargar documentos para tenant {tenant_id}")
            return {
                "success": False,
                "message": f"No se pudieron precargar documentos para tenant {tenant_id}",
                "tenant_id": tenant_id,
                "bucket_url": documentation_bucket_url
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error precargando documentos para tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error precargando documentos: {str(e)}")

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

@router.post("/tenants/{tenant_id}/generate-welcome-message")
async def generate_welcome_message(tenant_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera un mensaje de bienvenida personalizado usando IA
    """
    try:
        # Extraer configuración del tenant
        tenant_config = request.get("tenant_config", {})
        
        # Generar mensaje con IA
        ai_service = AIService()
        message = await ai_service.generate_welcome_message(tenant_config)
        
        return {
            "tenant_id": tenant_id,
            "message": message,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"❌ Error generando mensaje de bienvenida: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generando mensaje de bienvenida: {str(e)}")

@router.post("/tenants/{tenant_id}/generate-contact-save-message")
async def generate_contact_save_message(tenant_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera un mensaje para pedir guardar el contacto usando IA
    """
    try:
        # Extraer configuración del tenant
        tenant_config = request.get("tenant_config", {})
        
        # Generar mensaje con IA
        ai_service = AIService()
        message = await ai_service.generate_contact_save_message(tenant_config)
        
        return {
            "tenant_id": tenant_id,
            "message": message,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"❌ Error generando mensaje de guardar contacto: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generando mensaje de guardar contacto: {str(e)}")

@router.post("/tenants/{tenant_id}/generate-name-request-message")
async def generate_name_request_message(tenant_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera un mensaje para pedir el nombre del usuario usando IA
    """
    try:
        # Extraer configuración del tenant
        tenant_config = request.get("tenant_config", {})
        
        # Generar mensaje con IA
        ai_service = AIService()
        message = await ai_service.generate_name_request_message(tenant_config)
        
        return {
            "tenant_id": tenant_id,
            "message": message,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"❌ Error generando mensaje de pedir nombre: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generando mensaje de pedir nombre: {str(e)}")

@router.post("/tenants/{tenant_id}/generate-all-initial-messages")
async def generate_all_initial_messages(tenant_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera los 3 mensajes iniciales de una vez para optimizar el tiempo de respuesta
    """
    try:
        # 🔧 FIX: Extraer configuración del tenant del campo correcto
        tenant_config = request.get("tenant_config", {})
        if not tenant_config and "branding" in request:
            # Si no hay tenant_config pero sí branding, usar branding directamente
            tenant_config = {"branding": request["branding"]}
        
        logger.info(f"🔍 Configuración recibida: {tenant_config}")
        
        # Generar los 3 mensajes con IA
        ai_service = AIService()
        messages = await ai_service.generate_all_initial_messages(tenant_config)
        
        return {
            "tenant_id": tenant_id,
            "messages": messages,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"❌ Error generando mensajes iniciales: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generando mensajes iniciales: {str(e)}")

@router.post("/tenants/{tenant_id}/process-optimized")
async def process_message_optimized(tenant_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    🚀 ENDPOINT OPTIMIZADO: Procesa mensaje con análisis completo en una sola llamada
    Combina: clasificación + análisis de registro + detección de malicia + respuesta
    """
    try:
        logger.info(f"🚀 Procesando mensaje optimizado para tenant: {tenant_id}")
        
        # Extraer datos del request
        message = request.get("message", "").strip()
        user_context = request.get("user_context", {})
        session_id = request.get("session_id")
        current_state = request.get("current_state", "UNKNOWN")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message parameter is required")
        
        logger.info(f"📝 Mensaje: '{message[:50]}...' | Estado: {current_state}")
        
        # Procesar con el servicio de IA optimizado
        ai_service = AIService()
        
        # 1. Clasificar intención
        classification = await ai_service.classify_intent(tenant_id, message, user_context)
        intent = classification.get("classification", {}).get("category", "general_query")
        
        # 2. Analizar para registro
        analysis = await ai_service.analyze_registration_message(tenant_id, message, user_context, current_state)
        analysis_type = analysis.get("type", "other")
        analysis_value = analysis.get("value")
        
        # 3. Detectar malicia
        is_malicious = intent in ["malicious", "spam", "inappropriate"]
        
        # 4. Generar respuesta
        if is_malicious:
            response = "Lo siento, no puedo ayudarte con ese tipo de consulta."
        elif analysis_type == "name" and analysis_value:
            response = f"¡Hola {analysis_value}! Es un placer conocerte. ¿En qué puedo ayudarte?"
        elif analysis_type == "info":
            response = await ai_service.process_chat_message(tenant_id, message, user_context, session_id)
            response = response.get("response", "Gracias por tu consulta. ¿Hay algo más en lo que pueda ayudarte?")
        else:
            response = await ai_service.process_chat_message(tenant_id, message, user_context, session_id)
            response = response.get("response", "Gracias por tu mensaje. ¿En qué puedo ayudarte?")
        
        return {
            "response": response,
            "intent": intent,
            "analysis_type": analysis_type,
            "analysis_value": analysis_value,
            "is_malicious": is_malicious,
            "confidence": classification.get("confidence", 0.8),
            "processing_time": classification.get("processing_time", 0),
            "tenant_id": tenant_id,
            "session_id": session_id or f"session_{user_context.get('user_id', 'unknown')}",
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error procesando mensaje optimizado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando mensaje optimizado: {str(e)}")

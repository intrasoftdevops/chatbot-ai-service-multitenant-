"""
Servicio de IA optimizado con timeout y logging mejorado
"""
import logging
import time
from typing import Dict, Any, Optional
from chatbot_ai_service.config.optimization_config import optimization_config

logger = logging.getLogger(__name__)

class OptimizedAIService:
    """Servicio de IA optimizado con timeout y logging mejorado"""
    
    # Cache global de prompts cargados al arrancar
    _prompts_cache = {}
    
    def __init__(self, base_ai_service):
        self.base_ai_service = base_ai_service
        self.logger = logging.getLogger(__name__)
    
    async def process_chat_message_optimized(self, tenant_id: str, query: str, 
                                           user_context: Dict[str, Any], 
                                           session_id: str = None, 
                                           tenant_config: Dict[str, Any] = None,
                                           conversation_history: str = None) -> Dict[str, Any]:
        """
        Procesa mensaje de chat con optimizaciones simplificadas
        
        Args:
            tenant_id: ID del tenant
            query: Mensaje del usuario (SIN historial - solo para clasificación)
            user_context: Contexto del usuario
            session_id: ID de la sesión
            tenant_config: Configuración del tenant
            conversation_history: Historial de conversación (para procesamiento, NO para clasificación)
            
        Returns:
            Respuesta optimizada
        """
        print(f"🚀 [OPTIMIZED] MÉTODO INICIADO - tenant: {tenant_id}, query: '{query[:50]}...'")
        self.logger.info(f"🚀 [OPTIMIZED] MÉTODO INICIADO - tenant: {tenant_id}, query: '{query[:50]}...'")
        
        start_time = time.time()
        
        try:
            # 1. VERIFICAR CONFIGURACIÓN DEL TENANT
            # 🔍 DEBUG CRÍTICO: Ver qué tenant_config estamos recibiendo
            if tenant_config:
                self.logger.info(f"✅ [OPTIMIZED] tenant_config RECIBIDO - keys: {list(tenant_config.keys())}")
                if 'numero_whatsapp' in tenant_config:
                    self.logger.info(f"✅ [OPTIMIZED] numero_whatsapp PRESENTE: '{tenant_config['numero_whatsapp']}'")
                else:
                    self.logger.warning(f"❌ [OPTIMIZED] numero_whatsapp NO PRESENTE en tenant_config")
            else:
                self.logger.warning(f"⚠️ No se recibió tenant_config en el request, obteniendo desde servicio Java...")
                tenant_config = self._get_tenant_config(tenant_id)
                if not tenant_config:
                    return self._create_error_response("Tenant no encontrado", start_time)
                # 🔍 DEBUG: Ver qué devolvió _get_tenant_config
                self.logger.info(f"✅ [OPTIMIZED] tenant_config desde GET - keys: {list(tenant_config.keys())}")
                if 'numero_whatsapp' in tenant_config:
                    self.logger.info(f"✅ [OPTIMIZED] numero_whatsapp desde GET: '{tenant_config['numero_whatsapp']}'")
                else:
                    self.logger.warning(f"❌ [OPTIMIZED] numero_whatsapp NO en tenant_config desde GET")
            
            # 2. CLASIFICAR INTENCIÓN
            print(f"🎯 [OPTIMIZED] Clasificando intención...")
            self.logger.info(f"🎯 [OPTIMIZED] Clasificando intención...")
            try:
                # 🔧 AGREGAR HISTORIAL AL USER_CONTEXT ANTES DE CLASIFICAR
                classification_user_context = user_context.copy() if user_context else {}
                if conversation_history:
                    classification_user_context['conversation_history'] = conversation_history
                    self.logger.info(f"📚 [CLASIFICACIÓN] Historial incluido en user_context ({len(conversation_history)} chars)")
                
                intent_result = await self._classify_intent_optimized(tenant_id, query, classification_user_context)
                intent = intent_result.get("category", "saludo_apoyo")
                confidence = intent_result.get("confidence", 0.0)
                
                # 📊 IMPRIMIR CLASIFICACIÓN DETALLADA
                print(f"📊 [CLASIFICACIÓN] Mensaje: '{query[:100]}...'")
                self.logger.info(f"📊 [CLASIFICACIÓN] Mensaje: '{query[:100]}...'")
                print(f"📊 [CLASIFICACIÓN] Categoría: '{intent}'")
                self.logger.info(f"📊 [CLASIFICACIÓN] Categoría: '{intent}'")
                print(f"📊 [CLASIFICACIÓN] Confianza: {confidence:.2f}")
                self.logger.info(f"📊 [CLASIFICACIÓN] Confianza: {confidence:.2f}")
                print(f"📊 [CLASIFICACIÓN] Tenant: {tenant_id}")
                self.logger.info(f"📊 [CLASIFICACIÓN] Tenant: {tenant_id}")
                print(f"📊 [CLASIFICACIÓN] Session: {session_id}")
                self.logger.info(f"📊 [CLASIFICACIÓN] Session: {session_id}")
                print(f"📊 [CLASIFICACIÓN] {'='*50}")
                self.logger.info(f"📊 [CLASIFICACIÓN] {'='*50}")
                
                # 🎯 DEBUG: Verificar si es saludo antes del bloque de malicia
                print(f"🎯 [DEBUG] Intent después de clasificación: '{intent}'")
                print(f"🎯 [DEBUG] ¿Es saludo_apoyo? {intent == 'saludo_apoyo'}")
                print(f"🎯 [DEBUG] ¿Es queja_detalle_select? {intent == 'queja_detalle_select'}")
                
                # 🚫 PRIORIDAD CRÍTICA: Si es malicioso, BLOQUEAR INMEDIATAMENTE y NO procesar
                if intent == "malicioso":
                    self.logger.warning(f"🚫🚫🚫 MALICIA DETECTADA - BLOQUEANDO INMEDIATAMENTE")
                    self.logger.warning(f"🚫 Intent: '{intent}'")
                    self.logger.warning(f"🚫 Mensaje: '{query}'")
                    self.logger.warning(f"🚫 Confianza: {confidence:.2f}")
                    self.logger.warning(f"🚫 Tenant: {tenant_id}")
                    print(f"🚫🚫🚫 MALICIA DETECTADA EN PYTHON - BLOQUEANDO")
                    
                    # Obtener información del usuario para logging
                    user_id = user_context.get("user_id", "unknown")
                    phone_number = user_id if user_id != "unknown" else "unknown"
                    
                    self.logger.info(f"🔔 Información de usuario para bloqueo:")
                    self.logger.info(f"   - user_id: {user_id}")
                    self.logger.info(f"   - phone_number: {phone_number}")
                    
                    # Importar el servicio de notificación
                    from chatbot_ai_service.services.blocking_notification_service import BlockingNotificationService
                    
                    # Inicializar servicio de notificación si no existe
                    if not hasattr(self.base_ai_service, 'blocking_notification_service') or not self.base_ai_service.blocking_notification_service:
                        blocking_service = BlockingNotificationService()
                        import os
                        java_url = os.getenv("POLITICAL_REFERRALS_SERVICE_URL", "http://localhost:8080")
                        blocking_service.set_java_service_url(java_url)
                        self.base_ai_service.blocking_notification_service = blocking_service
                    
                    # Notificar al servicio Java para bloquear en WATI
                    self.logger.info(f"🔔 Enviando notificación de bloqueo al servicio Java")
                    try:
                        notification_result = await self.base_ai_service.blocking_notification_service.notify_user_blocked(
                            tenant_id=tenant_id,
                            user_id=user_id,
                            phone_number=phone_number,
                            malicious_message=query,
                            classification_confidence=confidence
                        )
                        self.logger.info(f"🔔 Resultado de notificación: {notification_result}")
                        
                        if notification_result.get("success"):
                            self.logger.info(f"✅ Usuario {user_id} bloqueado en WATI y base de datos")
                        else:
                            self.logger.error(f"❌ Error bloqueando usuario: {notification_result.get('error')}")
                    except Exception as notif_error:
                        self.logger.error(f"❌ Excepción notificando bloqueo: {str(notif_error)}")
                    
                    # NO enviar respuesta - bloquear silenciosamente
                    self.logger.warning(f"🚫 Usuario {user_id} bloqueado - NO enviando respuesta")
                    return {
                        "response": "",  # Respuesta vacía = no responder
                        "followup_message": "",
                        "from_cache": False,
                        "processing_time": time.time() - start_time,
                        "tenant_id": tenant_id,
                        "session_id": session_id,
                        "intent": "malicioso",
                        "confidence": confidence,
                        "user_blocked": True,
                        "optimized": True
                    }
            except Exception as classify_error:
                print(f"❌ [CLASIFICACIÓN] ERROR EN CLASIFICACIÓN: {classify_error}")
                self.logger.error(f"❌ [CLASIFICACIÓN] ERROR EN CLASIFICACIÓN: {classify_error}")
                self.logger.exception(classify_error)
                intent = "saludo_apoyo"
                confidence = 0.5
            
            # 🚀 ENFOQUE OPTIMIZADO: Primero intenta responder con documentos si el saludo contiene una pregunta o tema informativo
            if intent == "saludo_apoyo":
                # Siempre intentar responder con documentos
                try:
                    from chatbot_ai_service.clients.gemini_client import GeminiClient
                    from chatbot_ai_service.orchestrators.rag_orchestrator import RAGOrchestrator
                    rag = RAGOrchestrator(gemini_client=GeminiClient())
                    rag_response = await rag.process_query_simple(
                        query=query,
                        tenant_id=str(tenant_id),
                        user_context=user_context,
                        tenant_config=tenant_config
                    )
                    if rag_response and isinstance(rag_response, str) and len(rag_response.strip()) > 10:
                        processing_time = time.time() - start_time
                        self.logger.info(f"✅ Respuesta informativa desde documentos ({processing_time:.4f}s)")
                        return {
                            "response": rag_response.strip(),
                            "followup_message": "",
                            "from_cache": False,
                            "processing_time": processing_time,
                            "tenant_id": tenant_id,
                            "session_id": session_id,
                            "intent": intent,
                            "confidence": confidence,
                            "user_blocked": False,
                            "optimized": True
                        }
                except Exception as e:
                    self.logger.warning(f"⚠️ RAG en saludo_apoyo falló: {e}")

                # Fallback coherente basado en branding si RAG no devuelve
                try:
                    brand_cfg = (tenant_config or {}).get("branding", {})
                    contact_name = brand_cfg.get("contactName", brand_cfg.get("contact_name", "el candidato"))
                    response = f"Hola, estoy para ayudarte en lo que necesites sobre {contact_name}. ¿Qué te gustaría saber?"
                except Exception:
                    response = "Hola, estoy para ayudarte. ¿Qué te gustaría saber?"

                processing_time = time.time() - start_time
                return {
                    "response": response,
                    "followup_message": "",
                    "from_cache": False,
                    "processing_time": processing_time,
                    "tenant_id": tenant_id,
                    "session_id": session_id,
                    "intent": intent,
                    "confidence": confidence,
                    "optimized": True
                }
            
            # 🎯 NUEVO: Manejar citas directamente (RÁPIDO)
            if intent == "cita_campaña":
                self.logger.info(f"🔍 Intent es cita_campaña - generando respuesta con IA")
                print(f"🎯 [DEBUG] Intent detectado como cita_campaña")
                
                try:
                    # Obtener configuración del tenant
                    if not tenant_config:
                        tenant_config = self._get_tenant_config(tenant_id)
                    
                    # Obtener branding y configuración
                    branding_config = tenant_config.get("branding", {}) if tenant_config else {}
                    contact_name = branding_config.get("contactName", branding_config.get("contact_name", "el candidato"))
                    
                    # Obtener link de Calendly desde DB del tenant
                    calendly_link = tenant_config.get("link_calendly", "") if tenant_config else ""
                    
                    # Generar respuesta con IA basada en si hay link disponible o no
                    if calendly_link:
                        self.logger.info(f"✅ Link de Calendly disponible: {calendly_link}")
                        # Generar respuesta con IA que incluya el link
                        prompt = f"""Eres un asistente virtual de campaña política. El usuario quiere agendar una cita.

Información:
- Candidato: {contact_name}
- Link: {calendly_link}

CRÍTICO - FORMATO EXACTO REQUERIDO:
1. Escribe máximo 2-3 oraciones cortas y completas
2. La última oración NO debe mencionar el link, solo debe ser una oración completa y terminada con punto
3. NUNCA cortes una oración a la mitad (ejemplo MALO: "el enlace que te compartimos a.")
4. Después de la última oración completa, escribe un salto de línea y luego el link
5. NO uses corchetes, NO uses "Link de Calendly:", NO uses markdown

FORMATO EXACTO A USAR:
[2-3 oraciones completas]

{calendly_link}

Ejemplo CORRECTO:
¡Claro! Te ayudo a coordinar una cita con Daniel Quintero Presidente. Es una excelente oportunidad para conocerse y hablar sobre la campaña. Puedes agendar tu espacio usando el siguiente enlace.

{calendly_link}
"""

                        response = await self._generate_quick_ai_response(prompt)
                        
                        # Post-procesamiento: limpiar enlaces truncados o corruptos
                        import re
                        # Remover patrones como [Link de Calendly: https://...] si la IA los incluyera
                        response = re.sub(r'\[Link de Calendly:?\s*', '', response)
                        response = re.sub(r'\]\s*', '', response)
                        
                        # Remover enlaces truncados (que terminan con ...)
                        response = re.sub(rf'{re.escape(calendly_link[:20])}\.\.\.', '', response)
                        response = re.sub(r'https?://[^\s]+\.\.\.', '', response)
                        
                        # Si hay duplicados del link, consolidar
                        response = re.sub(rf'{re.escape(calendly_link)}\s+{re.escape(calendly_link)}', calendly_link, response)
                        
                        # Verificar si la respuesta incluye el enlace completo
                        has_full_link = calendly_link in response
                        
                        # Limpiar espacios múltiples
                        response = re.sub(r'\s+', ' ', response).strip()
                        
                        # Asegurar que el enlace esté al final si existe, si no agregarlo
                        if has_full_link:
                            # Remover todas las ocurrencias del link del texto
                            response = response.replace(calendly_link, '')
                            response = response.strip()
                            # Agregar el link al final
                            if not response.endswith('.') and not response.endswith(':'):
                                response += "."
                            response += f"\n\n{calendly_link}"
                        else:
                            self.logger.warning(f"⚠️ La IA no incluyó el enlace. Agregándolo ahora...")
                            # Si no incluye el enlace, agregarlo al final
                            if not response.endswith('.') and not response.endswith(':'):
                                response += "."
                            response += f"\n\n{calendly_link}"
                        
                        if not response or len(response.strip()) < 10:
                            # Fallback si IA no genera buena respuesta
                            response = f"""¡Perfecto! Te ayudo a agendar una cita con alguien de la campaña.

Puedes reservar tu cita directamente aquí: {calendly_link}

En la reunión podrás conocer más sobre {contact_name}, hablar sobre oportunidades de voluntariado o coordinar actividades en tu región. Si necesitas ayuda, pregúntame."""
                    else:
                        self.logger.info(f"⚠️ Link de Calendly NO disponible para tenant {tenant_id}")
                        # Generar respuesta con IA indicando que pronto estará disponible
                        prompt = f"""Genera una respuesta natural y amigable en español para un chatbot de campaña política. El usuario quiere agendar una cita pero el sistema de citas aún no está disponible.

Información:
- Nombre del candidato: {contact_name}

Genera una respuesta breve que indique que el sistema de citas estará disponible muy pronto, pero ofreciendo alternativas como contactar por WhatsApp o esperar a que el sistema esté listo."""

                        response = await self._generate_quick_ai_response(prompt)
                        
                        if not response or len(response.strip()) < 10:
                            # Fallback si IA no genera buena respuesta
                            response = f"""¡Hola! Me alegra tu interés en agendar una cita con {contact_name}. 

El sistema de citas estará disponible muy pronto. Mientras tanto, puedes contactarnos directamente por WhatsApp o esperar a que esté listo.

¿Te gustaría que te notifique cuando el sistema de citas esté disponible?"""
                    
                    processing_time = time.time() - start_time
                    self.logger.info(f"✅ Respuesta de cita generada con IA ({processing_time:.4f}s)")
                    print(f"🎯 [CITA] Respuesta generada por IA")
                    
                    return {
                        "response": response,
                        "followup_message": "",
                        "from_cache": False,
                        "processing_time": processing_time,
                        "tenant_id": tenant_id,
                        "session_id": session_id,
                        "intent": intent,
                        "confidence": confidence,
                        "user_blocked": False,
                        "optimized": True
                    }
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Error procesando cita: {e}")
                    self.logger.exception(e)
            
            # 🎯 NUEVO: Manejar publicidad_info directamente (RÁPIDO)
            if intent == "publicidad_info":
                self.logger.info(f"🔍 Intent es publicidad_info - generando respuesta con IA")
                print(f"🎯 [DEBUG] Intent detectado como publicidad_info")
                
                try:
                    # Obtener configuración del tenant
                    if not tenant_config:
                        tenant_config = self._get_tenant_config(tenant_id)
                    
                    # Obtener branding y configuración
                    branding_config = tenant_config.get("branding", {}) if tenant_config else {}
                    contact_name = branding_config.get("contactName", branding_config.get("contact_name", "el candidato"))
                    
                    # Obtener link de Forms desde DB del tenant
                    forms_link = tenant_config.get("link_forms", "") if tenant_config else ""
                    
                    # Generar respuesta con IA basada en si hay link disponible o no
                    if forms_link:
                        self.logger.info(f"✅ Link de Forms disponible: {forms_link}")
                        # Generar respuesta con IA que incluya el link
                        prompt = f"""Eres un asistente virtual de campaña política. El usuario quiere solicitar materiales publicitarios.

Información:
- Candidato: {contact_name}
- Link: {forms_link}

CRÍTICO - FORMATO EXACTO REQUERIDO:
1. Escribe máximo 2-3 oraciones cortas y completas
2. La última oración NO debe mencionar el link, solo debe ser una oración completa y terminada con punto
3. NUNCA cortes una oración a la mitad (ejemplo MALO: "material de difusión y.")
4. Después de la última oración completa, escribe un salto de línea y luego el link
5. NO uses corchetes, NO uses "Link de Forms:", NO uses markdown
6. Asegúrate de que TODAS las oraciones estén completas antes del link

FORMATO EXACTO A USAR:
[2-3 oraciones completas]

{forms_link}

Ejemplo CORRECTO:
¡Hola! Qué excelente que quieras solicitar materiales publicitarios para la campaña de {contact_name}. En el formulario podrás solicitar folletos, material de difusión y propaganda de la campaña.

{forms_link}"""

                        response = await self._generate_quick_ai_response(prompt)
                        
                        # Post-procesamiento: limpiar enlaces truncados o corruptos
                        import re
                        
                        # Detectar y corregir oraciones cortadas antes del enlace
                        # Buscar patrones como "material de difusión y." o "material de difusión y"
                        if forms_link in response:
                            # Si el enlace está en medio, moverlo al final
                            link_pos = response.find(forms_link)
                            text_before_link = response[:link_pos].strip()
                            text_after_link = response[link_pos + len(forms_link):].strip()
                            
                            # Si hay texto antes del enlace que termina mal, corregirlo
                            if text_before_link and not text_before_link.endswith(('.', '!', '?', ':')):
                                # Buscar si la última oración está incompleta
                                last_sentence = text_before_link.split('.')[-1].strip() if '.' in text_before_link else text_before_link
                                if last_sentence and not last_sentence.endswith(('.', '!', '?')):
                                    # Completar la oración o removerla si está cortada
                                    if last_sentence.endswith(('y', 'y.', 'y,', 'y ')):
                                        # Remover la última palabra incompleta
                                        words = text_before_link.split()
                                        if words:
                                            # Remover la última palabra si es "y" o similar
                                            if words[-1].lower() in ['y', 'y.', 'y,']:
                                                words.pop()
                                            text_before_link = ' '.join(words)
                                            if text_before_link and not text_before_link.endswith(('.', '!', '?')):
                                                text_before_link += "."
                            
                            # Reconstruir respuesta: texto antes del link + link al final
                            response = text_before_link.strip()
                            if text_after_link:
                                response += " " + text_after_link.strip()
                            
                            # Asegurar que termine con punto antes del link
                            if response and not response.endswith(('.', '!', '?', ':')):
                                response += "."
                        
                        # Remover patrones como [Link de Forms: https://...] si la IA los incluyera
                        response = re.sub(r'\[Link de Forms:?\s*', '', response)
                        response = re.sub(r'\]\s*', '', response)
                        
                        # Remover enlaces truncados (que terminan con ...)
                        response = re.sub(rf'{re.escape(forms_link[:20])}\.\.\.', '', response)
                        response = re.sub(r'https?://[^\s]+\.\.\.', '', response)
                        
                        # Si hay duplicados del link, consolidar
                        response = re.sub(rf'{re.escape(forms_link)}\s+{re.escape(forms_link)}', forms_link, response)
                        
                        # Verificar si la respuesta incluye el enlace completo
                        has_full_link = forms_link in response
                        
                        # Limpiar espacios múltiples (pero mantener saltos de línea)
                        response = re.sub(r'[ \t]+', ' ', response)  # Solo espacios horizontales
                        response = re.sub(r'\n\n\n+', '\n\n', response)  # Máximo 2 saltos de línea
                        response = response.strip()
                        
                        # Asegurar que el enlace esté al final si existe, si no agregarlo
                        if has_full_link:
                            # Remover todas las ocurrencias del link del texto
                            response = response.replace(forms_link, '')
                            response = response.strip()
                            # Remover puntos o comas finales si están solos
                            response = re.sub(r'[.,]+$', '.', response)
                            # Agregar el link al final
                            if not response.endswith(('.', '!', '?', ':')):
                                response += "."
                            response += f"\n\n{forms_link}"
                        else:
                            self.logger.warning(f"⚠️ La IA no incluyó el enlace. Agregándolo ahora...")
                            # Si no incluye el enlace, agregarlo al final
                            # Asegurar que la última oración esté completa
                            if response and not response.endswith(('.', '!', '?', ':')):
                                response += "."
                            response += f"\n\nPuedes solicitar materiales publicitarios aquí: {forms_link}"
                        
                        if not response or len(response.strip()) < 10:
                            # Fallback si IA no genera buena respuesta
                            response = f"""¡Perfecto! Te ayudo a solicitar materiales publicitarios de la campaña.

Puedes solicitar materiales publicitarios aquí: {forms_link}

En el formulario podrás solicitar folletos, material de difusión y propaganda de {contact_name}. Si necesitas ayuda, pregúntame."""
                    else:
                        self.logger.info(f"⚠️ Link de Forms NO disponible para tenant {tenant_id}")
                        # Generar respuesta con IA indicando que pronto estará disponible
                        prompt = f"""Genera una respuesta natural y amigable en español para un chatbot de campaña política. El usuario quiere solicitar materiales publicitarios pero el sistema aún no está disponible.

Información:
- Nombre del candidato: {contact_name}

Genera una respuesta breve que indique que el sistema para solicitar materiales estará disponible muy pronto, pero ofreciendo alternativas como contactar por WhatsApp o esperar a que el sistema esté listo."""

                        response = await self._generate_quick_ai_response(prompt)
                        
                        if not response or len(response.strip()) < 10:
                            # Fallback si IA no genera buena respuesta
                            response = f"""¡Hola! Me alegra tu interés en solicitar materiales publicitarios de {contact_name}. 

El sistema para solicitar materiales estará disponible muy pronto. Mientras tanto, puedes contactarnos directamente por WhatsApp o esperar a que esté listo.

¿Te gustaría que te notifique cuando el sistema esté disponible?"""
                    
                    processing_time = time.time() - start_time
                    self.logger.info(f"✅ Respuesta de publicidad generada con IA ({processing_time:.4f}s)")
                    print(f"🎯 [PUBLICIDAD] Respuesta generada por IA")
                    
                    return {
                        "response": response,
                        "followup_message": "",
                        "from_cache": False,
                        "processing_time": processing_time,
                        "tenant_id": tenant_id,
                        "session_id": session_id,
                        "intent": intent,
                        "confidence": confidence,
                        "user_blocked": False,
                        "optimized": True
                    }
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Error procesando publicidad: {e}")
                    self.logger.exception(e)
            
            # 🤝 NUEVO: Manejar atencion_humano directamente (RÁPIDO)
            if intent == "atencion_humano":
                self.logger.info(f"🤝 Intent es atencion_humano - procesando solicitud de atención humana")
                print(f"🎯 [DEBUG] Intent detectado como atencion_humano")
                
                try:
                    if not tenant_config:
                        tenant_config = self._get_tenant_config(tenant_id)
                    
                    brand_cfg = tenant_config.get("branding", {})
                    
                    # Llamar al handler de atención humana
                    response = await self.base_ai_service._handle_human_assistance_request(
                        brand_cfg, tenant_config, user_context, ""
                    )
                    
                    processing_time = time.time() - start_time
                    return {
                        "response": response,
                        "followup_message": "",
                        "from_cache": False,
                        "processing_time": processing_time,
                        "tenant_id": tenant_id,
                        "session_id": session_id,
                        "intent": intent,
                        "confidence": confidence,
                        "user_blocked": False,
                        "optimized": True,
                        "needs_human_assistance": user_context.get("_needs_human_assistance", False)
                    }
                except Exception as e:
                    self.logger.warning(f"⚠️ Error procesando atencion_humano: {e}")
                    self.logger.exception(e)
            
            # 🎯 NUEVO: Manejar actualizacion_datos directamente (RÁPIDO)
            if intent == "actualizacion_datos":
                self.logger.info(f"🔍 Intent es actualizacion_datos - llamando al handler específico")
                print(f"🎯 [DEBUG] Intent detectado como actualizacion_datos")
                
                try:
                    # Obtener configuración del tenant
                    if not tenant_config:
                        tenant_config = self._get_tenant_config(tenant_id)
                    
                    # Llamar al handler del base_ai_service que maneja actualizacion_datos
                    self.logger.info(f"📞 Llamando a _handle_data_update_request desde optimized service")
                    result = await self.base_ai_service._handle_data_update_request(
                        query, user_context, "", tenant_id=tenant_id
                    )
                    
                    # El método retorna (response_message, update_data_dict)
                    if isinstance(result, tuple):
                        response, update_data = result
                        # Guardar datos para que Java los procese
                        if update_data:
                            user_context["data_to_update"] = update_data
                            self.logger.info(f"📝 Datos para actualizar: {update_data}")
                        
                        processing_time = time.time() - start_time
                        self.logger.info(f"✅ Respuesta de actualización generada ({processing_time:.4f}s)")
                        
                        return {
                            "response": response,
                            "followup_message": "",
                            "from_cache": False,
                            "processing_time": processing_time,
                            "tenant_id": tenant_id,
                            "session_id": session_id,
                            "intent": intent,
                            "confidence": confidence,
                            "user_blocked": False,
                            "optimized": True,
                            "data_to_update": update_data  # Incluir datos para Java
                        }
                    else:
                        # Fallback si no retorna tupla
                        return {
                            "response": result if result else "Entiendo que quieres actualizar datos. Por favor, especifica qué información deseas cambiar.",
                            "followup_message": "",
                            "from_cache": False,
                            "processing_time": time.time() - start_time,
                            "tenant_id": tenant_id,
                            "session_id": session_id,
                            "intent": intent,
                            "confidence": confidence,
                            "optimized": True
                        }
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Error procesando actualizacion_datos: {e}")
                    self.logger.exception(e)
            
            # 🎯 NUEVO: Manejar colaboracion_voluntariado directamente (RÁPIDO)
            if intent == "colaboracion_voluntariado":
                self.logger.info(f"🔍 Intent es colaboracion_voluntariado - generando respuesta con opciones de área")
                print(f"🎯 [DEBUG] Intent detectado como colaboracion_voluntariado")
                
                try:
                    # Obtener configuración del tenant
                    if not tenant_config:
                        tenant_config = self._get_tenant_config(tenant_id)
                    
                    # Obtener branding y configuración
                    branding_config = tenant_config.get("branding", {}) if tenant_config else {}
                    contact_name = branding_config.get("contactName", branding_config.get("contact_name", "el candidato"))
                    
                    # Generar respuesta con opciones de colaboración
                    response = f"""¡Excelente que quieras apoyarnos! {contact_name} valora mucho la colaboración de personas comprometidas como tú.

¿En qué área te gustaría colaborar?

1. Redes sociales
2. Comunicaciones
3. Temas programáticos
4. Logística
5. Temas jurídicos
6. Trabajo territorial
7. Día de elecciones
8. Call center
9. Otro (¿cuál?)

Elige una opción o cuéntame directamente en qué te gustaría ayudar."""
                    
                    processing_time = time.time() - start_time
                    self.logger.info(f"✅ Respuesta de colaboracion generada ({processing_time:.4f}s)")
                    print(f"🎯 [COLABORACION] Respuesta generada")
                    
                    return {
                        "response": response,
                        "followup_message": "",
                        "from_cache": False,
                        "processing_time": processing_time,
                        "tenant_id": tenant_id,
                        "session_id": session_id,
                        "intent": intent,
                        "confidence": confidence,
                        "user_blocked": False,
                        "optimized": True
                    }
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Error procesando colaboracion: {e}")
                    self.logger.exception(e)
            
            # 🎯 NUEVO: Manejar selección de área de colaboración (RÁPIDO)
            if intent == "area_colaboracion_select":
                self.logger.info(f"🔍 Intent es area_colaboracion_select - confirmando selección de área")
                print(f"🎯 [DEBUG] Intent detectado como area_colaboracion_select")
                
                try:
                    # Obtener configuración del tenant
                    if not tenant_config:
                        tenant_config = self._get_tenant_config(tenant_id)
                    
                    # Obtener branding y configuración
                    branding_config = tenant_config.get("branding", {}) if tenant_config else {}
                    contact_name = branding_config.get("contactName", branding_config.get("contact_name", "el candidato"))
                    
                    # Extraer el área de colaboración del mensaje
                    area = self._extract_collaboration_area(query)
                    self.logger.info(f"🔍 Área extraída del mensaje: '{area}'")
                    print(f"🔍 [AREA_SELECT] Área extraída: '{area}'")
                    
                    # Mapear el área a formato consistente
                    area_mapped = self._map_collaboration_area(area)
                    self.logger.info(f"🔍 Área mapeada para BD: '{area_mapped}'")
                    print(f"🔍 [AREA_SELECT] Área mapeada: '{area_mapped}'")
                    
                    # Generar respuesta de confirmación
                    response = f"""¡Perfecto! Has seleccionado: **{area.title()}**

Tu información ha sido registrada. {contact_name} y el equipo de campaña estarán en contacto contigo pronto para coordinar tu participación en esta área.

¡Gracias por tu compromiso y por querer ser parte del cambio! 🙌"""
                    
                    processing_time = time.time() - start_time
                    self.logger.info(f"✅ Respuesta de confirmación de área generada ({processing_time:.4f}s)")
                    print(f"🎯 [AREA_SELECT] Respuesta generada para área: {area_mapped}")
                    self.logger.info(f"🎯 [AREA_SELECT] Enviando collaboration_area: '{area_mapped}' en respuesta")
                    print(f"🎯 [AREA_SELECT] collaboration_area que se enviará: '{area_mapped}'")
                    
                    return {
                        "response": response,
                        "followup_message": "",
                        "from_cache": False,
                        "processing_time": processing_time,
                        "tenant_id": tenant_id,
                        "session_id": session_id,
                        "intent": intent,
                        "confidence": confidence,
                        "user_blocked": False,
                        "optimized": True,
                        "collaboration_area": area_mapped  # Información extra para que Java actualice el usuario
                    }
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Error procesando selección de área: {e}")
                    self.logger.exception(e)
            
            # 🎯 NUEVO: Manejar quejas directamente (RÁPIDO)
            if intent == "quejas":
                self.logger.info(f"🔍 Intent es quejas - generando respuesta solicitando más detalles")
                print(f"🎯 [DEBUG] Intent detectado como quejas")
                
                try:
                    # Obtener configuración del tenant
                    if not tenant_config:
                        tenant_config = self._get_tenant_config(tenant_id)
                    
                    # Obtener branding y configuración
                    branding_config = tenant_config.get("branding", {}) if tenant_config else {}
                    contact_name = branding_config.get("contactName", branding_config.get("contact_name", "el candidato"))
                    
                    # Generar respuesta solicitando más detalles
                    response = f"""Entiendo que tienes una inquietud o queja. Tu opinión es muy importante para {contact_name} y queremos ayudarte.

Por favor, compárteme más detalles sobre tu queja o reclamo. Puedes contarme:
• ¿Qué sucedió?
• ¿Cuándo pasó?
• ¿Quién estuvo involucrado?

Describe tu situación y con gusto te ayudaré a resolverla o la transmitiré al equipo correspondiente."""
                    
                    processing_time = time.time() - start_time
                    self.logger.info(f"✅ Respuesta de quejas generada ({processing_time:.4f}s)")
                    print(f"🎯 [QUEJAS] Respuesta generada")
                    
                    return {
                        "response": response,
                        "followup_message": "",
                        "from_cache": False,
                        "processing_time": processing_time,
                        "tenant_id": tenant_id,
                        "session_id": session_id,
                        "intent": intent,
                        "confidence": confidence,
                        "user_blocked": False,
                        "optimized": True
                    }
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Error procesando quejas: {e}")
                    self.logger.exception(e)
            
            # 🎯 NUEVO: Manejar queja_detalle_select (RÁPIDO)
            print(f"🎯 [DEBUG PRE-QUEJA_DETALLE] Intent: '{intent}', ¿Es queja_detalle_select? {intent == 'queja_detalle_select'}")
            if intent == "queja_detalle_select":
                self.logger.info(f"🔍 Intent es queja_detalle_select - confirmando registro de queja")
                print(f"🎯 [DEBUG] Intent detectado como queja_detalle_select - ENTRANDO AL BLOQUE")
                
                try:
                    # Obtener configuración del tenant
                    if not tenant_config:
                        tenant_config = self._get_tenant_config(tenant_id)
                    
                    # Obtener branding y configuración
                    branding_config = tenant_config.get("branding", {}) if tenant_config else {}
                    contact_name = branding_config.get("contactName", branding_config.get("contact_name", "el candidato"))
                    
                    # Generar respuesta de confirmación
                    response = f"""Gracias por compartir los detalles de tu queja o reclamo. He registrado la información y la he enviado al equipo correspondiente de la campaña.

{contact_name} y su equipo tomarán cartas en el asunto para resolver tu inquietud lo antes posible.

Tu opinión es muy valiosa para nosotros. ¿Hay algo más en lo que pueda ayudarte?"""
                    
                    processing_time = time.time() - start_time
                    self.logger.info(f"✅ Respuesta de confirmación de queja generada ({processing_time:.4f}s)")
                    print(f"🎯 [QUEJA_DETALLE] Respuesta generada")
                    
                    # 🎯 Clasificar el tipo de queja basándose en el contenido del mensaje
                    complaint_type = self._classify_complaint_type(query)
                    
                    result_dict = {
                        "response": response,
                        "followup_message": "",
                        "from_cache": False,
                        "processing_time": processing_time,
                        "tenant_id": tenant_id,
                        "session_id": session_id,
                        "intent": intent,
                        "confidence": confidence,
                        "user_blocked": False,
                        "optimized": True,
                        "complaint_registered": True,  # Información extra para que Java sepa que se registró la queja
                        "complaint_type": complaint_type  # Tipo de queja (servicio, atencion, tecnica, lentitud, etc.)
                    }
                    
                    print(f"🎯 [QUEJA_DETALLE] RESULTADO FINAL: {result_dict}")
                    self.logger.info(f"🎯 [QUEJA_DETALLE] Keys en resultado: {list(result_dict.keys())}")
                    self.logger.info(f"🎯 [QUEJA_DETALLE] complaint_registered: {result_dict.get('complaint_registered')}")
                    self.logger.info(f"🎯 [QUEJA_DETALLE] complaint_type: {complaint_type}")
                    
                    return result_dict
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Error procesando queja_detalle: {e}")
                    self.logger.exception(e)
            
            # 3. PROCESAR CON SERVICIO BASE (con timeout)
            self.logger.info(f"📚 [OPTIMIZED] Procesando con servicio base...")
            import asyncio
            
            # 🔧 FIX: Pasar historial en user_context en lugar de incluirlo en el query
            processing_user_context = user_context.copy() if user_context else {}
            processing_query = query
            
            if conversation_history:
                # Agregar historial al contexto para que esté disponible en el prompt
                processing_user_context['conversation_history'] = conversation_history
                self.logger.info(f"📚 [OPTIMIZED] Agregando historial al user_context (NO al query)")
                self.logger.info(f"📚 [OPTIMIZED] Query puro: '{query}'")
            
            # 🔍 DEBUG CRÍTICO: Ver qué tenant_config vamos a pasar a base_ai_service
            self.logger.info(f"🔍 [OPTIMIZED] PREPARANDO para llamar a base_ai_service con tenant_config keys: {list(tenant_config.keys()) if tenant_config else 'None'}")
            if tenant_config and 'numero_whatsapp' in tenant_config:
                self.logger.info(f"✅ [OPTIMIZED] numero_whatsapp VA A PASARSE A base_ai_service: '{tenant_config['numero_whatsapp']}'")
            else:
                self.logger.warning(f"❌ [OPTIMIZED] numero_whatsapp NO VA A PASARSE A base_ai_service")
            
            try:
                result = await asyncio.wait_for(
                    self.base_ai_service.process_chat_message(
                        tenant_id, processing_query, processing_user_context, session_id, tenant_config
                    ),
                    timeout=optimization_config.AI_RESPONSE_TIMEOUT
                )
                
                # Agregar información de optimización al resultado
                result["intent"] = intent
                result["confidence"] = confidence
                result["optimized"] = True
                
                processing_time = time.time() - start_time
                result["processing_time"] = processing_time
                
                self.logger.info(f"✅ [OPTIMIZED] Procesamiento completado en {processing_time:.2f}s")
                self.logger.info(f"✅ [OPTIMIZED] INTENT FINAL: {intent} (confianza: {confidence})")
                
                return result
                
            except asyncio.TimeoutError:
                self.logger.error(f"⏰ Timeout generando respuesta (>10s) - retornando menú")
                # Retornar señal de timeout para que Java muestre menú
                processing_time = time.time() - start_time
                return {
                    "response": "",
                    "followup_message": "",
                    "from_cache": False,
                    "processing_time": processing_time,
                    "timeout": True,
                    "show_menu": True,
                    "menu_options": [
                        {"text": "¿Cómo voy?", "payload": "como_voy"},
                        {"text": "Compartir mi link", "payload": "compartir_link"}
                    ],
                    "tenant_id": tenant_id,
                    "session_id": session_id,
                    "intent": intent,
                    "confidence": confidence,
                    "optimized": True
                }
            
        except Exception as e:
            self.logger.error(f"❌ [OPTIMIZED] Error en procesamiento optimizado: {str(e)}")
            self.logger.error(f"❌ [OPTIMIZED] Traceback: {e}", exc_info=True)
            
            # Fallback al servicio base
            self.logger.info(f"🔄 [OPTIMIZED] Fallback al servicio base...")
            try:
                result = await self.base_ai_service.process_chat_message(
                    tenant_id, query, user_context, session_id, tenant_config
                )
                result["optimized"] = False  # Marcar como no optimizado
                return result
            except Exception as fallback_error:
                self.logger.error(f"❌ [OPTIMIZED] Error en fallback: {str(fallback_error)}")
                # Si todo falla, mostrar menú
                processing_time = time.time() - start_time
                return {
                    "response": "",
                    "followup_message": "",
                    "from_cache": False,
                    "processing_time": processing_time,
                    "timeout": True,
                    "show_menu": True,
                    "menu_options": [
                        {"text": "¿Cómo voy?", "payload": "como_voy"},
                        {"text": "Compartir mi link", "payload": "compartir_link"}
                    ],
                    "tenant_id": tenant_id,
                    "session_id": session_id,
                    "optimized": True
                }
    
    def _extract_collaboration_area(self, message: str) -> str:
        """Extrae el área de colaboración del mensaje del usuario"""
        message_lower = message.lower().strip()
        
        # Mapeo de patrones a áreas
        area_patterns = {
            "redes sociales": ["redes sociales", "redes", "1"],
            "comunicaciones": ["comunicaciones", "2"],
            "temas programáticos": ["temas programáticos", "programaticos", "3"],
            "logística": ["logistica", "logística", "4"],
            "temas jurídicos": ["temas jurídicos", "juridicos", "5"],
            "trabajo territorial": ["trabajo territorial", "territorial", "6"],
            "día de elecciones": ["dia de elecciones", "elecciones", "7"],
            "call center": ["call center", "callcenter", "8"],
            "otro": ["otro", "otra", "9"]
        }
        
        # Buscar coincidencias
        for area, patterns in area_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    return area
        
        # Si no encuentra nada específico, retornar el mensaje original
        return message.strip()
    
    def _map_collaboration_area(self, area: str) -> str:
        """Mapea el área a un formato consistente para la base de datos"""
        area_lower = area.lower().strip()
        
        # Mapeo a formato snake_case
        mapping = {
            "redes sociales": "redes_sociales",
            "comunicaciones": "comunicaciones",
            "temas programáticos": "temas_programaticos",
            "logística": "logistica",
            "logistica": "logistica",
            "temas jurídicos": "temas_juridicos",
            "juridicos": "temas_juridicos",
            "trabajo territorial": "trabajo_territorial",
            "territorial": "trabajo_territorial",
            "día de elecciones": "dia_elecciones",
            "elecciones": "dia_elecciones",
            "call center": "call_center",
            "callcenter": "call_center",
            "otro": "otro"
        }
        
        return mapping.get(area_lower, "otro")
    
    def _get_tenant_config(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene configuración del tenant"""
        try:
            from chatbot_ai_service.services.configuration_service import configuration_service
            config = configuration_service.get_tenant_config(tenant_id)
            if config:
                self.logger.info(f"✅ Configuración obtenida para tenant {tenant_id}")
            else:
                self.logger.warning(f"⚠️ No se encontró configuración para tenant {tenant_id}")
            return config
        except Exception as e:
            self.logger.error(f"Error obteniendo configuración del tenant {tenant_id}: {str(e)}")
            return None
    
    
    async def _classify_intent_optimized(self, tenant_id: str, query: str, 
                                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Clasifica intención de forma optimizada"""
        try:
            self.logger.info(f"🎯 [CLASIFICACIÓN] Iniciando clasificación para: '{query[:50]}...'")
            self.logger.info(f"🎯 [CLASIFICACIÓN] Tenant ID: {tenant_id}")
            
            # Usar el método de clasificación del servicio base
            result = await self.base_ai_service.classify_intent(tenant_id, query, user_context)
            
            if result and result.get("category"):
                self.logger.info(f"✅ [CLASIFICACIÓN] Clasificación exitosa: {result['category']} (confianza: {result.get('confidence', 0):.2f})")
                return result
            else:
                self.logger.warning("⚠️ [CLASIFICACIÓN] Clasificación falló, usando fallback")
                return {"category": "saludo_apoyo", "confidence": 0.5}
                
        except Exception as e:
            self.logger.error(f"❌ [CLASIFICACIÓN] Error en clasificación: {str(e)}")
            return {"category": "saludo_apoyo", "confidence": 0.5}
    
    def _create_error_response(self, error_message: str, start_time: float) -> Dict[str, Any]:
        """Crea respuesta de error"""
        return {
            "response": f"Lo siento, {error_message.lower()}.",
            "followup_message": "",
            "processing_time": time.time() - start_time,
            "error": error_message,
            "optimized": True
        }
    
    async def _generate_quick_ai_response(self, prompt: str) -> str:
        """Genera respuesta rápida con IA usando Gemini directamente"""
        try:
            print(f"🔍 DEBUG: _generate_quick_ai_response - Iniciando")
            import time as time_module
            start_gen = time_module.time()
            
            # Usar directamente el modelo Gemini del base_ai_service
            if hasattr(self.base_ai_service, 'model') and self.base_ai_service.model:
                response_obj = self.base_ai_service.model.generate_content(prompt)
                response = response_obj.text.strip()
            else:
                # Fallback: generar respuesta simple
                response = "¡Hola! Bienvenido a la campaña. ¿En qué puedo ayudarte?"
            
            elapsed = time_module.time() - start_gen
            print(f"🔍 DEBUG: _generate_quick_ai_response - Completado en {elapsed:.2f}s")
            
            if response:
                # Limitar longitud
                response = response.strip()
                if len(response) > 250:
                    last_space = response[:250].rfind(' ')
                    if last_space > 200:
                        response = response[:last_space]
                    else:
                        response = response[:247] + "..."
            
            return response if response else ""
            
        except Exception as e:
            print(f"🔍 DEBUG: _generate_quick_ai_response - ERROR: {e}")
            self.logger.warning(f"⚠️ Error generando con IA: {e}")
            return ""
    
    def _classify_complaint_type(self, message: str) -> str:
        """Clasifica el tipo de queja basándose en el contenido del mensaje"""
        message_lower = message.lower()
        
        # Tipo 1: Lentitud / demoras
        if any(word in message_lower for word in ["demorado", "lento", "tarda", "demasiado", "tardío", "retrasado"]):
            return "lentitud"
        
        # Tipo 2: Mala atención
        if any(phrase in message_lower for phrase in ["mala atención", "pésima atención", "horrible atención", "no hay buena atención", "atención deficiente"]):
            return "atencion"
        
        # Tipo 3: Problemas técnicos
        if any(word in message_lower for word in ["no funciona", "no sirve", "error", "bug", "falla", "técnico"]):
            return "tecnica"
        
        # Tipo 4: Calidad del servicio
        if any(phrase in message_lower for phrase in ["mal servicio", "servicio malo", "no se presta", "no presta", "pésimo servicio", "horrible servicio"]):
            return "servicio"
        
        # Tipo 5: Problemas generales (fallback)
        if any(word in message_lower for word in ["malo", "mala", "mal", "deficiente", "terrible", "horrible", "pésimo", "inadecuado"]):
            return "general"
        
        # Por defecto
        return "general"

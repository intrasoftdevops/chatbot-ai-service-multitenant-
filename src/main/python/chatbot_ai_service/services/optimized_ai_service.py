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
            if not tenant_config:
                self.logger.warning(f"⚠️ No se recibió tenant_config en el request, obteniendo desde servicio Java...")
                tenant_config = self._get_tenant_config(tenant_id)
                if not tenant_config:
                    return self._create_error_response("Tenant no encontrado", start_time)
            
            # 2. CLASIFICAR INTENCIÓN
            print(f"🎯 [OPTIMIZED] Clasificando intención...")
            self.logger.info(f"🎯 [OPTIMIZED] Clasificando intención...")
            try:
                intent_result = await self._classify_intent_optimized(tenant_id, query, user_context)
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
                    # user_id ya contiene el teléfono con + (ej: +573227281752)
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
            
            # 🚀 ENFOQUE OPTIMIZADO: Variaciones pre-generadas para saludos (RÁPIDO)
            # Si es saludo, usar variaciones precargadas desde DB
            if intent == "saludo_apoyo":
                self.logger.info(f"🔍 Intent es saludo_apoyo - usando variaciones pre-generadas")
                print(f"🎯 [DEBUG] Intent detectado como saludo_apoyo")
                print(f"🎯 [DEBUG] Tenants en cache: {list(OptimizedAIService._prompts_cache.keys())}")
                try:
                    # Obtener variaciones desde el cache global
                    cache_key = f'{tenant_id}_welcome_variations'
                    variations = OptimizedAIService._prompts_cache.get(cache_key, [])
                    print(f"🎯 [DEBUG] Cache key: {cache_key}")
                    print(f"🎯 [DEBUG] Variaciones encontradas: {len(variations)}")
                    print(f"🎯 [DEBUG] Variaciones: {variations}")
                    
                    if variations and len(variations) > 0:
                        # Seleccionar una variación aleatoria
                        import random
                        selected_response = random.choice(variations)
                        
                        # Limpiar números al inicio (ej: "2: texto" -> "texto")
                        import re
                        selected_response = re.sub(r'^\d+:\s*', '', selected_response).strip()
                        
                        # Personalizar con nombre del usuario si está disponible
                        session_context = user_context.get('session_context', {})
                        user_name = session_context.get('user_name') or session_context.get('name') or ""
                        
                        if user_name and "{user_name}" in selected_response:
                            selected_response = selected_response.replace("{user_name}", user_name)
                        
                        processing_time = time.time() - start_time
                        self.logger.info(f"✅ Respuesta desde variaciones pre-generadas ({processing_time:.4f}s)")
                        print(f"🎯 [SALUDO] Variación seleccionada: {selected_response[:100]}")
                        return {
                            "response": selected_response,
                            "followup_message": "",
                            "from_cache": True,
                            "processing_time": processing_time,
                            "tenant_id": tenant_id,
                            "session_id": session_id,
                            "intent": intent,
                            "confidence": confidence,
                            "user_blocked": False,
                            "optimized": True
                        }
                    else:
                        # Fallback si no hay variaciones
                        self.logger.warning(f"⚠️ No hay variaciones para tenant {tenant_id}")
                        return {
                            "response": "¡Hola! Bienvenido a la campaña. ¿En qué puedo ayudarte?",
                            "followup_message": "",
                            "from_cache": False,
                            "processing_time": 0.001,
                            "tenant_id": tenant_id,
                            "session_id": session_id,
                            "intent": intent,
                            "confidence": confidence,
                            "optimized": True
                        }
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Error procesando saludo: {e}")
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

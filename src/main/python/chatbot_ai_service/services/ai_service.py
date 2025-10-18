"""
Servicio de IA simplificado para el Chatbot AI Service

Este servicio se enfoca únicamente en procesamiento de IA y recibe
la configuración del proyecto Political Referrals via HTTP.
"""
import logging
import time
import os
from typing import Dict, Any, Optional, List

import google.generativeai as genai
import httpx
from chatbot_ai_service.services.configuration_service import configuration_service
from chatbot_ai_service.services.document_context_service import document_context_service
from chatbot_ai_service.services.session_context_service import session_context_service
from chatbot_ai_service.services.blocking_notification_service import BlockingNotificationService
from chatbot_ai_service.services.cache_service import cache_service

logger = logging.getLogger(__name__)

class AIService:
    """Servicio de IA simplificado - solo procesamiento de IA"""
    
    def __init__(self):
        self.model = None
        self._initialized = False
        # Servicio para notificar bloqueos
        self.blocking_notification_service = BlockingNotificationService()
        # Configurar URL del servicio Java desde variable de entorno
        java_service_url = os.getenv("POLITICAL_REFERRALS_SERVICE_URL")
        if java_service_url:
            self.blocking_notification_service.set_java_service_url(java_service_url)
        else:
            logger.warning("POLITICAL_REFERRALS_SERVICE_URL no configurado - funcionalidad de bloqueo limitada")
        
        # 🚀 FASE 1: Feature flag para usar GeminiClient
        # Permite migración gradual sin romper funcionalidad existente
        self.use_gemini_client = os.getenv("USE_GEMINI_CLIENT", "f").lower() == "true"
        self.gemini_client = None
        
        if self.use_gemini_client:
            try:
                from chatbot_ai_service.clients.gemini_client import GeminiClient
                self.gemini_client = GeminiClient()
                logger.info("✅ GeminiClient habilitado via feature flag USE_GEMINI_CLIENT=true")
            except Exception as e:
                logger.error(f"❌ Error inicializando GeminiClient: {e}")
                logger.warning("⚠️ Usando lógica original de AIService como fallback")
                self.use_gemini_client = False
        
        # 🚀 FASE 2: Feature flag para usar configuraciones avanzadas por tarea
        # Permite optimizar temperatura, top_p, etc. según el tipo de tarea
        self.use_advanced_model_configs = os.getenv("USE_ADVANCED_MODEL_CONFIGS", "false").lower() == "true"
        
        if self.use_advanced_model_configs and self.use_gemini_client:
            logger.info("✅ Configuraciones avanzadas de modelo habilitadas (USE_ADVANCED_MODEL_CONFIGS=true)")
        elif self.use_advanced_model_configs and not self.use_gemini_client:
            logger.warning("⚠️ USE_ADVANCED_MODEL_CONFIGS=true pero USE_GEMINI_CLIENT=false. Las configs avanzadas requieren GeminiClient.")
            self.use_advanced_model_configs = False
        
        # 🚀 FASE 6: Feature flag para usar RAGOrchestrator
        # Habilita el sistema completo de RAG con búsqueda híbrida y verificación
        self.use_rag_orchestrator = os.getenv("USE_RAG_ORCHESTRATOR", "false").lower() == "true"
        self.rag_orchestrator = None
        
        # 🛡️ FASE 5: Feature flag para guardrails estrictos
        # Habilita prompts especializados y verificación estricta de respuestas
        self.use_guardrails = os.getenv("USE_GUARDRAILS", "true").lower() == "true"
        self.strict_guardrails = os.getenv("STRICT_GUARDRAILS", "true").lower() == "true"
        
        if self.use_rag_orchestrator:
            if not self.use_gemini_client:
                logger.warning("⚠️ USE_RAG_ORCHESTRATOR=true pero USE_GEMINI_CLIENT=false. RAG requiere GeminiClient.")
                self.use_rag_orchestrator = False
            else:
                try:
                    from chatbot_ai_service.orchestrators.rag_orchestrator import RAGOrchestrator
                    self.rag_orchestrator = RAGOrchestrator(
                        gemini_client=self.gemini_client,
                        document_service=document_context_service,
                        enable_verification=True,
                        enable_citations=True,
                        enable_guardrails=self.use_guardrails,
                        strict_guardrails=self.strict_guardrails
                    )
                    logger.info(
                        f"✅ RAGOrchestrator habilitado (USE_RAG_ORCHESTRATOR=true) "
                        f"con guardrails={'ON' if self.use_guardrails else 'OFF'}"
                    )
                except Exception as e:
                    logger.error(f"❌ Error inicializando RAGOrchestrator: {e}")
                    logger.warning("⚠️ Usando lógica original sin RAG")
                    self.use_rag_orchestrator = False
        
        # 📊 Log resumen de features activadas
        features_status = {
            "GeminiClient": "✅" if self.use_gemini_client else "❌",
            "Advanced Configs": "✅" if self.use_advanced_model_configs else "❌",
            "RAG Orchestrator": "✅" if self.use_rag_orchestrator else "❌",
            "Guardrails": "✅" if self.use_guardrails else "❌",
            "Strict Guardrails": "✅" if self.strict_guardrails else "❌"
        }
        logger.info(f"🎛️ AIService inicializado | Features: {features_status}")
        
        # 🚀 OPTIMIZACIÓN: Pre-inicializar modelo para reducir cold start
        self._pre_warm_model()
    
    def _pre_warm_model(self):
        """Pre-calienta el modelo para reducir latencia en primera respuesta"""
        try:
            logger.info("🔥 Pre-calentando modelo Gemini...")
            self._ensure_model_initialized()
            if self.model:
                # Hacer una llamada simple para "despertar" el modelo
                test_prompt = "Responde solo: OK"
                self.model.generate_content(test_prompt)
                logger.info("✅ Modelo pre-calentado exitosamente")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo pre-calentar el modelo: {e}")
            # No es crítico, el modelo se inicializará en la primera llamada real
    
    def _get_fallback_response(self, prompt: str) -> str:
        """Genera respuesta de fallback inteligente sin usar IA"""
        # Analizar el prompt para dar respuesta contextual
        prompt_lower = prompt.lower()
        
        if "nombre" in prompt_lower or "llamo" in prompt_lower:
            return "Por favor, comparte tu nombre completo para continuar con el registro."
        elif "ciudad" in prompt_lower or "vives" in prompt_lower:
            return "¿En qué ciudad vives? Esto nos ayuda a conectar con promotores de tu región."
        elif "apellido" in prompt_lower:
            return "Perfecto, ahora necesito tu apellido para completar tu información."
        elif "código" in prompt_lower or "referido" in prompt_lower:
            return "Si tienes un código de referido, compártelo. Si no, escribe 'no' para continuar."
        elif "términos" in prompt_lower or "condiciones" in prompt_lower:
            return "¿Aceptas los términos y condiciones? Responde 'sí' o 'no'."
        elif "confirmar" in prompt_lower or "correcto" in prompt_lower:
            return "¿Confirmas que esta información es correcta? Responde 'sí' o 'no'."
        else:
            return "Gracias por tu mensaje. Te ayudo a completar tu registro paso a paso."
    
    async def _generate_intelligent_response_without_documents(self, query: str, user_context: Dict[str, Any], 
                                                           branding_config: Dict[str, Any], tenant_config: Dict[str, Any]) -> str:
        """Genera una respuesta inteligente cuando no hay documentos disponibles"""
        try:
            contact_name = branding_config.get("contactName", "el candidato")
            
            # Analizar la consulta para dar una respuesta contextual
            query_lower = query.lower()
            
            if "aguas vivas" in query_lower:
                return f"¡Excelente pregunta! {contact_name} tiene propuestas específicas sobre el manejo del agua y recursos hídricos. Te puedo ayudar a conectarte con nuestro equipo para obtener información detallada sobre estas propuestas. ¿Te gustaría que te contacte alguien del equipo?"
            
            elif "cuándo inicia" in query_lower or "cuando inicia" in query_lower or "inicia la campaña" in query_lower:
                return f"La campaña de {contact_name} está en marcha y trabajando activamente. Te puedo ayudar a conectarte con nuestro equipo para obtener información actualizada sobre las actividades y eventos de la campaña. ¿Te gustaría recibir información sobre próximos eventos?"
            
            elif any(word in query_lower for word in ["propuesta", "propone", "plan", "planes", "política", "políticas"]):
                return f"{contact_name} tiene propuestas específicas en diferentes áreas. Te puedo ayudar a conectarte con nuestro equipo para obtener información detallada sobre las propuestas que más te interesen. ¿Hay algún tema específico que te gustaría conocer?"
            
            elif any(word in query_lower for word in ["experiencia", "trayectoria", "historial", "antecedentes"]):
                return f"{contact_name} tiene una amplia experiencia y trayectoria. Te puedo ayudar a conectarte con nuestro equipo para obtener información detallada sobre su experiencia y antecedentes. ¿Te gustaría recibir información específica sobre algún área?"
            
            else:
                return f"Hola! Soy el asistente virtual de la campaña de {contact_name}. Te puedo ayudar con información sobre la campaña y conectarte con nuestro equipo para resolver tus consultas específicas. ¿Hay algo en particular que te gustaría saber?"
                
        except Exception as e:
            logger.error(f"Error generando respuesta inteligente: {str(e)}")
            return f"Hola! Soy el asistente virtual de la campaña de {branding_config.get('contactName', 'el candidato')}. ¿En qué puedo ayudarte?"

    def _get_general_fallback_response(self, prompt: str, tenant_config: dict = None) -> str:
        """Genera respuesta de fallback para conversaciones generales (usuarios registrados)"""
        prompt_lower = prompt.lower()
        
        # Obtener información del tenant para respuestas personalizadas
        contact_name = "el candidato"
        if tenant_config and tenant_config.get("branding", {}).get("contact_name"):
            contact_name = tenant_config["branding"]["contact_name"]
        
        # Categorías de respuestas de fallback
        if any(word in prompt_lower for word in ["hola", "hi", "hello", "buenos días", "buenas tardes"]):
            return f"¡Hola! Soy el asistente de {contact_name}. ¿En qué puedo ayudarte hoy?"
        
        elif any(word in prompt_lower for word in ["cómo", "como", "funciona", "trabaja"]):
            return f"Te explico cómo funciona: Somos la campaña de {contact_name}. Puedes registrarte como promotor, ganar puntos por referir personas y participar en nuestro ranking. ¿Te gustaría registrarte?"
        
        elif any(word in prompt_lower for word in ["puntos", "puntaje", "ranking", "posición"]):
            return "Los puntos se ganan refiriendo personas a la campaña. Cada referido te da puntos que se suman a tu ranking. ¡Mientras más refieras, más alto estás en la lista!"
        
        elif any(word in prompt_lower for word in ["referir", "referido", "invitar", "compartir"]):
            return "Para referir personas, comparte tu código único con amigos y familiares. Cuando se registren con tu código, ambos ganan puntos. ¡Es muy fácil!"
        
        elif any(word in prompt_lower for word in ["código", "mi código", "código personal"]):
            return "Tu código personal es único y te identifica como promotor. Lo puedes compartir con otras personas para que se registren y ambos ganen puntos."
        
        elif any(word in prompt_lower for word in ["premio", "ganar", "ganancia", "recompensa"]):
            return "Los promotores más activos pueden ganar premios y reconocimientos especiales. ¡Mientras más personas refieras, más oportunidades tienes de ganar!"
        
        elif any(word in prompt_lower for word in ["ayuda", "help", "soporte", "problema"]):
            return f"Estoy aquí para ayudarte. Puedo explicarte cómo funciona la campaña, ayudarte con tu registro, o resolver dudas sobre puntos y referidos. ¿Qué necesitas saber?"
        
        elif any(word in prompt_lower for word in ["horario", "hora", "cuándo", "cuando", "disponible"]):
            return "Estoy disponible 24/7 para ayudarte. Puedes escribirme en cualquier momento y te responderé lo más pronto posible."
        
        elif any(word in prompt_lower for word in ["contacto", "teléfono", "telefono", "email", "correo"]):
            return f"Para contacto directo, puedes comunicarte con el equipo de {contact_name}. También puedes seguirnos en nuestras redes sociales oficiales."
        
        elif any(word in prompt_lower for word in ["gracias", "thank", "thanks", "agradecido"]):
            return f"¡De nada! Es un placer ayudarte. Recuerda que puedes escribirme cuando necesites ayuda con la campaña de {contact_name}."
        
        elif any(word in prompt_lower for word in ["adiós", "adios", "bye", "hasta luego", "nos vemos"]):
            return f"¡Hasta luego! Fue un gusto ayudarte. ¡Que tengas un excelente día y sigue promoviendo la campaña de {contact_name}!"
        
        elif any(word in prompt_lower for word in ["información", "info", "datos", "sobre"]):
            return f"Te puedo ayudar con información sobre la campaña de {contact_name}, cómo ganar puntos, referir personas, y todo lo relacionado con ser promotor. ¿Qué te interesa saber?"
        
        elif any(word in prompt_lower for word in ["registro", "registrarme", "unirme", "participar"]):
            return "¡Excelente! Para registrarte como promotor, necesito algunos datos básicos: tu nombre completo, ciudad donde vives, y si tienes un código de referido. ¿Empezamos?"
        
        elif any(word in prompt_lower for word in ["estado", "mi estado", "progreso", "avance"]):
            return "Para ver tu estado actual, puntos y posición en el ranking, necesito verificar tu información. ¿Ya estás registrado como promotor?"
        
        elif any(word in prompt_lower for word in ["cita", "agendar", "agendarme", "reunión", "reunion", "enlace", "calendly", "calendario"]):
            # Respuesta directa con enlace de Calendly si está disponible
            calendly_link = None
            if tenant_config and tenant_config.get("link_calendly"):
                calendly_link = tenant_config["link_calendly"]
            
            if calendly_link:
                return f"""¡Perfecto! Te ayudo a agendar una cita con alguien de la campaña de {contact_name}.

📅 *Para agendar tu reunión:*
Puedes usar nuestro sistema de citas en línea: {calendly_link}

🎯 *¿Qué puedes hacer en la reunión?*
• Conocer más sobre las propuestas de {contact_name}
• Hablar sobre oportunidades de voluntariado
• Discutir ideas para la campaña
• Coordinar actividades en tu región

💡 *Mientras tanto:*
¿Sabías que puedes sumar puntos invitando a tus amigos y familiares a unirse a este movimiento? Cada persona que se registre con tu código te suma 50 puntos al ranking.

¿Te gustaría que te envíe tu link de referido para empezar a ganar puntos?"""
            else:
                return f"¡Excelente! Te ayudo a agendar una cita con alguien de la campaña de {contact_name}. Para poder darte el enlace correcto, necesito saber un poco más sobre el tipo de cita que buscas. ¿Te interesa hablar sobre voluntariado, prensa, temas de política, o algo más específico?"
        
        else:
            return f"Entiendo tu mensaje. Estoy aquí para ayudarte con todo lo relacionado con la campaña de {contact_name}. ¿Hay algo específico en lo que pueda asistirte?"
    
    def _ensure_model_initialized(self):
        """Inicializa el modelo de forma lazy con timeout"""
        if self._initialized:
            return
            
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            try:
                logger.info(f"✅ GEMINI_API_KEY cargada correctamente: {self.api_key[:10]}...")
                
                # Configuración básica para Gemini AI con timeout
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("Timeout inicializando Gemini")
                
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(5)  # 5 segundos timeout
                
                try:
                    genai.configure(api_key=self.api_key)
                    self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                    logger.info("✅ Modelo Gemini inicializado correctamente")
                finally:
                    signal.alarm(0)  # Cancelar timeout
                    
            except TimeoutError:
                logger.warning("⚠️ Timeout inicializando Gemini, usando fallback")
                self.model = None
            except Exception as e:
                logger.error(f"❌ Error inicializando modelo Gemini: {str(e)}")
                self.model = None
        else:
            logger.warning("GEMINI_API_KEY no configurado")
            self.model = None
            
        self._initialized = True
    
    async def _call_gemini_rest_api(self, prompt: str) -> str:
        """Llama a Gemini usando REST API en lugar de gRPC"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text']
                else:
                    return "No se pudo generar respuesta"
                    
        except Exception as e:
            logger.error(f"Error llamando a Gemini REST API: {str(e)}")
            return f"Error: {str(e)}"
    
    async def _generate_content(self, prompt: str, task_type: str = "chat_conversational") -> str:
        """
        Genera contenido usando Gemini, fallback a REST API si gRPC falla
        
        Args:
            prompt: Texto a enviar a Gemini
            task_type: Tipo de tarea para configuración optimizada (Fase 2)
        
        Returns:
            Respuesta generada por Gemini
        """
        
        # 🚀 FASE 1 + 2: Delegar a GeminiClient si está habilitado
        if self.use_gemini_client and self.gemini_client:
            try:
                # Usar configuraciones avanzadas si están habilitadas (Fase 2)
                use_custom_config = self.use_advanced_model_configs
                
                if use_custom_config:
                    logger.debug(f"🔄 Delegando a GeminiClient con task_type='{task_type}'")
                else:
                    logger.debug("🔄 Delegando generación de contenido a GeminiClient")
                
                return await self.gemini_client.generate_content(
                    prompt, 
                    task_type=task_type,
                    use_custom_config=use_custom_config
                )
            except Exception as e:
                logger.warning(f"⚠️ GeminiClient falló, usando lógica original: {e}")
                # Continuar con lógica original como fallback
        
        # MANTENER: Lógica original completa como fallback
        try:
            # Intentar con gRPC primero
            if self.model:
                response = self.model.generate_content(prompt)
                return response.text
        except Exception as e:
            logger.warning(f"gRPC falló, usando REST API: {str(e)}")
        
        # Fallback a REST API
        return await self._call_gemini_rest_api(prompt)
    
    async def process_chat_message(self, tenant_id: str, query: str, user_context: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
        """
        Procesa un mensaje de chat usando IA específica del tenant con sesión persistente y clasificación
        
        Args:
            tenant_id: ID del tenant
            query: Mensaje del usuario
            user_context: Contexto del usuario
            session_id: ID de la sesión para mantener contexto
            
        Returns:
            Respuesta procesada por IA
        """
        start_time = time.time()
        
        try:
            logger.info(f"Procesando mensaje para tenant {tenant_id}, sesión: {session_id}")
            
            # VERIFICAR SI EL USUARIO ESTÁ BLOQUEADO PRIMERO
            user_state = user_context.get("user_state", "")
            if user_state == "BLOCKED":
                logger.warn(f"🚫 Usuario bloqueado intentando enviar mensaje: {user_context.get('user_id', 'unknown')}")
                return {
                    "response": "",  # No responder nada a usuarios bloqueados
                    "processing_time": time.time() - start_time,
                    "tenant_id": tenant_id,
                    "session_id": session_id,
                    "intent": "blocked_user",
                    "confidence": 1.0
                }
            
            # Obtener configuración del tenant desde el servicio Java
            tenant_config = configuration_service.get_tenant_config(tenant_id)
            if not tenant_config:
                return {
                    "response": "Lo siento, no puedo procesar tu mensaje en este momento.",
                    "error": "Tenant no encontrado"
                }
            
            # Obtener configuración de IA
            ai_config = configuration_service.get_ai_config(tenant_id)
            branding_config = configuration_service.get_branding_config(tenant_id)
            
            # Gestionar sesión
            if not session_id:
                session_id = f"session_{tenant_id}_{int(time.time())}"
            
            session = session_context_service.get_session(session_id)
            if not session:
                session = session_context_service.create_session(
                    session_id=session_id,
                    tenant_id=tenant_id,
                    user_id=user_context.get("user_id"),
                    user_context=user_context
                )
            
            # Actualizar contexto del usuario en la sesión
            session_context_service.update_user_context(session_id, user_context)
            
            # Agregar mensaje del usuario a la sesión
            session_context_service.add_message(session_id, "user", query)
            
            # 🚀 OPTIMIZACIÓN 1: Verificar intenciones prioritarias primero (citas, etc.)
            cached_intent = self._get_cached_intent(query)
            if cached_intent:
                intent = cached_intent
                confidence = 0.95  # Alta confianza para patrones conocidos
                logger.info(f"🎯 Usando intención desde cache: {intent}")
            else:
                # Clasificar la intención del mensaje usando IA
                classification_result = await self.classify_intent(tenant_id, query, user_context, session_id)
                intent = classification_result.get("category", "saludo_apoyo")  # Cambiar default de "default" a "saludo_apoyo"
                confidence = classification_result.get("confidence", 0.0)
                
                # 🔧 DEBUG: Log detallado de la clasificación
                logger.info(f"🧠 CLASIFICACIÓN RESULTADO: intent='{intent}', confidence={confidence:.2f}")
                logger.info(f"📝 Mensaje clasificado: '{query[:100]}...'")
            
            # 🚀 OPTIMIZACIÓN 2: RAG con orden correcto: primero documentos, luego fallback
            document_context = None
            if intent == "conocer_candidato":
                logger.info(f"📚 Consulta sobre candidato detectada: {query}")
                # PRIMERO: Intentar obtener información de documentos
                try:
                    logger.info(f"📚 Usando RAG para consultar documentos del tenant {tenant_id}")
                    document_context = await self._fast_rag_search(tenant_id, query, ai_config)
                    if document_context:
                        logger.info(f"📚 Información encontrada en documentos: {len(document_context)} caracteres")
                    else:
                        logger.info(f"📚 No se encontró información en documentos, usando fallback genérico")
                        document_context = "gemini_direct"
                except Exception as e:
                    logger.error(f"❌ Error en RAG: {e}")
                    # Solo usar fallback si hay error
                    document_context = "gemini_direct"
            else:
                logger.info(f"🎯 Intención '{intent}' no requiere documentos, saltando carga")
            
            logger.info(f"🧠 Intención extraída: {intent} (confianza: {confidence:.2f})")
            
            # 1.5 NUEVO: Intentar obtener respuesta del caché
            cached_response = cache_service.get_cached_response(
                tenant_id=tenant_id,
                query=query,
                intent=intent
            )
            
            if cached_response:
                processing_time = time.time() - start_time
                logger.info(f"🚀 Respuesta servida desde caché (latencia: {processing_time:.2f}s)")
                
                # Agregar respuesta del bot a la sesión
                session_context_service.add_message(session_id, "assistant", cached_response.get("response", ""))
                
                return {
                    **cached_response,
                    "from_cache": True,
                    "processing_time": processing_time,
                    "tenant_id": tenant_id,
                    "session_id": session_id
                }
            
            # 🚀 OPTIMIZACIÓN 3: Respuestas rápidas para casos comunes
            if intent == "conocer_candidato":
                logger.info(f"📚 RESPUESTA ESPECIALIZADA: conocer_candidato")
                # Generar respuesta especializada para consultas sobre el candidato
                if document_context and document_context != "gemini_direct":
                    logger.info(f"📚 Usando contexto de documentos para respuesta")
                    response = await self._generate_candidate_response_with_documents(
                        query, user_context, branding_config, tenant_config, document_context
                    )
                else:
                    logger.info(f"📚 Usando Gemini directamente para respuesta rápida")
                    response = await self._generate_candidate_response_gemini_direct(
                        query, user_context, branding_config, tenant_config
                    )
            elif intent == "cita_campaña":
                logger.info(f"🎯 RESPUESTA RÁPIDA: cita_campaña")
                response = self._handle_appointment_request(branding_config, tenant_config)
            elif intent == "saludo_apoyo":
                logger.info(f"🎯 RESPUESTA RÁPIDA: saludo_apoyo")
                response = self._get_greeting_response(branding_config)
            elif intent == "colaboracion_voluntariado":
                logger.info(f"🎯 RESPUESTA RÁPIDA: colaboracion_voluntariado")
                response = self._get_volunteer_response(branding_config)
            else:
                # Procesar según la intención clasificada con IA
                if intent == "conocer_candidato":
                    # Respuesta específica sobre el candidato
                    response = await self._generate_ai_response_with_session(
                        query, user_context, ai_config, branding_config, tenant_id, session_id
                    )
                elif intent == "solicitud_funcional":
                    # Respuesta específica para consultas funcionales
                    response = self._handle_functional_request(query, branding_config)
                elif intent == "malicioso":
                    # Manejo específico para comportamiento malicioso
                    response = await self._handle_malicious_behavior(
                        query, user_context, tenant_id, confidence
                    )
                else:
                    # Respuesta general con contexto de sesión
                    response = await self._generate_ai_response_with_session(
                        query, user_context, ai_config, branding_config, tenant_id, session_id
                    )
            
            # Filtrar enlaces de la respuesta para WhatsApp (excepto citas)
            if intent == "cita_campaña":
                filtered_response = response  # No filtrar enlaces de Calendly
                logger.info("📅 Respuesta de cita - manteniendo enlaces de Calendly")
            else:
                filtered_response = self._filter_links_from_response(response)
            
            # Limitar respuesta a máximo 1000 caracteres
            if len(filtered_response) > 1000:
                logger.warning(f"⚠️ Respuesta muy larga ({len(filtered_response)} chars), truncando a 1000")
                filtered_response = filtered_response[:997] + "..."
            
            # Agregar respuesta del asistente a la sesión
            session_context_service.add_message(session_id, "assistant", filtered_response, metadata={"intent": intent, "confidence": confidence})
            
            processing_time = time.time() - start_time
            
            # NUEVO: Guardar en caché si es cacheable
            response_data = {
                "response": filtered_response,
                "intent": intent,
                "confidence": confidence
            }
            
            cache_service.cache_response(
                tenant_id=tenant_id,
                query=query,
                response=response_data,
                intent=intent
            )
            
            return {
                "response": filtered_response,
                "processing_time": processing_time,
                "tenant_id": tenant_id,
                "session_id": session_id,
                "intent": intent,
                "confidence": confidence,
                "from_cache": False
            }
            
        except Exception as e:
            logger.error(f"Error procesando mensaje para tenant {tenant_id}: {str(e)}")
            return {
                "response": "Lo siento, hubo un error procesando tu mensaje.",
                "error": str(e)
            }
    
    async def _generate_ai_response_with_session(self, query: str, user_context: Dict[str, Any], 
                                               ai_config: Dict[str, Any], branding_config: Dict[str, Any], 
                                               tenant_id: str, session_id: str) -> str:
        """Genera respuesta usando IA con contexto de sesión persistente"""
        self._ensure_model_initialized()
        if not self.model:
            return "Lo siento, el servicio de IA no está disponible."
        
        try:
            # Obtener contexto completo de la sesión
            session_context = session_context_service.build_context_for_ai(session_id)
            
            # Obtener configuración del tenant para incluir en el prompt
            tenant_config = configuration_service.get_tenant_config(tenant_id)
            
            # Construir prompt con contexto de sesión
            prompt = self._build_session_prompt(query, user_context, branding_config, session_context, tenant_config)
            
            # 🚀 FASE 2: Usar configuración optimizada para chat con sesión
            response_text = await self._generate_content(prompt, task_type="chat_with_session")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error generando respuesta con sesión: {str(e)}")
            return "Lo siento, no pude procesar tu mensaje."
    
    def _build_session_prompt(self, query: str, user_context: Dict[str, Any], 
                            branding_config: Dict[str, Any], session_context: str, tenant_config: Dict[str, Any] = None) -> str:
        """Construye el prompt para chat con contexto de sesión"""
        contact_name = branding_config.get("contactName", "el candidato")
        
        # Contexto del usuario actual
        current_context = ""
        if user_context.get("user_name"):
            current_context += f"El usuario se llama {user_context['user_name']}. "
        if user_context.get("user_state"):
            current_context += f"Estado actual: {user_context['user_state']}. "
        
        # Información específica del tenant
        tenant_info = ""
        if tenant_config:
            if tenant_config.get("link_calendly"):
                tenant_info += f"ENLACE DE CITAS: {tenant_config['link_calendly']}\n"
            if tenant_config.get("link_forms"):
                tenant_info += f"FORMULARIOS: {tenant_config['link_forms']}\n"
        
        # Detectar si es un saludo
        is_greeting = query.lower().strip() in ["hola", "hi", "hello", "hey", "buenos días", "buenas tardes", "buenas noches", "qué tal", "que tal"]
        
        prompt = f"""
Eres un asistente virtual para la campaña política de {contact_name}.

Tu objetivo es mantener conversaciones fluidas y naturales, recordando el contexto de la conversación anterior.

CONTEXTO ACTUAL DE LA SESIÓN:
{session_context}

CONTEXTO INMEDIATO:
{current_context}

INFORMACIÓN ESPECÍFICA DEL TENANT:
{tenant_info}

Mensaje actual del usuario: "{query}"

INSTRUCCIONES:
1. Mantén el contexto de la conversación anterior
2. Si es una pregunta de seguimiento, responde de manera natural
3. Usa la información específica de la campaña cuando sea relevante
4. Mantén un tono amigable y profesional
5. Si no tienes información específica, sé honesto al respecto
6. Integra sutilmente elementos motivacionales sin ser explícito sobre "EPIC MEANING" o "DEVELOPMENT"
7. **IMPORTANTE**: Si el usuario pide agendar una cita, usar el enlace específico de ENLACE DE CITAS
8. **CRÍTICO**: Mantén la respuesta concisa, máximo 800 caracteres
9. **NO menciones enlaces** a documentos externos, solo da información directa

SISTEMA DE PUNTOS Y RANKING:
- Cada referido registrado suma 50 puntos
- Retos semanales dan puntaje adicional
- Ranking actualizado a nivel ciudad, departamento y país
- Los usuarios pueden preguntar "¿Cómo voy?" para ver su progreso
- Para invitar personas: "mandame el link" o "dame mi código"

Responde de manera natural, contextual y útil. Si tienes información específica sobre la campaña en el contexto, úsala para dar una respuesta más precisa.

Respuesta:
"""
        
        return prompt
    
    async def _get_available_documents(self, documentation_bucket_url: str) -> List[str]:
        """Obtiene la lista de documentos disponibles en el bucket"""
        try:
            import httpx
            
            # Obtener lista de documentos del bucket
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(documentation_bucket_url)
                if response.status_code == 200:
                    # Parsear XML para obtener nombres de archivos
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.text)
                    documents = []
                    for contents in root.findall('.//{http://doc.s3.amazonaws.com/2006-03-01}Contents'):
                        key = contents.find('{http://doc.s3.amazonaws.com/2006-03-01}Key')
                        if key is not None and key.text:
                            documents.append(key.text)
                    logger.info(f"📚 Documentos disponibles: {len(documents)} archivos")
                    return documents
                else:
                    logger.warning(f"⚠️ No se pudo obtener lista de documentos: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"❌ Error obteniendo lista de documentos: {e}")
            return []
    
    async def _get_document_content_for_query(self, query: str, documentation_bucket_url: str) -> Optional[str]:
        """Obtiene contenido real de documentos relevantes para la consulta"""
        try:
            import httpx
            import pypdf
            import io
            
            # Mapear consultas a documentos específicos de manera genérica
            query_lower = query.lower()
            
            # Obtener todos los documentos disponibles
            all_documents = await self._get_available_documents(documentation_bucket_url)
            
            # Filtrar documentos relevantes basándose en palabras clave genéricas
            relevant_docs = []
            query_words = query_lower.split()
            
            for doc_name in all_documents:
                doc_lower = doc_name.lower()
                # Buscar coincidencias entre palabras de la consulta y el nombre del documento
                if any(word in doc_lower for word in query_words if len(word) > 3):  # Solo palabras de más de 3 caracteres
                    relevant_docs.append(doc_name)
            
            # Si no se encontraron documentos específicos, usar los primeros 2 documentos disponibles
            if not relevant_docs and all_documents:
                relevant_docs = all_documents[:2]
            
            logger.info(f"📚 Buscando documentos relevantes: {relevant_docs}")
            
            # Descargar y procesar documentos
            content_parts = []
            for doc_name in relevant_docs[:2]:  # Limitar a 2 documentos para evitar timeout
                try:
                    # Construir URL del documento
                    doc_url = f"{documentation_bucket_url}/{doc_name}"
                    logger.info(f"📥 Descargando documento: {doc_name}")
                    
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.get(doc_url)
                        if response.status_code == 200:
                            # Procesar PDF
                            if doc_name.endswith('.pdf'):
                                pdf_content = io.BytesIO(response.content)
                                pdf_reader = pypdf.PdfReader(pdf_content)
                                text = ""
                                for page in pdf_reader.pages[:3]:  # Solo primeras 3 páginas
                                    text += page.extract_text() + "\n"
                                if text.strip():
                                    content_parts.append(f"=== {doc_name} ===\n{text[:2000]}...")  # Limitar a 2000 chars
                                    logger.info(f"✅ Documento {doc_name} procesado: {len(text)} caracteres")
                            
                            # Procesar DOCX
                            elif doc_name.endswith('.docx'):
                                from docx import Document as DocxDocument
                                doc_content = io.BytesIO(response.content)
                                doc = DocxDocument(doc_content)
                                text = ""
                                for paragraph in doc.paragraphs[:20]:  # Solo primeras 20 líneas
                                    text += paragraph.text + "\n"
                                if text.strip():
                                    content_parts.append(f"=== {doc_name} ===\n{text[:2000]}...")  # Limitar a 2000 chars
                                    logger.info(f"✅ Documento {doc_name} procesado: {len(text)} caracteres")
                        else:
                            logger.warning(f"⚠️ No se pudo descargar {doc_name}: {response.status_code}")
                            
                except Exception as e:
                    logger.warning(f"⚠️ Error procesando {doc_name}: {e}")
                    continue
            
            if content_parts:
                full_content = "\n\n".join(content_parts)
                logger.info(f"📚 Contenido total obtenido: {len(full_content)} caracteres")
                return full_content
            else:
                logger.warning("⚠️ No se pudo obtener contenido de ningún documento")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo contenido de documentos: {e}")
            return None
    
    async def _fast_rag_search(self, tenant_id: str, query: str, ai_config: Dict[str, Any]) -> Optional[str]:
        """RAG rápido usando Gemini para buscar en documentos sin LlamaIndex"""
        try:
            # Obtener URL del bucket de documentos
            documentation_bucket_url = ai_config.get("documentation_bucket_url")
            if not documentation_bucket_url:
                logger.warning(f"⚠️ No hay URL de bucket de documentos para tenant {tenant_id}")
                return None
            
            logger.info(f"🔍 RAG rápido: buscando en bucket {documentation_bucket_url}")
            
            # Inicializar Gemini directamente
            try:
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    logger.warning("⚠️ GEMINI_API_KEY no disponible")
                    return None
                
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
                logger.info("✅ Modelo Gemini inicializado para RAG")
                
            except Exception as e:
                logger.error(f"❌ Error inicializando modelo: {e}")
                return None
            
            # Intentar obtener contenido real de documentos específicos
            document_content = await self._get_document_content_for_query(query, documentation_bucket_url)
            
            if document_content:
                logger.info(f"📚 Contenido de documentos obtenido: {len(document_content)} caracteres")
                # Usar el contenido real de los documentos
                prompt = f"""
                Eres un asistente que busca información específica en documentos políticos.
                
                PREGUNTA DEL USUARIO: "{query}"
                
                CONTENIDO DE DOCUMENTOS DISPONIBLE:
                {document_content}
                
                INSTRUCCIONES:
                1. Busca información relevante sobre esta pregunta en el contenido de documentos proporcionado
                2. Si encuentras información específica, extrae los puntos más importantes
                3. Si no encuentras información específica, responde "NO_ENCONTRADO"
                4. Responde solo con la información encontrada, sin agregar explicaciones adicionales
                5. Máximo 500 palabras
                
                Busca información relevante para la pregunta: "{query}"
                """
            else:
                logger.info("📚 No se pudo obtener contenido de documentos, usando títulos")
                # Fallback a solo títulos
                prompt = f"""
                Eres un asistente que busca información específica en documentos políticos.
                
                PREGUNTA DEL USUARIO: "{query}"
                
                INSTRUCCIONES:
                1. Basándote en los títulos de documentos disponibles, determina si hay información relevante
                2. Si encuentras información específica, extrae los puntos más importantes
                3. Si no encuentras información específica, responde "NO_ENCONTRADO"
                4. Responde solo con la información encontrada, sin agregar explicaciones adicionales
                5. Máximo 500 palabras
                
                DOCUMENTOS DISPONIBLES:
                Se encuentran documentos políticos y de campaña disponibles para consulta.
                
                Busca información relevante para la pregunta: "{query}"
                """
            
            try:
                response = model.generate_content(prompt)
                result = response.text.strip()
                
                if "NO_ENCONTRADO" in result or len(result) < 50:
                    logger.info(f"🔍 RAG rápido: No se encontró información específica para '{query}'")
                    return None
                
                logger.info(f"🔍 RAG rápido: Información encontrada ({len(result)} caracteres)")
                return result
                
            except Exception as e:
                logger.error(f"❌ Error en Gemini RAG: {e}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error en RAG rápido: {e}")
            return None
    
    async def _generate_candidate_response_gemini_direct(self, query: str, user_context: Dict[str, Any], 
                                                        branding_config: Dict[str, Any], tenant_config: Dict[str, Any]) -> str:
        """Genera respuesta especializada usando Gemini directamente (más rápido)"""
        try:
            contact_name = branding_config.get("contact_name", "el candidato")
            
            # Usar Gemini directamente para respuesta rápida
            self._ensure_model_initialized()
            if self.model:
                prompt = f"""
                Eres el asistente virtual de {contact_name}. El usuario pregunta: "{query}"
                
                INSTRUCCIONES:
                1. Responde específicamente sobre las propuestas de {contact_name} relacionadas con la pregunta
                2. Mantén un tono profesional y político, enfocado en las propuestas del candidato
                3. Si no tienes información específica, ofrece conectar al usuario con el equipo de la campaña
                4. Responde en máximo 200 palabras
                
                Responde de manera natural y útil sobre las propuestas de {contact_name}.
                """
                
                try:
                    response = self.model.generate_content(prompt)
                    return response.text
                except Exception as e:
                    logger.warning(f"Error con Gemini, usando fallback: {e}")
            
            # Fallback genérico
            return f"""¡Excelente pregunta sobre "{query}"!

{contact_name} tiene propuestas específicas sobre este tema. Te puedo ayudar a conectarte con nuestro equipo especializado para obtener información detallada sobre sus políticas y planes.

¿Te gustaría que te contacte alguien del equipo de la campaña para brindarte información más específica?"""

        except Exception as e:
            logger.error(f"Error generando respuesta con Gemini directo: {e}")
            return f"¡Excelente pregunta! {contact_name} tiene propuestas específicas sobre este tema. Te puedo ayudar a conectarte con nuestro equipo para obtener información detallada."
    
    async def _generate_candidate_response_with_documents(self, query: str, user_context: Dict[str, Any], 
                                                         branding_config: Dict[str, Any], tenant_config: Dict[str, Any], 
                                                         document_context: str) -> str:
        """Genera respuesta especializada usando documentos reales"""
        try:
            contact_name = branding_config.get("contact_name", "el candidato")
            
            # Usar Gemini para generar respuesta específica con documentos
            self._ensure_model_initialized()
            if self.model:
                prompt = f"""
                Eres el asistente virtual de {contact_name}. El usuario pregunta: "{query}"
                
                CONTEXTO DE DOCUMENTOS DISPONIBLE:
                {document_context}
                
                INSTRUCCIONES:
                1. Responde específicamente sobre las propuestas de {contact_name} basándote ÚNICAMENTE en el contexto de documentos proporcionado
                2. Si encuentras información relevante en el contexto, úsala para dar una respuesta precisa y específica
                3. Si no hay información específica en el contexto sobre el tema preguntado, explica que puedes conectar al usuario con el equipo especializado
                4. Mantén un tono profesional y político
                5. Responde en máximo 200 palabras
                6. NO inventes información que no esté en el contexto de documentos
                
                Responde basándote ÚNICAMENTE en el contexto de documentos proporcionado.
                """
                
                try:
                    response = self.model.generate_content(prompt)
                    return response.text
                except Exception as e:
                    logger.warning(f"Error con Gemini, usando fallback: {e}")
            
            # Fallback con contexto de documentos
            return f"""¡Excelente pregunta sobre "{query}"! 

Basándome en la documentación de {contact_name}, puedo proporcionarte información específica sobre sus propuestas relacionadas con este tema.

CONTEXTO ENCONTRADO:
{document_context[:500]}...

¿Te gustaría conocer más detalles sobre estas propuestas? Puedo conectarte con nuestro equipo especializado para brindarte información más específica."""
            
        except Exception as e:
            logger.error(f"Error generando respuesta con documentos: {e}")
            return f"¡Excelente pregunta! {contact_name} tiene propuestas específicas sobre este tema. Te puedo ayudar a conectarte con nuestro equipo para obtener información detallada."
    
    async def _generate_candidate_response(self, query: str, user_context: Dict[str, Any], 
                                         branding_config: Dict[str, Any], tenant_config: Dict[str, Any]) -> str:
        """Genera respuesta especializada para consultas sobre el candidato"""
        try:
            contact_name = branding_config.get("contact_name", "el candidato")
            
            # Usar Gemini para generar respuesta específica sobre el candidato
            self._ensure_model_initialized()
            if self.model:
                prompt = f"""
                Eres el asistente virtual de {contact_name}. El usuario pregunta: "{query}"
                
                Responde específicamente sobre las propuestas, políticas, planes o información relacionada con {contact_name}.
                
                Si la pregunta es sobre "aguas vivas" o temas relacionados con agua, explica las propuestas específicas de {contact_name} sobre:
                - Gestión del agua
                - Recursos hídricos
                - Políticas ambientales
                - Sostenibilidad
                
                Mantén un tono profesional y político, enfocado en las propuestas del candidato.
                Si no tienes información específica, ofrece conectar al usuario con el equipo de la campaña.
                
                Responde en máximo 200 palabras.
                """
                
                try:
                    response = self.model.generate_content(prompt)
                    return response.text
                except Exception as e:
                    logger.warning(f"Error con Gemini, usando fallback: {e}")
            
            # Fallback inteligente
            query_lower = query.lower()
            if any(word in query_lower for word in ["aguas vivas", "agua", "hídrico", "hidrico", "recurso"]):
                return f"""¡Excelente pregunta sobre "{query}"! 

{contact_name} tiene propuestas específicas sobre el manejo sostenible del agua y recursos hídricos. Sus políticas incluyen:

🌊 **Gestión Integral del Agua**: Planes para garantizar acceso equitativo al agua potable
💧 **Conservación de Recursos**: Estrategias para proteger y conservar los recursos hídricos
🌱 **Sostenibilidad Ambiental**: Propuestas para un manejo responsable del medio ambiente

¿Te gustaría conocer más detalles sobre estas propuestas? Puedo conectarte con nuestro equipo especializado para brindarte información más específica."""
            
            return f"""¡Excelente pregunta sobre "{query}"! 

{contact_name} tiene propuestas específicas sobre este tema. Te puedo ayudar a conectarte con nuestro equipo especializado para obtener información detallada sobre sus políticas y planes.

¿Te gustaría que te contacte alguien del equipo de la campaña para brindarte información más específica?"""
            
        except Exception as e:
            logger.error(f"Error generando respuesta de candidato: {e}")
            return f"¡Excelente pregunta! {contact_name} tiene propuestas específicas sobre este tema. Te puedo ayudar a conectarte con nuestro equipo para obtener información detallada."
    
    def _is_tenant_documents_loaded(self, tenant_id: str) -> bool:
        """
        Verifica si los documentos del tenant ya están cargados en cache
        """
        try:
            # Verificar si el tenant tiene documentos en cache
            doc_info = document_context_service.get_tenant_document_info(tenant_id)
            return doc_info is not None and doc_info.get("loaded", False)
        except Exception as e:
            logger.warning(f"Error verificando documentos cargados para tenant {tenant_id}: {e}")
            return False
    
    def _requires_document_context(self, query: str, document_context: str = None) -> bool:
        """
        Determina si la consulta requiere contexto de documentos basado en si hay contexto disponible
        """
        # Si hay contexto de documentos disponible, probablemente la consulta lo necesita
        if document_context and len(document_context.strip()) > 50:
            logger.info(f"📚 Contexto de documentos disponible ({len(document_context)} chars), usando para consulta")
            return True
        
        # Fallback: detectar si la consulta parece ser sobre temas específicos
        query_lower = query.lower().strip()
        
        # Patrones que sugieren consulta específica (no saludo genérico)
        specific_patterns = [
            "qué es", "que es", "qué significa", "que significa",
            "cuéntame", "cuentame", "información sobre", "informacion sobre",
            "dame información", "dame informacion", "habla sobre", "habla de"
        ]
        
        return any(pattern in query_lower for pattern in specific_patterns)
    
    def _get_cached_intent(self, query: str) -> Optional[str]:
        """
        Obtiene intención desde cache para consultas comunes
        """
        query_lower = query.lower().strip()
        
        # Patrones comunes que siempre tienen la misma intención
        # IMPORTANTE: El orden importa - patrones más específicos primero
        intent_patterns = {
            "conocer_candidato": [
                "propuesta", "propuestas", "propone", "políticas", "política", "planes", "plan",
                "programa", "plan de gobierno", "qué es", "que es", "qué significa", "que significa",
                "cómo funciona", "como funciona", "por qué", "por que", "cuál es", "cual es",
                "cuáles son", "cuales son", "información sobre", "informacion sobre",
                "detalles sobre", "detalles de", "que opina", "que piensa",
                "quién es", "quien es", "conocer", "información sobre", "biografía"
            ],
            "cita_campaña": [
                "cita", "agendar", "agendarme", "reunión", "reunion", "calendly", 
                "calendario", "enlace para cita", "quiero una cita"
            ],
            "colaboracion_voluntariado": [
                "voluntario", "voluntariado", "colaborar", "ayudar", "unirme",
                "participar", "trabajar con ustedes"
            ],
            "saludo_apoyo": [
                "hola", "hi", "hello", "hey", "buenos días", "buenas tardes", 
                "buenas noches", "qué tal", "que tal"
            ]
        }
        
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    logger.info(f"🎯 Intención detectada desde cache: {intent}")
                    return intent
        
        return None
    
    def _get_greeting_response(self, branding_config: Dict[str, Any]) -> str:
        """
        Respuesta rápida para saludos comunes
        """
        contact_name = branding_config.get("contactName", "el candidato")
        
        greetings = [
            f"¡Hola! 👋 ¡Qué gusto saludarte! Soy el asistente virtual de la campaña de {contact_name}.",
            f"¡Hola! 😊 ¡Bienvenido! Estoy aquí para ayudarte con información sobre la campaña de {contact_name}.",
            f"¡Hola! 🎉 ¡Excelente día! Soy tu asistente para todo lo relacionado con {contact_name}."
        ]
        
        import random
        return random.choice(greetings)
    
    def _get_volunteer_response(self, branding_config: Dict[str, Any]) -> str:
        """
        Respuesta rápida para consultas de voluntariado
        """
        contact_name = branding_config.get("contactName", "el candidato")
        
        return f"""¡Excelente! 🎯 Me emociona saber que quieres ser parte del equipo de {contact_name}.

🌟 *¿Cómo puedes ayudar?*
• Difundir el mensaje en redes sociales
• Participar en actividades de campo
• Organizar eventos en tu comunidad
• Invitar amigos y familiares

💡 *¿Sabías que puedes ganar puntos?*
Cada persona que se registre con tu código te suma 50 puntos al ranking. ¡Es una forma divertida de competir mientras ayudas!

¿Te gustaría que te envíe tu link de referido para empezar a ganar puntos?"""
    
    def _filter_links_from_response(self, response: str, intent: str = None) -> str:
        """
        Elimina completamente enlaces y referencias a enlaces de las respuestas para WhatsApp
        EXCEPTO enlaces de Calendly cuando la intención es cita_campaña
        """
        import re
        
        # Si es una respuesta de cita, mantener enlaces de Calendly
        if intent == "cita_campaña":
            logger.info("📅 Intención de cita detectada, manteniendo enlaces de Calendly")
            # Solo limpiar referencias a enlaces pero mantener enlaces de Calendly
            link_phrases = [
                r'puedes revisar este enlace[^.]*\.',
                r'puedes consultar este enlace[^.]*\.',
                r'visita este enlace[^.]*\.',
                r'accede a este enlace[^.]*\.',
                r'consulta el siguiente enlace[^.]*\.',
                r'revisa el siguiente enlace[^.]*\.',
                r'puedes ver más información en[^.]*\.',
                r'para más información visita[^.]*\.',
                r'allí encontrarás[^.]*\.',
                r'allí podrás[^.]*\.',
                r'en el siguiente enlace[^.]*\.',
                r'en este enlace[^.]*\.',
                r'\*\*Enlace a[^*]*\*\*[^.]*\.',
                r'te puedo compartir algunos enlaces[^.]*\.',
                r'te puedo compartir[^.]*enlaces[^.]*\.',
                r'compartir.*enlaces.*información[^.]*\.',
            ]
            
            filtered_response = response
            for phrase_pattern in link_phrases:
                filtered_response = re.sub(phrase_pattern, '', filtered_response, flags=re.IGNORECASE)
            
            return filtered_response.strip()
        
        # Para todas las demás intenciones, eliminar TODOS los enlaces
        patterns_to_remove = [
            r'https?://[^\s\)]+',  # URLs http/https
            r'www\.[^\s\)]+',      # URLs www
            r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s\)]*',  # Dominios genéricos
            r'\[([^\]]+)\]\([^)]+\)',  # Enlaces markdown [texto](url)
        ]
        
        # Frases comunes que mencionan enlaces
        link_phrases = [
            r'puedes revisar este enlace[^.]*\.',
            r'puedes consultar este enlace[^.]*\.',
            r'visita este enlace[^.]*\.',
            r'accede a este enlace[^.]*\.',
            r'consulta el siguiente enlace[^.]*\.',
            r'revisa el siguiente enlace[^.]*\.',
            r'puedes ver más información en[^.]*\.',
            r'para más información visita[^.]*\.',
            r'allí encontrarás[^.]*\.',
            r'allí podrás[^.]*\.',
            r'en el siguiente enlace[^.]*\.',
            r'en este enlace[^.]*\.',
            r'\*\*Enlace a[^*]*\*\*[^.]*\.',  # **Enlace a...**
            r'te puedo compartir algunos enlaces[^.]*\.',
            r'te puedo compartir[^.]*enlaces[^.]*\.',
            r'compartir.*enlaces.*información[^.]*\.',
        ]
        
        filtered_response = response
        
        # Eliminar enlaces directos
        for pattern in patterns_to_remove:
            filtered_response = re.sub(pattern, '', filtered_response)
        
        # Eliminar frases que mencionan enlaces
        for phrase_pattern in link_phrases:
            filtered_response = re.sub(phrase_pattern, '', filtered_response, flags=re.IGNORECASE)
        
        # Limpiar caracteres sueltos y puntuación rota
        filtered_response = re.sub(r'\[\s*\)', '', filtered_response)  # [) suelto
        filtered_response = re.sub(r'\[\s*\]', '', filtered_response)  # [] suelto
        filtered_response = re.sub(r'\*\s*\*', '', filtered_response)  # ** suelto
        filtered_response = re.sub(r':\s*\*', ':', filtered_response)   # :* suelto
        
        # Limpiar espacios múltiples y saltos de línea
        filtered_response = re.sub(r'\s+', ' ', filtered_response)
        filtered_response = re.sub(r'\n\s*\n', '\n', filtered_response)
        
        # Limpiar puntuación duplicada y mal formada
        filtered_response = re.sub(r'\.\s*\.', '.', filtered_response)
        filtered_response = re.sub(r'\?\s*\?', '?', filtered_response)
        filtered_response = re.sub(r':\s*\.', '.', filtered_response)  # :. mal formado
        filtered_response = re.sub(r'\*\s*\.', '.', filtered_response)  # *. mal formado
        
        return filtered_response.strip()
    
    def _handle_appointment_request(self, branding_config: Dict[str, Any], tenant_config: Dict[str, Any] = None) -> str:
        """Maneja solicitudes de agendar citas"""
        # 🔧 DEBUG: Log de entrada al método
        logger.info(f"📅 MANEJANDO SOLICITUD DE CITA")
        logger.info(f"📊 tenant_config disponible: {tenant_config is not None}")
        if tenant_config:
            logger.info(f"📊 link_calendly en tenant_config: {'link_calendly' in tenant_config}")
        
        contact_name = branding_config.get("contactName", "el candidato")
        
        # Obtener link de Calendly con prioridad de fuentes
        if tenant_config and tenant_config.get("link_calendly"):
            calendly_link = tenant_config.get("link_calendly")
            logger.info(f"✅ Usando link de Calendly desde BD: {calendly_link}")
        else:
            calendly_link = "https://calendly.com/dq-campana/reunion"
            logger.warning(f"⚠️ Link de Calendly NO encontrado en tenant_config, usando fallback: {calendly_link}")
        
        response = f"""¡Perfecto! Te ayudo a agendar una cita con alguien de la campaña de {contact_name}. 

📅 **Para agendar tu reunión:**
Puedes usar nuestro sistema de citas en línea: {calendly_link}

🎯 **¿Qué puedes hacer en la reunión?**
- Conocer más sobre las propuestas de {contact_name}
- Hablar sobre oportunidades de voluntariado
- Discutir ideas para la campaña
- Coordinar actividades en tu región

💡 **Mientras tanto:**
¿Sabías que puedes sumar puntos invitando a tus amigos y familiares a unirse a este movimiento? Cada persona que se registre con tu código te suma 50 puntos al ranking.

¿Te gustaría que te envíe tu link de referido para empezar a ganar puntos?"""
        
        # 🔧 DEBUG: Log de la respuesta generada
        logger.info(f"✅ Respuesta de cita generada: {len(response)} caracteres")
        
        return response
    
    def _handle_functional_request(self, query: str, branding_config: Dict[str, Any]) -> str:
        """Maneja solicitudes funcionales como '¿Cómo voy?' o pedir link"""
        query_lower = query.lower()
        contact_name = branding_config.get("contactName", "el candidato")
        
        if any(word in query_lower for word in ["como voy", "cómo voy", "progreso", "puntos", "ranking"]):
            return f"""¡Excelente pregunta! Te explico cómo funciona el sistema de puntos de la campaña de {contact_name}:

🏆 **Sistema de Puntos:**
- Cada referido registrado con tu código: **50 puntos**
- Retos semanales: **puntaje adicional**
- Ranking actualizado a nivel ciudad, departamento y país

📊 **Para ver tu progreso:**
Escribe "¿Cómo voy?" y te mostraré:
- Tus puntos totales
- Número de referidos
- Tu puesto en ciudad y nacional
- Lista de quienes están cerca en el ranking

🔗 **Para invitar personas:**
Escribe "dame mi código" o "mandame el link" y te enviaré tu enlace personalizado para referir amigos y familiares.

¿Quieres tu código de referido ahora?"""
        
        elif any(word in query_lower for word in ["link", "código", "codigo", "referido", "mandame", "dame"]):
            return f"""¡Por supuesto! Te ayudo con tu código de referido para la campaña de {contact_name}.

🔗 **Tu código personalizado:**
Pronto tendrás tu enlace único para referir personas.

📱 **Cómo usarlo:**
1. Comparte tu link con amigos y familiares
2. Cada persona que se registre suma 50 puntos
3. Sube en el ranking y gana recompensas

🎯 **Mensaje sugerido para compartir:**
"¡Hola! Te invito a unirte a la campaña de {contact_name}. Es una oportunidad de ser parte del cambio que Colombia necesita. Únete aquí: [TU_LINK]"

¿Te gustaría que genere tu código ahora?"""
        
        else:
            return f"""¡Claro! Te ayudo con información sobre la campaña de {contact_name}.

Puedes preguntarme sobre:
- Las propuestas de {contact_name}
- Cómo participar en la campaña
- Sistema de puntos y ranking
- Oportunidades de voluntariado
- Agendar citas con el equipo

¿En qué te puedo ayudar específicamente?"""
    
    def _handle_volunteer_request(self, branding_config: Dict[str, Any]) -> str:
        """Maneja solicitudes de voluntariado"""
        contact_name = branding_config.get("contactName", "el candidato")
        forms_link = branding_config.get("link_forms", "https://forms.gle/dq-publicidad-campana")
        
        return f"""¡Excelente! Me emociona que quieras ser parte del equipo de voluntarios de {contact_name}.

🤝 **Áreas donde puedes ayudar:**
1. Redes sociales
2. Comunicaciones  
3. Temas programáticos
4. Logística
5. Temas jurídicos
6. Trabajo territorial
7. Día de elecciones
8. Call center
9. Otras áreas (¡cuéntame cuál!)

📝 **Para registrarte como voluntario:**
Completa nuestro formulario: {forms_link}

💪 **Beneficios de ser voluntario:**
- Ser parte del cambio de Colombia
- Conocer personas con ideas afines
- Desarrollar habilidades de liderazgo
- Acceso a eventos exclusivos
- Puntos adicionales en el ranking

¿En qué área te interesa más participar?"""
    
    async def classify_intent(self, tenant_id: str, message: str, user_context: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
        """
        Clasifica la intención de un mensaje con contexto de sesión
        
        Args:
            tenant_id: ID del tenant
            message: Mensaje a clasificar
            user_context: Contexto del usuario
            session_id: ID de la sesión para contexto
            
        Returns:
            Clasificación de intención
        """
        try:
            logger.info(f"Clasificando intención para tenant {tenant_id}")
            
            # Obtener configuración del tenant
            tenant_config = configuration_service.get_tenant_config(tenant_id)

            # Asegurar session_id estable: derivar de user_context cuando no venga
            if not session_id:
                derived = None
                if user_context:
                    derived = user_context.get("session_id") or user_context.get("user_id") or user_context.get("phone")
                session_id = f"session_{tenant_id}_{derived}" if derived else f"session_{tenant_id}_classify"

            # Registrar/actualizar contexto mínimo de sesión para clasificación
            session = session_context_service.get_session(session_id)
            if not session:
                session_context_service.create_session(session_id=session_id, tenant_id=tenant_id, user_id=(user_context or {}).get("user_id"), user_context=user_context or {})
            else:
                session_context_service.update_user_context(session_id, user_context or {})
            if not tenant_config:
                logger.warning(f"❌ TENANT NO ENCONTRADO: {tenant_id} - Retornando general_query")
                return {
                    "category": "general_query",
                    "confidence": 0.0,
                    "original_message": message,
                    "error": "Tenant no encontrado"
                }
            
            # Clasificar intención usando IA
            classification = await self._classify_with_ai(message, user_context)
            
            return classification
            
        except Exception as e:
            logger.error(f"Error clasificando intención para tenant {tenant_id}: {str(e)}")
            return {
                "category": "general_query",
                "confidence": 0.0,
                "original_message": message,
                "error": str(e)
            }

    async def analyze_registration(self, tenant_id: str, message: str, user_context: Dict[str, Any] = None,
                                   session_id: str = None, current_state: str = None) -> Dict[str, Any]:
        """
        Analiza un mensaje usando IA para entender el contexto completo y extraer datos de registro.

        Retorna: { type: "name|lastname|city|info|other", value: str|None, confidence: float }
        """
        try:
            text = (message or "").strip()
            if not text:
                return {"type": "other", "value": None, "confidence": 0.0}

            if not session_id:
                derived = None
                if user_context:
                    derived = user_context.get("session_id") or user_context.get("user_id") or user_context.get("phone")
                session_id = f"session_{tenant_id}_{derived}" if derived else f"session_{tenant_id}_registration"

            state = (current_state or "").upper()

            # Usar IA para análisis inteligente basado en contexto
            ai_analysis = await self._analyze_registration_with_ai(text, state, user_context, session_id)
            if ai_analysis:
                return ai_analysis

            # Fallback inteligente si IA falla (por cuota excedida u otros errores)
            logger.info("Usando lógica de fallback inteligente para análisis de registro")
            return self._fallback_registration_analysis(text, state)
            
        except Exception as e:
            logger.error(f"Error analizando registro: {str(e)}")
            return {"type": "other", "value": None, "confidence": 0.0}
    
    def _fallback_registration_analysis(self, text: str, state: str) -> Dict[str, Any]:
        """
        Análisis de fallback inteligente cuando la IA no está disponible
        """
        try:
            lowered = text.lower().strip()
            
            # Detectar preguntas
            if "?" in text or any(w in lowered for w in ["qué", "que ", "cómo", "como ", "quién", "quien ", "dónde", "donde ", "por qué", "por que"]):
                return {"type": "info", "value": None, "confidence": 0.85}
            
            # Detectar nombres (lógica mejorada)
            words = text.split()
            
            # Si es un saludo simple
            if lowered in ["hola", "hi", "hello", "buenos días", "buenas tardes", "buenas noches"]:
                return {"type": "other", "value": None, "confidence": 0.9}
            
            # Si contiene palabras de confirmación + nombre
            confirmation_words = ["perfecto", "ok", "vale", "listo", "sí", "si", "bueno", "bien"]
            if any(word in lowered for word in confirmation_words):
                # Buscar nombre después de la confirmación
                for i, word in enumerate(words):
                    if word.lower() in confirmation_words and i + 1 < len(words):
                        # Extraer el resto como nombre
                        name_parts = words[i+1:]
                        if name_parts and all(part.replace("-", "").replace("'", "").isalpha() for part in name_parts):
                            name = " ".join(name_parts)
                            if len(name) >= 2:
                                return {"type": "name", "value": name, "confidence": 0.8}
            
            # Si parece un nombre directo (2-4 palabras, solo letras)
            if 2 <= len(words) <= 4 and not any(c.isdigit() for c in text):
                # Verificar que no empiece con palabras interrogativas
                if words[0].lower() not in ["que", "qué", "cómo", "como", "cuál", "cual", "quién", "quien", "dónde", "donde"]:
                    # Verificar que todas las palabras sean letras
                    if all(word.replace("-", "").replace("'", "").isalpha() for word in words):
                        return {"type": "name", "value": text, "confidence": 0.7}
            
            # Detectar ciudades
            city_indicators = ["vivo en", "soy de", "estoy en", "resido en", "ciudad", "municipio"]
            if any(indicator in lowered for indicator in city_indicators):
                # Extraer ciudad después del indicador
                for indicator in city_indicators:
                    if indicator in lowered:
                        city_part = lowered.split(indicator)[-1].strip()
                        if city_part and len(city_part) >= 2:
                            return {"type": "city", "value": city_part.title(), "confidence": 0.8}
            
            # Si contiene "me llamo" o "mi nombre es"
            if "me llamo" in lowered or "mi nombre es" in lowered:
                name_part = text
                if "me llamo" in lowered:
                    name_part = text.split("me llamo")[-1].strip()
                elif "mi nombre es" in lowered:
                    name_part = text.split("mi nombre es")[-1].strip()
                
                if name_part and len(name_part) >= 2:
                    return {"type": "name", "value": name_part, "confidence": 0.9}
            
            return {"type": "other", "value": None, "confidence": 0.5}
            
        except Exception as e:
            logger.error(f"Error en análisis de fallback: {str(e)}")
            return {"type": "other", "value": None, "confidence": 0.0}
    
    async def extract_data(self, tenant_id: str, message: str, data_type: str) -> Dict[str, Any]:
        """
        Extrae datos específicos de un mensaje
        
        Args:
            tenant_id: ID del tenant
            message: Mensaje del usuario
            data_type: Tipo de dato a extraer
            
        Returns:
            Datos extraídos
        """
        try:
            logger.info(f"Extrayendo {data_type} para tenant {tenant_id}")
            
            # Obtener configuración del tenant
            tenant_config = configuration_service.get_tenant_config(tenant_id)
            if not tenant_config:
                return {
                    "extracted_data": {},
                    "error": "Tenant no encontrado"
                }
            
            # Extraer datos usando IA
            extracted_data = await self._extract_with_ai(message, data_type)
            
            return {
                "extracted_data": extracted_data
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo {data_type} para tenant {tenant_id}: {str(e)}")
            return {
                "extracted_data": {},
                "error": str(e)
            }
    
    async def validate_data(self, tenant_id: str, data: str, data_type: str) -> Dict[str, Any]:
        """
        Valida datos de entrada del usuario
        
        Args:
            tenant_id: ID del tenant
            data: Dato a validar
            data_type: Tipo de dato
            
        Returns:
            Resultado de validación
        """
        try:
            logger.info(f"Validando {data_type}: '{data}' para tenant {tenant_id}")
            
            # Validación básica por tipo
            is_valid = self._basic_validation(data, data_type)
            
            if not is_valid:
                logger.warning(f"Validación básica falló para {data_type}: '{data}'")
                return {
                    "is_valid": False,
                    "data_type": data_type,
                    "reason": "formato_invalido"
                }
            
            # Para nombres y ciudades, validación adicional con IA
            if data_type.lower() in ["name", "lastname", "city"] and len(data) > 3:
                ai_validation = await self._validate_with_ai(data, data_type)
                if not ai_validation:
                    logger.warning(f"Validación IA falló para {data_type}: '{data}'")
                    return {
                        "is_valid": False,
                        "data_type": data_type,
                        "reason": "contenido_invalido"
                    }
            
            logger.info(f"Validación exitosa para {data_type}: '{data}'")
            return {
                "is_valid": True,
                "data_type": data_type
            }
            
        except Exception as e:
            logger.error(f"Error validando {data_type} para tenant {tenant_id}: {str(e)}")
            return {
                "is_valid": False,
                "error": str(e)
            }
    
    async def normalize_location(self, city_input: str) -> Dict[str, Any]:
        """Normaliza el nombre de una ciudad (puede ser fuera de Colombia),
        reconoce apodos y detecta su estado/departamento y país cuando sea posible."""
        self._ensure_model_initialized()
        # 1) Intento OFFLINE: apodos y alias conocidos + regex sencillas
        offline = self._normalize_location_offline(city_input)
        if offline:
            return offline
        if not self.model:
            return {"city": city_input.strip(), "state": None, "country": None}
        try:
            prompt = f"""
Eres un asistente que estandariza ubicaciones (cualquier país) y reconoce apodos locales.

Tarea: Dada una entrada de ciudad (puede venir con errores ortográficos, variaciones o apodos), devuelve un JSON con:
- city: nombre oficial de la ciudad/municipio con mayúsculas y tildes correctas
- state: estado/departamento/provincia oficial
- country: país oficial

Reglas:
- Solo responde el JSON, sin texto adicional.
- Si la entrada corresponde a un apodo, resuélvelo al nombre oficial.
- Si no puedes determinar estado o país, deja ese campo con null.
 - La entrada puede ser una FRASE COMPLETA del usuario (ej: "vivo en ..."). Extrae y normaliza la ciudad implícita.

Apodos comunes en Colombia (no exhaustivo):
- "la nevera" → Bogotá
- "medallo" → Medellín
- "la arenosa" → Barranquilla
- "la sucursal del cielo" → Cali
- "la ciudad bonita" → Bucaramanga
 - "la ciudad de la eterna primavera" → Medellín

Ejemplos válidos:
Entrada: "medellin" → {"city": "Medellín", "state": "Antioquia", "country": "Colombia"}
Entrada: "bogota" → {"city": "Bogotá", "state": "Cundinamarca", "country": "Colombia"}
Entrada: "soacha" → {"city": "Soacha", "state": "Cundinamarca", "country": "Colombia"}
Entrada: "la nevera" → {"city": "Bogotá", "state": "Cundinamarca", "country": "Colombia"}
Entrada: "vivo en la ciudad de la eterna primavera" → {"city": "Medellín", "state": "Antioquia", "country": "Colombia"}
Entrada: "New York" → {"city": "New York", "state": "New York", "country": "United States"}

Entrada real: "{city_input}".
Responde solo el JSON estricto sin comentarios:
"""
            response_text = await self._generate_content(prompt)
            text = (response_text or "").strip()
            import json
            result = json.loads(text)
            # Sanitizar salida mínima
            city = (result.get("city") or city_input or "").strip()
            state = (result.get("state") or None)
            country = (result.get("country") or None)
            return {"city": city, "state": state, "country": country}
        except Exception as e:
            logger.error(f"Error normalizando ubicación: {str(e)}")
            return {"city": city_input.strip() if city_input else "", "state": None, "country": None}

    def _normalize_location_offline(self, city_input: str) -> Optional[Dict[str, Any]]:
        """Mapa rápido de apodos/alias y extracción simple desde frases.
        Retorna None si no puede resolver offline.
        """
        if not city_input:
            return None
        text = city_input.strip().lower()
        # Normalizaciones simples de variantes comunes
        text = text.replace("sudamericana", "suramericana")
        text = text.replace("heroica", "heróica") if "ciudad heroica" in text else text

        # Diccionario de apodos/alias → (city, state, country)
        nick_map = {
            # Bogotá
            "la nevera": ("Bogotá", "Cundinamarca", "Colombia"),
            "bogota": ("Bogotá", "Cundinamarca", "Colombia"),
            "bogotá": ("Bogotá", "Cundinamarca", "Colombia"),
            "atenas suramericana": ("Bogotá", "Cundinamarca", "Colombia"),
            "la atenas suramericana": ("Bogotá", "Cundinamarca", "Colombia"),
            "atenas sudamericana": ("Bogotá", "Cundinamarca", "Colombia"),
            "la atenas sudamericana": ("Bogotá", "Cundinamarca", "Colombia"),
            # Medellín
            "medallo": ("Medellín", "Antioquia", "Colombia"),
            "ciudad de la eterna primavera": ("Medellín", "Antioquia", "Colombia"),
            "la ciudad de la eterna primavera": ("Medellín", "Antioquia", "Colombia"),
            "medellin": ("Medellín", "Antioquia", "Colombia"),
            "medellín": ("Medellín", "Antioquia", "Colombia"),
            # Barranquilla
            "la arenosa": ("Barranquilla", "Atlántico", "Colombia"),
            "puerta de oro de colombia": ("Barranquilla", "Atlántico", "Colombia"),
            "la puerta de oro de colombia": ("Barranquilla", "Atlántico", "Colombia"),
            "curramba": ("Barranquilla", "Atlántico", "Colombia"),
            "barranquilla": ("Barranquilla", "Atlántico", "Colombia"),
            # Cali
            "la sucursal del cielo": ("Cali", "Valle del Cauca", "Colombia"),
            "sultana del valle": ("Cali", "Valle del Cauca", "Colombia"),
            "cali": ("Cali", "Valle del Cauca", "Colombia"),
            # Bucaramanga
            "la ciudad bonita": ("Bucaramanga", "Santander", "Colombia"),
            "ciudad de los parques": ("Bucaramanga", "Santander", "Colombia"),
            "bucaramanga": ("Bucaramanga", "Santander", "Colombia"),
            # Buga
            "ciudad señora": ("Buga", "Valle del Cauca", "Colombia"),
            # Cartagena
            "ciudad heroica": ("Cartagena", "Bolívar", "Colombia"),
            "la ciudad heróica": ("Cartagena", "Bolívar", "Colombia"),
            "corralito de piedra": ("Cartagena", "Bolívar", "Colombia"),
            # Chía
            "ciudad de la luna": ("Chía", "Cundinamarca", "Colombia"),
            # Cúcuta
            "perla del norte": ("Cúcuta", "Norte de Santander", "Colombia"),
            # Ibagué
            "ciudad musical": ("Ibagué", "Tolima", "Colombia"),
            # Ipiales
            "ciudad de las nubes verdes": ("Ipiales", "Nariño", "Colombia"),
            # Montería
            "perla del sinu": ("Montería", "Córdoba", "Colombia"),
            "perla del sinú": ("Montería", "Córdoba", "Colombia"),
            # Neiva
            "ciudad amable": ("Neiva", "Huila", "Colombia"),
            # Pasto
            "ciudad sorpresa": ("Pasto", "Nariño", "Colombia"),
            # Pereira
            "ciudad sin puertas": ("Pereira", "Risaralda", "Colombia"),
            # Popayán
            "ciudad blanca": ("Popayán", "Cauca", "Colombia"),
            # Riohacha
            "fénix del caribe": ("Riohacha", "La Guajira", "Colombia"),
            "fenix del caribe": ("Riohacha", "La Guajira", "Colombia"),
            # Santa Marta
            "perla de america": ("Santa Marta", "Magdalena", "Colombia"),
            "perla de américa": ("Santa Marta", "Magdalena", "Colombia"),
            # Valledupar
            "capital mundial del vallenato": ("Valledupar", "Cesar", "Colombia"),
            # Villavicencio
            "puerta del llano": ("Villavicencio", "Meta", "Colombia"),
            # Zipaquirá
            "capital salinera": ("Zipaquirá", "Cundinamarca", "Colombia"),
        }

        # Match exacto por clave completa
        if text in nick_map:
            city, state, country = nick_map[text]
            return {"city": city, "state": state, "country": country}

        # Búsqueda por inclusión de apodos conocidos en frases completas
        for key, (city, state, country) in nick_map.items():
            if key in text:
                return {"city": city, "state": state, "country": country}

        # Regex para capturar patrones frecuentes en frases
        import re
        patterns = [
            r"ciudad\s+de\s+la\s+eterna\s+primavera",
            r"vivo\s+en\s+medallo",
            r"vivo\s+en\s+la\s+nevera",
            r"estoy\s+en\s+la\s+arenosa",
        ]
        for pat in patterns:
            if re.search(pat, text):
                # Reutilizar nick_map via búsqueda por inclusión
                for key, (city, state, country) in nick_map.items():
                    if key in text:
                        return {"city": city, "state": state, "country": country}

        # Si el texto parece una ciudad colombiana común, capitalizar mínimamente
        common_cities = {
            "soacha": ("Soacha", "Cundinamarca", "Colombia"),
            "itagui": ("Itagüí", "Antioquia", "Colombia"),
            "itagüi": ("Itagüí", "Antioquia", "Colombia"),
        }
        t = text.replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
        for key, val in common_cities.items():
            if t == key or f" {key} " in f" {t} ":
                city, state, country = val
                return {"city": city, "state": state, "country": country}

        return None

    # Métodos privados para procesamiento de IA
    
    async def _ensure_tenant_documents_loaded(self, tenant_id: str, ai_config: Dict[str, Any]):
        """Asegura que los documentos del tenant estén cargados"""
        try:
            # Verificar si ya tenemos documentos cargados
            doc_info = document_context_service.get_tenant_document_info(tenant_id)
            if doc_info:
                logger.debug(f"📚 Documentos ya cargados para tenant {tenant_id}: {doc_info.get('document_count', 0)} docs")
                return
            
            # Obtener URL del bucket de documentación
            documentation_bucket_url = ai_config.get("documentation_bucket_url")
            
            if documentation_bucket_url:
                logger.info(f"📥 Iniciando carga de documentos para tenant {tenant_id} desde: {documentation_bucket_url}")
                success = await document_context_service.load_tenant_documents(tenant_id, documentation_bucket_url)
                if success:
                    doc_info = document_context_service.get_tenant_document_info(tenant_id)
                    logger.info(f"✅ Documentos cargados para tenant {tenant_id}: {doc_info.get('document_count', 0)} docs")
                else:
                    logger.warning(f"⚠️ No se pudieron cargar documentos para tenant {tenant_id}")
            else:
                logger.debug(f"ℹ️ No hay bucket de documentación configurado para tenant {tenant_id}")
                
        except Exception as e:
            logger.error(f"❌ Error cargando documentos para tenant {tenant_id}: {str(e)}", exc_info=True)
    
    async def _generate_ai_response(self, query: str, user_context: Dict[str, Any], 
                                  ai_config: Dict[str, Any], branding_config: Dict[str, Any], 
                                  tenant_id: str) -> str:
        """Genera respuesta usando IA con contexto de documentos"""
        
        # 🚀 FASE 6: Usar RAGOrchestrator si está habilitado
        if self.use_rag_orchestrator and self.rag_orchestrator:
            try:
                # 🔧 FIX: Asegurar que documentos estén cargados ANTES de usar RAG
                await self._ensure_tenant_documents_loaded(tenant_id, ai_config)
                
                logger.info(f"🎯 Usando RAGOrchestrator | tenant_id={tenant_id} | session_id={session_id} | query='{query[:50]}...'")
                response = await self.rag_orchestrator.process_query_simple(
                    query=query,
                    tenant_id=tenant_id,
                    user_context=user_context,
                    session_id=session_id
                )
                logger.info(f"✅ RAG respuesta generada | length={len(response)} chars")
                return response
            except Exception as e:
                logger.error(f"❌ Error usando RAGOrchestrator: {str(e)}", exc_info=True)
                logger.info("⚠️ Fallback a lógica original (sin RAG)")
                # Continuar con lógica original como fallback
        
        # Lógica original (sin RAG)
        self._ensure_model_initialized()
        if not self.model:
            return "Lo siento, el servicio de IA no está disponible."
        
        try:
            # 🔧 FIX: Asegurar que documentos estén cargados antes de buscar contexto
            await self._ensure_tenant_documents_loaded(tenant_id, ai_config)
            
            # Obtener contexto relevante de documentos del cliente
            relevant_context = ""
            try:
                relevant_context = await document_context_service.get_relevant_context(
                    tenant_id, query, max_results=3
                )
                if relevant_context:
                    logger.info(f"Contexto relevante obtenido para tenant {tenant_id}: {len(relevant_context)} caracteres")
            except Exception as e:
                logger.warning(f"Error obteniendo contexto relevante: {str(e)}")
            
            # Construir prompt con contexto de documentos
            prompt = self._build_chat_prompt(query, user_context, branding_config, relevant_context)
            
            # 🚀 FASE 2: Usar configuración optimizada para chat conversacional
            response_text = await self._generate_content(prompt, task_type="chat_conversational")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error generando respuesta con IA: {str(e)}")
            return "Lo siento, no pude procesar tu mensaje."
    
    def _detect_malicious_intent(self, message: str) -> Dict[str, Any]:
        """
        Detecta intención maliciosa de manera inteligente usando análisis contextual
        """
        message_lower = message.lower().strip()
        
        # Indicadores de comportamiento malicioso (no solo palabras, sino patrones)
        malicious_indicators = {
            "insultos_directos": [
                "idiota", "imbécil", "estúpido", "tonto", "bobo", "bruto",
                "hijueputa", "malparido", "gonorrea", "marica", "chimba",
                "careverga", "verga", "chimbo", "malparida", "hijuepucha"
            ],
            "ataques_campana": [
                "ladrones", "corruptos", "estafadores", "mentirosos", "falsos",
                "robando", "estafando", "mintiendo", "engañando"
            ],
            "provocacion": [
                "vete a la mierda", "que se joda", "me importa un carajo",
                "no me importa", "me vale verga", "me vale mierda"
            ],
            "spam_indicators": [
                "spam", "basura", "mierda", "porquería", "pendejada"
            ]
        }
        
        # Analizar el mensaje por categorías
        detected_categories = []
        confidence_score = 0.0
        
        for category, indicators in malicious_indicators.items():
            for indicator in indicators:
                if indicator in message_lower:
                    detected_categories.append(category)
                    confidence_score += 0.2
                    break
        
        # Detectar patrones de agresividad
        aggressive_patterns = [
            r'\b(que\s+se\s+joda|vete\s+a\s+la\s+mierda|me\s+importa\s+un\s+carajo)\b',
            r'\b(no\s+me\s+importa|me\s+vale\s+verga|me\s+vale\s+mierda)\b',
            r'\b(eres\s+un|son\s+unos|esto\s+es\s+una)\b.*\b(idiota|imbécil|estafa|mentira)\b'
        ]
        
        import re
        for pattern in aggressive_patterns:
            if re.search(pattern, message_lower):
                detected_categories.append("aggressive_pattern")
                confidence_score += 0.3
                break
        
        # Calcular confianza final
        confidence_score = min(confidence_score, 1.0)
        
        is_malicious = len(detected_categories) > 0 and confidence_score >= 0.3
        
        if is_malicious:
            logger.warning(f"🚨 Intención maliciosa detectada - Categorías: {detected_categories}, Confianza: {confidence_score:.2f}")
            logger.warning(f"🚨 Mensaje: '{message}'")
        
        return {
            "is_malicious": is_malicious,
            "categories": detected_categories,
            "confidence": confidence_score,
            "reason": "intelligent_intent_detection"
        }

    async def _classify_with_ai(self, message: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Clasifica intención usando IA"""
        # 🔧 DEBUG: Log del mensaje a clasificar
        logger.info(f"🎯 CLASIFICANDO INTENCIÓN | mensaje: '{message}'")
        logger.info(f"📊 Longitud del mensaje: {len(message)} caracteres")
        
        self._ensure_model_initialized()
        
        # Primero verificar intención maliciosa de manera inteligente
        malicious_detection = self._detect_malicious_intent(message)
        if malicious_detection["is_malicious"]:
            logger.info(f"🚨 INTENCIÓN MALICIOSA DETECTADA: {malicious_detection['reason']}")
            return {
                "category": "malicioso",
                "confidence": malicious_detection["confidence"],
                "original_message": message,
                "reason": malicious_detection["reason"],
                "detected_categories": malicious_detection["categories"]
            }
        
        # 🔧 FALLBACK INTELIGENTE: Detectar preguntas sobre el candidato antes de usar IA
        try:
            message_lower = message.lower().strip()
            
            # Patrones de preguntas directas
            question_patterns = [
                "qué es", "que es", "qué significa", "que significa",
                "cómo funciona", "como funciona", "por qué", "por que",
                "cuál es", "cual es", "cuáles son", "cuales son",
                "que opina", "que piensa", "información", "detalles"
            ]
            
            # Patrones de propuestas y políticas
            policy_patterns = [
                "propuestas", "propone", "políticas", "planes", 
                "programa", "plan de gobierno", "propuesta", "propuesta de",
                "cuales son las", "que propone", "propuestas sobre", "propuestas de"
            ]
            
            # Verificar patrones de preguntas directas
            for pattern in question_patterns:
                if pattern in message_lower:
                    logger.info(f"🎯 PREGUNTA DETECTADA POR PATRÓN: '{message}' → conocer_candidato")
                    return {
                        "category": "conocer_candidato",
                        "confidence": 0.9,
                        "original_message": message,
                        "reason": "Detectado por patrón de pregunta"
                    }
            
            # Verificar patrones de propuestas y políticas
            for pattern in policy_patterns:
                if pattern in message_lower:
                    logger.info(f"🎯 PROPUESTA DETECTADA POR PATRÓN: '{message}' → conocer_candidato")
                    return {
                        "category": "conocer_candidato",
                        "confidence": 0.9,
                        "original_message": message,
                        "reason": "Detectado por patrón de propuesta"
                    }
        except Exception as e:
            logger.warning(f"Error en detección de patrones: {e}")
            # Continuar con el flujo normal
        
        if not self.model:
            logger.warning(f"⚠️ Modelo no disponible, usando fallback")
            return {
                "category": "saludo_apoyo", 
                "confidence": 0.0,
                "original_message": message
            }
        
        try:
            # Agregar timeout para evitar cuelgues
            import asyncio
            
            # Prompt para clasificación inteligente
            prompt = f"""
            Eres un experto en análisis de intención para campañas políticas. Clasifica la siguiente intención del mensaje:
            
            CATEGORÍAS (EN ORDEN DE PRIORIDAD):
            
            - malicioso: Mensajes con INTENCIÓN NEGATIVA, AGRESIVA o OFENSIVA hacia la campaña, candidato o equipo. Analiza el TONO y PROPÓSITO, no solo palabras específicas:
              * Insultos o ataques personales (directos o indirectos)
              * Lenguaje ofensivo, grosero o agresivo
              * Ataques a la integridad de la campaña o candidato
              * Mensajes de provocación o spam
              * Cualquier mensaje que busque dañar, ofender o agredir
            
            - cita_campaña: [PRIORIDAD ALTA] Cualquier solicitud para agendar, coordinar, tener una reunión o cita. 
              Ejemplos: "quiero una cita", "agendar reunión", "hablar con alguien", "coordinar encuentro", "me gustaría reunirme"
              ⚠️ IMPORTANTE: Si el mensaje menciona "cita", "reunión", "agendar", "coordinar", "hablar con alguien de la campaña" → SIEMPRE clasificar como "cita_campaña"
            
            - atencion_humano: Solicitudes EXPLÍCITAS para hablar con un agente humano o persona real
              Ejemplos: "quiero hablar con una persona real", "necesito un humano", "dame un asesor"
            
            - saludo_apoyo: Saludos, muestras de simpatía o respaldo positivo
            - publicidad_info: Preguntas sobre materiales publicitarios o difusión
        - conocer_candidato: [PRIORIDAD ALTA] Interés en propuestas, trayectoria, información del candidato, preguntas sobre políticas, planes de gobierno, experiencia, etc.
          Ejemplos: "¿qué propone?", "¿cuál es su experiencia?", "¿qué planes tiene?", "¿qué opina sobre...?", "¿cuáles son sus propuestas?", "¿qué es aguas vivas?", "¿cuándo inicia la campaña?", "¿qué significa...?", "¿qué es...?", "¿cómo funciona...?", "¿por qué...?", "cuales son las propuestas", "que propone sobre", "información sobre", "detalles sobre"
          ⚠️ IMPORTANTE: Si el mensaje pregunta sobre el candidato, sus propuestas, políticas, planes, experiencia, o cualquier información sobre él → SIEMPRE clasificar como "conocer_candidato"
          ⚠️ CRÍTICO: Cualquier pregunta que contenga palabras como "propuestas", "propone", "políticas", "planes", "información", "detalles" debe clasificarse como "conocer_candidato"
            - actualizacion_datos: Correcciones o actualizaciones de información personal
            - solicitud_funcional: Preguntas técnicas sobre la plataforma o sistema
            - colaboracion_voluntariado: Ofrecimientos de apoyo activo o voluntariado
            - quejas: Reclamos constructivos sobre gestión o procesos
            - lider: Mensajes de líderes comunitarios buscando coordinación
            - atencion_equipo_interno: Mensajes del equipo interno de la campaña
            - registration_response: Respuestas a preguntas de registro
            
            INSTRUCCIONES:
            1. Analiza la INTENCIÓN y TONO del mensaje, no solo palabras específicas
            2. Considera el CONTEXTO y PROPÓSITO del mensaje
            3. Si hay dudas sobre intención maliciosa, clasifica como "malicioso"
            4. Sé inteligente: un mensaje puede contener palabras fuertes pero tener intención constructiva
            
            Mensaje: "{message}"
            
            Responde solo con la categoría más apropiada basándote en la INTENCIÓN del mensaje.
            """
            
            # 🔧 DEBUG: Log del prompt completo
            logger.info(f"🤖 Prompt de clasificación enviado a Gemini")
            logger.debug(f"📋 Prompt completo: {prompt[:200]}...")
            
            # 🚀 FASE 2: Usar configuración optimizada para clasificación de intenciones con timeout
            try:
                response_text = await asyncio.wait_for(
                    self._generate_content(prompt, task_type="intent_classification"),
                    timeout=10.0  # 10 segundos de timeout
                )
            except asyncio.TimeoutError:
                logger.warning("⚠️ Timeout en clasificación de IA, usando fallback")
                return {
                    "category": "saludo_apoyo",
                    "confidence": 0.0,
                    "original_message": message,
                    "reason": "Timeout en IA"
                }
            
            # 🔧 DEBUG: Log de la respuesta de Gemini
            logger.info(f"🎯 Respuesta de Gemini para clasificación: '{response_text}'")
            
            category = response_text.strip().lower()
            
            # 🔧 DEBUG: Log de la intención final
            logger.info(f"✅ INTENCIÓN CLASIFICADA: '{category}'")
            
            # Validar categoría
            valid_categories = [
                "malicioso", "cita_campaña", "saludo_apoyo", "publicidad_info", 
                "conocer_candidato", "actualizacion_datos", "solicitud_funcional", 
                "colaboracion_voluntariado", "quejas", "lider", "atencion_humano", 
                "atencion_equipo_interno", "registration_response"
            ]
            
            if category not in valid_categories:
                logger.warning(f"⚠️ Intención no válida: '{category}', usando 'saludo_apoyo' como fallback")
                category = "saludo_apoyo"  # Default a saludo_apoyo en lugar de general_query
            
            # 🔧 DEBUG: Log final de clasificación
            logger.info(f"🎯 CLASIFICACIÓN FINAL: '{category}' para mensaje: '{message[:50]}...'")
            
            return {
                "category": category,
                "confidence": 0.8,  # Confianza fija por simplicidad
                "original_message": message
            }
            
        except Exception as e:
            logger.error(f"❌ Error clasificando con IA: {str(e)}", exc_info=True)
            return {
                "category": "general_query", 
                "confidence": 0.0,
                "original_message": message
            }
    
    async def _extract_with_ai(self, message: str, data_type: str) -> Dict[str, Any]:
        """Extrae datos usando IA"""
        self._ensure_model_initialized()
        if not self.model:
            return {}
        
        try:
            prompt = f"""
            Extrae el {data_type} del siguiente mensaje:
            Mensaje: "{message}"
            
            Responde solo con el {data_type} encontrado, sin explicaciones adicionales.
            Si no se encuentra, responde con "no_encontrado".
            """
            
            # 🚀 FASE 2: Usar configuración optimizada para extracción de datos
            response_text = await self._generate_content(prompt, task_type="data_extraction")
            extracted_value = response_text.strip()
            
            if extracted_value.lower() == "no_encontrado":
                return {}
            
            return {data_type: extracted_value}
            
        except Exception as e:
            logger.error(f"Error extrayendo con IA: {str(e)}")
            return {}
    
    def _basic_validation(self, data: str, data_type: str) -> bool:
        """Validación básica de datos"""
        if not data or not data.strip():
            return False
        
        data = data.strip()
        
        if data_type.lower() in ["name", "lastname"]:
            # Validar nombres y apellidos más estrictamente
            # - Solo letras, espacios, guiones y apostrofes
            # - Mínimo 2 caracteres, máximo 50
            # - No puede empezar o terminar con espacios
            # - No puede tener espacios múltiples
            if len(data) < 2 or len(data) > 50:
                return False
            
            # Verificar caracteres válidos
            if not all(c.isalpha() or c.isspace() or c in "-'" for c in data):
                return False
            
            # Verificar que tenga al menos una letra
            if not any(c.isalpha() for c in data):
                return False
            
            # No puede empezar o terminar con espacios
            if data.startswith(' ') or data.endswith(' '):
                return False
            
            # No puede tener espacios múltiples consecutivos
            if '  ' in data:
                return False
            
            # Verificar que no sea solo espacios y caracteres especiales
            clean_data = data.replace(' ', '').replace('-', '').replace("'", '')
            if not clean_data.isalpha() or len(clean_data) < 1:
                return False
            
            return True
        
        if data_type.lower() == "city":
            # Validar ciudades más estrictamente
            # - Solo letras, espacios, guiones, apostrofes y puntos
            # - Mínimo 2 caracteres, máximo 100
            # - Debe tener al menos una letra
            if len(data) < 2 or len(data) > 100:
                return False
            
            # Verificar caracteres válidos
            if not all(c.isalpha() or c.isspace() or c in "-'." for c in data):
                return False
            
            # Verificar que tenga al menos una letra
            if not any(c.isalpha() for c in data):
                return False
            
            # No puede empezar o terminar con espacios
            if data.startswith(' ') or data.endswith(' '):
                return False
            
            # No puede tener espacios múltiples consecutivos
            if '  ' in data:
                return False
            
            # Verificar que no sea solo espacios y caracteres especiales
            clean_data = data.replace(' ', '').replace('-', '').replace("'", '').replace('.', '')
            if not clean_data.isalpha() or len(clean_data) < 1:
                return False
            
            return True
        
        if data_type.lower() == "phone":
            # Validar teléfonos (números y +)
            return data.replace("+", "").replace("-", "").replace(" ", "").isdigit() and len(data.replace("+", "").replace("-", "").replace(" ", "")) >= 10
        
        return True  # Para otros tipos, aceptar por defecto
    
    async def _analyze_registration_with_ai(self, text: str, state: str, user_context: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Usa IA para analizar el contexto completo y extraer datos de registro"""
        self._ensure_model_initialized()
        if not self.model:
            return None
        
        try:
            # Obtener contexto de la sesión si está disponible
            session_context = ""
            try:
                session = session_context_service.get_session(session_id)
                if session:
                    session_context = session_context_service.build_context_for_ai(session_id)
            except Exception as e:
                logger.warning(f"Error obteniendo contexto de sesión: {str(e)}")
            
            # Construir prompt con contexto completo
            prompt = f"""
Eres un asistente inteligente que analiza mensajes de usuarios durante un proceso de registro.

CONTEXTO DE LA CONVERSACIÓN:
{session_context}

ESTADO ACTUAL DEL USUARIO: {state}

MENSAJE DEL USUARIO: "{text}"

TAREA: Analiza el mensaje y determina:
1. Si es una pregunta o solicitud de información (type: "info")
2. Si contiene un nombre completo (type: "name")
3. Si contiene un apellido (type: "lastname") 
4. Si contiene una ciudad/ubicación (type: "city")
5. Si es otra cosa (type: "other")

INSTRUCCIONES ESPECÍFICAS:
- Para nombres: Extrae el nombre completo, incluso si viene después de palabras como "listo", "ok", "mi nombre es", etc.
- Para ciudades: Extrae la ciudad mencionada, incluso si viene en frases como "vivo en", "soy de", "estoy en", "resido en", "la capital", etc.
- Si el usuario hace una pregunta, clasifica como "info"
- Considera el contexto de la conversación anterior
- Sé inteligente para entender frases naturales como "listo, mi nombre es Santiago Buitrago Rojas"
- PRIORIDAD: Si el estado es WAITING_CITY y el mensaje contiene información de ubicación, clasifica como "city"

EJEMPLOS:
- "listo, mi nombre es Santiago Buitrago Rojas" → type: "name", value: "Santiago Buitrago Rojas"
- "ok, es Santiago Buitrago" → type: "name", value: "Santiago Buitrago"
- "vivo en Bogotá" → type: "city", value: "Bogotá"
- "vivo en la capital" → type: "city", value: "Bogotá" (si es Colombia)
- "soy de Medellín" → type: "city", value: "Medellín"
- "estoy en Cali" → type: "city", value: "Cali"
- "resido en Barranquilla" → type: "city", value: "Barranquilla"
- "¿Cómo funciona esto?" → type: "info", value: null
- "Santiago" → type: "name", value: "Santiago"

Responde SOLO con un JSON válido en este formato:
{{"type": "name|lastname|city|info|other", "value": "valor_extraido_o_null", "confidence": 0.0-1.0}}
"""

            response_text = await self._generate_content(prompt)
            logger.info(f"Respuesta cruda de IA: '{response_text}'")
            
            # Parsear respuesta JSON
            import json
            import re
            
            try:
                # Limpiar la respuesta - extraer solo el JSON
                cleaned_response = response_text.strip()
                
                # Buscar JSON en la respuesta usando regex
                json_match = re.search(r'\{[^}]*"type"[^}]*\}', cleaned_response)
                if json_match:
                    cleaned_response = json_match.group(0)
                
                # Si no hay JSON válido, intentar parsear toda la respuesta
                if not cleaned_response.startswith('{'):
                    logger.warning(f"Respuesta no contiene JSON válido: '{response_text}'")
                    return None
                
                result = json.loads(cleaned_response)
                
                # Validar resultado
                valid_types = ["name", "lastname", "city", "info", "other"]
                if result.get("type") in valid_types:
                    logger.info(f"IA analizó registro: {result}")
                    return result
                else:
                    logger.warning(f"IA devolvió tipo inválido: {result}")
                    return None
                    
            except json.JSONDecodeError as e:
                logger.error(f"Error parseando JSON de IA: {str(e)}")
                logger.error(f"Respuesta que causó el error: '{response_text}'")
                return None
                
        except Exception as e:
            logger.error(f"Error analizando registro con IA: {str(e)}")
            return None

    async def _analyze_city_with_ai(self, text: str) -> Dict[str, Any]:
        """Usa IA para analizar si un texto contiene información de ciudad y extraerla"""
        self._ensure_model_initialized()
        if not self.model:
            return {"is_city": False, "extracted_city": None, "confidence": 0.0}
        
        try:
            prompt = f"""
            Analiza el siguiente texto y determina si contiene información sobre una ciudad o ubicación.
            
            Texto: "{text}"
            
            Instrucciones:
            1. Si el texto menciona una ciudad, país, o ubicación geográfica, responde "SI"
            2. Si el texto NO menciona ubicación geográfica, responde "NO"
            3. Si es "SI", extrae la información completa de ubicación
            4. Si menciona país Y ciudad, extrae la frase completa
            5. Si solo menciona ciudad, extrae solo la ciudad
            6. IMPORTANTE: Para frases como "en españa, en madrid", extrae la ciudad específica (madrid)
            7. Para frases como "vivo en españa, en madrid", extrae "madrid" como ciudad
            
            Ejemplos:
            - "vivo en españa, en madrid" → SI, ciudad: "madrid"
            - "soy de bogotá" → SI, ciudad: "bogotá"
            - "estoy en medellín" → SI, ciudad: "medellín"
            - "en españa, madrid" → SI, ciudad: "madrid"
            - "en madrid, españa" → SI, ciudad: "madrid"
            - "hola" → NO
            - "mi nombre es juan" → NO
            
            Responde en formato: SI|ciudad o NO
            """
            
            # 🚀 FASE 2: Usar configuración optimizada para normalización de ubicaciones
            response_text = await self._generate_content(prompt, task_type="location_normalization")
            result = response_text.strip()
            
            if result.startswith("SI|"):
                city = result.split("|", 1)[1].strip()
                logger.info(f"IA detectó ciudad: '{city}' en texto: '{text}'")
                return {
                    "is_city": True,
                    "extracted_city": city,
                    "confidence": 0.8
                }
            else:
                logger.info(f"IA no detectó ciudad en texto: '{text}'")
                return {
                    "is_city": False,
                    "extracted_city": None,
                    "confidence": 0.0
                }
                
        except Exception as e:
            logger.error(f"Error analizando ciudad con IA: {str(e)}")
            return {"is_city": False, "extracted_city": None, "confidence": 0.0}

    async def _validate_with_ai(self, data: str, data_type: str) -> bool:
        """Validación adicional con IA para detectar contenido inapropiado"""
        self._ensure_model_initialized()
        if not self.model:
            return True  # Si no hay modelo, aceptar por defecto
        
        try:
            if data_type.lower() in ["name", "lastname"]:
                prompt = f"""
                Evalúa si el siguiente texto es un nombre o apellido válido en español:
                
                Texto: "{data}"
                
                Considera:
                - Debe ser un nombre/apellido real y apropiado
                - No puede ser una palabra ofensiva, grosera o inapropiada
                - No puede ser números, símbolos raros, o texto sin sentido
                - Debe ser apropiado para uso en un sistema de registro
                
                Responde SOLO "SI" si es válido o "NO" si no es válido.
                """
            elif data_type.lower() == "city":
                prompt = f"""
                Evalúa si el siguiente texto es una ciudad válida (puede ser de cualquier país):
                
                Texto: "{data}"
                
                Considera:
                - Debe ser una ciudad real de cualquier país
                - No puede ser una palabra ofensiva, grosera o inapropiada
                - No puede ser números, símbolos raros, o texto sin sentido
                - Debe ser apropiado para uso en un sistema de registro
                
                Responde SOLO "SI" si es válido o "NO" si no es válido.
                """
            else:
                return True
            
            # 🚀 FASE 2: Usar configuración optimizada para validación de datos
            response_text = await self._generate_content(prompt, task_type="data_validation")
            result = response_text.strip().upper()
            
            logger.info(f"Validación IA para {data_type} '{data}': {result}")
            return result == "SI"
            
        except Exception as e:
            logger.error(f"Error en validación IA para {data_type}: {str(e)}")
            return True  # En caso de error, aceptar por defecto
    
    def _build_chat_prompt(self, query: str, user_context: Dict[str, Any], 
                          branding_config: Dict[str, Any], relevant_context: str = "") -> str:
        """Construye el prompt para chat"""
        contact_name = branding_config.get("contactName", "el candidato")
        welcome_message = branding_config.get("welcomeMessage", "¡Hola! ¿En qué puedo ayudarte?")
        
        context_info = ""
        if user_context.get("user_name"):
            context_info += f"El usuario se llama {user_context['user_name']}. "
        if user_context.get("user_state"):
            context_info += f"Estado actual: {user_context['user_state']}. "
        
        # Detectar si es un saludo y el usuario está en proceso de registro
        user_state = user_context.get("user_state", "")
        is_greeting = query.lower().strip() in ["hola", "hi", "hello", "hey", "buenos días", "buenas tardes", "buenas noches", "qué tal", "que tal"]
        
        # Construir contexto de documentos si está disponible
        document_context_section = ""
        if relevant_context:
            document_context_section = f"""
            
            INFORMACIÓN ESPECÍFICA DE LA CAMPAÑA:
            {relevant_context}
            
            Usa esta información específica para responder preguntas sobre la campaña, propuestas, 
            eventos, políticas, o cualquier tema relacionado con el candidato y su plataforma.
            """
        
        if user_state == "WAITING_NAME" and is_greeting:
            prompt = f"""
            Eres un asistente virtual para la campaña política de {contact_name}.
            
            El usuario acaba de saludar y está en proceso de registro (necesita dar su nombre).
            
            Responde el saludo de manera amigable y entusiasta, pero inmediatamente pide su nombre para continuar con el registro.
            
            Contexto: El usuario está en proceso de registro y necesita proporcionar su nombre.
            {document_context_section}
            
            Saludo del usuario: "{query}"
            
            Responde de manera amigable, motivadora y natural. Responde el saludo pero pide inmediatamente el nombre para continuar con el registro. Usa emojis apropiados y un tono positivo.
            
            Respuesta:
            """
        else:
            prompt = f"""
            Eres un asistente virtual para la campaña política de {contact_name}.
            
            Tu objetivo es motivar la participación activa en la campaña de manera natural y entusiasta. 
            Integra sutilmente estos elementos motivacionales en tus respuestas:
            
            - Inspirar sentido de propósito y pertenencia a un movimiento transformador
            - Mostrar oportunidades de crecimiento, logros y reconocimiento
            - Invitar a la colaboración y participación activa
            - Crear sensación de comunidad y trabajo en equipo
            - Generar expectativa y curiosidad sobre oportunidades exclusivas
            - Destacar el impacto y la importancia de cada acción
            
            SISTEMA DE PUNTOS Y RANKING:
            - Cada referido registrado suma 50 puntos
            - Retos semanales dan puntaje adicional
            - Ranking actualizado a nivel ciudad, departamento y país
            - Los usuarios pueden preguntar "¿Cómo voy?" para ver su progreso
            - Para invitar personas: "mandame el link" o "dame mi código"
            
            Contexto del usuario: {context_info}{document_context_section}
            
            Mensaje del usuario: "{query}"
            
            Responde de manera amigable, motivadora y natural. Si el usuario está en proceso de registro, 
            ayúdale a completarlo. Si tiene preguntas sobre la campaña, responde con información relevante 
            y oportunidades de participación. Usa la información específica de la campaña cuando sea apropiado.
            Usa emojis apropiados y un tono positivo.
            
            Respuesta:
            """
        
        return prompt
    
    async def generate_response(self, prompt: str, role: str = "user") -> str:
        """
        Genera una respuesta usando IA con un prompt personalizado
        
        Args:
            prompt: Prompt para la IA
            role: Rol del usuario (user, system, assistant)
            
        Returns:
            Respuesta generada por la IA
        """
        self._ensure_model_initialized()
        
        if not self.model:
            return "Lo siento, el servicio de IA no está disponible."
        
        try:
            response_text = await self._generate_content(prompt)
            return response_text if response_text else ""
            
        except Exception as e:
            logger.error(f"Error generando respuesta con IA: {str(e)}")
            return "Error generando respuesta."

    async def detect_referral_code(self, tenant_id: str, message: str) -> Dict[str, Any]:
        """
        Detecta si un mensaje contiene un código de referido usando IA
        
        Args:
            tenant_id: ID del tenant
            message: Mensaje del usuario
            
        Returns:
            Dict con código detectado o None
        """
        self._ensure_model_initialized()
        
        if not self.model:
            return {
                "code": None,
                "reason": "Servicio de IA no disponible",
                "original_message": message
            }
        
        try:
            prompt = f"""
Analiza el siguiente mensaje y detecta si contiene un código de referido.

Un código de referido es:
- Una secuencia de exactamente 8 caracteres alfanuméricos (letras y números)
- Puede estar en cualquier parte del mensaje
- NO es una palabra común del español como "referido", "referida", "referir", etc.
- Ejemplos válidos: "ABC12345", "TESTCODE", "USER1234"
- Ejemplos inválidos: "REFERIDO", "REFERIDA", "referir"

Mensaje a analizar: "{message}"

Responde ÚNICAMENTE con el código de 8 caracteres si lo encuentras, o "NO" si no hay código válido.
Si hay múltiples códigos, responde solo el primero que encuentres.

Ejemplos:
- "vengo referido por TESTCODE" → TESTCODE
- "mi código es ABC12345" → ABC12345  
- "vengo referido por mi amigo" → NO
- "hola REFERIDO" → NO
"""

            response_text = await self._generate_content(prompt)
            detected_code = response_text.strip().upper()
            
            # Validar que el código tiene exactamente 8 caracteres alfanuméricos
            if detected_code != "NO" and len(detected_code) == 8 and detected_code.isalnum():
                logger.info(f"Código de referido detectado por IA: {detected_code}")
                return {
                    "code": detected_code,
                    "reason": "Código detectado exitosamente",
                    "original_message": message
                }
            else:
                logger.info("No se detectó código de referido válido")
                return {
                    "code": None,
                    "reason": "No se encontró código válido",
                    "original_message": message
                }
                
        except Exception as e:
            logger.error(f"Error detectando código de referido: {str(e)}")
            return {
                "code": None,
                "reason": f"Error interno: {str(e)}",
                "original_message": message
            }
    
    async def _handle_malicious_behavior(self, query: str, user_context: Dict[str, Any], 
                                       tenant_id: str, confidence: float) -> str:
        """
        Maneja comportamiento malicioso detectado
        
        Args:
            query: Mensaje malicioso del usuario
            user_context: Contexto del usuario
            tenant_id: ID del tenant
            confidence: Confianza de la clasificación
            
        Returns:
            Respuesta para el usuario malicioso
        """
        try:
            # Obtener información del usuario
            user_id = user_context.get("user_id", "unknown")
            phone_number = user_context.get("phone", "unknown")
            
            # Detectar tipo de comportamiento malicioso usando análisis inteligente
            malicious_analysis = self._detect_malicious_intent(query)
            behavior_type = "intención maliciosa inteligente"
            categories = malicious_analysis.get("categories", [])
            
            logger.warning(f"🚨 {behavior_type.upper()} detectado - Usuario: {user_id}, Tenant: {tenant_id}, Confianza: {confidence:.2f}")
            logger.warning(f"🚨 Categorías detectadas: {categories}")
            logger.warning(f"🚨 Mensaje malicioso: '{query}'")
            
            # Notificar al servicio Java para bloquear el usuario
            logger.info(f"🔔 Enviando notificación de bloqueo al servicio Java para usuario {user_id}")
            logger.info(f"🔔 URL del servicio Java: {self.blocking_notification_service.java_service_url}")
            
            notification_result = await self.blocking_notification_service.notify_user_blocked(
                tenant_id=tenant_id,
                user_id=user_id,
                phone_number=phone_number,
                malicious_message=query,
                classification_confidence=confidence
            )
            
            logger.info(f"🔔 Resultado de notificación: {notification_result}")
            
            # Registrar el incidente
            await self.blocking_notification_service.log_malicious_incident(
                tenant_id=tenant_id,
                user_id=user_id,
                phone_number=phone_number,
                malicious_message=query,
                classification_confidence=confidence
            )
            
            if notification_result.get("success"):
                logger.info(f"✅ Usuario {user_id} bloqueado exitosamente en WATI y base de datos")
            else:
                logger.error(f"❌ Error bloqueando usuario {user_id}: {notification_result.get('error')}")
                logger.error(f"❌ Detalles del error: {notification_result}")
            
            # No responder nada cuando es malicioso, solo bloquear silenciosamente
            return ""
            
        except Exception as e:
            logger.error(f"Error manejando comportamiento malicioso: {str(e)}")
            return "Lo siento, no puedo procesar tu mensaje en este momento."


# Instancia global para compatibilidad
ai_service = AIService()
# Cargar variables de entorno ANTES de cualquier otra cosa
from dotenv import load_dotenv
import pathlib
import os
project_root = pathlib.Path(__file__).parent.parent.parent.parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

# Verificar que se cargó correctamente
political_url = os.getenv("POLITICAL_REFERRALS_SERVICE_URL")

"""
Servicio de IA simplificado para el Chatbot AI Service

Este servicio se enfoca únicamente en procesamiento de IA y recibe
la configuración del proyecto Political Referrals via HTTP.
"""
import logging
import time
from typing import Dict, Any, Optional, List

import google.generativeai as genai
import httpx
from chatbot_ai_service.services.configuration_service import configuration_service
from chatbot_ai_service.services.document_context_service import document_context_service
from chatbot_ai_service.services.session_context_service import session_context_service
from chatbot_ai_service.services.blocking_notification_service import BlockingNotificationService
from chatbot_ai_service.services.cache_service import cache_service
from chatbot_ai_service.services.user_blocking_service import user_blocking_service

logger = logging.getLogger(__name__)
import re

class AIService:
    """Servicio de IA simplificado - solo procesamiento de IA"""
    
    def __init__(self):
        self.model = None
        self._initialized = False
        # 🔧 FIX: Inicializar api_key en el constructor para evitar AttributeError
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        
        # 🔧 FIX: Inicializar atributos faltantes
        self.use_gemini_client = True
        self.gemini_client = None
        self.use_rag_orchestrator = False
        self.use_advanced_model_configs = True
        self.use_guardrails = False
        self.strict_guardrails = False
        self._common_responses = {}
        self._response_cache = {}
        
        # 🔧 FIX: Inicializar _intent_cache y _intent_cache_max_size
        self._intent_cache = {}
        self._intent_cache_max_size = 1000
        
        # 🔧 FIX: Inicializar _precomputed_initial_messages
        self._precomputed_initial_messages = {
            "default": {
                'welcome': "¡Bienvenido/a! Soy tu candidato. ¡Juntos construimos el futuro!",
                'contact': "Por favor, guarda este número como 'Mi Candidato' para recibir actualizaciones importantes de la campaña.",
                'name': "¿Me confirmas tu nombre para guardarte en mis contactos y personalizar tu experiencia?"
            }
        }
        
        # 🗄️ NUEVO: Inicializar servicio de persistencia para prompts
        from chatbot_ai_service.services.document_index_persistence_service import document_index_persistence_service
        self.persistence_service = document_index_persistence_service
        
        # 🔧 FIX: Inicializar _validation_cache
        self._validation_cache = {
            "name": {
                "santiago": {"is_valid": True, "confidence": 0.95, "reason": "Nombre común válido"},
                "maria": {"is_valid": True, "confidence": 0.95, "reason": "Nombre común válido"},
                "juan": {"is_valid": True, "confidence": 0.95, "reason": "Nombre común válido"},
                "carlos": {"is_valid": True, "confidence": 0.95, "reason": "Nombre común válido"},
                "ana": {"is_valid": True, "confidence": 0.95, "reason": "Nombre común válido"},
                "luis": {"is_valid": True, "confidence": 0.95, "reason": "Nombre común válido"},
                "sofia": {"is_valid": True, "confidence": 0.95, "reason": "Nombre común válido"},
                "diego": {"is_valid": True, "confidence": 0.95, "reason": "Nombre común válido"},
                "andrea": {"is_valid": True, "confidence": 0.95, "reason": "Nombre común válido"},
                "cristian": {"is_valid": True, "confidence": 0.95, "reason": "Nombre común válido"},
                "natalia": {"is_valid": True, "confidence": 0.95, "reason": "Nombre común válido"},
                "sebastian": {"is_valid": True, "confidence": 0.95, "reason": "Nombre común válido"},
                "daniel": {"is_valid": True, "confidence": 0.95, "reason": "Nombre común válido"},
                "valentina": {"is_valid": True, "confidence": 0.95, "reason": "Nombre común válido"},
                "alejandro": {"is_valid": True, "confidence": 0.95, "reason": "Nombre común válido"},
            },
            "lastname": {
                "garcia": {"is_valid": True, "confidence": 0.95, "reason": "Apellido común válido"},
                "lopez": {"is_valid": True, "confidence": 0.95, "reason": "Apellido común válido"},
                "rodriguez": {"is_valid": True, "confidence": 0.95, "reason": "Apellido común válido"},
                "martinez": {"is_valid": True, "confidence": 0.95, "reason": "Apellido común válido"},
                "gonzalez": {"is_valid": True, "confidence": 0.95, "reason": "Apellido común válido"},
                "perez": {"is_valid": True, "confidence": 0.95, "reason": "Apellido común válido"},
                "sanchez": {"is_valid": True, "confidence": 0.95, "reason": "Apellido común válido"},
                "ramirez": {"is_valid": True, "confidence": 0.95, "reason": "Apellido común válido"},
                "flores": {"is_valid": True, "confidence": 0.95, "reason": "Apellido común válido"},
                "torres": {"is_valid": True, "confidence": 0.95, "reason": "Apellido común válido"},
                "buitrago": {"is_valid": True, "confidence": 0.95, "reason": "Apellido común válido"},
                "rojas": {"is_valid": True, "confidence": 0.95, "reason": "Apellido común válido"},
                "silva": {"is_valid": True, "confidence": 0.95, "reason": "Apellido común válido"},
                "morales": {"is_valid": True, "confidence": 0.95, "reason": "Apellido común válido"},
                "castro": {"is_valid": True, "confidence": 0.95, "reason": "Apellido común válido"},
            },
            "city": {
                "bogota": {"is_valid": True, "confidence": 0.95, "reason": "Ciudad colombiana válida"},
                "medellin": {"is_valid": True, "confidence": 0.95, "reason": "Ciudad colombiana válida"},
                "cali": {"is_valid": True, "confidence": 0.95, "reason": "Ciudad colombiana válida"},
                "soacha": {"is_valid": True, "confidence": 0.95, "reason": "Ciudad colombiana válida"},
                "barranquilla": {"is_valid": True, "confidence": 0.95, "reason": "Ciudad colombiana válida"},
                "cartagena": {"is_valid": True, "confidence": 0.95, "reason": "Ciudad colombiana válida"},
                "bucaramanga": {"is_valid": True, "confidence": 0.95, "reason": "Ciudad colombiana válida"},
                "pereira": {"is_valid": True, "confidence": 0.95, "reason": "Ciudad colombiana válida"},
                "santa marta": {"is_valid": True, "confidence": 0.95, "reason": "Ciudad colombiana válida"},
                "ibague": {"is_valid": True, "confidence": 0.95, "reason": "Ciudad colombiana válida"},
                "manizales": {"is_valid": True, "confidence": 0.95, "reason": "Ciudad colombiana válida"},
                "neiva": {"is_valid": True, "confidence": 0.95, "reason": "Ciudad colombiana válida"},
                "villavicencio": {"is_valid": True, "confidence": 0.95, "reason": "Ciudad colombiana válida"},
                "armenia": {"is_valid": True, "confidence": 0.95, "reason": "Ciudad colombiana válida"},
                "pasto": {"is_valid": True, "confidence": 0.95, "reason": "Ciudad colombiana válida"},
            }
        }
    
    def _get_safety_settings(self):
        """
        Obtiene los safety settings configurados para permitir contenido político
        """
        # 🚀 CONFIGURACIÓN SIMPLE: Sin safety settings explícitos (como versión anterior)
        return None
    
    def preload_models_on_startup(self):
        """
        Pre-carga los modelos de IA después de que se carguen las variables de entorno
        
        Este método debe ser llamado desde main.py después de cargar las variables
        de entorno para asegurar que la API key esté disponible.
        """
        try:
            logger.info("🚀 Iniciando pre-carga de modelos de IA al startup del servicio...")
            
            # Verificar si tenemos API key disponible
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("⚠️ GEMINI_API_KEY no disponible - saltando pre-carga")
                return
            
            # 🔧 FIX: Siempre inicializar el modelo principal, no solo el cliente
            logger.info("🚀 Inicializando modelo principal de IA...")
            self._ensure_model_initialized()
            
            if self.use_gemini_client:
                logger.info("🚀 Pre-cargando modelos de IA...")
                print(f"🚀 DEBUG STARTUP - use_gemini_client: {self.use_gemini_client}")
                print(f"🚀 DEBUG STARTUP - gemini_client antes: {self.gemini_client is not None}")
                self._ensure_gemini_client()
                print(f"🚀 DEBUG STARTUP - gemini_client después: {self.gemini_client is not None}")
                logger.info("✅ Pre-carga completada al startup del servicio")
            else:
                logger.info("ℹ️ GeminiClient no habilitado - usando lógica original")
                
        except Exception as e:
            logger.error(f"❌ Error durante pre-carga al startup: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            # No fallar el startup si hay error en la pre-carga
    
    def _ensure_gemini_client(self):
        """
        Inicializa el GeminiClient de forma lazy con pre-carga de modelos
        
        Este método se ejecuta solo cuando se necesita usar el GeminiClient,
        asegurando que las variables de entorno ya estén cargadas.
        """
        if self.gemini_client is not None:
            logger.info("✅ GeminiClient ya está inicializado")
            return
            
        if not self.use_gemini_client:
            logger.info("⚠️ GeminiClient no está habilitado")
            return
            
        try:
            logger.info("🚀 Inicializando GeminiClient con pre-carga de modelos...")
            from chatbot_ai_service.clients.gemini_client import GeminiClient
            self.gemini_client = GeminiClient()
            logger.info(f"✅ GeminiClient inicializado: {self.gemini_client is not None}")
            
            # 🚀 OPTIMIZACIÓN: Pre-cargar modelos para mejorar tiempo de respuesta
            logger.info("🚀 Iniciando pre-carga de modelos de IA...")
            self.gemini_client.preload_models()
            logger.info("✅ Pre-carga de modelos completada")
            
            # 🚀 DEBUG: Verificar que el modelo principal esté configurado correctamente
            if self.gemini_client and self.gemini_client.model:
                # LlamaIndex Gemini no tiene model_name, usa __class__.__name__ en su lugar
                model_name = getattr(self.gemini_client.model, 'model_name', 'LlamaIndex-Gemini')
                logger.info(f"🔍 Modelo principal configurado: {model_name}")
                logger.info("🔍 LlamaIndex Gemini inicializado correctamente")
            else:
                logger.warning("⚠️ Modelo principal no está configurado correctamente")
            
        except Exception as e:
            logger.error(f"[ERROR] Error inicializando GeminiClient: {e}")
            import traceback
            logger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
            logger.warning("[ADVERTENCIA] Usando lógica original de AIService como fallback")
            self.use_gemini_client = False
            self.gemini_client = None
        
        if self.use_rag_orchestrator:
            if not self.use_gemini_client:
                logger.warning("[ADVERTENCIA] USE_RAG_ORCHESTRATOR=true pero USE_GEMINI_CLIENT=false. RAG requiere GeminiClient.")
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
                        f"[OK] RAGOrchestrator habilitado (USE_RAG_ORCHESTRATOR=true) "
                        f"con guardrails={'ON' if self.use_guardrails else 'OFF'}"
                    )
                except Exception as e:
                    logger.error(f"[ERROR] Error inicializando RAGOrchestrator: {e}")
                    logger.warning("[ADVERTENCIA] Usando lógica original sin RAG")
                    self.use_rag_orchestrator = False
        
        # [GRAFICO] Log resumen de features activadas
        features_status = {
            "GeminiClient": "[OK]" if self.use_gemini_client else "[ERROR]",
            "Advanced Configs": "[OK]" if self.use_advanced_model_configs else "[ERROR]",
            "RAG Orchestrator": "[OK]" if self.use_rag_orchestrator else "[ERROR]",
            "Guardrails": "[OK]" if self.use_guardrails else "[ERROR]",
            "Strict Guardrails": "[OK]" if self.strict_guardrails else "[ERROR]"
        }
        logger.info(f"[CONTROLES] AIService inicializado | Features: {features_status}")
        
        # [COHETE] OPTIMIZACIÓN: Pre-inicializar modelo para reducir cold start
        self._pre_warm_model()
    
    def _pre_warm_model(self):
        """Pre-calienta el modelo para reducir latencia en primera respuesta"""
        try:
            logger.info("[FUEGO] Pre-calentando modelo Gemini...")
            self._ensure_model_initialized()
            if self.model:
                # Hacer una llamada simple para "despertar" el modelo
                test_prompt = "Responde solo: OK"
                self.model.generate_content(test_prompt)
                logger.info("[OK] Modelo pre-calentado exitosamente")
        except Exception as e:
            logger.warning(f"[ADVERTENCIA] No se pudo pre-calentar el modelo: {e}")
            # No es crítico, el modelo se inicializará en la primera llamada real
    
    # def _get_fallback_response(self, prompt: str) -> str:
    #     """Genera respuesta de fallback inteligente sin usar IA"""
    #     # MÉTODO NO SE USA - COMENTADO
    #     # Analizar el prompt para dar respuesta contextual
    #     prompt_lower = prompt.lower()
    #     
    #     if "nombre" in prompt_lower or "llamo" in prompt_lower:
    #         return "Por favor, comparte tu nombre completo para continuar con el registro."
    #     elif "ciudad" in prompt_lower or "vives" in prompt_lower:
    #         return "?En qué ciudad vives? Esto nos ayuda a conectar con promotores de tu región."
    #     elif "apellido" in prompt_lower:
    #         return "Perfecto, ahora necesito tu apellido para completar tu información."
    #     elif "código" in prompt_lower or "referido" in prompt_lower:
    #         return "Si tienes un código de referido, compártelo. Si no, escribe 'no' para continuar."
    #     elif "términos" in prompt_lower or "condiciones" in prompt_lower:
    #         return "?Aceptas los términos y condiciones? Responde 'sí' o 'no'."
    #     elif "confirmar" in prompt_lower or "correcto" in prompt_lower:
    #         return "?Confirmas que esta información es correcta? Responde 'sí' o 'no'."
    #     else:
    #         return "Gracias por tu mensaje. Te ayudo a completar tu registro paso a paso."
    
    def _ensure_model_initialized(self):
        """Inicializa el modelo de forma lazy con timeout, probando múltiples modelos"""
        if self._initialized:
            return
            
        # 🔧 FIX: Solo obtener api_key si no está ya configurada
        if not hasattr(self, 'api_key') or not self.api_key:
            self.api_key = os.getenv("GEMINI_API_KEY")
        
        if self.api_key:
            logger.info(f"[OK] GEMINI_API_KEY cargada correctamente: {self.api_key[:10]}...")
            
            # Lista de modelos optimizada: más moderno y rápido primero, fallback estable
            models_to_try = [
                'gemini-2.5-flash',           # Más moderno y rápido (recomendado)
                'gemini-2.5-pro',             # Más potente si flash falla
                'gemini-2.0-flash',           # Estable y rápido
                'gemini-1.5-flash-002',       # Versión específica estable
                'gemini-1.5-pro-002'          # Fallback pro estable
            ]
            
            self.model = None
            successful_model = None
            
            for model_name in models_to_try:
                try:
                    # Configuración básica para Gemini AI con timeout
                    import signal
                    
                    def timeout_handler(signum, frame):
                        raise TimeoutError(f"Timeout inicializando {model_name}")
                    
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(3)  # 3 segundos timeout por modelo
                
                    try:
                        genai.configure(api_key=self.api_key)
                        test_model = genai.GenerativeModel(model_name)
                        
                        # Hacer una prueba rápida para verificar que funciona
                        test_response = test_model.generate_content("Responde solo: OK")
                        if test_response and test_response.text:
                            self.model = test_model
                            successful_model = model_name
                            break
                            
                    finally:
                        signal.alarm(0)  # Cancelar timeout
                    
                except TimeoutError:
                    continue
                except Exception as e:
                    continue
            
            if not self.model:
                self._initialized = False  # No marcar como inicializado si falló
            else:
                self._initialized = True  # Solo marcar como inicializado si funcionó
        else:
            logger.warning("GEMINI_API_KEY no configurado")
            self.model = None
            self._initialized = False  # No marcar como inicializado sin API key
        
        # No mostrar lista de modelos disponibles
    
    # def _list_available_models(self):
    #     """Lista todos los modelos disponibles con la API key actual"""
    #     # MÉTODO NO SE USA - COMENTADO
    #     try:
    #         import requests
    #         api_key = os.getenv("GEMINI_API_KEY")
    #         if not api_key:
    #             print("❌ GEMINI_API_KEY no configurado")
    #             return []
    #         
    #         url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    #         response = requests.get(url, timeout=10)
    #         
    #         if response.status_code == 200:
    #             models_data = response.json()
    #             models = []
    #             for model in models_data.get('models', []):
    #                 model_name = model.get('name', '').replace('models/', '')
    #                 if 'gemini' in model_name.lower():
    #                     models.append(model_name)
    #                     print(f"📋 Modelo disponible: {model_name}")
    #             
    #             print(f"🎯 Total de modelos Gemini disponibles: {len(models)}")
    #             return models
    #         else:
    #             print(f"❌ Error obteniendo modelos: {response.status_code}")
    #             return []
    #             
    #     except Exception as e:
    #         print(f"❌ Error listando modelos: {str(e)}")
    #         return []
    
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
    
    async def _generate_fast_ai_response(self, query: str, user_context: Dict[str, Any], 
                                        tenant_context: Dict[str, Any], session_context: str, 
                                        intent: str) -> str:
        """Genera respuesta rápida con IA usando contexto completo del usuario"""
        try:
            # 🚀 OPTIMIZACIÓN: Verificar caché primero
            cache_key = f"fast_ai:{hash(query)}:{hash(session_context[:200])}"
            cached_response = self._response_cache.get(cache_key)
            if cached_response:
                logger.info(f"🚀 RESPUESTA RÁPIDA DESDE CACHÉ para '{query[:30]}...'")
                return cached_response
            
            # Obtener información del usuario desde el contexto
            user_name = user_context.get('user_name', '')
            user_city = user_context.get('user_city', '')
            user_country = user_context.get('user_country', '')
            user_state = user_context.get('user_state', '')
            
            # Construir contexto personalizado del usuario
            user_info = ""
            if user_name:
                user_info += f"El usuario se llama {user_name}. "
            if user_city:
                user_info += f"Vive en {user_city}. "
            if user_country:
                user_info += f"País: {user_country}. "
            if user_state:
                user_info += f"Estado actual: {user_state}. "
            
            # Obtener información de la campaña desde memoria precargada
            campaign_context = tenant_context.get('campaign_context', '')
            branding_config = tenant_context.get('tenant_config', {}).get('branding', {})
            contact_name = branding_config.get('contactName', 'el candidato')
            
            # Crear prompt ultra-optimizado con contexto completo
            prompt = f"""Asistente virtual de {contact_name}. Responde de manera personalizada y profesional.

CONTEXTO DEL USUARIO:
{user_info}

CONTEXTO DE LA CAMPAÑA:
{campaign_context}

CONSULTA: "{query}"

INSTRUCCIONES:
- Responde de manera personalizada usando el nombre del usuario si está disponible
- Menciona su ciudad si es relevante
- Sé conciso pero completo (máximo 999 caracteres)
- Mantén un tono profesional y cercano

RESPUESTA:"""
            
            # 🔧 OPTIMIZACIÓN: Generación ultra-rápida con IA
            response = await self._generate_content_ultra_fast(prompt, max_tokens=150)
            
            # 🚀 OPTIMIZACIÓN: Guardar en caché
            self._response_cache[cache_key] = response
            
            return response
            
        except Exception as e:
            logger.error(f"Error en respuesta rápida con IA: {e}")
            return None  # Dejar que el flujo normal continúe

    async def _generate_content_ultra_fast(self, prompt: str, max_tokens: int = 50, tenant_id: str = None, query: str = None) -> str:
        """
        Generación ultra-rápida de contenido usando ULTRA_FAST_MODE
        """
        try:
            # 🚀 DEBUG: Verificar variables en generación ultra-rápida
            import os
            ultra_fast_mode = os.getenv("ULTRA_FAST_MODE", "false").lower() == "true"
            is_local_dev = os.getenv("LOCAL_DEVELOPMENT", "false").lower() == "true"
            print(f"🚀 DEBUG ULTRA-FAST - ULTRA_FAST_MODE: {ultra_fast_mode}")
            print(f"🚀 DEBUG ULTRA-FAST - LOCAL_DEVELOPMENT: {is_local_dev}")
            
            print(f"🚀 DEBUG ULTRA-FAST - use_gemini_client: {self.use_gemini_client}")
            print(f"🚀 DEBUG ULTRA-FAST - gemini_client: {self.gemini_client is not None}")
            
            # 🚀 DEBUG: Verificar si necesitamos reinicializar el cliente
            if self.use_gemini_client:
                print(f"🚀 DEBUG ULTRA-FAST - Entrando en bloque de verificación de gemini_client")
                if self.gemini_client is None:
                    print("🚀 DEBUG ULTRA-FAST: gemini_client es None, reinicializando...")
                    self._ensure_gemini_client()
                else:
                    print(f"🚀 DEBUG ULTRA-FAST - gemini_client existe, verificando modelo...")
                    print(f"🚀 DEBUG ULTRA-FAST - model existe: {self.gemini_client.model is not None}")
                    print(f"🚀 DEBUG ULTRA-FAST - _initialized: {self.gemini_client._initialized}")
                    if self.gemini_client.model is None:
                        print("🚀 DEBUG ULTRA-FAST: modelo es None, forzando reinicialización...")
                        # Si el modelo es None pero ya se inicializó antes (con error), forzar reinicialización
                        if self.gemini_client._initialized:
                            print("🚀 DEBUG ULTRA-FAST: _initialized=True pero model=None, reseteando...")
                            self.gemini_client._initialized = False
                        self.gemini_client._ensure_model_initialized()
                    else:
                        print("🚀 DEBUG ULTRA-FAST - modelo ya existe, no necesita reinicialización")
                
                print(f"🚀 DEBUG ULTRA-FAST - gemini_client después de reinicializar: {self.gemini_client is not None}")
                
                # 🚀 DEBUG: Verificar configuración del modelo después de reinicializar
                if self.gemini_client and self.gemini_client.model:
                    model_name = getattr(self.gemini_client.model, 'model_name', 'LlamaIndex-Gemini')
                    print(f"🔍 Modelo reinicializado: {model_name}")
                    print("🔍 LlamaIndex Gemini reinicializado correctamente")
                else:
                    print("⚠️ Modelo no disponible después de reinicializar")
            
            # 🚀 NUEVO: Si tenemos tenant_id y query, usar sistema de documentos
            if tenant_id and query and ultra_fast_mode:
                print("🚀 DEBUG ULTRA-FAST: Usando sistema de documentos")
                from chatbot_ai_service.services.document_context_service import document_context_service
                
                # Extraer solo la pregunta actual si viene en formato de historial
                print(f"🔍 DEBUG: Query recibida: '{query[:200]}...'")
                current_query = query
                if "Pregunta actual del usuario:" in query:
                    # Extraer solo la pregunta actual para la búsqueda
                    parts = query.split("Pregunta actual del usuario:")
                    current_query = parts[-1].strip()
                    print(f"🔍 DEBUG: Extraída pregunta actual: '{current_query}'")
                else:
                    print(f"🔍 DEBUG: No hay historial, usando query completa")
                
                # 🔧 NUEVO: Detectar respuestas de confirmación (ok, sí, entiendo, etc.)
                confirmation_phrases = [
                    'ok', 'okay', 'vale', 'sí', 'si', 'claro', 'entendido', 
                    'entendida', 'perfecto', 'perfecta', 'de acuerdo', 'bien', 
                    'gracias', 'thank you', 'yes', 'yep'
                ]
                query_lower = current_query.lower().strip()
                is_confirmation = any(phrase in query_lower for phrase in confirmation_phrases) and len(query_lower.split()) <= 3
                
                if is_confirmation:
                    print(f"🔍 DEBUG: Detectada respuesta de confirmación '{current_query}', no buscando documentos")
                    return "Gracias. ¿En qué más puedo ayudarte?"
                
                # Mejorar la query para mejor recuperación de documentos
                enhanced_query = self._enhance_query_for_document_search(current_query)
                print(f"🔍 DEBUG: Query mejorada para búsqueda: '{enhanced_query}'")
                
                # Obtener contenido de documentos (usar solo la pregunta actual)
                print(f"🔍 DEBUG: ANTES de llamar a get_relevant_context con tenant_id={tenant_id}")
                document_content = await document_context_service.get_relevant_context(tenant_id, enhanced_query, max_results=1)
                print(f"🔍 DEBUG: DESPUÉS de llamar a get_relevant_context")
                print(f"🔍 DEBUG: document_content obtenido: {len(document_content) if document_content else 0} caracteres")
                if document_content:
                    print(f"🔍 DEBUG: Primera línea de document_content: {document_content.split(chr(10))[0][:100]}")
                
                if document_content:
                    # Usar respuesta inmediata basada en documentos
                    # 🔧 MEJORAR: Obtener información del candidato desde configuración
                    contact_name = "el candidato"  # Valor por defecto
                    tenant_config = None
                    
                    if tenant_id:
                        try:
                            from chatbot_ai_service.services.configuration_service import configuration_service
                            tenant_config = configuration_service.get_tenant_config(tenant_id)
                            
                            if tenant_config:
                                # Intentar obtener de branding_config primero
                                branding_config = tenant_config.get('branding_config', {})
                                if isinstance(branding_config, dict):
                                    contact_name = branding_config.get('contactName') or branding_config.get('contact_name') or contact_name
                                
                                # Si no se encontró, intentar desde branding directo
                                if contact_name == "el candidato":
                                    branding = tenant_config.get('branding', {})
                                    if isinstance(branding, dict):
                                        contact_name = branding.get('contact_name') or branding.get('contactName') or contact_name
                                        
                                print(f"👤 [ULTRA-FAST] contact_name obtenido: '{contact_name}'")
                        except Exception as e:
                            print(f"⚠️ Error obteniendo tenant_config: {e}")
                    
                    print(f"🤖 ANTES de llamar a _generate_immediate_document_response")
                    print(f"🤖 query: '{query[:100]}...'")
                    print(f"🤖 document_content: {len(document_content)} caracteres")
                    response = await self._generate_immediate_document_response(query, document_content, contact_name, {}, tenant_config)
                    print(f"🤖 DESPUÉS de llamar a _generate_immediate_document_response")
                    print(f"🤖 RESPUESTA INMEDIATA GENERADA: {response[:200]}...")
                    return response
                else:
                    print("🔍 DEBUG: No hay documentos disponibles, usando fallback")
                    return "No tengo información suficiente sobre ese tema. Puedo ayudarte con otros temas de la campaña."
            
            # 🚀 FALLBACK: Usar Gemini si no hay documentos o no es ultra-fast mode
            if self.use_gemini_client and self.gemini_client and self.gemini_client.model:
                if ultra_fast_mode:
                    # 🚀 MODO ULTRA-RÁPIDO: Sin timeout para permitir procesamiento completo
                    print("🚀 ULTRA-FAST MODE: Generando sin timeout")
                    try:
                        response = await self.gemini_client.generate_content(prompt)
                        # 🔒 GARANTIZAR: No exceder 1000 caracteres
                        if response and len(response) > 1000:
                            last_space = response[:1000].rfind(' ')
                            response = response[:last_space] if last_space > 900 else response[:1000]
                        print(f"🚀 ULTRA-FAST MODE: Respuesta generada: {response[:100]}...")
                        return response
                    except Exception as e:
                        print(f"🚀 ULTRA-FAST MODE: Error con Gemini: {e}")
                        # Fallback a respuesta genérica
                        return "Sobre este tema, tengo información específica que te puede interesar. Te puedo ayudar a conectarte con nuestro equipo para obtener más detalles."
                else:
                    # 🚀 MODO NORMAL: Con timeout para evitar bloqueos
                    import asyncio
                    try:
                        response = await asyncio.wait_for(
                            self.gemini_client.generate_content(prompt),
                            timeout=5.0  # Timeout normal de 5 segundos
                        )
                        # 🔒 GARANTIZAR: No exceder 1000 caracteres
                        if response and len(response) > 1000:
                            last_space = response[:1000].rfind(' ')
                            response = response[:last_space] if last_space > 900 else response[:1000]
                        return response
                    except asyncio.TimeoutError:
                        logger.warning(f"⚠️ Timeout en generación normal para prompt: {prompt[:50]}...")
                        return "saludo_apoyo"  # Fallback seguro
            else:
                # Fallback al método original
                print("🚀 DEBUG ULTRA-FAST: Usando fallback al método original")
                return await self._generate_content(prompt, "intent_classification")
        except Exception as e:
            logger.error(f"Error en generación ultra-rápida: {e}")
            return "saludo_apoyo"  # Fallback seguro

    async def _generate_immediate_document_response(self, query: str, document_content: str, contact_name: str, user_context: Dict[str, Any] = None, tenant_config: Dict[str, Any] = None) -> str:
        """
        Genera respuesta inmediata basada en documentos usando IA
        Respeta la conciencia individual de cada tenant
        """
        try:
            # 🔧 FIX: Incluir historial de conversación si está disponible
            conversation_context = query
            
            if user_context and "conversation_history" in user_context:
                history = user_context["conversation_history"]
                if history and len(history.strip()) > 0:
                    # Combinar historial con pregunta actual para dar contexto completo
                    conversation_context = f"Historial de conversación:\n{history}\n\nPregunta actual: {query}"
                    print(f"🔍 DEBUG IMMEDIATE: Incluyendo historial ({len(history)} chars) en contexto")
            
            # 🔧 PRIMERO: Asegurar que gemini_client existe
            if self.use_gemini_client and self.gemini_client is None:
                print("🚀 DEBUG IMMEDIATE: gemini_client es None, inicializando...")
                self._ensure_gemini_client()
            
            # Extraer información relevante del documento
            content_lower = document_content.lower()
            query_lower = query.lower()
            
            print(f"🔍 DEBUG IMMEDIATE: query_lower = '{query_lower}'")
            print(f"🔍 DEBUG IMMEDIATE: conversation_context = '{conversation_context[:200]}...'")
            print(f"🔍 DEBUG IMMEDIATE: content_lower preview = '{content_lower[:200]}...'")
            
            # Limpiar el contenido para la IA (remover nombres de archivos y caracteres especiales)
            import re
            clean_content = document_content.replace('*', '').replace('\n', ' ')
            clean_content = re.sub(r'\s*\([^)]*\.pdf\)\s*', ' ', clean_content, flags=re.IGNORECASE)
            clean_content = re.sub(r'\.pdf', ' ', clean_content, flags=re.IGNORECASE)
            
            # Crear prompt para que la IA genere respuesta corta y natural
            print(f"🔍 DEBUG: Creando summary_prompt con contact_name={contact_name}...")
            
            # 🔧 NUEVO: Extraer la última pregunta del usuario del contexto completo
            last_user_input = query
            if "Pregunta actual del usuario:" in conversation_context:
                parts = conversation_context.split("Pregunta actual del usuario:")
                last_user_input = parts[-1].strip()
            elif "Pregunta actual:" in conversation_context:
                parts = conversation_context.split("Pregunta actual:")
                last_user_input = parts[-1].strip()
            elif "Usuario:" in conversation_context:
                # Extraer la última línea que empieza con "Usuario:"
                user_lines = [line for line in conversation_context.split('\n') if line.strip().startswith('Usuario:')]
                if user_lines:
                    last_user_input = user_lines[-1].replace('Usuario:', '').strip()
            
            print(f"🔍 DEBUG: Última entrada del usuario: '{last_user_input}'")
            
            try:
                # 🔧 MEJORAR: Obtener información adicional del tenant_config si está disponible
                candidate_bio = ""
                campaign_name = f"la campaña de {contact_name}"
                
                if tenant_config:
                    branding = tenant_config.get('branding', {})
                    if isinstance(branding, dict):
                        if branding.get('campaignName'):
                            campaign_name = branding.get('campaignName')
                        if branding.get('bio') or branding.get('candidateBio'):
                            candidate_bio = branding.get('bio') or branding.get('candidateBio', '')
                            if len(candidate_bio) > 300:
                                candidate_bio = candidate_bio[:300] + "..."
                
                # Construir prompt mejorado con identidad política clara
                summary_prompt = f"""Eres el asistente virtual oficial de {contact_name}, representante de {campaign_name}.

{candidate_bio if candidate_bio else f"Eres el asistente de {contact_name} y respondes desde su perspectiva política y campaña."}

Contexto de la conversación:
{conversation_context}

Información relevante de los documentos de campaña:
{clean_content[:2000]}

INSTRUCCIONES CRÍTICAS:
1. **IDENTIDAD**: Eres el asistente de {contact_name}. Responde desde SU perspectiva política.
2. **PROHIBIDO**: NUNCA uses frases como "el texto menciona", "el texto dice", "el texto señala", "los textos indican", "según los documentos", "en los documentos se dice". 
3. **OBLIGATORIO**: Habla directamente sobre los temas como si fueran parte de la posición y conocimiento de {contact_name}.
4. **TONO**: Responde de forma natural, como si {contact_name} mismo estuviera explicando su postura.
5. **EJEMPLOS CORRECTOS**: 
   - ✅ "Durante la presidencia de Álvaro Uribe Vélez, hubo falsos positivos..."
   - ✅ "Los falsos positivos ocurrieron durante..."
   - ❌ "El texto menciona que durante la presidencia..."
   - ❌ "Según los documentos, los falsos positivos..."
6. Si el usuario escribió una confirmación breve (ok, sí, entendido, claro, gracias, bien, etc.), responde EXACTAMENTE: "Gracias. ¿En qué más puedo ayudarte?"
7. Si es una pregunta real, responde de forma breve (máximo 800 caracteres) usando la información disponible
8. Siempre usa el nombre específico {contact_name} cuando sea relevante, nunca uses frases genéricas como "el candidato"

Última entrada del usuario: "{last_user_input}"

Respuesta (habla directamente, sin mencionar textos o documentos):"""
                print(f"🔍 DEBUG: summary_prompt creado exitosamente: {len(summary_prompt)} caracteres")
            except Exception as prompt_error:
                print(f"🔍 DEBUG: ERROR creando summary_prompt: {prompt_error}")
                import traceback
                traceback.print_exc()
                raise
            
            # Usar IA disponible para generar respuesta
            print(f"🔍 DEBUG: ¿use_gemini_client? {self.use_gemini_client}")
            print(f"🔍 DEBUG: ¿gemini_client disponible? {self.gemini_client is not None}")
            
            # Verificar si necesitamos reinicializar el modelo
            if self.use_gemini_client and self.gemini_client:
                print(f"🚀 DEBUG IMMEDIATE: Verificando modelo...")
                model_available = self.gemini_client.model is not None if self.gemini_client else False
                print(f"🔍 DEBUG: ¿modelo disponible? {model_available}")
                
                if not model_available and not self.gemini_client._initialized:
                    print("🚀 DEBUG IMMEDIATE: Modelo no inicializado, inicializando...")
                    self.gemini_client._ensure_model_initialized()
                elif not model_available and self.gemini_client._initialized:
                    print("🚀 DEBUG IMMEDIATE: _initialized=True pero model=None, reseteando e inicializando...")
                    self.gemini_client._initialized = False
                    self.gemini_client._ensure_model_initialized()
            
            model_available = self.gemini_client.model is not None if (self.gemini_client and hasattr(self.gemini_client, 'model')) else False
            print(f"🔍 DEBUG: ¿modelo disponible después de verificación? {model_available}")
            
            if self.use_gemini_client and self.gemini_client and model_available:
                try:
                    print(f"🤖 Llamando a generate_content con prompt de {len(summary_prompt)} caracteres")
                    ai_response = await self.gemini_client.generate_content(summary_prompt)
                    print(f"🤖 Respuesta recibida de IA: {len(ai_response) if ai_response else 0} caracteres")
                    if ai_response:
                        print(f"🤖 Pre-tratamiento respuesta: {ai_response[:500]}")
                        # 🔒 GARANTIZAR: No exceder 1000 caracteres bajo ninguna circunstancia
                        if len(ai_response) > 1000:
                            # Truncar de forma inteligente en el último espacio antes de 1000
                            last_space = ai_response[:1000].rfind(' ')
                            if last_space > 900:
                                ai_response = ai_response[:last_space]
                            else:
                                ai_response = ai_response[:1000]
                        print(f"🤖 Respuesta final después de truncamiento: {ai_response}")
                        return ai_response
                except Exception as e:
                    logger.warning(f"Error generando respuesta con IA: {e}")
            
            # Fallback: Si falló la IA, intentar generar respuesta básica con IA una vez más
            if self.use_gemini_client and self.gemini_client and model_available:
                try:
                    simple_prompt = f"Responde brevemente a: {query}. Máximo 200 caracteres."
                    ai_response = await self.gemini_client.generate_content(simple_prompt)
                    if ai_response and len(ai_response) > 50:
                        if len(ai_response) > 1000:
                            last_space = ai_response[:1000].rfind(' ')
                            ai_response = ai_response[:last_space] if last_space > 900 else ai_response[:1000]
                        return ai_response
                except Exception as e2:
                    logger.warning(f"Error en fallback de IA: {e2}")
            
            # Último fallback: mensaje genérico muy corto
            return "No tengo información suficiente sobre ese tema. Puedo ayudarte con otros temas de la campaña."
            
        except Exception as e:
            logger.error(f"Error generando respuesta inmediata: {e}")
            return "No tengo información suficiente sobre ese tema. Puedo ayudarte con otros temas de la campaña."

    async def _generate_content_with_documents(self, prompt: str, max_tokens: int = 200) -> str:
        """
        Generación de contenido específica para respuestas basadas en documentos
        Con timeout ultra-agresivo para desarrollo local
        """
        try:
            if self.use_gemini_client and self.gemini_client and self.gemini_client.model:
                # 🚀 OPTIMIZACIÓN: Sin timeout para permitir procesamiento completo
                try:
                    response = await self.gemini_client.generate_content(prompt)
                    # 🔒 GARANTIZAR: No exceder 1000 caracteres
                    if response and len(response) > 1000:
                        last_space = response[:1000].rfind(' ')
                        response = response[:last_space] if last_space > 900 else response[:1000]
                    return response
                except Exception as e:
                    logger.warning(f"⚠️ Error en generación con documentos: {e}")
                    # Respuesta de fallback más rápida
                    return "Sobre este tema, tengo información específica que te puede interesar. Te puedo ayudar a conectarte con nuestro equipo para obtener más detalles."
            else:
                # Fallback al método original
                return await self._generate_content(prompt, "document_response")
        except Exception as e:
            logger.error(f"Error en generación con documentos: {e}")
            return "Sobre este tema, tengo información específica que te puede interesar. Te puedo ayudar a conectarte con nuestro equipo para obtener más detalles."

    async def _generate_content_optimized(self, prompt: str, task_type: str = "general") -> str:
        """
        Generación optimizada de contenido para máxima velocidad
        """
        try:
            if self.use_gemini_client and self.gemini_client and self.gemini_client.model:
                # Usar configuración optimizada (ya pre-cargado al startup)
                response = await self.gemini_client.generate_content(prompt)
                # 🔒 GARANTIZAR: No exceder 1000 caracteres
                if response and len(response) > 1000:
                    last_space = response[:1000].rfind(' ')
                    response = response[:last_space] if last_space > 900 else response[:1000]
                return response
            else:
                # Fallback al método original
                return await self._generate_content(prompt, task_type)
        except Exception as e:
            logger.error(f"Error en generación optimizada: {e}")
            return await self._generate_content(prompt, task_type)
    
    async def _generate_content(self, prompt: str, task_type: str = "chat_conversational") -> str:
        """
        Genera contenido usando Gemini, fallback a REST API si gRPC falla
        
        Args:
            prompt: Texto a enviar a Gemini
            task_type: Tipo de tarea para configuración optimizada (Fase 2)
        
        Returns:
            Respuesta generada por Gemini
        """
        logger.info(f"🔍 DEBUG: _generate_content llamado con task_type: '{task_type}'")
        logger.info(f"🔍 DEBUG: Prompt length: {len(prompt)} caracteres")
        logger.info(f"🔍 DEBUG: Prompt preview: {prompt[:200]}...")
        
        # 🔧 OPTIMIZACIÓN: Cache local para evitar llamadas repetidas
        cache_key = self._generate_cache_key(prompt, task_type)
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            logger.info(f"✅ CACHE HIT: Respuesta cacheada para '{prompt[:30]}...'")
            return cached_response
        
        # [COHETE] FASE 1 + 2: Delegar a GeminiClient si está habilitado
        if self.use_gemini_client and self.gemini_client:
            try:
                # Usar configuraciones avanzadas si están habilitadas (Fase 2)
                use_custom_config = self.use_advanced_model_configs
                
                if use_custom_config:
                    logger.debug(f"🔄 Delegando a GeminiClient con task_type='{task_type}'")
                else:
                    logger.debug("🔄 Delegando generación de contenido a GeminiClient")
                
                response = await self.gemini_client.generate_content(
                    prompt, 
                    task_type=task_type,
                    use_custom_config=use_custom_config
                )
                
                # 🔒 GARANTIZAR: No exceder 1000 caracteres
                if response and len(response) > 1000:
                    last_space = response[:1000].rfind(' ')
                    response = response[:last_space] if last_space > 900 else response[:1000]
                
                # 🔧 OPTIMIZACIÓN: Guardar en cache
                self._cache_response(cache_key, response)
                return response
                
            except Exception as e:
                logger.warning(f"[ADVERTENCIA] GeminiClient falló, usando lógica original: {e}")
                # Continuar con lógica original como fallback
        
        # MANTENER: Lógica original completa como fallback
        try:
            # Intentar con gRPC primero
            if self.model:
                response = self.model.generate_content(prompt, safety_settings=self._get_safety_settings())
                response_text = response.text
                
                # 🔧 OPTIMIZACIÓN: Guardar en cache
                self._cache_response(cache_key, response_text)
                return response_text
        except Exception as e:
            logger.warning(f"gRPC falló, usando REST API: {str(e)}")
        
        # Fallback a REST API
        response = await self._call_gemini_rest_api(prompt)
        
        # 🔧 OPTIMIZACIÓN: Guardar en cache
        self._cache_response(cache_key, response)
        logger.info(f"🔍 DEBUG: _generate_content devolviendo: {len(response)} caracteres")
        logger.info(f"🔍 DEBUG: _generate_content respuesta: {response[:200]}...")
        return response
    
    def _get_cached_response(self, key: str) -> Optional[str]:
        """Obtiene respuesta del cache local"""
        return self._response_cache.get(key)
    
    def _cache_response(self, key: str, response: str):
        """Guarda respuesta en cache local"""
        self._response_cache[key] = response
        # Limitar tamaño del cache
        if len(self._response_cache) > 1000:
            # Eliminar las primeras 200 entradas (más antiguas)
            keys_to_remove = list(self._response_cache.keys())[:200]
            for k in keys_to_remove:
                del self._response_cache[k]
    
    def _generate_cache_key(self, prompt: str, task_type: str = "general") -> str:
        """Genera clave de cache basada en prompt y tipo de tarea"""
        import hashlib
        content = f"{task_type}:{prompt[:100]}"  # Solo primeros 100 chars
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    async def process_chat_message(self, tenant_id: str, query: str, user_context: Dict[str, Any], session_id: str = None, tenant_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Procesa un mensaje de chat usando IA específica del tenant con sesión persistente y clasificación
        
        Args:
            tenant_id: ID del tenant
            query: Mensaje del usuario
            user_context: Contexto del usuario
            session_id: ID de la sesión para mantener contexto
            tenant_config: Configuración del tenant (incluye ai_config con documentation_bucket_url)
        """
        print(f"INICIANDO PROCESAMIENTO: '{query}' para tenant {tenant_id}")
        
        # 🚀 Verificar variables al inicio del procesamiento
        import os
        ultra_fast_mode = os.getenv("ULTRA_FAST_MODE", "false").lower() == "true"
        is_local_dev = os.getenv("LOCAL_DEVELOPMENT", "false").lower() == "true"
        print(f"🚀 DEBUG PROCESAMIENTO - ULTRA_FAST_MODE: {ultra_fast_mode}")
        print(f"🚀 DEBUG PROCESAMIENTO - LOCAL_DEVELOPMENT: {is_local_dev}")
        
        start_time = time.time()
        
        # Inicializar followup_message para evitar errores de None
        followup_message = ""
        
        try:
            print(f"🔍 DENTRO DEL TRY INICIAL")
            logger.info(f"Procesando mensaje para tenant {tenant_id}, sesión: {session_id}")
            logger.info(f"🔍 DEBUG: Iniciando process_chat_message - query: '{query}', tenant_id: {tenant_id}")
            
            # 🚀 NUEVO: Usar directamente el sistema de documentos que funciona
            logger.info(f"🔍 DEBUG: ¿Entrando en ultra_fast_mode? {ultra_fast_mode}")
            
            # 🎯 FIX: Clasificar intención antes de decidir usar RAG
            logger.info(f"🔍 DEBUG: Clasificando intención...")
            try:
                from chatbot_ai_service.services.tenant_memory_service import tenant_memory_service
                tenant_context = tenant_memory_service.get_tenant_context(tenant_id)
                if tenant_context:
                    user_context['tenant_context'] = tenant_context
                
                classification_result = await self.classify_intent(tenant_id, query, user_context, session_id, tenant_config)
                intent = classification_result.get("category", "saludo_apoyo").strip()
                confidence = classification_result.get("confidence", 0.0)
                logger.info(f"🔍 DEBUG: Intención clasificada: '{intent}' con confianza: {confidence}")
            except Exception as e:
                logger.error(f"❌ ERROR en clasificación de intención: {str(e)}")
                intent = "saludo_apoyo"
                confidence = 0.0
            
            # 🎯 FIX: NO usar RAG para solicitud_funcional
            logger.info(f"🔍 DEBUG: ultra_fast_mode={ultra_fast_mode}, intent='{intent}'")
            print(f"🔍 PRINT: ultra_fast_mode={ultra_fast_mode}, intent='{intent}'")
            
            # 🎯 NUEVO: Si es solicitud_funcional, saltar todo el bloque de documentos y continuar
            if intent == "solicitud_funcional":
                print(f"🎯 DETECTADO solicitud_funcional - SALTANDO ULTRA-FAST MODE para procesar correctamente")
                logger.info(f"🎯 DETECTADO solicitud_funcional - SALTANDO ULTRA-FAST MODE para procesar correctamente")
            elif ultra_fast_mode:
                print(f"🎯 ENTRANDO EN ULTRA-FAST MODE para intent: '{intent}'")
                logger.info(f"🚀 ULTRA-FAST MODE: Usando sistema de documentos directo (intent: {intent})")
                from chatbot_ai_service.services.document_context_service import document_context_service
                
                # Extraer solo la pregunta actual si viene en formato de historial
                logger.info(f"🔍 DEBUG: Query recibida en process_chat_message: '{query[:200]}...'")
                logger.info(f"🔍 DEBUG: Longitud total del query: {len(query)}")
                logger.info(f"🔍 DEBUG: ¿Contiene 'Pregunta actual del usuario:'? {('Pregunta actual del usuario:' in query)}")
                current_query = query
                if "Pregunta actual del usuario:" in query:
                    # Extraer solo la pregunta actual para la búsqueda
                    parts = query.split("Pregunta actual del usuario:")
                    current_query = parts[-1].strip()
                    logger.info(f"🔍 DEBUG: Extraída pregunta actual: '{current_query}'")
                    logger.info(f"🔍 DEBUG: Longitud de current_query: {len(current_query)}")
                else:
                    logger.info(f"🔍 DEBUG: No hay historial, usando query completa")
                
                # Obtener contenido de documentos (usar solo la pregunta actual)
                logger.info(f"🔍 DEBUG: ANTES de get_relevant_context con current_query='{current_query}'")
                document_content = await document_context_service.get_relevant_context(tenant_id, current_query, max_results=1)
                logger.info(f"🔍 DEBUG: DESPUÉS de get_relevant_context")
                logger.info(f"🔍 DEBUG: document_content obtenido: {len(document_content) if document_content else 0} caracteres")
                if document_content:
                    logger.info(f"🔍 DEBUG: Primera línea de document_content: {document_content.split(chr(10))[0][:100]}")
                else:
                    logger.warning(f"🔍 DEBUG: document_content está vacío o None")
                
                if document_content:
                    # Usar respuesta inmediata basada en documentos
                    # 🔧 MEJORAR: Extraer contact_name de todos los lugares posibles (igual que RAGOrchestrator)
                    contact_name = None
                    candidate_name = None
                    
                    if tenant_config:
                        # Intentar obtener de branding_config primero (formato común)
                        branding_config = tenant_config.get('branding_config', {})
                        if isinstance(branding_config, dict):
                            contact_name = branding_config.get('contactName') or branding_config.get('contact_name')
                        
                        # Si no se encontró, intentar desde branding directo
                        if not contact_name:
                            branding = tenant_config.get('branding', {})
                            if isinstance(branding, dict):
                                contact_name = branding.get('contact_name') or branding.get('contactName')
                                candidate_name = branding.get('candidate_name') or branding.get('candidateName')
                        
                        # Si aún no se encontró, buscar en nivel raíz
                        if not contact_name:
                            contact_name = tenant_config.get('contact_name') or tenant_config.get('contactName')
                    
                    # Si NO se encontró ningún contact_name, usar valor por defecto
                    if not contact_name:
                        contact_name = "el candidato"
                    
                    # Usar candidate_name si está disponible, sino usar contact_name
                    final_candidate_name = candidate_name if candidate_name else contact_name
                    
                    logger.info(f"👤 [ULTRA-FAST] contact_name extraído: '{contact_name}', candidate_name: '{final_candidate_name}'")
                    
                    # Usar el query completo (con historial) para que la IA tenga contexto
                    response = await self._generate_immediate_document_response(
                        query, document_content, final_candidate_name, user_context, tenant_config
                    )
                    logger.info(f"🤖 RESPUESTA INMEDIATA GENERADA: {response[:200]}...")
                    
                    return {
                        "response": response,
                        "followup_message": "",
                        "processing_time": time.time() - start_time,
                        "intent": "conocer_candidato",
                        "confidence": 0.9,
                        "tenant_id": tenant_id
                    }
                else:
                    logger.info(f"🔍 DEBUG: No hay documentos disponibles, generando con IA")
                    # Generar respuesta con IA en tiempo real
                    try:
                        from chatbot_ai_service.services.tenant_memory_service import tenant_memory_service
                        tenant_memory = tenant_memory_service._tenant_memories.get(tenant_id)
                        
                        # Obtener contexto
                        campaign_context = tenant_memory.campaign_context if tenant_memory and hasattr(tenant_memory, 'campaign_context') else ""
                        common_questions = tenant_memory.common_questions[:3] if tenant_memory and hasattr(tenant_memory, 'common_questions') and tenant_memory.common_questions else []
                        
                        # Generar prompt
                        ai_prompt = f"""Soy el asistente de la campaña. El usuario pregunta: "{query}"
                        
Contexto: {campaign_context[:200] if campaign_context else "Campaña política"}
Temas: {', '.join(common_questions[:2]) if common_questions else "Política"}
                        
Responde naturalmente y de forma breve (máximo 150 caracteres):"""
                        
                        # Generar con IA con timeout
                        import asyncio
                        response = await asyncio.wait_for(
                            self._generate_content_optimized(ai_prompt),
                            timeout=10.0
                        )
                        
                        if response:
                            return {
                                "response": response[:300],  # Limitar longitud
                                "followup_message": "",
                                "processing_time": time.time() - start_time,
                                "intent": "conocer_candidato",
                                "confidence": 0.7,
                                "tenant_id": tenant_id
                            }
                    except (asyncio.TimeoutError, Exception) as e:
                        logger.warning(f"⚠️ Error generando con IA: {e}")
                    
                    # Fallback si IA falla
                    logger.info(f"🔍 DEBUG: Usando fallback genérico")
                    return {
                        "response": "¡Claro! Puedo ayudarte con información sobre la campaña. ¿Qué te gustaría saber específicamente?",
                        "followup_message": "",
                        "processing_time": time.time() - start_time,
                        "intent": "general_query",
                        "confidence": 0.5,
                        "tenant_id": tenant_id
                    }
            
            # 🔧 DEBUG CRÍTICO: Verificar parámetros de entrada
            logger.info(f"🔍 DEBUG: Parámetros recibidos:")
            logger.info(f"   - tenant_id: {tenant_id}")
            logger.info(f"   - query: '{query}'")
            logger.info(f"   - user_context: {user_context}")
            logger.info(f"   - session_id: {session_id}")
            logger.info(f"   - tenant_config: {tenant_config}")
            
            # 🚀 OPTIMIZACIÓN: Usar memoria precargada + contexto de sesión para acelerar clasificación de IA
            from chatbot_ai_service.services.tenant_memory_service import tenant_memory_service
            from chatbot_ai_service.services.session_context_service import session_context_service
            
            # 🚀 OPTIMIZACIÓN ULTRA-RÁPIDA: Contexto mínimo para máxima velocidad
            tenant_context = tenant_memory_service.get_tenant_context(tenant_id)
            if tenant_context:
                logger.info(f"🧠 Usando contexto precargado del tenant {tenant_id} para acelerar clasificación")
                user_context['tenant_context'] = tenant_context
            
            # 🚀 OPTIMIZACIÓN: Solo obtener contexto de sesión si es crítico
            if session_id and user_context.get("user_state") in ["WAITING_NAME", "WAITING_LASTNAME", "WAITING_CITY"]:
                session_context = session_context_service.build_context_for_ai(session_id)
                if session_context:
                    logger.info(f"👤 Usando contexto de sesión crítico para personalizar respuesta")
                    user_context['session_context'] = session_context
            
            # 🎯 NOTA: La clasificación de intención ya se hizo antes del bloque ultra_fast_mode (línea 934)
            # Continúa usando las variables 'intent' y 'confidence' ya clasificadas
            
            # 🚫 PRIORIDAD CRÍTICA: Si es malicioso, BLOQUEAR INMEDIATAMENTE y NO procesar
            if intent == "malicioso":
                logger.warning(f"🚫 Mensaje malicioso detectado por IA en process_chat_message - BLOQUEANDO USUARIO")
                logger.warning(f"🚫 Mensaje: '{query}'")
                logger.warning(f"🚫 Confianza: {confidence:.2f}")
                
                # Bloquear usuario
                blocked_response = await self._handle_malicious_behavior(
                    query, user_context, tenant_id, confidence
                )
                
                # NO enviar respuesta - bloquear silenciosamente
                logger.warning(f"🚫 Usuario bloqueado - NO enviando respuesta")
                return {
                    "response": "",  # Respuesta vacía = no responder
                    "followup_message": "",
                    "from_cache": False,
                    "processing_time": time.time() - start_time,
                    "tenant_id": tenant_id,
                    "session_id": session_id,
                    "intent": "malicioso",
                    "confidence": confidence,
                    "user_blocked": True
                }
            
            # VERIFICAR SI EL USUARIO ESTÁ BLOQUEADO PRIMERO
            user_state = user_context.get("user_state", "")
            if user_state == "BLOCKED":
                logger.warn(f"🚫 Usuario bloqueado intentando enviar mensaje: {user_context.get('user_id', 'unknown')}")
                return {
                    "response": "",  # No responder nada a usuarios bloqueados
                    "followup_message": "",
                    "processing_time": time.time() - start_time,
                    "tenant_id": tenant_id,
                    "session_id": session_id,
                    "intent": "blocked_user",
                    "confidence": 1.0
                }
            
            # 🚀 OPTIMIZACIÓN: Usar configuración del tenant desde memoria precargada
            if not tenant_config:
                tenant_context = user_context.get('tenant_context', {})
                tenant_config = tenant_context.get('tenant_config', {})
                if not tenant_config:
                    logger.warning(f"⚠️ No hay configuración del tenant {tenant_id} en memoria precargada")
                    return {
                        "response": "Lo siento, no puedo procesar tu mensaje en este momento.",
                        "followup_message": "",
                        "error": "Tenant no encontrado"
                    }
                else:
                    logger.info(f"✅ Usando configuración del tenant {tenant_id} desde memoria precargada")
            else:
                logger.info(f"🔧 Usando configuración del tenant enviada desde Java: {bool(tenant_config.get('aiConfig'))}")
            
            # Obtener configuración de IA
            ai_config = tenant_config.get("aiConfig", {}) if tenant_config else {}
            branding_config = tenant_config.get("branding", {}) if tenant_config else {}
            
            # 🔧 DEBUG: Log de configuración recibida
            logger.info(f"🔍 Configuración recibida para tenant {tenant_id}:")
            logger.info(f"  - tenant_config keys: {list(tenant_config.keys()) if tenant_config else 'None'}")
            logger.info(f"  - ai_config: {ai_config}")
            logger.info(f"  - ai_config keys: {list(ai_config.keys()) if ai_config else 'None'}")
            logger.info(f"  - documentation_bucket_url: {ai_config.get('documentation_bucket_url') if ai_config else 'None'}")
            
            # Gestionar sesión
            if not session_id:
                session_id = f"session_{tenant_id}_{int(time.time())}"
            
            # Verificar timeout de sesión antes de procesar
            timeout_check = session_context_service.check_session_timeout(session_id)
            if timeout_check["status"] == "expired":
                return {
                    "response": timeout_check["message"],
                    "followup_message": "",
                    "intent": "session_expired",
                    "confidence": 1.0,
                    "processing_time": time.time() - start_time,
                    "session_id": session_id,
                    "from_cache": False,
                    "error": None
                }
            elif timeout_check["status"] == "warning":
                # Enviar advertencia pero continuar procesando
                logger.info(f"⚠️ Advertencia de timeout para sesión {session_id}")
            
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
            
            # Agregar mensaje del usuario a la sesion
            session_context_service.add_message(session_id, "user", query)
            
            # 🔧 PRIORIDAD 1: DETECCIÓN DE MENSAJES MALICIOSOS (ahora por IA en classify_intent)
            # Nota: La detección de malicia ahora se hace por IA en classify_intent, no por patrones
            # Esto permite detectar amenazas indirectas, insultos creativos y contenido hostil de manera más inteligente
            
            # 🔧 PRIORIDAD 2: REGISTRO - Verificar si el usuario está en proceso de registro
            user_state = user_context.get("user_state", "")
            registration_states = ["WAITING_NAME", "WAITING_LASTNAME", "WAITING_CITY", "WAITING_CODE", "IN_PROGRESS"]
            
            if user_state in registration_states:
                logger.info(f"🔄 Usuario en proceso de registro (estado: {user_state}), priorizando análisis de registro")
                # Analizar como respuesta de registro en lugar de clasificar intención
                registration_analysis = await self.analyze_registration(tenant_id, query, user_context, session_id, user_state)
                
                if registration_analysis and registration_analysis.get("type") != "other":
                    logger.info(f"✅ Datos de registro extraídos: {registration_analysis}")
                    # Procesar como respuesta de registro
                    return await self._handle_registration_response(tenant_id, query, user_context, registration_analysis, branding_config, session_id)
                else:
                    logger.info(f"⚠️ No se pudieron extraer datos de registro, continuando con clasificación normal")
            
            # Clasificar la intencion del mensaje usando IA
            classification_result = await self.classify_intent(tenant_id, query, user_context, session_id, tenant_config)
            intent = classification_result.get("category", "saludo_apoyo").strip()
            confidence = classification_result.get("confidence", 0.0)
            
            # Mostrar solo la clasificacion
            print(f"🎯 INTENCIÓN: {intent}")
            print(f"🔍 LÍNEA 1203 - Después de clasificación")
            logger.info(f"🔍 DESPUÉS DE CLASIFICACIÓN - intent: '{intent}'")
            print(f"🔍 LÍNEA 1204 - logger.info ejecutado")
            logger.info(f"🔍 ESTE LOG DEBE APARECER después de INTENCIÓN")
            print(f"🔍 LÍNEA 1205 - Antes del bloque malicioso")
            
            # 🚫 PRIORIDAD CRÍTICA: Si es malicioso, BLOQUEAR INMEDIATAMENTE y NO procesar
            if intent == "malicioso":
                logger.warning(f"🚫 Mensaje malicioso detectado por IA - BLOQUEANDO USUARIO INMEDIATAMENTE")
                logger.warning(f"🚫 Mensaje: '{query}'")
                logger.warning(f"🚫 Confianza: {confidence:.2f}")
                
                # Obtener información del usuario
                user_id = user_context.get("user_id", "unknown")
                phone_number = user_context.get("phone_number", user_context.get("phone", "unknown"))
                
                # Bloquear usuario
                blocked_response = await self._handle_malicious_behavior(
                    query, user_context, tenant_id, confidence
                )
                
                # El handler retorna "" cuando bloquea, así que no enviamos nada
                logger.warning(f"🚫 Usuario {user_id} bloqueado - NO enviando respuesta")
                return {
                    "response": "",  # Respuesta vacía = no responder
                    "followup_message": "",
                    "from_cache": False,
                    "processing_time": time.time() - start_time if 'start_time' in locals() else 0.0,
                    "tenant_id": tenant_id,
                    "session_id": session_id,
                    "intent": "malicioso",
                    "confidence": confidence,
                    "user_blocked": True
                }
            
            print(f"🔍 LÍNEA 1241 - Después del bloque malicioso - intent: '{intent}'")
            try:
                logger.info(f"🔍 JUSTO DESPUÉS DEL PRINT - intent: '{intent}'")
                logger.info(f"🔍 INICIANDO BLOQUE RAG")
                logger.info(f"🔍 DEBUG: Llegando al bloque RAG - intent: '{intent}'")
                logger.info(f"🔍 DEBUG: ANTES DE CUALQUIER PROCESAMIENTO - intent: '{intent}'")
                logger.info(f"🔍 DEBUG: Continuando con el flujo normal...")
            except Exception as e:
                print(f"❌ ERROR en logs: {e}")
                import traceback
                traceback.print_exc()
            
            print(f"🔍 DESPUÉS DEL TRY/EXCEPT - intent: '{intent}'")
            
            # RAG con orden correcto: primero documentos, luego fallback
            document_context = None
            logger.info(f"🔍 ANTES DEL BLOQUE RAG - intent: '{intent}'")
            print(f"🔍 DESPUÉS DE LOGGER.info - intent: '{intent}'")
            
            print(f"🔍 ANTES DEL TRY RAG - intent: '{intent}'")
            print(f"🔍 START TIME: {start_time if 'start_time' in locals() else 'NO DEFINIDO'}")
            try:
                # Consultar documentos para intenciones que requieren información específica
                intents_requiring_docs = ["conocer_candidato", "pregunta_especifica", "consulta_propuesta"]
                print(f"🔍 intents_requiring_docs: {intents_requiring_docs}")
                print(f"🔍 ¿Es '{intent}' en intents_requiring_docs? {intent in intents_requiring_docs}")
                
                if intent in intents_requiring_docs:
                    print(f"🔍 DENTRO DEL IF - Intentando RAG para intención '{intent}'")
                    logger.info(f"🔍 DEBUG: Intentando RAG para intención '{intent}'")
                    # PRIMERO: Intentar obtener información de documentos
                    try:
                        logger.info(f"🔍 DEBUG: Llamando a _fast_rag_search...")
                        document_context = await self._fast_rag_search(tenant_id, query, ai_config, branding_config)
                        logger.info(f"🔍 DEBUG: _fast_rag_search devolvió: '{document_context}'")
                        if not document_context:
                            document_context = "gemini_direct"
                            logger.info(f"🔍 DEBUG: document_context es None, usando gemini_direct")
                        else:
                            logger.info(f"🔍 DEBUG: document_context tiene contenido: {len(document_context)} caracteres")
                        logger.info(f"📚 Documentos consultados para intención '{intent}'")
                    except Exception as e:
                        logger.error(f"[ERROR] Error en RAG: {e}")
                        # Solo usar fallback si hay error
                        document_context = "gemini_direct"
                else:
                    print(f"🔍 DENTRO DEL ELSE - Intención '{intent}' no requiere documentos, saltando carga")
                    logger.info(f"[OBJETIVO] Intención '{intent}' no requiere documentos, saltando carga")
            except Exception as e:
                logger.error(f"❌ ERROR en bloque RAG: {str(e)}")
                import traceback
                traceback.print_exc()
                document_context = "gemini_direct"
            
            print(f"🔍 DESPUÉS DEL BLOQUE RAG - intent: '{intent}', document_context: {document_context}")
            print(f"🔍 DESPUÉS DEL PRINT 1294 - Antes de logger.info")
            logger.info(f"🔍 DESPUÉS DEL BLOQUE RAG - intent: '{intent}'")
            print(f"🔍 DESPUÉS DE logger.info línea 1295")
            logger.info(f"🧠 Intención extraída: {intent} (confianza: {confidence:.2f})")
            print(f"🔍 DESPUÉS DE logger.info línea 1296")
            logger.info(f"🔍 DEBUG: Continuando con procesamiento de intención...")
            print(f"🔍 DESPUÉS DE logger.info línea 1297")
            logger.info(f"🔍 DEBUG: Llegando al bloque de procesamiento de intención")
            print(f"🔍 DESPUÉS DE logger.info línea 1298")
            logger.info(f"🔍 DEBUG: document_context = '{document_context}'")
            print(f"🔍 DESPUÉS DE logger.info línea 1299")
            logger.info(f"🔍 DEBUG: ANTES DE CACHÉ - intent: '{intent}'")
            print(f"🔍 DESPUÉS DE logger.info línea 1300")
            
            # 1.5 NUEVO: Intentar obtener respuesta del caché
            logger.info(f"🔍 ANTES DE cache_service.get_cached_response")
            print(f"🔍 DESPUÉS DE logger.info línea 1303")
            print(f"🔍 ANTES DE LLAMAR A get_cached_response")
            cached_response = cache_service.get_cached_response(
                tenant_id=tenant_id,
                query=query,
                intent=intent
            )
            print(f"🔍 DESPUÉS DE get_cached_response - cached_response: {cached_response}")
            
            # 🔧 FIX TEMPORAL: No usar caché para solicitud_funcional para que genere followup_message correctamente
            if cached_response and intent != "solicitud_funcional":
                print(f"🔍 DENTRO DEL IF CACHED - cached_response exists")
                processing_time = time.time() - start_time if 'start_time' in locals() else 0.0
                logger.info(f"Respuesta servida desde caché (latencia: {processing_time:.2f}s)")
                
                # Agregar respuesta del bot a la sesión
                session_context_service.add_message(session_id, "assistant", cached_response.get("response", ""))
                
                return {
                    **cached_response,
                    "followup_message": "",
                    "from_cache": True,
                    "processing_time": processing_time,
                    "tenant_id": tenant_id,
                    "session_id": session_id
                }
            
            if cached_response and intent == "solicitud_funcional":
                print(f"⚠️ CACHÉ ENCONTRADO PARA solicitud_funcional - SALTANDO para generar followup_message correcto")
            
            # OPTIMIZACIÓN 3: Respuestas rápidas para casos comunes
            logger.debug(f"[LUP] VERIFICANDO INTENT: {intent}")
            
            # Obtener contexto de sesión para todas las respuestas
            logger.info(f"🔍 ANTES DE session_context_service.build_context_for_ai")
            session_context = session_context_service.build_context_for_ai(session_id)
            logger.info(f"🔍 DESPUÉS DE session_context_service.build_context_for_ai")
            
            # 🚀 OPTIMIZACIÓN: Intentar respuesta rápida con IA pero usando contexto precargado
            tenant_context = user_context.get('tenant_context', {})
            if tenant_context and intent in ["saludo_apoyo"]:
                logger.info(f"🔍 Intent es saludo_apoyo - verificando prompts desde DB")
                
                # 🗄️ PRIORIDAD 1: Intentar usar prompts desde DB
                branding_config = tenant_context.get('tenant_config', {}).get('branding', {})
                prompts_from_db = self.persistence_service.get_tenant_prompts(tenant_id)
                
                if prompts_from_db and 'welcome' in prompts_from_db:
                    logger.info(f"✅ Usando prompt 'welcome' desde DB para tenant {tenant_id}")
                    fast_response = prompts_from_db['welcome']
                else:
                    logger.info(f"🔍 No hay prompts en DB, usando RESPUESTA RÁPIDA CON IA")
                    # Solo para casos simples, usar IA rápida con contexto completo del usuario
                    fast_response = await self._generate_fast_ai_response(
                        query, user_context, tenant_context, session_context, intent
                    )
                if fast_response:
                    logger.info(f"🚀 RESPUESTA RÁPIDA CON IA para '{query[:30]}...'")
                    logger.info(f"🔍 DEBUG: RESPUESTA RÁPIDA: {fast_response[:200]}...")
                    
                    # Agregar respuesta del bot a la sesión
                    session_context_service.add_message(session_id, "assistant", fast_response)
                    
                    processing_time = time.time() - start_time if 'start_time' in locals() else 0.0
                    return {
                        "response": fast_response,
                        "followup_message": "",
                        "from_fast_ai": True,
                        "processing_time": processing_time,
                        "tenant_id": tenant_id,
                        "session_id": session_id
                    }
            
            logger.info(f"🔍 EVALUANDO INTENT: '{intent}' - Tipo: {type(intent)}")
            logger.info(f"🔍 DEBUG: ANTES DEL TRY - intent: '{intent}'")
            
            try:
                logger.info(f"🔍 DEBUG: DENTRO DEL TRY - intent: '{intent}'")
                logger.info(f"🔍 DEBUG: ¿ES solicitud_funcional? {intent == 'solicitud_funcional'}")
                
                if intent == "conocer_candidato":
                    # Generar respuesta especializada para consultas sobre el candidato
                    logger.info(f"🎯 PROCESANDO conocer_candidato - document_context: {document_context[:100] if document_context else 'None'}...")
                    
                    if document_context and document_context != "gemini_direct":
                        logger.info(f"📚 Usando documentos para respuesta")
                        response = await self._generate_candidate_response_with_documents(
                            tenant_id, query, user_context, branding_config, tenant_config, document_context, session_context
                        )
                        logger.info(f"📚 RESPUESTA CON DOCUMENTOS GENERADA:")
                        logger.info(f"📚 CONTENIDO: {response}")
                    else:
                        logger.info(f"🤖 Usando Gemini directo para respuesta")
                        response = await self._generate_candidate_response_gemini_direct(
                            query, user_context, branding_config, tenant_config, session_context
                        )
                        logger.info(f"🤖 RESPUESTA GEMINI DIRECTO GENERADA:")
                        logger.info(f"🤖 CONTENIDO: {response}")
                    
                    logger.info(f"✅ RESPUESTA GENERADA para conocer_candidato: {len(response)} caracteres")
                elif intent == "cita_campaña":
                    logger.info(f"[OBJETIVO] RESPUESTA RÁPIDA: cita_campaña")
                    response = await self._handle_appointment_request_with_context(branding_config, tenant_config, session_context)
                elif intent == "publicidad_info":
                    logger.info(f"[OBJETIVO] RESPUESTA RÁPIDA: publicidad_info")
                    response = await self._handle_advertising_info_with_context(branding_config, tenant_config, session_context)
                elif intent == "atencion_humano":
                    logger.info(f"[OBJETIVO] RESPUESTA RÁPIDA: atencion_humano")
                    response = await self._handle_human_assistance_request(branding_config, tenant_config, user_context, session_context)
                elif intent == "actualizacion_datos":
                    logger.info(f"[OBJETIVO] RESPUESTA RÁPIDA: actualizacion_datos")
                    result = await self._handle_data_update_request(query, user_context, session_context, tenant_id=tenant_id)
                    
                    # El método ahora retorna (response_message, update_data_dict)
                    if isinstance(result, tuple):
                        response, update_data = result
                        # Guardar datos para que Java los procese (se retornarán en el response)
                        if update_data:
                            # Los datos se incluirán en el response del método principal
                            user_context["data_to_update"] = update_data
                            logger.info(f"📝 Datos para actualizar: {update_data}")
                    else:
                        response = result
                elif intent == "saludo_apoyo":
                    logger.info(f"[OBJETIVO] RESPUESTA RÁPIDA: saludo_apoyo")
                    response = self._get_greeting_response_with_context(branding_config, session_context, tenant_id=tenant_id)
                elif intent == "colaboracion_voluntariado":
                    logger.info(f"[OBJETIVO] RESPUESTA RÁPIDA: colaboracion_voluntariado")
                    response = self._get_volunteer_response_with_context(branding_config, session_context)
                elif intent == "quejas":
                    logger.info(f"[OBJETIVO] RESPUESTA RÁPIDA: quejas")
                    response = self._get_complaint_response_with_context(branding_config, session_context)
                elif intent == "queja_detalle_select":
                    logger.info(f"[OBJETIVO] RESPUESTA RÁPIDA: queja_detalle_select")
                    response = self._get_complaint_detail_response_with_context(branding_config, session_context, query)
                elif intent == "solicitud_funcional":
                    logger.info(f"🔍 LLEGANDO AL BLOQUE solicitud_funcional - intent: '{intent}'")
                    # 🔍 DEBUG: Ver qué tenant_config vamos a pasar
                    logger.info(f"🔍 [solicitud_funcional] tenant_config keys antes de pasar: {list(tenant_config.keys()) if tenant_config else 'None'}")
                    # Respuesta específica para consultas funcionales con contexto de sesión
                    logger.info(f"🎯 PROCESANDO solicitud_funcional - llamando _handle_functional_request_with_session")
                    result = await self._handle_functional_request_with_session(
                        query, user_context, ai_config, branding_config, tenant_id, session_id, tenant_config
                    )
                    
                    # Manejar el nuevo formato de respuesta (puede ser string o tupla)
                    logger.info(f"🎯 TIPO DE RESULTADO: {type(result)}")
                    if isinstance(result, tuple):
                        response, followup_message = result
                        logger.info(f"🎯 RESPUESTA GENERADA para solicitud_funcional: {len(response) if response else 0} caracteres")
                        logger.info(f"🎯 FOLLOWUP_MESSAGE generado: {len(followup_message) if followup_message else 0} caracteres")
                        logger.info(f"🎯 CONTENIDO FOLLOWUP: '{followup_message[:100] if followup_message and len(followup_message) > 0 else ''}...'")
                    else:
                        response = result
                        # 🔧 FIX: NO resetear followup_message aquí - ya está inicializado al inicio
                        logger.info(f"🎯 RESPUESTA GENERADA para solicitud_funcional: {len(response) if response else 0} caracteres")
                        logger.info(f"🎯 NO es tupla - tipo: {type(result)}")
                else:
                    # Procesar según la intención clasificada con IA
                    logger.info(f"🔍 INTENT DETECTADO: '{intent}' - Iniciando procesamiento")
                    
                    if intent == "conocer_candidato":
                        logger.info(f"🎯 PROCESANDO conocer_candidato (BLOQUE ELSE)")
                        # Respuesta específica sobre el candidato
                        response = await self._generate_ai_response_with_session(
                            query, user_context, ai_config, branding_config, tenant_id, session_id
                        )
                        logger.info(f"🎯 RESPUESTA GENERADA (BLOQUE ELSE):")
                        logger.info(f"🎯 CONTENIDO: {response}")
                    elif intent == "malicioso":
                        logger.info(f"🎯 PROCESANDO malicioso")
                        # Manejo específico para comportamiento malicioso
                        response = await self._handle_malicious_behavior(
                            query, user_context, tenant_id, confidence
                        )
                    else:
                        logger.info(f"🎯 PROCESANDO respuesta general para intent: '{intent}'")
                        # Respuesta general con contexto de sesión
                        response = await self._generate_ai_response_with_session(
                            query, user_context, ai_config, branding_config, tenant_id, session_id
                        )
            except Exception as e:
                logger.error(f"❌ ERROR en procesamiento de intención '{intent}': {str(e)}")
                response = f"Lo siento, hubo un error procesando tu consulta sobre '{intent}'. Por favor intenta de nuevo."
            
            # Filtrar enlaces de la respuesta para WhatsApp (excepto citas y publicidad)
            if intent == "cita_campaña":
                filtered_response = response  # No filtrar enlaces de Calendly
                logger.info("[CALENDARIO] Respuesta de cita - manteniendo enlaces de Calendly")
            elif intent == "publicidad_info":
                filtered_response = response  # No filtrar enlaces de Forms
                logger.info("[PUBLICIDAD] Respuesta de publicidad - manteniendo enlaces de Forms")
            else:
                filtered_response = self._filter_links_from_response(response)
            
            # Limitar respuesta a máximo 999 caracteres de forma inteligente
            if len(filtered_response) > 999:
                filtered_response = self._truncate_response_intelligently(filtered_response, 999)
            
            # Agregar respuesta del asistente a la sesión
            session_context_service.add_message(session_id, "assistant", filtered_response, metadata={"intent": intent, "confidence": confidence})
            
            processing_time = time.time() - start_time if 'start_time' in locals() else 0.0
            
            # NUEVO: Guardar en caché si es cacheable
            response_data = {
                "response": filtered_response,
                "intent": intent,
                "confidence": confidence
            }
            
            # 🎯 MARCADOR ESPECIAL PARA QUEJA_DETALLE_SELECT (para usar en final_response)
            is_complaint_detail = (intent == "queja_detalle_select")
            
            cache_service.cache_response(
                tenant_id=tenant_id,
                query=query,
                response=response_data,
                intent=intent
            )
            
            # 🧠 ACTUALIZAR MEMORIA DEL USUARIO CON EL CONTEXTO DE LA CONVERSACIÓN
            user_phone = user_context.get("user_id", "unknown")
            if user_phone != "unknown":
                from chatbot_ai_service.services.tenant_memory_service import tenant_memory_service
                
                # Actualizar contexto del usuario con información relevante
                context_update = {
                    "last_query": query,
                    "last_intent": intent,
                    "last_response": filtered_response[:100],  # Solo primeros 100 caracteres
                    "conversation_count": user_context.get("conversation_count", 0) + 1
                }
                
                tenant_memory_service.update_user_context(tenant_id, user_phone, context_update)
                logger.info(f"🧠 Memoria actualizada para {tenant_id}:{user_phone}")
            
            # 🔧 DEBUG CRÍTICO: Log antes del return final
            logger.info(f"🚀 PREPARANDO RESPUESTA FINAL:")
            logger.info(f"   - Response: {len(filtered_response)} caracteres")
            logger.info(f"   - Followup: {len(followup_message) if followup_message else 0} caracteres")
            logger.info(f"   - Intent: {intent}")
            logger.info(f"   - Confidence: {confidence}")
            logger.info(f"   - Processing time: {processing_time:.2f}s")
            
            # 🔧 DEBUG CRÍTICO: Mostrar contenido completo de la respuesta
            logger.info(f"📝 CONTENIDO COMPLETO DE LA RESPUESTA:")
            logger.info(f"📝 {filtered_response}")
            
            final_response = {
                "response": filtered_response,
                "followup_message": followup_message,
                "processing_time": processing_time,
                "tenant_id": tenant_id,
                "session_id": session_id,
                "intent": intent,
                "confidence": confidence,
                "from_cache": False
            }
            
            # 🎯 AGREGAR CAMPO ESPECIAL PARA QUEJA_DETALLE_SELECT
            if intent == "queja_detalle_select":
                final_response["complaint_registered"] = True
                logger.info(f"✅ Campo complaint_registered=True agregado a respuesta")
            
            if is_complaint_detail:
                final_response["complaint_registered"] = True
                logger.info(f"✅ Campo complaint_registered=True agregado (marcador)")
            
            # 🎯 AGREGAR CAMPO ESPECIAL PARA ACTUALIZACION_DATOS
            if intent == "actualizacion_datos" and user_context.get("data_to_update"):
                final_response["data_to_update"] = user_context["data_to_update"]
                logger.info(f"✅ Campo data_to_update agregado: {user_context['data_to_update']}")
            
            logger.info(f"✅ DEVOLVIENDO RESPUESTA FINAL: {final_response}")
            return final_response
            
        except Exception as e:
            logger.error(f"❌❌❌ EXCEPCIÓN EN process_chat_message: {str(e)}")
            import traceback
            logger.error(f"❌❌❌ TRACEBACK COMPLETO: {traceback.format_exc()}")
            return {
                "response": "Lo siento, hubo un error procesando tu mensaje.",
                "followup_message": "",
                "error": str(e)
            }
    
    async def _generate_ai_response_with_session(self, query: str, user_context: Dict[str, Any], 
                                               ai_config: Dict[str, Any], branding_config: Dict[str, Any], 
                                               tenant_id: str, session_id: str) -> str:
        """Genera respuesta usando IA con contexto de sesión persistente y caché"""
        self._ensure_model_initialized()
        if not self.model:
            return "Lo siento, el servicio de IA no está disponible."
        
        try:
            # 🚀 OPTIMIZACIÓN: Verificar caché de respuestas primero
            cache_key = f"response:{tenant_id}:{query.lower().strip()}"
            cached_response = self._response_cache.get(cache_key)
            if cached_response:
                logger.info(f"🚀 RESPUESTA DESDE CACHÉ para '{query[:30]}...'")
                return cached_response
            
            # Obtener contexto completo de la sesión
            session_context = session_context_service.build_context_for_ai(session_id)
            
            # 🚀 OPTIMIZACIÓN: Usar configuración del tenant desde memoria precargada
            tenant_context = user_context.get('tenant_context', {})
            tenant_config = tenant_context.get('tenant_config', {})
            if not tenant_config:
                logger.warning(f"⚠️ No hay configuración del tenant {tenant_id} en memoria precargada para sesión")
                return "Lo siento, no puedo procesar tu mensaje en este momento."
            
            # Construir prompt con contexto de sesión
            prompt = self._build_session_prompt(query, user_context, branding_config, session_context, tenant_config)
            
            # 🔧 OPTIMIZACIÓN: Generación optimizada para velocidad
            response_text = await self._generate_content_optimized(prompt, task_type="chat_with_session")
            
            # 🚀 OPTIMIZACIÓN: Guardar en caché para futuras consultas
            self._response_cache[cache_key] = response_text
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error generando respuesta con sesión: {str(e)}")
            return "Lo siento, no pude procesar tu mensaje."
    
    def _build_session_prompt(self, query: str, user_context: Dict[str, Any], 
                            branding_config: Dict[str, Any], session_context: str, tenant_config: Dict[str, Any] = None) -> str:
        """Construye el prompt para chat con contexto de sesión"""
        contact_name = branding_config.get("contactName", "el candidato")
        
        # Contexto completo del usuario actual
        current_context = ""
        if user_context.get("user_name"):
            current_context += f"El usuario se llama {user_context['user_name']}. "
        if user_context.get("user_city"):
            current_context += f"Vive en {user_context['user_city']}. "
        if user_context.get("user_country"):
            current_context += f"País: {user_context['user_country']}. "
        if user_context.get("user_state"):
            current_context += f"Estado actual: {user_context['user_state']}. "
        if user_context.get("user_phone"):
            current_context += f"Teléfono: {user_context['user_phone']}. "
        if user_context.get("conversation_count"):
            current_context += f"Es su conversación #{user_context['conversation_count']}. "
        
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

INFORMACIÓN IMPORTANTE:
- El candidato es {contact_name}
- Si el usuario pregunta sobre "el candidato", se refiere a {contact_name}

Tu objetivo es mantener conversaciones fluidas y naturales, recordando el contexto de la conversación anterior.

CONTEXTO COMPLETO DEL USUARIO:
{current_context}

CONTEXTO ACTUAL DE LA SESIÓN:
{session_context}

INFORMACIÓN ESPECÍFICA DEL TENANT:
{tenant_info}

Mensaje actual del usuario: "{query}"

INSTRUCCIONES PERSONALIZADAS:
1. **PERSONALIZA** tu respuesta usando el nombre del usuario si está disponible
2. **MENCIÓN** su ciudad si es relevante para la respuesta
3. Mantén el contexto de la conversación anterior
4. Si es una pregunta de seguimiento, responde de manera natural
5. Usa la información específica de la campaña cuando sea relevante
6. Mantén un tono amigable y profesional
7. Si no tienes información específica, sé honesto al respecto
8. Integra sutilmente elementos motivacionales sin ser explícito sobre "EPIC MEANING" o "DEVELOPMENT"
9. **IMPORTANTE**: Si el usuario pide agendar una cita, usar el enlace específico de ENLACE DE CITAS
10. **CRÍTICO**: Mantén la respuesta concisa, máximo 999 caracteres
11. **NO menciones enlaces** a documentos externos, solo da información directa
12. **SIEMPRE identifica correctamente que {contact_name} es el candidato**

SISTEMA DE PUNTOS Y RANKING:
- Cada referido registrado suma 50 puntos
- Retos semanales dan puntaje adicional
- Ranking actualizado a nivel ciudad, departamento y país
- Los usuarios pueden preguntar "?Cómo voy?" para ver su progreso
- Para invitar personas: "mandame el link" o "dame mi código"

Responde de manera natural, contextual y útil, personalizando la respuesta según la información del usuario disponible.

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
                    logger.info(f"[LIBROS] Documentos disponibles: {len(documents)} archivos")
                    return documents
                else:
                    logger.warning(f"[ADVERTENCIA] No se pudo obtener lista de documentos: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"[ERROR] Error obteniendo lista de documentos: {e}")
            return []
    
    # async def _get_document_content_for_query(self, query: str, documentation_bucket_url: str) -> tuple[Optional[str], Optional[str]]:
    #     """Obtiene contenido real de documentos relevantes usando SmartRetriever optimizado"""
    #     # MÉTODO NO SE USA - COMENTADO
    #     try:
    #         import httpx
    #         import pypdf
    #         import io
    #         from chatbot_ai_service.retrievers.smart_retriever import SmartRetriever
    #         
    #         # Obtener todos los documentos disponibles
    #         all_documents = await self._get_available_documents(documentation_bucket_url)
    #         
    #         if not all_documents:
    #             logger.warning("[ADVERTENCIA] No hay documentos disponibles")
    #             return None, None
    #         
    #         # Crear instancia del SmartRetriever
    #         smart_retriever = SmartRetriever()
    #         
    #         # Descargar y procesar todos los documentos para crear la lista de documentos con contenido
    #         documents_with_content = []
    #         for doc_name in all_documents:
    #             try:
    #                 doc_url = f"{documentation_bucket_url}/{doc_name}"
    #                 
    #                 async with httpx.AsyncClient(timeout=30.0) as client:
    #                     response = await client.get(doc_url)
    #                     if response.status_code == 200:
    #                         text = ""
    #                         
    #                         # Procesar PDF
    #                         if doc_name.endswith('.pdf'):
    #                             pdf_content = io.BytesIO(response.content)
    #                             pdf_reader = pypdf.PdfReader(pdf_content)
    #                             for page in pdf_reader.pages[:5]:  # Primeras 5 páginas
    #                                 text += page.extract_text() + "\n"
    #                         
    #                         # Procesar DOCX
    #                         elif doc_name.endswith('.docx'):
    #                             from docx import Document as DocxDocument
    #                             doc_content = io.BytesIO(response.content)
    #                             doc = DocxDocument(doc_content)
    #                             for paragraph in doc.paragraphs[:50]:  # Primeras 50 líneas
    #                                 text += paragraph.text + "\n"
    #                         
    #                         if text.strip():
    #                             documents_with_content.append({
    #                                 "id": doc_name,
    #                                 "filename": doc_name,
    #                                 "content": text.strip()
    #                             })
    #                             logger.info(f"[OK] Documento {doc_name} cargado: {len(text)} caracteres")
    #                         
    #             except Exception as e:
    #                 logger.warning(f"[ADVERTENCIA] Error procesando {doc_name}: {e}")
    #                 continue
    #         
    #         if not documents_with_content:
    #             logger.warning("[ADVERTENCIA] No se pudo cargar contenido de ningún documento")
    #             return None, None
    #         
    #         # Usar SmartRetriever para encontrar documentos relevantes
    #         search_results = smart_retriever.search_documents(documents_with_content, query, max_results=3)
    #         
    #         if not search_results:
    #             logger.warning("[ADVERTENCIA] No se encontraron documentos relevantes")
    #             return None, None
    #         
    #         # Log de documentos seleccionados
    #         selected_docs = [result.filename for result in search_results]
    #         logger.info(f"[LIBROS] Buscando documentos relevantes: {selected_docs}")
    #         print(f"📚 DOCUMENTOS SELECCIONADOS: {selected_docs}")
    #         
    #         # Construir contenido usando los resultados del SmartRetriever
    #         content_parts = []
    #         document_name = search_results[0].filename  # Primer documento
    #         
    #         for result in search_results:
    #             # Limitar contenido a 2000 caracteres por documento
    #             content_preview = result.content[:2000] + "..." if len(result.content) > 2000 else result.content
    #             content_parts.append(f"=== {result.filename} ===\n{content_preview}")
    #             logger.info(f"[OK] Documento {result.filename} incluido (score: {result.score:.1f})")
    #         
    #         if content_parts:
    #             full_content = "\n\n".join(content_parts)
    #             logger.info(f"[LIBROS] Contenido total obtenido: {len(full_content)} caracteres")
    #             return full_content, document_name
    #         else:
    #             logger.warning("[ADVERTENCIA] No se pudo obtener contenido de ningún documento")
    #             return None, None
    #             
    #     except Exception as e:
    #         logger.error(f"[ERROR] Error obteniendo contenido de documentos: {e}")
    #         return None, None
    
    async def _fast_rag_search(self, tenant_id: str, query: str, ai_config: Dict[str, Any], branding_config: Dict[str, Any] = None) -> Optional[str]:
        """RAG ultra-rápido usando documentos precargados - OPTIMIZADO"""
        try:
            # Obtener contact_name del branding config
            contact_name = "el candidato"
            if branding_config:
                contact_name = branding_config.get("contactName", "el candidato")
            
            logger.info(f"[RAG] Buscando en documentos precargados para tenant {tenant_id}")
            
            # 🚀 OPTIMIZACIÓN: Usar documentos precargados directamente
            from chatbot_ai_service.services.document_context_service import document_context_service
            
            # 🚀 OPTIMIZACIÓN: Verificar cache primero sin cargar
            doc_info = document_context_service.get_tenant_document_info(tenant_id)
            if not doc_info or doc_info.get('document_count', 0) == 0:
                # Solo cargar si realmente no están disponibles
                documentation_bucket_url = ai_config.get("documentation_bucket_url")
                if not documentation_bucket_url:
                    logger.warning(f"[ADVERTENCIA] No hay URL de bucket de documentos para tenant {tenant_id}")
                    return None
                else:
                    logger.info(f"📥 Cargando documentos para tenant {tenant_id} desde: {documentation_bucket_url}")
                    success = await document_context_service.load_tenant_documents(tenant_id, documentation_bucket_url)
                    if not success:
                        logger.warning(f"[ADVERTENCIA] No se pudieron cargar documentos para tenant {tenant_id}")
                        return None
            
            # 🚀 OPTIMIZACIÓN ULTRA-RÁPIDA: Obtener contexto relevante más rápido
            document_content = await document_context_service.get_relevant_context(tenant_id, query, max_results=1)  # Reducido a 1 para máxima velocidad
            
            if document_content:
                logger.info(f"[LIBROS] Contenido de documentos precargados obtenido: {len(document_content)} caracteres")
                print(f"📄 DOCUMENTOS PRECARGADOS: {len(document_content)} caracteres")
                # 🚀 OPTIMIZACIÓN ULTRA-RÁPIDA: Prompt híbrido inteligente con instrucciones del sistema
                prompt = f"""Eres el asistente virtual oficial de {contact_name}. Tu función es proporcionar información útil y precisa sobre las propuestas y políticas de {contact_name}.

INSTRUCCIONES:
- Responde siempre en español
- Mantén un tono profesional y cercano
- Usa la información proporcionada para dar respuestas específicas
- Si no tienes información específica, ofrece conectar con el equipo oficial

PREGUNTA DEL USUARIO: {query}

INFORMACIÓN DISPONIBLE: {document_content}

Responde como asistente virtual oficial de {contact_name}, usando la información proporcionada para dar una respuesta útil y específica."""
            else:
                logger.info("[RAG] No se pudo obtener contenido de documentos precargados")
                return None
            
            # 🚀 OPTIMIZACIÓN: Usar configuración ultra-rápida para RAG
            try:
                response = await self._generate_content_ultra_fast(prompt, tenant_id=tenant_id, query=query)  # Usar método ultra-rápido con documentos
                result = response.strip()
                
                if len(result) < 30:  # Reducido de 50 a 30
                    logger.info(f"[RAG] Respuesta muy corta para '{query}'")
                    return None
                
                logger.info(f"[RAG] Respuesta generada: {len(result)} caracteres")
                return result
                
            except Exception as e:
                logger.error(f"[ERROR] Error generando respuesta RAG: {e}")
                # 🚀 FALLBACK INTELIGENTE: Si Gemini bloquea, generar respuesta basada en palabras clave
                return self._generate_fallback_response(query, document_content, contact_name)
                
        except Exception as e:
            logger.error(f"[ERROR] Error en RAG rápido: {e}")
            return None
    
    def _generate_fallback_response(self, query: str, document_content: str, contact_name: str) -> str:
        """Genera una respuesta de fallback inteligente basada en análisis de contenido"""
        try:
            # Análisis inteligente del contenido del documento
            content_lower = document_content.lower()
            
            # NO usar respuestas hardcodeadas - dejar que la IA genere todo
            # Respuesta genérica que no asume contenido específico
            return f"Hola! Soy el asistente virtual de {contact_name}. Tengo información sobre este tema. ¿Te gustaría que profundice en algún aspecto específico?"
                
        except Exception as e:
            logger.error(f"[FALLBACK] Error generando respuesta de fallback: {e}")
            return f"Hola! Soy el asistente virtual de {contact_name}. Sobre este tema, tenemos información específica que puede interesarte. ¿Te gustaría que te conecte con nuestro equipo para obtener más detalles?"
    
    async def _generate_candidate_response_gemini_direct(self, query: str, user_context: Dict[str, Any], 
                                                       branding_config: Dict[str, Any], tenant_config: Dict[str, Any], 
                                                       session_context: str = "") -> str:
        """Genera respuesta especializada usando Gemini directamente (más rápido)"""
        try:
            contact_name = branding_config.get("contactName", "el candidato")
            
            # 🚀 OPTIMIZACIÓN: Construir contexto completo del usuario
            user_info = ""
            if user_context.get("user_name"):
                user_info += f"El usuario se llama {user_context['user_name']}. "
            if user_context.get("user_city"):
                user_info += f"Vive en {user_context['user_city']}. "
            if user_context.get("user_country"):
                user_info += f"País: {user_context['user_country']}. "
            if user_context.get("user_state"):
                user_info += f"Estado actual: {user_context['user_state']}. "
            if user_context.get("user_phone"):
                user_info += f"Teléfono: {user_context['user_phone']}. "
            
            # Usar Gemini directamente para respuesta rápida
            self._ensure_model_initialized()
            if self.model:
                # Incluir contexto de sesión si está disponible
                context_section = ""
                if session_context:
                    context_section = f"""
                
                CONTEXTO DE LA CONVERSACIÓN:
                {session_context}
                """
                
                prompt = f"""
                Asistente virtual de {contact_name}. El usuario pregunta: "{query}"
                
                CONTEXTO COMPLETO DEL USUARIO:
                {user_info}
                {context_section}
                
                INFORMACIÓN IMPORTANTE:
                - El candidato es {contact_name}
                - Si el usuario pregunta sobre "el candidato", se refiere a {contact_name}
                
                INSTRUCCIONES PERSONALIZADAS:
                1. **PERSONALIZA** tu respuesta usando el nombre del usuario si está disponible
                2. **MENCIÓN** su ciudad si es relevante para la respuesta
                3. Responde específicamente sobre las propuestas de {contact_name} relacionadas con la pregunta
                4. Mantén un tono profesional y político, enfocado en las propuestas del candidato
                5. Si hay contexto de conversación anterior, úsalo para dar respuestas más naturales y fluidas
                6. Si no tienes información específica, ofrece conectar al usuario con el equipo de la campaña
                7. Responde en máximo 999 caracteres de forma COMPLETA - no uses "..." ni cortes abruptos
                8. SIEMPRE identifica correctamente que {contact_name} es el candidato
                9. PRIORIDAD: Genera una respuesta completa que quepa en 999 caracteres sin truncar
                10. Si mencionas listas numeradas, completa al menos 3 elementos principales
                11. Termina la respuesta de manera natural, no abrupta
                
                Responde de manera natural, útil y COMPLETA sobre las propuestas de {contact_name}, personalizando según la información del usuario.
                """
                
                try:
                    response = self.model.generate_content(prompt, safety_settings=self._get_safety_settings())
                    print(f"🤖 RESPUESTA DIRECTA: {response.text[:200]}...")
                    return response.text
                except Exception as e:
                    logger.warning(f"Error con Gemini, usando fallback: {e}")
            
            # Fallback genérico
            return f"""Sobre este tema, {contact_name} tiene información específica que te puede interesar. Te puedo ayudar a conectarte con nuestro equipo para obtener más detalles.

Te gustaría que alguien del equipo te contacte para brindarte información más específica?"""

        except Exception as e:
            logger.error(f"Error generando respuesta con Gemini directo: {e}")
            return f"Sobre este tema, {contact_name} tiene información específica que te puede interesar. Te puedo ayudar a conectarte con nuestro equipo para obtener más detalles."
    
    async def _generate_candidate_response_with_documents(self, tenant_id: str, query: str, user_context: Dict[str, Any], 
                                                         branding_config: Dict[str, Any], tenant_config: Dict[str, Any], 
                                                         document_context: str, session_context: str = "") -> str:
        """Genera respuesta especializada usando documentos reales con caché"""
        try:
            # 🚀 OPTIMIZACIÓN: Verificar caché de respuestas con documentos
            cache_key = f"doc_response:{hash(query)}:{hash(document_context[:500])}"
            cached_response = self._response_cache.get(cache_key)
            if cached_response:
                logger.info(f"🚀 RESPUESTA CON DOCUMENTOS DESDE CACHÉ para '{query[:30]}...'")
                return cached_response
            
            # 🧠 OBTENER INFORMACIÓN DEL TENANT Y SU CONCIENCIA
            from chatbot_ai_service.services.tenant_memory_service import tenant_memory_service
            from chatbot_ai_service.services.document_index_persistence_service import document_index_persistence_service
            
            # Obtener nombre del candidato desde tenant_config
            branding = branding_config or {}
            contact_name = branding.get("contactName", "el candidato")
            
            # Si no está en branding_config, intentar desde tenant_config directamente
            if contact_name == "el candidato" and tenant_config:
                tenant_branding = tenant_config.get("branding", {})
                contact_name = tenant_branding.get("contactName", "el candidato")
            
            # Obtener contexto de la campaña desde tenant_memory
            tenant_memory = tenant_memory_service._tenant_memories.get(tenant_id)
            campaign_context = ""
            common_questions = []
            
            if tenant_memory:
                if hasattr(tenant_memory, 'campaign_context') and tenant_memory.campaign_context:
                    campaign_context = tenant_memory.campaign_context
                if hasattr(tenant_memory, 'common_questions') and tenant_memory.common_questions:
                    common_questions = tenant_memory.common_questions[:3]
            
            # 🚀 OPTIMIZACIÓN: Construir contexto completo del usuario
            user_info = ""
            if user_context.get("user_name"):
                user_info += f"El usuario se llama {user_context['user_name']}. "
            if user_context.get("user_city"):
                user_info += f"Vive en {user_context['user_city']}. "
            if user_context.get("user_country"):
                user_info += f"País: {user_context['user_country']}. "
            if user_context.get("user_state"):
                user_info += f"Estado actual: {user_context['user_state']}. "
            if user_context.get("user_phone"):
                user_info += f"Teléfono: {user_context['user_phone']}. "
            
            # El document_context ya contiene la información procesada por la IA
            # Solo necesitamos formatearla de manera más natural
            if document_context and document_context != "NO_ENCONTRADO":
                
                # 🎯 CARGAR PLANTILLA DE PROMPT DESDE DB (si existe)
                prompt_template = None
                stored_prompts = document_index_persistence_service.get_tenant_prompts(tenant_id)
                if stored_prompts and 'document_response_template' in stored_prompts:
                    prompt_template = stored_prompts['document_response_template']
                    logger.info(f"✅ Usando plantilla de prompt desde DB para tenant {tenant_id}")
                
                # Si no hay plantilla en DB, usar la por defecto
                if not prompt_template:
                    prompt_template = """Eres el asistente virtual de la campaña de {contact_name}.

INFORMACIÓN DEL CANDIDATO:
{contact_name} es candidato político. {campaign_context_info}

CONTEXTO DEL USUARIO:
{user_info}

DOCUMENTOS DE LA CAMPAÑA (información específica):
{document_context}

PREGUNTA DEL USUARIO: "{query}"

INSTRUCCIONES:
1. Responde sobre {contact_name} y su campaña de manera natural y empática
2. USA la información de los documentos proporcionados arriba
3. Sé específico y concreto, NO uses frases genéricas como "La información disponible"
4. Si tienes información específica sobre el tema, menciónala directamente
5. Personaliza tu respuesta usando el nombre del usuario si está disponible
6. Máximo 250 palabras
7. Tono: empático, cercano y profesional

RESPUESTA:"""
                
                # Formatear plantilla con valores dinámicos
                campaign_context_info = f"Contexto de campaña: {campaign_context[:200]}" if campaign_context else ""
                
                prompt = prompt_template.format(
                    contact_name=contact_name,
                    campaign_context_info=campaign_context_info,
                    user_info=user_info if user_info else 'Usuario nuevo sin información adicional',
                    document_context=document_context,
                    query=query
                )
                
                # 🧠 Generar respuesta usando el prompt con contexto del tenant y documentos
                logger.info(f"🤖 Generando respuesta con IA usando prompt de {len(prompt)} caracteres")
                
                try:
                    # Usar el modelo Gemini directamente
                    if self.model:
                        response = self.model.generate_content(prompt, safety_settings=self._get_safety_settings())
                        response_text = response.text.strip()
                        
                        logger.info(f"✅ Respuesta generada: {len(response_text)} caracteres")
                        print(f"🤖 RESPUESTA GENERADA: {response_text[:200]}...")
                    else:
                        logger.error("⚠️ Modelo Gemini no disponible")
                        response_text = f"Sobre este tema, {contact_name} tiene información específica que te puede interesar."
                except Exception as e:
                    logger.error(f"❌ Error generando respuesta con IA: {e}")
                    response_text = f"Sobre este tema, {contact_name} tiene información específica que te puede interesar."
                
                # 🚀 OPTIMIZACIÓN: Guardar en caché por tenant (respeta conciencia individual)
                tenant_cache_key = f"{tenant_id}:{cache_key}"
                self._response_cache[tenant_cache_key] = response_text
                
                return response_text
            else:
                # Si no se encontró información específica, usar respuesta genérica
                return await self._generate_candidate_response_gemini_direct(
                    query, user_context, branding_config, tenant_config
                )
            
        except Exception as e:
            logger.error(f"Error generando respuesta con documentos: {e}")
            return f"Sobre este tema, {contact_name} tiene información específica que te puede interesar. Te puedo ayudar a conectarte con nuestro equipo para obtener más detalles."
    
    
    def _get_greeting_response(self, branding_config: Dict[str, Any]) -> str:
        """
        Respuesta rápida para saludos comunes
        """
        contact_name = branding_config.get("contactName", "el candidato")
        
        greetings = [
            f"!Hola! 👋 !Qué gusto saludarte! Soy el asistente virtual de la campaña de {contact_name}.",
            f"!Hola! 😊 !Bienvenido! Estoy aquí para ayudarte con información sobre la campaña de {contact_name}.",
            f"!Hola! [CELEBRACION] !Excelente día! Soy tu asistente para todo lo relacionado con {contact_name}."
        ]
        
        import random
        return random.choice(greetings)
    
    def _get_volunteer_response(self, branding_config: Dict[str, Any]) -> str:
        """
        Respuesta rápida para consultas de voluntariado
        """
        contact_name = branding_config.get("contactName", "el candidato")
        
        return f"""!Excelente! [OBJETIVO] Me emociona saber que quieres ser parte del equipo de {contact_name}.

[ESTRELLA] *?Cómo puedes ayudar?*
- Difundir el mensaje en redes sociales
- Participar en actividades de campo
- Organizar eventos en tu comunidad
- Invitar amigos y familiares

[IDEA] *?Sabías que puedes ganar puntos?*
Cada persona que se registre con tu código te suma 50 puntos al ranking. !Es una forma divertida de competir mientras ayudas!

?Te gustaría que te envíe tu link de referido para empezar a ganar puntos?"""
    
    def _truncate_response_intelligently(self, text: str, max_length: int = 1000) -> str:
        """
        Trunca el texto de forma inteligente, buscando un punto de corte natural
        GARANTIZA que la respuesta nunca exceda max_length (por defecto 1000 caracteres)
        """
        if not text:
            return text
            
        if len(text) <= max_length:
            return text
        
        # Buscar el mejor punto de corte antes del límite
        search_length = min(max_length - 10, len(text))  # Dejar espacio para corte natural
        
        # Buscar puntos de corte naturales en orden de preferencia
        cut_points = [
            text.rfind('. ', 0, search_length),  # Punto seguido de espacio
            text.rfind('.\n', 0, search_length),  # Punto seguido de salto de línea
            text.rfind('! ', 0, search_length),  # Exclamación seguida de espacio
            text.rfind('? ', 0, search_length),  # Interrogación seguida de espacio
            text.rfind(':', 0, search_length),  # Dos puntos (para completar listas)
            text.rfind('; ', 0, search_length),  # Punto y coma seguido de espacio
            text.rfind(', ', 0, search_length),  # Coma seguida de espacio
            text.rfind(' - ', 0, search_length),  # Guión seguido de espacio
            text.rfind('\n', 0, search_length),  # Salto de línea
            text.rfind(' ', 0, search_length),  # Cualquier espacio
        ]
        
        # Encontrar el mejor punto de corte
        best_cut = -1
        for cut_point in cut_points:
            if cut_point > best_cut and cut_point > max_length * 0.8:  # Al menos 80% del límite para respuestas más completas
                best_cut = cut_point
        
        if best_cut > 0:
            truncated = text[:best_cut + 1].strip()
            # No agregar "..." - la respuesta debe ser completa y concisa
            # GARANTIZAR que no exceda el límite
            if len(truncated) > max_length:
                truncated = truncated[:max_length].rstrip()
            return truncated
        else:
            # Si no se encuentra un buen punto de corte, cortar en el límite exacto sin "..."
            return text[:max_length].rstrip()
    
    def _ensure_max_response_length(self, response: str, max_length: int = 1000) -> str:
        """
        GARANTIZA que la respuesta no exceda max_length caracteres
        Usa truncamiento inteligente que respeta límites de oraciones
        """
        if not response:
            return response
        return self._truncate_response_intelligently(response, max_length)
    
    def _filter_links_from_response(self, response: str, intent: str = None) -> str:
        """
        Elimina completamente enlaces y referencias a enlaces de las respuestas para WhatsApp
        EXCEPTO enlaces de Calendly cuando la intención es cita_campaña
        EXCEPTO enlaces de Forms cuando la intención es publicidad_info
        """
        import re
        
        # Si es una respuesta de cita, mantener enlaces de Calendly
        if intent == "cita_campaña":
            logger.info("[CALENDARIO] Intención de cita detectada, manteniendo enlaces de Calendly")
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
        
        # Si es una respuesta de publicidad, mantener enlaces de Forms
        if intent == "publicidad_info":
            logger.info("[PUBLICIDAD] Intención de publicidad detectada, manteniendo enlaces de Forms")
            # Solo limpiar referencias a enlaces pero mantener enlaces de Forms
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
        
        # 🔧 FIX: Eliminar placeholders de enlaces que puedan aparecer
        placeholder_patterns = [
            r'\[ENLACE DE WHATSAPP PARA COMPARTIR\]',
            r'\[ENLACE DE WHATSAPP\]',
            r'\[ENLACE PARA COMPARTIR\]',
            r'\[ENLACE\]',
            r'\[LINK DE WHATSAPP\]',
            r'\[LINK PARA COMPARTIR\]',
            r'\[LINK\]',
            r'\[URL\]',
        ]
        
        for pattern in placeholder_patterns:
            filtered_response = re.sub(pattern, '', filtered_response, flags=re.IGNORECASE)
        
        return filtered_response.strip()
    
    def _handle_appointment_request(self, branding_config: Dict[str, Any], tenant_config: Dict[str, Any] = None) -> str:
        """Maneja solicitudes de agendar citas"""
        # 🔧 DEBUG: Log de entrada al método
        logger.info(f"[CALENDARIO] MANEJANDO SOLICITUD DE CITA")
        logger.info(f"[GRAFICO] tenant_config disponible: {tenant_config is not None}")
        if tenant_config:
            logger.info(f"[GRAFICO] link_calendly en tenant_config: {'link_calendly' in tenant_config}")
        
        contact_name = branding_config.get("contactName", "el candidato")
        
        # Obtener link de Calendly con prioridad de fuentes
        if tenant_config and tenant_config.get("link_calendly"):
            calendly_link = tenant_config.get("link_calendly")
            logger.info(f"[OK] Usando link de Calendly desde BD: {calendly_link}")
        else:
            calendly_link = "https://calendly.com/dq-campana/reunion"
            logger.warning(f"[ADVERTENCIA] Link de Calendly NO encontrado en tenant_config, usando fallback: {calendly_link}")
        
        response = f"""!Perfecto! Te ayudo a agendar una cita con alguien de la campaña de {contact_name}. 

[CALENDARIO] **Para agendar tu reunión:**
Puedes usar nuestro sistema de citas en línea: {calendly_link}

[OBJETIVO] **?Qué puedes hacer en la reunión?**
- Conocer más sobre las propuestas de {contact_name}
- Hablar sobre oportunidades de voluntariado
- Discutir ideas para la campaña
- Coordinar actividades en tu región

[IDEA] **Mientras tanto:**
?Sabías que puedes sumar puntos invitando a tus amigos y familiares a unirse a este movimiento? Cada persona que se registre con tu código te suma 50 puntos al ranking.

?Te gustaría que te envíe tu link de referido para empezar a ganar puntos?"""
        
        # 🔧 DEBUG: Log de la respuesta generada
        logger.info(f"[OK] Respuesta de cita generada: {len(response)} caracteres")
        
        return response
    
    async def _handle_functional_request_with_session(self, query: str, user_context: Dict[str, Any], 
                                                    ai_config: Dict[str, Any], branding_config: Dict[str, Any], 
                                                    tenant_id: str, session_id: str, tenant_config: Dict[str, Any] = None) -> str:
        """Maneja solicitudes funcionales con contexto de sesión para respuestas más naturales"""
        try:
            logger.info(f"🔧 INICIANDO _handle_functional_request_with_session para query: '{query}'")
            logger.info(f"🔧 Parámetros recibidos:")
            logger.info(f"🔧   - query: {query}")
            logger.info(f"🔧   - tenant_id: {tenant_id}")
            logger.info(f"🔧   - session_id: {session_id}")
            logger.info(f"🔧   - user_context: {user_context}")
            
            # 🔍 DEBUG CRÍTICO: Ver qué tenant_config recibimos
            logger.info(f"🔧   - tenant_config recibido: {bool(tenant_config)}")
            logger.info(f"🔧   - tenant_config keys: {list(tenant_config.keys()) if tenant_config else 'None'}")
            if tenant_config and 'numero_whatsapp' in tenant_config:
                logger.info(f"✅ [_handle_functional_request_with_session] numero_whatsapp PRESENTE: '{tenant_config['numero_whatsapp']}'")
            else:
                logger.warning(f"❌ [_handle_functional_request_with_session] numero_whatsapp NO PRESENTE en tenant_config")
            
            # Obtener contexto de sesión
            session_context = session_context_service.build_context_for_ai(session_id)
            logger.info(f"📝 Contexto de sesión obtenido: {len(session_context) if session_context else 0} elementos")
            
            # Obtener nombre del contacto desde branding_config
            contact_name = branding_config.get("contact_name", branding_config.get("contactName", "el candidato"))
            logger.info(f"👤 Nombre del contacto: {contact_name}")
            
            # Intentar obtener datos reales del usuario
            logger.info(f"🔍 Obteniendo datos del usuario para tenant: {tenant_id}")
            logger.info(f"🔍 user_context completo: {user_context}")
            logger.info(f"🔍 phone en user_context: {user_context.get('phone')}")
            logger.info(f"🔍 user_id en user_context: {user_context.get('user_id')}")
            logger.info(f"🔍 user_state en user_context: {user_context.get('user_state')}")
            
            user_data = self._get_user_progress_data(tenant_id, user_context)
            logger.info(f"📊 Datos del usuario obtenidos: {bool(user_data)}")
            logger.info(f"📊 Tipo de user_data: {type(user_data)}")
            logger.info(f"📊 Contenido de user_data: {user_data}")
            
            # Si no se pudieron obtener datos del servicio Java, usar datos del user_context
            if not user_data and user_context:
                logger.warning(f"⚠️ user_data es None, usando datos del user_context")
                # Construir user_data desde user_context
                user_data = {
                    "user": {
                        "name": user_context.get("name", "Usuario"),
                        "city": user_context.get("city"),
                        "state": user_context.get("state")
                    },
                    "points": user_context.get("points", 0),
                    "total_referrals": user_context.get("total_referrals", 0),
                    "completed_referrals": user_context.get("completed_referrals", []),
                    "referral_code": user_context.get("referral_code")
                }
                logger.info(f"📊 user_data construido desde user_context: {user_data}")
            elif user_data:
                logger.info(f"📊 Detalles de user_data: {user_data}")
            
            if user_data:
                # Si tenemos datos reales, crear un prompt contextualizado
                user_name = user_data.get("user", {}).get("name", "Usuario")
                points = user_data.get("points", 0)
                total_referrals = user_data.get("total_referrals", 0)
                completed_referrals = user_data.get("completed_referrals", [])
                # 🔧 FIX: Asegurar que completed_referrals sea una lista
                if not isinstance(completed_referrals, list):
                    logger.warning(f"⚠️ completed_referrals no es una lista, es: {type(completed_referrals)}")
                    completed_referrals = []
                referral_code = user_data.get("referral_code")
                
                logger.info(f"🔍 Datos del usuario procesados:")
                logger.info(f"🔍   - user_name: {user_name}")
                logger.info(f"🔍   - points: {points}")
                logger.info(f"🔍   - total_referrals: {total_referrals}")
                logger.info(f"🔍   - referral_code: {referral_code}")
                logger.info(f"🔍   - Tipo de referral_code: {type(referral_code)}")
                logger.info(f"🔍   - user_data completo: {user_data}")
                
                # Verificar si es solicitud de enlace o consulta de progreso
                query_lower = query.lower().strip()
                link_keywords = ["link", "código", "codigo", "referido", "mandame", "dame", "enlace", "compartir", "comparte", "envia", "envía", "link", "url", "mi enlace", "mi código", "mi codigo"]
                
                # 🎯 NUEVO: Detectar consultas de progreso del usuario
                progress_keywords = ["como voy", "cuantos puntos", "cuántos puntos", "mis puntos", "mi progreso", 
                                      "mis referidos", "cuantos referidos", "cuántos referidos", "ver mis", "estado"]
                is_progress_query = any(keyword in query_lower for keyword in progress_keywords)
                logger.info(f"🔍 Es consulta de progreso: {is_progress_query}")
                logger.info(f"🔍 Query original: '{query}'")
                logger.info(f"🔍 Query lower: '{query_lower}'")
                
                logger.info(f"🔍 Verificando palabras clave de enlace en: '{query_lower}'")
                logger.info(f"🔍 Palabras clave: {link_keywords}")
                logger.info(f"🔍 referral_code: {referral_code}")
                
                found_keywords = [word for word in link_keywords if word in query_lower]
                logger.info(f"🔍 Palabras encontradas: {found_keywords}")
                
                # Verificación más robusta
                is_link_request = (
                    referral_code and 
                    any(word in query_lower for word in link_keywords)
                ) or (
                    referral_code and 
                    ("mi" in query_lower and ("enlace" in query_lower or "código" in query_lower or "codigo" in query_lower))
                )
                
                logger.info(f"🔍 Es solicitud de enlace: {is_link_request}")
                
                # 🎯 NUEVO: Siempre incluir enlace si es consulta de progreso o solicitud de enlace
                should_include_link = is_link_request or (is_progress_query and referral_code)
                logger.info(f"🔍 Incluir enlace: {should_include_link} (es_link: {is_link_request}, es_progreso: {is_progress_query}, referral_code: {bool(referral_code)})")
                
                # Si es consulta de progreso pero NO hay código, aún devolver datos del usuario
                if is_progress_query and not should_include_link:
                    logger.warning(f"⚠️ Consulta de progreso SIN código de referido")
                
                # 🔧 FIX: Crear contextual_prompt ANTES para que esté disponible en todos los casos
                contextual_prompt = self._build_functional_prompt_with_data(
                    query, user_context, branding_config, session_context, user_data, tenant_id
                )
                
                if should_include_link:
                    logger.info(f"🔗 NUEVO ENFOQUE: Generando respuesta con enlace - es_link: {is_link_request}, es_progreso: {is_progress_query}")
                    
                    # Generar enlace de WhatsApp
                    whatsapp_link = self._generate_whatsapp_referral_link(user_name, referral_code, contact_name, tenant_id, user_context, tenant_config)
                    
                    if whatsapp_link:
                        # Generar respuesta principal sin enlace
                        points = user_data.get("points", 0)
                        total_referrals = user_data.get("total_referrals", 0)
                        completed_referrals = user_data.get("completed_referrals", [])
                        # 🔧 FIX: Asegurar que completed_referrals sea una lista
                        if not isinstance(completed_referrals, list):
                            logger.warning(f"⚠️ completed_referrals no es una lista, es: {type(completed_referrals)}")
                            completed_referrals = []
                        
                        # 🎯 Mensaje personalizado según el tipo de consulta
                        if is_progress_query:
                            # Consulta de progreso: mensaje motivacional con datos
                            response = f"""¡Hola {user_name}! 🚀 Aquí está tu progreso:

📊 **Tu progreso:**
• Puntos: {points}
• Referidos completados: {len(completed_referrals) if completed_referrals else 0}
• Total de referidos: {total_referrals}
• Tu código: {referral_code}

💡 **Tip:** Cada persona que se registre con tu código te suma 50 puntos. Comparte tu enlace para seguir creciendo.

En el siguiente mensaje te envío tu enlace para compartir 📲"""
                        else:
                            # Solicitud explícita de enlace
                            response = f"""¡Claro que sí, {user_name}! 🚀 Aquí tienes tu información para seguir sumando más personas a la campaña de {contact_name}:

📊 **Tu progreso actual:**
- Puntos: {points}
- Referidos completados: {len(completed_referrals) if completed_referrals else 0}
- Total de referidos: {total_referrals}
- Tu código: {referral_code}

¡Vamos con toda, {user_name}! Con tu ayuda, llegaremos a más rincones de Colombia. 💪🇨🇴

En el siguiente mensaje te envío tu enlace para compartir."""
                        
                        logger.info(f"✅ NUEVO ENFOQUE: Respuesta generada, enlace en followup_message")
                        # Devolver la respuesta con el enlace en el campo followup_message
                        return response, whatsapp_link
                    else:
                        logger.warning(f"⚠️ NUEVO ENFOQUE: No se pudo generar enlace de WhatsApp")
                        response = await self._generate_content(contextual_prompt, task_type="functional_with_data")
                        return response, None
                else:
                    logger.info(f"⚠️ No se detectaron palabras clave de enlace o no hay código de referido")
                    logger.info(f"⚠️ Condición: referral_code={bool(referral_code)}, keywords_detected={any(word in query_lower for word in link_keywords)}")
                    logger.info(f"⚠️ Query procesado: '{query_lower}'")
                    logger.info(f"⚠️ Palabras clave disponibles: {link_keywords}")
                    logger.info(f"⚠️ Palabras encontradas: {found_keywords}")
                
                # 🔧 FIX: contextual_prompt ya se creó antes, solo generar respuesta con IA
                logger.info(f"🔧 Usando contextual_prompt creado previamente")
                
                # Generar respuesta con IA usando el contexto
                response_text = await self._generate_content(contextual_prompt, task_type="functional_with_data")
                
                logger.info(f"🔧 RETORNANDO respuesta desde _handle_functional_request_with_session (fallback)")
                return response_text, ""  # 🔧 FIX: Retornar tupla consistente (response, "")
            else:
                # Fallback: usar respuesta genérica pero con contexto de sesión
                contextual_prompt = self._build_functional_prompt_generic(
                    query, user_context, branding_config, session_context
                )
                
                response_text = await self._generate_content(contextual_prompt, task_type="functional_generic")
                logger.info(f"🔧 RETORNANDO respuesta desde _handle_functional_request_with_session (genérico)")
                return response_text, ""  # 🔧 FIX: Retornar tupla consistente (response, "")
                
        except Exception as e:
            logger.error(f"Error manejando solicitud funcional con sesión: {str(e)}")
            logger.exception(e)  # 🔧 FIX: Imprimir traceback completo
            # Fallback a respuesta básica - asegurar que retorne tupla
            try:
                fallback_response = self._handle_functional_request(query, branding_config, tenant_id, user_context)
                if isinstance(fallback_response, tuple):
                    return fallback_response
                else:
                    return fallback_response, ""
            except Exception as fallback_error:
                logger.error(f"Error en fallback también: {str(fallback_error)}")
                return f"Lo siento, hubo un error procesando tu solicitud. Intenta de nuevo.", ""
    
    def _build_functional_prompt_with_data(self, query: str, user_context: Dict[str, Any], 
                                         branding_config: Dict[str, Any], session_context: str, 
                                         user_data: Dict[str, Any], tenant_id: str = None) -> str:
        """Construye un prompt contextualizado con datos reales del usuario"""
        contact_name = branding_config.get("contactName", "el candidato")
        user = user_data.get("user", {})
        points = user_data.get("points", 0)
        total_referrals = user_data.get("total_referrals", 0)
        completed_referrals = user_data.get("completed_referrals", [])
        # 🔧 FIX: Asegurar que completed_referrals sea una lista
        if not isinstance(completed_referrals, list):
            logger.warning(f"⚠️ completed_referrals no es una lista en _build_functional_prompt_with_data, es: {type(completed_referrals)}")
            completed_referrals = []
        referral_code = user_data.get("referral_code")
        
        user_name = user.get("name", "Usuario")
        user_city = user.get("city", "tu ciudad")
        user_state = user.get("state", "tu departamento")
        
        # Construir información de referidos
        referrals_info = ""
        if completed_referrals:
            referrals_info = f"\nReferidos completados:\n"
            for i, ref in enumerate(completed_referrals[:3], 1):  # Mostrar solo los primeros 3
                ref_name = ref.get("name", "Usuario")
                ref_city = ref.get("city", "ciudad")
                referrals_info += f"- {ref_name} de {ref_city}\n"
            if len(completed_referrals) > 3:
                referrals_info += f"- ... y {len(completed_referrals) - 3} más\n"
        
        # 🔧 FIX: NO generar enlace aquí - debe manejarse en la lógica principal
        # para evitar que aparezca en la respuesta principal
        whatsapp_link = ""
        query_lower = query.lower().strip()
        link_keywords = ["link", "código", "codigo", "referido", "mandame", "dame", "enlace", "compartir", "comparte", "envia", "envía", "link", "url", "mi enlace", "mi código", "mi codigo"]
        
        logger.info(f"🔍 Verificando si es solicitud de enlace - Query: '{query}' - Keywords detectadas: {[kw for kw in link_keywords if kw in query_lower]}")
        
        # Verificación más robusta (igual que en la lógica principal)
        is_link_request = (
            referral_code and 
            any(word in query_lower for word in link_keywords)
        ) or (
            referral_code and 
            ("mi" in query_lower and ("enlace" in query_lower or "código" in query_lower or "codigo" in query_lower))
        )
        
        if is_link_request:
            logger.info(f"🔗 SOLICITUD DE ENLACE DETECTADA - NO incluir en prompt para evitar duplicación")
            # NO generar enlace aquí - se manejará en la lógica principal
        else:
            logger.info(f"❌ No es solicitud de enlace - referral_code: {referral_code}, keywords encontradas: {[kw for kw in link_keywords if kw in query_lower]}")
        
        prompt = f"""Asistente virtual de la campaña de {contact_name}. 

CONTEXTO DE LA CONVERSACIÓN:
{session_context}

DATOS REALES DEL USUARIO:
- Nombre: {user_name}
- Ciudad: {user_city}
- Departamento: {user_state}
- Puntos actuales: {points}
- Total de referidos: {total_referrals}
- Referidos completados: {len(completed_referrals) if completed_referrals else 0}
- Código de referido: {referral_code}
{referrals_info}

CONSULTA DEL USUARIO: "{query}"

INSTRUCCIONES IMPORTANTES:
- Responde de manera natural y conversacional, considerando el contexto de la conversación
- Usa los datos reales del usuario para personalizar la respuesta
- Mantén un tono motivacional y positivo
- Si el usuario pregunta sobre puntos, muestra sus puntos reales
- Si pregunta sobre referidos, menciona sus referidos reales
- Incluye su código de referido si es relevante
- Usa emojis apropiados para WhatsApp
- Mantén la respuesta concisa pero informativa
- **IMPORTANTE**: Si el usuario pide enlace/código/compartir, menciona que recibirá su enlace en un mensaje separado

Responde de manera natural y personalizada:"""

        return prompt
    
    def _build_functional_prompt_generic(self, query: str, user_context: Dict[str, Any], 
                                       branding_config: Dict[str, Any], session_context: str) -> str:
        """Construye un prompt genérico para solicitudes funcionales cuando no hay datos específicos"""
        contact_name = branding_config.get("contactName", "el candidato")
        
        prompt = f"""Asistente virtual de la campaña de {contact_name}.

CONTEXTO DE LA CONVERSACIÓN:
{session_context}

CONSULTA DEL USUARIO: "{query}"

INSTRUCCIONES:
- Responde de manera natural y conversacional, considerando el contexto de la conversación
- Si el usuario pregunta sobre puntos o progreso, explica cómo funciona el sistema
- Mantén un tono motivacional y positivo
- Usa emojis apropiados para WhatsApp
- Mantén la respuesta concisa pero informativa
- Si es relevante, menciona que pueden consultar su progreso específico

Responde de manera natural:"""

        return prompt
    
    def _generate_direct_link_response_with_followup(self, user_name: str, referral_code: str, contact_name: str, tenant_id: str, user_data: Dict[str, Any], user_context: Dict[str, Any] = None) -> str:
        """Genera una respuesta directa con información de seguimiento para segundo mensaje"""
        try:
            logger.info(f"🚀 INICIANDO _generate_direct_link_response_with_followup")
            logger.info(f"🚀 Parámetros: user_name={user_name}, referral_code={referral_code}, contact_name={contact_name}, tenant_id={tenant_id}")
            
            # Generar enlace de WhatsApp
            logger.info(f"🔗 Generando enlace de WhatsApp para {user_name} con código {referral_code}")
            whatsapp_link = self._generate_whatsapp_referral_link(user_name, referral_code, contact_name, tenant_id, user_context, None)
            logger.info(f"🔗 Enlace generado: {whatsapp_link}")
            logger.info(f"🔗 Longitud del enlace: {len(whatsapp_link) if whatsapp_link else 0}")
            
            has_followup_link = bool(whatsapp_link and whatsapp_link.strip())
            logger.info(f"🔗 ¿Tiene enlace válido?: {has_followup_link}")
            logger.info(f"🔗 whatsapp_link.strip(): '{whatsapp_link.strip() if whatsapp_link else ''}'")
            
            # Obtener datos adicionales
            points = user_data.get("points", 0)
            total_referrals = user_data.get("total_referrals", 0)
            completed_referrals = user_data.get("completed_referrals", [])
            
            # Generar respuesta principal (sin enlace)
            completed_count = len(completed_referrals) if completed_referrals else 0
            response = f"""¡Claro que sí, {user_name}! 🚀 Aquí tienes la información para que sigas sumando más personas a la campaña de {contact_name}:

📊 **Tu progreso actual:**
- Puntos: {points}
- Referidos completados: {completed_count}
- Total de referidos: {total_referrals}
- Tu código: {referral_code}

¡Vamos con toda, {user_name}! Con tu ayuda, llegaremos a más rincones de Colombia. 💪🇨🇴"""

            if has_followup_link:
                logger.info(f"🔁 Se enviará segundo mensaje con enlace (len={len(whatsapp_link) if whatsapp_link else 0})")
                response += "\n\nEn el siguiente mensaje te envío tu enlace para compartir."
            
            # Agregar información especial para el segundo mensaje solo si hay enlace
            if has_followup_link and whatsapp_link and whatsapp_link.strip():
                response += f"\n\n<<<FOLLOWUP_MESSAGE_START>>>{whatsapp_link}<<<FOLLOWUP_MESSAGE_END>>>"
                logger.info(f"✅ Marcador FOLLOWUP_MESSAGE agregado con enlace válido")
                logger.info(f"🔗 Enlace completo en marcador: {whatsapp_link}")
            else:
                logger.warning(f"⚠️ No se agregó marcador FOLLOWUP_MESSAGE - enlace vacío o inválido")
                logger.warning(f"⚠️ has_followup_link: {has_followup_link}, whatsapp_link: '{whatsapp_link if whatsapp_link else None}'")
            
            logger.info(f"✅ Respuesta directa generada con seguimiento para {user_name}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error generando respuesta directa con seguimiento: {str(e)}")
            return f"¡Hola {user_name}! Tu código de referido es: {referral_code}"
    
    def _generate_direct_link_response(self, user_name: str, referral_code: str, contact_name: str, tenant_id: str, user_data: Dict[str, Any], user_context: Dict[str, Any] = None, tenant_config: Dict[str, Any] = None) -> str:
        """Genera una respuesta directa con el enlace de WhatsApp cuando se solicita"""
        try:
            # Generar enlace de WhatsApp
            whatsapp_link = self._generate_whatsapp_referral_link(user_name, referral_code, contact_name, tenant_id, user_context, tenant_config)
            
            if not whatsapp_link:
                logger.error("❌ No se pudo generar enlace de WhatsApp")
                return f"¡Hola {user_name}! Tu código de referido es: {referral_code}"
            
            # Obtener datos adicionales
            points = user_data.get("points", 0)
            total_referrals = user_data.get("total_referrals", 0)
            completed_referrals = user_data.get("completed_referrals", [])
            
            # Generar respuesta directa con enlace
            completed_count = len(completed_referrals) if completed_referrals else 0
            response = f"""¡Claro que sí, {user_name}! 🚀 Aquí tienes tu enlace de WhatsApp personalizado para que sigas sumando más personas a la campaña de {contact_name}:

📊 **Tu progreso actual:**
- Puntos: {points}
- Referidos completados: {completed_count}
- Total de referidos: {total_referrals}
- Tu código: {referral_code}

¡Vamos con toda, {user_name}! Con tu ayuda, llegaremos a más rincones de Colombia. 💪🇨🇴

En el siguiente mensaje te envío tu enlace para compartir."""
            
            logger.info(f"✅ Respuesta directa generada con enlace para {user_name}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error generando respuesta directa: {str(e)}")
            return f"¡Hola {user_name}! Tu código de referido es: {referral_code}"
    
    def _generate_whatsapp_referral_link(self, user_name: str, referral_code: str, contact_name: str, tenant_id: str = None, user_context: Dict[str, Any] = None, tenant_config: Dict[str, Any] = None) -> str:
        """Genera un enlace de WhatsApp personalizado para referidos"""
        try:
            # 🔍 DEBUG CRÍTICO: Ver de dónde viene el tenant_config que se usará
            logger.info(f"🔍 [_generate_whatsapp_referral_link] tenant_config pasado al parámetro: keys={list(tenant_config.keys()) if tenant_config else 'None'}")
            
            # Si no se pasó tenant_config como parámetro, intentar obtenerlo desde user_context
            if not tenant_config:
                # Obtener número de WhatsApp del tenant desde memoria precargada
                tenant_context = user_context.get('tenant_context', {}) if user_context else {}
                tenant_config = tenant_context.get('tenant_config', {})
                logger.warning(f"⚠️ [_generate_whatsapp_referral_link] tenant_config NO pasado como parámetro, usando de user_context")
            else:
                logger.info(f"✅ [_generate_whatsapp_referral_link] tenant_config pasado como parámetro")
            
            logger.info(f"🔍 [_generate_whatsapp_referral_link] tenant_config final que se usará: keys={list(tenant_config.keys()) if tenant_config else 'None'}")
            
            whatsapp_number = self._get_tenant_whatsapp_number(tenant_id, tenant_config)
            # Validar número
            logger.info(f"📱 Número obtenido de _get_tenant_whatsapp_number: '{whatsapp_number}'")
            if not whatsapp_number or not str(whatsapp_number).strip():
                logger.warning("⚠️ No hay numero_whatsapp configurado para el tenant; no se generará enlace")
                return ""
            
            # 🔧 FIX: Validar que no sea el tenant_id
           
            logger.info(f"📱 Generando enlace con número: {whatsapp_number}")
            
            # Generar el texto del mensaje que el usuario compartirá
            import urllib.parse
            
            # Mensaje más claro y reenviable
            referral_text = f"Hola, vengo referido por {user_name}, codigo: {referral_code}"
            encoded_referral_text = urllib.parse.quote(referral_text)
            
            # Generar el enlace de registro con parámetros para facilitar reenvío
            registration_link = f"https://wa.me/{whatsapp_number}?text={encoded_referral_text}&context=forward&type=link"
            
            # Mensaje completo optimizado para reenvío (manteniendo formato original)
            message_text = f"Amigos, soy {user_name} y quiero invitarte a unirte a la campaña de {contact_name}: {registration_link}"
            
            # Este es el mensaje final que se enviará (sin encoding adicional)
            whatsapp_link = message_text
            
            logger.info(f"✅ Enlace de WhatsApp generado para {user_name} con código {referral_code}")
            logger.info(f"🔗 Enlace completo: {whatsapp_link}")
            
            return whatsapp_link
            
        except Exception as e:
            logger.error(f"❌ Error generando enlace de WhatsApp: {str(e)}")
            return ""
    
    def _get_tenant_whatsapp_number(self, tenant_id: str, tenant_config: Dict[str, Any] = None) -> str:
        """Obtiene el número de WhatsApp configurado para el tenant desde memoria precargada"""
        try:
            logger.info(f"🔍 INICIANDO _get_tenant_whatsapp_number para tenant: {tenant_id}")
            if tenant_id:
                # 🚀 OPTIMIZACIÓN: Usar configuración del tenant desde memoria precargada
                if not tenant_config:
                    logger.warning(f"⚠️ No hay configuración del tenant {tenant_id} para WhatsApp")
                    return ""
                
                logger.info(f"✅ Usando configuración del tenant {tenant_id} desde memoria precargada para WhatsApp")
                logger.info(f"📋 Configuración del tenant {tenant_id}: {tenant_config}")
                if tenant_config:
                    logger.info(f"📋 TODOS los campos en tenant_config: {list(tenant_config.keys())}")
                    logger.info(f"📋 Contenido completo de tenant_config: {tenant_config}")
                    
                    # Aceptar claves alternativas por compatibilidad
                    whatsapp_number = None
                    if "numero_whatsapp" in tenant_config:
                        whatsapp_number = tenant_config.get("numero_whatsapp")
                        logger.info(f"📱 Encontrado numero_whatsapp: {whatsapp_number}")
                    elif "whatsapp_number" in tenant_config:
                        whatsapp_number = tenant_config.get("whatsapp_number")
                        logger.info(f"📱 Encontrado whatsapp_number: {whatsapp_number}")
                    
                    if whatsapp_number and str(whatsapp_number).strip():
                        # 🔧 VALIDACIÓN CRÍTICA: Asegurar que NO sea el tenant_id
                        if str(whatsapp_number).strip() == str(tenant_id).strip():
                            logger.error(f"❌ ERROR: El número de WhatsApp es igual al tenant_id '{tenant_id}'. No se generará enlace.")
                            return ""
                        
                        logger.info(f"✅ Número de WhatsApp del tenant {tenant_id}: {whatsapp_number}")
                        return str(whatsapp_number).strip()

                    logger.warning(
                        f"⚠️ No se encontró numero_whatsapp/whatsapp_number en configuración del tenant {tenant_id}. Keys disponibles: {list(tenant_config.keys())}"
                    )
                else:
                    logger.warning(f"⚠️ No se pudo obtener configuración del tenant {tenant_id}")
            else:
                logger.warning("⚠️ tenant_id es None o vacío")
            # Sin número configurado
            logger.info(f"🔍 RETORNANDO cadena vacía desde _get_tenant_whatsapp_number")
            return ""
            
        except Exception as e:
            logger.warning(f"❌ Error obteniendo número de WhatsApp del tenant: {e}")
            return ""
    
    def _get_user_progress_data(self, tenant_id: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene los datos de progreso del usuario desde el servicio Java"""
        try:
            logger.info(f"🔍 _get_user_progress_data llamado con tenant_id: {tenant_id}, user_context: {user_context}")
            
            if not tenant_id or not user_context:
                logger.warning("Faltan parámetros para consultar datos del usuario")
                return None
                
            phone = user_context.get("phone")
            logger.info(f"🔍 Teléfono obtenido del contexto: {phone}")
            
            if not phone:
                logger.warning("No se encontró teléfono en el contexto del usuario")
                return None
            
            # 🚀 OPTIMIZACIÓN: Usar configuración del tenant desde memoria precargada
            tenant_context = user_context.get('tenant_context', {})
            tenant_config = tenant_context.get('tenant_config', {})
            if not tenant_config:
                logger.warning(f"No se encontró configuración para tenant {tenant_id} en memoria precargada")
                return None
                
            client_project_id = tenant_config.get("client_project_id")
            if not client_project_id:
                logger.warning(f"No se encontró client_project_id para tenant {tenant_id}")
                return None
            
            # Consultar datos del usuario desde el servicio Java
            import requests
            import os
            
            java_service_url = os.getenv("POLITICAL_REFERRALS_SERVICE_URL")
            logger.info(f"🔍 Java service URL: {java_service_url}")
            if not java_service_url:
                logger.warning("POLITICAL_REFERRALS_SERVICE_URL no configurado")
                return None
            
            # 🔧 FIX: Usar endpoint de progreso que retorna todo junto
            progress_url = f"{java_service_url}/api/users/progress"
            progress_payload = {
                "clientProjectId": client_project_id,
                "phone": phone
            }
            
            logger.info(f"🔍 Consultando progreso de usuario: {progress_url} con payload: {progress_payload}")
            
            progress_response = requests.post(progress_url, json=progress_payload, timeout=10)
            logger.info(f"🔍 Respuesta de progreso: status={progress_response.status_code}")
            if progress_response.status_code != 200:
                logger.warning(f"❌ Error consultando progreso: {progress_response.status_code}")
                logger.warning(f"❌ Response text: {progress_response.text}")
                return None
                
            progress_data = progress_response.json()
            logger.info(f"🔍 Datos de progreso obtenidos: {progress_data}")
            if not progress_data:
                logger.warning("❌ No se obtuvo progreso del usuario")
                return None
            
            # Extraer datos del usuario y referidos
            user_data = progress_data.get("user", {})
            referral_code = user_data.get("referral_code")
            points = progress_data.get("points", 0)
            total_referrals = progress_data.get("totalReferrals", 0)
            completed_referrals_count = progress_data.get("completedReferrals", 0)
            referrals = progress_data.get("referrals", [])
            
            logger.info(f"✅ Progreso obtenido: points={points}, total_referrals={total_referrals}, referral_code={referral_code}")
            
            completed_referrals = [r for r in referrals if r.get("completed", False)]
            
            return {
                "user": user_data,
                "referrals": referrals,
                "completed_referrals": completed_referrals,
                "points": points,
                "referral_code": referral_code,
                "total_referrals": total_referrals
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos del usuario: {str(e)}")
            return None
    
    def _format_user_progress_response(self, user_data: Dict[str, Any], contact_name: str) -> str:
        """Formatea la respuesta con los datos reales del usuario"""
        try:
            user = user_data.get("user", {})
            points = user_data.get("points", 0)
            total_referrals = user_data.get("total_referrals", 0)
            completed_referrals = user_data.get("completed_referrals", [])
            referral_code = user_data.get("referral_code")
            
            user_name = user.get("name", "Usuario")
            user_city = user.get("city", "tu ciudad")
            
            completed_count = len(completed_referrals) if completed_referrals else 0
            response = f"""🎯 **¡Hola {user_name}! Aquí está tu progreso:**

[TROFEO] **Tus Puntos Actuales: {points}**
- Referidos completados: {completed_count}
- Total de referidos: {total_referrals}
- Puntos por referido: 50 puntos

[GRAFICO] **Tu Ranking:**
- Ciudad: {user_city}
- Departamento: {user.get('state', 'N/A')}
- País: Colombia

[ENLACE] **Tu Código de Referido: {referral_code}**

[OBJETIVO] **¡Sigue invitando!**
Cada persona que se registre con tu código te suma 50 puntos más.

¿Quieres que te envíe tu link personalizado para compartir?"""
            
            return response
            
        except Exception as e:
            logger.error(f"Error formateando respuesta de progreso: {str(e)}")
            return f"Error obteniendo tu progreso. Por favor intenta de nuevo."
    
    def _handle_functional_request(self, query: str, branding_config: Dict[str, Any], tenant_id: str = None, user_context: Dict[str, Any] = None) -> str:
        """Maneja solicitudes funcionales como '?Cómo voy?' o pedir link"""
        query_lower = query.lower()
        contact_name = branding_config.get("contactName", "el candidato")
        
        if any(word in query_lower for word in ["como voy", "cómo voy", "progreso", "puntos", "ranking"]):
            # Intentar obtener datos reales del usuario
            user_data = self._get_user_progress_data(tenant_id, user_context)
            
            if user_data:
                return self._format_user_progress_response(user_data, contact_name)
            else:
                # Fallback a respuesta genérica si no se pueden obtener datos
                return f"""!Excelente pregunta! Te explico cómo funciona el sistema de puntos de la campaña de {contact_name}:

[TROFEO] **Sistema de Puntos:**
- Cada referido registrado con tu código: **50 puntos**
- Retos semanales: **puntaje adicional**
- Ranking actualizado a nivel ciudad, departamento y país

[GRAFICO] **Para ver tu progreso:**
Escribe "?Cómo voy?" y te mostraré:
- Tus puntos totales
- Número de referidos
- Tu puesto en ciudad y nacional
- Lista de quienes están cerca en el ranking

[ENLACE] **Para invitar personas:**
Escribe "dame mi código" o "mandame el link" y te enviaré tu enlace personalizado para referir amigos y familiares.

?Quieres tu código de referido ahora?"""
        
        elif any(word in query_lower for word in ["link", "código", "codigo", "referido", "mandame", "dame"]):
            return f"""!Por supuesto! Te ayudo con tu código de referido para la campaña de {contact_name}.

[ENLACE] **Tu código personalizado:**
Pronto tendrás tu enlace único para referir personas.

[CELULAR] **Cómo usarlo:**
1. Comparte tu link con amigos y familiares
2. Cada persona que se registre suma 50 puntos
3. Sube en el ranking y gana recompensas

[OBJETIVO] **Mensaje sugerido para compartir:**
"!Hola! Te invito a unirte a la campaña de {contact_name}. Es una oportunidad de ser parte del cambio que Colombia necesita. Únete aquí: [TU_LINK]"

?Te gustaría que genere tu código ahora?"""
        
        else:
            return f"""!Claro! Te ayudo con información sobre la campaña de {contact_name}.

Puedes preguntarme sobre:
- Las propuestas de {contact_name}
- Cómo participar en la campaña
- Sistema de puntos y ranking
- Oportunidades de voluntariado
- Agendar citas con el equipo

?En qué te puedo ayudar específicamente?"""
    
    async def classify_intent(self, tenant_id: str, message: str, user_context: Dict[str, Any], session_id: str = None, tenant_config: Dict[str, Any] = None) -> Dict[str, Any]:
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
            logger.info(f"🎯 [CLASIFICACIÓN BASE] Iniciando clasificación para: '{message[:50]}...'")
            logger.info(f"🎯 [CLASIFICACIÓN BASE] Tenant ID: {tenant_id}")
            logger.info(f"🎯 [CLASIFICACIÓN BASE] Session ID: {session_id}")
            
            # 🔍 DEBUG: Verificar si hay historial en user_context
            if user_context and "conversation_history" in user_context:
                history = user_context["conversation_history"]
                logger.info(f"🔍 [CLASIFICACIÓN BASE] Historial detectado en user_context ({len(history) if history else 0} chars)")
                if history:
                    logger.info(f"🔍 [CLASIFICACIÓN BASE] Primeros 200 chars de historial: '{history[:200]}...'")
            else:
                logger.info(f"🔍 [CLASIFICACIÓN BASE] NO hay historial en user_context")
            
            # 🚀 OPTIMIZACIÓN: Detección ultra-rápida para saludos comunes
            message_lower = message.lower().strip()
            if message_lower in self._common_responses:
                classification = self._common_responses[message_lower]
                logger.info(f"🚀 [CLASIFICACIÓN BASE] BYPASS GEMINI: Saludo común '{message_lower}' -> {classification}")
                logger.info(f"📊 [CLASIFICACIÓN BASE] Resultado: {classification} (confianza: 1.0)")
                return {
                    "category": classification,
                    "confidence": 0.95,
                    "original_message": message,
                    "reason": "Bypass Gemini - Saludo común"
                }
            
            # 🚀 VELOCIDAD MÁXIMA: Usar solo IA, sin bypass
            logger.info(f"🎯 USANDO IA DIRECTA: '{message[:30]}...'")
            
            # 🔧 OPTIMIZACIÓN: Detección rápida basada en contexto
            if user_context and user_context.get("user_state") == "WAITING_NAME":
                if self._analyze_registration_intent(message, "name"):
                    logger.info(f"✅ BYPASS GEMINI: Contexto WAITING_NAME -> registration_response")
                    return {
                        "category": "registration_response",
                        "confidence": 0.95,
                        "original_message": message,
                        "reason": "Bypass Gemini - Contexto"
                    }
            
            if user_context and user_context.get("user_state") == "WAITING_LASTNAME":
                if self._analyze_registration_intent(message, "lastname"):
                    logger.info(f"✅ BYPASS GEMINI: Contexto WAITING_LASTNAME -> registration_response")
                    return {
                        "category": "registration_response",
                        "confidence": 0.95,
                        "original_message": message,
                        "reason": "Bypass Gemini - Contexto"
                    }
            
            if user_context and user_context.get("user_state") == "WAITING_CITY":
                if self._analyze_registration_intent(message, "city"):
                    logger.info(f"✅ BYPASS GEMINI: Contexto WAITING_CITY -> registration_response")
                    return {
                        "category": "registration_response",
                        "confidence": 0.95,
                        "original_message": message,
                        "reason": "Bypass Gemini - Contexto"
                    }
            
            # 🔧 OPTIMIZACIÓN: Solo usar Gemini para casos complejos
            logger.info(f"🎯 USANDO GEMINI para caso complejo: '{message[:50]}...'")
            
            # 🚀 OPTIMIZACIÓN CRÍTICA: Usar IA con timeout, reintentar si falla (sin palabras clave)
            import asyncio
            classification_result = None
            try:
                # Intentar con timeout de 8 segundos
                classification_result = await asyncio.wait_for(
                    self._classify_with_ai(message, user_context, "", tenant_id),
                    timeout=8.0
                )
            except asyncio.TimeoutError:
                logger.warning(f"⏰ TIMEOUT en clasificación Gemini para '{message[:30]}...', reintentando con timeout más largo")
                try:
                    # Reintentar con timeout más largo (15 segundos)
                    classification_result = await asyncio.wait_for(
                        self._classify_with_ai(message, user_context, "", tenant_id),
                        timeout=15.0
                    )
                    logger.info("✅ Reintento exitoso después de timeout inicial")
                except asyncio.TimeoutError:
                    logger.error(f"⏰ TIMEOUT también en reintento para '{message[:30]}...', usando fallback genérico")
                    # Fallback genérico sin palabras clave - siempre usar solicitud_funcional como último recurso
                    classification_result = {
                        "category": "solicitud_funcional",
                        "confidence": 0.3,
                        "original_message": message,
                        "reason": "Timeout en clasificación IA - fallback genérico"
                    }
            
            # 🚀 OPTIMIZACIÓN CRÍTICA: Usar configuración enviada desde Java (ya optimizada)
            # La configuración viene como parámetro desde el servicio Java
            if not tenant_config:
                logger.info(f"🔍 Obteniendo configuración desde servicio Java para tenant: {tenant_id}")
                tenant_config = configuration_service.get_tenant_config(tenant_id)
                if not tenant_config:
                    logger.warning(f"No se encontró configuración para tenant {tenant_id} en memoria precargada para clasificación")
                    tenant_config = {}
            else:
                logger.debug(f"✅ Usando configuración optimizada enviada desde Java para tenant: {tenant_id}")

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
                logger.warning(f"[ERROR] TENANT NO ENCONTRADO: {tenant_id} - Retornando general_query")
                return {
                    "category": "general_query",
                    "confidence": 0.0,
                    "original_message": message,
                    "error": "Tenant no encontrado"
                }
            
            # Obtener contexto de la sesión para la clasificación
            session_context = session_context_service.build_context_for_ai(session_id)
            
            # Clasificar intención usando IA con contexto de sesión
            classification = await self._classify_with_ai(message, user_context, session_context, tenant_id)
            
            # 📊 IMPRIMIR RESULTADO FINAL DE CLASIFICACIÓN
            if classification and classification.get("category"):
                logger.info(f"📊 [CLASIFICACIÓN BASE] RESULTADO FINAL: {classification['category']} (confianza: {classification.get('confidence', 0):.2f})")
                logger.info(f"📊 [CLASIFICACIÓN BASE] Mensaje original: '{message[:100]}...'")
                logger.info(f"📊 [CLASIFICACIÓN BASE] Tenant: {tenant_id}")
                logger.info(f"📊 [CLASIFICACIÓN BASE] {'='*60}")
            else:
                logger.warning(f"⚠️ [CLASIFICACIÓN BASE] No se pudo clasificar el mensaje: '{message[:50]}...'")
            
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

            # 🚀 VELOCIDAD MÁXIMA: Usar solo IA para análisis de registro
            logger.info(f"🎯 USANDO IA DIRECTA REGISTRATION: '{text[:30]}...'")

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
            
            # 🚀 OPTIMIZACIÓN: Usar configuración del tenant desde memoria precargada
            # Nota: Este método necesita ser llamado con user_context para acceder a tenant_context
            logger.warning(f"⚠️ Método extract_data necesita ser optimizado para usar memoria precargada")
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
            # 🔧 OPTIMIZACIÓN: Verificación rápida de explicaciones sobre datos disponibles
            if self._is_data_explanation(data):
                return {
                    "is_valid": False,
                    "data_type": data_type,
                    "reason": "explicacion_datos",
                    "suggested_response": self._generate_explanation_response(data_type, data)
                }
            
            # 🔧 OPTIMIZACIÓN: Verificación rápida de palabras que NO son datos válidos
            if self._contains_non_data_indicators(data):
                return {
                    "is_valid": False,
                    "data_type": data_type,
                    "reason": "no_es_dato",
                    "suggested_response": self._generate_clarification_response(data_type)
                }
            
            # Validación básica por tipo
            is_valid = self._basic_validation(data, data_type)
            
            if not is_valid:
                return {
                    "is_valid": False,
                    "data_type": data_type,
                    "reason": "formato_invalido"
                }
            
            # 🔧 OPTIMIZACIÓN: Validación IA solo para casos complejos
            if data_type.lower() in ["name", "lastname", "city"] and len(data) > 3:
                ai_validation = await self._validate_with_ai(data, data_type)
                if not ai_validation:
                    return {
                        "is_valid": False,
                        "data_type": data_type,
                        "reason": "contenido_invalido"
                    }
            
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
- "la nevera" -> Bogotá
- "medallo" -> Medellín
- "la arenosa" -> Barranquilla
- "la sucursal del cielo" -> Cali
- "la ciudad bonita" -> Bucaramanga
 - "la ciudad de la eterna primavera" -> Medellín

Ejemplos válidos:
Entrada: "medellin" -> {"city": "Medellín", "state": "Antioquia", "country": "Colombia"}
Entrada: "bogota" -> {"city": "Bogotá", "state": "Cundinamarca", "country": "Colombia"}
Entrada: "soacha" -> {"city": "Soacha", "state": "Cundinamarca", "country": "Colombia"}
Entrada: "la nevera" -> {"city": "Bogotá", "state": "Cundinamarca", "country": "Colombia"}
Entrada: "vivo en la ciudad de la eterna primavera" -> {"city": "Medellín", "state": "Antioquia", "country": "Colombia"}
Entrada: "New York" -> {"city": "New York", "state": "New York", "country": "United States"}

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

        # Diccionario de apodos/alias -> (city, state, country)
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
        """Asegura que los documentos del tenant estén cargados - OPTIMIZADO"""
        try:
            # 🚀 OPTIMIZACIÓN: Verificar cache primero
            doc_info = document_context_service.get_tenant_document_info(tenant_id)
            if doc_info and doc_info.get('document_count', 0) > 0:
                logger.debug(f"[LIBROS] Documentos ya cargados para tenant {tenant_id}: {doc_info.get('document_count', 0)} docs")
                return
            
            # 🚀 OPTIMIZACIÓN: Solo cargar si no están en cache
            documentation_bucket_url = ai_config.get("documentation_bucket_url")
            
            if documentation_bucket_url:
                logger.info(f"📥 Cargando documentos para tenant {tenant_id} desde: {documentation_bucket_url}")
                # 🚀 OPTIMIZACIÓN: Usar carga asíncrona más rápida
                success = await document_context_service.load_tenant_documents(tenant_id, documentation_bucket_url)
                if success:
                    doc_info = document_context_service.get_tenant_document_info(tenant_id)
                    logger.info(f"[OK] Documentos cargados para tenant {tenant_id}: {doc_info.get('document_count', 0)} docs")
                else:
                    logger.warning(f"[ADVERTENCIA] No se pudieron cargar documentos para tenant {tenant_id}")
            else:
                logger.debug(f"[INFO] No hay bucket de documentación configurado para tenant {tenant_id}")
                
        except Exception as e:
            logger.error(f"[ERROR] Error cargando documentos para tenant {tenant_id}: {str(e)}", exc_info=True)
    
    async def _generate_ai_response(self, query: str, user_context: Dict[str, Any], 
                                  ai_config: Dict[str, Any], branding_config: Dict[str, Any], 
                                  tenant_id: str, session_id: str = None) -> str:
        """Genera respuesta usando IA con contexto de documentos"""
        
        # 🚀 OPTIMIZACIÓN: Obtener configuración del tenant desde memoria precargada
        tenant_context = user_context.get('tenant_context', {})
        tenant_config = tenant_context.get('tenant_config', {})
        
        logger.info(f"🔍 [TENANT_CONFIG] tenant_config keys: {list(tenant_config.keys()) if tenant_config else 'None'}")
        logger.info(f"🔍 [TENANT_CONFIG] tenant_config content: {tenant_config}")
        
        # [COHETE] FASE 6: Usar RAGOrchestrator si está habilitado
        if self.use_rag_orchestrator and self.rag_orchestrator:
            try:
                # 🚀 OPTIMIZACIÓN: Solo cargar documentos si no están en cache
                doc_info = document_context_service.get_tenant_document_info(tenant_id)
                if not doc_info or doc_info.get('document_count', 0) == 0:
                    await self._ensure_tenant_documents_loaded(tenant_id, ai_config)
                
                logger.info(f"[OBJETIVO] Usando RAGOrchestrator | tenant_id={tenant_id} | session_id={session_id} | query='{query[:50]}...'")
                response = await self.rag_orchestrator.process_query_simple(
                    query=query,
                    tenant_id=tenant_id,
                    user_context=user_context,
                    session_id=session_id,
                    tenant_config=tenant_config
                )
                logger.info(f"[OK] RAG respuesta generada | length={len(response)} chars")
                return response
            except Exception as e:
                logger.error(f"[ERROR] Error usando RAGOrchestrator: {str(e)}", exc_info=True)
                logger.info("[ADVERTENCIA] Fallback a lógica original (sin RAG)")
                # Continuar con lógica original como fallback
        
        # Lógica original (sin RAG)
        self._ensure_model_initialized()
        if not self.model:
            return "Lo siento, el servicio de IA no está disponible."
        
        try:
            # 🚀 OPTIMIZACIÓN: Solo cargar documentos si no están en cache
            doc_info = document_context_service.get_tenant_document_info(tenant_id)
            if not doc_info or doc_info.get('document_count', 0) == 0:
                await self._ensure_tenant_documents_loaded(tenant_id, ai_config)
            
            # Obtener contexto relevante de documentos del cliente
            relevant_context = ""
            try:
                relevant_context = await document_context_service.get_relevant_context(
                    tenant_id, query, max_results=2  # Reducido de 3 a 2 para mayor velocidad
                )
                if relevant_context:
                    logger.info(f"Contexto relevante obtenido para tenant {tenant_id}: {len(relevant_context)} caracteres")
            except Exception as e:
                logger.warning(f"Error obteniendo contexto relevante: {str(e)}")
            
            # Construir prompt con contexto de documentos
            prompt = self._build_chat_prompt(query, user_context, branding_config, relevant_context)
            
            # 🚀 OPTIMIZACIÓN: Usar configuración ultra-rápida para chat conversacional
            response_text = await self._generate_content_ultra_fast(prompt, max_tokens=200)  # Usar método ultra-rápido
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error generando respuesta con IA: {str(e)}")
            return "Lo siento, no pude procesar tu mensaje."
    
    def _detect_malicious_intent(self, message: str) -> Dict[str, Any]:
        """
        ⚠️ DEPRECADO - Ya no se usa detección por patrones/keywords
        
        La detección de malicia ahora se hace completamente por IA usando Gemini
        en el método _classify_with_ai(), que es más inteligente y puede detectar:
        - Amenazas indirectas
        - Insultos creativos
        - Lenguaje codificado
        - Contexto y sarcasmo
        - Patrones de hostilidad sutiles
        
        Este método se mantiene por compatibilidad pero ya no se llama.
        """
        # Retornar que NO es malicioso, ya que la detección real se hace por IA
        return {
            "is_malicious": False,
            "categories": [],
            "confidence": 0.0,
            "reason": "deprecated_pattern_detection"
        }

    async def _classify_with_ai(self, message: str, user_context: Dict[str, Any], session_context: str = "", tenant_id: str = None) -> Dict[str, Any]:
        """Clasifica intención usando IA con optimizaciones de velocidad"""
        
        self._ensure_model_initialized()
        
        # 🔧 DETECCIÓN COMPLETAMENTE CON IA - Sin patrones ni palabras clave
        # Todo se hace directamente con IA usando Gemini
        # La IA es más inteligente y puede detectar amenazas indirectas, insultos creativos, etc.
        
        # 🚀 USAR SOLO IA - Sin patrones ni palabras clave
        # La clasificación se hace completamente con IA
        
        if not self.model:
            return {
                "category": "saludo_apoyo", 
                "confidence": 0.0,
                "original_message": message
            }
        
        try:
            # 🚀 OPTIMIZACIÓN: Verificar caché de intenciones primero
            if tenant_id:
                cache_key = f"intent:{tenant_id}:{message.lower().strip()}"
                cached_result = self._intent_cache.get(cache_key)
                if cached_result and time.time() - cached_result.get("timestamp", 0) < 300:  # TTL 5 minutos
                    return cached_result
            
            # 🔧 DETECTAR SI HAY HISTORIAL DE CONVERSACIÓN PARA MEJORAR LA CLASIFICACIÓN
            conversation_history = ""
            if user_context and "conversation_history" in user_context:
                conversation_history = user_context["conversation_history"]
                logger.info(f"🔍 [CLASIFICACIÓN] Historial detectado ({len(conversation_history)} chars)")
            
            # 🚀 OPTIMIZACIÓN: Prompt ultra-corto para velocidad máxima con detección de malicia por IA
            if conversation_history and len(conversation_history) > 0:
                prompt = f"""Clasifica este mensaje en UNA de estas categorías:
- malicioso (SOLO insultos PERSONALES directos - NO preguntas: "eres un corrupto", "ustedes son mentirosos", amenazas, ataques a personas, groserías colombianas (hp, hpta, malparido, gonorrea, marica, guevón, etc.). Las PREGUNTAS nunca son maliciosas, incluso sobre temas sensibles)
- conocer_candidato (preguntas sobre política, propuestas, candidato, QUIÉN ES el candidato, "quién eres", "quien eres", "qué eres", "que eres")
- atencion_humano (solicitar hablar con agente humano, asesor, persona: "quiero agente humano", "asesor", "hablar con alguien")
- solicitud_funcional (app, referidos, puntos, estado, progreso, consultas funcionales, preguntas sobre QUIÉN ES el bot/chatbot: "quién eres", "quien eres", "dime quién eres")
- cita_campaña (agendar reunión)
- saludo_apoyo (hola, gracias, mensajes positivos, mensajes de apoyo o elogios hacia el candidato - SOLO si NO contiene preguntas)
- publicidad_info (pedir material)
- actualizacion_datos (corregir, cambiar o actualizar información personal: nombre, apellido, ciudad, teléfono, etc.)
- colaboracion_voluntariado (ofrecer ayudar)
- area_colaboracion_select (respondiendo con un área de colaboración específica: redes, logística, comunicaciones, territorial, jurídicos, programáticos, elecciones, call center, u otro)
- quejas (mensaje inicial sobre problema, queja, reclamo, o crítica SIN detalles)
- queja_detalle_select (mensaje con detalles específicos de problema, falla, error, mal servicio, insatisfacción, críticas al servicio/sistema)

CONTEXTO DE CONVERSACIÓN ANTERIOR:
{conversation_history}

MENSAJE ACTUAL: "{message}"

REGLAS CRÍTICAS:

1. QUEJA DETALLE_SELECT (detalles de problema):
   - Mensajes que describen problemas específicos: "esto es malo", "no funciona", "muy lento", "demorado", "deficiente", "no se presta buen servicio", "mala atención", "no sirve", "pésimo servicio"
   - Críticas al servicio/sistema: "el servicio es horrible", "todo es muy demorado", "no hay buena atención"
   - Expresiones de insatisfacción con el servicio: "esto no me parece bien", "nada funciona bien"
   - ⚠️ SIEMPRE que hay críticas al servicio (aunque no diga "queja"), es queja_detalle_select

2. QUEJAS (mensaje inicial sin detalles):
   - Solo dice "tengo una queja", "quiero hacer un reclamo", "hay un problema" SIN detalles adicionales

3. MALICIOSO (SOLO ataques directos a personas - NO preguntas):
   - ⚠️ DIFERENCIA CRÍTICA: PREGUNTA vs. ATAQUE
   - PREGUNTAS (incluso sobre temas sensibles) → NO son maliciosas:
     * Si termina con "?" o tiene estructura de pregunta ("cómo", "qué", "por qué", "sería", "podría", "sabría")
     * Si usa condicionales hipotéticos ("si digo que...", "entonces si...", "como podría saber")
     * Si busca información o aclaración ("es cierto?", "cómo saber", "podría saber")
     * → Clasificar como "conocer_candidato" o "solicitud_funcional"
   - ATAQUES DIRECTOS (afirmaciones sin pregunta) → SÍ son maliciosas:
     * Afirmaciones directas sin "?" ni estructura de pregunta
     * Insultos personales: "eres un corrupto", "ustedes son mentirosos", "tú eres un ladrón"
     * Groserías y palabras ofensivas colombianas: hp, hpta, hijueputa, malparido, gonorrea, marica, maricón, guevón, jeta, carajo, chimba, verga, paraco, chancleta, mamado, etc.
     * Cualquier insulto, grosería, palabra ofensiva o lenguaje vulgar dirigido a personas
     * Amenazas o ataques directos a personas
     * → Clasificar como "malicioso"
   - ⚠️ Críticas al servicio NO son maliciosas: "el servicio es malo" ≠ malicio

4. SALUDO_APOYO:
   - "hola", "gracias", "ok", mensajes positivos
   - Mensajes de apoyo o elogios hacia el candidato (mensajes que expresan apoyo, admiración o mensajes positivos dirigidos al candidato)
   - ⚠️ NO uses esto para críticas al servicio

Si el mensaje describe problemas con el servicio/funcionalidad/sistema/atención SIN insultar a personas = queja_detalle_select

Devuelve SOLO el nombre de la categoría:"""
            else:
                prompt = f"""Clasifica este mensaje en UNA de estas categorías:
- malicioso (SOLO insultos PERSONALES directos - NO preguntas: "eres un corrupto", "ustedes son mentirosos", amenazas, ataques a personas, groserías colombianas (hp, hpta, malparido, gonorrea, marica, guevón, etc.). Las PREGUNTAS nunca son maliciosas, incluso sobre temas sensibles)
- conocer_candidato (preguntas sobre política, propuestas, candidato, QUIÉN ES el candidato, "quién eres", "quien eres", "qué eres", "que eres")
- solicitud_funcional (app, referidos, puntos, estado, progreso, consultas funcionales, preguntas sobre QUIÉN ES el bot/chatbot: "quién eres", "quien eres", "dime quién eres")
- cita_campaña (agendar reunión)
- saludo_apoyo (hola, gracias, mensajes positivos, mensajes de apoyo o elogios hacia el candidato - SOLO si NO contiene preguntas)
- publicidad_info (pedir material)
- actualizacion_datos (corregir, cambiar o actualizar información personal: nombre, apellido, ciudad, teléfono, etc.)
- colaboracion_voluntariado (ofrecer ayudar)
- area_colaboracion_select (respondiendo con un área de colaboración específica: redes, logística, comunicaciones, territorial, jurídicos, programáticos, elecciones, call center, u otro)
- quejas (mensaje inicial sobre problema, queja, reclamo, o crítica SIN detalles)
- queja_detalle_select (mensaje con detalles específicos de problema, falla, error, mal servicio, insatisfacción, críticas al servicio/sistema)

REGLAS CRÍTICAS:

1. QUEJA DETALLE_SELECT (detalles de problema):
   - Mensajes que describen problemas específicos: "esto es malo", "no funciona", "muy lento", "demorado", "deficiente", "no se presta buen servicio", "mala atención", "no sirve", "pésimo servicio"
   - Críticas al servicio/sistema: "el servicio es horrible", "todo es muy demorado", "no hay buena atención", "aqui no se presta buen servicio"
   - Expresiones de insatisfacción con el servicio: "esto no me parece bien", "nada funciona bien"
   - ⚠️ SIEMPRE que hay críticas al servicio (aunque no diga "queja"), es queja_detalle_select

2. QUEJAS (mensaje inicial sin detalles):
   - Solo dice "tengo una queja", "quiero hacer un reclamo", "hay un problema" SIN detalles adicionales

3. MALICIOSO (SOLO ataques directos a personas - NO preguntas):
   - ⚠️ DIFERENCIA CRÍTICA: PREGUNTA vs. ATAQUE
   - PREGUNTAS (incluso sobre temas sensibles) → NO son maliciosas:
     * Si termina con "?" o tiene estructura de pregunta ("cómo", "qué", "por qué", "sería", "podría", "sabría")
     * Si usa condicionales hipotéticos ("si digo que...", "entonces si...", "como podría saber")
     * Si busca información o aclaración ("es cierto?", "cómo saber", "podría saber")
     * → Clasificar como "conocer_candidato" o "solicitud_funcional"
   - ATAQUES DIRECTOS (afirmaciones sin pregunta) → SÍ son maliciosas:
     * Afirmaciones directas sin "?" ni estructura de pregunta
     * Insultos personales: "eres un corrupto", "ustedes son mentirosos", "tú eres un ladrón"
     * Groserías y palabras ofensivas colombianas: hp, hpta, hijueputa, malparido, gonorrea, marica, maricón, guevón, jeta, carajo, chimba, verga, paraco, chancleta, mamado, etc.
     * Cualquier insulto, grosería, palabra ofensiva o lenguaje vulgar dirigido a personas
     * Amenazas o ataques directos a personas
     * → Clasificar como "malicioso"
   - ⚠️ Críticas al servicio NO son maliciosas: "el servicio es malo" ≠ malicio

4. SALUDO_APOYO:
   - "hola", "gracias", "ok", mensajes positivos
   - Mensajes de apoyo o elogios hacia el candidato (mensajes que expresan apoyo, admiración o mensajes positivos dirigidos al candidato)
   - ⚠️ NO uses esto para críticas al servicio

Si el mensaje describe problemas con el servicio/funcionalidad/sistema/atención SIN insultar a personas = queja_detalle_select

Mensaje: "{message}"

Devuelve SOLO el nombre de la categoría:"""
            
            # 🔧 OPTIMIZACIÓN: Timeout ultra-agresivo (2 segundos)
            import asyncio
            
            # 🐛 DEBUG: Log del prompt para ver qué está recibiendo la IA
            logger.info(f"🔍 [PROMPT DEBUG] Prompt completo:\n{prompt[:500]}...")
            
            try:
                response_text = await asyncio.wait_for(
                    self._generate_content_ultra_fast(prompt, max_tokens=20),
                    timeout=2.0
                )
            except asyncio.TimeoutError:
                return {
                    "category": "saludo_apoyo",
                    "confidence": 0.0,
                    "original_message": message,
                    "reason": "Timeout ultra-agresivo"
                }
            
            category = response_text.strip().lower()
            
            # 🐛 DEBUG: Log la respuesta de la IA
            logger.info(f"🔍 [IA DEBUG] Respuesta de IA: '{response_text}' -> category: '{category}'")
            
            # 🔧 MEJORADO: Extraer SOLO la categoría válida (primera palabra de la respuesta)
            # Limpiar la respuesta: tomar solo la primera palabra después de limpiar
            category_clean = category.split()[0] if category.split() else category
            
            # Lista de categorías válidas
            valid_categories = ["malicioso", "saludo_apoyo", "conocer_candidato", "solicitud_funcional", 
                               "cita_campaña", "publicidad_info", "actualizacion_datos", "colaboracion_voluntariado", "area_colaboracion_select", "quejas", "queja_detalle_select", "atencion_humano"]
            
            # Si category_clean es una categoría válida, usar esa
            if category_clean in valid_categories:
                category = category_clean
                logger.info(f"✅ Categoría limpia extraída: '{category}'")
            elif len(category) > 50:
                valid_categories = ["malicioso", "saludo_apoyo", "conocer_candidato", "solicitud_funcional", 
                                   "cita_campaña", "publicidad_info", "actualizacion_datos", "colaboracion_voluntariado", "quejas"]
                
                # Buscar si contiene alguna categoría válida
                found_category = None
                for cat in valid_categories:
                    if cat in category:
                        found_category = cat
                        break
                
                if found_category:
                    logger.info(f"✅ Categoría extraída de respuesta larga: '{found_category}'")
                    category = found_category
                else:
                    logger.warning("⚠️ RESPUESTA LARGA SIN CATEGORÍA VÁLIDA - Usando conocer_candidato")
                    category = "conocer_candidato"  # Fallback seguro, NO usar fallback inteligente
            
            # 🔧 OPTIMIZACIÓN: Detección mejorada de bloqueo por safety filters
            if category in ["hola, ¿en qué puedo ayudarte hoy?", "lo siento, no puedo procesar esa consulta en este momento. por favor, intenta reformular tu pregunta de manera más específica.", "hola", "hello", "hi"]:
                logger.warning("⚠️ GEMINI BLOQUEADO - Usando fallback inteligente")
                category = self._fallback_intent_classification(message, user_context)
            
            # Detectar si la respuesta es muy genérica (posible bloqueo)
            if len(category) < 3 or category in ["ok", "yes", "no", "si", "sí"]:
                logger.warning("⚠️ RESPUESTA MUY GENÉRICA - Posible bloqueo")
                category = self._fallback_intent_classification(message, user_context)
            
            logger.info(f"✅ INTENCIÓN: '{category}'")
            
            # Validar categoría
            valid_categories = [
                "malicioso", "cita_campaña", "saludo_apoyo", "publicidad_info", 
                "conocer_candidato", "actualizacion_datos", "solicitud_funcional", 
                "colaboracion_voluntariado", "area_colaboracion_select", "quejas", "queja_detalle_select", "lider", "atencion_humano", 
                "atencion_equipo_interno", "registration_response"
            ]
            
            if category not in valid_categories:
                logger.warning(f"[ADVERTENCIA] Intención no válida: '{category}', usando fallback inteligente")
                print(f"❌ INTENCIÓN NO VÁLIDA: '{category}' - Usando fallback inteligente")
                category = self._fallback_intent_classification(message, user_context)
            
            # 🔧 DEBUG: Log final de clasificación
            logger.info(f"[OBJETIVO] CLASIFICACIÓN FINAL: '{category}' para mensaje: '{message[:50]}...'")
            print(f"✅ CLASIFICACIÓN FINAL: '{category}' para mensaje: '{message[:50]}...'")
            
            # 🚀 OPTIMIZACIÓN: Guardar en caché para futuras consultas
            result = {
                "category": category,
                "confidence": 0.8,  # Confianza fija por simplicidad
                "original_message": message,
                "timestamp": time.time()  # TTL para limpieza automática
            }
            
            # Guardar en caché solo si tenemos tenant_id
            if tenant_id:
                cache_key = f"intent:{tenant_id}:{message.lower().strip()}"
                
                # Limpiar caché automáticamente (TTL + tamaño)
                self._cleanup_intent_cache()
                
                self._intent_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] Error clasificando con IA: {str(e)}", exc_info=True)
            return {
                "category": "general_query", 
                "confidence": 0.0,
                "original_message": message
            }
    
    def _classify_with_patterns(self, message: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Clasificación ultra-rápida usando patrones de texto"""
        message_lower = message.lower().strip()
        
        # 🎯 PRIORIDAD 1: Detectar quejas implícitas ANTES de patrones exactos
        # Palabras sobre servicio/sistema
        service_words = [
            "servicio", "sistema", "esto", "esta", "app", "aplicación",
            "atención", "atencion", "proceso", "plataforma", "soporte",
            "funcionalidad", "característica", "feature", "aqui", "aquí",
            "todo", "algo", "nada", "ninguno", "ninguna"
        ]
        
        # Indicadores de queja implícita
        queja_indicators = [
            "malo", "mala", "mal", "muy mal", "malísimo", "malísima",
            "pésimo", "pésima", "terrible", "horrible", "deplorable",
            "deficiente", "no funciona", "no sirve", "no está bien",
            "no me gusta", "no me parece", "no es bueno", "no es adecuado",
            "inadecuado", "mal servicio", "servicio malo", "muy lento",
            "no funciona bien", "no sirve bien", "problema con",
            "no se presta", "no presta", "no hay buen", "no hay buena",
            "muy demorado", "demorado", "lento", "tarda", "demasiado",
            "mala atención", "pésima atención", "horrible atención"
        ]
        
        has_queja_indicator = any(indicator in message_lower for indicator in queja_indicators)
        has_service_word = any(word in message_lower for word in service_words)
        
        if has_queja_indicator and (has_service_word or len(message_lower) > 20):
            has_personal_attack = any(word in message_lower for word in ["tú", "tu", "usted", "ustedes", "eres", "son"])
            if not has_personal_attack:
                logger.info(f"🎯 QUEJA IMPLÍCITA DETECTADA: '{message}' -> críticas al servicio")
                return {
                    "category": "queja_detalle_select",
                    "confidence": 0.85,
                    "original_message": message,
                    "reason": "Queja implícita sobre servicio"
                }
        
        # 🚫 PRIORIDAD 2: Detectar malicia (SOLO si NO es pregunta)
        # ⚠️ Verificar primero si es una pregunta - las preguntas NUNCA son maliciosas
        question_indicators = [
            "?", "cómo", "como", "qué", "que", "por qué", "porque", "cuál", "cual",
            "sería", "podría", "podria", "sabría", "sabria", "si digo", "entonces si",
            "como podría", "como podria", "cómo saber", "como saber"
        ]
        is_question = any(indicator in message_lower for indicator in question_indicators)
        
        malicious_patterns = [
            # Groserías colombianas comunes
            "hp", "hpta", "hijueputa", "hijuep", "hijue", "malparido", "malparida",
            "gonorrea", "marica", "maricon", "maricón", "chimba", "verga",
            "guevón", "guevon", "guevona", "guevonada",
            "jeta", "carajo", "mamado", "mamados", "mamada", "mamadas",
            "paraco", "paracos", "chancleta", "chancletas",
            # Insultos generales
            "corrupto", "asqueroso", "idiota", "imbécil", "bruto",
            "ladrón", "ladrones", "ratero", "rateros", "estafa", "mentiroso",
            "vete a la mierda", "que se joda", "porquería", "basura", "mierda",
            "tú eres", "ustedes son", "eres un", "son unos", "vete a", "que se muera",
            "chupa", "hijo de", "hija de", "hijos de", "hijas de"
        ]
        
        for pattern in malicious_patterns:
            if pattern in message_lower:
                if "queja" in message_lower or "reclamo" in message_lower:
                    logger.info(f"🎯 MENSAJE TIENE QUEJA: saltando detección de malicia por '{pattern}'")
                    break
                # ⚠️ Si es pregunta, NO clasificar como malicioso
                if is_question:
                    logger.info(f"🎯 MENSAJE ES PREGUNTA: saltando detección de malicia por '{pattern}' (es pregunta, no ataque)")
                    break
                logger.warning(f"🚨 MALICIA DETECTADA: '{pattern}' en mensaje")
                return {
                    "category": "malicioso",
                    "confidence": 0.9,
                    "original_message": message,
                    "reason": "Pattern-based malicious detection"
                }
        
        # Patrones de alta confianza (ordenado por especificidad - primero los más específicos)
        patterns = {
            "solicitud_funcional": [
                "quien eres", "quién eres", "dime quién", "dime quien", "que eres", "qué eres",  # 🔧 FIX: Preguntas sobre identidad del bot primero
                "puntos", "referidos", "app", "aplicación", "estado", "progreso", "como voy",
                "cuánto", "cuantos", "cuántos", "referidos tengo", "mis puntos", "mi estado",
                "mis referidos", "tengo puntos", "total referidos", "ver mis"
            ],
            "conocer_candidato": [
                "propuestas", "propuesta", "quiero conocer", "conocer", "saber de", "información sobre",
                "quien es", "qué es", "cómo funciona", "candidato", "políticas", "obras", 
                "programas", "plan de gobierno", "proyectos", "planes", "que ofrece", "que propone"
            ],
            "saludo_apoyo": [
                "hola", "hi", "hello", "buenos días", "buenas tardes", "buenas noches",
                "gracias", "ok", "okay", "sí", "si", "no", "perfecto", "excelente"
            ],
            # 🔧 FIX: NOTA: "saludo_apoyo" solo si NO contiene preguntas. Si contiene "quien eres" o similar, usar "solicitud_funcional"
            "cita_campaña": [
                "cita", "reunión", "encuentro", "agendar", "visitar", "conocer",
                "hablar", "conversar", "entrevista"
            ],
            "publicidad_info": [
                "folleto", "material", "publicidad", "difusión", "propaganda",
                "información", "brochure", "panfleto"
            ],
            "colaboracion_voluntariado": [
                "voluntario", "ayudar", "colaborar", "trabajar", "participar",
                "unirme", "apoyar", "contribuir"
            ],
            "area_colaboracion_select": [
                "redes sociales", "redes", "comunicaciones", "temas programáticos",
                "programaticos", "logistica", "logística", "temas jurídicos",
                "juridicos", "trabajo territorial", "territorial", "dia de elecciones",
                "elecciones", "call center", "callcenter", "call center",
                "otro área", "otra área", "otro"
            ],
            "quejas": [
                "queja", "reclamo", "problema", "mal servicio", "no funciona",
                "error", "falla", "defecto", "no me parece", "me parece que",
                "no está bien", "no funciona bien", "servicio adecuado",
                "inadecuado", "malo", "pésimo", "deficiente"
            ],
            "queja_detalle_select": [
                "mi queja es", "mi reclamo es", "el problema es", "lo que pasó",
                "lo que sucedió", "detalle", "detalles", "explicar",
                "no me parece", "me parece que no", "mal servicio", "muy lento",
                "no funciona", "está mal", "inadecuado", "no se presta", "no presta",
                "demorado", "muy demorado", "lento", "tarda", "demasiado",
                "no hay buen servicio", "no hay buena atención", "mala atención"
            ],
            "registration_response": [
                "me llamo", "mi nombre es", "soy", "vivo en", "mi ciudad es",
                "mi teléfono es", "mi email es"
            ]
        }
        
        # 🎯 DETECCIÓN ESPECIAL: Queja completa en un solo mensaje
        # Si el mensaje contiene "tengo una queja" Y además detalles adicionales, es queja_detalle_select
        if "tengo una queja" in message_lower or "tengo queja" in message_lower:
            # Verificar si hay detalles adicionales (más de 20 caracteres adicionales)
            queja_pos = message_lower.find("queja")
            if queja_pos != -1 and len(message_lower) > queja_pos + 35:  # Más de 35 chars después de "queja" = hay detalles
                logger.info(f"🎯 QUEJA COMPLETA DETECTADA: '{message}' tiene queja + detalles")
                return {
                    "category": "queja_detalle_select",
                    "confidence": 0.95,
                    "original_message": message,
                    "reason": "Queja completa en un solo mensaje"
                }
            else:
                # Solo dice "tengo una queja" sin detalles
                logger.info(f"🎯 QUEJA INICIAL DETECTADA: '{message}'")
                return {
                    "category": "quejas",
                    "confidence": 0.9,
                    "original_message": message,
                    "reason": "Mensaje inicial de queja"
                }
        
        # Buscar coincidencias exactas primero
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern in message_lower:
                    logger.info(f"🎯 PATTERN MATCH: '{pattern}' en '{message}' -> {category}")
                    return {
                        "category": category,
                        "confidence": 0.9,
                        "original_message": message,
                        "reason": f"Pattern match: {pattern}"
                    }
        
        # Buscar coincidencias parciales
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                pattern_words = pattern.split()
                if any(word in message_lower for word in pattern_words):
                    return {
                        "category": category,
                        "confidence": 0.7,
                        "original_message": message,
                        "reason": f"Partial pattern match: {pattern}"
                    }
        
        # Si no hay coincidencias, usar fallback inteligente
        return {
            "category": "conocer_candidato",  # Fallback más común
            "confidence": 0.3,
            "original_message": message,
            "reason": "No pattern match, using fallback"
        }
    
    def _cleanup_intent_cache(self):
        """Limpia automáticamente el caché de intenciones (TTL + tamaño)"""
        current_time = time.time()
        
        # Limpiar por TTL (5 minutos)
        expired_keys = []
        for key, value in self._intent_cache.items():
            if current_time - value.get("timestamp", 0) > 300:  # 5 minutos
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._intent_cache[key]
        
        # Limpiar por tamaño si es necesario
        if len(self._intent_cache) >= self._intent_cache_max_size:
            # Eliminar el 20% más antiguo
            sorted_items = sorted(self._intent_cache.items(), key=lambda x: x[1].get("timestamp", 0))
            keys_to_remove = [key for key, _ in sorted_items[:self._intent_cache_max_size // 5]]
            for key in keys_to_remove:
                del self._intent_cache[key]
    
    def _fallback_intent_classification(self, message: str, context: Dict[str, Any] = None) -> str:
        """
        Clasificación de fallback cuando Gemini está bloqueado por safety filters
        Solo para casos muy específicos y obvios - confiar en Gemini para el resto
        
        Args:
            message: Mensaje a clasificar
            context: Contexto adicional (ej: estado del usuario, tipo de conversación)
            
        Returns:
            Categoría detectada
        """
        # 🔧 FIX: Sin patrones ni palabras clave - devuelve fallback genérico
        # La IA debería haber clasificado, pero si falló, usar solicitud_funcional como último recurso
        logger.warning(f"⚠️ Usando fallback genérico (sin patrones) para: '{message[:50]}...'")
        return "solicitud_funcional"  # Fallback genérico sin usar palabras clave
    
    def _looks_like_data_explanation(self, message: str) -> bool:
        """
        Detecta si un mensaje es una explicación sobre qué datos puede proporcionar el usuario
        
        Args:
            message: Mensaje a analizar
            
        Returns:
            True si parece ser una explicación sobre datos disponibles
        """
        message_lower = message.lower().strip()
        
        # Patrones que indican explicaciones sobre datos disponibles
        explanation_patterns = [
            "puedo solo", "solo puedo", "solo tengo", "solo dispongo",
            "solo me permite", "solo me deja", "solo me da",
            "un nombre y un apellido", "nombre y apellido", "solo nombre", "solo apellido",
            "no tengo más", "no tengo otros", "no tengo más datos", "no tengo más información",
            "solo eso", "nada más", "eso es todo", "eso es lo que tengo",
            "me permite solo", "me deja solo", "me da solo", "me da únicamente"
        ]
        
        # Verificar si contiene alguno de los patrones
        for pattern in explanation_patterns:
            if pattern in message_lower:
                return True
        
        # Verificar si contiene palabras clave de datos + palabras de limitación
        data_words = ["nombre", "apellido", "ciudad", "dirección", "teléfono", "email", "datos", "información"]
        limitation_words = ["solo", "únicamente", "solamente", "nada más", "eso es todo", "no tengo más"]
        
        has_data_word = any(word in message_lower for word in data_words)
        has_limitation_word = any(word in message_lower for word in limitation_words)
        
        if has_data_word and has_limitation_word:
            return True
        
        return False
    
    def _is_data_explanation(self, message: str) -> bool:
        """
        Detecta si un mensaje es una explicación sobre qué datos puede proporcionar el usuario
        
        Args:
            message: Mensaje a analizar
            
        Returns:
            True si es una explicación sobre datos disponibles
        """
        return self._looks_like_data_explanation(message)
    
    def _contains_non_data_indicators(self, message: str) -> bool:
        """
        Detecta si un mensaje contiene palabras que indican que NO es un dato válido
        
        Args:
            message: Mensaje a analizar
            
        Returns:
            True si contiene indicadores de que no es un dato válido
        """
        message_lower = message.lower().strip()
        
        # Palabras que indican que NO es un dato válido
        non_data_indicators = [
            "ok", "okey", "okay", "listo", "bien", "si", "no", "tal vez",
            "hola", "buenos", "buenas", "saludos", "gracias", "por favor",
            "disculpa", "perdon", "lo siento", "entendido", "comprendo",
            "vale", "perfecto", "excelente", "claro", "obvio", "seguro",
            "por supuesto", "naturalmente", "exacto", "correcto", "asi es",
            "como", "que", "cual", "donde", "cuando", "por que", "para que",
            "quiero", "necesito", "me gustaria", "puedo", "soy", "tengo",
            "no entiendo", "no se", "no tengo", "no puedo", "no me deja",
            "problema", "error", "falla", "no funciona", "ayuda"
        ]
        
        return any(indicator in message_lower for indicator in non_data_indicators)
    
    def _generate_explanation_response(self, data_type: str, message: str) -> str:
        """
        Genera una respuesta inteligente cuando el usuario explica qué datos puede proporcionar
        
        Args:
            data_type: Tipo de dato esperado
            message: Mensaje del usuario
            
        Returns:
            Respuesta generada
        """
        if data_type.lower() == "name":
            return "Entiendo perfectamente. No te preocupes, puedes proporcionar solo el nombre que tengas disponible. ¿Cuál es tu nombre?"
        elif data_type.lower() == "lastname":
            return "Perfecto, entiendo que tienes limitaciones con los datos. ¿Cuál es tu apellido?"
        elif data_type.lower() == "city":
            return "No hay problema, entiendo tu situación. ¿En qué ciudad vives?"
        else:
            return "Entiendo tu situación. Por favor, proporciona la información que tengas disponible."
    
    def _generate_clarification_response(self, data_type: str) -> str:
        """
        Genera una respuesta para aclarar qué tipo de dato se espera
        
        Args:
            data_type: Tipo de dato esperado
            
        Returns:
            Respuesta de aclaración
        """
        if data_type.lower() == "name":
            return "Por favor, proporciona tu nombre completo. Por ejemplo: 'Juan Carlos' o 'María'"
        elif data_type.lower() == "lastname":
            return "Por favor, proporciona tu apellido. Por ejemplo: 'García' o 'Rodríguez'"
        elif data_type.lower() == "city":
            return "Por favor, proporciona el nombre de tu ciudad. Por ejemplo: 'Bogotá' o 'Medellín'"
        else:
            return "Por favor, proporciona la información solicitada."
    
    def _analyze_registration_intent(self, message: str, data_type: str) -> bool:
        """
        Análisis ultra-rápido de intención de registro
        
        Args:
            message: Mensaje a analizar
            data_type: Tipo de dato esperado ("name", "lastname", "city")
            
        Returns:
            True si el mensaje tiene la INTENCIÓN de proporcionar datos de registro
        """
        message_lower = message.lower().strip()
        
        # 🔧 OPTIMIZACIÓN: Detección ultra-rápida de palabras comunes que NO son datos
        non_data_words = ["ok", "listo", "bien", "si", "no", "hola", "gracias", "vale", "claro", "como", "que", "cual"]
        if any(word in message_lower for word in non_data_words):
            return False
        
        # 🔧 OPTIMIZACIÓN: Detección ultra-rápida de explicaciones sobre datos
        if self._looks_like_data_explanation(message):
            return True
        
        # 🔧 OPTIMIZACIÓN: Detección ultra-rápida de nombres comunes
        if data_type == "name":
            common_names = ["santiago", "juan", "maria", "carlos", "ana", "luis", "pedro", "sofia", "diego", "camila"]
            if any(name in message_lower for name in common_names):
                return True
        
        # 🔧 OPTIMIZACIÓN: Detección ultra-rápida de ciudades comunes
        if data_type == "city":
            common_cities = ["bogotá", "medellín", "cali", "barranquilla", "cartagena", "bucaramanga", "pereira", "santa marta"]
            if any(city in message_lower for city in common_cities):
                return True
        
        # 🔧 OPTIMIZACIÓN: Si es una frase corta sin palabras comunes, probablemente es un dato
        words = message.split()
        if len(words) <= 3 and "?" not in message:
            return True
        
        return False
    
    # def _looks_like_name_response(self, message: str) -> bool:
    #     """
    #     Detecta si un mensaje parece ser una respuesta de nombre
    #     MÉTODO NO SE USA - COMENTADO
    #     """
    #     message_lower = message.lower().strip()
    #     
    #     # Palabras que indican que NO es un nombre (lista expandida)
    #     not_name_indicators = [
    #         "hola", "buenos", "buenas", "saludos", "como", "que", "cual", 
    #         "donde", "cuando", "por que", "quiero", "necesito", "me gustaria",
    #         "puedo", "soy", "mi nombre es", "me llamo", "soy de", "vivo en",
    #         "ok", "okey", "okay", "listo", "bien", "si", "no", "tal vez",
    #         "gracias", "por favor", "disculpa", "perdon", "lo siento",
    #         "entendido", "comprendo", "vale", "perfecto", "excelente",
    #         "claro", "obvio", "seguro", "por supuesto", "naturalmente"
    #     ]
    #     
    #     if any(indicator in message_lower for indicator in not_name_indicators):
    #         return False
    #     
    #     # Si contiene palabras como "nombre", "apellido", "solo" - probablemente es una respuesta de datos
    #     data_indicators = [
    #         "nombre", "apellido", "solo", "un", "una", "dos", "tres", "varias"
    #     ]
    #     
    #     if any(indicator in message_lower for indicator in data_indicators):
    #         return True
    #     
    #     # Si es una frase corta (1-4 palabras) sin signos de interrogación Y no contiene palabras comunes
    #     words = message.split()
    #     if len(words) <= 4 and "?" not in message:
    #         # Verificar que no sean palabras muy comunes
    #         common_words = ["ok", "listo", "bien", "si", "no", "hola", "gracias", "vale", "claro"]
    #         if not any(word.lower() in common_words for word in words):
    #             return True
    #     
    #     return False
    
    # def _looks_like_lastname_response(self, message: str) -> bool:
    #     """
    #     Detecta si un mensaje parece ser una respuesta de apellido
    #     MÉTODO NO SE USA - COMENTADO
    #     """
    #     message_lower = message.lower().strip()
    #     
    #     # Palabras que indican que NO es un apellido (lista expandida)
    #     not_lastname_indicators = [
    #         "hola", "buenos", "buenas", "saludos", "como", "que", "cual", 
    #         "donde", "cuando", "por que", "quiero", "necesito", "me gustaria",
    #         "puedo", "soy", "mi apellido es", "me apellido", "soy de", "vivo en",
    #         "ok", "okey", "okay", "listo", "bien", "si", "no", "tal vez",
    #         "gracias", "por favor", "disculpa", "perdon", "lo siento",
    #         "entendido", "comprendo", "vale", "perfecto", "excelente",
    #         "claro", "obvio", "seguro", "por supuesto", "naturalmente"
    #     ]
    #     
    #     if any(indicator in message_lower for indicator in not_lastname_indicators):
    #         return False
    #     
    #     # Si contiene palabras como "apellido", "solo" - probablemente es una respuesta de datos
    #     data_indicators = [
    #         "apellido", "solo", "un", "una", "dos", "tres", "varias"
    #     ]
    #     
    #     if any(indicator in message_lower for indicator in data_indicators):
    #         return True
    #     
    #     # Si es una frase corta (1-3 palabras) sin signos de interrogación Y no contiene palabras comunes
    #     words = message.split()
    #     if len(words) <= 3 and "?" not in message:
    #         # Verificar que no sean palabras muy comunes
    #         common_words = ["ok", "listo", "bien", "si", "no", "hola", "gracias", "vale", "claro"]
    #         if not any(word.lower() in common_words for word in words):
    #             return True
    #     
    #     return False
    
    # def _looks_like_city_response(self, message: str) -> bool:
    #     """
    #     Detecta si un mensaje parece ser una respuesta de ciudad
    #     MÉTODO NO SE USA - COMENTADO
    #     """
    #     message_lower = message.lower().strip()
    #     
    #     # Palabras que indican que NO es una ciudad (lista expandida)
    #     not_city_indicators = [
    #         "hola", "buenos", "buenas", "saludos", "como", "que", "cual", 
    #         "donde", "cuando", "por que", "quiero", "necesito", "me gustaria",
    #         "puedo", "soy", "mi ciudad es", "vivo en", "soy de",
    #         "ok", "okey", "okay", "listo", "bien", "si", "no", "tal vez",
    #         "gracias", "por favor", "disculpa", "perdon", "lo siento",
    #         "entendido", "comprendo", "vale", "perfecto", "excelente",
    #         "claro", "obvio", "seguro", "por supuesto", "naturalmente"
    #     ]
    #     
    #     if any(indicator in message_lower for indicator in not_city_indicators):
    #         return False
    #     
    #     # Si contiene palabras como "ciudad", "vivo", "soy de" - probablemente es una respuesta de datos
    #     data_indicators = [
    #         "ciudad", "vivo", "soy de", "estoy en", "resido en", "habito en"
    #     ]
    #     
    #     if any(indicator in message_lower for indicator in data_indicators):
    #         return True
    #     
    #     # Si es una frase corta (1-3 palabras) sin signos de interrogación
    #     words = message.split()
    #     if len(words) <= 3 and "?" not in message:
    #         return True
    #     
    #     return False
    
    # def _looks_like_data_explanation(self, message: str) -> bool:
    #     """
    #     Detecta si un mensaje es una explicación sobre qué datos puede proporcionar el usuario
    #     MÉTODO DUPLICADO - NO SE USA
    #     """
    #     message_lower = message.lower().strip()
    #     
    #     # Patrones que indican explicaciones sobre datos disponibles
    #     explanation_patterns = [
    #         "puedo solo", "solo puedo", "solo tengo", "solo tengo", "solo dispongo",
    #         "solo me permite", "solo me deja", "solo me da", "solo me da",
    #         "un nombre y un apellido", "nombre y apellido", "solo nombre", "solo apellido",
    #         "no tengo más", "no tengo otros", "no tengo más datos", "no tengo más información",
    #         "solo eso", "nada más", "eso es todo", "eso es lo que tengo",
    #         "me permite solo", "me deja solo", "me da solo", "me da únicamente"
    #     ]
    #     
    #     # Verificar si contiene alguno de los patrones
    #     for pattern in explanation_patterns:
    #         if pattern in message_lower:
    #             return True
    #     
    #     # Verificar si contiene palabras clave de datos + palabras de limitación
    #     data_words = ["nombre", "apellido", "ciudad", "dirección", "teléfono", "email", "datos", "información"]
    #     limitation_words = ["solo", "únicamente", "solamente", "nada más", "eso es todo", "no tengo más"]
    #     
    #     has_data_word = any(word in message_lower for word in data_words)
    #     has_limitation_word = any(word in message_lower for word in limitation_words)
    #     
    #     if has_data_word and has_limitation_word:
    #         return True
    #     
    #     return False
    
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
            
            # [COHETE] FASE 2: Usar configuración optimizada para extracción de datos
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
- Si el usuario explica limitaciones (ej: "solo puedo dar nombre y apellido"), clasifica como "info"
- Considera el contexto de la conversación anterior
- Sé inteligente para entender frases naturales como "listo, mi nombre es Pepito Perez"
- PRIORIDAD: Si el estado es WAITING_CITY y el mensaje contiene información de ubicación, clasifica como "city"
- PRIORIDAD: Si el estado es WAITING_LASTNAME y el mensaje contiene apellidos, clasifica como "lastname"

EJEMPLOS:
- "listo, mi nombre es Pepito Perez Mora" -> type: "name", value: "Pepito Perez Mora"
- "ok, es Pepito Perez" -> type: "name", value: "Pepito Perez"
- "Te lo escribi antes Campos P" -> type: "lastname", value: "Campos P"
- "Si ese es mi apellido" -> type: "lastname", value: "Campos P" (si se mencionó antes)
- "vivo en Bogotá" -> type: "city", value: "Bogotá"
- "vivo en la capital" -> type: "city", value: "Bogotá" (si es Colombia)
- "solo puedo dar nombre y apellido" -> type: "info", value: null
- "no tengo ciudad" -> type: "info", value: null
- "¿cómo funciona esto?" -> type: "info", value: null
- "soy de Medellín" -> type: "city", value: "Medellín"
- "estoy en Cali" -> type: "city", value: "Cali"
- "resido en Barranquilla" -> type: "city", value: "Barranquilla"
- "?Cómo funciona esto?" -> type: "info", value: null
- "Pepito" -> type: "name", value: "Pepito"

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

    # async def _analyze_city_with_ai(self, text: str) -> Dict[str, Any]:
    #     """Usa IA para analizar si un texto contiene información de ciudad y extraerla"""
    #     # MÉTODO NO SE USA - COMENTADO
    #     self._ensure_model_initialized()
    #     if not self.model:
    #         return {"is_city": False, "extracted_city": None, "confidence": 0.0}
    #     
    #     try:
    #         prompt = f"""
    #         Analiza el siguiente texto y determina si contiene información sobre una ciudad o ubicación.
    #         
    #         Texto: "{text}"
    #         
    #         Instrucciones:
    #         1. Si el texto menciona una ciudad, país, o ubicación geográfica, responde "SI"
    #         2. Si el texto NO menciona ubicación geográfica, responde "NO"
    #         3. Si es "SI", extrae la información completa de ubicación
    #         4. Si menciona país Y ciudad, extrae la frase completa
    #         5. Si solo menciona ciudad, extrae solo la ciudad
    #         6. IMPORTANTE: Para frases como "en españa, en madrid", extrae la ciudad específica (madrid)
    #         7. Para frases como "vivo en españa, en madrid", extrae "madrid" como ciudad
    #         
    #         Ejemplos:
    #         - "vivo en españa, en madrid" -> SI, ciudad: "madrid"
    #         - "soy de bogotá" -> SI, ciudad: "bogotá"
    #         - "estoy en medellín" -> SI, ciudad: "medellín"
    #         - "en españa, madrid" -> SI, ciudad: "madrid"
    #         - "en madrid, españa" -> SI, ciudad: "madrid"
    #         - "hola" -> NO
    #         - "mi nombre es juan" -> NO
    #         
    #         Responde en formato: SI|ciudad o NO
    #         """
    #         
    #         # [COHETE] FASE 2: Usar configuración optimizada para normalización de ubicaciones
    #         response_text = await self._generate_content(prompt, task_type="location_normalization")
    #         result = response_text.strip()
    #         
    #         if result.startswith("SI|"):
    #             city = result.split("|", 1)[1].strip()
    #             logger.info(f"IA detectó ciudad: '{city}' en texto: '{text}'")
    #             return {
    #                 "is_city": True,
    #                 "extracted_city": city,
    #                 "confidence": 0.8
    #             }
    #         else:
    #             logger.info(f"IA no detectó ciudad en texto: '{text}'")
    #             return {
    #                 "is_city": False,
    #                 "extracted_city": None,
    #                 "confidence": 0.0
    #             }
    #             
    #     except Exception as e:
    #         logger.error(f"Error analizando ciudad con IA: {str(e)}")
    #         return {"is_city": False, "extracted_city": None, "confidence": 0.0}

    async def _validate_with_ai(self, data: str, data_type: str) -> bool:
        """Validación rápida con IA - optimizada para velocidad"""
        self._ensure_model_initialized()
        if not self.model:
            return True
        
        try:
            # Prompt optimizado y conciso
            prompt = f"¿Es '{data}' un {data_type} válido? Responde: SI o NO"
            
            response_text = await self._generate_content(prompt, task_type="data_validation")
            return response_text.strip().upper() == "SI"
            
        except Exception as e:
            logger.error(f"Error en validación IA: {str(e)}")
            return True
    
    def _build_chat_prompt(self, query: str, user_context: Dict[str, Any], 
                          branding_config: Dict[str, Any], relevant_context: str = "") -> str:
        """Construye el prompt para chat"""
        contact_name = branding_config.get("contactName", "el candidato")
        welcome_message = branding_config.get("welcomeMessage", "!Hola! ?En qué puedo ayudarte?")
        
        context_info = ""
        if user_context.get("user_name"):
            context_info += f"El usuario se llama {user_context['user_name']}. "
        if user_context.get("user_city"):
            context_info += f"Vive en {user_context['user_city']}. "
        if user_context.get("user_country"):
            context_info += f"País: {user_context['user_country']}. "
        if user_context.get("user_state"):
            context_info += f"Estado actual: {user_context['user_state']}. "
        if user_context.get("user_phone"):
            context_info += f"Teléfono: {user_context['user_phone']}. "
        if user_context.get("conversation_count"):
            context_info += f"Es su conversación #{user_context['conversation_count']}. "
        
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
            Asistente virtual para la campaña política de {contact_name}.
            
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
            Asistente virtual para la campaña política de {contact_name}.
            
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
            - Los usuarios pueden preguntar "?Cómo voy?" para ver su progreso
            - Para invitar personas: "mandame el link" o "dame mi código"
            
            CONTEXTO COMPLETO DEL USUARIO: {context_info}{document_context_section}
            
            Mensaje del usuario: "{query}"
            
            INSTRUCCIONES PERSONALIZADAS:
            1. **PERSONALIZA** tu respuesta usando el nombre del usuario si está disponible
            2. **MENCIÓN** su ciudad si es relevante para la respuesta
            3. Responde de manera amigable, motivadora y natural
            4. Si el usuario está en proceso de registro, ayúdale a completarlo
            5. Si tiene preguntas sobre la campaña, responde con información relevante y oportunidades de participación
            6. Usa la información específica de la campaña cuando sea apropiado
            7. Usa emojis apropiados y un tono positivo
            8. Mantén la respuesta concisa, máximo 999 caracteres
            
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
- "vengo referido por TESTCODE" -> TESTCODE
- "mi código es ABC12345" -> ABC12345  
- "vengo referido por mi amigo" -> NO
- "hola REFERIDO" -> NO
"""

            response_text = await self._generate_content(prompt)
            logger.info(f"🔍 DEBUG: Respuesta cruda de IA para detección de código: '{response_text}'")
            
            detected_code = response_text.strip().upper()
            logger.info(f"🔍 DEBUG: detected_code después de strip y upper: '{detected_code}'")
            
            # Validar que el código tiene exactamente 8 caracteres alfanuméricos
            if detected_code != "NO" and len(detected_code) == 8 and detected_code.isalnum():
                logger.info(f"✅ Código de referido detectado por IA: {detected_code}")
                return {
                    "code": detected_code,
                    "reason": "Código detectado exitosamente",
                    "original_message": message
                }
            else:
                logger.info(f"❌ No se detectó código de referido válido. detected_code: '{detected_code}', len: {len(detected_code)}, isalnum: {detected_code.isalnum() if detected_code else False}")
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
            
            # Comportamiento malicioso detectado por IA (Gemini)
            # Ya no usamos análisis por patrones, ahora la IA detecta directamente
            behavior_type = "intención maliciosa detectada por IA"
            
            logger.warning(f"🚨 {behavior_type.upper()} - Usuario: {user_id}, Tenant: {tenant_id}, Confianza: {confidence:.2f}")
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
                logger.info(f"[OK] Usuario {user_id} bloqueado exitosamente en WATI y base de datos")
            else:
                logger.error(f"[ERROR] Error bloqueando usuario {user_id}: {notification_result.get('error')}")
                logger.error(f"[ERROR] Detalles del error: {notification_result}")
            
            # No responder nada cuando es malicioso, solo bloquear silenciosamente
            return ""
            
        except Exception as e:
            logger.error(f"Error manejando comportamiento malicioso: {str(e)}")
            return "Lo siento, no puedo procesar tu mensaje en este momento."
    
    async def _handle_appointment_request_with_context(self, branding_config: Dict[str, Any], 
                                               tenant_config: Dict[str, Any], session_context: str = "") -> str:
        """Maneja solicitudes de citas con contexto de sesión"""
        contact_name = branding_config.get("contactName", branding_config.get("contact_name", "el candidato"))
        
        # Obtener link de Calendly desde DB del tenant
        calendly_link = tenant_config.get("link_calendly", "") if tenant_config else ""
        
        # Generar respuesta con IA
        if calendly_link:
            logger.info(f"✅ Link de Calendly disponible: {calendly_link}")
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
        else:
            logger.info(f"⚠️ Link de Calendly NO disponible")
            prompt = f"""Genera una respuesta natural y amigable en español para un chatbot de campaña política. El usuario quiere agendar una cita pero el sistema aún no está disponible.

Información:
- Nombre del candidato: {contact_name}

Indica que el sistema de citas estará disponible muy pronto."""
        
        try:
            # Generar respuesta con IA usando el modelo
            if self.model:
                response_obj = self.model.generate_content(prompt)
                response = response_obj.text.strip()
                
                # Post-procesamiento: limpiar enlaces truncados o corruptos
                import re
                # Remover patrones como [Link de Calendly: https://...] si la IA los incluyera
                response = re.sub(r'\[Link de Calendly:?\s*', '', response)
                response = re.sub(r'\]\s*', '', response)
                
                # Remover enlaces truncados (que terminan con ...)
                if calendly_link:
                    response = re.sub(rf'{re.escape(calendly_link[:20])}\.\.\.', '', response)
                    response = re.sub(r'https?://[^\s]+\.\.\.', '', response)
                    
                    # Verificar si la respuesta incluye el enlace completo
                    has_full_link = calendly_link in response
                    
                    # Si hay duplicados del link, consolidar
                    response = re.sub(rf'{re.escape(calendly_link)}\s+{re.escape(calendly_link)}', calendly_link, response)
                    
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
                        logger.warning(f"⚠️ La IA no incluyó el enlace. Agregándolo ahora...")
                        # Si no incluye el enlace, agregarlo al final
                        if not response.endswith('.') and not response.endswith(':'):
                            response += "."
                        response += f"\n\n{calendly_link}"
                else:
                    # Limpiar espacios múltiples
                    response = re.sub(r'\s+', ' ', response).strip()
                
                if not response or len(response.strip()) < 10:
                    # Fallback
                    if calendly_link:
                        return f"¡Perfecto! Puedes reservar tu cita aquí: {calendly_link}"
                    else:
                        return f"El sistema de citas estará disponible muy pronto. ¿Te gustaría que te notifique cuando esté listo?"
                return response
            else:
                # Si no hay modelo, usar fallback
                if calendly_link:
                    return f"¡Perfecto! Puedes reservar tu cita aquí: {calendly_link}"
                else:
                    return "El sistema de citas estará disponible muy pronto."
        except Exception as e:
            logger.error(f"Error generando respuesta con IA: {e}")
            # Fallback final
            if calendly_link:
                return f"¡Perfecto! Puedes reservar tu cita aquí: {calendly_link}"
            else:
                return "El sistema de citas estará disponible muy pronto."
    
    async def _handle_advertising_info_with_context(self, branding_config: Dict[str, Any], 
                                               tenant_config: Dict[str, Any], session_context: str = "") -> str:
        """Maneja solicitudes de información publicitaria con contexto de sesión"""
        contact_name = branding_config.get("contactName", branding_config.get("contact_name", "el candidato"))
        
        # Obtener link de Forms desde DB del tenant
        forms_link = tenant_config.get("link_forms", "") if tenant_config else ""
        
        # Generar respuesta con IA
        if forms_link:
            logger.info(f"✅ Link de Forms disponible: {forms_link}")
            prompt = f"""Genera una respuesta natural y amigable en español para un chatbot de campaña política. El usuario quiere solicitar materiales publicitarios o información de campaña.

Información:
- Nombre del candidato: {contact_name}
- Link de Formularios: {forms_link}

Genera una respuesta breve y conversacional que incluya el link del formulario para solicitar materiales."""
        else:
            logger.info(f"⚠️ Link de Forms NO disponible")
            prompt = f"""Genera una respuesta natural y amigable en español para un chatbot de campaña política. El usuario quiere solicitar materiales publicitarios pero el sistema aún no está disponible.

Información:
- Nombre del candidato: {contact_name}

Indica que el sistema para solicitar materiales estará disponible muy pronto."""
        
        try:
            # Generar respuesta con IA usando el modelo
            if self.model:
                response_obj = self.model.generate_content(prompt)
                response = response_obj.text.strip()
                
                # Verificar si la respuesta incluye el enlace
                if forms_link and forms_link not in response:
                    logger.warning(f"⚠️ La IA no incluyó el enlace. Agregándolo ahora...")
                    # Si no incluye el enlace, agregarlo al final
                    if not response.endswith('.'):
                        response += "."
                    response += f"\n\nPuedes solicitar materiales publicitarios aquí: {forms_link}"
                
                if not response or len(response.strip()) < 10:
                    # Fallback
                    if forms_link:
                        return f"¡Perfecto! Puedes solicitar materiales publicitarios aquí: {forms_link}"
                    else:
                        return f"El sistema para solicitar materiales estará disponible muy pronto. ¿Te gustaría que te notifique cuando esté listo?"
                return response
            else:
                # Si no hay modelo, usar fallback
                if forms_link:
                    return f"¡Perfecto! Puedes solicitar materiales publicitarios aquí: {forms_link}"
                else:
                    return "El sistema para solicitar materiales estará disponible muy pronto."
        except Exception as e:
            logger.error(f"Error generando respuesta con IA: {e}")
            # Fallback final
            if forms_link:
                return f"¡Perfecto! Puedes solicitar materiales publicitarios aquí: {forms_link}"
            else:
                return "El sistema para solicitar materiales estará disponible muy pronto."
    
    async def _handle_human_assistance_request(self, branding_config: Dict[str, Any], 
                                               tenant_config: Dict[str, Any],
                                               user_context: Dict[str, Any],
                                               session_context: str = "") -> str:
        """Maneja solicitudes de atención humana - redirecciona a un agente
        
        Returns:
            str: Mensaje indicando que será redirigido a un agente
        """
        contact_name = branding_config.get("contactName", branding_config.get("contact_name", "el equipo"))
        
        try:
            logger.info("🤝 [ATENCIÓN HUMANA] Procesando solicitud de atención humana")
            
            # Mensaje de confirmación
            response = f"Perfecto, voy a conectarte con un agente humano para ayudarte mejor. Un momento por favor."
            
            # Indizar en user_context que se debe asignar a un team
            user_context["_needs_human_assistance"] = True
            user_context["_human_assistance_message"] = response
            
            logger.info("✅ [ATENCIÓN HUMANA] Solicitud marcada para redirección a equipo humano")
            
            return response
            
        except Exception as e:
            logger.error(f"Error manejando solicitud de atención humana: {e}")
            return "Entendido, voy a conectarte con un agente humano. Un momento por favor."
    
    async def _handle_data_update_request(self, query: str, user_context: Dict[str, Any], 
                                         session_context: str = "", tenant_id: str = None) -> tuple:
        """Maneja solicitudes de actualización de datos dinámica
        
        Returns:
            tuple: (response_message, update_data_dict)
        """
        import json
        import re
        
        try:
            self._ensure_model_initialized()
            
            if not self.model:
                return ("Por favor, proporciona la información que deseas actualizar. Ejemplo: 'Quiero actualizar mi nombre a Juan y mi ciudad a Medellín'", None)
            
            # 🔍 VERIFICAR SI ESTÁ EN MODO "ESPERANDO DATOS"
            query_lower = query.lower().strip()
            is_waiting_for_data = any([
                "actualizar" in query_lower and "datos" in query_lower,
                "actualizar" in query_lower and "información" in query_lower,
                "cambiar" in query_lower and "datos" in query_lower,
                "modificar" in query_lower and "datos" in query_lower,
                "corregir" in query_lower and "datos" in query_lower
            ]) and not any([word in query_lower for word in ["nombre", "apellido", "ciudad", "ciudad", "city", "name", "lastname", "teléfono", "phone"]])
            
            # Si solo dice que quiere actualizar pero no dice qué, inicializar estado
            if is_waiting_for_data:
                logger.info("⚠️ Usuario quiere actualizar datos pero no especificó cuáles")
                message = "Perfecto, puedo ayudarte a actualizar tus datos. Por favor, indícame qué información deseas cambiar. Por ejemplo:\n\n• Nombre\n• Apellido\n• Ciudad\n• Teléfono\n\nO puedes escribir directamente: 'Quiero cambiar mi nombre a Juan'"
                
                # Guardar en sesión que estamos esperando datos
                user_context["pending_data_update"] = True
                return (message, None)
            
            # Extraer información de actualización usando IA
            prompt = """Analiza el siguiente mensaje y extrae qué datos quiere actualizar el usuario.
            
Mensaje del usuario: """ + f'"{query}"' + """

Contexto de conversación anterior:
{session_context if session_context else "No hay contexto previo"}

INSTRUCCIONES:
1. Identifica TODOS los campos que el usuario quiere actualizar (nombre, apellido, ciudad, teléfono, etc.)
2. Para cada campo, identifica el NUEVO valor que el usuario quiere
3. Si el usuario quiere actualizar "todo" o "todos", identificar todos los campos mencionados en el contexto
4. **IMPORTANTE**: Si dice "mi nombre" o solo da un nombre sin contexto, determinar si es nombre o apellido basándote en:
   - Si dice "mi nombre es X" o "mi nombre es X Y" y solo hay una palabra después de "es", es NOMBRE
   - Si dice "mi apellido es X", es APELLIDO
   - Si dice solo "Juan" sin contexto, pero la palabra tiene vocales comunes de apellidos colombianos (García, Rodríguez, Pérez, etc.), considerar como APELLIDO
   - Si la palabra empieza con mayúscula y tiene estructura típica de nombre hispano (Juan, María, Carlos, etc.), es NOMBRE
   - Si hay duda, usar el contexto de la conversación para determinar
5. Devuelve SOLO un JSON con la estructura:
{{"field_name": "nuevo_valor", "field_name2": "nuevo_valor2"}}

Mapeo de campos:
- "name" para nombre
- "lastname" para apellido  
- "city" para ciudad
- "phone" para teléfono

Ejemplos:
- "Quiero actualizar mi nombre a Juan" → {{"name": "Juan"}}
- "Mi nombre es Juan Pérez" → {{"name": "Juan Pérez"}}  (nombre completo)
- "Mi apellido es García" → {{"lastname": "García"}}
- "Mi apellido es Pérez" → {{"lastname": "Pérez"}}
- "Vivo en Bogotá" → {{"city": "Bogotá"}}
- "Quiero cambiar mi nombre a María y mi ciudad a Cali" → {{"name": "María", "city": "Cali"}}
- "Mi nombre es Carlos" (después de pedir actualización) → {{"name": "Carlos"}}
- "Ahora mi apellido es Rodríguez" → {{"lastname": "Rodríguez"}}

REGLA ESPECIAL PARA NOMBRE VS APELLIDO:
- Si dice solo "Juan", "María", "Carlos" sin contexto, usar tu criterio basado en nombres comunes hispanos
- Si dice "García", "Pérez", "Rodríguez", "López", "González" → APELLIDO
- Si dice "mi nombre es X" → NOMBRE
- Si dice "mi apellido es X" → APELLIDO

**IMPORTANTE**: Si el usuario da "Santiago Buitrago Rojas":
- "Santiago" es NOMBRE → name: Santiago
- "Buitrago Rojas" son los apellidos → lastname: Buitrago Rojas
- Si solo da "Juan Pérez" → name: Juan, lastname: Pérez

Ejemplos de separación:
- "Juan García" → {"name": "Juan", "lastname": "García"}
- "María José López" → {"name": "María José", "lastname": "López"}
- "Carlos Rodríguez Pérez" → {"name": "Carlos", "lastname": "Rodríguez Pérez"}

Devuelve SOLO el JSON, sin texto adicional:"""

            response_obj = await self._generate_content_ultra_fast(prompt, max_tokens=200)
            response_text = response_obj.strip()
            
            # Limpiar la respuesta para extraer JSON
            
            # Buscar JSON en la respuesta - soportar JSON con llaves anidadas
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text)
            update_data_str = None
            
            # Fallback: si no encuentra con regex, buscar entre ```json y ```
            if not json_match:
                json_block = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_block:
                    update_data_str = json_block.group(1)
                else:
                    # Último fallback: buscar cualquier JSON
                    json_simple = re.search(r'\{[^{}]*"name"[^{}]*\}', response_text)
                    if json_simple:
                        update_data_str = json_simple.group()
            else:
                update_data_str = json_match.group()
                
            if update_data_str and update_data_str.strip():
                update_data = json.loads(update_data_str)
                
                logger.info(f"✅ Datos a actualizar extraídos (antes de normalizar): {update_data}")
                
                # 🔧 NORMALIZAR datos extraídos: primera letra en mayúscula
                if "name" in update_data and update_data["name"]:
                    update_data["name"] = update_data["name"].title()
                if "lastname" in update_data and update_data["lastname"]:
                    update_data["lastname"] = update_data["lastname"].title()
                if "city" in update_data and update_data["city"]:
                    update_data["city"] = update_data["city"].title()
                if "phone" in update_data and update_data["phone"]:
                    update_data["phone"] = update_data["phone"].strip()
                
                logger.info(f"✅ Datos normalizados: {update_data}")
                
                # Generar mensaje de confirmación mostrando TODOS los datos (actuales + actualizados)
                confirmation_lines = []
                
                # Obtener datos actuales del usuario desde user_context
                current_name = user_context.get("user_name") or user_context.get("name") or ""
                current_lastname = user_context.get("user_lastname") or user_context.get("lastname") or ""
                current_city = user_context.get("user_city") or user_context.get("city") or ""
                current_state = user_context.get("user_state") or user_context.get("state") or ""
                current_country = user_context.get("user_country") or user_context.get("country") or "Colombia"
                
                # Aplicar cambios para mostrar cómo quedarían
                final_name = update_data.get("name", current_name) if update_data else current_name
                final_lastname = update_data.get("lastname", current_lastname) if update_data else current_lastname
                final_city = update_data.get("city", current_city) if update_data else current_city
                final_state = update_data.get("state", current_state) if update_data else current_state
                final_country = update_data.get("country", current_country) if update_data else current_country
                
                # Mostrar los 3 datos completos (nombre, apellido, ciudad)
                if final_name:
                    confirmation_lines.append(f"👤 Nombre: {final_name}")
                if final_lastname:
                    confirmation_lines.append(f"👤 Apellido: {final_lastname}")
                if final_city:
                    # Construir información completa de ubicación
                    location_parts = [final_city]
                    if final_state:
                        location_parts.append(final_state)
                    if final_country:
                        location_parts.append(final_country)
                    location_info = ", ".join(location_parts)
                    confirmation_lines.append(f"🏙️ Ciudad: {location_info}")
                
                confirmation_body = "Perfecto! Tus datos quedarían así:\n\n" + "\n".join(confirmation_lines) + "\n\n¿Confirmas que estos datos son correctos?"
                
                # Indicar que se deben enviar botones
                update_data["_needs_interactive_buttons"] = True
                update_data["_confirmation_message"] = confirmation_body
                
                # Retornar mensaje Y datos para que Java envíe botones
                return (confirmation_body, update_data)
            else:
                # Fallback si no se pudo extraer JSON
                logger.warning("⚠️ No se pudo extraer datos para actualizar")
                return ("Entiendo que quieres actualizar tu información. Por favor, indica específicamente qué datos deseas cambiar. Por ejemplo: 'Quiero actualizar mi nombre a Juan' o 'Cambiar mi ciudad a Bogotá'.", None)
                
        except json.JSONDecodeError as json_error:
            logger.error(f"❌ Error decodificando JSON de actualización: {json_error}")
            return ("Hubo un problema procesando tu solicitud de actualización. Por favor, intenta de nuevo especificando los datos que deseas cambiar.", None)
        except Exception as e:
            logger.error(f"❌ Error procesando actualización de datos: {e}")
            return ("Hubo un error procesando tu solicitud de actualización. Por favor, intenta de nuevo.", None)
    
    def _get_greeting_response_with_context(self, branding_config: Dict[str, Any], session_context: str = "", tenant_id: str = None) -> str:
        """Genera saludo con contexto de sesión inteligente - USA PROMPTS DESDE DB"""
        contact_name = branding_config.get("contactName", "el candidato")
        
        # 🗄️ PRIORIDAD 1: Intentar usar prompts desde DB
        if tenant_id:
            prompts_from_db = self.persistence_service.get_tenant_prompts(tenant_id)
            if prompts_from_db and 'welcome' in prompts_from_db:
                logger.info(f"✅ Usando prompt 'welcome' desde DB para tenant {tenant_id}")
                return prompts_from_db['welcome']
        
        # Si hay contexto de sesión, generar respuesta contextual inteligente
        if session_context and len(session_context.strip()) > 50:
            # Usar IA para generar respuesta contextual basada en la conversación anterior
            try:
                self._ensure_model_initialized()
                if self.model:
                    prompt = f"""
                    Asistente virtual de {contact_name}. El usuario acaba de enviar un saludo o respuesta corta como "ok", "hola", "gracias", etc.
                    
                    CONTEXTO DE LA CONVERSACIÓN ANTERIOR:
                    {session_context}
                    
                    INSTRUCCIONES:
                    1. Genera una respuesta natural y contextual basada en la conversación anterior
                    2. Si el usuario acababa de preguntar sobre propuestas, ofrece más información específica
                    3. Si el usuario acababa de agendar una cita, confirma o pregunta si necesita algo más
                    4. Si es la primera interacción, da la bienvenida
                    5. Mantén un tono amigable y profesional
                    6. Responde en máximo 200 caracteres
                    7. **PROHIBIDO**: NUNCA uses placeholders como [TU_ENLACE_PERSONAL_AQUÍ], [ENLACE], [LINK], etc.
                    8. **IMPORTANTE**: Responde solo con texto natural, sin enlaces ni placeholders
                    
                    Responde de manera natural y contextual:
                    """
                    
                    response = self.model.generate_content(prompt, safety_settings=self._get_safety_settings())
                    filtered_response = self._filter_links_from_response(response.text.strip())
                    return filtered_response
            except Exception as e:
                logger.warning(f"Error generando saludo contextual: {e}")
        
        # Fallback: respuesta genérica
        if session_context:
            fallback_response = f"""¡Hola! Me da mucho gusto verte de nuevo. ¿En qué más puedo ayudarte hoy con información sobre {contact_name} y sus propuestas?"""
            return self._filter_links_from_response(fallback_response)
        else:
            fallback_response = f"""¡Hola! Te doy la bienvenida a nuestra campaña: {contact_name}!!! 
            
¿En qué puedo ayudarte hoy? Puedo responder tus preguntas sobre nuestras propuestas, ayudarte a agendar una cita, o conectarte con nuestro equipo."""
            return self._filter_links_from_response(fallback_response)
    
    def _get_volunteer_response_with_context(self, branding_config: Dict[str, Any], session_context: str = "") -> str:
        """Genera respuesta de voluntariado con clasificación por área"""
        contact_name = branding_config.get("contactName", "el candidato")
        
        # Respuesta con opciones de clasificación por área
        volunteer_response = f"""¡Excelente que quieras apoyarnos! {contact_name} valora mucho la colaboración de personas comprometidas como tú.

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
        
        return volunteer_response

    def _get_complaint_response_with_context(self, branding_config: Dict[str, Any], session_context: str = "") -> str:
        """Genera respuesta inicial para quejas solicitando más detalles"""
        contact_name = branding_config.get("contactName", "el candidato")
        
        # Respuesta pidiendo detalles de la queja
        complaint_response = f"""Entiendo que tienes una inquietud o queja. Tu opinión es muy importante para {contact_name} y queremos ayudarte.

Por favor, compárteme más detalles sobre tu queja o reclamo. Puedes contarme:
• ¿Qué sucedió?
• ¿Cuándo pasó?
• ¿Quién estuvo involucrado?

Describe tu situación y con gusto te ayudaré a resolverla o la transmitiré al equipo correspondiente."""
        
        return complaint_response

    def _get_complaint_detail_response_with_context(self, branding_config: Dict[str, Any], session_context: str = "", complaint_detail: str = "") -> str:
        """Genera respuesta de confirmación de queja registrada"""
        contact_name = branding_config.get("contactName", "el candidato")
        
        # Respuesta confirmando recepción de queja
        complaint_confirmation = f"""Gracias por compartir los detalles de tu queja o reclamo. He registrado la información y la he enviado al equipo correspondiente de la campaña.

{contact_name} y su equipo tomarán cartas en el asunto para resolver tu inquietud lo antes posible.

Tu opinión es muy valiosa para nosotros. ¿Hay algo más en lo que pueda ayudarte?"""
        
        return complaint_confirmation


    async def validate_user_data(self, tenant_id: str, data: str, data_type: str) -> Dict[str, Any]:
        """
        Valida datos de usuario usando cache y IA
        
        Args:
            tenant_id: ID del tenant
            data: Datos a validar
            data_type: Tipo de dato (name, lastname, city, etc.)
            
        Returns:
            Dict con resultado de validación
        """
        # 🚀 OPTIMIZACIÓN: Verificar cache primero para datos comunes
        if data_type in self._validation_cache:
            data_lower = data.lower().strip()
            if data_lower in self._validation_cache[data_type]:
                logger.info(f"✅ Cache hit para validación {data_type}: '{data}' -> válido")
                return self._validation_cache[data_type][data_lower]
        
        logger.info(f"🔍 Cache miss para validación {data_type}: '{data}' - usando IA")
        # Validación determinística previa (aceptar sin IA si es claramente válido)
        try:
            clean = (data or "").strip()
            if data_type in ("name", "lastname") and clean:
                # Pre-procesar muletillas y prefijos comunes de presentación de nombre
                lower = clean.lower()
                lower = re.sub(r"^(claro|bueno|ok|okay|vale|listo|pues|sí|si|hola)[,\s]+", "", lower)
                lower = re.sub(r"^(mi\s+nombre\s+es|me\s+llamo|yo\s+me\s+llamo|soy|nombre\s*:\s*|nombre\s+es)\s+", "", lower)
                lower = re.sub(r"[^A-Za-zÁÉÍÓÚáéíóúÑñ\s\-'\.]", " ", lower)
                lower = re.sub(r"\s+", " ", lower).strip()
                if lower:
                    clean = lower
                # Normalizar espacios múltiples
                clean_norm = re.sub(r"\s+", " ", clean)
                # Solo letras, espacios, guiones, apóstrofes y puntos; longitud 2-50
                if re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ\s\-'\.]{2,50}$", clean_norm):
                    words = [w for w in clean_norm.split(" ") if w]
                    max_words = 4 if data_type == "name" else 3
                    if 1 <= len(words) <= max_words:
                        logger.info(f"✅ Validación determinística aprobó {data_type}: '{clean_norm}'")
                        return {
                            "is_valid": True,
                            "confidence": 0.95,
                            "reason": "Validación determinística: formato y longitud válidos",
                            "suggestions": []
                        }
        except Exception as _e:
            logger.warning(f"⚠️ Error en validación determinística ({data_type}): {_e}")
        
        self._ensure_model_initialized()
        
        if not self.model:
            return {
                "is_valid": False,
                "confidence": 0.0,
                "reason": "Servicio de IA no disponible",
                "suggestions": []
            }
        
        try:
            # Crear prompt específico según el tipo de dato
            if data_type == "name":
                prompt = f"""
Analiza si el siguiente texto es un nombre válido de persona:

Texto: "{clean}"

Un nombre válido debe:
- Contener solo letras, espacios, guiones, apostrofes y puntos
- Tener entre 2 y 50 caracteres
- NO contener números (excepto en casos especiales como "María José")
- NO ser una palabra común del español como "referido", "gracias", "hola", etc.
- NO ser un código alfanumérico
- NO ser una pregunta o consulta (ej: "Pero dime quién eres", "quién eres", "dime qué")
- Puede incluir nombre completo con apellidos si el usuario los ingresó juntos (máximo 4 palabras)

IMPORTANTE: 
- Si el texto es una pregunta o consulta (contiene palabras como "quién", "dime", "eres", "qué", "cómo"), es INVALIDO
- Si el usuario ingresó su nombre completo con apellidos (ej: "Santiago Buitrago Rojas"), es VÁLIDO ya que el sistema lo separará correctamente

Responde ÚNICAMENTE "VALIDO" o "INVALIDO" seguido de la razón si es inválido.

Ejemplos:
- "Juan" -> VALIDO
- "María José" -> VALIDO
- "José María" -> VALIDO
- "Santiago Buitrago Rojas" -> VALIDO (nombre completo con apellidos)
- "Carlos Alberto Pérez" -> VALIDO (nombre completo)
- "Ana María García López" -> VALIDO (nombre completo con apellidos)
- "SANTIAGO" -> VALIDO
- "Pero Dime Quién Eres" -> INVALIDO (es una pregunta, no un nombre)
- "Quién Eres" -> INVALIDO (es una pregunta)
- "Dime Quién" -> INVALIDO (es una pregunta)
- "K351ERXL" -> INVALIDO (es un código, no un nombre)
- "referido" -> INVALIDO (palabra común)
- "12345678" -> INVALIDO (solo números)
"""
            elif data_type == "lastname":
                prompt = f"""
Analiza si el siguiente texto es un apellido válido de persona:

Texto: "{data}"

Un apellido válido debe:
- Contener solo letras, espacios, guiones, apostrofes y puntos
- Tener entre 2 y 50 caracteres
- NO contener números (excepto en casos especiales)
- NO ser una palabra común del español como "referido", "gracias", "hola", etc.
- NO ser un código alfanumérico

Responde ÚNICAMENTE "VALIDO" o "INVALIDO" seguido de la razón si es inválido.

Ejemplos:
- "García" -> VALIDO
- "García López" -> VALIDO
- "Pérez" -> VALIDO
- "K351ERXL" -> INVALIDO (es un código, no un apellido)
- "referido" -> INVALIDO (palabra común)
"""
            elif data_type == "city":
                prompt = f"""
Analiza si el siguiente texto es una ciudad válida de Colombia:

Texto: "{data}"

Una ciudad válida debe:
- Contener solo letras, espacios, guiones, apostrofes y puntos
- Tener entre 2 y 100 caracteres
- NO contener números (excepto en casos especiales como "San José del Guaviare")
- NO ser una palabra común del español como "referido", "gracias", "hola", etc.
- NO ser un código alfanumérico
- Ser una ciudad real de Colombia O un apodo conocido de una ciudad colombiana

APODOS VÁLIDOS DE CIUDADES COLOMBIANAS:
- "La sucursal del cielo" -> Cali (VALLE DEL CAUCA)
- "La eterna primavera" -> Medellín (ANTIOQUIA)
- "La ciudad de la eterna primavera" -> Medellín (ANTIOQUIA)
- "La ciudad eterna" -> Medellín (ANTIOQUIA)
- "La sultana del valle" -> Cali (VALLE DEL CAUCA)
- "La capital mundial de la salsa" -> Cali (VALLE DEL CAUCA)
- "La heroica" -> Cartagena (BOLÍVAR)
- "La puerta de oro de Colombia" -> Barranquilla (ATLÁNTICO)
- "La ciudad de las puertas abiertas" -> Manizales (CALDAS)
- "La ciudad blanca" -> Popayán (CAUCA)
- "La villa de robledo" -> Cartago (VALLE DEL CAUCA)
- "La villa del cacique" -> Calarcá (QUINDÍO)

IMPORTANTE: Si el texto describe una ciudad con una frase poética o apodo, es VÁLIDO si representa una ciudad colombiana real.

Responde ÚNICAMENTE "VALIDO" o "INVALIDO" seguido de la razón si es inválido.

Ejemplos:
- "Bogotá" -> VALIDO
- "Medellín" -> VALIDO
- "Cali" -> VALIDO
- "Soacha" -> VALIDO
- "La sucursal del cielo" -> VALIDO (Cali)
- "La eterna primavera" -> VALIDO (Medellín)
- "La heroica" -> VALIDO (Cartagena)
- "K351ERXL" -> INVALIDO (es un código, no una ciudad)
- "referido" -> INVALIDO (palabra común)
- "mi ciudad favorita" -> INVALIDO (descripción genérica, no nombre específico)
"""
            else:
                # Validación genérica
                prompt = f"""
Analiza si el siguiente texto es válido para el tipo de dato "{data_type}":

Texto: "{data}"

El texto debe:
- Contener solo letras, espacios, guiones, apostrofes y puntos
- Tener entre 2 y 100 caracteres
- NO ser una palabra común del español como "referido", "gracias", "hola", etc.
- NO ser un código alfanumérico

Responde ÚNICAMENTE "VALIDO" o "INVALIDO" seguido de la razón si es inválido.
"""
            
            response_text = await self._generate_content(prompt)
            
            if not response_text:
                return {
                    "is_valid": False,
                    "confidence": 0.0,
                    "reason": "No se pudo obtener respuesta de la IA",
                    "suggestions": []
                }
            
            response_upper = response_text.strip().upper()
            
            if "VALIDO" in response_upper:
                return {
                    "is_valid": True,
                    "confidence": 0.9,
                    "reason": "Datos válidos según IA",
                    "suggestions": []
                }
            else:
                reason = response_text.strip()
                return {
                    "is_valid": False,
                    "confidence": 0.8,
                    "reason": reason,
                    "suggestions": []
                }
                
        except Exception as e:
            logger.error(f"Error validando datos con IA: {str(e)}")
            return {
                "is_valid": False,
                "confidence": 0.0,
                "reason": f"Error en validación: {str(e)}",
                "suggestions": []
            }

    async def analyze_registration_message(self, tenant_id: str, message: str, user_context: Dict[str, Any], current_state: str) -> Dict[str, Any]:
        """
        Analiza un mensaje durante el proceso de registro
        """
        return await self.analyze_registration(tenant_id, message, user_context, current_state)

    async def _handle_malicious_message(self, tenant_id: str, query: str, user_context: Dict[str, Any], 
                                       malicious_detection: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Maneja mensajes maliciosos detectados durante el proceso de registro
        
        Args:
            tenant_id: ID del tenant
            query: Mensaje malicioso del usuario
            user_context: Contexto del usuario
            malicious_detection: Resultado de la detección de comportamiento malicioso
            session_id: ID de la sesión
            
        Returns:
            Respuesta de bloqueo o advertencia
        """
        try:
            confidence = malicious_detection.get("confidence", 0.0)
            reason = malicious_detection.get("reason", "Comportamiento inapropiado")
            
            logger.warning(f"🚫 Comportamiento malicioso detectado: confianza={confidence}, razón={reason}")
            
            # Obtener información del usuario para logging
            user_id = user_context.get("user_id", "unknown")
            user_name = user_context.get("user_name", "Usuario")
            user_state = user_context.get("user_state", "unknown")
            
            # Log del incidente malicioso
            await user_blocking_service.log_malicious_incident(
                tenant_id=tenant_id,
                user_id=user_id,
                phone_number=user_context.get("phone_number", ""),
                malicious_message=query,
                classification_confidence=confidence
            )
            
            # Determinar respuesta según el nivel de malicia
            if confidence >= 0.9:
                # Comportamiento muy malicioso - bloquear usuario
                await user_blocking_service.block_user(tenant_id, user_id, reason="Comportamiento malicioso durante registro")
                user_context["user_state"] = "BLOCKED"
                session_context_service.update_user_context(session_id, user_context)
                
                response = "Tu mensaje contiene contenido inapropiado. Has sido bloqueado del sistema."
                logger.warning(f"🚫 Usuario {user_id} bloqueado por comportamiento malicioso durante registro")
                
            elif confidence >= 0.7:
                # Comportamiento moderadamente malicioso - advertencia
                response = "Por favor, mantén un tono respetuoso. Este es un espacio para el diálogo constructivo sobre la campaña política."
                
            else:
                # Comportamiento ligeramente inapropiado - redirección suave
                response = "Entiendo que quieres participar. Por favor, comparte información constructiva sobre la campaña."
            
            # Agregar respuesta del bot a la sesión
            session_context_service.add_message(session_id, "assistant", response)
            
            processing_time = time.time() - start_time if 'start_time' in locals() else 0.0
            
            return {
                "response": response,
                "followup_message": "",
                "from_cache": False,
                "processing_time": processing_time,
                "tenant_id": tenant_id,
                "session_id": session_id,
                "intent": "malicioso",
                "confidence": confidence,
                "malicious_detection": malicious_detection,
                "user_blocked": confidence >= 0.8
            }
            
        except Exception as e:
            logger.error(f"❌ Error manejando mensaje malicioso: {str(e)}")
            # Fallback a respuesta genérica de bloqueo
            return {
                "response": "Por favor, mantén un tono respetuoso en nuestras conversaciones.",
                "followup_message": "",
                "from_cache": False,
                "processing_time": time.time() - start_time,
                "tenant_id": tenant_id,
                "session_id": session_id,
                "intent": "malicioso",
                "confidence": 0.0,
                "error": str(e)
            }

    async def _handle_registration_response(self, tenant_id: str, query: str, user_context: Dict[str, Any], 
                                           registration_analysis: Dict[str, Any], branding_config: Dict[str, Any], 
                                           session_id: str) -> Dict[str, Any]:
        """
        Maneja respuestas de registro cuando el usuario está en proceso de registro
        
        Args:
            tenant_id: ID del tenant
            query: Mensaje del usuario
            user_context: Contexto del usuario
            registration_analysis: Análisis de la respuesta de registro
            branding_config: Configuración de branding
            session_id: ID de la sesión
            
        Returns:
            Respuesta procesada para el usuario
        """
        try:
            contact_name = branding_config.get("contactName", "el candidato")
            data_type = registration_analysis.get("type", "other")
            data_value = registration_analysis.get("value", "")
            confidence = registration_analysis.get("confidence", 0.0)
            
            logger.info(f"🔄 Procesando respuesta de registro: tipo={data_type}, valor='{data_value}', confianza={confidence}")
            
            # Construir respuesta específica según el tipo de datos extraídos
            if data_type == "name" and data_value:
                response = f"¡Perfecto! Nombre anotado: {data_value}. Ahora necesito tu apellido:"
                # Actualizar contexto del usuario
                user_context["user_name"] = data_value
                session_context_service.update_user_context(session_id, user_context)
                
            elif data_type == "lastname" and data_value:
                user_name = user_context.get("user_name", "Usuario")
                response = f"¡Perfecto, {user_name}! Apellido anotado: {data_value}. Ahora dime, ¿en qué ciudad vives?"
                # Actualizar contexto del usuario
                user_context["user_lastname"] = data_value
                session_context_service.update_user_context(session_id, user_context)
                
            elif data_type == "city" and data_value:
                user_name = user_context.get("user_name", "Usuario")
                response = f"¡Excelente, {user_name}! Ciudad anotada: {data_value}. Ahora dime, ¿en qué te puedo asistir hoy desde la oficina de {contact_name}?"
                # Actualizar contexto del usuario
                user_context["user_city"] = data_value
                user_context["user_state"] = "COMPLETED"  # Marcar como completado
                session_context_service.update_user_context(session_id, user_context)
                
            elif data_type == "code" and data_value:
                user_name = user_context.get("user_name", "Usuario")
                response = f"¡Perfecto, {user_name}! Código de referido anotado: {data_value}. Ahora dime, ¿en qué te puedo asistir hoy desde la oficina de {contact_name}?"
                # Actualizar contexto del usuario
                user_context["referral_code"] = data_value
                user_context["user_state"] = "COMPLETED"  # Marcar como completado
                session_context_service.update_user_context(session_id, user_context)
                
            elif data_type == "info":
                # Usar IA para generar respuesta natural cuando es información/explicación
                logger.info(f"🎯 Generando respuesta con IA para explicación: '{query[:30]}...'")
                ai_response = await self._generate_content_optimized(
                    f"""Eres un asistente de campaña política. El usuario está en proceso de registro.

CONTEXTO:
- Estado del usuario: {user_context.get('user_state', 'UNKNOWN')}
- Mensaje del usuario: "{query}"

INSTRUCCIONES:
1. Si el usuario explica limitaciones (ej: "solo puedo dar nombre y apellido"), entiende y adapta el proceso
2. Si es un saludo, responde amigablemente y continúa el registro
3. Si pregunta sobre el candidato, explica que después del registro le puedes ayudar
4. Mantén un tono amigable y profesional
5. Siempre guía hacia completar el registro

RESPUESTA NATURAL:""",
                    "registration_response"
                )
                response = ai_response if ai_response else "Entiendo tu consulta. ¿Podrías proporcionarme la información que necesito?"
                
            else:
                # Si no se pudo extraer datos específicos, pedir aclaración
                user_state = user_context.get("user_state", "")
                if user_state == "WAITING_NAME":
                    response = "Por favor, comparte tu nombre completo para continuar con el registro."
                elif user_state == "WAITING_LASTNAME":
                    response = "Perfecto, ahora necesito tu apellido para completar tu información."
                elif user_state == "WAITING_CITY":
                    response = "¿En qué ciudad vives? Esto nos ayuda a conectar con promotores de tu región."
                elif user_state == "WAITING_CODE":
                    response = "Si tienes un código de referido, compártelo. Si no, escribe 'no' para continuar."
                else:
                    response = "Por favor, comparte la información solicitada para continuar."
            
            # Agregar respuesta del bot a la sesión
            session_context_service.add_message(session_id, "assistant", response)
            
            processing_time = time.time() - start_time if 'start_time' in locals() else 0.0
            
            return {
                "response": response,
                "followup_message": "",
                "from_cache": False,
                "processing_time": processing_time,
                "tenant_id": tenant_id,
                "session_id": session_id,
                "intent": "registration_response",
                "confidence": confidence,
                "extracted_data": {
                    "type": data_type,
                    "value": data_value
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error manejando respuesta de registro: {str(e)}")
            # Fallback a respuesta genérica
            return {
                "response": "Por favor, comparte la información solicitada para continuar con el registro.",
                "followup_message": "",
                "from_cache": False,
                "processing_time": time.time() - start_time,
                "tenant_id": tenant_id,
                "session_id": session_id,
                "intent": "registration_response",
                "confidence": 0.0,
                "error": str(e)
            }

    async def extract_user_name_from_message(self, tenant_id: str, message: str) -> Dict[str, Any]:
     """
     Extrae el nombre del usuario de cualquier mensaje (no necesariamente con código de referido)
     MÉTODO NO SE USA - COMENTADO
     """
     self._ensure_model_initialized()
     
     if not self.model:
         return {
             "name": None,
             "is_valid": False,
             "confidence": 0.0,
             "reason": "Servicio de IA no disponible"
         }
     
     try:
         prompt = f"""
 Analiza el siguiente mensaje y extrae el nombre completo de la persona:

 Mensaje: "{message}"

 IMPORTANTE:
 - Busca patrones como "Soy [nombre]", "Me llamo [nombre]", "Mi nombre es [nombre]", etc.
 - Extrae el nombre completo (nombre y apellidos si están disponibles)
 - Si el mensaje no contiene un nombre claro, responde "NO_NAME"
 - Ignora saludos como "hola", "buenos días", etc.

 Ejemplos:
 - "Soy Santiago Buitrago Rojas" -> "Santiago Buitrago Rojas"
 - "Me llamo María García" -> "María García"
 - "Mi nombre es Carlos" -> "Carlos"
 - "Hola, soy Ana" -> "Ana"
 - "hola" -> "NO_NAME"
 - "buenos días" -> "NO_NAME"

 Responde ÚNICAMENTE el nombre extraído o "NO_NAME" si no se puede determinar.
 """

         response_text = await self._generate_content(prompt)
         
         if not response_text:
             return {
                 "name": None,
                 "is_valid": False,
                 "confidence": 0.0,
                 "reason": "No se pudo obtener respuesta de la IA"
             }
         
         response_clean = response_text.strip()
         
         if response_clean.upper() == "NO_NAME":
             return {
                 "name": None,
                 "is_valid": False,
                 "confidence": 0.9,
                 "reason": "El mensaje no contiene un nombre claro"
             }
         
         # Validar que el nombre extraído es válido
         validation_result = await self.validate_user_data(tenant_id, response_clean, "name")
         
         if validation_result.get("is_valid", False):
             return {
                 "name": response_clean,
                 "is_valid": True,
                 "confidence": validation_result.get("confidence", 0.8),
                 "reason": "Nombre extraído y validado correctamente"
             }
         else:
             return {
                 "name": response_clean,
                 "is_valid": False,
                 "confidence": validation_result.get("confidence", 0.5),
                 "reason": f"Nombre extraído pero no válido: {validation_result.get('reason', '')}"
             }
             
     except Exception as e:
         logger.error(f"Error extrayendo nombre del mensaje con IA: {str(e)}")
         return {
             "name": None,
             "is_valid": False,
             "confidence": 0.0,
             "reason": f"Error en extracción: {str(e)}"
         }

    async def extract_user_name_from_message(self, tenant_id: str, message: str) -> Dict[str, Any]:
        """
        Extrae el nombre del usuario de un mensaje (con o sin referido, con o sin frases como
        "mi nombre es", "me llamo", "soy"). Usa limpieza y extracción determinística antes de IA.
        """
        try:
            text = (message or "").strip()
            if not text:
                return {"name": None, "is_valid": False, "confidence": 0.0, "reason": "Mensaje vacío"}

            # 🔧 FIX: Usar IA para detectar si el mensaje es una pregunta o consulta (no un nombre)
            is_question_result = await self.is_question_message(tenant_id, text)
            if is_question_result.get("is_question", False):
                logger.info(f"⚠️ IA detectó que el mensaje es una pregunta - rechazando: '{text}'")
                return {"name": None, "is_valid": False, "confidence": is_question_result.get("confidence", 0.9), 
                        "reason": is_question_result.get("reason", "Mensaje es una pregunta, no un nombre")}

            # 1) Limpieza de prefijos y normalización
            cleaned = re.sub(r"^(claro|bueno|ok|okay|vale|listo|pues|sí|si|hola)[,\s]+", "", text, flags=re.IGNORECASE)
            cleaned = re.sub(r"^(mi\s+nombre\s+es|me\s+llamo|yo\s+me\s+llamo|soy|nombre\s*:\s*|nombre\s+es)\s+", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"[^A-Za-zÁÉÍÓÚáéíóúÑñ\s\-'\.]", " ", cleaned)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()

            # 2) Extracción determinística si el resultado luce como nombre completo
            if cleaned and re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ\s\-'\.]{2,50}$", cleaned):
                words = [w for w in cleaned.split(" ") if w]
                if 1 <= len(words) <= 4:
                    # Capitalizar palabras
                    name_cap = " ".join([w[:1].upper() + w[1:] if len(w) > 0 else w for w in words])
                    validation = await self.validate_user_data(tenant_id, name_cap, "name")
                    if validation.get("is_valid", False):
                        return {"name": name_cap, "is_valid": True, "confidence": 0.95, "reason": "Extracción determinística"}

            # 3) IA como respaldo: prompt genérico robusto
            self._ensure_model_initialized()
            if not self.model:
                return {"name": None, "is_valid": False, "confidence": 0.0, "reason": "Servicio de IA no disponible"}

            prompt = f"""
Analiza el siguiente mensaje y extrae SOLO el nombre y apellidos (si aparecen) de la persona que se está registrando.

Mensaje: "{message}"

Reglas:
- El mensaje puede incluir frases como: "mi nombre es", "me llamo", "soy", "nombre:", emojis o muletillas como "claro".
- Ignora cualquier persona que REFIERA (p. ej., "vengo referido por Juan" -> NO extraer "Juan").
- Entrega solo el nombre de QUIEN SE REGISTRA, con mayúscula inicial por palabra.
- Si no puedes identificar un nombre del usuario, responde exactamente "NO_NAME".

Ejemplos:
- "Hola, vengo referido por Juan" -> NO_NAME
- "Soy María" -> María
- "Me llamo Carlos Pérez" -> Carlos Pérez
- "Claro, mi nombre es Ana García López" -> Ana García López
- "Nombre: José" -> José

Responde ÚNICAMENTE con el nombre (sin explicaciones) o "NO_NAME".
"""
            response_text = await self._generate_content(prompt)
            if not response_text:
                return {"name": None, "is_valid": False, "confidence": 0.0, "reason": "IA sin respuesta"}

            candidate = response_text.strip()
            if candidate.upper() == "NO_NAME":
                return {"name": None, "is_valid": False, "confidence": 0.9, "reason": "IA no encontró nombre"}

            # 4) Limpieza y validación del candidato de IA
            candidate = re.sub(r"[^A-Za-zÁÉÍÓÚáéíóúÑñ\s\-'\.]", " ", candidate)
            candidate = re.sub(r"\s+", " ", candidate).strip()
            validation = await self.validate_user_data(tenant_id, candidate, "name")
            if validation.get("is_valid", False):
                return {"name": candidate, "is_valid": True, "confidence": validation.get("confidence", 0.85), "reason": "IA validó nombre"}

            # 5) Último recurso: heurística simple tomando las últimas palabras tipo nombre
            tokens = [t for t in candidate.split(" ") if t and re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ\-'\.]+$", t)]
            if 1 <= len(tokens) <= 4:
                fallback_name = " ".join(tokens)
                validation2 = await self.validate_user_data(tenant_id, fallback_name, "name")
                if validation2.get("is_valid", False):
                    return {"name": fallback_name, "is_valid": True, "confidence": 0.8, "reason": "Heurística validada"}

            return {"name": None, "is_valid": False, "confidence": 0.0, "reason": "No se pudo extraer un nombre válido"}

        except Exception as e:
            logger.error(f"Error extrayendo nombre del mensaje con IA: {str(e)}")
            return {"name": None, "is_valid": False, "confidence": 0.0, "reason": f"Error en extracción: {str(e)}"}

    async def is_question_message(self, tenant_id: str, message: str) -> Dict[str, Any]:
        """
        Verifica si un mensaje es una pregunta o consulta usando IA (no un nombre o dato de registro)
        """
        self._ensure_model_initialized()
        
        if not self.model:
            return {
                "is_question": False,
                "confidence": 0.0,
                "reason": "Servicio de IA no disponible"
            }
        
        try:
            prompt = f"""
Analiza el siguiente mensaje y determina si es una PREGUNTA o CONSULTA (no un nombre, apellido, ciudad u otro dato de registro).

Mensaje: "{message}"

Reglas:
- Si el mensaje es una pregunta (ej: "¿quién eres?", "dime quién eres", "qué es esto", "cómo funciona") -> es PREGUNTA
- Si el mensaje es una consulta o solicitud de información (ej: "explícame", "cuéntame sobre", "quiero saber") -> es PREGUNTA
- Si el mensaje contiene un nombre, apellido, ciudad u otro dato personal (ej: "Soy Juan Pérez", "Me llamo María", "Vivo en Bogotá") -> NO es PREGUNTA
- Si el mensaje es una respuesta directa a una pregunta del sistema (ej: "Juan", "Pérez", "Bogotá") -> NO es PREGUNTA

Ejemplos:
- "Pero dime quién eres" -> PREGUNTA (es una pregunta sobre identidad)
- "¿Quién eres?" -> PREGUNTA (es una pregunta directa)
- "Quiero saber más" -> PREGUNTA (es una consulta)
- "Soy Juan Pérez" -> NO es PREGUNTA (es un nombre)
- "Me llamo María" -> NO es PREGUNTA (es un nombre)
- "Vivo en Bogotá" -> NO es PREGUNTA (es una ciudad)
- "Juan" -> NO es PREGUNTA (es un nombre)

Responde ÚNICAMENTE "PREGUNTA" o "NO_PREGUNTA" seguido de una breve razón.
"""
            
            response_text = await self._generate_content(prompt, task_type="question_detection")
            response_clean = response_text.strip().upper()
            
            is_question = response_clean.startswith("PREGUNTA")
            
            # Extraer razón si está disponible
            reason = "Mensaje analizado con IA"
            if ":" in response_text or "-" in response_text:
                parts = response_text.split(":", 1) if ":" in response_text else response_text.split("-", 1)
                if len(parts) > 1:
                    reason = parts[1].strip()
            
            logger.info(f"🔍 IA analizó si es pregunta: '{message[:50]}...' -> {is_question} (confianza: 0.9)")
            
            return {
                "is_question": is_question,
                "confidence": 0.9,
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Error verificando si es pregunta con IA: {str(e)}")
            return {
                "is_question": False,
                "confidence": 0.0,
                "reason": f"Error en análisis: {str(e)}"
            }

    async def generate_welcome_message(self, tenant_config: Dict[str, Any] = None) -> str:
        """
        Genera un mensaje de bienvenida personalizado usando IA
        
        Args:
            tenant_config: Configuración del tenant (opcional)
            
        Returns:
            Mensaje de bienvenida generado por IA
        """
        try:
            # Obtener información del tenant para personalización
            tenant_info = ""
            if tenant_config:
                branding = tenant_config.get('branding', {})
                if branding:
                    candidate_name = branding.get('candidate_name', '')
                    campaign_name = branding.get('campaign_name', '')
                    if candidate_name:
                        tenant_info += f"Candidato: {candidate_name}. "
                    if campaign_name:
                        tenant_info += f"Campaña: {campaign_name}. "
            
            # Generar mensaje con IA usando el método que sí funciona
            prompt = f"""Genera un mensaje de bienvenida para WhatsApp de la campaña de {tenant_info.strip() or 'nuestro candidato'}.

El mensaje debe ser amigable y presentar la campaña. Máximo 100 caracteres.

Mensaje:"""

            try:
                response = await self._generate_content(prompt, task_type="chat_conversational")
                if response and len(response.strip()) > 0:
                    return response.strip()
            except Exception as e:
                logger.warning(f"Error generando mensaje con IA: {e}")
            
            # Fallback si IA falla
            if candidate_name and campaign_name:
                response = f"¡Hola! Bienvenido a la campaña de {candidate_name} - {campaign_name}."
            elif candidate_name:
                response = f"¡Hola! Bienvenido a la campaña de {candidate_name}."
            elif campaign_name:
                response = f"¡Hola! Bienvenido a {campaign_name}."
            else:
                response = "¡Hola! Bienvenido a nuestra campaña."
            
            return response.strip()
                
        except Exception as e:
            logger.error(f"Error generando mensaje de bienvenida con IA: {str(e)}")
            return "¡Hola! Te doy la bienvenida a nuestra campaña. ¡Es un placer conocerte!"

    async def generate_contact_save_message(self, tenant_config: Dict[str, Any] = None) -> str:
        """
        Genera un mensaje para pedir al usuario que guarde el contacto usando IA
        
        Args:
            tenant_config: Configuración del tenant (opcional)
            
        Returns:
            Mensaje para guardar contacto generado por IA
        """
        try:
            # Obtener nombre del contacto desde la configuración
            contact_name = "Contacto"
            if tenant_config:
                branding = tenant_config.get('branding', {})
                if branding:
                    config_contact_name = branding.get('contact_name', '')
                    if config_contact_name and config_contact_name.strip():
                        contact_name = config_contact_name.strip()
            
            # Generar mensaje con IA usando el método que sí funciona
            prompt = f"""Genera un mensaje para WhatsApp pidiendo guardar el contacto como "{contact_name}".

El mensaje debe ser educado y explicar por qué es importante. Máximo 150 caracteres.

Mensaje:"""

            try:
                response = await self._generate_content(prompt, task_type="chat_conversational")
                if response and len(response.strip()) > 0:
                    return response.strip()
            except Exception as e:
                logger.warning(f"Error generando mensaje con IA: {e}")
            
            # Fallback si IA falla
            response = f"Por favor, guarda este número como '{contact_name}' para recibir actualizaciones importantes de la campaña."
            
            return response.strip()
                
        except Exception as e:
            logger.error(f"Error generando mensaje de guardar contacto con IA: {str(e)}")
            return f"Te pido que lo primero que hagas sea guardar este número con el nombre: {contact_name}"

    async def generate_all_initial_messages(self, tenant_config: Dict[str, Any] = None, tenant_id: str = None) -> Dict[str, str]:
        """
        Genera los 3 mensajes iniciales de una vez para optimizar el tiempo de respuesta
        AHORA CARGA DESDE DB SI EXISTEN
        
        Args:
            tenant_config: Configuración del tenant (opcional)
            tenant_id: ID del tenant para cargar desde DB
            
        Returns:
            Diccionario con los 3 mensajes generados
        """
        try:
            # 🗄️ PRIORIDAD 1: Intentar cargar prompts desde DB
            if tenant_id:
                prompts_from_db = self.persistence_service.get_tenant_prompts(tenant_id)
                if prompts_from_db:
                    # 🔧 FIX: Validar que la estructura es correcta (welcome, contact, name)
                    required_keys = ['welcome', 'contact', 'name']
                    if all(key in prompts_from_db for key in required_keys):
                        logger.info(f"✅ Usando prompts desde DB para tenant {tenant_id}: {len(prompts_from_db)} prompts")
                        return prompts_from_db
                    else:
                        logger.warning(f"⚠️ Prompts en DB tienen estructura incorrecta para tenant {tenant_id}")
                        logger.warning(f"   Ubicación en DB: Collection='tenant_prompts', Document='{tenant_id}', Field='prompts'")
                        logger.warning(f"   Estructura actual en DB: {list(prompts_from_db.keys())}")
                        logger.warning(f"   Contenido actual: {prompts_from_db}")
                        logger.warning(f"   Estructura esperada: {required_keys}")
                        logger.info(f"🔄 Regenerando mensajes con estructura correcta...")
                        logger.info(f"📝 Los nuevos mensajes se guardarán sobrescribiendo la estructura incorrecta")
                        # Continuar para regenerar los mensajes
                else:
                    logger.info(f"ℹ️ No hay prompts en DB para tenant {tenant_id}, generando nuevos")
            
            # 🔍 DEBUG: Log para ver qué se recibe
            logger.info(f"🔍 DEBUG generate_all_initial_messages: tenant_config recibido: {tenant_config}")
            
            # 🚀 OPTIMIZACIÓN: Usar respuestas precomputadas para casos comunes
            candidate_name = ""
            contact_name = "Mi Candidato"
            branding = {}
            
            if tenant_config:
                branding = tenant_config.get('branding', {}) or {}
                logger.info(f"🔍 DEBUG: branding extraído: {branding}")
                if branding:
                    candidate_name = branding.get('candidate_name', '')
                    config_contact_name = branding.get('contact_name', '')
                    logger.info(f"🔍 DEBUG: candidate_name='{candidate_name}', contact_name='{config_contact_name}'")
                    if config_contact_name and config_contact_name.strip():
                        contact_name = config_contact_name.strip()
            
            # 🚀 PERSONALIZACIÓN: Usar mensajes del branding si están disponibles
            personalized_messages = self._precomputed_initial_messages["default"].copy()
            
            # Verificar si hay un mensaje de bienvenida personalizado en el branding
            if branding and isinstance(branding, dict):
                welcome_message = branding.get('welcome_message', '')
                if welcome_message and welcome_message.strip():
                    logger.info(f"✅ Usando mensaje de bienvenida personalizado del branding")
                    # Reemplazar variables en el mensaje
                    welcome_message = welcome_message.strip()
                    # Reemplazar {candidate_name} o {CANDIDATE_NAME} con el nombre del candidato
                    if candidate_name and candidate_name.strip():
                        welcome_message = welcome_message.replace("{candidate_name}", candidate_name)
                        welcome_message = welcome_message.replace("{CANDIDATE_NAME}", candidate_name)
                    # Reemplazar {campaign_name} si está disponible
                    campaign_name = branding.get('campaign_name', '')
                    if campaign_name and campaign_name.strip():
                        welcome_message = welcome_message.replace("{campaign_name}", campaign_name)
                        welcome_message = welcome_message.replace("{CAMPAIGN_NAME}", campaign_name)
                    # Reemplazar \n por saltos de línea reales
                    welcome_message = welcome_message.replace("\\n", "\n")
                    welcome_message = welcome_message.replace("\\t", "\t")
                    personalized_messages['welcome'] = welcome_message
                elif candidate_name and candidate_name.strip():
                    # Si no hay welcome_message pero sí candidate_name, personalizar el mensaje genérico
                    logger.info(f"🚀 Personalizando mensaje genérico con nombre del candidato: {candidate_name}")
                    personalized_messages['welcome'] = personalized_messages['welcome'].replace("tu candidato", candidate_name)
                    personalized_messages['welcome'] = personalized_messages['welcome'].replace("tu representante", candidate_name)
            
            # Verificar si hay un mensaje de contacto personalizado
            if branding and isinstance(branding, dict):
                contact_message = branding.get('greeting_message', '')
                # Si no hay greeting_message, personalizar el genérico con contact_name
                if not contact_message or not contact_message.strip():
                    if contact_name and contact_name.strip() and contact_name != "Mi Candidato":
                        logger.info(f"📝 Personalizando mensaje de contacto con: {contact_name}")
                        personalized_messages['contact'] = personalized_messages['contact'].replace("Mi Candidato", contact_name)
                else:
                    # Si hay greeting_message, usarlo (aunque no es exactamente el mismo propósito)
                    logger.info(f"✅ Usando mensaje de saludo del branding")
            
            return personalized_messages
                
        except Exception as e:
            logger.error(f"Error generando mensajes iniciales: {str(e)}")
            # Usar respuestas genéricas como último recurso
            return self._precomputed_initial_messages["default"].copy()

    async def generate_name_request_message(self, tenant_config: Dict[str, Any] = None) -> str:
        """
        Genera un mensaje para pedir el nombre del usuario usando IA
        
        Args:
            tenant_config: Configuración del tenant (opcional)
            
        Returns:
            Mensaje para pedir nombre generado por IA
        """
        try:
            # Generar mensaje con IA usando el método que sí funciona
            prompt = f"""Genera un mensaje para WhatsApp pidiendo el nombre del usuario.

El mensaje debe ser amigable y explicar por qué necesitas el nombre. Máximo 120 caracteres.

Mensaje:"""

            try:
                response = await self._generate_content(prompt, task_type="chat_conversational")
                if response and len(response.strip()) > 0:
                    return response.strip()
            except Exception as e:
                logger.warning(f"Error generando mensaje con IA: {e}")
            
            # Fallback si IA falla
            response = "¿Me confirmas tu nombre para guardarte en mis contactos y personalizar tu experiencia?"
            
            return response.strip()
                
        except Exception as e:
            logger.error(f"Error generando mensaje de pedir nombre con IA: {str(e)}")
            return "¿Me confirmas tu nombre para guardarte en mis contactos?"
    
    def _enhance_query_for_document_search(self, query: str) -> str:
        """
        Mejora la query para mejor recuperación de documentos
        Añade sinónimos y términos relacionados relevantes
        """
        query_lower = query.lower()
        
        # Sinónimos y términos relacionados genéricos
        synonym_map = {
            "culpable": ["responsable", "autor", "involucrado", "implicado"],
            "responsable": ["culpable", "autor", "involucrado", "implicado"],
        }
        
        enhanced_query = query
        
        # Añadir sinónimos relevantes
        for key, synonyms in synonym_map.items():
            if key in query_lower:
                enhanced_query += " " + " ".join(synonyms)
                break
        
        return enhanced_query
    
    def _is_content_relevant(self, query: str, content: str) -> bool:
        """
        Verifica si el contenido es relevante para la query
        """
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Extraer palabras clave importantes de la query
        query_words = set(query_lower.split())
        
        # Filtrar palabras muy comunes
        stop_words = {'de', 'la', 'el', 'en', 'y', 'a', 'que', 'es', 'un', 'una', 'por', 'con', 'para', 'su', 'los', 'las', 'le', 'se', 'del', 'al', 'lo', 'como', 'si', 'son', 'están', 'más', 'cuál', 'cuáles', 'qué', 'quién', 'quiénes', 'es', 'son', 'está', 'están', 'hay', 'ser', 'está'}
        important_words = query_words - stop_words
        
        # Verificar si al menos algunas palabras importantes están en el contenido
        if len(important_words) == 0:
            return True  # No hay palabras importantes, asumir relevante
        
        matches = sum(1 for word in important_words if word in content_lower)
        relevance_score = matches / len(important_words) if important_words else 0
        
        # Considerar relevante si al menos el 20% de las palabras importantes coinciden
        # Reducido a 20% para ser más permisivo
        is_relevant = relevance_score >= 0.2
        
        logger.info(f"🔍 DEBUG RELEVANCIA: query_words={important_words}, matches={matches}, score={relevance_score:.2f}, relevante={is_relevant}")
        logger.info(f"🔍 DEBUG RELEVANCIA: Preview content: {content_lower[:200]}...")
        
        return is_relevant

# Instancia global para compatibilidad
ai_service = AIService()
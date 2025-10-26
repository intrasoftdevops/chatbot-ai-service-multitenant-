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
    
    def _get_safety_settings(self):
        """
        Obtiene los safety settings configurados para permitir contenido político
        """
        # 🚀 CONFIGURACIÓN SIMPLE: Sin safety settings explícitos (como versión anterior)
        return None
        
        # 🚀 OPTIMIZACIÓN: Cache para validaciones comunes
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
                "pastata": {"is_valid": True, "confidence": 0.95, "reason": "Ciudad colombiana válida"},
            }
        }
        
        # Servicio para notificar bloqueos
        self.blocking_notification_service = BlockingNotificationService()
        # Configurar URL del servicio Java desde variable de entorno
        java_service_url = os.getenv("POLITICAL_REFERRALS_SERVICE_URL")
        if java_service_url:
            self.blocking_notification_service.set_java_service_url(java_service_url)
        else:
            logger.warning("POLITICAL_REFERRALS_SERVICE_URL no configurado - funcionalidad de bloqueo limitada")
        
        # 🔧 OPTIMIZACIÓN: Cache local para respuestas comunes
        # (Ya inicializado arriba, no duplicar)
        
        # 🚀 OPTIMIZACIÓN: Respuestas precomputadas genéricas para casos comunes
        self._precomputed_initial_messages = {
            "default": {
                'welcome': "¡Bienvenido/a! Soy tu candidato. ¡Juntos construimos el futuro!",
                'contact': "Por favor, guarda este número como 'Mi Candidato' para recibir actualizaciones importantes de la campaña.",
                'name': "¿Me confirmas tu nombre para guardarte en mis contactos y personalizar tu experiencia?"
            }
        }
        self._common_responses = {
            # Saludos comunes
            "hola": "saludo_apoyo",
            "hi": "saludo_apoyo", 
            "hello": "saludo_apoyo",
            "buenos días": "saludo_apoyo", 
            "buenas tardes": "saludo_apoyo",
            "buenas noches": "saludo_apoyo",
            "gracias": "saludo_apoyo",
            
            # Confirmaciones comunes
            "ok": "saludo_apoyo",
            "okay": "saludo_apoyo",
            "okey": "saludo_apoyo",
            "vale": "saludo_apoyo",
            "listo": "saludo_apoyo",
            "entendido": "saludo_apoyo",
            "perfecto": "saludo_apoyo",
            "bien": "saludo_apoyo",
            "si": "saludo_apoyo",
            "sí": "saludo_apoyo",
            "no": "saludo_apoyo",
            
            # Explicaciones sobre datos
            "solo puedo dar nombre y apellido": "registration_response",
            "solo puedo dar un nombre y un apellido": "registration_response",
            "puedo solo un nombre y un apellido": "registration_response",
            "solo tengo nombre y apellido": "registration_response",
            "no tengo ciudad": "registration_response",
            "no sé mi ciudad": "registration_response",
            "no conozco mi ciudad": "registration_response",
            
            # Nombres comunes
            "santiago": "registration_response",
            "juan": "registration_response",
            "maria": "registration_response",
            "carlos": "registration_response",
            "ana": "registration_response",
            "luis": "registration_response",
            "pedro": "registration_response",
            
            # Ciudades comunes
            "bogotá": "registration_response",
            "medellín": "registration_response",
            "cali": "registration_response",
            "barranquilla": "registration_response",
            "bogota": "registration_response",
            "medellin": "registration_response"
        }
        
        # 🔧 OPTIMIZACIÓN: Bypass completo de Gemini para casos comunes
        self.bypass_gemini = True
        
        # 🔧 OPTIMIZACIÓN: Configuración de rendimiento para Gemini
        self.gemini_performance_config = {
            "temperature": 0.1,  # Más determinístico y rápido
            "top_p": 0.8,        # Reducir opciones para velocidad
            "top_k": 20,         # Limitar tokens para velocidad
            "max_output_tokens": 100,  # Respuestas más cortas
            "candidate_count": 1  # Solo una respuesta
        }
        
        # [COHETE] FASE 1: Feature flag para usar GeminiClient
        # Permite migración gradual sin romper funcionalidad existente
        # 🚀 OPTIMIZACIÓN: Habilitado por defecto para usar pre-carga de modelos
        self.use_gemini_client = os.getenv("USE_GEMINI_CLIENT", "true").lower() == "true"
        self.gemini_client = None
        
        if self.use_gemini_client:
            logger.info("[OK] GeminiClient habilitado via feature flag USE_GEMINI_CLIENT=true")
            # La inicialización se hace de forma lazy en _ensure_gemini_client()
            
        # La pre-carga se hará después de cargar las variables de entorno
        
        # [COHETE] FASE 2: Feature flag para usar configuraciones avanzadas por tarea
        # Permite optimizar temperatura, top_p, etc. según el tipo de tarea
        # 🚀 OPTIMIZACIÓN: Habilitado por defecto para usar pre-carga optimizada
        self.use_advanced_model_configs = os.getenv("USE_ADVANCED_MODEL_CONFIGS", "true").lower() == "true"
        
        if self.use_advanced_model_configs and self.use_gemini_client:
            logger.info("[OK] Configuraciones avanzadas de modelo habilitadas (USE_ADVANCED_MODEL_CONFIGS=true)")
        elif self.use_advanced_model_configs and not self.use_gemini_client:
            logger.warning("[ADVERTENCIA] USE_ADVANCED_MODEL_CONFIGS=true pero USE_GEMINI_CLIENT=false. Las configs avanzadas requieren GeminiClient.")
            self.use_advanced_model_configs = False
        
        # [COHETE] FASE 6: Feature flag para usar RAGOrchestrator
        # Habilita el sistema completo de RAG con búsqueda híbrida y verificación
        self.use_rag_orchestrator = os.getenv("USE_RAG_ORCHESTRATOR", "false").lower() == "true"
        self.rag_orchestrator = None
        
        # [ESCUDO] FASE 5: Feature flag para guardrails estrictos
        # Habilita prompts especializados y verificación estricta de respuestas
        self.use_guardrails = os.getenv("USE_GUARDRAILS", "true").lower() == "true"
        self.strict_guardrails = os.getenv("STRICT_GUARDRAILS", "true").lower() == "true"
    
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
            if self.use_gemini_client and self.gemini_client is None:
                print("🚀 DEBUG ULTRA-FAST: gemini_client es None, reinicializando...")
                self._ensure_gemini_client()
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
                    # La IA se encarga de entender el contexto y responder apropiadamente
                    contact_name = "el candidato"  # Valor por defecto
                    print(f"🤖 ANTES de llamar a _generate_immediate_document_response")
                    print(f"🤖 query: '{query[:100]}...'")
                    print(f"🤖 document_content: {len(document_content)} caracteres")
                    response = await self._generate_immediate_document_response(query, document_content, contact_name)
                    print(f"🤖 DESPUÉS de llamar a _generate_immediate_document_response")
                    print(f"🤖 RESPUESTA INMEDIATA GENERADA: {response[:200]}...")
                    return response
                else:
                    print("🔍 DEBUG: No hay documentos disponibles, usando fallback")
                    return "No tengo información suficiente sobre ese tema. Puedo ayudarte con otros temas de la campaña."
            
            # 🚀 FALLBACK: Usar Gemini si no hay documentos o no es ultra-fast mode
            if self.use_gemini_client and self.gemini_client:
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

    async def _generate_immediate_document_response(self, query: str, document_content: str, contact_name: str) -> str:
        """
        Genera respuesta inmediata basada en documentos usando IA
        Respeta la conciencia individual de cada tenant
        """
        try:
            # Extraer información relevante del documento
            content_lower = document_content.lower()
            query_lower = query.lower()
            
            print(f"🔍 DEBUG IMMEDIATE: query_lower = '{query_lower}'")
            print(f"🔍 DEBUG IMMEDIATE: content_lower preview = '{content_lower[:200]}...'")
            
            # Limpiar el contenido para la IA (remover nombres de archivos y caracteres especiales)
            import re
            clean_content = document_content.replace('*', '').replace('\n', ' ')
            clean_content = re.sub(r'\s*\([^)]*\.pdf\)\s*', ' ', clean_content, flags=re.IGNORECASE)
            clean_content = re.sub(r'\.pdf', ' ', clean_content, flags=re.IGNORECASE)
            
            # Crear prompt para que la IA genere respuesta corta y natural
            print(f"🔍 DEBUG: Creando summary_prompt con contact_name={contact_name}...")
            try:
                summary_prompt = f"""
Responde la siguiente pregunta de forma breve y concisa (máximo 800 caracteres):

Pregunta: {query}

Información disponible:
{clean_content[:2000]}

INSTRUCCIONES CRÍTICAS: 
- NO menciones nombres de archivos o documentos
- NO digas "según el documento" o "en el documento"
- NO uses la frase genérica "el candidato" bajo ninguna circunstancia
- Si en la información hay nombres específicos (personas, entidades), ÚSALOS directamente
- Si la pregunta menciona "el responsable", "el candidato" o similares, busca el NOMBRE ESPECÍFICO en la información y úsalo
- Responde como si fueras un experto en el tema que conoce la información de primera mano
- Sé específico: usa nombres reales, fechas, lugares exactos
- Máximo 800 caracteres
- Responde la pregunta directamente y con precisión

Ejemplo de lo que NO debes hacer:
❌ "El candidato propuso..."
✅ "Federico Gutiérrez propuso..." (si ese es el nombre en la información)

Respuesta:"""
                print(f"🔍 DEBUG: summary_prompt creado exitosamente: {len(summary_prompt)} caracteres")
            except Exception as prompt_error:
                print(f"🔍 DEBUG: ERROR creando summary_prompt: {prompt_error}")
                import traceback
                traceback.print_exc()
                raise
            
            # Usar IA disponible para generar respuesta
            print(f"🔍 DEBUG: ¿use_gemini_client? {self.use_gemini_client}")
            print(f"🔍 DEBUG: ¿gemini_client disponible? {self.gemini_client is not None}")
            if self.use_gemini_client and self.gemini_client:
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
            if self.use_gemini_client and self.gemini_client:
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
            if self.use_gemini_client and self.gemini_client:
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
            if self.use_gemini_client and self.gemini_client:
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
        
        # 🚀 DEBUG: Verificar variables al inicio del procesamiento
        import os
        ultra_fast_mode = os.getenv("ULTRA_FAST_MODE", "false").lower() == "true"
        is_local_dev = os.getenv("LOCAL_DEVELOPMENT", "false").lower() == "true"
        print(f"🚀 DEBUG PROCESAMIENTO - ULTRA_FAST_MODE: {ultra_fast_mode}")
        print(f"🚀 DEBUG PROCESAMIENTO - LOCAL_DEVELOPMENT: {is_local_dev}")
        
        start_time = time.time()
        
        # Inicializar followup_message para evitar errores de None
        followup_message = ""
        
        try:
            logger.info(f"Procesando mensaje para tenant {tenant_id}, sesión: {session_id}")
            logger.info(f"🔍 DEBUG: Iniciando process_chat_message - query: '{query}', tenant_id: {tenant_id}")
            
            # 🚀 NUEVO: Usar directamente el sistema de documentos que funciona
            logger.info(f"🔍 DEBUG: ¿Entrando en ultra_fast_mode? {ultra_fast_mode}")
            if ultra_fast_mode:
                logger.info(f"🚀 ULTRA-FAST MODE: Usando sistema de documentos directo")
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
                    contact_name = "el candidato"  # Valor por defecto
                    if tenant_config and tenant_config.get("branding_config"):
                        contact_name = tenant_config["branding_config"].get("contactName", "el candidato")
                    
                    # Usar el query completo (con historial) para que la IA tenga contexto
                    response = await self._generate_immediate_document_response(query, document_content, contact_name)
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
                    logger.info(f"🔍 DEBUG: No hay documentos disponibles, usando fallback")
                    return {
                        "response": "Sobre este tema, tengo información específica que te puede interesar. Te puedo ayudar a conectarte con nuestro equipo para obtener más detalles.",
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
            
            # Clasificar la intencion del mensaje usando IA (pero con contexto precargado)
            logger.info(f"🔍 DEBUG: Clasificando intención...")
            try:
                classification_result = await self.classify_intent(tenant_id, query, user_context, session_id, tenant_config)
                intent = classification_result.get("category", "saludo_apoyo").strip()
                confidence = classification_result.get("confidence", 0.0)
                logger.info(f"🔍 DEBUG: Intención clasificada: '{intent}' con confianza: {confidence}")
            except Exception as e:
                logger.error(f"❌ ERROR en clasificación de intención: {str(e)}")
                intent = "saludo_apoyo"
                confidence = 0.5
                logger.info(f"🔍 DEBUG: Usando intención por defecto: '{intent}'")
            
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
            
            # 🔧 PRIORIDAD 1: DETECCIÓN DE MENSAJES MALICIOSOS (incluso durante registro)
            malicious_detection = self._detect_malicious_intent(query)
            if malicious_detection and malicious_detection.get("is_malicious", False):
                logger.warning(f"🚫 Mensaje malicioso detectado durante registro: {malicious_detection}")
                # Manejar comportamiento malicioso inmediatamente
                return await self._handle_malicious_message(tenant_id, query, user_context, malicious_detection, session_id)
            
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
            logger.info(f"🔍 DESPUÉS DE CLASIFICACIÓN - intent: '{intent}'")
            logger.info(f"🔍 JUSTO DESPUÉS DEL PRINT - intent: '{intent}'")
            logger.info(f"🔍 INICIANDO BLOQUE RAG")
            logger.info(f"🔍 DEBUG: Llegando al bloque RAG - intent: '{intent}'")
            logger.info(f"🔍 DEBUG: ANTES DE CUALQUIER PROCESAMIENTO - intent: '{intent}'")
            logger.info(f"🔍 DEBUG: Continuando con el flujo normal...")
            
            # RAG con orden correcto: primero documentos, luego fallback
            document_context = None
            logger.info(f"🔍 ANTES DEL BLOQUE RAG - intent: '{intent}'")
            
            try:
                # Consultar documentos para intenciones que requieren información específica
                intents_requiring_docs = ["conocer_candidato", "solicitud_funcional", "pregunta_especifica", "consulta_propuesta"]
                
                if intent in intents_requiring_docs:
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
                    logger.info(f"[OBJETIVO] Intención '{intent}' no requiere documentos, saltando carga")
            except Exception as e:
                logger.error(f"❌ ERROR en bloque RAG: {str(e)}")
                document_context = "gemini_direct"
            
            logger.info(f"🔍 DESPUÉS DEL BLOQUE RAG - intent: '{intent}'")
            logger.info(f"🧠 Intención extraída: {intent} (confianza: {confidence:.2f})")
            logger.info(f"🔍 DEBUG: Continuando con procesamiento de intención...")
            logger.info(f"🔍 DEBUG: Llegando al bloque de procesamiento de intención")
            logger.info(f"🔍 DEBUG: document_context = '{document_context}'")
            logger.info(f"🔍 DEBUG: ANTES DE CACHÉ - intent: '{intent}'")
            
            # 1.5 NUEVO: Intentar obtener respuesta del caché
            logger.info(f"🔍 ANTES DE cache_service.get_cached_response")
            cached_response = cache_service.get_cached_response(
                tenant_id=tenant_id,
                query=query,
                intent=intent
            )
            
            if cached_response:
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
            
            # OPTIMIZACIÓN 3: Respuestas rápidas para casos comunes
            logger.debug(f"[LUP] VERIFICANDO INTENT: {intent}")
            
            # Obtener contexto de sesión para todas las respuestas
            logger.info(f"🔍 ANTES DE session_context_service.build_context_for_ai")
            session_context = session_context_service.build_context_for_ai(session_id)
            logger.info(f"🔍 DESPUÉS DE session_context_service.build_context_for_ai")
            
            # 🚀 OPTIMIZACIÓN: Intentar respuesta rápida con IA pero usando contexto precargado
            tenant_context = user_context.get('tenant_context', {})
            logger.info(f"🔍 DEBUG: tenant_context obtenido: {bool(tenant_context)}")
            logger.info(f"🔍 DEBUG: intent: '{intent}'")
            if tenant_context and intent in ["saludo_apoyo"]:
                logger.info(f"🔍 DEBUG: USANDO RESPUESTA RÁPIDA CON IA - saltando RAG")
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
                    response = self._handle_appointment_request_with_context(branding_config, tenant_config, session_context)
                elif intent == "saludo_apoyo":
                    logger.info(f"[OBJETIVO] RESPUESTA RÁPIDA: saludo_apoyo")
                    response = self._get_greeting_response_with_context(branding_config, session_context)
                elif intent == "colaboracion_voluntariado":
                    logger.info(f"[OBJETIVO] RESPUESTA RÁPIDA: colaboracion_voluntariado")
                    response = self._get_volunteer_response_with_context(branding_config, session_context)
                elif intent == "solicitud_funcional":
                    logger.info(f"🔍 LLEGANDO AL BLOQUE solicitud_funcional - intent: '{intent}'")
                    # Respuesta específica para consultas funcionales con contexto de sesión
                    logger.info(f"🎯 PROCESANDO solicitud_funcional - llamando _handle_functional_request_with_session")
                    result = await self._handle_functional_request_with_session(
                        query, user_context, ai_config, branding_config, tenant_id, session_id
                    )
                    
                    # Manejar el nuevo formato de respuesta (puede ser string o tupla)
                    if isinstance(result, tuple):
                        response, followup_message = result
                        logger.info(f"🎯 RESPUESTA GENERADA para solicitud_funcional: {len(response)} caracteres")
                        logger.info(f"🎯 FOLLOWUP_MESSAGE generado: {len(followup_message) if followup_message else 0} caracteres")
                    else:
                        response = result
                        followup_message = ""
                        logger.info(f"🎯 RESPUESTA GENERADA para solicitud_funcional: {len(response)} caracteres")
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
            
            # Filtrar enlaces de la respuesta para WhatsApp (excepto citas)
            if intent == "cita_campaña":
                filtered_response = response  # No filtrar enlaces de Calendly
                logger.info("[CALENDARIO] Respuesta de cita - manteniendo enlaces de Calendly")
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
            
            logger.info(f"✅ DEVOLVIENDO RESPUESTA FINAL: {final_response}")
            return final_response
            
        except Exception as e:
            logger.error(f"Error procesando mensaje para tenant {tenant_id}: {str(e)}")
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
            
            # Mostrar el contenido completo del documento para debugging
            print(f"📄 CONTENIDO COMPLETO DEL DOCUMENTO:")
            print(f"📄 {document_context}")
            print(f"📄 LONGITUD: {len(document_context)} caracteres")
            
            # Truncar el contenido para acelerar Gemini (máximo 1500 caracteres para mayor velocidad)
            if len(document_context) > 1500:
                document_context = document_context[:1500] + "..."
                print(f"⚠️ CONTENIDO TRUNCADO para acelerar Gemini: {len(document_context)} caracteres")
            
            # El document_context ya contiene la información procesada por la IA
            # Solo necesitamos formatearla de manera más natural
            if document_context and document_context != "NO_ENCONTRADO":
                # Crear prompt ULTRA-OPTIMIZADO con contexto completo del usuario
                prompt = f"""Asistente virtual de {contact_name}. Responde de manera personalizada y profesional.

CONTEXTO COMPLETO DEL USUARIO:
{user_info}

INFORMACIÓN ESPECÍFICA SOBRE LA CONSULTA: {document_context}

CONSULTA: "{query}"

INSTRUCCIONES CRÍTICAS:
- **USA EXCLUSIVAMENTE** la información específica proporcionada arriba
- **NO INVENTES** información que no esté en el contenido proporcionado
- **RESPONDE DIRECTAMENTE** basándote en los datos específicos del documento
- **PERSONALIZA** tu respuesta usando el nombre del usuario si está disponible
- **MENCIÓN** su ciudad si es relevante para la respuesta
- Máximo 999 caracteres
- Mantén un tono profesional y cercano
- Si la información específica no responde completamente la consulta, dilo claramente

RESPUESTA BASADA EN LA INFORMACIÓN ESPECÍFICA:"""
                
                # 🚀 OPTIMIZACIÓN CRÍTICA: Respuesta inmediata basada en documentos sin Gemini
                # Solo cuando ULTRA_FAST_MODE está activo
                import os
                ultra_fast_mode = os.getenv("ULTRA_FAST_MODE", "false").lower() == "true"
                is_local_dev = os.getenv("LOCAL_DEVELOPMENT", "false").lower() == "true"
                logger.info(f"🚀 ULTRA_FAST_MODE detectado en respuesta: {ultra_fast_mode}")
                logger.info(f"🚀 LOCAL_DEVELOPMENT detectado en respuesta: {is_local_dev}")
                
                if ultra_fast_mode:
                    # Obtener contenido de documentos para respuesta inmediata
                    document_content = await document_context_service.get_relevant_context(tenant_id, query, max_results=1)
                    print(f"🔍 DEBUG: document_content obtenido: {len(document_content) if document_content else 0} caracteres")
                    print(f"🔍 DEBUG: document_content preview: {document_content[:200] if document_content else 'None'}...")
                    
                    if document_content:
                        response = await self._generate_immediate_document_response(query, document_content, contact_name)
                        print(f"🤖 RESPUESTA INMEDIATA GENERADA: {response[:200]}...")
                    else:
                        # Fallback si no hay documentos
                        response = f"Sobre este tema, {contact_name} tiene información específica que te puede interesar. Te puedo ayudar a conectarte con nuestro equipo para obtener más detalles."
                        print(f"🤖 RESPUESTA FALLBACK GENERADA: {response[:200]}...")
                else:
                    # Usar Gemini normal cuando ULTRA_FAST_MODE está inactivo
                    response = await self._generate_content_with_documents(prompt, document_content)
                    print(f"🤖 RESPUESTA GEMINI GENERADA: {response[:200]}...")
                
                # 🚀 OPTIMIZACIÓN: Guardar en caché por tenant (respeta conciencia individual)
                tenant_cache_key = f"{tenant_id}:{cache_key}"
                self._response_cache[tenant_cache_key] = response
                
                return response
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
    
    def _truncate_response_intelligently(self, text: str, max_length: int) -> str:
        """Trunca el texto de forma inteligente, buscando un punto de corte natural"""
        if len(text) <= max_length:
            return text
        
        # Buscar el mejor punto de corte antes del límite
        search_length = min(max_length - 10, len(text))  # Dejar espacio para "..."
        
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
            return truncated
        else:
            # Si no se encuentra un buen punto de corte, cortar en el límite exacto sin "..."
            return text[:max_length]
    
    def _filter_links_from_response(self, response: str, intent: str = None) -> str:
        """
        Elimina completamente enlaces y referencias a enlaces de las respuestas para WhatsApp
        EXCEPTO enlaces de Calendly cuando la intención es cita_campaña
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
                                                    tenant_id: str, session_id: str) -> str:
        """Maneja solicitudes funcionales con contexto de sesión para respuestas más naturales"""
        try:
            logger.info(f"🔧 INICIANDO _handle_functional_request_with_session para query: '{query}'")
            logger.info(f"🔧 Parámetros recibidos:")
            logger.info(f"🔧   - query: {query}")
            logger.info(f"🔧   - tenant_id: {tenant_id}")
            logger.info(f"🔧   - session_id: {session_id}")
            logger.info(f"🔧   - user_context: {user_context}")
            
            # Obtener contexto de sesión
            session_context = session_context_service.build_context_for_ai(session_id)
            logger.info(f"📝 Contexto de sesión obtenido: {len(session_context) if session_context else 0} elementos")
            
            # Obtener nombre del contacto desde branding_config
            contact_name = branding_config.get("contact_name", branding_config.get("contactName", "el candidato"))
            logger.info(f"👤 Nombre del contacto: {contact_name}")
            
            # Intentar obtener datos reales del usuario
            logger.info(f"🔍 Obteniendo datos del usuario para tenant: {tenant_id}")
            logger.info(f"🔍 user_context recibido: {user_context}")
            user_data = self._get_user_progress_data(tenant_id, user_context)
            logger.info(f"📊 Datos del usuario obtenidos: {bool(user_data)}")
            logger.info(f"📊 Tipo de user_data: {type(user_data)}")
            
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
                referral_code = user_data.get("referral_code")
                
                logger.info(f"🔍 Datos del usuario procesados:")
                logger.info(f"🔍   - user_name: {user_name}")
                logger.info(f"🔍   - points: {points}")
                logger.info(f"🔍   - total_referrals: {total_referrals}")
                logger.info(f"🔍   - referral_code: {referral_code}")
                
                # Verificar si es solicitud de enlace y generar respuesta directa
                query_lower = query.lower().strip()
                link_keywords = ["link", "código", "codigo", "referido", "mandame", "dame", "enlace", "compartir", "comparte", "envia", "envía", "link", "url", "mi enlace", "mi código", "mi codigo"]
                
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
                
                if is_link_request:
                    logger.info(f"🔗 NUEVO ENFOQUE: Detectada solicitud de enlace - generando respuesta con followup_message")
                    
                    # Generar enlace de WhatsApp
                    whatsapp_link = self._generate_whatsapp_referral_link(user_name, referral_code, contact_name, tenant_id, user_context)
                    
                    if whatsapp_link:
                        # Generar respuesta principal sin enlace
                        points = user_data.get("points", 0)
                        total_referrals = user_data.get("total_referrals", 0)
                        completed_referrals = user_data.get("completed_referrals", [])
                        
                        response = f"""¡Claro que sí, {user_name}! 🚀 Aquí tienes la información para que sigas sumando más personas a la campaña de {contact_name}:

📊 **Tu progreso actual:**
- Puntos: {points}
- Referidos completados: {len(completed_referrals)}
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
                
                # Crear prompt contextualizado con datos reales
                contextual_prompt = self._build_functional_prompt_with_data(
                    query, user_context, branding_config, session_context, user_data, tenant_id
                )
                
                # Generar respuesta con IA usando el contexto
                response_text = await self._generate_content(contextual_prompt, task_type="functional_with_data")
                
                logger.info(f"🔧 RETORNANDO respuesta desde _handle_functional_request_with_session (fallback)")
                return response_text
            else:
                # Fallback: usar respuesta genérica pero con contexto de sesión
                contextual_prompt = self._build_functional_prompt_generic(
                    query, user_context, branding_config, session_context
                )
                
                response_text = await self._generate_content(contextual_prompt, task_type="functional_generic")
                logger.info(f"🔧 RETORNANDO respuesta desde _handle_functional_request_with_session (genérico)")
                return response_text
                
        except Exception as e:
            logger.error(f"Error manejando solicitud funcional con sesión: {str(e)}")
            # Fallback a respuesta básica
            return self._handle_functional_request(query, branding_config, tenant_id, user_context)
    
    def _build_functional_prompt_with_data(self, query: str, user_context: Dict[str, Any], 
                                         branding_config: Dict[str, Any], session_context: str, 
                                         user_data: Dict[str, Any], tenant_id: str = None) -> str:
        """Construye un prompt contextualizado con datos reales del usuario"""
        contact_name = branding_config.get("contactName", "el candidato")
        user = user_data.get("user", {})
        points = user_data.get("points", 0)
        total_referrals = user_data.get("total_referrals", 0)
        completed_referrals = user_data.get("completed_referrals", [])
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
- Referidos completados: {len(completed_referrals)}
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
            whatsapp_link = self._generate_whatsapp_referral_link(user_name, referral_code, contact_name, tenant_id, user_context)
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
            response = f"""¡Claro que sí, {user_name}! 🚀 Aquí tienes la información para que sigas sumando más personas a la campaña de {contact_name}:

📊 **Tu progreso actual:**
- Puntos: {points}
- Referidos completados: {len(completed_referrals)}
- Total de referidos: {total_referrals}
- Tu código: {referral_code}

¡Vamos con toda, {user_name}! Con tu ayuda, llegaremos a más rincones de Colombia. 💪🇨🇴"""

            if has_followup_link:
                logger.info(f"🔁 Se enviará segundo mensaje con enlace (len={len(whatsapp_link)})")
                response += "\n\nEn el siguiente mensaje te envío tu enlace para compartir."
            
            # Agregar información especial para el segundo mensaje solo si hay enlace
            if has_followup_link and whatsapp_link.strip():
                response += f"\n\n<<<FOLLOWUP_MESSAGE_START>>>{whatsapp_link}<<<FOLLOWUP_MESSAGE_END>>>"
                logger.info(f"✅ Marcador FOLLOWUP_MESSAGE agregado con enlace válido")
                logger.info(f"🔗 Enlace completo en marcador: {whatsapp_link}")
            else:
                logger.warning(f"⚠️ No se agregó marcador FOLLOWUP_MESSAGE - enlace vacío o inválido")
                logger.warning(f"⚠️ has_followup_link: {has_followup_link}, whatsapp_link: '{whatsapp_link}'")
            
            logger.info(f"✅ Respuesta directa generada con seguimiento para {user_name}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error generando respuesta directa con seguimiento: {str(e)}")
            return f"¡Hola {user_name}! Tu código de referido es: {referral_code}"
    
    def _generate_direct_link_response(self, user_name: str, referral_code: str, contact_name: str, tenant_id: str, user_data: Dict[str, Any], user_context: Dict[str, Any] = None) -> str:
        """Genera una respuesta directa con el enlace de WhatsApp cuando se solicita"""
        try:
            # Generar enlace de WhatsApp
            whatsapp_link = self._generate_whatsapp_referral_link(user_name, referral_code, contact_name, tenant_id, user_context)
            
            if not whatsapp_link:
                logger.error("❌ No se pudo generar enlace de WhatsApp")
                return f"¡Hola {user_name}! Tu código de referido es: {referral_code}"
            
            # Obtener datos adicionales
            points = user_data.get("points", 0)
            total_referrals = user_data.get("total_referrals", 0)
            completed_referrals = user_data.get("completed_referrals", [])
            
            # Generar respuesta directa con enlace
            response = f"""¡Claro que sí, {user_name}! 🚀 Aquí tienes tu enlace de WhatsApp personalizado para que sigas sumando más personas a la campaña de {contact_name}:

📊 **Tu progreso actual:**
- Puntos: {points}
- Referidos completados: {len(completed_referrals)}
- Total de referidos: {total_referrals}
- Tu código: {referral_code}

¡Vamos con toda, {user_name}! Con tu ayuda, llegaremos a más rincones de Colombia. 💪🇨🇴

En el siguiente mensaje te envío tu enlace para compartir."""
            
            logger.info(f"✅ Respuesta directa generada con enlace para {user_name}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error generando respuesta directa: {str(e)}")
            return f"¡Hola {user_name}! Tu código de referido es: {referral_code}"
    
    def _generate_whatsapp_referral_link(self, user_name: str, referral_code: str, contact_name: str, tenant_id: str = None, user_context: Dict[str, Any] = None) -> str:
        """Genera un enlace de WhatsApp personalizado para referidos"""
        try:
            # Obtener número de WhatsApp del tenant desde memoria precargada
            tenant_context = user_context.get('tenant_context', {}) if user_context else {}
            tenant_config = tenant_context.get('tenant_config', {})
            whatsapp_number = self._get_tenant_whatsapp_number(tenant_id, tenant_config)
            # Validar número
            if not whatsapp_number or not str(whatsapp_number).strip():
                logger.warning("⚠️ No hay numero_whatsapp configurado para el tenant; no se generará enlace")
                return ""
            
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
                    # Aceptar claves alternativas por compatibilidad
                    whatsapp_number = None
                    if "numero_whatsapp" in tenant_config:
                        whatsapp_number = tenant_config.get("numero_whatsapp")
                        logger.info(f"📱 Encontrado numero_whatsapp: {whatsapp_number}")
                    elif "whatsapp_number" in tenant_config:
                        whatsapp_number = tenant_config.get("whatsapp_number")
                        logger.info(f"📱 Encontrado whatsapp_number: {whatsapp_number}")

                    if whatsapp_number and str(whatsapp_number).strip():
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
            
            # Consultar usuario por teléfono
            user_url = f"{java_service_url}/api/users/by-phone"
            user_payload = {
                "clientProjectId": client_project_id,
                "phone": phone
            }
            
            logger.info(f"🔍 Consultando usuario: {user_url} con payload: {user_payload}")
            
            user_response = requests.post(user_url, json=user_payload, timeout=10)
            logger.info(f"🔍 Respuesta del usuario: status={user_response.status_code}")
            if user_response.status_code != 200:
                logger.warning(f"❌ Error consultando usuario: {user_response.status_code}")
                logger.warning(f"❌ Response text: {user_response.text}")
                return None
                
            user_data = user_response.json()
            logger.info(f"🔍 Datos del usuario obtenidos: {user_data}")
            if not user_data:
                logger.warning("❌ Usuario no encontrado")
                return None
            
            # Consultar referidos del usuario
            referral_code = user_data.get("referralCode")
            if not referral_code:
                logger.warning("Usuario no tiene código de referido")
                return {
                    "user": user_data,
                    "referrals": [],
                    "points": 0,
                    "referral_code": None
                }
            
            # Consultar usuarios referidos por este código
            referrals_url = f"{java_service_url}/api/users/by-referral-code"
            referrals_payload = {
                "clientProjectId": client_project_id,
                "referralCode": referral_code
            }
            
            logger.info(f"Consultando referidos: {referrals_url} con payload: {referrals_payload}")
            
            referrals_response = requests.post(referrals_url, json=referrals_payload, timeout=10)
            referrals = []
            
            if referrals_response.status_code == 200:
                referrals_data = referrals_response.json()
                if isinstance(referrals_data, list):
                    referrals = referrals_data
                elif isinstance(referrals_data, dict) and referrals_data:
                    referrals = [referrals_data]
            
            # Calcular puntos (50 por referido completado)
            completed_referrals = [r for r in referrals if r.get("completed", False)]
            points = len(completed_referrals) * 50
            
            return {
                "user": user_data,
                "referrals": referrals,
                "completed_referrals": completed_referrals,
                "points": points,
                "referral_code": referral_code,
                "total_referrals": len(referrals)
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
            
            response = f"""🎯 **¡Hola {user_name}! Aquí está tu progreso:**

[TROFEO] **Tus Puntos Actuales: {points}**
- Referidos completados: {len(completed_referrals)}
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
            
            # 🚀 OPTIMIZACIÓN CRÍTICA: Timeout rápido para evitar demoras
            import asyncio
            try:
                # Intentar con timeout de 8 segundos
                classification_result = await asyncio.wait_for(
                    self._classify_with_ai(message, user_context, "", tenant_id),
                    timeout=8.0
                )
            except asyncio.TimeoutError:
                logger.warning(f"⏰ TIMEOUT en clasificación Gemini para '{message[:30]}...', usando fallback rápido")
                # Fallback rápido basado en palabras clave
                classification_result = self._fast_fallback_classification(message)
            
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

    def _fast_fallback_classification(self, message: str) -> Dict[str, Any]:
        """
        Clasificación rápida basada en palabras clave para casos de timeout
        """
        message_lower = message.lower()
        
        # Palabras clave para diferentes intenciones
        keywords = {
            "saludo_apoyo": ["hola", "buenos", "buenas", "saludo", "hey"],
            "conocer_candidato": ["quien", "candidato", "propuesta", "plan", "agua", "viva", "hidroituango"],
            "registro": ["nombre", "apellido", "ciudad", "telefono", "email"],
            "agendar_cita": ["cita", "reunion", "calendly", "agendar"],
            "malicioso": ["odio", "violencia", "amenaza", "insulto"]
        }
        
        # Buscar coincidencias
        for intent, words in keywords.items():
            for word in words:
                if word in message_lower:
                    return {
                        "category": intent,
                        "confidence": 0.8,
                        "original_message": message,
                        "reason": "Fast fallback - keyword match"
                    }
        
        # Default
        return {
            "category": "saludo_apoyo",
            "confidence": 0.6,
            "original_message": message,
            "reason": "Fast fallback - default"
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

    async def _classify_with_ai(self, message: str, user_context: Dict[str, Any], session_context: str = "", tenant_id: str = None) -> Dict[str, Any]:
        """Clasifica intención usando IA con optimizaciones de velocidad"""
        
        self._ensure_model_initialized()
        
        # Primero verificar intención maliciosa de manera inteligente
        malicious_detection = self._detect_malicious_intent(message)
        if malicious_detection["is_malicious"]:
            return {
                "category": "malicioso",
                "confidence": malicious_detection["confidence"],
                "original_message": message,
                "reason": malicious_detection["reason"],
                "detected_categories": malicious_detection["categories"]
            }
        
        # 🚀 OPTIMIZACIÓN: Clasificación híbrida (patrones + IA)
        pattern_result = self._classify_with_patterns(message, user_context)
        if pattern_result["confidence"] > 0.8:
            return pattern_result
        
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
            
            # 🚀 OPTIMIZACIÓN: Prompt ultra-corto para velocidad máxima
            prompt = f"""Clasifica: "{message}" en UNA categoría:
saludo_apoyo|cita_campaña|conocer_candidato|publicidad_info|colaboracion_voluntariado|quejas|malicioso|registration_response|solicitud_funcional

Respuesta:"""
            
            # 🔧 OPTIMIZACIÓN: Timeout ultra-agresivo (2 segundos)
            import asyncio
            try:
                response_text = await asyncio.wait_for(
                    self._generate_content_ultra_fast(prompt, max_tokens=5),
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
            
            # 🔧 OPTIMIZACIÓN: Detección mejorada de bloqueo por safety filters
            if category in ["hola, ¿en qué puedo ayudarte hoy?", "lo siento, no puedo procesar esa consulta en este momento. por favor, intenta reformular tu pregunta de manera más específica.", "hola", "hello", "hi"] or len(category) > 50:
                logger.warning("⚠️ GEMINI BLOQUEADO O RESPUESTA LARGA - Usando fallback")
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
                "colaboracion_voluntariado", "quejas", "lider", "atencion_humano", 
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
        
        # Patrones de alta confianza
        patterns = {
            "saludo_apoyo": [
                "hola", "hi", "hello", "buenos días", "buenas tardes", "buenas noches",
                "gracias", "ok", "okay", "sí", "si", "no", "perfecto", "excelente"
            ],
            "conocer_candidato": [
                "quien es", "qué es", "cómo funciona", "propuestas",
                "candidato", "políticas", "obras", "programas", "plan de gobierno"
            ],
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
            "quejas": [
                "queja", "reclamo", "problema", "mal servicio", "no funciona",
                "error", "falla", "defecto"
            ],
            "registration_response": [
                "me llamo", "mi nombre es", "soy", "vivo en", "mi ciudad es",
                "mi teléfono es", "mi email es"
            ]
        }
        
        # Buscar coincidencias exactas primero
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern in message_lower:
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
        message_lower = message.lower().strip()
        
        # Solo detectar casos muy obvios y específicos
        if message_lower in ["hola", "buenos días", "buenas tardes", "buenas noches", "gracias"]:
            return "saludo_apoyo"
        
        # Detectar preguntas sobre casos específicos, propuestas, políticas
        political_question_patterns = [
            "que es", "qué es", "quien es", "quién es", "como funciona", "cómo funciona",
            "caso", "propuesta", "política", "obra", "proyecto"
        ]
        
        for pattern in political_question_patterns:
            if pattern in message_lower:
                return "conocer_candidato"
        
        # Detectar explicaciones sobre datos disponibles (muy específico)
        if self._looks_like_data_explanation(message):
            return "registration_response"
        
        # Detectar respuestas de registro basadas en contexto específico
        if context and context.get("user_state") == "WAITING_NAME":
            if self._analyze_registration_intent(message, "name"):
                return "registration_response"
        
        if context and context.get("user_state") == "WAITING_LASTNAME":
            if self._analyze_registration_intent(message, "lastname"):
                return "registration_response"

        if context and context.get("user_state") == "WAITING_CITY":
            if self._analyze_registration_intent(message, "city"):
                return "registration_response"
        
        # Para todo lo demás, confiar en que Gemini maneje la clasificación correctamente
        # Si llegamos aquí, significa que Gemini falló, así que usar conocer_candidato como fallback
        return "conocer_candidato"
    
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
                logger.info(f"[OK] Usuario {user_id} bloqueado exitosamente en WATI y base de datos")
            else:
                logger.error(f"[ERROR] Error bloqueando usuario {user_id}: {notification_result.get('error')}")
                logger.error(f"[ERROR] Detalles del error: {notification_result}")
            
            # No responder nada cuando es malicioso, solo bloquear silenciosamente
            return ""
            
        except Exception as e:
            logger.error(f"Error manejando comportamiento malicioso: {str(e)}")
            return "Lo siento, no puedo procesar tu mensaje en este momento."
    
    def _handle_appointment_request_with_context(self, branding_config: Dict[str, Any], 
                                               tenant_config: Dict[str, Any], session_context: str = "") -> str:
        """Maneja solicitudes de citas con contexto de sesión"""
        contact_name = branding_config.get("contactName", "el candidato")
        calendly_link = tenant_config.get("link_calendly", "")
        
        # Si hay contexto de sesión, personalizar la respuesta
        if session_context:
            return f"""¡Perfecto! Me alegra que quieras agendar una cita con {contact_name}. 
            
Puedes reservar tu cita directamente aquí: {calendly_link}

Si tienes alguna pregunta específica sobre la reunión o necesitas ayuda con el proceso, no dudes en preguntarme."""
        else:
            return f"""¡Excelente! Para agendar una cita con {contact_name}, puedes usar este enlace: {calendly_link}"""
    
    def _get_greeting_response_with_context(self, branding_config: Dict[str, Any], session_context: str = "") -> str:
        """Genera saludo con contexto de sesión inteligente"""
        contact_name = branding_config.get("contactName", "el candidato")
        
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
        """Genera respuesta de voluntariado con contexto de sesión"""
        contact_name = branding_config.get("contactName", "el candidato")
        
        # Si hay contexto de sesión, personalizar la respuesta
        if session_context:
            return f"""¡Qué genial que quieras ser parte del equipo de {contact_name}! 
            
Tu apoyo es fundamental para el cambio que queremos lograr. Te puedo ayudar a conectarte con nuestro equipo de voluntarios o responder cualquier pregunta que tengas sobre cómo participar."""
        else:
            return f"""¡Excelente! {contact_name} valora mucho el apoyo de personas como tú. 
            
Te puedo ayudar a conectarte con nuestro equipo de voluntarios. ¿Te gustaría que te ayude a agendar una reunión o tienes alguna pregunta específica sobre cómo participar?"""


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

Texto: "{data}"

Un nombre válido debe:
- Contener solo letras, espacios, guiones, apostrofes y puntos
- Tener entre 2 y 50 caracteres
- NO contener números (excepto en casos especiales como "María José")
- NO ser una palabra común del español como "referido", "gracias", "hola", etc.
- NO ser un código alfanumérico

Responde ÚNICAMENTE "VALIDO" o "INVALIDO" seguido de la razón si es inválido.

Ejemplos:
- "Juan" -> VALIDO
- "María José" -> VALIDO
- "José María" -> VALIDO
- "SANTIAGO" -> VALIDO
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
- Ser una ciudad real de Colombia

Responde ÚNICAMENTE "VALIDO" o "INVALIDO" seguido de la razón si es inválido.

Ejemplos:
- "Bogotá" -> VALIDO
- "Medellín" -> VALIDO
- "Cali" -> VALIDO
- "Soacha" -> VALIDO
- "K351ERXL" -> INVALIDO (es un código, no una ciudad)
- "referido" -> INVALIDO (palabra común)
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
        Extrae el nombre del usuario de un mensaje que contiene un código de referido
        
        Args:
            tenant_id: ID del tenant
            message: Mensaje que contiene código de referido
            
        Returns:
            Dict con el nombre extraído y validación
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
Analiza el siguiente mensaje y extrae SOLO el nombre de la persona que se está registrando:

Mensaje: "{message}"

IMPORTANTE:
- El mensaje puede contener un código de referido
- El mensaje puede mencionar a la persona que refiere
- Debes extraer SOLO el nombre de quien se está registrando, NO de quien refiere
- Si el mensaje no contiene un nombre claro del usuario, responde "NO_NAME"

Ejemplos:
- "Hola, vengo referido por Juan, codigo: ABC123" -> El usuario NO menciona su nombre, debe responder "NO_NAME"
- "Soy María, vengo referido por Juan, codigo: ABC123" -> El nombre es "María"
- "Me llamo Carlos, codigo: DEF456" -> El nombre es "Carlos"
- "Hola, soy Ana García, vengo referido por Pedro, codigo: GHI789" -> El nombre es "Ana García"

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
                    "reason": "El mensaje no contiene el nombre del usuario"
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

    async def generate_all_initial_messages(self, tenant_config: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Genera los 3 mensajes iniciales de una vez para optimizar el tiempo de respuesta
        
        Args:
            tenant_config: Configuración del tenant (opcional)
            
        Returns:
            Diccionario con los 3 mensajes generados
        """
        try:
            # 🚀 OPTIMIZACIÓN: Usar respuestas precomputadas para casos comunes
            candidate_name = ""
            contact_name = "Mi Candidato"
            
            if tenant_config:
                branding = tenant_config.get('branding', {})
                if branding:
                    candidate_name = branding.get('candidate_name', '')
                    config_contact_name = branding.get('contact_name', '')
                    if config_contact_name and config_contact_name.strip():
                        contact_name = config_contact_name.strip()
            
            # Verificar si podemos usar respuestas precomputadas genéricas
            if not candidate_name or candidate_name.strip() == "":
                logger.info("🚀 Usando respuestas precomputadas genéricas")
                return self._precomputed_initial_messages["default"].copy()
            
            # Si necesitamos personalización específica, usar IA
            logger.info(f"🔄 Generando mensajes personalizados para candidato: {candidate_name}")
            
            # Obtener información del tenant para personalización
            tenant_info = ""
            if tenant_config:
                branding = tenant_config.get('branding', {})
                if branding:
                    campaign_name = branding.get('campaign_name', '')
                    
                    if candidate_name:
                        tenant_info += f"Candidato: {candidate_name}. "
                    if campaign_name:
                        tenant_info += f"Campaña: {campaign_name}. "
            
            # 🚀 OPTIMIZACIÓN: Prompt ultra-optimizado para velocidad
            prompt = f"""Genera 3 mensajes WhatsApp campaña política.

Info: {tenant_info}
Contacto: {contact_name}

1. Bienvenida (100 chars): BIENVENIDA:
2. Guardar contacto (150 chars): CONTACTO:  
3. Pedir nombre (120 chars): NOMBRE:"""

            try:
                # 🚀 OPTIMIZACIÓN: Usar configuración ultra-rápida para mensajes iniciales
                response = await self._generate_content_ultra_fast(prompt)
                if response and len(response.strip()) > 0:
                    # Parsear la respuesta
                    lines = response.strip().split('\n')
                    messages = {}
                    
                    for line in lines:
                        if line.startswith('BIENVENIDA:'):
                            messages['welcome'] = line.replace('BIENVENIDA:', '').strip()
                        elif line.startswith('CONTACTO:'):
                            messages['contact'] = line.replace('CONTACTO:', '').strip()
                        elif line.startswith('NOMBRE:'):
                            messages['name'] = line.replace('NOMBRE:', '').strip()
                    
                    if len(messages) == 3:
                        return messages
            except Exception as e:
                logger.warning(f"Error generando mensajes con IA: {e}")
            
            # 🚀 FALLBACK ULTRA-RÁPIDO: Usar respuestas precomputadas si IA falla
            logger.warning("⚠️ IA falló, usando respuestas precomputadas como fallback")
            return self._precomputed_initial_messages["default"].copy()
                
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
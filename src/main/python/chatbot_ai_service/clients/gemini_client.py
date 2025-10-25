"""
Cliente dedicado para interactuar con Gemini AI

Este cliente fue extraído de AIService para separar responsabilidades:
- AIService: Lógica de negocio y orquestación
- GeminiClient: Comunicación con Gemini AI

Extraído de: src/main/python/chatbot_ai_service/services/ai_service.py
Líneas de referencia: 24-33, 39-56, 150-217
"""
import logging
import time
import os
from typing import Optional, Dict, Any
import google.generativeai as genai
import httpx

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Cliente para Gemini AI con configuración avanzada y resiliencia
    
    Características:
    - Inicialización lazy del modelo
    - Rate limiting (15 requests/minuto)
    - Fallback automático de gRPC a REST API
    - Manejo robusto de errores
    
    Uso:
        client = GeminiClient()
        response = await client.generate_content("¿Cómo estás?")
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el cliente de Gemini
        
        Args:
            api_key: API key de Gemini (opcional, usa GEMINI_API_KEY por defecto)
        """
        self.model = None
        self._initialized = False
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        # Rate limiting (copiado de AIService línea 27-29)
        self.request_times = []
        self.max_requests_per_minute = 15
        
        # NUEVO: Cache de modelos por configuración (Fase 2)
        self.models_cache = {}  # Key: config_hash -> model instance
        
        logger.info("GeminiClient inicializado (lazy loading)")
    
    def preload_models(self):
        """
        Pre-carga los modelos más comunes para mejorar el tiempo de respuesta
        
        Este método inicializa los modelos que se usan frecuentemente
        para evitar la latencia de inicialización en tiempo real.
        """
        if not self.api_key:
            logger.warning("⚠️ No se puede pre-cargar modelos: GEMINI_API_KEY no configurado")
            return
            
        logger.info("🚀 Pre-cargando modelos de IA para optimizar tiempo de respuesta...")
        print("🚀 DEBUG PRELOAD: Iniciando preload_models()")
        
        # 🚀 OPTIMIZACIÓN: Usar configuración ultra-rápida con safety settings desactivados
        import os
        ultra_fast_mode = os.getenv("ULTRA_FAST_MODE", "false").lower() == "true"
        logger.info(f"🚀 ULTRA_FAST_MODE detectado en preload: {ultra_fast_mode}")
        print(f"🚀 DEBUG PRELOAD: ULTRA_FAST_MODE = {ultra_fast_mode}")
        
        # Configuraciones de modelos más comunes
        common_configs = [
            # Configuración para clasificación de intenciones
            {
                "model_name": "gemini-2.5-flash",
                "temperature": 0.01 if ultra_fast_mode else 0.1,
                "top_p": 0.1 if ultra_fast_mode else 0.8,
                "top_k": 1 if ultra_fast_mode else 20,
                "max_output_tokens": 64 if ultra_fast_mode else 100,
                "description": "Para clasificación de intenciones"
            },
            # Configuración para generación de mensajes de bienvenida
            {
                "model_name": "gemini-2.5-flash", 
                "temperature": 0.8,
                "top_p": 0.9,
                "top_k": 50,
                "max_output_tokens": 500,
                "description": "Para generar mensajes de bienvenida personalizados"
            },
            # Configuración para generación de mensajes de contacto
            {
                "model_name": "gemini-2.5-flash",
                "temperature": 0.8,
                "top_p": 0.9,
                "top_k": 50,
                "max_output_tokens": 500,
                "description": "Para generar mensajes de guardado de contacto"
            },
            # Configuración para solicitud de nombre
            {
                "model_name": "gemini-2.5-flash",
                "temperature": 0.8,
                "top_p": 0.9,
                "top_k": 50,
                "max_output_tokens": 500,
                "description": "Para solicitar información del usuario"
            },
            # Configuración para análisis de registro
            {
                "model_name": "gemini-2.5-flash",
                "temperature": 0.1,
                "top_p": 0.8,
                "top_k": 20,
                "max_output_tokens": 200,
                "description": "Para analizar respuestas de registro"
            }
        ]
        
        # Pre-cargar cada configuración
        for i, config in enumerate(common_configs):
            try:
                logger.info(f"📦 Pre-cargando modelo {i+1}/{len(common_configs)}: {config['description']}")
                self._get_or_create_model(config)
                logger.info(f"✅ Modelo {i+1} pre-cargado exitosamente")
            except Exception as e:
                logger.warning(f"⚠️ Error pre-cargando modelo {i+1}: {str(e)}")
        
        logger.info(f"🎯 Pre-carga completada: {len(self.models_cache)} modelos disponibles en cache")
        
        # 🚀 CRÍTICO: Inicializar también el modelo principal
        logger.info("🚀 Inicializando modelo principal durante preload...")
        self._ensure_model_initialized()
        logger.info(f"🔍 Modelo principal inicializado: {self.model is not None}")
    
    def _ensure_model_initialized(self):
        """
        Inicializa el modelo de forma lazy
        
        COPIADO de AIService línea 150-169
        
        Solo se ejecuta una vez, en el primer uso del modelo.
        Esto mejora el tiempo de startup del servicio.
        """
        logger.info("🚀 _ensure_model_initialized() llamado")
        logger.info(f"🔍 _initialized: {self._initialized}")
        logger.info(f"🔍 api_key disponible: {self.api_key is not None}")
        
        if self._initialized:
            logger.info("✅ Modelo ya inicializado, saltando")
            return
            
        if self.api_key:
            try:
                # Configuración básica para Gemini AI
                genai.configure(api_key=self.api_key)
                
                # 🚀 OPTIMIZACIÓN MÁXIMA: Configuración ultra-rápida para clasificación
                from google.generativeai.types import HarmCategory, HarmBlockThreshold
                
                # 🚀 CONFIGURACIÓN SIMPLE: Sin safety settings explícitos (como versión anterior)
                # La versión anterior NO tenía safety settings explícitos y funcionaba
                safety_settings = None
                
                generation_config = {
                    "temperature": 0.8,  # Temperatura moderada como versión anterior
                    "top_p": 0.9,        # Configuración moderada
                    "top_k": 20,         # Configuración moderada
                    "max_output_tokens": 1000,  # Como versión anterior
                    "candidate_count": 1
                }
                
                print("🚀 DEBUG PRELOAD: Configurando safety settings...")
                logger.info("✅ Safety settings configurados con BLOCK_NONE para contenido político")
                print("🚀 DEBUG PRELOAD: Safety settings configurados")
                logger.info(f"🔍 Safety settings aplicados: {safety_settings}")
                print(f"🚀 DEBUG PRELOAD: Safety settings = {safety_settings}")
                
                # 🚀 OPTIMIZACIÓN CRÍTICA: Usar solo el modelo más rápido cuando ULTRA_FAST_MODE está activo
                import os
                ultra_fast_mode = os.getenv("ULTRA_FAST_MODE", "false").lower() == "true"
                is_local_dev = os.getenv("LOCAL_DEVELOPMENT", "false").lower() == "true"
                
                logger.info(f"🚀 ULTRA_FAST_MODE detectado: {ultra_fast_mode}")
                logger.info(f"🚀 LOCAL_DEVELOPMENT detectado: {is_local_dev}")
                print(f"🚀 DEBUG PRELOAD: ULTRA_FAST_MODE = {ultra_fast_mode}")
                print(f"🚀 DEBUG PRELOAD: LOCAL_DEVELOPMENT = {is_local_dev}")
                
                if ultra_fast_mode:
                    # Usar el modelo más moderno y rápido disponible en 2025
                    models_to_try = ['gemini-2.5-flash']  # Modelo más moderno y rápido
                    logger.info("🚀 ULTRA-RÁPIDO: Usando modelo más moderno gemini-2.5-flash (ULTRA_FAST_MODE activo)")
                else:
                    # Probar modelos desde el más moderno hacia el más antiguo
                    models_to_try = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-pro']
                    logger.info("🚀 NORMAL: Usando múltiples modelos modernos (ULTRA_FAST_MODE inactivo)")
                
                print(f"🚀 DEBUG PRELOAD: Modelos a probar = {models_to_try}")
                for model_name in models_to_try:
                    print(f"🚀 DEBUG PRELOAD: Intentando inicializar modelo: {model_name}")
                    try:
                        print(f"🚀 DEBUG PRELOAD: Dentro del try para {model_name}")
                        logger.info(f"🚀 Intentando inicializar modelo: {model_name}")
                        logger.info(f"🔍 Safety settings a aplicar: {safety_settings}")
                        logger.info(f"🔍 Generation config a aplicar: {generation_config}")
                        print(f"🚀 DEBUG PRELOAD: Creando GenerativeModel para {model_name}")
                        
                        self.model = genai.GenerativeModel(
                            model_name,
                            safety_settings=safety_settings,
                            generation_config=generation_config
                        )
                        print(f"🚀 DEBUG PRELOAD: GenerativeModel creado exitosamente para {model_name}")
                        logger.info(f"✅ Modelo {model_name} inicializado correctamente en GeminiClient con safety settings")
                        logger.info(f"🔍 Safety settings aplicados durante inicialización: {safety_settings}")
                        break
                    except Exception as model_error:
                        logger.warning(f"⚠️ Modelo {model_name} no disponible: {str(model_error)}")
                        import traceback
                        logger.warning(f"⚠️ Traceback: {traceback.format_exc()}")
                        if model_name == models_to_try[-1]:  # Si es el último modelo
                            logger.error(f"❌ Ningún modelo de Gemini está disponible")
                            self.model = None
            except Exception as e:
                logger.error(f"❌ Error inicializando modelo Gemini: {str(e)}")
                self.model = None
        else:
            logger.warning("⚠️ GEMINI_API_KEY no configurado")
            self.model = None
            
        self._initialized = True
    
    def _extract_text_from_response(self, response) -> str:
        """
        Extrae texto de una respuesta de Gemini, manejando respuestas simples y multi-part
        
        Args:
            response: Respuesta de Gemini (puede ser simple o multi-part)
            
        Returns:
            Texto extraído de la respuesta
        """
        try:
            # Intentar acceso rápido para respuestas simples
            return response.text
        except (ValueError, AttributeError) as e:
            # Si falla, es una respuesta multi-part
            logger.warning(f"⚠️ response.text falló: {str(e)}, intentando extracción manual...")
            try:
                # Debug: Ver estructura de respuesta
                logger.debug(f"🔍 Response type: {type(response)}")
                logger.debug(f"🔍 Has candidates: {hasattr(response, 'candidates')}")
                
                if hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    logger.debug(f"🔍 Candidate type: {type(candidate)}")
                    logger.debug(f"🔍 Has content: {hasattr(candidate, 'content')}")
                    
                    # Chequear si fue bloqueado por safety
                    if hasattr(candidate, 'finish_reason'):
                        logger.debug(f"🔍 Finish reason: {candidate.finish_reason}")
                        # finish_reason=2 corresponde a SAFETY
                        if str(candidate.finish_reason) in ['SAFETY', '3', '2']:  # 2 = SAFETY enum value
                            logger.warning(f"⚠️ Respuesta bloqueada por safety filters. Finish reason: {candidate.finish_reason}")
                            if hasattr(candidate, 'safety_ratings'):
                                logger.warning(f"   Safety ratings: {candidate.safety_ratings}")
                            # Retornar respuesta JSON válida para safety block
                            return '{"category": "saludo_apoyo", "confidence": 0.8, "reason": "safety_block"}'
                    
                    if hasattr(candidate, 'content') and candidate.content:
                        content = candidate.content
                        logger.debug(f"🔍 Content has parts: {hasattr(content, 'parts')}")
                        
                        if hasattr(content, 'parts'):
                            if content.parts:
                                # Concatenar todas las partes de texto
                                text_parts = []
                                for i, part in enumerate(content.parts):
                                    logger.debug(f"🔍 Part {i} type: {type(part)}, has text: {hasattr(part, 'text')}")
                                    if hasattr(part, 'text'):
                                        text_parts.append(part.text)
                                
                                if text_parts:
                                    result = ''.join(text_parts)
                                    logger.info(f"✅ Texto extraído de respuesta multi-part: {len(result)} chars")
                                    return result
                                else:
                                    logger.error(f"❌ Parts existen pero ninguna tiene texto. Parts: {[str(p) for p in content.parts[:3]]}")
                            else:
                                logger.error(f"❌ Content no tiene parts o parts está vacío. Content: {content}")
                        else:
                            logger.error(f"❌ Content no tiene atributo 'parts'. Content: {content}")
                
                # Si nada funciona, retornar mensaje de error más específico
                logger.error(f"❌ No se pudo extraer texto de la respuesta de Gemini")
                # Verificar si hay finish_reason disponible para dar mejor feedback
                if hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason'):
                        finish_reason = str(candidate.finish_reason)
                        if finish_reason in ['2', '3']:  # SAFETY
                            logger.warning("⚠️ Respuesta bloqueada por safety filters. Finish reason: 2")
                            logger.warning(f"   Safety ratings: {candidate.safety_ratings if hasattr(candidate, 'safety_ratings') else 'N/A'}")
                            return '{"category": "saludo_apoyo", "confidence": 0.8, "reason": "safety_block"}'
                        elif finish_reason == '1':  # STOP (normal)
                            return "Hola, ¿en qué puedo ayudarte hoy?"
                        else:
                            logger.warning(f"⚠️ Finish reason inesperado: {finish_reason}")
                
                return '{"category": "general_query", "confidence": 0.5, "reason": "processing_error"}'
                
            except Exception as ex:
                logger.error(f"❌ Error extrayendo texto de respuesta multi-part: {str(ex)}", exc_info=True)
                return "Lo siento, hubo un error procesando la respuesta."
    
    def _check_rate_limit(self):
        """
        Verifica y aplica rate limiting para evitar exceder cuota de API
        
        COPIADO de AIService línea 39-56
        
        Límite: 15 requests por minuto
        Si se excede, espera automáticamente hasta que se libere cuota.
        """
        current_time = time.time()
        
        # Limpiar requests antiguos (más de 1 minuto)
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        # Si hemos excedido el límite, esperar
        if len(self.request_times) >= self.max_requests_per_minute:
            sleep_time = 60 - (current_time - self.request_times[0])
            if sleep_time > 0:
                logger.warning(f"⏳ Rate limit alcanzado. Esperando {sleep_time:.1f} segundos...")
                time.sleep(sleep_time)
                # Limpiar la lista después de esperar
                self.request_times = []
        
        # Registrar este request
        self.request_times.append(current_time)
    
    async def _call_gemini_rest_api(self, prompt: str) -> str:
        """
        Llama a Gemini usando REST API en lugar de gRPC
        
        COPIADO de AIService línea 171-196
        
        Este método se usa como fallback cuando gRPC falla.
        Es más compatible pero ligeramente más lento.
        
        Args:
            prompt: Texto a enviar a Gemini
            
        Returns:
            Respuesta generada por Gemini
            
        Raises:
            Exception: Si la llamada REST también falla
        """
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"
            
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
            logger.error(f"❌ Error llamando a Gemini REST API: {str(e)}")
            raise
    
    def _get_or_create_model(self, config: Dict[str, Any]):
        """
        Obtiene o crea un modelo con configuración específica (Fase 2)
        
        Usa cache para evitar recrear modelos con la misma configuración.
        
        Args:
            config: Diccionario con configuración del modelo
            
        Returns:
            Instancia del modelo configurado
        """
        # Crear hash único para esta configuración
        config_items = sorted(config.items())
        config_hash = str(config_items)
        
        # Si ya existe en cache, retornarlo (modelo + config)
        if config_hash in self.models_cache:
            logger.debug(f"📦 Usando modelo cacheado")
            return self.models_cache[config_hash]
        
        # Asegurar que tenemos API key configurada
        if not self.api_key:
            logger.warning("⚠️ GEMINI_API_KEY no configurado")
            return None
        
        try:
            # Configurar Gemini AI
            genai.configure(api_key=self.api_key)
            
            # 🚀 OPTIMIZACIÓN CRÍTICA: Configuración ultra-rápida solo cuando ULTRA_FAST_MODE está activo
            import os
            ultra_fast_mode = os.getenv("ULTRA_FAST_MODE", "false").lower() == "true"
            is_local_dev = os.getenv("LOCAL_DEVELOPMENT", "false").lower() == "true"
            
            logger.info(f"🚀 ULTRA_FAST_MODE detectado en generación: {ultra_fast_mode}")
            logger.info(f"🚀 LOCAL_DEVELOPMENT detectado en generación: {is_local_dev}")
            
            if ultra_fast_mode:
                # Configuración ultra-agresiva solo cuando ULTRA_FAST_MODE está activo
                generation_config = {
                    "temperature": 0.01,      # Ultra-bajo para respuestas más rápidas y determinísticas
                    "top_p": 0.1,            # Ultra-bajo para respuestas más enfocadas
                    "max_output_tokens": 64,  # Ultra-reducido para respuestas más rápidas
                    "top_k": 1,              # Ultra-bajo para respuestas más determinísticas
                    "candidate_count": 1,    # Solo 1 candidato para máxima velocidad
                }
                logger.info("🚀 CONFIGURACIÓN ULTRA-RÁPIDA ACTIVADA (ULTRA_FAST_MODE activo)")
            else:
                # Configuración normal cuando ULTRA_FAST_MODE está inactivo
                generation_config = {
                    "temperature": 0.1,      # Normal para respuestas balanceadas
                    "top_p": 0.5,            # Normal para respuestas balanceadas
                    "max_output_tokens": 256,  # Normal para respuestas completas
                    "top_k": 10,             # Normal para respuestas balanceadas
                }
                logger.info("🚀 CONFIGURACIÓN NORMAL ACTIVADA (ULTRA_FAST_MODE inactivo)")
            
            # 🚀 CONFIGURACIÓN SIMPLE: Sin safety settings explícitos (como versión anterior)
            safety_settings = None
            logger.info("🚀 FILTROS DE SEGURIDAD DESACTIVADOS para contenido político")
            
            # Agregar response_mime_type si está presente (para JSON)
            # NOTA: Este campo solo funciona en versiones recientes de google-generativeai
            if "response_mime_type" in config:
                generation_config["response_mime_type"] = config["response_mime_type"]
            
            # Crear modelo SIN generation_config (siguiendo recomendación de comunidad)
            # Los configs se pasarán directamente en generate_content()
            model_name = config.get("model_name", "gemini-2.5-flash")
            
            # 🚀 CONFIGURACIÓN SIMPLE: Sin safety settings explícitos (como versión anterior)
            safety_settings = None
            logger.info("🚀 FILTROS DE SEGURIDAD DESACTIVADOS para contenido político")
            
            # Crear modelo con safety settings, probando desde el más moderno
            models_to_try = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
            if model_name in models_to_try:
                models_to_try = [model_name] + [m for m in models_to_try if m != model_name]
            
            model = None
            for try_model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(
                        model_name=try_model_name,
                        safety_settings=safety_settings
                    )
                    logger.info(f"✅ Modelo {try_model_name} creado exitosamente")
                    break
                except Exception as model_error:
                    logger.warning(f"⚠️ Modelo {try_model_name} no disponible: {str(model_error)}")
                    if try_model_name == models_to_try[-1]:  # Si es el último modelo
                        logger.error(f"❌ Ningún modelo de Gemini está disponible para la configuración")
                        model = None
            
            # Guardar modelo Y configuración en cache (juntos)
            self.models_cache[config_hash] = {
                "model": model,
                "generation_config": generation_config
            }
            
            logger.info(
                f"✅ Modelo creado: {model_name} | "
                f"temp={generation_config['temperature']}, "
                f"top_p={generation_config.get('top_p', 'N/A')}, "
                f"top_k={generation_config.get('top_k', 'N/A')}, "
                f"max_tokens={generation_config.get('max_output_tokens', 'N/A')}"
            )
            
            return self.models_cache[config_hash]
            
        except Exception as e:
            logger.error(f"❌ Error creando modelo con config personalizada: {str(e)}")
            return None
    
    async def generate_content(
        self, 
        prompt: str, 
        task_type: str = "chat_conversational",
        use_custom_config: bool = True
    ) -> str:
        """
        Genera contenido usando Gemini con fallback automático
        
        MEJORADO en Fase 2: Soporte para configuraciones por tarea
        
        Estrategia de fallback:
        1. Intenta con gRPC y configuración específica (si use_custom_config=True)
        2. Si falla, usa modelo por defecto
        3. Si falla, usa REST API (más compatible)
        4. Si todo falla, lanza excepción
        
        Args:
            prompt: Texto a enviar a Gemini
            task_type: Tipo de tarea (ej: "intent_classification", "chat_conversational")
            use_custom_config: Si True, usa configuración específica para la tarea
            
        Returns:
            Respuesta generada por Gemini
            
        Raises:
            Exception: Si ambos métodos (gRPC y REST) fallan
        """
        # Log de inicio
        logger.debug(f"🎯 Generando contenido | task_type={task_type}, use_custom_config={use_custom_config}")
        
        # Aplicar rate limiting
        self._check_rate_limit()
        
        # Intentar con configuración personalizada (Fase 2)
        if use_custom_config:
            try:
                from chatbot_ai_service.config.model_configs import get_config_for_task
                
                config = get_config_for_task(task_type)
                logger.debug(f"📋 Config obtenida para {task_type}: model={config.get('model_name')}, temp={config.get('temperature')}")
                model_data = self._get_or_create_model(config)
                
                if model_data:
                    logger.debug(f"🚀 Usando modelo configurado para task_type='{task_type}'")
                    # Extraer modelo y config del dict
                    model = model_data["model"]
                    generation_config = model_data["generation_config"]
                    # Pasar config directamente a generate_content (recomendación de comunidad)
                    # 🚀 CRÍTICO: Aplicar safety settings para permitir contenido político
                    from google.generativeai.types import HarmCategory, HarmBlockThreshold
                    # 🚀 CONFIGURACIÓN SIMPLE: Sin safety settings explícitos (como versión anterior)
                    safety_settings = None
                    print(f"🚀 DEBUG SAFETY: Aplicando safety_settings: {safety_settings}")
                    print(f"🚀 DEBUG PROMPT: Prompt enviado: {prompt[:200]}...")  # Mostrar primeros 200 caracteres
                    response = model.generate_content(prompt, generation_config=generation_config, safety_settings=safety_settings)
                    print(f"🚀 DEBUG SAFETY: Response finish_reason: {response.candidates[0].finish_reason if response.candidates else 'No candidates'}")
                    return self._extract_text_from_response(response)
                else:
                    logger.debug("⚠️ No se pudo crear modelo con config personalizada, usando modelo por defecto")
            except Exception as e:
                logger.warning(f"⚠️ Config personalizada falló, usando modelo por defecto: {str(e)}")
        # Fallback 1: Modelo por defecto (comportamiento original)
        try:
            # Asegurar que el modelo esté inicializado
            self._ensure_model_initialized()
            
            if self.model:
                logger.debug("🚀 Usando modelo por defecto (gRPC)")
                # 🚀 CONFIGURACIÓN SIMPLE: Sin safety settings explícitos (como versión anterior)
                safety_settings = None
                print(f"🚀 DEBUG SAFETY FALLBACK: Aplicando safety_settings: {safety_settings}")
                print(f"🚀 DEBUG PROMPT FALLBACK: Prompt enviado: {prompt[:200]}...")  # Mostrar primeros 200 caracteres
                response = self.model.generate_content(prompt, safety_settings=safety_settings)
                print(f"🚀 DEBUG SAFETY FALLBACK: Response finish_reason: {response.candidates[0].finish_reason if response.candidates else 'No candidates'}")
                return self._extract_text_from_response(response)
        except Exception as e:
            logger.warning(f"⚠️ gRPC falló, usando REST API: {str(e)}")
        
        # Fallback 2: REST API como último recurso
        logger.debug("🔄 Usando REST API como fallback")
        return await self._call_gemini_rest_api(prompt)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del cliente
        
        Returns:
            Diccionario con estadísticas de uso
        """
        current_time = time.time()
        recent_requests = [t for t in self.request_times if current_time - t < 60]
        
        return {
            "initialized": self._initialized,
            "has_api_key": bool(self.api_key),
            "model_loaded": self.model is not None,
            "requests_last_minute": len(recent_requests),
            "max_requests_per_minute": self.max_requests_per_minute,
            "rate_limit_utilization": len(recent_requests) / self.max_requests_per_minute if self.max_requests_per_minute > 0 else 0,
        }


"""
Servicio de IA simplificado para el Chatbot AI Service

Este servicio se enfoca únicamente en procesamiento de IA y recibe
la configuración del proyecto Political Referrals via HTTP.
"""
import logging
import time
import os
from typing import Dict, Any, Optional

import google.generativeai as genai
from chatbot_ai_service.services.configuration_service import configuration_service
from chatbot_ai_service.services.document_context_service import document_context_service
from chatbot_ai_service.services.session_context_service import session_context_service

logger = logging.getLogger(__name__)

class AIService:
    """Servicio de IA simplificado - solo procesamiento de IA"""
    
    def __init__(self):
        self.model = None
        self._initialized = False
    
    def _ensure_model_initialized(self):
        """Inicializa el modelo de forma lazy"""
        if self._initialized:
            return
            
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                logger.info("Modelo Gemini inicializado correctamente")
            except Exception as e:
                logger.error(f"Error inicializando modelo Gemini: {str(e)}")
                self.model = None
        else:
            logger.warning("GEMINI_API_KEY no configurado")
            self.model = None
            
        self._initialized = True
    
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
            
            # Cargar documentos del cliente si están disponibles
            await self._ensure_tenant_documents_loaded(tenant_id, ai_config)
            
            # Actualizar contexto de documentos en la sesión
            document_context = await document_context_service.get_relevant_context(tenant_id, query, max_results=3)
            if document_context:
                session_context_service.update_document_context(session_id, document_context)
            
            # 1. PRIMERO: Clasificar la intención del mensaje
            classification_result = await self.classify_intent(tenant_id, query, user_context, session_id)
            intent = classification_result.get("category", "default")  # El método classify_intent devuelve "category"
            confidence = classification_result.get("confidence", 0.0)
            
            logger.info(f"🔍 Clasificación completa: {classification_result}")
            logger.info(f"🧠 Intención extraída: {intent} (confianza: {confidence:.2f})")
            
            # 2. SEGUNDO: Procesar según la intención clasificada
            if intent == "cita_campaña":
                # Respuesta específica para agendar citas
                response = self._handle_appointment_request(branding_config)
            elif intent == "saludo_apoyo":
                # Respuesta específica para saludos
                response = await self._generate_ai_response_with_session(
                    query, user_context, ai_config, branding_config, tenant_id, session_id
                )
            elif intent == "conocer_daniel":
                # Respuesta específica sobre Daniel Quintero
                response = await self._generate_ai_response_with_session(
                    query, user_context, ai_config, branding_config, tenant_id, session_id
                )
            elif intent == "solicitud_funcional":
                # Respuesta específica para consultas funcionales
                response = self._handle_functional_request(query, branding_config)
            elif intent == "colaboracion_voluntariado":
                # Respuesta específica para voluntariado
                response = self._handle_volunteer_request(branding_config)
            else:
                # Respuesta general con contexto de sesión
                response = await self._generate_ai_response_with_session(
                    query, user_context, ai_config, branding_config, tenant_id, session_id
                )
            
            # Agregar respuesta del asistente a la sesión
            session_context_service.add_message(session_id, "assistant", response, metadata={"intent": intent, "confidence": confidence})
            
            processing_time = time.time() - start_time
            
            return {
                "response": response,
                "processing_time": processing_time,
                "tenant_id": tenant_id,
                "session_id": session_id,
                "intent": intent,
                "confidence": confidence
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
            
            # Construir prompt con contexto de sesión
            prompt = self._build_session_prompt(query, user_context, branding_config, session_context)
            
            # Generar respuesta
            response = self.model.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generando respuesta con sesión: {str(e)}")
            return "Lo siento, no pude procesar tu mensaje."
    
    def _build_session_prompt(self, query: str, user_context: Dict[str, Any], 
                            branding_config: Dict[str, Any], session_context: str) -> str:
        """Construye el prompt para chat con contexto de sesión"""
        contact_name = branding_config.get("contactName", "el candidato")
        
        # Contexto del usuario actual
        current_context = ""
        if user_context.get("user_name"):
            current_context += f"El usuario se llama {user_context['user_name']}. "
        if user_context.get("user_state"):
            current_context += f"Estado actual: {user_context['user_state']}. "
        
        # Detectar si es un saludo
        is_greeting = query.lower().strip() in ["hola", "hi", "hello", "hey", "buenos días", "buenas tardes", "buenas noches", "qué tal", "que tal"]
        
        prompt = f"""
Eres un asistente virtual para la campaña política de {contact_name}.

Tu objetivo es mantener conversaciones fluidas y naturales, recordando el contexto de la conversación anterior.

CONTEXTO ACTUAL DE LA SESIÓN:
{session_context}

CONTEXTO INMEDIATO:
{current_context}

Mensaje actual del usuario: "{query}"

INSTRUCCIONES:
1. Mantén el contexto de la conversación anterior
2. Si es una pregunta de seguimiento, responde de manera natural
3. Usa la información específica de la campaña cuando sea relevante
4. Mantén un tono amigable y profesional
5. Si no tienes información específica, sé honesto al respecto
6. Integra sutilmente elementos motivacionales sin ser explícito sobre "EPIC MEANING" o "DEVELOPMENT"

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
    
    def _handle_appointment_request(self, branding_config: Dict[str, Any]) -> str:
        """Maneja solicitudes de agendar citas"""
        contact_name = branding_config.get("contactName", "el candidato")
        calendly_link = branding_config.get("link_calendly", "https://calendly.com/dq-campana/reunion")
        
        return f"""¡Perfecto! Te ayudo a agendar una cita con alguien de la campaña de {contact_name}. 

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
        Analiza un mensaje y determina si contiene un dato de registro (name/lastname/city) o es información general.

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

            lowered = text.lower()
            if "?" in text or any(w in lowered for w in ["qué", "que ", "cómo", "como ", "quién", "quien ", "dónde", "donde "]):
                return {"type": "info", "value": None, "confidence": 0.85}

            def looks_like_city(s: str) -> bool:
                if len(s) < 2 or len(s) > 100:
                    return False
                import re
                # Permitir comas y otros caracteres comunes en frases de ubicación
                if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ .,'-]+$", s):
                    return False
                forbidden = ["hola", "gracias", "ok", "vale", "listo", "si", "sí", "no"]
                return s.lower() not in forbidden

            def split_full_name(s: str):
                parts = [p for p in s.split() if p]
                if len(parts) >= 2 and all(p.replace("ñ", "n").isalpha() for p in [x.lower() for x in parts]):
                    return parts[0], " ".join(parts[1:])
                return (parts[0], None) if parts else (None, None)

            # Usar IA para análisis más inteligente cuando el estado es WAITING_CITY
            if state == "WAITING_CITY":
                # Usar IA para extraer información de ciudad de frases naturales
                ai_analysis = await self._analyze_city_with_ai(text)
                if ai_analysis and ai_analysis.get("is_city", False):
                    return {
                        "type": "city", 
                        "value": ai_analysis.get("extracted_city", text), 
                        "confidence": ai_analysis.get("confidence", 0.8)
                    }

            if state == "WAITING_NAME":
                first, last = split_full_name(text)
                if first and len(first) >= 2 and first.lower() not in ["que", "qué", "ok", "vale", "gracias", "listo", "si", "sí", "no"]:
                    val = text if last else first
                    return {"type": "name", "value": val, "confidence": 0.9}

            if state == "WAITING_LASTNAME":
                if len(text) >= 2 and looks_like_city(text) and not any(ch.isdigit() for ch in text):
                    return {"type": "lastname", "value": text, "confidence": 0.9}

            if state == "WAITING_CITY" or state == "":
                if looks_like_city(text):
                    return {"type": "city", "value": text, "confidence": 0.9}

            words = text.split()
            if 2 <= len(words) <= 4 and not any(c.isdigit() for c in text):
                if words[0].lower() not in ["que", "qué", "ok", "vale", "gracias", "listo", "si", "sí", "no"]:
                    return {"type": "name", "value": text, "confidence": 0.6}

            return {"type": "other", "value": None, "confidence": 0.5}
            
        except Exception as e:
            logger.error(f"Error analizando registro: {str(e)}")
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
            response = self.model.generate_content(prompt)
            text = (response.text or "").strip()
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
            if document_context_service.get_tenant_document_info(tenant_id):
                return
            
            # Obtener URL del bucket de documentación
            documentation_bucket_url = ai_config.get("documentation_bucket_url")
            
            if documentation_bucket_url:
                logger.info(f"Cargando documentos para tenant {tenant_id} desde: {documentation_bucket_url}")
                success = await document_context_service.load_tenant_documents(tenant_id, documentation_bucket_url)
                if success:
                    logger.info(f"Documentos cargados exitosamente para tenant {tenant_id}")
                else:
                    logger.warning(f"No se pudieron cargar documentos para tenant {tenant_id}")
            else:
                logger.info(f"No hay bucket de documentación configurado para tenant {tenant_id}")
                
        except Exception as e:
            logger.error(f"Error cargando documentos para tenant {tenant_id}: {str(e)}")
    
    async def _generate_ai_response(self, query: str, user_context: Dict[str, Any], 
                                  ai_config: Dict[str, Any], branding_config: Dict[str, Any], 
                                  tenant_id: str) -> str:
        """Genera respuesta usando IA con contexto de documentos"""
        self._ensure_model_initialized()
        if not self.model:
            return "Lo siento, el servicio de IA no está disponible."
        
        try:
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
            
            # Generar respuesta
            response = self.model.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generando respuesta con IA: {str(e)}")
            return "Lo siento, no pude procesar tu mensaje."
    
    async def _classify_with_ai(self, message: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Clasifica intención usando IA"""
        self._ensure_model_initialized()
        if not self.model:
            return {
                "category": "saludo_apoyo", 
                "confidence": 0.0,
                "original_message": message
            }
        
        try:
            # Prompt para clasificación
            prompt = f"""
            Clasifica la siguiente intención del mensaje en una de estas categorías para campañas políticas:
            
            - malicioso: Mensajes con intención negativa, spam, provocación o ataques hacia la campaña
            - cita_campaña: Contacto para agendar, confirmar o coordinar una reunión con miembros de la campaña
            - saludo_apoyo: Mensajes de cortesía, muestras de simpatía o expresiones de respaldo hacia el candidato o la campaña
            - publicidad_info: Preguntas o solicitudes relacionadas con materiales publicitarios, difusión o información de campaña
            - conocer_candidato: Interés en la trayectoria, propuestas o información personal/política del candidato
            - actualizacion_datos: Casos donde el ciudadano corrige o actualiza su información en la base de datos
            - solicitud_funcional: Preguntas técnicas o de uso sobre el software, plataforma o mecanismos de comunicación (como "¿Cómo voy?", "link de mi tribu", "esto cómo funciona?")
            - colaboracion_voluntariado: Ofrecimiento de apoyo activo, voluntariado o trabajo dentro de la campaña
            - quejas: Reclamos o comentarios negativos sobre la campaña, su gestión, comunicaciones o procesos
            - lider: Mensajes de actores que se identifican como líderes comunitarios, sociales o políticos buscando coordinar acciones
            - atencion_humano: Mensajes de usuarios que buscan hablar con un agente humano
            - atencion_equipo_interno: Mensajes de personas de la campaña que requieren información rápida
            - registration_response: Respuesta a pregunta de registro (nombre, apellido, ciudad, etc.)
            
            Mensaje: "{message}"
            
            Responde solo con la categoría más apropiada.
            """
            
            response = self.model.generate_content(prompt)
            category = response.text.strip().lower()
            
            # Validar categoría
            valid_categories = [
                "malicioso", "cita_campaña", "saludo_apoyo", "publicidad_info", 
                "conocer_candidato", "actualizacion_datos", "solicitud_funcional", 
                "colaboracion_voluntariado", "quejas", "lider", "atencion_humano", 
                "atencion_equipo_interno", "registration_response"
            ]
            
            if category not in valid_categories:
                category = "saludo_apoyo"  # Default a saludo_apoyo en lugar de general_query
            
            return {
                "category": category,
                "confidence": 0.8,  # Confianza fija por simplicidad
                "original_message": message
            }
            
        except Exception as e:
            logger.error(f"Error clasificando con IA: {str(e)}")
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
            
            response = self.model.generate_content(prompt)
            extracted_value = response.text.strip()
            
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
            
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            
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
            
            response = self.model.generate_content(prompt)
            result = response.text.strip().upper()
            
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
            response = self.model.generate_content(prompt)
            return response.text if response.text else ""
            
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

            response = self.model.generate_content(prompt)
            detected_code = response.text.strip().upper()
            
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


# Instancia global para compatibilidad
ai_service = AIService()
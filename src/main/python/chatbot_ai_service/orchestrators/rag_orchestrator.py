"""
RAG Orchestrator - Cerebro del sistema RAG

Orquesta el flujo completo de Retrieval-Augmented Generation:
1. Query Rewriting (reformular preguntas)
2. Document Retrieval (buscar documentos relevantes)
3. Context Building (construir contexto)
4. Response Generation (generar respuesta)
5. Verification (verificar respuesta)
6. Citation (agregar citas)

Este es el componente central del sistema RAG, coordinando todos
los demás componentes para producir respuestas verificadas y fundamentadas.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from chatbot_ai_service.retrievers.smart_retriever import SmartRetriever, SearchResult
from chatbot_ai_service.verifiers.source_verifier import SourceVerifier, VerificationResult
from chatbot_ai_service.prompts.system_prompts import PromptBuilder, PromptType
from chatbot_ai_service.guardrails.guardrail_verifier import GuardrailVerifier, GuardrailVerificationResult
from chatbot_ai_service.guardrails.response_sanitizer import ResponseSanitizer

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """Respuesta completa del RAGOrchestrator"""
    response: str
    response_with_citations: str
    verification: VerificationResult
    retrieved_documents: List[SearchResult]
    metadata: Dict[str, Any]
    guardrail_result: Optional[GuardrailVerificationResult] = None
    sanitization_applied: bool = False


class RAGOrchestrator:
    """
    Orquestador principal del sistema RAG
    
    Coordina todo el flujo desde la pregunta del usuario hasta
    la respuesta verificada con citas de fuentes.
    
    Características:
    - Query rewriting para mejor búsqueda
    - Hybrid retrieval (semántica + keywords)
    - Context building inteligente
    - Response generation con documentos
    - Source verification
    - Automatic citations
    """
    
    def __init__(
        self, 
        gemini_client=None,
        document_service=None,
        enable_verification: bool = True,
        enable_citations: bool = True,
        enable_guardrails: bool = True,
        strict_guardrails: bool = True
    ):
        """
        Inicializa el RAGOrchestrator
        
        Args:
            gemini_client: Cliente de Gemini para generación
            document_service: Servicio de documentos
            enable_verification: Si True, verifica respuestas
            enable_citations: Si True, agrega citas
            enable_guardrails: Si True, aplica guardrails estrictos
            strict_guardrails: Si True, fallos críticos invalidan respuesta
        """
        self.gemini_client = gemini_client
        self.document_service = document_service
        self.enable_verification = enable_verification
        self.enable_citations = enable_citations
        self.enable_guardrails = enable_guardrails
        self.strict_guardrails = strict_guardrails
        
        # Inicializar componentes
        self.retriever = SmartRetriever()
        self.verifier = SourceVerifier()
        
        # 🛡️ FASE 5: Guardrails
        self.prompt_builder = PromptBuilder()
        self.guardrail_verifier = GuardrailVerifier(strict_mode=strict_guardrails)
        self.response_sanitizer = ResponseSanitizer(aggressive_mode=strict_guardrails)
        
        logger.info(
            f"🚀 RAGOrchestrator inicializado "
            f"(verification={enable_verification}, citations={enable_citations}, "
            f"guardrails={enable_guardrails}, strict={strict_guardrails})"
        )
    
    async def _rewrite_query(self, query: str) -> List[str]:
        """
        Reescribe el query para mejorar la búsqueda
        
        Genera variaciones del query original para capturar
        más documentos relevantes.
        
        Args:
            query: Query original del usuario
            
        Returns:
            Lista de queries (incluyendo el original)
        """
        # Por ahora, solo retornamos el query original
        # En futuras versiones, usaremos Gemini para generar variaciones
        
        queries = [query]
        
        # Agregar variación con palabras clave adicionales
        if "propuesta" in query.lower() or "propone" in query.lower():
            queries.append(f"{query} plan gobierno programa")
        
        if "candidato" in query.lower():
            queries.append(f"{query} trayectoria biografia perfil")
        
        logger.debug(f"Query rewriting: {len(queries)} variaciones generadas")
        return queries
    
    async def _retrieve_documents(
        self, 
        queries: List[str], 
        tenant_id: str,
        max_results: int = 5
    ) -> List[SearchResult]:
        """
        Recupera documentos relevantes para los queries
        
        Args:
            queries: Lista de queries
            tenant_id: ID del tenant
            max_results: Máximo de documentos a recuperar
            
        Returns:
            Lista de documentos recuperados
        """
        all_docs = []
        
        for query in queries:
            docs = await self.retriever.retrieve(
                query=query,
                tenant_id=tenant_id,
                max_results=max_results
            )
            all_docs.extend(docs)
        
        # Deduplicar por doc_id
        unique_docs = {}
        for doc in all_docs:
            if doc.doc_id not in unique_docs:
                unique_docs[doc.doc_id] = doc
            else:
                # Si ya existe, mantener el de mayor score
                if doc.score > unique_docs[doc.doc_id].score:
                    unique_docs[doc.doc_id] = doc
        
        # Ordenar por score y retornar top N
        final_docs = sorted(
            unique_docs.values(), 
            key=lambda x: x.score, 
            reverse=True
        )[:max_results]
        
        logger.info(f"Recuperados {len(final_docs)} documentos únicos")
        return final_docs
    
    def _build_rag_context(
        self, 
        documents: List[SearchResult],
        max_context_length: int = 3000
    ) -> str:
        """
        Construye el contexto para Gemini a partir de los documentos
        
        Args:
            documents: Documentos recuperados
            max_context_length: Longitud máxima del contexto
            
        Returns:
            Contexto formateado para el prompt
        """
        if not documents:
            return "No se encontraron documentos relevantes."
        
        context_parts = []
        current_length = 0
        
        for i, doc in enumerate(documents, 1):
            doc_text = f"[Documento {i}] {doc.filename}\n{doc.content}\n"
            
            # Verificar si agregar este documento excede el límite
            if current_length + len(doc_text) > max_context_length:
                # Truncar el documento si es necesario
                remaining_space = max_context_length - current_length
                if remaining_space > 200:  # Solo agregar si queda espacio razonable
                    doc_text = doc_text[:remaining_space] + "...\n"
                    context_parts.append(doc_text)
                break
            
            context_parts.append(doc_text)
            current_length += len(doc_text)
        
        context = "\n".join(context_parts)
        
        logger.debug(f"Contexto construido: {len(context)} caracteres de {len(documents)} documentos")
        return context
    
    def _build_rag_prompt(
        self, 
        query: str, 
        context: str,
        user_context: Dict[str, Any] = None,
        tenant_config: Dict[str, Any] = None
    ) -> str:
        """
        Construye el prompt completo para RAG con guardrails y personalidad específica del tenant
        INCLUYE contexto de sesión para continuidad
        
        Args:
            query: Pregunta del usuario
            context: Contexto de documentos
            user_context: Contexto adicional del usuario (puede incluir session_context)
            tenant_config: Configuración del tenant para personalización
            
        Returns:
            Prompt formateado con guardrails y personalidad
        """
        # 🆕 NUEVO: Obtener identidad del tenant para personalización completa
        tenant_identity = None
        tenant_memory = None
        
        if tenant_config:
            tenant_id = tenant_config.get('tenant_id')
            if tenant_id:
                try:
                    # Intentar importar servicios de identidad y memoria (opcional)
                    try:
                        from chatbot_ai_service.identity.tenant_identity_service import TenantIdentityService
                        from chatbot_ai_service.memory.tenant_memory_service import TenantMemoryService
                        
                        identity_service = TenantIdentityService()
                        memory_service = TenantMemoryService()
                        
                        # Obtener identidad y memoria de forma asíncrona (no bloquear)
                        # Nota: Esto se ejecuta dentro de un contexto async, así que podemos usar await
                        # Pero como este método no es async, simplemente lo saltamos por ahora
                        # (la personalización avanzada es opcional)
                        logger.debug("⚠️ Cargando identidad/memoria requiere contexto async - saltando por ahora")
                        tenant_identity = None
                        tenant_memory = None
                        
                        if tenant_identity:
                            logger.info(f"✅ Identidad del tenant cargada: {tenant_identity.candidate_name}")
                        if tenant_memory:
                            logger.info(f"✅ Memoria del tenant cargada: {tenant_memory.total_conversations} conversaciones")
                    except ImportError:
                        # Si los servicios no están disponibles, continuar sin ellos
                        logger.debug("⚠️ Servicios de identidad/memoria no disponibles - continuando sin personalización avanzada")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando identidad/memoria del tenant: {e}")
        
        # Extraer información de branding del tenant
        # Primero intentar obtener de branding_config (si existe)
        contact_name = None
        candidate_name = "Asistente"
        
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
            
            # Si aún no se encontró, buscar en nivel raíz
            if not contact_name:
                contact_name = tenant_config.get('contact_name') or tenant_config.get('contactName')
            
            # Si branding existe, obtener candidate_name
            branding = tenant_config.get('branding', {})
            if isinstance(branding, dict):
                candidate_name = branding.get('candidate_name', candidate_name)
        
        # Si NO se encontró ningún contact_name, usar valor por defecto
        if not contact_name:
            contact_name = "el candidato"
        
        # Log para debug
        logger.info(f"👤 [RAG] contact_name extraído: '{contact_name}'")
        if contact_name == "el candidato":
            logger.warning(f"⚠️ [RAG] Usando valor por defecto 'el candidato'. tenant_config keys: {list(tenant_config.keys()) if tenant_config else 'None'}")
        
        # 🔧 FIX: Incluir contexto de sesión si está disponible
        session_context = ""
        if user_context and "session_context" in user_context:
            session_context = user_context["session_context"]
            logger.debug(f"Contexto de sesión incluido en prompt: {len(session_context)} chars")
        
        # 🔧 FIX: Incluir historial de conversación si está disponible
        if user_context and "conversation_history" in user_context:
            conversation_history = user_context["conversation_history"]
            logger.debug(f"Historial de conversación incluido en prompt: {len(conversation_history)} chars")
            # Extraer solo la pregunta actual del usuario, eliminando el historial del query si está presente
            if conversation_history and query.startswith("Historial de conversación:"):
                # El query incluyó historial por error, limpiarlo
                lines = query.split('\n')
                # Buscar "Pregunta actual del usuario:" y tomar todo lo que viene después
                for i, line in enumerate(lines):
                    if "Pregunta actual del usuario:" in line or "Pregunta actual:" in line:
                        query = '\n'.join(lines[i+1:]).strip()
                        logger.info(f"Query limpiado de historial: '{query[:100]}...'")
                        break
        
        # 🎯 NUEVO: Detectar si es un saludo/apoyo antes de construir prompt técnico
        is_greeting_or_support = self._is_greeting_or_support(query)
        
        if is_greeting_or_support:
            logger.info("🎯 Detectado saludo/apoyo - usando prompt conversacional")
            return self._build_greeting_prompt(query, context, user_context, contact_name, candidate_name, tenant_config)
        
        # 🛡️ FASE 5: Usar PromptBuilder con guardrails
        if self.enable_guardrails:
            # Detectar automáticamente el tipo de prompt
            prompt_type = self.prompt_builder.detect_prompt_type(query)
            
            logger.debug(f"Tipo de prompt detectado: {prompt_type.value}")
            
            # Construir prompt con guardrails y personalidad
            prompt = self.prompt_builder.build_prompt(
                query=query,
                documents=context,
                prompt_type=prompt_type,
                user_context=user_context
            )
            
            return prompt
        
        # Fallback: Prompt original con personalidad
        user_info = ""
        if user_context and user_context.get("user_name"):
            user_info = f"El usuario se llama {user_context['user_name']}. "
        
        # 🆕 NUEVO: Enriquecer con identidad del tenant si está disponible
        personality_text = ""
        key_proposals_text = ""
        bio_text = ""
        
        if tenant_identity:
            # Usar identidad completa del tenant
            candidate_name = tenant_identity.candidate_name
            campaign_name = tenant_identity.campaign_name
            contact_name = tenant_identity.contact_name
            
            # Personalidad y estilo
            if tenant_identity.personality_traits:
                traits = ", ".join(tenant_identity.personality_traits)
                personality_text = f"Tu personalidad: {traits}. "
            
            # Tono y estilo de comunicación
            style_info = f"Estilo de comunicación: {tenant_identity.communication_style}, tono: {tenant_identity.tone}. "
            
            # Bio si está disponible
            if tenant_identity.bio:
                bio_text = f"\n**SOBRE TI:** {tenant_identity.bio}\n"
            
            # Propuestas clave
            if tenant_identity.key_proposals:
                proposals = "\n".join([f"- {p}" for p in tenant_identity.key_proposals[:3]])  # Top 3
                key_proposals_text = f"\n**PROPUESTAS CLAVE DE TU CAMPAÑA:**\n{proposals}\n"
        else:
            # Fallback a valores anteriores
            candidate_name = candidate_name
            campaign_name = f"la campaña de {contact_name}"
        
        prompt = f"""
Asistente virtual {candidate_name} de la campaña política {campaign_name}.
{bio_text}
**TU PERSONALIDAD Y TONO:**
{personality_text}{style_info}
- Habla como representante de {contact_name} y su campaña
- Sé amigable, cercano y auténtico
- Usa un tono conversacional pero profesional
- Muestra pasión por los temas de la campaña
- Si no tienes información específica, ofrece conectar con el equipo de {contact_name}
{key_proposals_text}

**REGLAS FUNDAMENTALES:**
1. SOLO responde con información de los DOCUMENTOS proporcionados
2. Si la información está en los documentos, úsala pero NO cites la fuente
3. Si NO está en los documentos, di explícitamente "No tengo esa información en nuestros documentos de campaña"
4. NUNCA inventes datos, números, fechas o detalles que no estén en los documentos
5. Si la pregunta requiere información no disponible, sugiere contactar al equipo de {contact_name}

**CONTEXTO DEL USUARIO:**
{user_info}

**DOCUMENTOS DISPONIBLES:**
{context}

**PREGUNTA DEL USUARIO:**
{query}

**INSTRUCCIONES PARA LA RESPUESTA:**
- Sé claro, conciso y directo
- Usa la información de los documentos
- Si no hay información, sé honesto al respecto
- Mantén un tono profesional y amigable como representante de {contact_name}

**TU RESPUESTA:**
"""
        return prompt
    
    def _is_greeting_or_support(self, query: str) -> bool:
        """
        Detecta si el query es un saludo o mensaje de apoyo
        
        Args:
            query: Mensaje del usuario
            
        Returns:
            True si es un saludo/apoyo, False si es una pregunta técnica
        """
        query_lower = query.lower().strip()
        
        # Palabras clave que indican saludo/apoyo
        greeting_keywords = [
            "hola", "buenos días", "buenas tardes", "buenas noches",
            "saludos", "qué tal", "cómo estás", "cómo va",
            "listo", "perfecto", "excelente", "genial",
            "con toda", "con quintero", "apoyo", "vamos", "adelante",
            "ok", "okey", "okay", "sí", "claro", "por supuesto",
            "gracias", "muchas gracias", "genial", "perfecto"
        ]
        
        # Frases completas que indican apoyo
        support_phrases = [
            "con toda con", "todo con", "vamos con", "adelante con",
            "apoyo a", "estoy con", "vamos por", "sí a"
        ]
        
        # Verificar si contiene palabras clave de saludo
        if any(keyword in query_lower for keyword in greeting_keywords):
            # Si es muy corto (menos de 20 caracteres) y contiene saludo, probablemente es saludo
            if len(query) < 30:
                return True
            
            # Si contiene frases de apoyo, es saludo/apoyo
            if any(phrase in query_lower for phrase in support_phrases):
                return True
        
        # Si no contiene signos de interrogación y es muy corto (máximo 3 palabras), probablemente es saludo
        if "?" not in query and len(query.split()) <= 3:
            return True
        
        return False
    
    def _build_greeting_prompt(
        self,
        query: str,
        context: str,
        user_context: Dict[str, Any],
        contact_name: str,
        candidate_name: str,
        tenant_config: Dict[str, Any] = None
    ) -> str:
        """
        Construye un prompt especializado para saludos/apoyos
        
        Este prompt reconoce que es un saludo y responde de manera conversacional
        usando la personalidad de la campaña, sin forzar búsquedas técnicas.
        """
        user_info = ""
        if user_context and user_context.get("user_name"):
            user_info = f"El usuario se llama {user_context['user_name']}."
        
        # Obtener información de branding
        branding = tenant_config.get('branding', {}) if tenant_config else {}
        if isinstance(branding, dict):
            candidate_name = branding.get('candidate_name', candidate_name)
        
        prompt = f"""
Eres un asistente virtual de la campaña política de {contact_name}.

**TU PERSONALIDAD:**
- Eres amigable, cercano y auténtico
- Representas a {contact_name} y su campaña
- Usas un tono conversacional pero profesional
- Muestras pasión y entusiasmo por la campaña
- Respondes a saludos y mensajes de apoyo con calidez

**CONTEXTO:**
{user_info}
El usuario acaba de escribir: "{query}"

**DOCUMENTOS DISPONIBLES (opcional - úsalos solo si añaden valor):**
{context if context and context.strip() != "No se encontraron documentos relevantes." else "No hay documentos específicos necesarios para este saludo."}

**INSTRUCCIONES PARA RESPONDER:**
1. Reconoce que esto es un SALUDO o MENSAJE DE APOYO, NO una pregunta técnica
2. Responde de manera cálida, amigable y entusiasta
3. Agradece el apoyo o saludo si es apropiado
4. Si el contexto tiene información relevante sobre la campaña, puedes mencionarla brevemente
5. NO busques "información sobre" nombres o términos técnicos - es un saludo, no una consulta
6. Puedes invitar al usuario a hacer preguntas sobre la campaña o propuestas
7. Mantén la respuesta breve (2-4 oraciones máximo)
8. **CRÍTICO:** NO uses citas de documentos [Documento N]
9. **CRÍTICO:** NO uses prefijos como "Respuesta basada en documentos" o "💡 Respuesta basada en documentos"
10. **CRÍTICO:** NO incluyas secciones de "📚 Fuentes:" o "📚 **Fuentes:**"
11. Responde SOLO con el mensaje cálido y natural, sin elementos técnicos

**EJEMPLOS DE SALUDOS/APOYOS:**
- Si el usuario dice algo como "Listo, con toda con {contact_name}!" o "Vamos con {contact_name}!" → Responde con entusiasmo agradeciendo el apoyo (ejemplo: "¡Qué energía tan bacana! Nos encanta sentir ese apoyo. ¡Claro que sí, con toda con {contact_name} para construir el futuro que Colombia merece!")
- Si el usuario dice "Hola" → Saluda amigablemente y ofrece ayuda (ejemplo: "¡Hola! Me alegra saludarte. ¿En qué puedo ayudarte hoy?")
- Si el usuario dice "Vamos con todo!" o mensajes de apoyo similares → Responde con energía y agradecimiento (ejemplo: "¡Excelente! Esa energía es la que necesitamos. ¡Vamos con todo para lograr el cambio que Colombia merece!")

**TU RESPUESTA (breve, cálida, entusiasta, SIN prefijos técnicos, SIN citas, SIN secciones de fuentes):**
"""
        return prompt
    
    def _clean_greeting_response(self, response: str) -> str:
        """
        Limpia la respuesta de saludo removiendo prefijos técnicos y citas
        
        Args:
            response: Respuesta generada
            
        Returns:
            Respuesta limpia sin prefijos técnicos ni citas
        """
        import re
        
        cleaned = response.strip()
        
        # Remover prefijos comunes
        prefixes_to_remove = [
            r"^💡\s*\*?Respuesta basada en documentos.*?\*?:?\s*\n*\n*",
            r"^💡\s*Respuesta basada en documentos.*?:?\s*\n*\n*",
            r"^Respuesta basada en documentos.*?:?\s*\n*\n*",
        ]
        
        for pattern in prefixes_to_remove:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remover secciones de fuentes
        source_patterns = [
            r"\n*\n*📚\s*\*?\*?Fuentes?\*?\*?:?\s*\n*.*?$",
            r"\n*\n*📚\s*Fuentes?\s*:?\s*\n*.*?$",
            r"\n*\n*\*\*Fuentes?\*\*:?\s*\n*.*?$",
            r"\n*\n*Fuentes?\s*:?\s*\n*.*?$",
        ]
        
        for pattern in source_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
        
        # Remover citas de documentos [Documento N] o [1], etc.
        cleaned = re.sub(r'\[Documento\s+\d+\]', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\[Doc\s+\d+\]', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\[Fuente\s+\d+\]', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\[\d+\]', '', cleaned)
        
        # Limpiar espacios múltiples y líneas vacías
        cleaned = re.sub(r'\n\n\n+', '\n\n', cleaned)
        cleaned = re.sub(r' +', ' ', cleaned)
        
        return cleaned.strip()
    
    async def _generate_response(
        self, 
        prompt: str,
        task_type: str = "rag_generation"
    ) -> str:
        """
        Genera la respuesta usando Gemini
        
        Args:
            prompt: Prompt completo
            task_type: Tipo de tarea para configuración
            
        Returns:
            Respuesta generada
        """
        logger.info(f"🔍 [GENERATE_RESPONSE] Iniciando generación de respuesta...")
        logger.info(f"🔍 [GENERATE_RESPONSE] ¿gemini_client disponible? {self.gemini_client is not None}")
        logger.info(f"🔍 [GENERATE_RESPONSE] Longitud del prompt: {len(prompt)} caracteres")
        logger.info(f"🔍 [GENERATE_RESPONSE] Primeros 500 chars del prompt: {prompt[:500]}")
        
        if not self.gemini_client:
            logger.error("❌ [GENERATE_RESPONSE] GeminiClient no disponible")
            return "Lo siento, el servicio de IA no está disponible en este momento."
        
        try:
            logger.info(f"🔍 [GENERATE_RESPONSE] Llamando a gemini_client.generate_content...")
            response = await self.gemini_client.generate_content(
                prompt=prompt,
                task_type=task_type,
                use_custom_config=True
            )
            
            logger.info(f"✅ [GENERATE_RESPONSE] Respuesta generada ({len(response) if response else 0} caracteres)")
            if response:
                logger.info(f"✅ [GENERATE_RESPONSE] Primeros 200 chars: {response[:200]}")
            else:
                logger.warning(f"⚠️ [GENERATE_RESPONSE] Respuesta vacía o None")
            
            return response if response else "No pude generar una respuesta. Por favor intenta de nuevo."
            
        except Exception as e:
            logger.error(f"❌ [GENERATE_RESPONSE] Error generando respuesta: {str(e)}")
            import traceback
            logger.error(f"❌ [GENERATE_RESPONSE] Traceback: {traceback.format_exc()}")
            return f"Lo siento, hubo un error al procesar tu consulta: {str(e)}"
    
    async def process_query(
        self, 
        query: str, 
        tenant_id: str,
        user_context: Dict[str, Any] = None,
        max_docs: int = 3,
        tenant_config: Dict[str, Any] = None
    ) -> RAGResponse:
        """
        Procesa un query completo usando RAG
        
        Este es el método principal que orquesta todo el flujo:
        1. Rewrite query
        2. Retrieve documents
        3. Build context
        4. Generate response
        5. Verify response
        6. Add citations
        
        Args:
            query: Pregunta del usuario
            tenant_id: ID del tenant
            user_context: Contexto adicional del usuario
            max_docs: Máximo número de documentos a usar
            
        Returns:
            RAGResponse con respuesta completa y metadata
        """
        logger.info(f"Procesando query RAG: '{query}' para tenant {tenant_id}")
        
        start_time = None
        try:
            import time
            start_time = time.time()
        except:
            pass
        
        # 1. Query Rewriting
        logger.info("1️⃣ Reescribiendo query...")
        queries = await self._rewrite_query(query)
        
        # 2. Obtener contexto relevante (compatible con y sin LlamaIndex)
        logger.info("2️⃣ Recuperando contexto desde DocumentContextService...")
        try:
            from chatbot_ai_service.services.document_context_service import document_context_service
            context = await document_context_service.get_relevant_context(tenant_id, query, max_results=max_docs)
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo contexto: {e}")
            context = ""

        # Construir lista mínima de documentos para verificación/citas
        documents = []
        if context and context.strip():
            try:
                # Crear una fuente sintética si no tenemos objetos reales
                documents = [
                    SearchResult(
                        doc_id="synthetic_context",
                        filename="Contexto consolidado",
                        content=context,
                        score=1.0,
                        match_type="aggregated"
                    )
                ]
            except Exception as _e:
                logger.debug(f"No se pudo crear fuente sintética: {_e}")
        
        # 3. Build Context (noop si ya viene listo)
        logger.info("3️⃣ Construyendo contexto...")
        if not context:
            context = "No se encontraron documentos relevantes."
        
        # 4. Build Prompt
        logger.info("4️⃣ Construyendo prompt...")
        prompt = self._build_rag_prompt(query, context, user_context, tenant_config)
        
        # 5. Generate Response
        logger.info("5️⃣ Generando respuesta...")
        logger.info(f"🔍 [PROCESS_QUERY] Prompt length: {len(prompt)} chars")
        logger.info(f"🔍 [PROCESS_QUERY] Prompt first 500 chars: {prompt[:500]}")
        response = await self._generate_response(prompt)
        logger.info(f"🔍 [PROCESS_QUERY] Response received: {len(response) if response else 0} chars")
        logger.info(f"🔍 [PROCESS_QUERY] Response content: {response[:200] if response else 'None'}")
        
        # 🛡️ FASE 5: Verificación con Guardrails
        guardrail_result = None
        sanitization_applied = False
        
        # 🎯 NUEVO: Detectar si es saludo para aplicar guardrails más flexibles
        is_greeting = self._is_greeting_or_support(query)
        
        if self.enable_guardrails:
            logger.info("6️⃣ Verificando guardrails...")
            guardrail_result = self.guardrail_verifier.verify(
                response=response,
                documents=documents,
                query=query
            )
            
            logger.info(
                f"   └─ Score: {guardrail_result.score:.0%}, "
                f"Critical: {guardrail_result.critical_failures}, "
                f"Warnings: {guardrail_result.warnings}"
            )
            
            # Si falla guardrails, sanitizar (pero ser más flexible con saludos)
            if not guardrail_result.all_passed:
                logger.warning(f"⚠️ Guardrails no pasados: {guardrail_result.recommendation}")
                
                # Para saludos, solo sanitizar si hay fallas críticas graves
                if is_greeting:
                    # Para saludos, ser más flexible - solo sanitizar si hay problemas de seguridad
                    if self.strict_guardrails and guardrail_result.critical_failures > 2:
                        logger.info("7️⃣ Sanitizando respuesta de saludo (modo flexible)...")
                        response, changes = self.response_sanitizer.sanitize(
                            response=response,
                            documents=documents,
                            guardrail_result=guardrail_result
                        )
                        sanitization_applied = True
                        logger.info(f"   └─ Cambios aplicados: {len(changes)}")
                    else:
                        logger.info("   └─ Saludo detectado - guardrails flexibles aplicados")
                else:
                    # Para preguntas técnicas, aplicar guardrails estrictos normalmente
                    if self.strict_guardrails and guardrail_result.critical_failures > 0:
                        logger.info("7️⃣ Sanitizando respuesta...")
                        response, changes = self.response_sanitizer.sanitize(
                            response=response,
                            documents=documents,
                            guardrail_result=guardrail_result
                        )
                        sanitization_applied = True
                        logger.info(f"   └─ Cambios aplicados: {len(changes)}")
        
        # 8. Verify Response (SourceVerifier)
        verification = None
        if self.enable_verification:
            logger.info("8️⃣ Verificando fuentes...")
            verification = self.verifier.verify_response(response, documents)
        else:
            verification = VerificationResult(
                is_verified=True,
                confidence=1.0,
                unsupported_claims=[],
                sources_used=[],
                hallucination_risk=0.0,
                recommendation="Verificación deshabilitada"
            )
        
        # 9. Add Citations (skip for greetings)
        response_with_citations = response
        if self.enable_citations and not is_greeting:
            logger.info("9️⃣ Agregando citas...")
            response_with_citations = self.verifier.add_citations(response, documents)
        elif is_greeting:
            logger.info("9️⃣ Saltando citas para saludo/apoyo")
            # Limpiar cualquier prefijo o cita que pueda haber sido agregado
            response_with_citations = self._clean_greeting_response(response)
        
        # Calculate processing time
        processing_time = None
        if start_time:
            try:
                processing_time = time.time() - start_time
            except:
                pass
        
        # Build metadata
        metadata = {
            "query": query,
            "tenant_id": tenant_id,
            "num_documents_retrieved": len(documents),
            "num_queries_generated": len(queries),
            "verification_enabled": self.enable_verification,
            "citations_enabled": self.enable_citations,
            "guardrails_enabled": self.enable_guardrails,
            "processing_time_seconds": processing_time
        }
        
        # Agregar metadata de guardrails si está habilitado
        if guardrail_result:
            metadata["guardrail_score"] = guardrail_result.score
            metadata["guardrail_passed"] = guardrail_result.all_passed
            metadata["critical_failures"] = guardrail_result.critical_failures
            metadata["warnings"] = guardrail_result.warnings
            metadata["sanitization_applied"] = sanitization_applied
        
        # Log de documentos utilizados para la respuesta
        if documents:
            doc_names = [doc.filename for doc in documents]
            logger.info(f"DOCUMENTOS UTILIZADOS PARA LA RESPUESTA: {doc_names}")
        else:
            logger.info("RESPUESTA GENERADA SIN DOCUMENTOS (información general)")
        
        logger.info(
            f"Query RAG procesado exitosamente "
            f"({len(documents)} docs, {processing_time:.2f}s)" if processing_time else ""
        )
        
        return RAGResponse(
            response=response,
            response_with_citations=response_with_citations,
            verification=verification,
            retrieved_documents=documents,
            metadata=metadata,
            guardrail_result=guardrail_result,
            sanitization_applied=sanitization_applied
        )
    
    async def process_query_simple(
        self, 
        query: str, 
        tenant_id: str,
        user_context: Dict[str, Any] = None,
        session_id: str = None,
        tenant_config: Dict[str, Any] = None
    ) -> str:
        """
        Versión simplificada que solo retorna la respuesta con citas
        INCLUYE contexto de sesión para mantener continuidad
        
        Args:
            query: Pregunta del usuario
            tenant_id: ID del tenant
            user_context: Contexto del usuario
            session_id: ID de sesión para contexto persistente
            tenant_config: Configuración del tenant para personalización
            
        Returns:
            Respuesta con citas (string)
        """
        # 🔧 FIX: Incluir contexto de sesión si está disponible
        if session_id:
            try:
                from chatbot_ai_service.services.session_context_service import session_context_service
                session_context = session_context_service.build_context_for_ai(session_id)
                if session_context:
                    # Agregar contexto de sesión al user_context
                    if not user_context:
                        user_context = {}
                    user_context["session_context"] = session_context
                    logger.info(f"✅ Contexto de sesión incluido en RAG: {len(session_context)} chars")
            except Exception as e:
                logger.warning(f"⚠️ Error obteniendo contexto de sesión: {str(e)}")
        
        logger.info(f"🔍 [RAG_SIMPLE] Procesando query: '{query[:100]}...'")
        rag_response = await self.process_query(query, tenant_id, user_context, tenant_config=tenant_config)
        
        logger.info(f"🔍 [RAG_SIMPLE] Respuesta recibida: {len(rag_response.response) if rag_response.response else 0} caracteres")
        if rag_response.response:
            logger.info(f"🔍 [RAG_SIMPLE] Primeros 200 chars: {rag_response.response[:200]}")
        else:
            logger.warning(f"🔍 [RAG_SIMPLE] Respuesta vacía o None")
        
        # 🎯 DETECTAR SI ES SALUDO Y LIMPIAR CITAS
        is_greeting = self._is_greeting_or_support(query)
        
        if is_greeting:
            logger.info(f"🔍 [RAG_SIMPLE] Saludo detectado - limpiando citas y prefijos técnicos")
            # Usar la respuesta sin citas y limpiarla
            cleaned_response = self._clean_greeting_response(rag_response.response)
            return cleaned_response
        
        if self.enable_citations:
            logger.info(f"🔍 [RAG_SIMPLE] Devolviendo respuesta con citas")
            return rag_response.response_with_citations
        else:
            logger.info(f"🔍 [RAG_SIMPLE] Devolviendo respuesta sin citas")
            return rag_response.response


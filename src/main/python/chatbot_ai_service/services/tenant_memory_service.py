"""
Servicio de memoria persistente por tenant-usuario

Mantiene una "conciencia" del tenant para cada usuario, formada al iniciar el servicio
usando los datos precargados. Esto permite respuestas más rápidas sin buscar cada vez.

AHORA CON PERSISTENCIA EN FIRESTORE
"""
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from chatbot_ai_service.config.firebase_config import get_firebase_config
from google.cloud import firestore

logger = logging.getLogger(__name__)

@dataclass
class TenantConsciousness:
    """Representa la conciencia del tenant para un usuario específico"""
    tenant_id: str
    user_phone: str
    tenant_config: Dict[str, Any]
    document_summary: str
    campaign_context: str
    common_responses: Dict[str, str]  # Cache de respuestas frecuentes
    last_updated: float
    created_at: float

@dataclass
class TenantMemory:
    """Memoria global del tenant con información precargada"""
    tenant_id: str
    tenant_config: Dict[str, Any]
    document_summary: str
    campaign_context: str
    common_questions: List[str]
    precomputed_responses: Dict[str, str]
    last_updated: float

class TenantMemoryService:
    """Servicio para gestionar memoria persistente por tenant-usuario"""
    
    def __init__(self):
        # 🗄️ NUEVO: Conectar con Firestore para persistencia
        firebase = get_firebase_config()
        self.db = firebase.get_firestore()
        
        # Memoria global por tenant (se forma al iniciar el servicio)
        self._tenant_memories: Dict[str, TenantMemory] = {}
        
        # Conciencia específica por usuario-tenant
        self._user_consciousness: Dict[str, TenantConsciousness] = {}
        
        # TTL para limpiar memorias inactivas
        self._memory_ttl = 3600  # 1 hora
        self._consciousness_ttl = 1800  # 30 minutos
        
        logger.info("🧠 TenantMemoryService inicializado con persistencia Firestore")
    
    def initialize_tenant_memory(self, tenant_id: str, tenant_config: Dict[str, Any], 
                                document_summary: str = "") -> bool:
        """Inicializa la memoria global del tenant al arrancar el servicio"""
        try:
            # Crear contexto de campaña desde la configuración
            campaign_context = self._build_campaign_context(tenant_config)
            
            # Crear preguntas comunes basadas en la configuración
            common_questions = self._generate_common_questions(tenant_config)
            
            # Precomputar respuestas comunes
            precomputed_responses = self._precompute_common_responses(
                tenant_config, campaign_context, common_questions
            )
            
            memory = TenantMemory(
                tenant_id=tenant_id,
                tenant_config=tenant_config,
                document_summary=document_summary,
                campaign_context=campaign_context,
                common_questions=common_questions,
                precomputed_responses=precomputed_responses,
                last_updated=time.time()
            )
            
            self._tenant_memories[tenant_id] = memory
            
            # 🗄️ NUEVO: Guardar en Firestore para persistencia
            try:
                memory_dict = {
                    'tenant_id': tenant_id,
                    'tenant_config': json.dumps(tenant_config),  # Serializar config
                    'document_summary': document_summary,
                    'campaign_context': campaign_context,
                    'common_questions': common_questions,
                    'precomputed_responses': json.dumps(precomputed_responses),  # Serializar
                    'last_updated': time.time(),
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'version': '2.0'  # Marcar versión del formato
                }
                
                doc_ref = self.db.collection('tenant_memory_cache').document(tenant_id)
                doc_ref.set(memory_dict)
                
                logger.info(f"🗄️ Memoria del tenant {tenant_id} guardada en Firestore")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo guardar en Firestore (continuando): {e}")
            
            logger.info(f"🧠 Memoria del tenant {tenant_id} inicializada:")
            logger.info(f"  - Contexto de campaña: {len(campaign_context)} caracteres")
            logger.info(f"  - Preguntas comunes: {len(common_questions)}")
            logger.info(f"  - Respuestas precomputadas: {len(precomputed_responses)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando memoria del tenant {tenant_id}: {e}")
            return False
    
    def get_or_create_user_consciousness(self, tenant_id: str, user_phone: str) -> TenantConsciousness:
        """Obtiene o crea la conciencia específica del usuario para el tenant"""
        consciousness_key = f"{tenant_id}:{user_phone}"
        
        # Limpiar conciencias expiradas
        self._cleanup_expired_consciousness()
        
        if consciousness_key in self._user_consciousness:
            consciousness = self._user_consciousness[consciousness_key]
            consciousness.last_updated = time.time()
            return consciousness
        
        # Crear nueva conciencia basada en la memoria del tenant
        tenant_memory = self._tenant_memories.get(tenant_id)
        if not tenant_memory:
            logger.warning(f"⚠️ No hay memoria del tenant {tenant_id} para crear conciencia")
            return None
        
        consciousness = TenantConsciousness(
            tenant_id=tenant_id,
            user_phone=user_phone,
            tenant_config=tenant_memory.tenant_config.copy(),
            document_summary=tenant_memory.document_summary,
            campaign_context=tenant_memory.campaign_context,
            common_responses=tenant_memory.precomputed_responses.copy(),
            last_updated=time.time(),
            created_at=time.time()
        )
        
        self._user_consciousness[consciousness_key] = consciousness
        
        logger.info(f"🧠 Nueva conciencia creada: {tenant_id}:{user_phone}")
        return consciousness
    
    def get_fast_response(self, tenant_id: str, user_phone: str, query: str) -> Optional[str]:
        """Intenta obtener una respuesta rápida desde la conciencia del usuario"""
        consciousness = self.get_or_create_user_consciousness(tenant_id, user_phone)
        if not consciousness:
            logger.warning(f"⚠️ No se pudo crear conciencia para {tenant_id}:{user_phone}")
            return None
        
        query_lower = query.lower().strip()
        logger.info(f"🔍 Buscando respuesta rápida para: '{query_lower}' en tenant {tenant_id}")
        logger.info(f"🔍 Patrones disponibles: {list(consciousness.common_responses.keys())}")
        
        # Buscar respuesta precomputada con coincidencia flexible
        for pattern, response in consciousness.common_responses.items():
            if pattern in query_lower:
                logger.info(f"🚀 Respuesta rápida encontrada para patrón: '{pattern}' en consulta: '{query_lower}'")
                return response
        
        # Buscar coincidencias parciales (palabras clave)
        for pattern, response in consciousness.common_responses.items():
            pattern_words = pattern.split()
            if any(word in query_lower for word in pattern_words):
                logger.info(f"🚀 Respuesta rápida encontrada por palabra clave: '{pattern}' en consulta: '{query_lower}'")
                return response
        
        # Buscar en preguntas comunes desde la memoria del tenant
        tenant_memory = self._tenant_memories.get(tenant_id)
        if tenant_memory and tenant_memory.common_questions:
            for question in tenant_memory.common_questions:
                if any(word in query_lower for word in question.lower().split()):
                    # Generar respuesta rápida basada en el contexto
                    logger.info(f"🚀 Respuesta rápida encontrada por pregunta común: '{question}' en consulta: '{query_lower}'")
                    return self._generate_quick_response(consciousness, query)
        
        logger.info(f"⚠️ No se encontró respuesta rápida para: '{query_lower}' - continuando con flujo normal")
        return None
    
    def update_user_context(self, tenant_id: str, user_phone: str, 
                           context_data: Dict[str, Any]) -> bool:
        """Actualiza el contexto específico del usuario"""
        consciousness = self.get_or_create_user_consciousness(tenant_id, user_phone)
        if not consciousness:
            return False
        
        # Actualizar contexto del usuario en la configuración
        if 'user_context' not in consciousness.tenant_config:
            consciousness.tenant_config['user_context'] = {}
        
        consciousness.tenant_config['user_context'].update(context_data)
        consciousness.last_updated = time.time()
        
        logger.info(f"🧠 Contexto actualizado para {tenant_id}:{user_phone}")
        return True
    
    def get_tenant_context(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el contexto completo del tenant"""
        tenant_memory = self._tenant_memories.get(tenant_id)
        if not tenant_memory:
            return None
        
        return {
            'tenant_config': tenant_memory.tenant_config,
            'campaign_context': tenant_memory.campaign_context,
            'document_summary': tenant_memory.document_summary,
            'common_questions': tenant_memory.common_questions,
            'precomputed_responses': tenant_memory.precomputed_responses
        }
    
    def _build_campaign_context(self, tenant_config: Dict[str, Any]) -> str:
        """Construye el contexto de campaña desde la configuración"""
        context_parts = []
        
        # Información de branding
        branding = tenant_config.get('branding', {})
        if branding:
            contact_name = branding.get('contactName', 'el candidato')
            candidate_name = branding.get('candidateName', contact_name)
            campaign_name = branding.get('campaignName', 'la campaña')
            
            context_parts.append(f"Candidato: {candidate_name}")
            context_parts.append(f"Campaña: {campaign_name}")
            context_parts.append(f"Contacto: {contact_name}")
            
            if branding.get('welcomeMessage'):
                context_parts.append(f"Mensaje de bienvenida: {branding['welcomeMessage']}")
        
        # Información de features
        features = tenant_config.get('features', {})
        if features:
            if features.get('ai_enabled'):
                context_parts.append("IA habilitada para respuestas inteligentes")
            if features.get('referrals_enabled'):
                context_parts.append("Sistema de referidos activo")
        
        # Información de AI
        ai_config = tenant_config.get('aiConfig', {})
        if ai_config:
            model = ai_config.get('model', 'gemini-pro')
            context_parts.append(f"Modelo de IA: {model}")
        
        return "\n".join(context_parts)
    
    def _generate_common_questions(self, tenant_config: Dict[str, Any]) -> List[str]:
        """Genera preguntas comunes basadas en la configuración del tenant"""
        questions = []
        
        branding = tenant_config.get('branding', {})
        contact_name = branding.get('contactName', 'el candidato')
        
        # Preguntas comunes de campaña política
        questions.extend([
            f"¿Quién es {contact_name}?",
            f"¿Cuáles son las propuestas de {contact_name}?",
            f"¿Cómo puedo apoyar a {contact_name}?",
            f"¿Dónde puedo conocer más sobre {contact_name}?",
            f"¿Cuáles son los logros de {contact_name}?",
            "¿Cómo puedo participar en la campaña?",
            "¿Qué hace diferente a este candidato?",
            "¿Cómo puedo ayudar como voluntario?",
            "¿Dónde puedo agendar una cita?",
            "¿Cómo funciona el sistema de referidos?"
        ])
        
        return questions
    
    def _precompute_common_responses(self, tenant_config: Dict[str, Any], 
                                   campaign_context: str, 
                                   common_questions: List[str]) -> Dict[str, str]:
        """Precomputa respuestas comunes para acelerar las respuestas"""
        responses = {}
        
        branding = tenant_config.get('branding', {})
        contact_name = branding.get('contactName', 'el candidato')
        
        # Respuestas precomputadas para preguntas frecuentes
        responses.update({
            "quien es": f"{contact_name} es nuestro candidato. Puedo contarte más sobre sus propuestas y logros.",
            "quien eres": f"¡Hola! Soy el asistente virtual de la campaña de {contact_name}. ¿En qué puedo ayudarte?",
            "propuestas": f"Las propuestas de {contact_name} están enfocadas en mejorar nuestra comunidad. ¿Te interesa algún tema específico?",
            "apoyar": f"Puedes apoyar a {contact_name} de varias formas: como voluntario, compartiendo información, o participando en eventos.",
            "voluntario": f"¡Excelente! Como voluntario puedes ayudar con difusión, eventos y organización. ¿En qué área te interesa participar?",
            "cita": f"Puedes agendar una cita para conocer más sobre {contact_name} y sus propuestas.",
            "referidos": "El sistema de referidos te permite invitar amigos y familiares a conocer la campaña. Cada referido registrado suma puntos.",
            "hola": f"¡Hola! Soy el asistente virtual de la campaña de {contact_name}. ¿En qué puedo ayudarte?",
            "gracias": f"¡De nada! Estoy aquí para ayudarte con cualquier pregunta sobre {contact_name} y la campaña."
        })
        
        return responses
    
    def get_fast_intent_classification(self, tenant_id: str, query: str) -> Optional[Dict[str, Any]]:
        """Clasificación rápida de intenciones usando patrones precargados"""
        tenant_memory = self._tenant_memories.get(tenant_id)
        if not tenant_memory:
            return None
        
        query_lower = query.lower().strip()
        
        # Patrones de intención precomputados
        intent_patterns = {
            "saludo_apoyo": ["hola", "hi", "hello", "hey", "buenos días", "buenas tardes", "buenas noches", "qué tal", "que tal", "quien eres", "quien es"],
            "propuestas_campaña": ["propuestas", "propuesta", "plan", "planes", "proyecto", "proyectos", "educación", "salud", "trabajo"],
            "voluntariado": ["voluntario", "voluntarios", "ayudar", "participar", "colaborar", "trabajar", "unirme"],
            "cita_campaña": ["cita", "citas", "agendar", "reunión", "reuniones", "conocer", "hablar"],
            "publicidad_info": ["folleto", "folletos", "material", "materiales", "publicidad", "difusión", "propaganda", "brochure", "panfleto", "información publicitaria"],
            "actualizacion_datos": ["actualizar", "actualizar datos", "corregir", "cambiar", "modificar", "mi nombre es", "mi apellido es", "vivo en", "mi ciudad es", "cambiar mi"],
            "atencion_humano": ["quiero que me atienda un agente humano", "asesor", "quisiera hablar con un asesor", "hablar con persona", "atencion humana", "agente humano", "quiero hablar con alguien", "necesito un humano", "me atienda una persona"],
            "referidos": ["referido", "referidos", "invitar", "invitar amigos", "compartir", "recomendar"],
            "agradecimiento": ["gracias", "thank you", "muchas gracias", "te agradezco", "appreciate"],
            "despedida": ["adiós", "adios", "bye", "hasta luego", "nos vemos", "chao"],
            "información_general": ["información", "info", "saber", "conocer", "entender", "explicar"]
        }
        
        # Buscar coincidencias de intención
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    confidence = 0.9 if pattern in query_lower else 0.7
                    logger.info(f"🚀 Intención rápida encontrada: '{intent}' para patrón: '{pattern}' en consulta: '{query_lower}'")
                    return {
                        "category": intent,
                        "confidence": confidence,
                        "source": "memory_patterns"
                    }
        
        return None
    
    def _generate_quick_response(self, consciousness: TenantConsciousness, query: str) -> str:
        """Genera una respuesta rápida basada en la conciencia del usuario"""
        branding = consciousness.tenant_config.get('branding', {})
        contact_name = branding.get('contactName', 'el candidato')
        
        # Respuesta genérica rápida
        return f"Basándome en la información de {contact_name}, puedo ayudarte con eso. ¿Te gustaría que profundice en algún aspecto específico?"
    
    def _cleanup_expired_consciousness(self):
        """Limpia las conciencias de usuario expiradas"""
        current_time = time.time()
        expired_keys = []
        
        for key, consciousness in self._user_consciousness.items():
            if current_time - consciousness.last_updated > self._consciousness_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._user_consciousness[key]
            logger.info(f"🧠 Conciencia expirada eliminada: {key}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la memoria"""
        return {
            'tenant_memories': len(self._tenant_memories),
            'user_consciousness': len(self._user_consciousness),
            'memory_ttl': self._memory_ttl,
            'consciousness_ttl': self._consciousness_ttl
        }
    
    def load_tenant_memory_from_firestore(self, tenant_id: str) -> bool:
        """
        Carga la memoria del tenant desde Firestore al reiniciar el servicio
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            True si se cargó exitosamente
        """
        try:
            doc_ref = self.db.collection('tenant_memory_cache').document(tenant_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.warning(f"⚠️ No existe memoria guardada para tenant {tenant_id} en Firestore")
                return False
            
            data = doc.to_dict()
            
            # Deserializar campos JSON
            tenant_config = json.loads(data.get('tenant_config', '{}'))
            precomputed_responses = json.loads(data.get('precomputed_responses', '{}'))
            
            # Reconstruir memoria
            memory = TenantMemory(
                tenant_id=tenant_id,
                tenant_config=tenant_config,
                document_summary=data.get('document_summary', ''),
                campaign_context=data.get('campaign_context', ''),
                common_questions=data.get('common_questions', []),
                precomputed_responses=precomputed_responses,
                last_updated=data.get('last_updated', time.time())
            )
            
            # Cargar en memoria RAM
            self._tenant_memories[tenant_id] = memory
            
            logger.info(f"✅ Memoria cargada desde Firestore para tenant {tenant_id}")
            logger.info(f"  - Preguntas comunes: {len(memory.common_questions)}")
            logger.info(f"  - Respuestas precomputadas: {len(memory.precomputed_responses)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cargando memoria desde Firestore para tenant {tenant_id}: {e}")
            return False
    
    def get_all_tenant_memories_from_firestore(self) -> List[str]:
        """
        Obtiene lista de todos los tenant IDs que tienen memoria guardada
        
        Returns:
            Lista de tenant IDs
        """
        if self.db is None:
            logger.warning("⚠️ Firestore no disponible - no se pueden obtener memorias de tenant")
            return []
        
        try:
            docs = self.db.collection('tenant_memory_cache').get()
            tenant_ids = [doc.id for doc in docs]
            logger.info(f"✅ {len(tenant_ids)} memorias de tenant encontradas en Firestore")
            return tenant_ids
        except Exception as e:
            logger.error(f"❌ Error obteniendo memorias desde Firestore: {e}")
            return []
    
    def get_tenant_precomputed_responses(self, tenant_id: str) -> Optional[Dict[str, str]]:
        """
        Obtiene las respuestas precomputadas de un tenant
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            Diccionario con respuestas precomputadas o None
        """
        tenant_memory = self._tenant_memories.get(tenant_id)
        if tenant_memory and tenant_memory.precomputed_responses:
            logger.info(f"✅ {len(tenant_memory.precomputed_responses)} respuestas precomputadas disponibles para tenant {tenant_id}")
            return tenant_memory.precomputed_responses
        
        logger.warning(f"⚠️ No hay respuestas precomputadas para tenant {tenant_id}")
        return None
    
    def get_tenant_common_questions(self, tenant_id: str) -> List[str]:
        """
        Obtiene las preguntas comunes de un tenant
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            Lista de preguntas comunes
        """
        tenant_memory = self._tenant_memories.get(tenant_id)
        if tenant_memory and tenant_memory.common_questions:
            return tenant_memory.common_questions
        return []
    
    def get_tenant_campaign_context(self, tenant_id: str) -> str:
        """
        Obtiene el contexto de campaña de un tenant
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            Contexto de campaña como string
        """
        tenant_memory = self._tenant_memories.get(tenant_id)
        if tenant_memory:
            return tenant_memory.campaign_context
        return ""

# Instancia global del servicio
tenant_memory_service = TenantMemoryService()

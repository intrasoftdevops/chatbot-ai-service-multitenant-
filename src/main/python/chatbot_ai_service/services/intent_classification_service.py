"""
Servicio de clasificación de intenciones específicas para el sistema político
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from chatbot_ai_service.models.intent_models import (
    IntentCategory, IntentClassification, IntentAction, IntentExamples,
    IntentConfiguration, IntentStats
)
from chatbot_ai_service.models.chat_models import ClassificationRequest, ClassificationResponse
from chatbot_ai_service.services.tenant_service import TenantService
from chatbot_ai_service.services.ai_service import AIService

logger = logging.getLogger(__name__)

class IntentClassificationService:
    """Servicio para clasificación de intenciones políticas"""
    
    def __init__(self, tenant_service: TenantService, ai_service: AIService):
        self.tenant_service = tenant_service
        self.ai_service = ai_service
        self._intent_examples = self._initialize_intent_examples()
        self._action_configurations = self._initialize_action_configurations()
    
    async def classify_intent(self, request: ClassificationRequest) -> IntentClassification:
        """
        Clasifica la intención de un mensaje usando IA y reglas específicas
        """
        try:
            logger.info(f"Clasificando intención para tenant {request.tenant_id}")
            
            # Obtener configuración del tenant
            tenant_config = await self.tenant_service.get_tenant_config(request.tenant_id)
            if not tenant_config:
                return self._create_fallback_classification(request.message)
            
            # Clasificar usando IA
            ai_classification = await self.ai_service.classify_intent(request)
            
            # Mapear a categorías específicas del sistema
            intent_category = self._map_to_intent_category(ai_classification.intent, request.message)
            
            # Crear acción específica
            action = self._create_intent_action(intent_category, request.message, tenant_config)
            
            return IntentClassification(
                category=intent_category,
                confidence=ai_classification.confidence,
                original_message=request.message,
                extracted_entities=ai_classification.entities,
                action=action,
                fallback=ai_classification.fallback,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error al clasificar intención para tenant {request.tenant_id}: {e}")
            return self._create_fallback_classification(request.message)
    
    def _initialize_intent_examples(self) -> Dict[IntentCategory, IntentExamples]:
        """Inicializa ejemplos de intenciones específicas del sistema"""
        return {
            IntentCategory.MALICIOSO: IntentExamples(
                category=IntentCategory.MALICIOSO,
                examples=[
                    "Son unos ladrones",
                    "Voten por el otro candidato",
                    "Esto es una estafa",
                    "Spam spam spam",
                    "Van a perder las elecciones"
                ],
                keywords=["spam", "estafa", "ladrón", "perder", "fraude"],
                action_description="Bloquear usuario y desactivar comunicaciones"
            ),
            
            IntentCategory.CITA_CAMPANA: IntentExamples(
                category=IntentCategory.CITA_CAMPANA,
                examples=[
                    "Quiero agendar una cita",
                    "¿Cuándo pueden visitar mi barrio?",
                    "Necesito coordinar una reunión",
                    "¿Pueden venir a mi casa?",
                    "Quiero hablar con el candidato"
                ],
                keywords=["cita", "reunión", "visita", "agendar", "coordinar"],
                action_description="Enviar link de Calendly"
            ),
            
            IntentCategory.SALUDO_APOYO: IntentExamples(
                category=IntentCategory.SALUDO_APOYO,
                examples=[
                    "Hola, apoyo al candidato",
                    "Cuenten conmigo",
                    "Vamos a ganar",
                    "Candidato para presidente",
                    "Los apoyo completamente"
                ],
                keywords=["apoyo", "cuenten", "ganar", "presidente", "fuerza"],
                action_description="Responder con gratitud e invitar a compartir link y reglas de puntos"
            ),
            
            IntentCategory.PUBLICIDAD_INFO: IntentExamples(
                category=IntentCategory.PUBLICIDAD_INFO,
                examples=[
                    "Necesito material publicitario",
                    "¿Tienen afiches?",
                    "Quiero difundir la campaña",
                    "¿Cómo consigo volantes?",
                    "Necesito información para compartir"
                ],
                keywords=["publicidad", "afiche", "volante", "difundir", "material"],
                action_description="Enviar forms para solicitar publicidad"
            ),
            
            IntentCategory.CONOCER_CANDIDATO: IntentExamples(
                category=IntentCategory.CONOCER_CANDIDATO,
                examples=[
                    "¿Quién es el candidato?",
                    "¿Cuáles son sus propuestas?",
                    "¿Qué ha hecho el candidato?",
                    "¿Cuál es su experiencia?",
                    "Quiero conocer más del candidato"
                ],
                keywords=["quién", "propuestas", "experiencia", "trayectoria", "conocer"],
                action_description="Redireccionar a DQBot y avisar ciudad de visita"
            ),
            
            IntentCategory.ACTUALIZACION_DATOS: IntentExamples(
                category=IntentCategory.ACTUALIZACION_DATOS,
                examples=[
                    "Quiero cambiar mi teléfono",
                    "Mi dirección cambió",
                    "Actualizar mis datos",
                    "Corregir mi información",
                    "Cambiar mi nombre"
                ],
                keywords=["cambiar", "actualizar", "corregir", "modificar", "datos"],
                action_description="Permitir actualización dinámica de datos de voluntario"
            ),
            
            IntentCategory.SOLICITUD_FUNCIONAL: IntentExamples(
                category=IntentCategory.SOLICITUD_FUNCIONAL,
                examples=[
                    "¿Cómo voy?",
                    "¿Cuántos puntos tengo?",
                    "Link de mi tribu",
                    "¿Cómo funciona esto?",
                    "¿Cuántas personas tengo debajo?"
                ],
                keywords=["cómo voy", "puntos", "tribu", "funciona", "debajo"],
                action_description="Proporcionar información funcional del sistema"
            ),
            
            IntentCategory.COLABORACION_VOLUNTARIADO: IntentExamples(
                category=IntentCategory.COLABORACION_VOLUNTARIADO,
                examples=[
                    "Quiero ser voluntario",
                    "¿Cómo puedo ayudar?",
                    "Me ofrezco para la campaña",
                    "Quiero trabajar con ustedes",
                    "¿Necesitan ayuda?"
                ],
                keywords=["voluntario", "ayudar", "trabajar", "ofrezco", "colaborar"],
                action_description="Clasificar usuario según área de colaboración"
            ),
            
            IntentCategory.QUEJAS: IntentExamples(
                category=IntentCategory.QUEJAS,
                examples=[
                    "No me gusta esto",
                    "Esto está mal",
                    "Tengo una queja",
                    "No estoy de acuerdo",
                    "Esto es incorrecto"
                ],
                keywords=["queja", "mal", "incorrecto", "disgusto", "problema"],
                action_description="Registrar queja en base de datos con clasificación"
            ),
            
            IntentCategory.LIDER: IntentExamples(
                category=IntentCategory.LIDER,
                examples=[
                    "Soy líder comunal",
                    "Represento a mi barrio",
                    "Soy dirigente político",
                    "Lidero una organización",
                    "Soy presidente de junta"
                ],
                keywords=["líder", "comunal", "dirigente", "presidente", "represento"],
                action_description="Registrar como lead en base de datos"
            ),
            
            IntentCategory.ATENCION_HUMANO: IntentExamples(
                category=IntentCategory.ATENCION_HUMANO,
                examples=[
                    "Quiero hablar con una persona",
                    "¿Hay alguien disponible?",
                    "Necesito atención humana",
                    "¿Puedo hablar con un agente?",
                    "Esto no lo entiendo"
                ],
                keywords=["persona", "humano", "agente", "disponible", "atender"],
                action_description="Redireccionar a voluntario del Default Team"
            ),
            
            IntentCategory.ATENCION_EQUIPO_INTERNO: IntentExamples(
                category=IntentCategory.ATENCION_EQUIPO_INTERNO,
                examples=[
                    "¿Cuánta gente hay en Chocó?",
                    "¿Cuántos voluntarios hay en Bogotá?",
                    "Necesito reportes",
                    "¿Cuántos puntos tiene la campaña?",
                    "Estadísticas de mi zona"
                ],
                keywords=["estadísticas", "reporte", "cuántos", "datos internos", "información"],
                action_description="Validar permisos y conectar con BackOffice"
            )
        }
    
    def _initialize_action_configurations(self) -> Dict[IntentCategory, Dict[str, Any]]:
        """Inicializa configuraciones de acciones por categoría"""
        return {
            IntentCategory.MALICIOSO: {
                "block_user": True,
                "disable_communications": True,
                "response_message": "Tu mensaje ha sido registrado. Gracias por tu feedback.",
                "database_update": {
                    "allow_broadcast": False,
                    "allow_sms": False,
                    "blocked": True,
                    "block_reason": "malicious_content"
                }
            },
            
            IntentCategory.CITA_CAMPANA: {
                "redirect_url": "calendly_link",
                "response_message": "¡Perfecto! Te ayudo a agendar una cita. Aquí tienes el enlace:",
                "requires_calendly": True
            },
            
            IntentCategory.SALUDO_APOYO: {
                "response_message": "¡Muchas gracias por tu apoyo! Te invitamos a compartir nuestro enlace y conocer las reglas de puntos. ¡Juntos vamos a ganar!",
                "share_link": True,
                "points_rules": True
            },
            
            IntentCategory.PUBLICIDAD_INFO: {
                "redirect_url": "forms_link",
                "response_message": "¡Excelente! Te ayudo con material publicitario. Llena este formulario:",
                "requires_forms": True
            },
            
            IntentCategory.CONOCER_CANDIDATO: {
                "redirect_to_dqbot": True,
                "response_message": "Te redirijo a nuestro bot especializado para que conozcas más sobre el candidato. También te avisaremos cuando visitemos tu ciudad.",
                "city_notification": True
            },
            
            IntentCategory.ACTUALIZACION_DATOS: {
                "dynamic_update": True,
                "response_message": "Te ayudo a actualizar tus datos. ¿Qué información quieres cambiar?",
                "data_fields": ["name", "phone", "address", "city"]
            },
            
            IntentCategory.SOLICITUD_FUNCIONAL: {
                "functional_response": True,
                "response_message": "Te muestro tu información:",
                "available_queries": ["points", "tribe", "referrals", "ranking"]
            },
            
            IntentCategory.COLABORACION_VOLUNTARIADO: {
                "collaboration_classification": True,
                "response_message": "¡Excelente! Te ayudo a clasificar cómo puedes colaborar. ¿En qué área te interesa?",
                "collaboration_areas": [
                    "Redes sociales", "Comunicaciones", "Temas programáticos",
                    "Logística", "Temas jurídicos", "Trabajo territorial",
                    "Día de elecciones", "Call center", "Otro"
                ]
            },
            
            IntentCategory.QUEJAS: {
                "register_complaint": True,
                "response_message": "Gracias por tu feedback. Hemos registrado tu comentario y lo revisaremos.",
                "complaint_classification": True
            },
            
            IntentCategory.LIDER: {
                "register_lead": True,
                "response_message": "¡Perfecto! Te registramos como líder. Un miembro del equipo se pondrá en contacto contigo.",
                "lead_database": True
            },
            
            IntentCategory.ATENCION_HUMANO: {
                "redirect_to_human": True,
                "response_message": "Te conectamos con un voluntario humano del equipo.",
                "default_team": True
            },
            
            IntentCategory.ATENCION_EQUIPO_INTERNO: {
                "validate_permissions": True,
                "response_message": "Validando permisos para acceder a información interna...",
                "backoffice_connection": True
            }
        }
    
    def _map_to_intent_category(self, ai_intent: str, message: str) -> IntentCategory:
        """Mapea la intención de IA a categorías específicas del sistema"""
        message_lower = message.lower()
        
        # Mapeo específico basado en palabras clave
        if any(keyword in message_lower for keyword in ["spam", "estafa", "ladrón", "fraude"]):
            return IntentCategory.MALICIOSO
        
        if any(keyword in message_lower for keyword in ["cita", "reunión", "agendar", "visita"]):
            return IntentCategory.CITA_CAMPANA
        
        if any(keyword in message_lower for keyword in ["apoyo", "cuenten", "ganar", "fuerza"]):
            return IntentCategory.SALUDO_APOYO
        
        if any(keyword in message_lower for keyword in ["publicidad", "afiche", "volante", "material"]):
            return IntentCategory.PUBLICIDAD_INFO
        
        if any(keyword in message_lower for keyword in ["quién es", "propuestas", "conocer candidato"]):
            return IntentCategory.CONOCER_CANDIDATO
        
        if any(keyword in message_lower for keyword in ["cambiar", "actualizar", "corregir datos"]):
            return IntentCategory.ACTUALIZACION_DATOS
        
        if any(keyword in message_lower for keyword in ["cómo voy", "puntos", "tribu", "funciona"]):
            return IntentCategory.SOLICITUD_FUNCIONAL
        
        if any(keyword in message_lower for keyword in ["voluntario", "ayudar", "colaborar"]):
            return IntentCategory.COLABORACION_VOLUNTARIADO
        
        if any(keyword in message_lower for keyword in ["queja", "mal", "incorrecto"]):
            return IntentCategory.QUEJAS
        
        if any(keyword in message_lower for keyword in ["líder", "comunal", "dirigente"]):
            return IntentCategory.LIDER
        
        if any(keyword in message_lower for keyword in ["persona", "humano", "agente"]):
            return IntentCategory.ATENCION_HUMANO
        
        if any(keyword in message_lower for keyword in ["estadísticas", "reporte", "cuántos"]):
            return IntentCategory.ATENCION_EQUIPO_INTERNO
        
        # Fallback
        return IntentCategory.SOLICITUD_FUNCIONAL
    
    def _create_intent_action(self, category: IntentCategory, message: str, tenant_config) -> IntentAction:
        """Crea la acción específica para una categoría de intención"""
        config = self._action_configurations.get(category, {})
        
        return IntentAction(
            action_type=category.value,
            parameters=config,
            response_message=config.get("response_message", "Gracias por tu mensaje."),
            requires_human=config.get("redirect_to_human", False) or config.get("default_team", False),
            requires_permission=config.get("validate_permissions", False),
            database_update=config.get("database_update")
        )
    
    def _create_fallback_classification(self, message: str) -> IntentClassification:
        """Crea una clasificación de fallback"""
        return IntentClassification(
            category=IntentCategory.SOLICITUD_FUNCIONAL,
            confidence=0.3,
            original_message=message,
            extracted_entities={},
            action=IntentAction(
                action_type="fallback",
                response_message="Gracias por tu mensaje. ¿En qué más puedo ayudarte?",
                requires_human=False
            ),
            fallback=True,
            timestamp=datetime.now()
        )
    
    async def get_intent_examples(self, tenant_id: str) -> Dict[str, Any]:
        """Obtiene ejemplos de intenciones para un tenant"""
        try:
            examples = {}
            for category, intent_examples in self._intent_examples.items():
                examples[category.value] = {
                    "examples": intent_examples.examples,
                    "keywords": intent_examples.keywords,
                    "action_description": intent_examples.action_description
                }
            
            return {
                "tenant_id": tenant_id,
                "intent_categories": examples,
                "total_categories": len(examples)
            }
            
        except Exception as e:
            logger.error(f"Error al obtener ejemplos de intenciones para tenant {tenant_id}: {e}")
            return {"error": str(e)}


"""
Controlador para clasificación e intenciones en el servicio de IA multi-tenant
"""

import logging
from fastapi import APIRouter, HTTPException

from chatbot_ai_service.models.chat_models import (
    ClassificationRequest, ClassificationResponse,
    DataExtractionRequest, DataExtractionResponse,
    DataValidationRequest, DataValidationResponse,
    ReferralDetectionRequest, ReferralDetectionResponse,
    SimplePromptRequest, SimplePromptResponse
)
from chatbot_ai_service.services.ai_service import AIService
from chatbot_ai_service.services.tenant_service import TenantService
from chatbot_ai_service.services.intent_classification_service import IntentClassificationService
from chatbot_ai_service.services.action_handler_service import ActionHandlerService
from chatbot_ai_service.services.registration_data_validator import RegistrationDataValidator
from chatbot_ai_service.services.registration_intent_classifier import RegistrationIntentClassifier
from chatbot_ai_service.services.referral_detection_service import ReferralDetectionService
from chatbot_ai_service.config.firebase_config import FirebaseConfig
import time

logger = logging.getLogger(__name__)

class ClassificationController:
    """Controlador para clasificación de intenciones y extracción de datos"""
    
    def __init__(self, ai_service: AIService, tenant_service: TenantService):
        self.ai_service = ai_service
        self.tenant_service = tenant_service
        
        # Inicializar servicios específicos para clasificación de intenciones
        firebase_config = FirebaseConfig()
        self.intent_classification_service = IntentClassificationService(tenant_service, ai_service)
        self.action_handler_service = ActionHandlerService(tenant_service, firebase_config)
        
        # Inicializar nuevos servicios para registro
        self.data_validator = RegistrationDataValidator()
        self.intent_classifier = RegistrationIntentClassifier()
        self.referral_detector = ReferralDetectionService()
        
        self.router = APIRouter()
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas del controlador"""
        
        @self.router.post("/tenants/{tenant_id}/classify")
        async def classify_intent(tenant_id: str, request: ClassificationRequest):
            """
            Clasifica la intención de un mensaje para un tenant específico usando el sistema político
            """
            try:
                # Verificar que el tenant existe y está activo
                if not await self.tenant_service.is_tenant_active(tenant_id):
                    raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} no encontrado o inactivo")
                
                # Asegurar que el tenant_id en el request coincida con el de la URL
                request.tenant_id = tenant_id
                
                # Clasificar intención usando el servicio específico
                classification = await self.intent_classification_service.classify_intent(request)
                
                # Obtener configuración del tenant
                tenant_config = await self.tenant_service.get_tenant_config(tenant_id)
                
                # Ejecutar acción correspondiente
                action_result = await self.action_handler_service.execute_action(classification, tenant_config)
                
                return {
                    "classification": classification.dict(),
                    "action_result": action_result,
                    "tenant_id": tenant_id,
                    "timestamp": classification.timestamp
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error al clasificar intención para tenant {tenant_id}: {e}")
                raise HTTPException(status_code=500, detail="Error interno del servidor")
        
        @self.router.post("/tenants/{tenant_id}/extract-data", response_model=DataExtractionResponse)
        async def extract_user_data(tenant_id: str, request: DataExtractionRequest):
            """
            Extrae datos del usuario desde un mensaje para un tenant específico
            """
            try:
                # Verificar que el tenant existe y está activo
                if not await self.tenant_service.is_tenant_active(tenant_id):
                    raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} no encontrado o inactivo")
                
                # Asegurar que el tenant_id en el request coincida con el de la URL
                request.tenant_id = tenant_id
                
                # Extraer datos
                response = await self.ai_service.extract_user_data(request)
                
                return response
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error al extraer datos para tenant {tenant_id}: {e}")
                raise HTTPException(status_code=500, detail="Error interno del servidor")
        
        @self.router.get("/tenants/{tenant_id}/intent-examples")
        async def get_intent_examples(tenant_id: str):
            """
            Obtiene ejemplos de intenciones específicas del sistema político para un tenant
            """
            try:
                # Verificar que el tenant existe
                if not await self.tenant_service.is_tenant_active(tenant_id):
                    raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} no encontrado o inactivo")
                
                # Obtener ejemplos específicos del sistema político
                examples = await self.intent_classification_service.get_intent_examples(tenant_id)
                
                return examples
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error al obtener ejemplos de intenciones para tenant {tenant_id}: {e}")
                raise HTTPException(status_code=500, detail="Error interno del servidor")
        
        @self.router.get("/tenants/{tenant_id}/extraction-fields")
        async def get_extraction_fields(tenant_id: str):
            """
            Obtiene los campos disponibles para extracción de datos para un tenant
            """
            try:
                # Verificar que el tenant existe
                if not await self.tenant_service.is_tenant_active(tenant_id):
                    raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} no encontrado o inactivo")
                
                # Campos básicos para extracción
                extraction_fields = {
                    "personal_info": {
                        "name": {
                            "description": "Nombre completo del usuario",
                            "examples": ["Mi nombre es Juan", "Soy María", "Me llamo Carlos"],
                            "required": True
                        },
                        "lastname": {
                            "description": "Apellido del usuario",
                            "examples": ["Mi apellido es Pérez", "Soy García", "Apellido López"],
                            "required": True
                        },
                        "phone": {
                            "description": "Número de teléfono",
                            "examples": ["3001234567", "+57 300 123 4567", "Mi teléfono es 3001234567"],
                            "required": True
                        },
                        "city": {
                            "description": "Ciudad de residencia",
                            "examples": ["Vivo en Medellín", "Soy de Bogotá", "Ciudad: Cali"],
                            "required": True
                        }
                    },
                    "additional_info": {
                        "email": {
                            "description": "Correo electrónico",
                            "examples": ["mi.email@gmail.com", "Correo: usuario@hotmail.com"],
                            "required": False
                        },
                        "age": {
                            "description": "Edad del usuario",
                            "examples": ["Tengo 25 años", "Soy mayor de edad", "Edad: 30"],
                            "required": False
                        },
                        "profession": {
                            "description": "Profesión u ocupación",
                            "examples": ["Soy ingeniero", "Trabajo en salud", "Profesión: docente"],
                            "required": False
                        }
                    }
                }
                
                return {
                    "tenant_id": tenant_id,
                    "extraction_fields": extraction_fields,
                    "total_fields": len(extraction_fields["personal_info"]) + len(extraction_fields["additional_info"]),
                    "required_fields": [field for field, config in extraction_fields["personal_info"].items() if config["required"]]
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error al obtener campos de extracción para tenant {tenant_id}: {e}")
                raise HTTPException(status_code=500, detail="Error interno del servidor")
        
        @self.router.get("/tenants/{tenant_id}/intent-actions")
        async def get_intent_actions(tenant_id: str):
            """
            Obtiene las acciones disponibles para cada tipo de intención
            """
            try:
                # Verificar que el tenant existe
                if not await self.tenant_service.is_tenant_active(tenant_id):
                    raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} no encontrado o inactivo")
                
                # Obtener configuración del tenant
                tenant_config = await self.tenant_service.get_tenant_config(tenant_id)
                
                # Definir acciones disponibles por categoría
                intent_actions = {
                    "malicioso": {
                        "description": "Mensajes con intención negativa, spam, provocación o ataques",
                        "action": "Bloquear usuario y desactivar comunicaciones (AllowBroadcast=false, AllowSMS=false)",
                        "requires_human": False,
                        "database_update": True
                    },
                    "cita_campaña": {
                        "description": "Contacto para agendar, confirmar o coordinar una reunión",
                        "action": "Enviar link de Calendly",
                        "redirect_url": tenant_config.link_calendly if tenant_config else None,
                        "requires_human": False
                    },
                    "saludo_apoyo": {
                        "description": "Mensajes de cortesía, muestras de simpatía o expresiones de respaldo",
                        "action": "Responder con gratitud e invitar a compartir link y reglas de puntos",
                        "requires_human": False,
                        "share_content": True
                    },
                    "publicidad_info": {
                        "description": "Preguntas o solicitudes relacionadas con materiales publicitarios",
                        "action": "Enviar forms para solicitar publicidad",
                        "redirect_url": tenant_config.link_forms if tenant_config else None,
                        "requires_human": False
                    },
                    "conocer_candidato": {
                        "description": "Interés en la trayectoria, propuestas o información del candidato",
                        "action": "Redireccionar a DQBot y avisar ciudad de visita",
                        "requires_human": False,
                        "city_notification": True
                    },
                    "actualizacion_datos": {
                        "description": "Casos donde el ciudadano corrige o actualiza su información",
                        "action": "Permitir actualización dinámica de datos de voluntario",
                        "requires_human": False,
                        "dynamic_update": True
                    },
                    "solicitud_funcional": {
                        "description": "Preguntas técnicas o de uso sobre el software y plataforma",
                        "action": "Proporcionar información funcional (puntos, tribu, referidos)",
                        "requires_human": False,
                        "functional_queries": ["cómo voy", "link de mi tribu", "esto como funciona", "como van las personas debajo de mi"]
                    },
                    "colaboracion_voluntariado": {
                        "description": "Ofrecimiento de apoyo activo, voluntariado o trabajo dentro de la campaña",
                        "action": "Clasificar usuario según área de colaboración",
                        "requires_human": False,
                        "collaboration_areas": [
                            "Redes sociales", "Comunicaciones", "Temas programáticos",
                            "Logística", "Temas jurídicos", "Trabajo territorial",
                            "Día de elecciones", "Call center", "Otro"
                        ]
                    },
                    "quejas": {
                        "description": "Reclamos o comentarios negativos sobre la campaña",
                        "action": "Registrar en base de datos con clasificación del tipo de queja",
                        "requires_human": False,
                        "database_logging": True
                    },
                    "lider": {
                        "description": "Mensajes de actores que se identifican como líderes comunitarios",
                        "action": "Registrar en base de datos de leads",
                        "requires_human": True,
                        "lead_database": True
                    },
                    "atencion_humano": {
                        "description": "Mensajes de usuarios que buscan hablar con un agente humano",
                        "action": "Redireccionar a voluntario del Default Team",
                        "requires_human": True,
                        "default_team": True
                    },
                    "atencion_equipo_interno": {
                        "description": "Mensajes de personas de la campaña que requieren información rápida",
                        "action": "Validar permisos y conectar con BackOffice",
                        "requires_human": False,
                        "requires_permission": True,
                        "backoffice_connection": True
                    }
                }
                
                return {
                    "tenant_id": tenant_id,
                    "intent_actions": intent_actions,
                    "total_categories": len(intent_actions),
                    "tenant_links": {
                        "calendly": tenant_config.link_calendly if tenant_config else None,
                        "forms": tenant_config.link_forms if tenant_config else None
                    }
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error al obtener acciones de intenciones para tenant {tenant_id}: {e}")
                raise HTTPException(status_code=500, detail="Error interno del servidor")
        
        @self.router.post("/tenants/{tenant_id}/validate-data", response_model=DataValidationResponse)
        async def validate_registration_data(tenant_id: str, request: DataValidationRequest):
            """
            Valida datos de registro (nombre, apellido, ciudad, etc.)
            """
            try:
                # Verificar que el tenant existe y está activo
                if not await self.tenant_service.is_tenant_active(tenant_id):
                    raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} no encontrado o inactivo")
                
                # Asegurar que el tenant_id coincida
                request.tenant_id = tenant_id
                
                # Validar dato
                result, reason, confidence = await self.data_validator.validate_data(
                    message=request.message,
                    data_type=request.data_type,
                    tenant_id=tenant_id
                )
                
                return DataValidationResponse(
                    tenant_id=tenant_id,
                    result=result,
                    reason=reason,
                    confidence=confidence
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error al validar datos para tenant {tenant_id}: {e}")
                raise HTTPException(status_code=500, detail="Error interno del servidor")
        
        @self.router.post("/tenants/{tenant_id}/detect-referral", response_model=ReferralDetectionResponse)
        async def detect_referral_code(tenant_id: str, request: ReferralDetectionRequest):
            """
            Detecta códigos de referido en un mensaje
            """
            try:
                # Verificar que el tenant existe y está activo
                if not await self.tenant_service.is_tenant_active(tenant_id):
                    raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} no encontrado o inactivo")
                
                # Asegurar que el tenant_id coincida
                request.tenant_id = tenant_id
                
                # Detectar código de referido
                detection_result = await self.referral_detector.detect_referral_code(
                    message=request.query,
                    tenant_id=tenant_id
                )
                
                return ReferralDetectionResponse(
                    referral_code=detection_result.get("referral_code"),
                    referred_by_phone=detection_result.get("referred_by_phone"),
                    confidence=detection_result.get("confidence", 0.0)
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error al detectar código de referido para tenant {tenant_id}: {e}")
                raise HTTPException(status_code=500, detail="Error interno del servidor")
        
        @self.router.post("/tenants/{tenant_id}/classify-registration-intent", response_model=ClassificationResponse)
        async def classify_registration_intent(tenant_id: str, request: ClassificationRequest):
            """
            Clasifica la intención de un mensaje durante el registro
            """
            try:
                # Verificar que el tenant existe y está activo
                if not await self.tenant_service.is_tenant_active(tenant_id):
                    raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} no encontrado o inactivo")
                
                # Asegurar que el tenant_id coincida
                request.tenant_id = tenant_id
                
                # Clasificar intención
                intent, confidence, suggested_response = await self.intent_classifier.classify_intent(
                    message=request.message,
                    tenant_id=tenant_id
                )
                
                return ClassificationResponse(
                    tenant_id=tenant_id,
                    intent=intent,
                    confidence=confidence,
                    suggested_response=suggested_response,
                    metadata={"user_context": request.user_context}
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error al clasificar intención de registro para tenant {tenant_id}: {e}")
                raise HTTPException(status_code=500, detail="Error interno del servidor")
        
        @self.router.post("/tenants/{tenant_id}/simple-prompt", response_model=SimplePromptResponse)
        async def process_simple_prompt(tenant_id: str, request: SimplePromptRequest):
            """
            Procesa un prompt simple con IA contextual
            """
            try:
                # Verificar que el tenant existe y está activo
                if not await self.tenant_service.is_tenant_active(tenant_id):
                    raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} no encontrado o inactivo")
                
                # Asegurar que el tenant_id coincida
                request.tenant_id = tenant_id
                
                # Obtener configuración del tenant
                tenant_config = await self.tenant_service.get_tenant_config(tenant_id)
                
                # Procesar prompt
                start_time = time.time()
                response = await self.ai_service.process_simple_prompt(
                    prompt=request.prompt,
                    tenant_config=tenant_config,
                    use_documentation=request.use_documentation
                )
                processing_time = time.time() - start_time
                
                return SimplePromptResponse(
                    tenant_id=tenant_id,
                    response=response,
                    processing_time=processing_time
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error al procesar prompt simple para tenant {tenant_id}: {e}")
                raise HTTPException(status_code=500, detail="Error interno del servidor")

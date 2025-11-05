"""
Manejador de acciones de soporte y atención
"""

import logging
from typing import Dict, Any
from datetime import datetime

from chatbot_ai_service.models.intent_models import IntentClassification
from chatbot_ai_service.models.tenant_models import TenantConfig
from chatbot_ai_service.config.firebase_config import FirebaseConfig

logger = logging.getLogger(__name__)

class SupportActionHandler:
    """Manejador para acciones de soporte y atención"""
    
    def __init__(self, firebase_config: FirebaseConfig):
        self.firestore = firebase_config.firestore
    
    async def handle_complaint_action(self, classification: IntentClassification, tenant_config: TenantConfig) -> Dict[str, Any]:
        """Maneja quejas y reclamos"""
        try:
            # Registrar queja en base de datos
            complaint_data = {
                "tenant_id": tenant_config.tenant_id,
                "message": classification.original_message,
                "timestamp": datetime.now(),
                "classification": "complaint",
                "status": "pending_review"
            }
            
            await self._log_incident(
                tenant_config.tenant_id,
                "complaint",
                classification.original_message,
                complaint_data
            )
            
            return {
                "success": True,
                "action": "complaint_registered",
                "response_message": classification.action.response_message,
                "complaint_logged": True
            }
            
        except Exception as e:
            logger.error(f"Error al manejar queja: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_leader_action(self, classification: IntentClassification, tenant_config: TenantConfig) -> Dict[str, Any]:
        """Maneja mensajes de líderes comunitarios"""
        try:
            # Registrar como lead en base de datos
            leader_data = {
                "tenant_id": tenant_config.tenant_id,
                "message": classification.original_message,
                "timestamp": datetime.now(),
                "type": "leader",
                "status": "pending_contact"
            }
            
            await self._register_lead(tenant_config.tenant_id, leader_data)
            
            return {
                "success": True,
                "action": "leader_registered",
                "response_message": classification.action.response_message,
                "lead_registered": True
            }
            
        except Exception as e:
            logger.error(f"Error al manejar líder: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_human_attention_action(self, classification: IntentClassification, tenant_config: TenantConfig) -> Dict[str, Any]:
        """Maneja solicitudes de atención humana"""
        try:
            return {
                "success": True,
                "action": "human_redirect",
                "response_message": classification.action.response_message,
                "requires_human": True,
                "default_team": True
            }
            
        except Exception as e:
            logger.error(f"Error al manejar solicitud de atención humana: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_internal_team_action(self, classification: IntentClassification, tenant_config: TenantConfig) -> Dict[str, Any]:
        """Maneja solicitudes del equipo interno"""
        try:
            # Aquí se validarían permisos del usuario
            # Por ahora, simular validación
            
            return {
                "success": True,
                "action": "internal_info_request",
                "response_message": classification.action.response_message,
                "requires_permission": True,
                "backoffice_connection": True,
                "permission_validated": False  # Se validaría en el backend
            }
            
        except Exception as e:
            logger.error(f"Error al manejar solicitud interna: {e}")
            return {"success": False, "error": str(e)}
    
    async def _log_incident(self, tenant_id: str, incident_type: str, message: str, metadata: Dict[str, Any]):
        """Registra incidentes en la base de datos"""
        try:
            incident_data = {
                "tenant_id": tenant_id,
                "incident_type": incident_type,
                "message": message,
                "metadata": metadata,
                "timestamp": datetime.now(),
                "status": "pending_review"
            }
            
            # Guardar en colección de incidentes
            incidents_ref = self.firestore.collection("incidents")
            incidents_ref.add(incident_data)
            
            logger.info(f"Incidente registrado para tenant {tenant_id}: {incident_type}")
            
        except Exception as e:
            logger.error(f"Error al registrar incidente: {e}")
    
    async def _register_lead(self, tenant_id: str, leader_data: Dict[str, Any]):
        """Registra un lead en la base de datos"""
        try:
            # Guardar en colección de leads
            leads_ref = self.firestore.collection("leads")
            leads_ref.add(leader_data)
            
            logger.info(f"Lead registrado para tenant {tenant_id}")
            
        except Exception as e:
            logger.error(f"Error al registrar lead: {e}")

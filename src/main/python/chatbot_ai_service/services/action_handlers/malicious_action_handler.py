"""
Manejador de acciones maliciosas
"""

import logging
from typing import Dict, Any
from datetime import datetime

from chatbot_ai_service.models.intent_models import IntentClassification
from chatbot_ai_service.models.tenant_models import TenantConfig
from chatbot_ai_service.config.firebase_config import FirebaseConfig

logger = logging.getLogger(__name__)

class MaliciousActionHandler:
    """Manejador para acciones maliciosas"""
    
    def __init__(self, firebase_config: FirebaseConfig):
        self.firestore = firebase_config.firestore
    
    async def handle_malicious_action(self, classification: IntentClassification, tenant_config: TenantConfig) -> Dict[str, Any]:
        """Maneja acciones maliciosas - bloquear usuario"""
        try:
            # Extraer información del usuario si está disponible
            user_info = classification.extracted_entities
            
            # Actualizar base de datos para bloquear usuario
            if user_info.get("phone"):
                await self._update_user_permissions(
                    tenant_config.tenant_id,
                    user_info["phone"],
                    {
                        "allow_broadcast": False,
                        "allow_sms": False,
                        "blocked": True,
                        "block_reason": "malicious_content",
                        "blocked_at": datetime.now()
                    }
                )
            
            # Registrar incidente
            await self._log_incident(
                tenant_config.tenant_id,
                "malicious_content",
                classification.original_message,
                user_info
            )
            
            return {
                "success": True,
                "action": "user_blocked",
                "response_message": classification.action.response_message,
                "blocked_user": True,
                "database_updated": True
            }
            
        except Exception as e:
            logger.error(f"Error al manejar acción maliciosa: {e}")
            return {"success": False, "error": str(e)}
    
    async def _update_user_permissions(self, tenant_id: str, phone: str, permissions: Dict[str, Any]):
        """Actualiza permisos de usuario en la base de datos"""
        try:
            # Actualizar en colección de usuarios existente
            users_ref = self.firestore.collection("users")
            query = users_ref.where("tenant_id", "==", tenant_id).where("phone", "==", phone)
            
            docs = query.get()
            for doc in docs:
                doc.reference.update(permissions)
                logger.info(f"Permisos actualizados para usuario {phone} en tenant {tenant_id}")
                
        except Exception as e:
            logger.error(f"Error al actualizar permisos de usuario: {e}")
    
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

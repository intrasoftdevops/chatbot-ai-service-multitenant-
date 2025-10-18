"""
Servicio para notificar bloqueos de usuarios al servicio Java
"""

import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class BlockingNotificationService:
    """Servicio para notificar bloqueos de usuarios al servicio Java"""
    
    def __init__(self):
        self.java_service_url = None  # Se configurará desde variables de entorno
    
    def set_java_service_url(self, url: str):
        """Configura la URL del servicio Java"""
        self.java_service_url = url
    
    async def notify_user_blocked(self, tenant_id: str, user_id: str, phone_number: str, 
                                malicious_message: str, classification_confidence: float) -> Dict[str, Any]:
        """
        Notifica al servicio Java que un usuario debe ser bloqueado
        
        Args:
            tenant_id: ID del tenant
            user_id: ID del usuario
            phone_number: Número de teléfono del usuario
            malicious_message: Mensaje malicioso que causó el bloqueo
            classification_confidence: Confianza de la clasificación
            
        Returns:
            Dict con el resultado de la notificación
        """
        if not self.java_service_url:
            logger.error("URL del servicio Java no configurada")
            return {
                "success": False,
                "error": "URL del servicio Java no configurada"
            }
        
        try:
            url = f"{self.java_service_url}/api/v1/block-user"
            
            payload = {
                "tenantId": tenant_id,
                "userId": user_id,
                "phoneNumber": phone_number,
                "maliciousMessage": malicious_message,
                "classificationConfidence": classification_confidence,
                "blockedAt": datetime.now().isoformat(),
                "reason": "malicious_behavior",
                "blockedBy": "ai_system"
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            logger.info(f"Notificando bloqueo de usuario al servicio Java: {user_id} (tenant: {tenant_id})")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    logger.info(f"Notificación de bloqueo enviada exitosamente para usuario {user_id}")
                    return {
                        "success": True,
                        "message": "Usuario bloqueado exitosamente",
                        "user_id": user_id,
                        "tenant_id": tenant_id
                    }
                else:
                    logger.error(f"Error notificando bloqueo al servicio Java: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Error del servicio Java: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Excepción notificando bloqueo al servicio Java: {str(e)}")
            return {
                "success": False,
                "error": f"Excepción: {str(e)}"
            }
    
    async def log_malicious_incident(self, tenant_id: str, user_id: str, phone_number: str, 
                                   malicious_message: str, classification_confidence: float) -> Dict[str, Any]:
        """
        Registra un incidente malicioso en los logs
        
        Args:
            tenant_id: ID del tenant
            user_id: ID del usuario
            phone_number: Número de teléfono
            malicious_message: Mensaje malicioso
            classification_confidence: Confianza de la clasificación
            
        Returns:
            Dict con el resultado del logging
        """
        try:
            incident_data = {
                "timestamp": datetime.now().isoformat(),
                "tenant_id": tenant_id,
                "user_id": user_id,
                "phone_number": phone_number,
                "malicious_message": malicious_message,
                "classification_confidence": classification_confidence,
                "action_taken": "user_blocked",
                "severity": "high"
            }
            
            # Log estructurado para monitoreo
            logger.warning(f"MALICIOUS_INCIDENT: {json.dumps(incident_data)}")
            
            return {
                "success": True,
                "incident_logged": True,
                "incident_id": f"incident_{tenant_id}_{user_id}_{int(datetime.now().timestamp())}"
            }
            
        except Exception as e:
            logger.error(f"Error registrando incidente malicioso: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

"""
Servicio para manejar el bloqueo de usuarios en la base de datos
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class UserBlockingService:
    """Servicio para manejar el bloqueo de usuarios"""
    
    def __init__(self):
        # En un entorno real, esto se conectaría a la base de datos
        # Por ahora usamos un diccionario en memoria para simular
        self.blocked_users = {}
    
    async def block_user(self, tenant_id: str, user_id: str, phone_number: str, 
                        reason: str, malicious_message: str) -> Dict[str, Any]:
        """
        Bloquea un usuario en la base de datos
        
        Args:
            tenant_id: ID del tenant
            user_id: ID del usuario
            phone_number: Número de teléfono del usuario
            reason: Razón del bloqueo
            malicious_message: Mensaje malicioso que causó el bloqueo
            
        Returns:
            Dict con el resultado de la operación
        """
        try:
            block_record = {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "phone_number": phone_number,
                "blocked_at": datetime.now().isoformat(),
                "reason": reason,
                "malicious_message": malicious_message,
                "status": "blocked",
                "blocked_by": "ai_system"
            }
            
            # En un entorno real, esto se guardaría en la base de datos
            # Por ahora lo guardamos en memoria
            self.blocked_users[f"{tenant_id}_{user_id}"] = block_record
            
            logger.warning(f"Usuario bloqueado en BD: {user_id} (tenant: {tenant_id}) - Razón: {reason}")
            
            return {
                "success": True,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "blocked_at": block_record["blocked_at"],
                "status": "blocked"
            }
            
        except Exception as e:
            logger.error(f"Error bloqueando usuario en BD: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def unblock_user(self, tenant_id: str, user_id: str) -> Dict[str, Any]:
        """
        Desbloquea un usuario en la base de datos
        
        Args:
            tenant_id: ID del tenant
            user_id: ID del usuario
            
        Returns:
            Dict con el resultado de la operación
        """
        try:
            key = f"{tenant_id}_{user_id}"
            
            if key in self.blocked_users:
                self.blocked_users[key]["status"] = "unblocked"
                self.blocked_users[key]["unblocked_at"] = datetime.now().isoformat()
                
                logger.info(f"Usuario desbloqueado en BD: {user_id} (tenant: {tenant_id})")
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "unblocked_at": self.blocked_users[key]["unblocked_at"],
                    "status": "unblocked"
                }
            else:
                return {
                    "success": False,
                    "error": "Usuario no encontrado en la lista de bloqueados"
                }
                
        except Exception as e:
            logger.error(f"Error desbloqueando usuario en BD: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def is_user_blocked(self, tenant_id: str, user_id: str) -> bool:
        """
        Verifica si un usuario está bloqueado
        
        Args:
            tenant_id: ID del tenant
            user_id: ID del usuario
            
        Returns:
            True si el usuario está bloqueado, False en caso contrario
        """
        try:
            key = f"{tenant_id}_{user_id}"
            user_record = self.blocked_users.get(key)
            
            if user_record and user_record.get("status") == "blocked":
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando estado de bloqueo: {str(e)}")
            return False
    
    async def get_blocked_user_info(self, tenant_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un usuario bloqueado
        
        Args:
            tenant_id: ID del tenant
            user_id: ID del usuario
            
        Returns:
            Dict con la información del usuario bloqueado o None si no está bloqueado
        """
        try:
            key = f"{tenant_id}_{user_id}"
            return self.blocked_users.get(key)
            
        except Exception as e:
            logger.error(f"Error obteniendo información de usuario bloqueado: {str(e)}")
            return None
    
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

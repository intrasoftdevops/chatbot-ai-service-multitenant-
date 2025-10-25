"""
Servicio para obtener configuraciones de tenants directamente desde Firestore
Evita dependencias circulares con el servicio Java
"""

import logging
from typing import Dict, Any, Optional, List
import asyncio
from google.cloud import firestore
import os

logger = logging.getLogger(__name__)

class FirestoreTenantService:
    """Servicio para obtener configuraciones de tenants desde Firestore"""
    
    def __init__(self):
        self.db = None
        self._initialized = False
        
    def _ensure_initialized(self):
        """Asegurar que Firestore esté inicializado"""
        if not self._initialized:
            try:
                # Inicializar cliente de Firestore
                project_id = os.getenv("FIRESTORE_PROJECT_ID", "political-referrals")
                database_id = os.getenv("FIRESTORE_DATABASE_ID", "(default)")
                
                self.db = firestore.Client(project=project_id, database=database_id)
                self._initialized = True
                logger.info(f"✅ Firestore inicializado: project={project_id}, database={database_id}")
                
            except Exception as e:
                logger.error(f"❌ Error inicializando Firestore: {e}")
                raise
    
    async def get_all_tenant_configs(self) -> Dict[str, Any]:
        """Obtener todas las configuraciones de tenants desde Firestore"""
        try:
            self._ensure_initialized()
            
            logger.info("🔍 Obteniendo configuraciones de tenants desde Firestore...")
            
            # Obtener todas las configuraciones de tenants
            tenants_ref = self.db.collection('TenantConfigs')
            docs = tenants_ref.stream()
            
            tenant_configs = {}
            count = 0
            
            for doc in docs:
                try:
                    data = doc.to_dict()
                    tenant_id = data.get('tenantId')
                    
                    if tenant_id:
                        # Convertir a formato esperado por el servicio de IA
                        optimized_config = self._convert_to_optimized_config(data)
                        tenant_configs[tenant_id] = optimized_config
                        count += 1
                        logger.debug(f"✅ Configuración cargada para tenant: {tenant_id}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error procesando documento {doc.id}: {e}")
                    continue
            
            logger.info(f"🎉 Configuraciones obtenidas desde Firestore: {count} tenants")
            return tenant_configs
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo configuraciones desde Firestore: {e}")
            return {}
    
    def _convert_to_optimized_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convertir configuración de Firestore al formato optimizado"""
        try:
            # Extraer campos principales
            optimized_config = {
                "tenant_id": data.get("tenantId"),
                "contact_name": data.get("contactName"),
                "tenant_type": data.get("tenantType", "dev"),
                "status": data.get("status", "active"),
                "wati_tenant_id": data.get("watiTenantId"),
                "client_project_id": data.get("clientProjectId"),
                "client_database_id": data.get("clientDatabaseId"),
                "link_calendly": data.get("linkCalendly"),
                "link_forms": data.get("linkForms"),
                "welcome_message": data.get("welcomeMessage"),
                "wati_api_token": data.get("watiApiToken"),
            }
            
            # Extraer aiConfig si existe
            ai_config = data.get("aiConfig", {})
            if ai_config:
                optimized_config["aiConfig"] = {
                    "documentation_bucket_url": ai_config.get("documentationBucketUrl")
                }
            
            # Extraer branding si existe
            branding = data.get("branding", {})
            if branding:
                optimized_config["branding"] = {
                    "candidate_name": branding.get("candidateName"),
                    "campaign_name": branding.get("campaignName"),
                    "contact_name": branding.get("contactName")
                }
            
            return optimized_config
            
        except Exception as e:
            logger.error(f"❌ Error convirtiendo configuración: {e}")
            return {"tenant_id": data.get("tenantId", "unknown")}
    
    async def get_tenant_config(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Obtener configuración de un tenant específico"""
        try:
            self._ensure_initialized()
            
            logger.info(f"🔍 Obteniendo configuración para tenant: {tenant_id}")
            
            # Buscar configuración específica
            doc_ref = self.db.collection('TenantConfigs').where('tenantId', '==', tenant_id).limit(1)
            docs = list(doc_ref.stream())
            
            if docs:
                data = docs[0].to_dict()
                optimized_config = self._convert_to_optimized_config(data)
                logger.info(f"✅ Configuración encontrada para tenant: {tenant_id}")
                return optimized_config
            else:
                logger.warning(f"⚠️ No se encontró configuración para tenant: {tenant_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo configuración para tenant {tenant_id}: {e}")
            return None

# Instancia global del servicio
firestore_tenant_service = FirestoreTenantService()

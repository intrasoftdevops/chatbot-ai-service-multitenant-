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
                # Configurar credenciales de Firebase
                project_id = os.getenv("FIRESTORE_PROJECT_ID", "political-referrals")
                database_id = os.getenv("FIRESTORE_DATABASE_ID", "(default)")

                logger.info(f"🔧 Inicializando Firestore con project={project_id}, database={database_id}")

                # Verificar si estamos en Cloud Run
                if os.getenv("K_SERVICE"):
                    logger.info("🌩️ Detectado Cloud Run - usando credenciales automáticas")
                    self.db = firestore.Client(project=project_id, database=database_id)
                else:
                    logger.info("💻 Modo desarrollo local - configurando credenciales...")
                    logger.info(f"🔍 GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
                    
                    try:
                        # Usar Application Default Credentials directamente
                        logger.info("🔄 Creando cliente de Firestore...")
                        
                        # Para desarrollo local, usar Application Default Credentials directamente
                        logger.info("🔄 Usando Application Default Credentials...")
                        self.db = firestore.Client(project=project_id, database=database_id)
                            
                        logger.info("✅ Cliente de Firestore creado exitosamente")
                    except Exception as firestore_error:
                        logger.error(f"❌ Error específico creando cliente Firestore: {firestore_error}")
                        logger.error(f"❌ Tipo de error: {type(firestore_error)}")
                        raise

                self._initialized = True
                logger.info(f"✅ Firestore inicializado correctamente")

            except Exception as e:
                logger.error(f"❌ Error inicializando Firestore: {e}")
                logger.error(f"💡 Para desarrollo local, ejecuta: gcloud auth application-default login")
                logger.error(f"💡 O configura GOOGLE_APPLICATION_CREDENTIALS con la ruta al archivo JSON")
                raise
    
    async def get_all_tenant_configs(self) -> Dict[str, Any]:
        """Obtener todas las configuraciones de tenants desde Firestore"""
        try:
            self._ensure_initialized()
            
            logger.info("🔍 Obteniendo configuraciones de tenants desde Firestore...")
            
            # Obtener todas las configuraciones de tenants
            tenants_ref = self.db.collection('clientes')
            docs = tenants_ref.stream()
            
            tenant_configs = {}
            count = 0
            
            for doc in docs:
                try:
                    data = doc.to_dict()
                    tenant_id = data.get('tenant_id')
                    
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
            logger.error("💡 Asegúrate de haber ejecutado: gcloud auth application-default login")
            return {}
    
    def _convert_to_optimized_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convertir configuración de Firestore al formato optimizado"""
        try:
            # Extraer campos principales
            optimized_config = {
                "tenant_id": data.get("tenant_id"),
                "contact_name": data.get("branding", {}).get("contact_name"),
                "tenant_type": data.get("tenant_type", "dev"),
                "status": data.get("status", "active"),
                "wati_tenant_id": data.get("wati_tenant_id"),
                "client_project_id": data.get("client_project_id"),
                "client_database_id": data.get("client_database_id"),
                "link_calendly": data.get("link_calendly"),
                "link_forms": data.get("link_forms"),
                "welcome_message": data.get("branding", {}).get("welcome_message"),
                "wati_api_token": data.get("wati_api_token"),
            }
            
            # Extraer aiConfig si existe
            ai_config = data.get("ai_config", {})
            if ai_config:
                optimized_config["aiConfig"] = {
                    "documentation_bucket_url": ai_config.get("documentation_bucket_url")
                }
            
            # Extraer branding si existe
            branding = data.get("branding", {})
            if branding:
                optimized_config["branding"] = {
                    "candidate_name": branding.get("contact_name"),
                    "campaign_name": branding.get("contact_name"),
                    "contact_name": branding.get("contact_name")
                }
            
            return optimized_config
            
        except Exception as e:
            logger.error(f"❌ Error convirtiendo configuración: {e}")
            return {"tenant_id": data.get("tenant_id", "unknown")}
    
    async def get_tenant_config(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Obtener configuración de un tenant específico"""
        try:
            self._ensure_initialized()
            
            logger.info(f"🔍 Obteniendo configuración para tenant: {tenant_id}")
            
            # Buscar configuración específica
            doc_ref = self.db.collection('clientes').where('tenant_id', '==', tenant_id).limit(1)
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

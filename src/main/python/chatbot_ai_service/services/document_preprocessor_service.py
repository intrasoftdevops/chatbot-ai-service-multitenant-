"""
Servicio de preprocesamiento de documentos por tenant
Optimiza la carga inicial de documentos para mejorar tiempos de respuesta
"""
import logging
import time
from typing import Dict, Any, Optional, List
import asyncio
from chatbot_ai_service.services.document_context_service import document_context_service
from chatbot_ai_service.services.configuration_service import configuration_service

logger = logging.getLogger(__name__)

class DocumentPreprocessorService:
    """Servicio para preprocesar documentos por tenant"""
    
    def __init__(self):
        self._preprocessed_cache = {}  # Cache de documentos preprocesados
        self._processing_status = {}   # Estado de procesamiento por tenant
        self._initialized_tenants = set()  # Tenants ya inicializados
        
    async def preprocess_tenant_documents(self, tenant_id: str) -> bool:
        """
        Preprocesa documentos de un tenant específico
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            True si se preprocesaron exitosamente
        """
        try:
            if tenant_id in self._initialized_tenants:
                logger.info(f"✅ Tenant {tenant_id} ya preprocesado")
                return True
                
            logger.info(f"🚀 Iniciando preprocesamiento para tenant {tenant_id}")
            print(f"📚 [BACKGROUND] Procesando tenant {tenant_id}...")
            start_time = time.time()
            
            # Obtener configuración del tenant desde Firestore
            from chatbot_ai_service.services.firestore_tenant_service import firestore_tenant_service
            config = await firestore_tenant_service.get_tenant_config(tenant_id)
            if not config:
                logger.error(f"❌ No se pudo obtener configuración para tenant {tenant_id}")
                return False
                
            # Obtener URL del bucket de documentos
            ai_config = config.get("aiConfig", {})
            if ai_config is None:
                ai_config = {}
            documentation_bucket_url = ai_config.get("documentation_bucket_url")
            if not documentation_bucket_url or documentation_bucket_url.strip() == "":
                logger.warning(f"⚠️ Tenant {tenant_id} no tiene documentation_bucket_url válido en aiConfig")
                return False
                
            # Marcar como procesando
            self._processing_status[tenant_id] = "processing"
            
            # Cargar documentos usando el servicio existente con timeout
            logger.info(f"⏱️ Iniciando carga de documentos con timeout de 8 minutos...")
            success = await asyncio.wait_for(
                document_context_service.load_tenant_documents(
                    tenant_id, documentation_bucket_url
                ),
                timeout=480  # 8 minutos timeout
            )
            
            if success:
                # Obtener información de documentos cargados
                doc_info = document_context_service.get_tenant_document_info(tenant_id)
                
                # Crear cache optimizado
                self._preprocessed_cache[tenant_id] = {
                    "tenant_id": tenant_id,
                    "bucket_url": documentation_bucket_url,
                    "document_count": doc_info.get("document_count", 0),
                    "total_chars": doc_info.get("total_chars", 0),
                    "preprocessed_at": time.time(),
                    "status": "ready"
                }
                
                self._initialized_tenants.add(tenant_id)
                self._processing_status[tenant_id] = "completed"
                
                duration = time.time() - start_time
                logger.info(f"✅ Tenant {tenant_id} preprocesado en {duration:.2f}s")
                print(f"✅ [BACKGROUND] Tenant {tenant_id} preprocesado en {duration:.2f}s")
                return True
            else:
                self._processing_status[tenant_id] = "failed"
                logger.error(f"❌ Falló preprocesamiento para tenant {tenant_id}")
                return False
                
        except asyncio.TimeoutError:
            logger.error(f"⏰ Timeout preprocesando tenant {tenant_id} - documentos muy grandes o lentos")
            self._processing_status[tenant_id] = "timeout"
            return False
        except Exception as e:
            logger.error(f"❌ Error preprocesando tenant {tenant_id}: {str(e)}")
            self._processing_status[tenant_id] = "failed"
            return False
    
    async def preprocess_all_tenants(self) -> Dict[str, bool]:
        """
        Preprocesa documentos para todos los tenants disponibles
        
        Returns:
            Dict con resultados por tenant
        """
        logger.info("🚀 Iniciando preprocesamiento masivo de documentos")
        results = {}
        
        # Obtener lista de tenants desde Firestore
        try:
            from chatbot_ai_service.services.firestore_tenant_service import firestore_tenant_service
            # Obtener todos los tenants desde Firestore
            all_configs = await firestore_tenant_service.get_all_tenant_configs()
            known_tenants = list(all_configs.keys())
            
            tasks = []
            for tenant_id in known_tenants:
                task = asyncio.create_task(self.preprocess_tenant_documents(tenant_id))
                tasks.append((tenant_id, task))
            
            # Esperar a que terminen todos
            for tenant_id, task in tasks:
                try:
                    result = await task
                    results[tenant_id] = result
                except Exception as e:
                    logger.error(f"❌ Error procesando tenant {tenant_id}: {str(e)}")
                    results[tenant_id] = False
            
            successful = sum(1 for success in results.values() if success)
            logger.info(f"✅ Preprocesamiento completado: {successful}/{len(results)} tenants exitosos")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error en preprocesamiento masivo: {str(e)}")
            return {}
    
    def get_preprocessed_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de documentos preprocesados"""
        return self._preprocessed_cache.get(tenant_id)
    
    def is_tenant_preprocessed(self, tenant_id: str) -> bool:
        """Verifica si un tenant está preprocesado"""
        return tenant_id in self._initialized_tenants
    
    def get_processing_status(self, tenant_id: str) -> str:
        """Obtiene el estado de procesamiento de un tenant"""
        return self._processing_status.get(tenant_id, "not_started")
    
    def clear_tenant_cache(self, tenant_id: str):
        """Limpia el cache de un tenant específico"""
        self._preprocessed_cache.pop(tenant_id, None)
        self._processing_status.pop(tenant_id, None)
        self._initialized_tenants.discard(tenant_id)
        logger.info(f"🗑️ Cache limpiado para tenant {tenant_id}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache"""
        return {
            "total_tenants": len(self._initialized_tenants),
            "preprocessed_tenants": list(self._initialized_tenants),
            "processing_status": dict(self._processing_status),
            "cache_size": len(self._preprocessed_cache)
        }

# Instancia global
document_preprocessor_service = DocumentPreprocessorService()

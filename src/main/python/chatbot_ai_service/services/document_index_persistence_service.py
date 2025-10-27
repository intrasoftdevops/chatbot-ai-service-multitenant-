"""
Servicio de persistencia para índices de documentos

Este servicio guarda y carga los índices de documentos procesados
desde Firestore para evitar reprocesar en cada reinicio del servicio.
"""
import logging
import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
from google.cloud import firestore
from chatbot_ai_service.config.firebase_config import get_firebase_config

logger = logging.getLogger(__name__)

class DocumentIndexPersistenceService:
    """Servicio para persistir índices de documentos en Firestore"""
    
    def __init__(self):
        self._firebase_config = get_firebase_config()
        self.collection_name = "document_indexes"
    
    @property
    def db(self):
        """Obtiene el cliente de Firestore"""
        return self._firebase_config.get_firestore()
    
    def _get_index_hash(self, tenant_id: str, documentation_bucket_url: str) -> str:
        """Genera un hash único para el índice basado en tenant y bucket"""
        content = f"{tenant_id}:{documentation_bucket_url}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def save_index_metadata(self, tenant_id: str, bucket_url: str, 
                                   documents_count: int, file_types: Dict[str, int],
                                   total_chars: int, processing_time: float = None) -> bool:
        """
        Guarda los metadatos del índice de documentos
        
        Args:
            tenant_id: ID del tenant
            bucket_url: URL del bucket
            documents_count: Número de documentos procesados
            file_types: Diccionario con tipos de archivo y cantidad
            total_chars: Total de caracteres procesados
            processing_time: Tiempo de procesamiento en segundos
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            index_hash = self._get_index_hash(tenant_id, bucket_url)
            
            # Guardar metadatos del índice
            metadata = {
                "tenant_id": tenant_id,
                "bucket_url": bucket_url,
                "index_hash": index_hash,
                "documents_count": documents_count,
                "file_types": file_types,
                "total_chars": total_chars,
                "processing_time": processing_time,
                "last_updated": firestore.SERVER_TIMESTAMP,
                "created_at": firestore.SERVER_TIMESTAMP
            }
            
            doc_ref = self.db.collection(self.collection_name).document(index_hash)
            doc_ref.set(metadata)
            
            logger.info(f"✅ Metadatos de índice guardados para tenant {tenant_id}: {documents_count} documentos")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando metadatos de índice: {str(e)}")
            return False
    
    def get_index_metadata(self, tenant_id: str, bucket_url: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los metadatos del índice de documentos
        
        Args:
            tenant_id: ID del tenant
            bucket_url: URL del bucket
            
        Returns:
            Diccionario con metadatos o None si no existe
        """
        try:
            index_hash = self._get_index_hash(tenant_id, bucket_url)
            doc_ref = self.db.collection(self.collection_name).document(index_hash)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo metadatos de índice: {str(e)}")
            return None
    
    def index_exists(self, tenant_id: str, bucket_url: str) -> bool:
        """
        Verifica si ya existe un índice para este tenant y bucket
        
        Args:
            tenant_id: ID del tenant
            bucket_url: URL del bucket
            
        Returns:
            True si el índice existe
        """
        metadata = self.get_index_metadata(tenant_id, bucket_url)
        return metadata is not None
    
    def save_document_summary(self, tenant_id: str, summary: str, vector_summary: str = None) -> bool:
        """
        Guarda el resumen de documentos procesados para un tenant
        
        Args:
            tenant_id: ID del tenant
            summary: Resumen en texto del contenido
            vector_summary: Resumen vectorizado (opcional)
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            summary_data = {
                "tenant_id": tenant_id,
                "summary": summary,
                "vector_summary": vector_summary,
                "last_updated": firestore.SERVER_TIMESTAMP
            }
            
            doc_ref = self.db.collection("document_summaries").document(tenant_id)
            doc_ref.set(summary_data)
            
            logger.info(f"✅ Resumen de documentos guardado para tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando resumen de documentos: {str(e)}")
            return False
    
    def get_document_summary(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el resumen de documentos para un tenant
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            Diccionario con el resumen o None si no existe
        """
        try:
            doc_ref = self.db.collection("document_summaries").document(tenant_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo resumen de documentos: {str(e)}")
            return None
    
    async def save_prompts_cache(self, tenant_id: str, prompts: Dict[str, Any]) -> bool:
        """
        Guarda los prompts pre-procesados para un tenant
        
        Args:
            tenant_id: ID del tenant
            prompts: Diccionario con los prompts procesados
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            prompts_data = {
                "tenant_id": tenant_id,
                "prompts": prompts,
                "last_updated": firestore.SERVER_TIMESTAMP
            }
            
            doc_ref = self.db.collection("tenant_prompts_cache").document(tenant_id)
            doc_ref.set(prompts_data)
            
            logger.info(f"✅ Prompts guardados para tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando prompts: {str(e)}")
            return False
    
    def get_prompts_cache(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los prompts pre-procesados para un tenant
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            Diccionario con los prompts o None si no existe
        """
        try:
            doc_ref = self.db.collection("tenant_prompts_cache").document(tenant_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return data.get("prompts") if data else None
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo prompts: {str(e)}")
            return None
    
    def mark_index_as_stale(self, tenant_id: str, bucket_url: str) -> bool:
        """
        Marca un índice como "obsoleto" para forzar re-procesamiento
        
        Args:
            tenant_id: ID del tenant
            bucket_url: URL del bucket
            
        Returns:
            True si se marcó exitosamente
        """
        try:
            index_hash = self._get_index_hash(tenant_id, bucket_url)
            doc_ref = self.db.collection(self.collection_name).document(index_hash)
            doc_ref.update({"is_stale": True, "last_updated": firestore.SERVER_TIMESTAMP})
            
            logger.info(f"✅ Índice marcado como obsoleto para tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error marcando índice como obsoleto: {str(e)}")
            return False
    
    async def save_tenant_prompts(self, tenant_id: str, prompts: Dict[str, str]) -> bool:
        """
        Guarda los prompts personalizados de un tenant en DB
        
        Args:
            tenant_id: ID del tenant
            prompts: Diccionario con prompts (welcome, contact, name, etc.)
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            prompts_data = {
                "tenant_id": tenant_id,
                "prompts": prompts,
                "last_updated": firestore.SERVER_TIMESTAMP,
                "version": "2.0"
            }
            
            doc_ref = self.db.collection('tenant_prompts').document(tenant_id)
            doc_ref.set(prompts_data)
            
            logger.info(f"✅ Prompts guardados en DB para tenant {tenant_id}: {len(prompts)} prompts")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando prompts para tenant {tenant_id}: {str(e)}")
            return False
    
    def get_tenant_prompts(self, tenant_id: str) -> Optional[Dict[str, str]]:
        """
        Obtiene los prompts personalizados de un tenant desde DB
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            Diccionario con prompts o None si no existe
        """
        try:
            doc_ref = self.db.collection('tenant_prompts').document(tenant_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                prompts = data.get('prompts', {})
                logger.info(f"✅ Prompts cargados desde DB para tenant {tenant_id}: {len(prompts)} prompts")
                return prompts
            
            logger.warning(f"⚠️ No hay prompts guardados para tenant {tenant_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo prompts para tenant {tenant_id}: {str(e)}")
            return None

# Instancia global del servicio
document_index_persistence_service = DocumentIndexPersistenceService()


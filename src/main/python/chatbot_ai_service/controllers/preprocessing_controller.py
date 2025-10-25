"""
Controlador para preprocesamiento de documentos
Proporciona endpoints para inicializar y gestionar el preprocesamiento
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from chatbot_ai_service.services.document_preprocessor_service import document_preprocessor_service
from chatbot_ai_service.services.intelligent_cache_service import intelligent_cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/preprocessing", tags=["Document Preprocessing"])

@router.post("/tenant/{tenant_id}/init")
async def initialize_tenant_preprocessing(tenant_id: str, background_tasks: BackgroundTasks):
    """
    Inicializa preprocesamiento de documentos para un tenant específico
    
    Args:
        tenant_id: ID del tenant
        background_tasks: Tareas en background de FastAPI
        
    Returns:
        Estado de inicialización
    """
    try:
        logger.info(f"🚀 Inicializando preprocesamiento para tenant {tenant_id}")
        
        # Verificar si ya está preprocesado
        if document_preprocessor_service.is_tenant_preprocessed(tenant_id):
            return {
                "status": "already_preprocessed",
                "tenant_id": tenant_id,
                "message": "Tenant ya está preprocesado"
            }
        
        # Iniciar preprocesamiento en background
        background_tasks.add_task(
            document_preprocessor_service.preprocess_tenant_documents,
            tenant_id
        )
        
        return {
            "status": "initialized",
            "tenant_id": tenant_id,
            "message": "Preprocesamiento iniciado en background"
        }
        
    except Exception as e:
        logger.error(f"Error inicializando preprocesamiento para tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/all/init")
async def initialize_all_preprocessing(background_tasks: BackgroundTasks):
    """
    Inicializa preprocesamiento para todos los tenants
    
    Args:
        background_tasks: Tareas en background de FastAPI
        
    Returns:
        Estado de inicialización masiva
    """
    try:
        logger.info("🚀 Iniciando preprocesamiento masivo")
        
        # Iniciar preprocesamiento masivo en background
        background_tasks.add_task(
            document_preprocessor_service.preprocess_all_tenants
        )
        
        return {
            "status": "initialized",
            "message": "Preprocesamiento masivo iniciado en background"
        }
        
    except Exception as e:
        logger.error(f"Error inicializando preprocesamiento masivo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tenant/{tenant_id}/status")
async def get_tenant_preprocessing_status(tenant_id: str):
    """
    Obtiene el estado del preprocesamiento para un tenant
    
    Args:
        tenant_id: ID del tenant
        
    Returns:
        Estado del preprocesamiento
    """
    try:
        status = document_preprocessor_service.get_processing_status(tenant_id)
        is_preprocessed = document_preprocessor_service.is_tenant_preprocessed(tenant_id)
        info = document_preprocessor_service.get_preprocessed_info(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "status": status,
            "is_preprocessed": is_preprocessed,
            "info": info
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estado para tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_preprocessing_stats():
    """
    Obtiene estadísticas del preprocesamiento
    
    Returns:
        Estadísticas del sistema
    """
    try:
        preprocessor_stats = document_preprocessor_service.get_cache_stats()
        cache_stats = intelligent_cache_service.get_cache_stats()
        
        return {
            "preprocessor": preprocessor_stats,
            "intelligent_cache": cache_stats,
            "timestamp": "2025-01-24T16:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tenant/{tenant_id}/cache")
async def clear_tenant_cache(tenant_id: str):
    """
    Limpia el cache de preprocesamiento para un tenant
    
    Args:
        tenant_id: ID del tenant
        
    Returns:
        Estado de limpieza
    """
    try:
        document_preprocessor_service.clear_tenant_cache(tenant_id)
        intelligent_cache_service.clear_tenant_cache(tenant_id)
        
        return {
            "status": "cleared",
            "tenant_id": tenant_id,
            "message": "Cache limpiado exitosamente"
        }
        
    except Exception as e:
        logger.error(f"Error limpiando cache para tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_preprocessing_status():
    """
    Obtiene el estado general del preprocesamiento de documentos
    
    Returns:
        Estado del preprocesamiento con información detallada
    """
    try:
        # Obtener estadísticas del cache
        cache_stats = document_preprocessor_service.get_cache_stats()
        
        # Determinar si el preprocesamiento está completo
        processing_statuses = cache_stats.get("processing_status", {})
        
        # Verificar si hay tenants en procesamiento
        processing_tenants = [tenant for tenant, status in processing_statuses.items() 
                            if status in ["processing"]]
        
        # Verificar si hay tenants fallidos
        failed_tenants = [tenant for tenant, status in processing_statuses.items() 
                        if status in ["failed", "timeout"]]
        
        # Verificar si hay tenants completados
        completed_tenants = [tenant for tenant, status in processing_statuses.items() 
                            if status == "completed"]
        
        # Determinar estado general
        if processing_tenants:
            overall_status = "processing"
            completed = False
        elif failed_tenants:
            overall_status = "failed"
            completed = False
        elif completed_tenants:
            overall_status = "completed"
            completed = True
        else:
            overall_status = "not_started"
            completed = False
        
        return {
            "status": overall_status,
            "completed": completed,
            "failed": len(failed_tenants) > 0,
            "processing": len(processing_tenants) > 0,
            "total_tenants": cache_stats.get("total_tenants", 0),
            "completed_tenants": len(completed_tenants),
            "failed_tenants": len(failed_tenants),
            "processing_tenants": len(processing_tenants),
            "tenant_details": {
                "completed": completed_tenants,
                "failed": failed_tenants,
                "processing": processing_tenants
            },
            "cache_stats": cache_stats
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del preprocesamiento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

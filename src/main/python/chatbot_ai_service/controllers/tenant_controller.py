"""
Controlador para gestión de tenants en el servicio de IA multi-tenant
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends

from chatbot_ai_service.models.tenant_models import TenantConfig, TenantHealth, TenantStats
from chatbot_ai_service.services.tenant_service import TenantService

logger = logging.getLogger(__name__)

class TenantController:
    """Controlador para gestión de tenants"""
    
    def __init__(self, tenant_service: TenantService):
        self.tenant_service = tenant_service
        self.router = APIRouter()
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas del controlador"""
        
        @self.router.get("/tenants/{tenant_id}")
        async def get_tenant_config(tenant_id: str):
            """Obtiene la configuración de un tenant"""
            try:
                config = await self.tenant_service.get_tenant_config(tenant_id)
                if not config:
                    raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} no encontrado o inactivo")
                
                return config.dict()
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error al obtener configuración de tenant {tenant_id}: {e}")
                raise HTTPException(status_code=500, detail="Error interno del servidor")
        
        @self.router.get("/tenants/{tenant_id}/status")
        async def get_tenant_status(tenant_id: str):
            """Verifica el estado de un tenant"""
            try:
                is_active = await self.tenant_service.is_tenant_active(tenant_id)
                
                if is_active:
                    return {
                        "tenant_id": tenant_id,
                        "status": "active",
                        "message": f"Tenant {tenant_id} está activo"
                    }
                else:
                    return {
                        "tenant_id": tenant_id,
                        "status": "inactive",
                        "message": f"Tenant {tenant_id} no encontrado o inactivo"
                    }
                
            except Exception as e:
                logger.error(f"Error al verificar estado de tenant {tenant_id}: {e}")
                raise HTTPException(status_code=500, detail="Error interno del servidor")
        
        @self.router.get("/tenants/{tenant_id}/health")
        async def get_tenant_health(tenant_id: str):
            """Obtiene el estado de salud de un tenant"""
            try:
                health = await self.tenant_service.get_tenant_health(tenant_id)
                if not health:
                    raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} no encontrado")
                
                return health.dict()
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error al obtener health de tenant {tenant_id}: {e}")
                raise HTTPException(status_code=500, detail="Error interno del servidor")
        
        @self.router.get("/tenants/{tenant_id}/stats")
        async def get_tenant_stats(tenant_id: str):
            """Obtiene estadísticas de un tenant"""
            try:
                stats = await self.tenant_service.get_tenant_stats(tenant_id)
                if not stats:
                    raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} no encontrado")
                
                return stats.dict()
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error al obtener estadísticas de tenant {tenant_id}: {e}")
                raise HTTPException(status_code=500, detail="Error interno del servidor")
        
        @self.router.get("/tenants/{tenant_id}/ai-config")
        async def get_tenant_ai_config(tenant_id: str):
            """Obtiene la configuración de IA de un tenant"""
            try:
                ai_config = await self.tenant_service.get_ai_config(tenant_id)
                if not ai_config:
                    raise HTTPException(status_code=404, detail=f"Configuración de IA no encontrada para tenant {tenant_id}")
                
                return ai_config
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error al obtener configuración de IA de tenant {tenant_id}: {e}")
                raise HTTPException(status_code=500, detail="Error interno del servidor")
        
        @self.router.get("/tenants/{tenant_id}/branding-config")
        async def get_tenant_branding_config(tenant_id: str):
            """Obtiene la configuración de marca de un tenant"""
            try:
                branding_config = await self.tenant_service.get_branding_config(tenant_id)
                if not branding_config:
                    raise HTTPException(status_code=404, detail=f"Configuración de marca no encontrada para tenant {tenant_id}")
                
                return branding_config
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error al obtener configuración de marca de tenant {tenant_id}: {e}")
                raise HTTPException(status_code=500, detail="Error interno del servidor")


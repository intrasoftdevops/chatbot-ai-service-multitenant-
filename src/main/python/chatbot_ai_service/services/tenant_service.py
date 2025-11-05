"""
Servicio de gestión de tenants

Replica la funcionalidad de TenantService.java del servicio Spring Boot
Obtiene la configuración de tenants desde Firestore
"""
import logging
from typing import Optional, Dict, Any
from google.cloud import firestore

from chatbot_ai_service.config.firebase_config import get_firebase_config
from chatbot_ai_service.models.tenant_models import TenantConfig, BrandingConfig, AIConfig, ReferralConfig, FeatureConfig

logger = logging.getLogger(__name__)


class TenantService:
    """Servicio para gestionar configuraciones de tenants"""
    
    # Colección de Firestore donde se almacenan los tenants
    TENANTS_COLLECTION = "tenants"
    
    def __init__(self):
        """Inicializa el servicio de tenants"""
        self.firebase_config = get_firebase_config()
        self._cache = {}  # Cache simple de configuraciones
    
    def get_tenant_config(self, tenant_id: str) -> Optional[TenantConfig]:
        """
        Obtiene la configuración de un tenant desde Firestore
        
        Args:
            tenant_id: ID del tenant
            
        Returns:
            Configuración del tenant o None si no existe
        """
        try:
            # Verificar cache
            if tenant_id in self._cache:
                logger.debug(f"Retornando configuración de tenant {tenant_id} desde cache")
                return self._cache[tenant_id]
            
            logger.info(f"Obteniendo configuración desde Firestore para tenant: {tenant_id}")
            
            # Obtener cliente de Firestore
            db = self.firebase_config.get_firestore()
            
            # Obtener documento del tenant
            doc_ref = db.collection(self.TENANTS_COLLECTION).document(tenant_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.warning(f"Tenant {tenant_id} no encontrado en Firestore")
                return None
            
            # Convertir documento a dict
            tenant_data = doc.to_dict()
            logger.info(f"Configuración encontrada desde Firestore para tenant: {tenant_id}")
            logger.debug(f"Datos del tenant: {tenant_data}")
            
            # Mapear a modelo TenantConfig
            tenant_config = self._map_firestore_to_tenant_config(tenant_id, tenant_data)
            
            # Guardar en cache
            self._cache[tenant_id] = tenant_config
            
            logger.info(f"Tenant {tenant_id} configurado exitosamente")
            return tenant_config
            
        except Exception as e:
            logger.error(f"Error obteniendo configuración del tenant {tenant_id}: {str(e)}")
            return None
    
    def _map_firestore_to_tenant_config(self, tenant_id: str, data: Dict[str, Any]) -> TenantConfig:
        """
        Mapea datos de Firestore a TenantConfig
        
        Args:
            tenant_id: ID del tenant
            data: Datos del documento de Firestore
            
        Returns:
            Configuración del tenant mapeada
        """
        try:
            # Mapear branding
            branding_data = data.get("branding", {})
            branding = BrandingConfig(
                primary_color=branding_data.get("primary_color"),
                secondary_color=branding_data.get("secondary_color"),
                accent_color=branding_data.get("accent_color"),
                logo_url=branding_data.get("logo_url"),
                welcome_message=branding_data.get("welcome_message"),
                privacy_message=branding_data.get("privacy_message"),
                privacy_url=branding_data.get("privacy_url"),
                contact_name=branding_data.get("contact_name"),
                privacy_video_url=branding_data.get("privacy_video_url"),
                greeting_message=branding_data.get("greeting_message")
            ) if branding_data else None
            
            # Mapear AI config
            ai_config_data = data.get("ai_config", {})
            ai_config = AIConfig(
                model=ai_config_data.get("model", "gemini-1.5-flash"),
                temperature=ai_config_data.get("temperature", 0.7),
                max_tokens=ai_config_data.get("max_tokens", 1000),
                documentation_bucket_url=ai_config_data.get("documentation_bucket_url"),
                enable_context=ai_config_data.get("enable_context", True)
            ) if ai_config_data else None
            
            # Mapear referral config
            referral_config_data = data.get("referral_config", {})
            referral_config = ReferralConfig(
                enabled=referral_config_data.get("enabled", True),
                points_per_referral=referral_config_data.get("points_per_referral", 10),
                rewards_enabled=referral_config_data.get("rewards_enabled", True)
            ) if referral_config_data else None
            
            # Mapear features
            features_data = data.get("features", {})
            features = FeatureConfig(
                analytics=features_data.get("analytics", True),
                referrals=features_data.get("referrals", True),
                appointments=features_data.get("appointments", True),
                surveys=features_data.get("surveys", True)
            ) if features_data else None
            
            # Crear configuración completa
            tenant_config = TenantConfig(
                tenant_id=tenant_id,
                tenant_type=data.get("tenant_type"),
                client_project_id=data.get("client_project_id", tenant_id),
                client_database_id=data.get("client_database_id", "(default)"),
                numero_whatsapp=data.get("numero_whatsapp"),
                link_calendly=data.get("link_calendly"),
                link_forms=data.get("link_forms"),
                status=data.get("status", "active"),
                use_adc=data.get("use_adc", True),
                client_credentials_secret=data.get("client_credentials_secret"),
                wati_tenant_id=data.get("wati_tenant_id"),
                wati_api_token=data.get("wati_api_token"),
                wati_api_endpoint=data.get("wati_api_endpoint"),
                branding=branding,
                ai_config=ai_config,
                referral_config=referral_config,
                features=features,
                integrations=data.get("integrations")
            )
            
            logger.info(f"Configuración mapeada exitosamente para tenant: {tenant_id}")
            logger.debug(f"Branding config - contact_name: {branding.contact_name if branding else 'None'}")
            logger.debug(f"AI config - documentation_url: {ai_config.documentation_bucket_url if ai_config else 'None'}")
            
            return tenant_config
            
        except Exception as e:
            logger.error(f"Error mapeando configuración del tenant {tenant_id}: {str(e)}")
            raise
    
    def clear_cache(self, tenant_id: Optional[str] = None):
        """
        Limpia el cache de configuraciones
        
        Args:
            tenant_id: ID del tenant específico a limpiar, o None para limpiar todo
        """
        if tenant_id:
            self._cache.pop(tenant_id, None)
            logger.info(f"Cache limpiado para tenant: {tenant_id}")
        else:
            self._cache.clear()
            logger.info("Cache completo limpiado")


# Singleton global
_tenant_service_instance = None


def get_tenant_service() -> TenantService:
    """
    Obtiene la instancia singleton de TenantService
    
    Returns:
        Instancia de TenantService
    """
    global _tenant_service_instance
    if _tenant_service_instance is None:
        _tenant_service_instance = TenantService()
    return _tenant_service_instance

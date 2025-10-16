"""
Configuración de Firebase para el servicio de IA

Replica la funcionalidad de FirebaseConfig.java del servicio Spring Boot
"""
import os
import logging
from google.cloud import firestore
from google.auth import default as google_auth_default

logger = logging.getLogger(__name__)


class FirebaseConfig:
    """Configuración de Firebase y Firestore"""
    
    def __init__(self):
        """Inicializa la configuración de Firebase"""
        self.project_id = os.getenv("FIRESTORE_PROJECT_ID", "political-referrals")
        self._firestore_client = None
        
        # Limpiar GOOGLE_APPLICATION_CREDENTIALS si tiene valores de ejemplo
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path and ("example" in credentials_path or "your-" in credentials_path or "/path/to/" in credentials_path):
            logger.warning(f"GOOGLE_APPLICATION_CREDENTIALS tiene un valor de ejemplo, ignorándolo: {credentials_path}")
            os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
        
    def get_firestore(self) -> firestore.Client:
        """
        Obtiene el cliente de Firestore
        
        Returns:
            Cliente de Firestore configurado
        """
        if self._firestore_client is None:
            self._firestore_client = self._initialize_firestore()
        return self._firestore_client
    
    def _initialize_firestore(self) -> firestore.Client:
        """
        Inicializa el cliente de Firestore
        
        Usa Application Default Credentials (ADC) igual que el servicio Java
        """
        try:
            logger.info(f"Configurando Firestore con project-id: {self.project_id}")
            
            # Usar Application Default Credentials (ADC)
            # Esto funciona automáticamente en Google Cloud y localmente con gcloud auth
            credentials, project = google_auth_default()
            logger.info(f"🔐 Credenciales obtenidas - proyecto detectado: {project}")
            
            # Crear cliente de Firestore
            client = firestore.Client(
                project=self.project_id,
                credentials=credentials
            )
            
            logger.info(f"Firestore configurado exitosamente para proyecto: {self.project_id}")
            return client
            
        except Exception as e:
            logger.error(f"Error configurando Firestore: {str(e)}")
            # En caso de error, crear cliente sin credenciales explícitas
            # (funciona en GCP con service account automático)
            return firestore.Client(project=self.project_id)


# Singleton global
_firebase_config_instance = None


def get_firebase_config() -> FirebaseConfig:
    """
    Obtiene la instancia singleton de FirebaseConfig
    
    Returns:
        Instancia de FirebaseConfig
    """
    global _firebase_config_instance
    if _firebase_config_instance is None:
        _firebase_config_instance = FirebaseConfig()
    return _firebase_config_instance

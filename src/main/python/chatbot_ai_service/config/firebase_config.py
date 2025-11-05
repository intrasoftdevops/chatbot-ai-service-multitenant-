"""
Configuración de Firebase para el servicio de IA

Replica la funcionalidad de FirebaseConfig.java del servicio Spring Boot
"""
import os
import logging
from google.cloud import firestore
from google.auth import default as google_auth_default
from google.auth.exceptions import DefaultCredentialsError

logger = logging.getLogger(__name__)


class FirebaseConfig:
    """Configuración de Firebase y Firestore"""
    
    def __init__(self):
        """Inicializa la configuración de Firebase"""
        self.project_id = os.getenv("FIRESTORE_PROJECT_ID", "political-referrals")
        self._firestore_client = None
        
        # Limpiar GOOGLE_APPLICATION_CREDENTIALS si tiene valores de ejemplo
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path:
            if ("example" in credentials_path or "your-" in credentials_path or "/path/to/" in credentials_path):
                logger.warning(f"GOOGLE_APPLICATION_CREDENTIALS tiene un valor de ejemplo, ignorándolo: {credentials_path}")
                os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
            elif not os.path.exists(credentials_path):
                logger.warning(f"GOOGLE_APPLICATION_CREDENTIALS apunta a un archivo que no existe: {credentials_path}")
                logger.info("💡 Usando ADC (Application Default Credentials) en su lugar")
                os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
        
    def get_firestore(self) -> firestore.Client:
        """
        Obtiene el cliente de Firestore
        
        Returns:
            Cliente de Firestore configurado, o None si no está disponible
        """
        if self._firestore_client is None:
            self._firestore_client = self._initialize_firestore()
        return self._firestore_client
    
    def _initialize_firestore(self) -> firestore.Client | None:
        """
        Inicializa el cliente de Firestore
        
        Usa Application Default Credentials (ADC) igual que el servicio Java
        
        Returns:
            Cliente de Firestore o None si no está disponible
        """
        logger.info(f"Configurando Firestore con project-id: {self.project_id}")
        
        # Verificar si hay alguna variable de entorno problemática
        gac = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if gac:
            logger.info(f"🔍 GOOGLE_APPLICATION_CREDENTIALS está configurada: {gac}")
        
        # Intentar obtener credenciales explícitamente primero para verificar ADC
        credentials = None
        try:
            logger.info("🔄 Verificando Application Default Credentials (ADC)...")
            credentials, detected_project = google_auth_default()
            logger.info(f"✅ ADC verificadas - proyecto detectado: {detected_project}")
        except Exception as adc_check_error:
            error_msg = str(adc_check_error)
            # Si el error menciona un path de ejemplo, es probable que haya un problema
            # pero intentemos crear el cliente de todas formas ya que ADC puede funcionar
            # El cliente de Firestore puede usar ADC de forma diferente a google_auth_default()
            if "/path/to/" in error_msg or ("service-account.json" in error_msg and "not found" in error_msg):
                logger.warning(f"⚠️ Error al verificar ADC explícitamente (mensaje de ejemplo detectado)")
                logger.info("💡 Esto puede ser un falso positivo. Intentando crear cliente Firestore directamente...")
                logger.info("💡 El cliente de Firestore puede usar ADC de forma diferente")
                credentials = None  # Intentar sin credenciales explícitas
            elif isinstance(adc_check_error, DefaultCredentialsError):
                logger.warning(f"⚠️ ADC no disponible: {error_msg}")
                logger.info("💡 Para desarrollo local, ejecuta: gcloud auth application-default login")
                raise
            else:
                # Otro tipo de error, pero intentemos de todas formas
                logger.warning(f"⚠️ Error al verificar ADC: {error_msg}")
                logger.info("💡 Intentando crear cliente Firestore directamente...")
                credentials = None
        
        # Crear cliente de Firestore
        try:
            if credentials:
                logger.info("🔄 Creando cliente Firestore con credenciales ADC...")
                client = firestore.Client(project=self.project_id, credentials=credentials)
            else:
                logger.info("🔄 Creando cliente Firestore (usará ADC automáticamente)...")
                client = firestore.Client(project=self.project_id)
            
            logger.info(f"✅ Firestore configurado exitosamente para proyecto: {self.project_id}")
            return client
            
        except Exception as e:
            error_msg = str(e)
            
            # Si es el error específico del path de ejemplo, es un problema conocido
            # El servicio puede funcionar sin Firestore en el startup (carga lazy)
            if "/path/to/" in error_msg or ("service-account.json" in error_msg and "not found" in error_msg):
                logger.warning(f"⚠️ Error conocido con credenciales (mensaje de ejemplo detectado)")
                logger.warning("⚠️ Firestore no estará disponible en el startup, pero el servicio continuará")
                logger.warning("⚠️ Firestore se cargará de forma lazy cuando sea necesario")
                logger.info("💡 Para desarrollo local, ejecuta: gcloud auth application-default login")
                logger.info("💡 O configura GOOGLE_APPLICATION_CREDENTIALS con la ruta al archivo JSON")
                logger.info("💡 El servicio funcionará normalmente, pero algunas funciones de Firestore pueden no estar disponibles")
                
                # Retornar None para indicar que Firestore no está disponible
                # El código que lo usa debe manejar este caso
                return None
            else:
                logger.error(f"❌ Error creando cliente Firestore: {error_msg}")
                
                # Si es un error de credenciales, dar instrucciones
                if "credentials" in error_msg.lower() or "authentication" in error_msg.lower():
                    logger.error("💡 Para desarrollo local, ejecuta: gcloud auth application-default login")
                    logger.error("💡 O configura GOOGLE_APPLICATION_CREDENTIALS con la ruta al archivo JSON")
                
                raise


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

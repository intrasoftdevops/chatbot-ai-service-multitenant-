"""
Manager para manejar múltiples conexiones de Firebase
Cada cliente tiene su propio proyecto y base de datos de Firebase

Similar a FirebaseManager.java del servicio Spring Boot
"""
import logging
from typing import Optional, Dict
from threading import Lock
from google.cloud import firestore
from google.auth import default as google_auth_default

logger = logging.getLogger(__name__)


class FirebaseManager:
    """
    Manager para manejar múltiples conexiones de Firebase
    Cada tenant tiene su propio proyecto y base de datos
    """
    
    def __init__(self):
        """Inicializa el manager de Firebase"""
        # Cache de conexiones: clave = f"{project_id}:{database_id}"
        self._firestore_connections: Dict[str, firestore.Client] = {}
        self._lock = Lock()
        logger.info("✅ FirebaseManager inicializado")
    
    def get_firestore(self, project_id: str, database_id: str = "(default)") -> firestore.Client:
        """
        Obtiene una conexión de Firestore para un proyecto y base de datos específicos
        
        Args:
            project_id: ID del proyecto de Firebase
            database_id: ID de la base de datos (por defecto "(default)")
            
        Returns:
            Instancia de Firestore para el proyecto y base de datos
        """
        if not project_id or not project_id.strip():
            raise ValueError("Project ID cannot be null or empty")
        
        if not database_id or not database_id.strip():
            database_id = "(default)"
        
        # Crear clave única para la conexión
        connection_key = f"{project_id}:{database_id}"
        
        # Usar lock para acceso thread-safe
        with self._lock:
            # Si ya existe la conexión, retornarla
            if connection_key in self._firestore_connections:
                logger.debug(f"✅ Reutilizando conexión Firestore: {connection_key}")
                return self._firestore_connections[connection_key]
            
            # Crear nueva conexión
            logger.info(f"🔧 Creando nueva conexión de Firestore para proyecto: {project_id}, database: {database_id}")
            firestore_client = self._create_firestore_connection(project_id, database_id)
            
            # Guardar en cache
            self._firestore_connections[connection_key] = firestore_client
            
            logger.info(f"✅ Conexión de Firestore creada exitosamente: {connection_key}")
            return firestore_client
    
    def _create_firestore_connection(self, project_id: str, database_id: str) -> firestore.Client:
        """
        Crea una nueva conexión de Firestore para el proyecto y base de datos especificados
        
        Args:
            project_id: ID del proyecto
            database_id: ID de la base de datos
            
        Returns:
            Nueva instancia de Firestore
        """
        try:
            logger.info(f"🔄 Inicializando Firestore con project={project_id}, database={database_id}")
            
            # Verificar credenciales
            try:
                credentials, detected_project = google_auth_default()
                logger.info(f"✅ ADC verificadas - proyecto detectado: {detected_project}")
            except Exception as adc_error:
                logger.warning(f"⚠️ Error verificando ADC: {adc_error}")
                logger.info("💡 Intentando crear cliente Firestore directamente (usará ADC automáticamente)")
            
            # Crear cliente de Firestore con proyecto y base de datos específicos
            firestore_client = firestore.Client(project=project_id, database=database_id)
            
            logger.info(f"✅ Cliente de Firestore creado exitosamente para {project_id}:{database_id}")
            return firestore_client
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error al crear conexión de Firestore para proyecto {project_id}, database {database_id}: {error_msg}")
            
            # Si es un error de credenciales, dar instrucciones
            if "credentials" in error_msg.lower() or "authentication" in error_msg.lower():
                logger.error("💡 Para desarrollo local, ejecuta: gcloud auth application-default login")
                logger.error("💡 O configura GOOGLE_APPLICATION_CREDENTIALS con la ruta al archivo JSON")
            
            raise RuntimeError(f"Failed to create Firestore connection for project: {project_id}, database: {database_id}") from e
    
    def close_all_connections(self):
        """Cierra todas las conexiones de Firestore"""
        with self._lock:
            logger.info(f"🔄 Cerrando {len(self._firestore_connections)} conexiones de Firestore")
            
            for connection_key, firestore_client in self._firestore_connections.items():
                try:
                    # Firestore Client en Python no tiene método close explícito
                    # Las conexiones se cierran automáticamente al salir del scope
                    logger.info(f"✅ Conexión {connection_key} marcada para cierre")
                except Exception as e:
                    logger.error(f"❌ Error al cerrar conexión {connection_key}: {e}")
            
            self._firestore_connections.clear()
            logger.info("✅ Todas las conexiones cerradas")


# Instancia global singleton
_firebase_manager_instance: Optional[FirebaseManager] = None
_manager_lock = Lock()


def get_firebase_manager() -> FirebaseManager:
    """
    Obtiene la instancia singleton de FirebaseManager
    
    Returns:
        Instancia de FirebaseManager
    """
    global _firebase_manager_instance
    
    if _firebase_manager_instance is None:
        with _manager_lock:
            if _firebase_manager_instance is None:
                _firebase_manager_instance = FirebaseManager()
    
    return _firebase_manager_instance


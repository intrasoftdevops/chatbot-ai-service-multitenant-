"""
Configuración de optimizaciones para el chatbot AI service
"""
import os

class OptimizationConfig:
    """Configuración de optimizaciones de rendimiento"""
    
    # Timeout para respuestas de IA (segundos)
    AI_RESPONSE_TIMEOUT = int(os.getenv("AI_RESPONSE_TIMEOUT", "15"))
    
    # Límite de caracteres para respuestas
    MAX_RESPONSE_LENGTH = int(os.getenv("MAX_RESPONSE_LENGTH", "800"))
    
    # Número máximo de resultados de contexto
    MAX_CONTEXT_RESULTS = int(os.getenv("MAX_CONTEXT_RESULTS", "2"))
    
    # Número máximo de mensajes de contexto de conversación
    MAX_CONVERSATION_CONTEXT = int(os.getenv("MAX_CONVERSATION_CONTEXT", "3"))
    
    # Habilitar cache inteligente
    USE_INTELLIGENT_CACHE = os.getenv("USE_INTELLIGENT_CACHE", "true").lower() == "true"
    
    # Habilitar preprocesamiento de documentos
    USE_DOCUMENT_PREPROCESSING = os.getenv("USE_DOCUMENT_PREPROCESSING", "true").lower() == "true"
    
    # Habilitar contexto de sesión
    USE_SESSION_CONTEXT = os.getenv("USE_SESSION_CONTEXT", "true").lower() == "true"
    
    # Configuraciones de cache
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
    CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "1000"))
    
    # Configuraciones de documentos
    AUTO_PREPROCESS_DOCUMENTS = os.getenv("AUTO_PREPROCESS_DOCUMENTS", "true").lower() == "true"
    PREPROCESSING_TIMEOUT = int(os.getenv("PREPROCESSING_TIMEOUT", "300"))
    
    # Configuraciones de conversación
    ENABLE_CONVERSATION_CONTEXT = os.getenv("ENABLE_CONVERSATION_CONTEXT", "true").lower() == "true"
    MAX_MEMORY_MESSAGES = int(os.getenv("MAX_MEMORY_MESSAGES", "10"))
    
    # Configuraciones de debugging
    ENABLE_OPTIMIZATION_LOGS = os.getenv("ENABLE_OPTIMIZATION_LOGS", "true").lower() == "true"
    ENABLE_PERFORMANCE_METRICS = os.getenv("ENABLE_PERFORMANCE_METRICS", "true").lower() == "true"

# Instancia global de configuración
optimization_config = OptimizationConfig()

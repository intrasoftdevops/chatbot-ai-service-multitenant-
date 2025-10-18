"""
Configuraciones de modelo Gemini por tipo de tarea

Este módulo define configuraciones específicas para diferentes tipos de tareas,
optimizando temperatura, top_p, y otros parámetros según el caso de uso.

Estrategia:
- Tareas determinísticas (clasificación, extracción): temperature=0.0
- Tareas conversacionales: temperature=0.7
- Tareas analíticas complejas: modelos más potentes

Impacto esperado:
- +5-10% precisión en clasificación
- Respuestas JSON más confiables
- Menos retries por respuestas inválidas
"""

from typing import Dict, Any

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIONES POR TIPO DE TAREA
# ══════════════════════════════════════════════════════════════════════════════

MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    # ──────────────────────────────────────────────────────────────────────────
    # CHAT CONVERSACIONAL
    # ──────────────────────────────────────────────────────────────────────────
    "chat_conversational": {
        "model_name": "gemini-2.5-flash",
        "temperature": 0.7,  # Respuestas naturales y variadas
        "top_p": 0.8,
        "top_k": 40,
        "max_output_tokens": 1024,
        "description": "Para conversaciones naturales con el usuario",
    },
    
    # ──────────────────────────────────────────────────────────────────────────
    # CLASIFICACIÓN DE INTENCIONES
    # ──────────────────────────────────────────────────────────────────────────
    "intent_classification": {
        "model_name": "gemini-2.5-flash",
        "temperature": 0.0,  # Completamente determinístico
        "top_p": 0.1,  # Muy restrictivo
        "top_k": 1,  # Solo la mejor opción
        "max_output_tokens": 100,  # Respuestas cortas
        # "response_mime_type": "application/json",  # No soportado en 0.3.2
        "description": "Para clasificar intenciones con alta precisión",
    },
    
    # ──────────────────────────────────────────────────────────────────────────
    # EXTRACCIÓN DE DATOS
    # ──────────────────────────────────────────────────────────────────────────
    "data_extraction": {
        "model_name": "gemini-2.5-flash",
        "temperature": 0.0,  # Determinístico
        "top_p": 0.1,
        "top_k": 1,
        "max_output_tokens": 512,
        # "response_mime_type": "application/json",  # No soportado en 0.3.2
        "description": "Para extraer datos estructurados (nombre, ciudad, teléfono)",
    },
    
    # ──────────────────────────────────────────────────────────────────────────
    # VALIDACIÓN DE DATOS
    # ──────────────────────────────────────────────────────────────────────────
    "data_validation": {
        "model_name": "gemini-2.5-flash",
        "temperature": 0.0,  # Determinístico
        "top_p": 0.1,
        "top_k": 1,
        "max_output_tokens": 256,
        # "response_mime_type": "application/json",  # No soportado en 0.3.2
        "description": "Para validar datos con criterios estrictos",
    },
    
    # ──────────────────────────────────────────────────────────────────────────
    # ANÁLISIS DE DOCUMENTOS
    # ──────────────────────────────────────────────────────────────────────────
    "document_analysis": {
        "model_name": "gemini-2.5-pro",  # Modelo más potente
        "temperature": 0.1,  # Casi determinístico, pero con algo de creatividad
        "top_p": 0.9,
        "top_k": 40,
        "max_output_tokens": 2048,  # Respuestas más largas
        "description": "Para análisis profundo de documentos complejos",
    },
    
    # ──────────────────────────────────────────────────────────────────────────
    # DETECCIÓN DE COMPORTAMIENTO MALICIOSO
    # ──────────────────────────────────────────────────────────────────────────
    "malicious_detection": {
        "model_name": "gemini-2.5-flash",
        "temperature": 0.0,  # Muy estricto
        "top_p": 0.1,
        "top_k": 1,
        "max_output_tokens": 200,
        # "response_mime_type": "application/json",  # No soportado en 0.3.2
        "description": "Para detectar intentos maliciosos con alta precisión",
    },
    
    # ──────────────────────────────────────────────────────────────────────────
    # ANÁLISIS DE REGISTRO
    # ──────────────────────────────────────────────────────────────────────────
    "registration_analysis": {
        "model_name": "gemini-2.5-flash",
        "temperature": 0.1,  # Casi determinístico
        "top_p": 0.2,
        "top_k": 5,
        "max_output_tokens": 512,
        # "response_mime_type": "application/json",  # No soportado en 0.3.2
        "description": "Para analizar respuestas en flujo de registro",
    },
    
    # ──────────────────────────────────────────────────────────────────────────
    # NORMALIZACIÓN DE UBICACIONES
    # ──────────────────────────────────────────────────────────────────────────
    "location_normalization": {
        "model_name": "gemini-2.0-flash",
        "temperature": 0.0,  # Completamente determinístico
        "top_p": 0.1,
        "top_k": 1,
        "max_output_tokens": 100,
        # "response_mime_type": "application/json",  # No soportado en 0.3.2
        "description": "Para normalizar nombres de ciudades con precisión",
    },
    
    # ──────────────────────────────────────────────────────────────────────────
    # GENERACIÓN DE RESPUESTAS CON SESIÓN
    # ──────────────────────────────────────────────────────────────────────────
    "chat_with_session": {
        "model_name": "gemini-2.0-flash",
        "temperature": 0.6,  # Balanceado entre consistencia y naturalidad
        "top_p": 0.8,
        "top_k": 40,
        "max_output_tokens": 1024,
        "description": "Para respuestas que consideran contexto de sesión",
    },
    
    # ──────────────────────────────────────────────────────────────────────────
    # RAG (Retrieval-Augmented Generation)
    # ──────────────────────────────────────────────────────────────────────────
    "rag_generation": {
        "model_name": "gemini-1.5-pro",  # Modelo potente para RAG
        "temperature": 0.3,  # Balance entre precisión y naturalidad
        "top_p": 0.9,
        "top_k": 40,
        "max_output_tokens": 2048,
        "description": "Para generar respuestas basadas en documentos (RAG)",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES PÚBLICAS
# ══════════════════════════════════════════════════════════════════════════════

def get_config_for_task(task_type: str) -> Dict[str, Any]:
    """
    Obtiene la configuración óptima para un tipo de tarea
    
    Args:
        task_type: Tipo de tarea (ej: "intent_classification", "chat_conversational")
        
    Returns:
        Diccionario con la configuración del modelo
        
    Ejemplo:
        >>> config = get_config_for_task("intent_classification")
        >>> print(config["temperature"])  # 0.0
        >>> print(config["model_name"])   # "gemini-2.0-flash"
    """
    # Si la tarea no existe, usar configuración conversacional por defecto
    if task_type not in MODEL_CONFIGS:
        return MODEL_CONFIGS["chat_conversational"].copy()
    
    return MODEL_CONFIGS[task_type].copy()


def list_available_tasks() -> list:
    """
    Lista todas las tareas disponibles con sus descripciones
    
    Returns:
        Lista de tuplas (task_type, description)
        
    Ejemplo:
        >>> tasks = list_available_tasks()
        >>> for task, desc in tasks:
        ...     print(f"{task}: {desc}")
    """
    return [
        (task, config.get("description", "Sin descripción"))
        for task, config in MODEL_CONFIGS.items()
    ]


def get_task_summary() -> Dict[str, str]:
    """
    Obtiene un resumen de todas las tareas y sus modelos
    
    Returns:
        Diccionario con task_type -> model_name
        
    Ejemplo:
        >>> summary = get_task_summary()
        >>> print(summary["intent_classification"])  # "gemini-2.0-flash"
    """
    return {
        task: config.get("model_name", "unknown")
        for task, config in MODEL_CONFIGS.items()
    }


# ══════════════════════════════════════════════════════════════════════════════
# MAPEO DE MÉTODOS A TASK TYPES
# ══════════════════════════════════════════════════════════════════════════════

METHOD_TO_TASK_TYPE = {
    "classify_intent": "intent_classification",
    "_classify_with_ai": "intent_classification",
    "_detect_malicious_intent": "malicious_detection",
    "extract_data": "data_extraction",
    "_extract_with_ai": "data_extraction",
    "validate_data": "data_validation",
    "_validate_with_ai": "data_validation",
    "normalize_location": "location_normalization",
    "_analyze_city_with_ai": "location_normalization",
    "analyze_registration": "registration_analysis",
    "_analyze_registration_with_ai": "registration_analysis",
    "process_chat_message": "chat_with_session",
    "_generate_ai_response_with_session": "chat_with_session",
    "_generate_ai_response": "chat_conversational",
    "_build_chat_prompt": "chat_conversational",
}


def get_task_type_for_method(method_name: str) -> str:
    """
    Obtiene el task_type apropiado para un método de AIService
    
    Args:
        method_name: Nombre del método (ej: "classify_intent")
        
    Returns:
        Task type correspondiente
        
    Ejemplo:
        >>> task = get_task_type_for_method("classify_intent")
        >>> print(task)  # "intent_classification"
    """
    return METHOD_TO_TASK_TYPE.get(method_name, "chat_conversational")


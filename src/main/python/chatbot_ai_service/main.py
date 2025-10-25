"""
Chatbot AI Service - Simplificado
================================

Servicio de IA que se enfoca únicamente en procesamiento de IA.
Recibe configuración del proyecto Political Referrals via HTTP.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx
from dotenv import load_dotenv
import logging

from chatbot_ai_service.controllers.chat_controller import router as chat_router
from chatbot_ai_service.controllers.city_normalization_controller import router as city_router
from chatbot_ai_service.controllers.preprocessing_controller import router as preprocessing_router

# Cargar variables de entorno
# Buscar .env en el directorio raíz del proyecto (3 niveles arriba)
import pathlib
project_root = pathlib.Path(__file__).parent.parent.parent.parent.parent
env_path = project_root / ".env"
print(f"🔍 Buscando archivo .env en: {env_path}")
print(f"📁 Archivo .env existe: {env_path.exists()}")
load_dotenv(env_path)

# Verificar que POLITICAL_REFERRALS_SERVICE_URL se cargó
political_url = os.getenv("POLITICAL_REFERRALS_SERVICE_URL")
if political_url:
    print(f"✅ POLITICAL_REFERRALS_SERVICE_URL cargada: {political_url}")
else:
    print("❌ POLITICAL_REFERRALS_SERVICE_URL no encontrada")

# Configurar logging global para que se vean logs de controllers/servicios
log_level_str = os.getenv("LOG_LEVEL", "DEBUG").upper()
log_level = getattr(logging, log_level_str, logging.DEBUG)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logging.getLogger(__name__).info(f"Logging configurado en nivel: {log_level_str}")

# Verificar que la API key se cargó correctamente
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    print(f"✅ GEMINI_API_KEY cargada correctamente: {api_key[:10]}...")
else:
    print("❌ GEMINI_API_KEY no encontrada")

# 🚀 DEBUG: Verificar variables de optimización
local_dev = os.getenv("LOCAL_DEVELOPMENT", "false").lower() == "true"
ultra_fast = os.getenv("ULTRA_FAST_MODE", "false").lower() == "true"
print(f"🚀 DEBUG - LOCAL_DEVELOPMENT: {local_dev}")
print(f"🚀 DEBUG - ULTRA_FAST_MODE: {ultra_fast}")

# 🚀 OPTIMIZACIÓN: Pre-cargar modelos de IA después de cargar variables de entorno
try:
    print("🚀 Iniciando pre-carga de modelos de IA...")
    from chatbot_ai_service.services.ai_service import ai_service
    ai_service.preload_models_on_startup()
    print("✅ Pre-carga de modelos completada")
except Exception as e:
    print(f"❌ Error durante pre-carga: {e}")
    # No fallar el startup si hay error en la pre-carga

# 🚀 PRECARGA AUTOMÁTICA DE DOCUMENTOS
async def preload_documents_on_startup_optimized():
    """Precargar documentos automáticamente al inicio del servicio usando el servicio optimizado"""
    try:
        print("🚀 Iniciando precarga optimizada de documentos...")
        
        # Importar servicios optimizados
        from chatbot_ai_service.services.document_preprocessor_service import document_preprocessor_service
        from chatbot_ai_service.services.tenant_memory_service import tenant_memory_service
        
        # Obtener configuración de tenants desde Firestore
        response_data = await get_tenant_configs_from_firestore()
        
        if not response_data or not isinstance(response_data, dict):
            print("⚠️ No se pudieron obtener configuraciones de tenants desde Firestore")
            return
        
        # Extraer la lista de tenants de la respuesta
        tenant_configs = response_data.get("tenants", {})
        
        if not tenant_configs:
            print("⚠️ No se encontraron configuraciones de tenants en la respuesta")
            return
        
        print(f"📊 Encontrados {len(tenant_configs)} tenants para precargar")
        
        # Inicializar memoria para cada tenant (rápido)
        for tenant_id, tenant_config in tenant_configs.items():
            print(f"🧠 Inicializando memoria para tenant {tenant_id}...")
            memory_success = tenant_memory_service.initialize_tenant_memory(
                tenant_id=tenant_id,
                tenant_config=tenant_config,
                document_summary=""  # Se llenará después si hay documentos
            )
            
            if memory_success:
                print(f"✅ Memoria inicializada para tenant {tenant_id}")
            else:
                print(f"⚠️ No se pudo inicializar memoria para tenant {tenant_id}")
        
        # Hacer preprocesamiento SÍNCRONO usando asyncio.run() en un hilo separado
        print("🚀 Iniciando preprocesamiento SÍNCRONO...")
        import asyncio
        import threading
        
        def run_sync_preprocessing():
            async def synchronous_preprocessing():
                try:
                    print("📚 [SYNC] Iniciando preprocesamiento de documentos...")
                    results = await document_preprocessor_service.preprocess_all_tenants()
                    
                    successful_tenants = sum(1 for success in results.values() if success)
                    print(f"✅ [SYNC] Preprocesamiento completado: {successful_tenants}/{len(results)} tenants exitosos")
                    
                    # Mostrar estadísticas de memoria
                    memory_stats = tenant_memory_service.get_memory_stats()
                    print(f"🧠 [SYNC] Estadísticas de memoria:")
                    print(f"  - Memorias de tenants: {memory_stats['tenant_memories']}")
                    print(f"  - Conciencias de usuarios: {memory_stats['user_consciousness']}")
                    
                    print("🎉 [SYNC] ¡Preprocesamiento completado! El servicio está completamente optimizado.")
                    return True
                    
                except Exception as e:
                    print(f"❌ [SYNC] Error en preprocesamiento: {e}")
                    return False
            
            # Ejecutar en un nuevo event loop
            return asyncio.run(synchronous_preprocessing())
        
        # Ejecutar preprocesamiento en un hilo separado para evitar conflictos con el event loop principal
        preprocessing_thread = threading.Thread(target=run_sync_preprocessing)
        preprocessing_thread.start()
        preprocessing_thread.join()  # Esperar a que termine
        
        print("✅ Servicio completamente listo - todos los documentos preprocesados")
    except Exception as e:
        print(f"❌ Error durante precarga optimizada de documentos: {e}")
        # No fallar el startup si hay error en la precarga

async def get_tenant_configs_from_firestore():
    """Obtener configuración de todos los tenants directamente desde Firestore"""
    try:
        from chatbot_ai_service.services.firestore_tenant_service import firestore_tenant_service
        
        print("🔍 Obteniendo configuraciones de tenants desde Firestore...")
        tenant_configs = await firestore_tenant_service.get_all_tenant_configs()
        
        if tenant_configs:
            print(f"✅ Configuraciones obtenidas desde Firestore: {len(tenant_configs)} tenants")
            return {
                "status": "success",
                "tenants": tenant_configs,
                "total_tenants": len(tenant_configs)
            }
        else:
            print("⚠️ No se encontraron configuraciones de tenants en Firestore")
            return {
                "status": "success",
                "tenants": {},
                "total_tenants": 0
            }
            
    except Exception as e:
        print(f"❌ Error obteniendo configuración de tenants desde Firestore: {e}")
        return {
            "status": "error",
            "tenants": {},
            "total_tenants": 0,
            "error": str(e)
        }

# Configuración de la aplicación
app = FastAPI(
    title="Chatbot AI Service",
    description="Servicio de IA para chatbots políticos - Solo procesamiento de IA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(chat_router)
app.include_router(city_router)
app.include_router(preprocessing_router)

# Importar y agregar el nuevo controlador de clasificación de intenciones
from chatbot_ai_service.controllers.intent_classification_controller import router as intent_classification_router
app.include_router(intent_classification_router)

# 🚀 EVENTO DE STARTUP: Precargar documentos automáticamente
@app.on_event("startup")
async def startup_event():
    """Evento de startup para precargar documentos automáticamente"""
    await preload_documents_on_startup_optimized()

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "chatbot-ai-service",
        "version": "1.0.0",
        "description": "Servicio de IA para chatbots políticos",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check del servicio con verificación de preprocesamiento"""
    try:
        from chatbot_ai_service.services.document_preprocessor_service import document_preprocessor_service
        
        # Obtener estado del preprocesamiento
        cache_stats = document_preprocessor_service.get_cache_stats()
        processing_statuses = cache_stats.get("processing_status", {})
        
        # Verificar si hay tenants en procesamiento o fallidos
        processing_tenants = [tenant for tenant, status in processing_statuses.items() 
                            if status in ["processing"]]
        failed_tenants = [tenant for tenant, status in processing_statuses.items() 
                        if status in ["failed", "timeout"]]
        completed_tenants = [tenant for tenant, status in processing_statuses.items() 
                            if status == "completed"]
        
        # Determinar estado de salud - CRÍTICO: Solo "healthy" cuando esté completamente listo
        if processing_tenants:
            health_status = "preprocessing"  # Cloud Run NO enviará tráfico
        elif failed_tenants:
            health_status = "degraded"      # Cloud Run NO enviará tráfico
        elif completed_tenants:
            health_status = "healthy"       # Cloud Run SÍ enviará tráfico
        else:
            health_status = "starting"      # Cloud Run NO enviará tráfico
        
        return {
            "status": health_status,
            "service": "chatbot-ai-service",
            "version": "1.0.0",
            "preprocessing": {
                "completed_tenants": len(completed_tenants),
                "processing_tenants": len(processing_tenants),
                "failed_tenants": len(failed_tenants),
                "total_tenants": cache_stats.get("total_tenants", 0)
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "service": "chatbot-ai-service",
            "version": "1.0.0",
            "error": str(e)
        }

@app.get("/ready")
async def readiness_check():
    """Readiness check - Con preprocesamiento síncrono, si el servicio está disponible ya está listo"""
    return {"status": "ready"}

# Nota: La aplicación se ejecuta con Granian (servidor ASGI en Rust)
# Ver run_server.sh (local) o Dockerfile (producción) para configuración del servidor
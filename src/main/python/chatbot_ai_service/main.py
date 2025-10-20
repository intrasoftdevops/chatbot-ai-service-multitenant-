"""
Chatbot AI Service - Simplificado
================================

Servicio de IA que se enfoca únicamente en procesamiento de IA.
Recibe configuración del proyecto Political Referrals via HTTP.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import logging

from chatbot_ai_service.controllers.chat_controller import router as chat_router
from chatbot_ai_service.controllers.city_normalization_controller import router as city_router

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

# Importar y agregar el nuevo controlador de clasificación de intenciones
from chatbot_ai_service.controllers.intent_classification_controller import router as intent_classification_router
app.include_router(intent_classification_router)

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
    """Health check del servicio"""
    return {
        "status": "healthy",
        "service": "chatbot-ai-service",
        "version": "1.0.0"
    }

# Nota: La aplicación se ejecuta con Granian (servidor ASGI en Rust)
# Ver run_server.sh (local) o Dockerfile (producción) para configuración del servidor
"""
Chatbot AI Service - Simplificado
================================

Servicio de IA que se enfoca únicamente en procesamiento de IA.
Recibe configuración del proyecto Political Referrals via HTTP.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
import logging

from chatbot_ai_service.controllers.chat_controller import router as chat_router

# Cargar variables de entorno
# Buscar .env en el directorio raíz del proyecto (3 niveles arriba)
import pathlib
project_root = pathlib.Path(__file__).parent.parent.parent.parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

# Configurar logging global para que se vean logs de controllers/servicios
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
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
app.include_router(chat_router, prefix="/api/v1")

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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development"
    )
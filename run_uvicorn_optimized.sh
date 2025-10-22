#!/bin/zsh

# ══════════════════════════════════════════════════════════════════════════════
# Script para ejecutar el servidor con Uvicorn optimizado para máxima velocidad
# ══════════════════════════════════════════════════════════════════════════════

cd /Users/santiagobuitragorojas/Documents/Intrasoft/Repos/daniel-quintero-repos/Refactor/chatbot-ai-service-multitenant

# Activar entorno virtual
source venv/bin/activate

# Cargar variables de entorno desde .env
set -a
source .env
set +a

# Configurar PYTHONPATH
PYTHONPATH="$(pwd)/src/main/python"
export PYTHONPATH

# ──────────────────────────────────────────────────────────────────────────────
# 🚀 FEATURE FLAGS para máxima velocidad
# ──────────────────────────────────────────────────────────────────────────────
USE_GEMINI_CLIENT=true
export USE_GEMINI_CLIENT

USE_ADVANCED_MODEL_CONFIGS=true
export USE_ADVANCED_MODEL_CONFIGS

# ──────────────────────────────────────────────────────────────────────────────
# 🚀 Ejecutar servidor con Uvicorn optimizado
# ──────────────────────────────────────────────────────────────────────────────
echo "══════════════════════════════════════════════════════════════════════════════"
echo "🚀 INICIANDO CHATBOT AI SERVICE - Uvicorn Optimizado"
echo "══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📍 PYTHONPATH: $PYTHONPATH"
echo ""
echo "🎯 FEATURE FLAGS:"
echo "   ✅ USE_GEMINI_CLIENT: $USE_GEMINI_CLIENT"
echo "   ✅ USE_ADVANCED_MODEL_CONFIGS: $USE_ADVANCED_MODEL_CONFIGS"
echo ""
echo "🔧 SERVICIOS:"
echo "   🌐 CONFIG SERVICE: $POLITICAL_REFERRALS_SERVICE_URL"
echo ""
echo "══════════════════════════════════════════════════════════════════════════════"
echo "🎮 Servidor arrancando con Uvicorn optimizado..."
echo "══════════════════════════════════════════════════════════════════════════════"
echo ""

# Usar Uvicorn con configuración optimizada para máxima velocidad
python -m uvicorn chatbot_ai_service.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --loop uvloop \
    --http httptools \
    --access-log \
    --log-level info \
    --timeout-keep-alive 30 \
    --timeout-graceful-shutdown 10 \
    --limit-concurrency 1000 \
    --limit-max-requests 10000 \
    --backlog 2048

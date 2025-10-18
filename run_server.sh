#!/bin/zsh

# ══════════════════════════════════════════════════════════════════════════════
# Script para ejecutar el servidor con FASE 1 + FASE 2 activadas
# ══════════════════════════════════════════════════════════════════════════════

cd /Users/user/Desktop/chatbot-ai-service-multitenant-

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
# 🚀 FASE 1: Activar GeminiClient
# ──────────────────────────────────────────────────────────────────────────────
USE_GEMINI_CLIENT=true
export USE_GEMINI_CLIENT

# ──────────────────────────────────────────────────────────────────────────────
# 🎯 FASE 2: Activar Configuraciones Avanzadas
# ──────────────────────────────────────────────────────────────────────────────
USE_ADVANCED_MODEL_CONFIGS=true
export USE_ADVANCED_MODEL_CONFIGS

# ──────────────────────────────────────────────────────────────────────────────
# 🧠 FASE 6: Activar RAGOrchestrator (SMART MODE)
# ──────────────────────────────────────────────────────────────────────────────
USE_RAG_ORCHESTRATOR=false  # Cambiar a true para activar RAG
export USE_RAG_ORCHESTRATOR

# ──────────────────────────────────────────────────────────────────────────────
# 🛡️ FASE 5: Activar Guardrails Estrictos
# ──────────────────────────────────────────────────────────────────────────────
USE_GUARDRAILS=true  # Prompts con guardrails anti-alucinación
STRICT_GUARDRAILS=true  # Modo estricto: fallas críticas invalidan respuesta
export USE_GUARDRAILS
export STRICT_GUARDRAILS

# ──────────────────────────────────────────────────────────────────────────────
# 💾 Redis Cache (Ya configurado en .env, pero puede sobrescribirse aquí)
# ──────────────────────────────────────────────────────────────────────────────
# REDIS_ENABLED ya está en .env como true
# REDIS_HOST ya está en .env como 10.47.98.187

# ──────────────────────────────────────────────────────────────────────────────
# 🚀 Ejecutar servidor
# ──────────────────────────────────────────────────────────────────────────────
echo "══════════════════════════════════════════════════════════════════════════════"
echo "🚀 INICIANDO CHATBOT AI SERVICE - MULTITENANT"
echo "══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📍 PYTHONPATH: $PYTHONPATH"
echo ""
echo "🎯 FEATURE FLAGS:"
echo "   ✅ FASE 1 - USE_GEMINI_CLIENT: $USE_GEMINI_CLIENT"
echo "   ✅ FASE 2 - USE_ADVANCED_MODEL_CONFIGS: $USE_ADVANCED_MODEL_CONFIGS"
echo "   🛡️ FASE 5 - USE_GUARDRAILS: $USE_GUARDRAILS (Strict: $STRICT_GUARDRAILS)"
echo "   🧠 FASE 6 - USE_RAG_ORCHESTRATOR: $USE_RAG_ORCHESTRATOR"
echo ""
echo "🔧 SERVICIOS:"
echo "   🌐 CONFIG SERVICE: $POLITICAL_REFERRALS_SERVICE_URL"
echo "   💾 REDIS: $REDIS_ENABLED (Host: $REDIS_HOST)"
echo ""
echo "══════════════════════════════════════════════════════════════════════════════"
echo "🎮 Servidor arrancando... Busca estos logs:"
echo "   ✅ GeminiClient habilitado via feature flag"
echo "   ✅ Configuraciones avanzadas de modelo habilitadas"
echo "   🛡️ Guardrails estrictos habilitados"
echo "   🧠 RAGOrchestrator habilitado (si USE_RAG_ORCHESTRATOR=true)"
echo "══════════════════════════════════════════════════════════════════════════════"
echo ""

python3 src/main/python/chatbot_ai_service/main.py


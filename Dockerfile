# ============================================================================
# Multi-stage Dockerfile optimizado para Chatbot AI Service Multi-Tenant
# ============================================================================

# ============================================================================
# STAGE 1: Builder - Instala dependencias y compila paquetes
# ============================================================================
FROM python:3.11-slim AS builder

# Variables de entorno para build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Instalar SOLO dependencias necesarias para compilar
# Separamos en capas para mejor cache
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y actualizar pip
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel

# Instalar dependencias en un directorio específico (para copiar después)
RUN pip install --prefix=/install --no-warn-script-location \
    google-generativeai==0.8.5 \
    llama-index-core==0.14.5 \
    llama-index-llms-gemini==0.6.1 \
    llama-index-embeddings-gemini==0.4.1

# Instalar resto de dependencias
RUN pip install --prefix=/install --no-warn-script-location -r requirements.txt

# ============================================================================
# STAGE 2: Runtime - Imagen final optimizada
# ============================================================================
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    PYTHONPATH=/app \
    NLTK_DATA=/app/nltk_data

WORKDIR /app

# Instalar SOLO runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar dependencias instaladas desde builder
COPY --from=builder /install /usr/local

# Crear usuario no root ANTES de copiar archivos
RUN useradd --create-home --shell /bin/bash app \
    && mkdir -p /app/nltk_data \
    && chown -R app:app /app

# Copiar código fuente
COPY --chown=app:app src/main/python/ .

# Cambiar a usuario no root
USER app

# Health check (sin dependencias extras)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

# Exponer puerto
EXPOSE ${PORT}

# Comando de inicio con Granian (servidor Rust ultrarrápido)
# --workers 2: Procesos paralelos (aprovechar CPU de Cloud Run)
# Nota: ASGI no soporta --blocking-threads > 1, pero 2 workers ya da paralelización
CMD ["sh", "-c", "granian --interface asgi chatbot_ai_service.main:app --host 0.0.0.0 --port ${PORT} --workers 2"]


# Dockerfile para Chatbot AI Service Multi-Tenant
FROM python:3.11-slim

# Configurar variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar paquetes de Python
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3-dev \
    cargo \
    rustc \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .

# Actualizar pip, setuptools y wheel primero
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Instalar dependencias pesadas primero con VERSIONES EXACTAS
# Versiones específicas evitan resolución compleja de pip en Cloud Build
RUN pip install --no-cache-dir \
    google-generativeai==0.8.5 \
    llama-index-core==0.14.5 \
    llama-index-llms-gemini==0.6.1 \
    llama-index-embeddings-gemini==0.4.1

# Instalar el resto de dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente (Python package root)
COPY src/main/python/ .

# Asegurar PYTHONPATH para imports desde /app
ENV PYTHONPATH=/app

# Configurar NLTK_DATA para LlamaIndex
ENV NLTK_DATA=/app/nltk_data

# Crear usuario no root
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app \
    && mkdir -p /app/nltk_data \
    && chown -R app:app /app/nltk_data
USER app

# Exponer puerto
EXPOSE $PORT

# Comando de inicio (usar puerto proporcionado por Cloud Run)
CMD ["sh", "-c", "python -m uvicorn chatbot_ai_service.main:app --host 0.0.0.0 --port ${PORT}"]


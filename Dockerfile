# Dockerfile para Chatbot AI Service Multi-Tenant
FROM python:3.11-slim

# Configurar variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
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


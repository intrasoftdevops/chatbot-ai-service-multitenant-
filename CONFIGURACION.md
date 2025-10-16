# 🔧 Configuración del Servicio AI Multi-Tenant

## ⚠️ IMPORTANTE: API Key de Google Gemini

Para que el servicio genere **respuestas en lenguaje natural** usando IA, necesitas configurar tu API key de Google Gemini.

### Paso 1: Obtener API Key

1. Ve a: https://makersuite.google.com/app/apikey
2. Crea o copia tu API key de Google AI Studio

### Paso 2: Crear archivo `.env`

Crea un archivo `.env` en la raíz del proyecto (`chatbot-ai-service-multitenant/`) con el siguiente contenido:

```bash
# Google AI (Gemini) - REQUERIDO
GOOGLE_API_KEY=tu_api_key_aqui

# Firebase (para obtener configuración de tenants)
FIRESTORE_PROJECT_ID=political-referrals

# Opcional: Si usas service account para Firestore localmente
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Paso 3: Reiniciar el servicio

```bash
cd Refactor/chatbot-ai-service-multitenant
source venv/bin/activate
cd src/main/python
python -c "
from chatbot_ai_service.main_with_intents import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')"
```

## ✅ Verificar que funciona

Después de configurar la API key, el servicio debería:

1. ✅ Generar respuestas en lenguaje natural variadas (NO siempre iguales)
2. ✅ Responder preguntas contextuales: "¿qué es esto?", "¿quién eres?", etc.
3. ✅ Usar información del tenant desde Firestore

## 🚨 Sin API Key

Si NO configuras la `GOOGLE_API_KEY`, el servicio:
- ⚠️ Usará respuestas de fallback predefinidas (limitadas)
- ⚠️ NO generará respuestas en lenguaje natural
- ⚠️ Las respuestas serán siempre iguales

## 📝 Verificar configuración

Para verificar que la API key está cargada correctamente, revisa los logs del servicio Python:

```
# Si está configurada correctamente:
INFO:chatbot_ai_service.main_with_intents:Enviando prompt a Gemini: ...
INFO:chatbot_ai_service.main_with_intents:Respuesta generada por Gemini: ...

# Si NO está configurada:
WARNING:chatbot_ai_service.main_with_intents:No se encontró GOOGLE_API_KEY, usando respuesta contextual por defecto
```


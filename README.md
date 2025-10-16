# 🤖 Chatbot AI Service Multi-Tenant

## 📋 Descripción

**Chatbot AI Service Multi-Tenant** es el servicio de IA que reemplaza el ChatbotIA actual. Proporciona RAG conversacional, análisis de intenciones y extracción de datos para múltiples clientes (tenants) políticos usando las bases de datos existentes. El sistema es **genérico** y puede ser usado por cualquier candidato político.

## ✨ Funcionalidades Principales

- **Multi-Tenancy**: Soporte completo para múltiples campañas políticas
- **IA Conversacional**: Integración con Gemini AI y LlamaIndex para RAG
- **Análisis de Intenciones**: Clasificación automática de mensajes
- **Extracción de Datos**: Reconocimiento de información del usuario
- **Gestión de Conversaciones**: Historial y contexto por tenant
- **Cache Inteligente**: Redis para optimizar rendimiento
- **APIs RESTful**: Integración con Political Referrals Service

## 🏗️ Arquitectura

### Enfoque Multi-Tenant
- ✅ **Usar bases de datos existentes** - sin migración de datos
- ✅ **Filtrar por `tenant_id`** en todas las consultas
- ✅ **Configuración desde `/clientes`** existente
- ✅ **Cache por tenant** para mejor rendimiento

### Servicios Integrados
- **TenantService**: Gestión de configuración por tenant
- **AIService**: Procesamiento con Gemini AI y LlamaIndex
- **ConversationService**: Gestión de conversaciones multi-tenant

## 📊 APIs Disponibles

### Gestión de Tenants
- `GET /api/v1/tenants/{tenantId}` - Configuración completa
- `GET /api/v1/tenants/{tenantId}/status` - Estado del tenant
- `GET /api/v1/tenants/{tenantId}/health` - Health check
- `GET /api/v1/tenants/{tenantId}/stats` - Estadísticas
- `GET /api/v1/tenants/{tenantId}/ai-config` - Configuración IA
- `GET /api/v1/tenants/{tenantId}/branding-config` - Configuración marca

### Chat e IA
- `POST /api/v1/tenants/{tenantId}/chat` - Procesar mensaje
- `GET /api/v1/tenants/{tenantId}/conversations/{sessionId}/history` - Historial
- `GET /api/v1/tenants/{tenantId}/conversations/active` - Conversaciones activas
- `GET /api/v1/tenants/{tenantId}/conversations/phone/{phone}` - Por teléfono
- `GET /api/v1/tenants/{tenantId}/conversations/stats` - Estadísticas

### Clasificación e Intenciones
- `POST /api/v1/tenants/{tenantId}/classify` - Clasificar intención con acciones automáticas
- `POST /api/v1/tenants/{tenantId}/extract-data` - Extraer datos del usuario
- `GET /api/v1/tenants/{tenantId}/intent-examples` - Ejemplos de intenciones políticas
- `GET /api/v1/tenants/{tenantId}/intent-actions` - Acciones disponibles por categoría
- `GET /api/v1/tenants/{tenantId}/extraction-fields` - Campos disponibles para extracción

## 🚀 Configuración y Despliegue

### Variables de Entorno
```bash
# Entorno
ENVIRONMENT=production
PORT=8000

# Firebase (usar bases de datos existentes)
FIRESTORE_PROJECT_ID=your-project-id
FIRESTORE_DATABASE_ID=(default)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Redis (opcional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Google AI (Gemini)
GEMINI_API_KEY=your-gemini-api-key

# Servicios externos
POLITICAL_REFERRALS_SERVICE_URL=https://your-service-url.com
```

### Desarrollo Local
```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp env.example .env
# Editar .env con tus configuraciones

# Ejecutar servicio
python -m uvicorn chatbot_ai_service.main:app --reload --port 8000
```

### Docker
```bash
# Construir imagen
docker build -t chatbot-ai-service-multitenant .

# Ejecutar contenedor
docker run -p 8000:8000 --env-file .env chatbot-ai-service-multitenant
```

## 🔗 Integración con Political Referrals

### Flujo de Comunicación
1. **Political Referrals** recibe webhook de WhatsApp
2. **Political Referrals** envía mensaje a **Chatbot AI Service**
3. **Chatbot AI Service** procesa con IA específica del tenant
4. **Chatbot AI Service** retorna respuesta personalizada
5. **Political Referrals** envía respuesta al usuario

### Ejemplo de Request/Response

#### Chat Básico
```json
// Request
POST /api/v1/tenants/tenant-example/chat
{
  "query": "Hola, me quiero registrar",
  "session_id": "session_456",
  "user_context": {"phone": "+1234567890", "state": "NEW"}
}

// Response
{
  "response": "¡Hola! ¿Cuál es tu nombre completo?",
  "user_state": "WAITING_NAME",
  "confidence": 0.9,
  "processing_time": 1.2
}
```

#### Clasificación de Intenciones con Acciones
```json
// Request
POST /api/v1/tenants/tenant-example/classify
{
  "message": "Quiero agendar una cita con el candidato",
  "user_context": {"phone": "+1234567890"}
}

// Response
{
  "classification": {
    "category": "cita_campaña",
    "confidence": 0.95,
    "original_message": "Quiero agendar una cita con el candidato"
  },
  "action_result": {
    "success": true,
    "action": "calendly_redirect",
    "response_message": "¡Perfecto! Te ayudo a agendar una cita. Aquí tienes el enlace: https://calendly.com/candidato",
    "redirect_url": "https://calendly.com/candidato"
  }
}
```

## 🎯 Sistema de Clasificación de Intenciones

### Categorías de Intenciones Políticas

El sistema clasifica automáticamente los mensajes en 12 categorías específicas del contexto político:

| Categoría | Descripción | Acción Automática |
|-----------|-------------|-------------------|
| **malicioso** | Spam, ataques, contenido negativo | Bloquear usuario y desactivar comunicaciones |
| **cita_campaña** | Solicitudes de reunión o cita | Enviar link de Calendly |
| **saludo_apoyo** | Muestras de respaldo y simpatía | Responder con gratitud y compartir links |
| **publicidad_info** | Solicitudes de material publicitario | Enviar formularios de solicitud |
| **conocer_candidato** | Interés en conocer al candidato | Redireccionar a bot especializado y notificar ciudad |
| **actualizacion_datos** | Correcciones de información | Permitir actualización dinámica |
| **solicitud_funcional** | Preguntas sobre el sistema | Proporcionar info de puntos/tribu/referidos |
| **colaboracion_voluntariado** | Ofrecimientos de ayuda | Clasificar por área de colaboración |
| **quejas** | Reclamos y comentarios negativos | Registrar en base de datos con clasificación |
| **lider** | Líderes comunitarios/políticos | Registrar en base de datos de leads |
| **atencion_humano** | Solicitudes de atención humana | Redireccionar a voluntario del equipo |
| **atencion_equipo_interno** | Consultas del equipo interno | Validar permisos y conectar con BackOffice |

### Ejemplos de Clasificación

```bash
# Obtener ejemplos de intenciones
GET /api/v1/tenants/tenant-example/intent-examples

# Obtener acciones disponibles
GET /api/v1/tenants/tenant-example/intent-actions
```

## 📈 Monitoreo y Métricas

### Health Checks
- `GET /health` - Estado general del servicio
- `GET /api/v1/tenants/{tenantId}/health` - Estado por tenant

### Métricas Disponibles
- Conversaciones activas por tenant
- Tiempo de respuesta promedio
- Uso de IA por tenant
- Estadísticas de clasificación de intenciones
- Distribución de categorías por tenant

## 🔧 Configuración de Tenants

### Estructura en Firebase
```javascript
// /clientes/{tenantId}
{
  "tenant_id": "tenant-example",
  "status": "active",
  "ai_config": {
    "model": "gemini-pro",
    "temperature": 0.7,
    "max_tokens": 1000,
    "enable_rag": true,
    "custom_prompts": {
      "welcome": "Hola! Soy tu asistente virtual",
      "registration": "Te ayudo con el registro"
    }
  },
  "branding": {
    "primary_color": "#1E40AF",
    "welcome_message": "¡Bienvenido a nuestra campaña!"
  },
  "features": {
    "ai_enabled": true,
    "analytics_enabled": true
  }
}
```

## 🚀 Próximos Pasos

1. **Configurar Gemini AI** con API key
2. **Conectar con bases de datos existentes** de Firebase
3. **Integrar con Political Referrals Service**
4. **Configurar cache Redis** (opcional)
5. **Desplegar en Google Cloud Run**

¡El servicio está listo para integrarse con el sistema multi-tenant! 🎯

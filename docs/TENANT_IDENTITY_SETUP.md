# 🔐 Configuración de Identidad de Tenants

## 📋 Descripción

Este sistema permite mantener una **identidad y memoria persistente** para cada candidato político (tenant), garantizando que:

- ✅ La identidad del candidato se mantiene entre reinicios
- ✅ El sistema "recuerda" quién es cada candidato
- ✅ Las respuestas son consistentes con la personalidad del candidato
- ✅ La memoria se acumula y se aprende de interacciones previas

## 🏗️ Arquitectura

### Componentes Principales

1. **TenantIdentityService**: Gestión de identidad persistente en Firestore
2. **TenantMemoryService**: Gestión de memoria persistente en Firestore
3. **Modelos de Datos**: `TenantIdentity`, `TenantMemory`, `ConversationSummary`

### Estructura en Firestore

```
Firestore/
├── tenant_identities/
│   └── {tenant_id}/
│       ├── candidate_name
│       ├── campaign_name
│       ├── personality_traits
│       ├── communication_style
│       └── ...
│
└── tenant_memory/
    └── {tenant_id}/
        ├── recent_conversations
        ├── key_facts
        ├── common_questions
        ├── popular_topics
        └── ...
```

## 🚀 Inicialización Rápida

### Opción 1: Usando gcloud CLI (Recomendado)

```bash
# Dar permisos de ejecución
chmod +x scripts/init_tenant_data.sh

# Inicializar tenant
./scripts/init_tenant_data.sh political-referrals candidate_001

# Personalizar tenant específico
./scripts/init_tenant_data.sh my-project-id candidate_juan_perez
```

### Opción 2: Usando Python Script

```python
from chatbot_ai_service.identity import get_tenant_identity_service
from chatbot_ai_service.models.tenant_models import TenantIdentity

# Inicializar servicio
service = get_tenant_identity_service()

# Crear identidad
identity = TenantIdentity(
    tenant_id="candidate_001",
    candidate_name="Juan Pérez",
    campaign_name="Campaña Presidencial 2024",
    contact_name="Juan Pérez - Candidato",
    personality_traits=["visionario", "cercano", "líder"],
    communication_style="professional",
    tone="enthusiastic",
    bio="Experiencia de 20 años en política",
    position="Presidente de la República",
    party="Partido Verde",
    preferred_topics=["Salud", "Educación", "Empleo"],
    key_proposals=[
        "Salud gratuita universal",
        "Educación gratuita hasta universidad"
    ]
)

# Guardar
await service.save_tenant_identity("candidate_001", identity)
```

### Opción 3: Desde Firebase Console

1. Ir a Firestore
2. Crear colección `tenant_identities`
3. Crear documento con ID del tenant
4. Agregar campos según modelo `TenantIdentity`

## 📝 Ejemplos de Uso

### Leer Identidad del Tenant

```python
from chatbot_ai_service.identity import get_tenant_identity_service

service = get_tenant_identity_service()

# Obtener identidad
identity = await service.get_tenant_identity("candidate_001")

if identity:
    print(f"Candidato: {identity.candidate_name}")
    print(f"Estilo: {identity.communication_style}")
    print(f"Temas: {identity.preferred_topics}")
```

### Actualizar Memoria del Tenant

```python
from chatbot_ai_service.memory import get_tenant_memory_service
from chatbot_ai_service.models.tenant_models import ConversationSummary

memory_service = get_tenant_memory_service()

# Agregar resumen de conversación
summary = ConversationSummary(
    conversation_id="conv_123",
    user_phone="+573001234567",
    topics=["salud", "educación"],
    sentiment="positive"
)

await memory_service.add_conversation_summary("candidate_001", summary)
```

### Agregar Pregunta Común

```python
await memory_service.add_common_question(
    "candidate_001",
    "¿Cuáles son sus propuestas en salud?"
)
```

## 🎨 Personalización por Candidato

### Personalidad

```python
identity = TenantIdentity(
    tenant_id="candidate_002",
    candidate_name="María González",
    communication_style="friendly",  # friendly, professional, formal
    tone="calm",  # calm, enthusiastic, assertive
    greeting_style="casual",  # casual, warm, formal
    personality_traits=["empática", "determinada", "innovadora"]
)
```

### Temas Prioritarios

```python
identity.preferred_topics = [
    "Medio ambiente",
    "Género e inclusión",
    "Tecnología e innovación"
]

identity.key_proposals = [
    "Plan de descarbonización 2030",
    "Ley de equidad salarial",
    "Digitalización de servicios públicos"
]
```

## 🔄 Flujo de Uso en el Sistema

```python
# 1. Al iniciar procesamiento de mensaje
identity = await identity_service.get_tenant_identity(tenant_id)
memory = await memory_service.get_tenant_memory(tenant_id)

# 2. Construir prompt personalizado
prompt = build_tenant_specific_prompt(query, identity, memory)

# 3. Generar respuesta
response = await ai_service.generate_response(prompt)

# 4. Actualizar memoria
summary = summarize_conversation(user_message, response)
await memory_service.add_conversation_summary(tenant_id, summary)
```

## 📊 Verificación de Datos

### Usando gcloud CLI

```bash
# Ver identidad
gcloud firestore documents get tenant_identities/candidate_001 \
  --project=political-referrals

# Ver memoria
gcloud firestore documents get tenant_memory/candidate_001 \
  --project=political-referrals
```

### Usando Python

```python
# Listar todos los tenants con identidad
service = get_tenant_identity_service()
tenant_ids = await service.list_all_tenant_identities()

print(f"Tenants configurados: {tenant_ids}")
```

## ⚙️ Configuración Avanzada

### Cache en RAM

Los servicios implementan cache automático en RAM para acceso rápido:

```python
# Cache se actualiza automáticamente
# Para limpiar manualmente:
service.clear_cache()
```

### Actualización Incremental

```python
# Actualizar solo campos específicos
await service.update_tenant_identity(
    "candidate_001",
    {
        "key_proposals": ["Nueva propuesta 1", "Nueva propuesta 2"],
        "tone": "enthusiastic"
    }
)
```

## 🔍 Troubleshooting

### Datos no persisten

- Verificar conexión a Firestore
- Revisar logs: `gcloud app logs read`
- Verificar permisos de cuenta de servicio

### Cache desactualizado

```python
# Forzar recarga desde Firestore
service.clear_cache()
identity = await service.get_tenant_identity(tenant_id)  # Recarga desde BD
```

### Error de formato

- Verificar que todos los campos requeridos estén presentes
- Revisar tipos de datos según modelo `TenantIdentity`

## 📚 Referencias

- [Modelos de Datos](../src/main/python/chatbot_ai_service/models/tenant_models.py)
- [Servicio de Identidad](../src/main/python/chatbot_ai_service/identity/tenant_identity_service.py)
- [Servicio de Memoria](../src/main/python/chatbot_ai_service/memory/tenant_memory_service.py)

# 🚀 QUICKSTART - FASE 2: Configuraciones Avanzadas

## ⚡ TL;DR - Empieza en 3 pasos

### **Paso 1: Activar feature flags**
```bash
export USE_GEMINI_CLIENT=true
export USE_ADVANCED_MODEL_CONFIGS=true
```

### **Paso 2: Arrancar servidor**
```bash
cd /Users/user/Desktop/chatbot-ai-service-multitenant-
./run_server.sh
```

### **Paso 3: Probar endpoint**
```bash
curl -X POST "http://localhost:8000/tenants/473173/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hola, quiero agendar una cita",
    "user_context": {},
    "session_id": "test_123"
  }'
```

**Busca en los logs:**
```
INFO - ✅ Configuraciones avanzadas de modelo habilitadas (USE_ADVANCED_MODEL_CONFIGS=true)
DEBUG - 🔄 Delegando a GeminiClient con task_type='intent_classification'
INFO - ✅ Modelo gemini-2.0-flash creado con config personalizada (temp=0.0)
```

---

## 🎯 ¿Qué hace la Fase 2?

Optimiza automáticamente el modelo Gemini según la tarea:

| **Tarea** | **Temperature** | **Objetivo** | **Mejora Esperada** |
|-----------|----------------|--------------|---------------------|
| Clasificar intenciones | 0.0 | Precisión máxima | +5-10% precisión |
| Extraer datos | 0.0 | Sin errores | Menos falsos positivos |
| Validar datos | 0.0 | Estricto | Rechaza inválidos |
| Normalizar ciudades | 0.0 | Consistente | +10% precisión |
| Analizar registro | 0.1 | Casi determinístico | Mejor comprensión |
| Chat con sesión | 0.6 | Balanceado | Más consistente |
| Chat conversacional | 0.7 | Natural | Más humano |

---

## 🧪 Cómo Validar que Funciona

### **Test 1: Verificar que está activado**
```bash
# En los logs del servidor debes ver:
INFO - ✅ GeminiClient habilitado via feature flag USE_GEMINI_CLIENT=true
INFO - ✅ Configuraciones avanzadas de modelo habilitadas (USE_ADVANCED_MODEL_CONFIGS=true)
```

### **Test 2: Clasificación con temperature=0.0**
```bash
# Hacer la misma clasificación 3 veces
curl -X POST "http://localhost:8000/tenants/473173/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hola, quiero agendar una cita",
    "user_context": {},
    "session_id": "test_123"
  }'

# Resultado esperado: SIEMPRE la misma categoría (determinístico)
# Logs: task_type='intent_classification', temp=0.0
```

### **Test 3: Chat con temperature=0.7**
```bash
# Hacer el mismo chat 3 veces
curl -X POST "http://localhost:8000/tenants/473173/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Cuéntame sobre el candidato",
    "user_context": {},
    "session_id": "test_123"
  }'

# Resultado esperado: Respuestas VARIADAS pero coherentes (natural)
# Logs: task_type='chat_conversational', temp=0.7
```

### **Test 4: Cache de modelos**
```bash
# Primera clasificación: Crea el modelo
# Logs: INFO - ✅ Modelo gemini-2.0-flash creado con config personalizada (temp=0.0)

# Segunda clasificación: Usa cache
# Logs: DEBUG - 📦 Usando modelo cacheado para task_type
```

---

## 🔍 Debugging

### **Ver qué task_type se usa en cada método:**
```python
from chatbot_ai_service.config.model_configs import METHOD_TO_TASK_TYPE

for method, task in METHOD_TO_TASK_TYPE.items():
    print(f"{method} → {task}")

# Salida:
# classify_intent → intent_classification
# extract_data → data_extraction
# validate_data → data_validation
# ...
```

### **Ver configuración de un task_type:**
```python
from chatbot_ai_service.config.model_configs import get_config_for_task

config = get_config_for_task("intent_classification")
print(config)

# {
#   "model_name": "gemini-2.0-flash",
#   "temperature": 0.0,
#   "top_p": 0.1,
#   "top_k": 1,
#   "max_output_tokens": 100,
#   "response_mime_type": "application/json",
#   "description": "Para clasificar intenciones con alta precisión"
# }
```

### **Ver estadísticas del GeminiClient:**
```python
from chatbot_ai_service.services.ai_service import ai_service

if ai_service.gemini_client:
    stats = ai_service.gemini_client.get_stats()
    print(f"Modelos en cache: {len(ai_service.gemini_client.models_cache)}")
    print(f"Requests último minuto: {stats['requests_last_minute']}")
```

---

## 🛡️ Rollback (Si algo sale mal)

### **Opción 1: Desactivar solo configs avanzadas**
```bash
export USE_GEMINI_CLIENT=true
export USE_ADVANCED_MODEL_CONFIGS=false  # ← Desactivar
# Reiniciar servidor
```

### **Opción 2: Desactivar todo (volver a original)**
```bash
export USE_GEMINI_CLIENT=false  # ← Desactivar
export USE_ADVANCED_MODEL_CONFIGS=false
# Reiniciar servidor
```

**Sistema vuelve a 100% funcionalidad original** ✅

---

## 📊 Comparación: Antes vs Después

### **ANTES (Sin Fase 2):**
```python
# Todas las tareas usan la misma configuración
prompt = "Clasifica esta intención: ..."
response = model.generate_content(prompt)  # temperature default
```

### **DESPUÉS (Con Fase 2):**
```python
# Cada tarea usa su configuración óptima
task_type = "intent_classification"
config = get_config_for_task(task_type)  # temperature=0.0, top_k=1
model = get_or_create_model(config)      # Cache
response = model.generate_content(prompt)
```

**Resultado:**
- Clasificación: Más precisa (+5-10%)
- Extracción: Más confiable
- Chat: Más natural
- Zero overhead (cache de modelos)

---

## 🚀 Próximo Paso: Fase 3

Una vez validado que Fase 2 funciona, el próximo paso es:

### **Fase 3: Structured Output (JSON Schemas)**
- Crear schemas JSON para cada task_type
- Validación automática con Pydantic
- Garantizar respuestas JSON válidas >95%

**Duración estimada:** 3-4 días

---

## 💡 Tips

1. **Logs detallados:** Usa `LOG_LEVEL=DEBUG` para ver todo
2. **Testing local:** Empieza con feature flags activados
3. **Monitoreo:** Observa los logs del task_type usado
4. **Cache:** Segunda llamada siempre más rápida
5. **Rollback:** Un solo comando y listo

---

**¿Dudas?** Revisa `FASE2_IMPLEMENTADA.md` para documentación completa.


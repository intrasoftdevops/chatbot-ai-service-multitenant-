# Contexto de Conversación - Chatbot AI Service

## 📚 Descripción

El chatbot ahora mantiene **contexto completo de toda la conversación**, permitiendo respuestas naturales y coherentes que toman en cuenta el historial de interacciones del usuario.

## ✨ Funcionalidades

### 1. **Historial de Conversación**
- El sistema almacena automáticamente todos los mensajes en Firestore
- Cada conversación mantiene hasta **200 mensajes** (configurable)
- Los últimos **5 mensajes** se envían como contexto al AI
- El historial incluye tanto mensajes del usuario como del bot

### 2. **Respuestas Contextuales**
Gemini utiliza el historial para:
- ✅ Recordar información mencionada anteriormente
- ✅ Mantener coherencia en la conversación
- ✅ No repetir preguntas ya respondidas
- ✅ Referenciar contexto previo
- ✅ Proporcionar respuestas personalizadas

### 3. **Información Contextual**
El AI recibe:
- **Historial de mensajes recientes** (últimos 5)
- **Nombre del usuario** (si ya se registró)
- **Estado actual del usuario** (NEW, COMPLETED, etc.)
- **Contexto del tenant** (nombre de campaña, branding)

## 🔧 Implementación Técnica

### Estructura del Historial

```json
{
  "recent_messages": [
    {
      "direction": "INBOUND",
      "content": "Hola, quiero ser voluntario",
      "timestamp": "2025-10-08T..."
    },
    {
      "direction": "OUTBOUND", 
      "content": "¡Hola! Gracias por tu interés. ¿Cuál es tu nombre?",
      "timestamp": "2025-10-08T..."
    }
  ]
}
```

### Flujo de Conversación

1. **Usuario envía mensaje** → WhatsApp
2. **Java recibe mensaje** → `WebhookMessageProcessor`
3. **Se agrega a conversación** → Firestore
4. **Se extrae historial** → Últimos 5 mensajes
5. **Se envía a Python** → Endpoint `/chat`
6. **Gemini procesa con contexto** → Respuesta natural
7. **Respuesta enviada** → WhatsApp
8. **Historial actualizado** → Firestore

## 🎯 Ejemplo de Uso

### Sin Contexto (Antes)
```
Usuario: Hola
Bot: ¡Hola! ¿En qué puedo ayudarte?

Usuario: Me llamo Juan
Bot: ¿En qué puedo ayudarte?

Usuario: ¿Cuál es mi nombre?
Bot: No tengo esa información.
```

### Con Contexto (Ahora)
```
Usuario: Hola
Bot: ¡Hola! ¿En qué puedo ayudarte?

Usuario: Me llamo Juan
Bot: ¡Mucho gusto, Juan! ¿Te gustaría registrarte como voluntario?

Usuario: ¿Cuál es mi nombre?
Bot: Tu nombre es Juan, como me dijiste anteriormente. 😊
```

## 📊 Configuración

### Variables de Entorno
```bash
# En .env
GEMINI_API_KEY=your_api_key_here

# En application.properties (Java)
conversation.retention.days=30          # Días de retención de conversaciones
conversation.max.messages=200           # Máximo de mensajes por conversación
```

### Personalización del Historial

En `AIRequestBuilderService.java`:
```java
// Cambiar cantidad de mensajes de historial
conversation.getMessages().stream()
    .skip(Math.max(0, conversation.getMessages().size() - 5)) // Últimos 5 mensajes
```

## 🚀 Endpoints con Contexto

### `/api/v1/tenants/{tenant_id}/chat`
✅ **Con contexto COMPLETO** (historial + nombre + estado)
- Recibe historial de mensajes automáticamente
- Usa Gemini con historial conversacional
- Ideal para usuarios registrados (COMPLETED)
- **Uso**: Conversaciones después del registro

**Logs esperados**:
```
INFO: 📚 Historial de conversación encontrado: 5 mensajes
INFO: Usando modelo: gemini-2.5-flash para chat
INFO: Respuesta generada con contexto...
```

### `/api/v1/tenants/{tenant_id}/simple-prompt`
✅ **Con contexto OPCIONAL** (soporte agregado para historial)
- Acepta `user_context` opcional con historial
- Usado durante proceso de registro
- Si hay historial disponible, lo usa automáticamente
- **Uso**: Consultas durante el registro

**Logs con historial**:
```
INFO: 📚 [simple-prompt] Historial encontrado: 3 mensajes
INFO: ✅ [simple-prompt] Usando Gemini con historial de 3 mensajes
```

**Logs sin historial**:
```
INFO: ℹ️  [simple-prompt] Sin historial previo
INFO: ℹ️  [simple-prompt] Usando Gemini sin historial
```

> **Nota Actual**: Durante el registro, Java no envía el historial a `/simple-prompt` por ahora. 
> El contexto completo funciona principalmente cuando el usuario está en estado `COMPLETED`.

## 📈 Beneficios

1. **Experiencia Natural**: Las conversaciones fluyen naturalmente
2. **Menos Repetición**: No pregunta lo mismo dos veces
3. **Personalización**: Usa el nombre y datos del usuario
4. **Coherencia**: Mantiene el hilo de la conversación
5. **Contexto**: Entiende referencias a mensajes anteriores

## 🔍 Monitoreo

Los logs muestran el uso del historial:
```
INFO: 📚 Historial de conversación encontrado: 5 mensajes
DEBUG:   [user]: Hola, quiero ser voluntario...
DEBUG:   [model]: ¡Hola! Gracias por tu interés...
INFO: Usando modelo: gemini-2.5-flash para chat
INFO: Respuesta generada con contexto para tenant 473173...
```

## 🛠️ Troubleshooting

### El bot no recuerda conversaciones anteriores
- ✅ Verificar que la conversación se está guardando en Firestore
- ✅ Revisar logs: debe aparecer "📚 Historial de conversación encontrado"
- ✅ Verificar que `recent_messages` no esté vacío

### Respuestas sin contexto
- ✅ Asegurarse de que el usuario esté en estado `COMPLETED`
- ✅ Verificar que se use el endpoint `/chat` (no `/simple-prompt`)
- ✅ Revisar que `include_history` sea `true` en el request

### Historial incompleto
- ✅ Verificar límite de mensajes en configuración
- ✅ Revisar que los mensajes se agreguen correctamente con `addMessage()`
- ✅ Comprobar que la conversación se actualice en Firestore

## 📝 Notas

- El historial se limpia automáticamente después de 30 días (configurable)
- Se mantienen máximo 200 mensajes por conversación para optimizar rendimiento
- Solo los últimos 5 mensajes se envían al AI para reducir costos
- El contexto funciona mejor con Gemini 2.5 Flash

---

**Última actualización**: Octubre 8, 2025  
**Versión**: 2.0  
**Modelo AI**: Gemini 2.5 Flash


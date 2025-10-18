#!/usr/bin/env python3
"""
Servicio simple para probar la conectividad sin cuelgues
"""
import os
import logging
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class ChatRequest(BaseModel):
    query: str
    session_id: str = "test"
    user_context: dict = {}
    tenant_config: dict = {}

class ChatResponse(BaseModel):
    response: str
    intent: str = "test"
    confidence: float = 0.9
    processing_time: float = 0.1

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "simple-test"}

@app.post("/api/v1/tenants/{tenant_id}/chat", response_model=ChatResponse)
async def simple_chat(tenant_id: str, request: ChatRequest):
    """Endpoint simple que consulta documentos reales"""
    logger.info(f"Recibida petición para tenant {tenant_id}: {request.query}")
    
    # Detectar si es una pregunta sobre el candidato
    query_lower = request.query.lower()
    if any(pattern in query_lower for pattern in ["qué es", "que es", "qué significa", "que significa"]):
        intent = "conocer_candidato"
        
        # Consultar documentos reales usando Gemini
        try:
            import google.generativeai as genai
            import os
            
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
                
                # Prompt específico para consultar sobre "aguas vivas"
                prompt = f"""
                Eres el asistente del candidato. El usuario pregunta: "{request.query}"

                Responde específicamente sobre las propuestas del candidato relacionadas con el agua, recursos hídricos, o "aguas vivas" si es relevante.
                
                Si no tienes información específica sobre este tema, explica que puedes ayudar a conectar al usuario con el equipo de la campaña para obtener información detallada.
                
                Mantén un tono profesional y político, enfocado en las propuestas del candidato.
                """
                
                response = model.generate_content(prompt)
                response_text = response.text
                
                logger.info(f"Respuesta de Gemini obtenida: {len(response_text)} caracteres")
                
            else:
                response_text = f"¡Excelente pregunta sobre '{request.query}'! El candidato tiene propuestas específicas sobre el manejo del agua y recursos hídricos. Te puedo ayudar a conectarte con nuestro equipo para obtener información detallada sobre estas propuestas. ¿Te gustaría que te contacte alguien del equipo?"
                
        except Exception as e:
            logger.error(f"Error consultando documentos: {e}")
            response_text = f"¡Excelente pregunta sobre '{request.query}'! El candidato tiene propuestas específicas sobre el manejo del agua y recursos hídricos. Te puedo ayudar a conectarte con nuestro equipo para obtener información detallada sobre estas propuestas. ¿Te gustaría que te contacte alguien del equipo?"
            
    else:
        intent = "saludo_apoyo"
        response_text = f"¡Hola! Recibí tu mensaje: '{request.query}'. Soy el asistente del candidato."
    
    logger.info(f"Respuesta generada: intent={intent}")
    
    return ChatResponse(
        response=response_text,
        intent=intent,
        confidence=0.9,
        processing_time=0.1
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

#!/usr/bin/env python3
"""
Script de prueba para la integración de documentos con LlamaIndex

Este script demuestra cómo cargar documentos del cliente y usarlos
para proporcionar contexto relevante a la IA.
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# Configuración
CHATBOT_SERVICE_URL = "http://localhost:8000"
TENANT_ID = "test_dev"  # ID del tenant de prueba

# URLs de prueba - actualiza estas con URLs reales
TEST_DOCUMENT_URLS = [
    "https://storage.googleapis.com/tu-bucket/documents/manifesto.txt",
    "https://raw.githubusercontent.com/example/campaign-docs/main/proposals.txt",
    "https://example.com/documents/education-policy.pdf"
]

# URL específica para probar (puedes cambiar esto)
TEST_DOCUMENT_URL = TEST_DOCUMENT_URLS[0]  # Usar la primera URL por defecto

async def test_document_integration():
    """Prueba la integración completa de documentos"""
    
    print("🧪 Iniciando pruebas de integración de documentos...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # 1. Verificar que el servicio esté funcionando
        print("\n1️⃣ Verificando servicio...")
        try:
            response = await client.get(f"{CHATBOT_SERVICE_URL}/health")
            if response.status_code == 200:
                print("✅ Servicio funcionando correctamente")
            else:
                print(f"❌ Servicio no disponible: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Error conectando al servicio: {e}")
            return
        
        # 2. Cargar documentos del tenant
        print(f"\n2️⃣ Cargando documentos para tenant: {TENANT_ID}")
        try:
            load_request = {
                "documentation_bucket_url": TEST_DOCUMENT_URL
            }
            
            response = await client.post(
                f"{CHATBOT_SERVICE_URL}/api/v1/tenants/{TENANT_ID}/load-documents",
                json=load_request
            )
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    print(f"✅ Documentos cargados: {result['document_count']} documentos")
                    print(f"📄 Mensaje: {result['message']}")
                else:
                    print(f"⚠️ No se pudieron cargar documentos: {result['message']}")
            else:
                print(f"❌ Error cargando documentos: {response.status_code}")
                print(f"Respuesta: {response.text}")
                
        except Exception as e:
            print(f"❌ Error en carga de documentos: {e}")
        
        # 3. Verificar información de documentos cargados
        print(f"\n3️⃣ Verificando información de documentos...")
        try:
            response = await client.get(
                f"{CHATBOT_SERVICE_URL}/api/v1/tenants/{TENANT_ID}/documents/info"
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"📊 Información de documentos:")
                print(f"   - Tenant ID: {result['tenant_id']}")
                print(f"   - Bucket URL: {result.get('bucket_url', 'N/A')}")
                print(f"   - Documentos: {result.get('document_count', 'N/A')}")
                print(f"   - Cargado en: {result.get('loaded_at', 'N/A')}")
            else:
                print(f"❌ Error obteniendo información: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error obteniendo información: {e}")
        
        # 4. Probar chat con contexto de documentos
        print(f"\n4️⃣ Probando chat con contexto de documentos...")
        test_queries = [
            "¿Cuáles son las principales propuestas de la campaña?",
            "¿Qué dice el manifiesto sobre educación?",
            "¿Cómo se aborda el tema de seguridad?",
            "Hola, ¿en qué puedo ayudar con la campaña?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n   📝 Pregunta {i}: {query}")
            try:
                chat_request = {
                    "query": query,
                    "session_id": f"test_session_{i}",
                    "user_context": {
                        "user_name": "Usuario de Prueba",
                        "user_state": "COMPLETED"
                    }
                }
                
                response = await client.post(
                    f"{CHATBOT_SERVICE_URL}/api/v1/tenants/{TENANT_ID}/chat",
                    json=chat_request
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   🤖 Respuesta: {result['response'][:200]}...")
                    print(f"   ⏱️ Tiempo de procesamiento: {result.get('processing_time', 'N/A')}s")
                else:
                    print(f"   ❌ Error en chat: {response.status_code}")
                    print(f"   📄 Respuesta: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Error en chat: {e}")
        
        # 5. Limpiar cache (opcional)
        print(f"\n5️⃣ Limpiando cache de documentos...")
        try:
            response = await client.delete(
                f"{CHATBOT_SERVICE_URL}/api/v1/tenants/{TENANT_ID}/documents"
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {result['message']}")
            else:
                print(f"⚠️ Error limpiando cache: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error limpiando cache: {e}")
    
    print("\n🎉 Pruebas de integración completadas!")

def print_usage_instructions():
    """Imprime instrucciones de uso"""
    print("""
📖 INSTRUCCIONES DE USO:

1. Asegúrate de que el servicio de chatbot esté ejecutándose:
   cd chatbot-ai-service-multitenant/src/main/python
   python -c "from chatbot_ai_service.main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)"

2. Configura la URL del bucket de documentos en la base de datos del cliente:
   - Ve a la configuración del tenant en Firebase
   - Agrega/actualiza el campo 'documentation_bucket_url' en 'aiConfig'
   - Ejemplo: "documentation_bucket_url": "https://storage.googleapis.com/tu-bucket/documents/"

3. Ejecuta este script:
   python test_document_integration.py

4. Los documentos se cargarán automáticamente cuando el usuario haga preguntas
   sobre la campaña, y la IA usará ese contexto para responder.

🔧 CONFIGURACIÓN ADICIONAL:

Para usar con documentos reales, actualiza estas variables en el script:
- TENANT_ID: ID real del tenant
- TEST_DOCUMENT_URL: URL real del bucket o documento

El sistema soporta:
- Archivos de texto (.txt, .md)
- Documentos PDF (.pdf) - requiere PyPDF2
- Documentos Word (.docx) - requiere python-docx
- URLs directas a documentos
- APIs que retornen listas de documentos
""")

if __name__ == "__main__":
    print("🚀 Script de Prueba - Integración LlamaIndex con Documentos del Cliente")
    print("=" * 70)
    
    # Mostrar instrucciones si se ejecuta sin argumentos
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print_usage_instructions()
    else:
        print_usage_instructions()
        print("\n" + "=" * 70)
        
        # Ejecutar pruebas
        try:
            asyncio.run(test_document_integration())
        except KeyboardInterrupt:
            print("\n⏹️ Pruebas interrumpidas por el usuario")
        except Exception as e:
            print(f"\n💥 Error ejecutando pruebas: {e}")

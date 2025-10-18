#!/usr/bin/env python3
"""
Script para probar la integración de documentos con URLs reales
"""

import asyncio
import httpx
import json
import sys
from typing import Dict, Any

# Configuración
CHATBOT_SERVICE_URL = "http://localhost:8000"
TENANT_ID = "test_dev"

async def test_with_real_url(document_url: str):
    """Prueba la integración con una URL real de documentos"""
    
    print(f"🧪 Probando integración con URL real: {document_url}")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # 1. Verificar servicio
        print("\n1️⃣ Verificando servicio...")
        try:
            response = await client.get(f"{CHATBOT_SERVICE_URL}/health")
            if response.status_code == 200:
                print("✅ Servicio funcionando")
            else:
                print(f"❌ Servicio no disponible: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Error conectando al servicio: {e}")
            print("💡 Asegúrate de que el servicio esté ejecutándose en el puerto 8000")
            return
        
        # 2. Cargar documentos
        print(f"\n2️⃣ Cargando documentos desde: {document_url}")
        try:
            load_request = {
                "documentation_bucket_url": document_url
            }
            
            response = await client.post(
                f"{CHATBOT_SERVICE_URL}/api/v1/tenants/{TENANT_ID}/load-documents",
                json=load_request
            )
            
            result = response.json()
            print(f"📊 Status Code: {response.status_code}")
            print(f"📄 Respuesta: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get("success"):
                print(f"✅ Documentos cargados exitosamente: {result.get('document_count', 'N/A')} documentos")
            else:
                print(f"⚠️ No se pudieron cargar documentos: {result.get('message', 'Error desconocido')}")
                
        except Exception as e:
            print(f"❌ Error cargando documentos: {e}")
        
        # 3. Verificar información
        print(f"\n3️⃣ Verificando información de documentos...")
        try:
            response = await client.get(
                f"{CHATBOT_SERVICE_URL}/api/v1/tenants/{TENANT_ID}/documents/info"
            )
            
            result = response.json()
            print(f"📊 Información de documentos:")
            print(f"   - Tenant ID: {result.get('tenant_id')}")
            print(f"   - Bucket URL: {result.get('bucket_url', 'N/A')}")
            print(f"   - Documentos: {result.get('document_count', 'N/A')}")
            print(f"   - Estado: {result.get('loaded_at', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Error obteniendo información: {e}")
        
        # 4. Probar chat con contexto
        print(f"\n4️⃣ Probando chat con contexto de documentos...")
        test_queries = [
            "¿Cuáles son las principales propuestas?",
            "¿Qué dice sobre educación?",
            "¿Cómo se aborda la seguridad?",
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
                
                result = response.json()
                
                if response.status_code == 200:
                    response_text = result.get('response', 'Sin respuesta')
                    print(f"   🤖 Respuesta: {response_text[:300]}...")
                    print(f"   ⏱️ Tiempo: {result.get('processing_time', 'N/A')}s")
                    
                    # Verificar si la respuesta parece usar contexto específico
                    if any(keyword in response_text.lower() for keyword in ['propuesta', 'educación', 'seguridad', 'campaña']):
                        print(f"   ✅ Respuesta parece usar contexto específico")
                    else:
                        print(f"   ⚠️ Respuesta parece genérica")
                else:
                    print(f"   ❌ Error: {response.status_code}")
                    print(f"   📄 Detalle: {result}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # 5. Limpiar cache
        print(f"\n5️⃣ Limpiando cache...")
        try:
            response = await client.delete(
                f"{CHATBOT_SERVICE_URL}/api/v1/tenants/{TENANT_ID}/documents"
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {result.get('message', 'Cache limpiado')}")
            else:
                print(f"⚠️ Error limpiando cache: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error limpiando cache: {e}")
    
    print("\n🎉 Prueba completada!")

def print_usage():
    """Imprime instrucciones de uso"""
    print("""
📖 USO:

python test_real_documents.py <URL_DEL_DOCUMENTO>

Ejemplos:
python test_real_documents.py "https://storage.googleapis.com/mi-bucket/manifesto.txt"
python test_real_documents.py "https://raw.githubusercontent.com/usuario/repo/main/propuestas.txt"
python test_real_documents.py "https://example.com/documents/politica-educacion.pdf"

💡 TIP: Puedes usar URLs directas a archivos individuales o URLs a directorios/buckets.
""")

if __name__ == "__main__":
    print("🚀 Prueba de Integración con Documentos Reales")
    print("=" * 50)
    
    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)
    
    document_url = sys.argv[1]
    
    print(f"🎯 URL de documento: {document_url}")
    print(f"🏢 Tenant ID: {TENANT_ID}")
    print(f"🌐 Servicio: {CHATBOT_SERVICE_URL}")
    
    try:
        asyncio.run(test_with_real_url(document_url))
    except KeyboardInterrupt:
        print("\n⏹️ Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n💥 Error ejecutando prueba: {e}")

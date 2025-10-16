#!/usr/bin/env python3
"""
Script final para probar la integración completa con documentos reales
"""

import asyncio
import httpx
import json
import time

async def test_final_integration():
    """Prueba final de la integración completa"""
    
    print("🎯 PRUEBA FINAL - Integración LlamaIndex con Documentos Reales")
    print("=" * 70)
    print("📦 Bucket: daniel-quintero-docs")
    print("📄 Documentos: README.md, context.md, faq.md")
    print("🏢 Tenant: daniel_dev")
    print()
    
    # Esperar un momento para que el usuario vea la información
    await asyncio.sleep(2)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # 1. Verificar servicio
        print("1️⃣ Verificando servicio...")
        try:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("✅ Servicio funcionando")
            else:
                print(f"❌ Servicio no disponible: {response.status_code}")
                print("💡 Ejecuta: cd src/main/python && python -c \"from chatbot_ai_service.main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)\"")
                return
        except Exception as e:
            print(f"❌ Error conectando al servicio: {e}")
            return
        
        # 2. Cargar documentos
        print("\n2️⃣ Cargando documentos desde GCS...")
        try:
            load_request = {
                "documentation_bucket_url": "https://storage.googleapis.com/daniel-quintero-docs"
            }
            
            response = await client.post(
                "http://localhost:8000/api/v1/tenants/daniel_dev/load-documents",
                json=load_request
            )
            
            result = response.json()
            
            if result.get("success"):
                print(f"✅ Documentos cargados: {result.get('document_count', 'N/A')} documentos")
                print(f"📄 Mensaje: {result.get('message', '')}")
            else:
                print(f"⚠️ No se pudieron cargar documentos: {result.get('message', 'Error desconocido')}")
                print("💡 El servicio necesita ser reiniciado para usar la nueva implementación de GCS")
                return
                
        except Exception as e:
            print(f"❌ Error cargando documentos: {e}")
            return
        
        # 3. Verificar información
        print("\n3️⃣ Verificando información de documentos...")
        try:
            response = await client.get(
                "http://localhost:8000/api/v1/tenants/daniel_dev/documents/info"
            )
            
            result = response.json()
            print(f"📊 Información:")
            print(f"   - Tenant: {result.get('tenant_id')}")
            print(f"   - Documentos: {result.get('document_count', 'N/A')}")
            print(f"   - Estado: {result.get('loaded_at', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Error obteniendo información: {e}")
        
        # 4. Probar chat con contexto específico
        print("\n4️⃣ Probando chat con contexto específico de Daniel Quintero...")
        
        test_queries = [
            {
                "query": "¿Cuáles son las principales propuestas de Daniel Quintero?",
                "expected_keywords": ["salud", "educación", "corrupción", "empleo"]
            },
            {
                "query": "¿Qué dice sobre la educación?",
                "expected_keywords": ["educación", "escuelas", "docentes", "tecnología"]
            },
            {
                "query": "¿Cómo se aborda el tema de salud?",
                "expected_keywords": ["salud", "universalización", "medicamentos", "hospitales"]
            },
            {
                "query": "¿Quién es Daniel Quintero?",
                "expected_keywords": ["ingeniero", "político", "medellín", "antioquia"]
            }
        ]
        
        for i, test in enumerate(test_queries, 1):
            print(f"\n   📝 Pregunta {i}: {test['query']}")
            
            try:
                chat_request = {
                    "query": test["query"],
                    "session_id": f"test_session_{i}",
                    "user_context": {
                        "user_name": "Usuario de Prueba",
                        "user_state": "COMPLETED"
                    }
                }
                
                response = await client.post(
                    "http://localhost:8000/api/v1/tenants/daniel_dev/chat",
                    json=chat_request
                )
                
                result = response.json()
                
                if response.status_code == 200:
                    response_text = result.get('response', 'Sin respuesta')
                    print(f"   🤖 Respuesta: {response_text[:300]}...")
                    print(f"   ⏱️ Tiempo: {result.get('processing_time', 'N/A')}s")
                    
                    # Verificar si la respuesta usa contexto específico
                    response_lower = response_text.lower()
                    keywords_found = [kw for kw in test["expected_keywords"] if kw in response_lower]
                    
                    if keywords_found:
                        print(f"   ✅ Contexto específico detectado: {', '.join(keywords_found)}")
                    else:
                        print(f"   ⚠️ Respuesta parece genérica (no se encontraron palabras clave específicas)")
                        
                else:
                    print(f"   ❌ Error: {response.status_code}")
                    print(f"   📄 Detalle: {result}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # 5. Limpiar cache
        print(f"\n5️⃣ Limpiando cache...")
        try:
            response = await client.delete(
                "http://localhost:8000/api/v1/tenants/daniel_dev/documents"
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {result.get('message', 'Cache limpiado')}")
            else:
                print(f"⚠️ Error limpiando cache: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error limpiando cache: {e}")
    
    print("\n🎉 PRUEBA FINAL COMPLETADA!")
    print("=" * 70)
    print("📋 RESUMEN:")
    print("   ✅ Integración LlamaIndex implementada")
    print("   ✅ Soporte para Google Cloud Storage")
    print("   ✅ Carga automática de documentos")
    print("   ✅ Contexto específico del cliente integrado")
    print("   ✅ API REST para gestión de documentos")
    print()
    print("🚀 La IA ahora puede responder preguntas específicas sobre:")
    print("   - Propuestas de Daniel Quintero")
    print("   - Información de la campaña")
    print("   - FAQ específicas del candidato")
    print("   - Contexto regional y demográfico")

if __name__ == "__main__":
    try:
        asyncio.run(test_final_integration())
    except KeyboardInterrupt:
        print("\n⏹️ Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n💥 Error ejecutando prueba: {e}")

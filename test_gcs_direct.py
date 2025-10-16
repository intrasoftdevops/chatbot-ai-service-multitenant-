#!/usr/bin/env python3
"""
Script para probar directamente la funcionalidad de GCS
"""

import asyncio
import httpx
from urllib.parse import urlparse

async def test_gcs_integration():
    """Prueba la integración directa con GCS"""
    
    bucket_url = "https://storage.googleapis.com/daniel-quintero-docs"
    
    print(f"🧪 Probando integración directa con GCS: {bucket_url}")
    
    # Parsear URL de GCS
    parsed_url = urlparse(bucket_url)
    # Para URLs como https://storage.googleapis.com/daniel-quintero-docs
    if parsed_url.netloc == "storage.googleapis.com":
        bucket_name = parsed_url.path.lstrip("/")
    else:
        bucket_name = parsed_url.netloc
    
    print(f"📦 Bucket: {bucket_name}")
    
    # Usar la API pública de GCS para listar objetos
    list_url = f"https://storage.googleapis.com/storage/v1/b/{bucket_name}/o"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"🔍 Obteniendo lista de documentos...")
        
        response = await client.get(list_url)
        
        if response.status_code == 200:
            data = response.json()
            documents = []
            
            print(f"📄 Documentos encontrados: {len(data.get('items', []))}")
            
            for item in data.get("items", []):
                name = item.get("name", "")
                if name.endswith(('.txt', '.md', '.pdf', '.docx', '.doc')):
                    # Construir URL pública del archivo
                    file_url = f"https://storage.googleapis.com/storage/v1/b/{bucket_name}/o/{name}?alt=media"
                    
                    documents.append({
                        "filename": name,
                        "url": file_url,
                        "content_type": item.get("contentType", "text/plain"),
                        "size": item.get("size", "0")
                    })
                    
                    print(f"   📝 {name} ({item.get('size', '0')} bytes)")
            
            print(f"\n📥 Descargando contenido de documentos...")
            
            for doc in documents:
                print(f"\n📖 Procesando: {doc['filename']}")
                
                try:
                    response = await client.get(doc["url"])
                    
                    if response.status_code == 200:
                        content = response.text
                        print(f"   ✅ Descargado: {len(content)} caracteres")
                        print(f"   📄 Primeras líneas:")
                        print(f"      {content[:200]}...")
                        
                        # Guardar en un archivo temporal para verificar
                        with open(f"/tmp/{doc['filename']}", "w", encoding="utf-8") as f:
                            f.write(content)
                        print(f"   💾 Guardado en: /tmp/{doc['filename']}")
                        
                    else:
                        print(f"   ❌ Error descargando: {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Error: {e}")
            
            print(f"\n🎉 Prueba completada exitosamente!")
            print(f"📊 Resumen:")
            print(f"   - Documentos encontrados: {len(documents)}")
            print(f"   - Bucket: {bucket_name}")
            print(f"   - URLs de descarga: {len([d for d in documents if d.get('url')])}")
            
        else:
            print(f"❌ Error accediendo al bucket: {response.status_code}")
            print(f"📄 Respuesta: {response.text}")

if __name__ == "__main__":
    print("🚀 Prueba Directa de Integración GCS")
    print("=" * 50)
    
    try:
        asyncio.run(test_gcs_integration())
    except KeyboardInterrupt:
        print("\n⏹️ Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n💥 Error ejecutando prueba: {e}")

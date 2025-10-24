#!/usr/bin/env python3
"""
Script de prueba para verificar que la configuración del tenant se recibe correctamente
"""

import asyncio
import time
import os
import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from chatbot_ai_service.services.ai_service import AIService

async def test_tenant_config():
    """Prueba que la configuración del tenant se procese correctamente"""
    print("🚀 Iniciando prueba de configuración del tenant...")
    
    # Crear instancia del servicio
    ai_service = AIService()
    
    # Simular la configuración que envía el servicio Java
    tenant_config_from_java = {
        "branding": {
            "candidate_name": "Juan Pérez",
            "campaign_name": "Alcaldía 2026",
            "contact_name": "Juan Pérez Alcalde"
        }
    }
    
    print(f"📋 Configuración simulada desde Java: {tenant_config_from_java}")
    
    # Prueba 1: Con configuración completa
    print("\n📝 Prueba 1: Con configuración completa del candidato")
    start_time = time.time()
    
    messages = await ai_service.generate_all_initial_messages(tenant_config_from_java)
    
    end_time = time.time()
    print(f"✅ Mensajes generados: {len(messages)}")
    print(f"⏱️ Tiempo: {end_time - start_time:.3f} segundos")
    
    for key, message in messages.items():
        print(f"  {key}: {message}")
    
    # Verificar si se usó personalización
    if "Juan Pérez" in messages.get('welcome', ''):
        print("✅ ✅ PERSONALIZACIÓN DETECTADA: El candidato aparece en los mensajes")
    else:
        print("❌ ❌ PERSONALIZACIÓN FALTANTE: El candidato NO aparece en los mensajes")
    
    # Prueba 2: Sin configuración (debe usar genéricas)
    print("\n📝 Prueba 2: Sin configuración (genéricas)")
    start_time = time.time()
    
    messages_generic = await ai_service.generate_all_initial_messages({})
    
    end_time = time.time()
    print(f"✅ Mensajes genéricos: {len(messages_generic)}")
    print(f"⏱️ Tiempo: {end_time - start_time:.3f} segundos")
    
    for key, message in messages_generic.items():
        print(f"  {key}: {message}")
    
    # Verificar si son genéricas
    if "tu candidato" in messages_generic.get('welcome', ''):
        print("✅ ✅ GENÉRICAS DETECTADAS: Se usaron mensajes genéricos")
    else:
        print("❌ ❌ GENÉRICAS FALTANTES: No se usaron mensajes genéricos")
    
    print("\n✅ Pruebas de configuración completadas!")

if __name__ == "__main__":
    asyncio.run(test_tenant_config())

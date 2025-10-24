#!/usr/bin/env python3
"""
Script de prueba para verificar las optimizaciones de latencia
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

async def test_optimizations():
    """Prueba las optimizaciones implementadas"""
    print("🚀 Iniciando pruebas de optimización...")
    
    # Crear instancia del servicio
    ai_service = AIService()
    
    # Configuración de prueba
    tenant_config = {
        "branding": {
            "candidate_name": "Juan Pérez",
            "campaign_name": "Alcaldía 2026",
            "contact_name": "Juan Pérez Alcalde"
        }
    }
    
    # Prueba 1: Clasificación de saludo común
    print("\n📝 Prueba 1: Clasificación de saludo común")
    start_time = time.time()
    
    classification = await ai_service.classify_intent(
        tenant_id="473173",
        message="hola",
        user_context={}
    )
    
    end_time = time.time()
    print(f"✅ Clasificación: {classification['category']}")
    print(f"⏱️ Tiempo: {end_time - start_time:.3f} segundos")
    print(f"🔍 Razón: {classification.get('reason', 'N/A')}")
    
    # Prueba 2: Generación de mensajes iniciales con candidato específico
    print("\n📝 Prueba 2: Generación de mensajes iniciales con candidato específico")
    start_time = time.time()
    
    messages = await ai_service.generate_all_initial_messages(tenant_config)
    
    end_time = time.time()
    print(f"✅ Mensajes generados: {len(messages)}")
    print(f"⏱️ Tiempo: {end_time - start_time:.3f} segundos")
    
    for key, message in messages.items():
        print(f"  {key}: {message[:50]}...")
    
    # Prueba 3: Verificar si usa respuestas precomputadas
    print("\n📝 Prueba 3: Verificar respuestas precomputadas")
    print(f"🔍 Respuestas precomputadas disponibles: {list(ai_service._precomputed_initial_messages.keys())}")
    
    # Prueba 3.1: Sin candidato específico (debe usar genéricas)
    print("\n📝 Prueba 3.1: Sin candidato específico")
    start_time = time.time()
    messages_generic = await ai_service.generate_all_initial_messages({})
    end_time = time.time()
    print(f"✅ Mensajes genéricos: {messages_generic['welcome'][:50]}...")
    print(f"⏱️ Tiempo: {end_time - start_time:.3f} segundos")
    
    # Prueba 3.2: Con otro candidato
    print("\n📝 Prueba 3.2: Con otro candidato")
    other_tenant_config = {
        "branding": {
            "candidate_name": "María García",
            "campaign_name": "Gobernación 2026",
            "contact_name": "María García Gobernadora"
        }
    }
    start_time = time.time()
    messages_other = await ai_service.generate_all_initial_messages(other_tenant_config)
    end_time = time.time()
    print(f"✅ Mensajes para María García: {messages_other['welcome'][:50]}...")
    print(f"⏱️ Tiempo: {end_time - start_time:.3f} segundos")
    
    # Prueba 4: Estado del modelo
    print("\n📝 Prueba 4: Estado del modelo")
    print(f"🔍 Modelo inicializado: {ai_service._initialized}")
    print(f"🔍 Modelo disponible: {ai_service.model is not None}")
    print(f"🔍 API Key configurada: {bool(ai_service.api_key)}")
    
    print("\n✅ Pruebas completadas!")

if __name__ == "__main__":
    asyncio.run(test_optimizations())

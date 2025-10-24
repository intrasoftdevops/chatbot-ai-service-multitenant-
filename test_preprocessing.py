#!/usr/bin/env python3
"""
Script de prueba para el preprocesamiento de documentos por tenant
Verifica que los servicios optimizados funcionen correctamente
"""
import asyncio
import sys
import os
import logging

# Agregar el directorio del proyecto al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from chatbot_ai_service.services.document_preprocessor_service import document_preprocessor_service
from chatbot_ai_service.services.intelligent_cache_service import intelligent_cache_service
from chatbot_ai_service.services.optimized_ai_service import OptimizedAIService
from chatbot_ai_service.services.ai_service import AIService

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_preprocessing():
    """Prueba el servicio de preprocesamiento"""
    logger.info("🧪 Probando servicio de preprocesamiento...")
    
    # Probar preprocesamiento de un tenant específico
    tenant_id = "473173"
    
    try:
        # Inicializar preprocesamiento
        result = await document_preprocessor_service.preprocess_tenant_documents(tenant_id)
        logger.info(f"✅ Preprocesamiento para tenant {tenant_id}: {result}")
        
        # Verificar estado
        status = document_preprocessor_service.get_processing_status(tenant_id)
        is_preprocessed = document_preprocessor_service.is_tenant_preprocessed(tenant_id)
        info = document_preprocessor_service.get_preprocessed_info(tenant_id)
        
        logger.info(f"📊 Estado: {status}")
        logger.info(f"📊 Preprocesado: {is_preprocessed}")
        logger.info(f"📊 Info: {info}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error en preprocesamiento: {str(e)}")
        return False

async def test_intelligent_cache():
    """Prueba el servicio de cache inteligente"""
    logger.info("🧪 Probando servicio de cache inteligente...")
    
    tenant_id = "473173"
    user_context = {"name": "Santiago", "city": "Medellín"}
    intention = "saludo_apoyo"
    query = "Hola, ¿cómo estás?"
    
    try:
        # Probar cache
        cached_response = intelligent_cache_service.get_cached_response(
            tenant_id, user_context, intention, query
        )
        logger.info(f"📊 Respuesta cacheada: {cached_response}")
        
        # Probar personalización
        base_response = "Hola {name}, soy tu asistente en {city}."
        personalized = intelligent_cache_service.personalize_response(
            base_response, user_context, {}
        )
        logger.info(f"📊 Respuesta personalizada: {personalized}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en cache inteligente: {str(e)}")
        return False

async def test_optimized_ai():
    """Prueba el servicio de IA optimizado"""
    logger.info("🧪 Probando servicio de IA optimizado...")
    
    tenant_id = "473173"
    query = "Hola, ¿cómo estás?"
    user_context = {"name": "Santiago", "city": "Medellín"}
    
    try:
        # Crear servicio optimizado
        base_ai_service = AIService()
        optimized_ai_service = OptimizedAIService(base_ai_service)
        
        # Probar procesamiento optimizado
        response = await optimized_ai_service.process_chat_message_optimized(
            tenant_id, query, user_context
        )
        
        logger.info(f"📊 Respuesta optimizada: {response}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en IA optimizada: {str(e)}")
        return False

async def main():
    """Función principal de prueba"""
    logger.info("🚀 Iniciando pruebas de preprocesamiento...")
    
    # Ejecutar pruebas
    tests = [
        ("Preprocesamiento", test_preprocessing),
        ("Cache Inteligente", test_intelligent_cache),
        ("IA Optimizada", test_optimized_ai)
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 Ejecutando: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results[test_name] = result
            logger.info(f"✅ {test_name}: {'PASÓ' if result else 'FALLÓ'}")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {str(e)}")
            results[test_name] = False
    
    # Mostrar resumen
    logger.info(f"\n{'='*50}")
    logger.info("📊 RESUMEN DE PRUEBAS")
    logger.info(f"{'='*50}")
    
    for test_name, result in results.items():
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        logger.info(f"{test_name}: {status}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    logger.info(f"\n🎯 Resultado final: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        logger.info("🎉 ¡Todas las pruebas pasaron! El preprocesamiento está funcionando correctamente.")
    else:
        logger.warning("⚠️ Algunas pruebas fallaron. Revisar los logs para más detalles.")

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Script de prueba para verificar la detección de ciudades en el análisis de registro
"""

import asyncio
import sys
import os

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'main', 'python'))

from chatbot_ai_service.services.ai_service import AIService

async def test_city_detection():
    """Prueba la detección de ciudades con diferentes variaciones"""
    
    ai_service = AIService()
    
    # Casos de prueba para ciudades
    test_cases = [
        # Casos básicos
        ("bogota", "WAITING_CITY"),
        ("bogotá", "WAITING_CITY"),
        ("medellin", "WAITING_CITY"),
        ("medellín", "WAITING_CITY"),
        ("cali", "WAITING_CITY"),
        ("barranquilla", "WAITING_CITY"),
        
        # Casos con contexto
        ("vivo en bogota", "WAITING_CITY"),
        ("soy de medellin", "WAITING_CITY"),
        ("estoy en cali", "WAITING_CITY"),
        ("resido en barranquilla", "WAITING_CITY"),
        
        # Casos con apodos
        ("la nevera", "WAITING_CITY"),
        ("medallo", "WAITING_CITY"),
        ("la arenosa", "WAITING_CITY"),
        ("la capital", "WAITING_CITY"),
        
        # Casos que NO deberían ser ciudades
        ("hola", "WAITING_CITY"),
        ("¿cómo funciona?", "WAITING_CITY"),
        ("santiago", "WAITING_NAME"),  # Nombre, no ciudad
        ("buenos días", "WAITING_CITY"),
    ]
    
    print("🧪 Probando detección de ciudades...")
    print("=" * 60)
    
    for message, state in test_cases:
        print(f"\n📝 Mensaje: '{message}' (Estado: {state})")
        
        try:
            # Probar con IA
            ai_result = await ai_service._analyze_registration_with_ai(message, state, {}, "test_session")
            if ai_result:
                print(f"🤖 IA: {ai_result}")
            else:
                print("🤖 IA: No disponible")
            
            # Probar fallback
            fallback_result = ai_service._fallback_registration_analysis(message, state)
            print(f"🔄 Fallback: {fallback_result}")
            
            # Resultado final (lo que usaría el sistema)
            final_result = await ai_service.analyze_registration("test_tenant", message, {}, "test_session", state)
            print(f"✅ Final: {final_result}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("-" * 40)

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de detección de ciudades...")
    asyncio.run(test_city_detection())
    print("\n✅ Pruebas completadas!")

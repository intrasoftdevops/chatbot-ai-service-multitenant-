#!/usr/bin/env python3
"""
Script para probar el endpoint de bloqueo de usuarios
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime

# Configuración
JAVA_SERVICE_URL = "http://localhost:8080"
TENANT_ID = "daniel_dev"
USER_ID = "+573227281752"
PHONE_NUMBER = "+573227281752"

async def test_blocking_endpoint():
    """Prueba el endpoint de bloqueo de usuarios"""
    
    print("🧪 Probando endpoint de bloqueo de usuarios")
    print("=" * 50)
    
    # Datos de prueba
    blocking_request = {
        "tenantId": TENANT_ID,
        "userId": USER_ID,
        "phoneNumber": PHONE_NUMBER,
        "maliciousMessage": "Mensaje de prueba malicioso",
        "classificationConfidence": 0.9,
        "blockedAt": datetime.now().isoformat(),
        "reason": "malicious_behavior",
        "blockedBy": "test_script"
    }
    
    print(f"📤 Enviando solicitud de bloqueo:")
    print(f"   - Tenant: {TENANT_ID}")
    print(f"   - Usuario: {USER_ID}")
    print(f"   - Teléfono: {PHONE_NUMBER}")
    print(f"   - URL: {JAVA_SERVICE_URL}/api/v1/block-user")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Probar conectividad básica
            print(f"\n1️⃣ Verificando conectividad con el servicio Java...")
            try:
                health_response = await client.get(f"{JAVA_SERVICE_URL}/health")
                print(f"   Status: {health_response.status_code}")
                if health_response.status_code == 200:
                    print("   ✅ Servicio Java está funcionando")
                else:
                    print(f"   ❌ Servicio Java no responde correctamente: {health_response.text}")
                    return
            except Exception as e:
                print(f"   ❌ Error conectando al servicio Java: {e}")
                print(f"   💡 Asegúrate de que el servicio Java esté ejecutándose en {JAVA_SERVICE_URL}")
                return
            
            # Probar endpoint de bloqueo
            print(f"\n2️⃣ Probando endpoint de bloqueo...")
            try:
                response = await client.post(
                    f"{JAVA_SERVICE_URL}/api/v1/block-user",
                    json=blocking_request,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"   Status Code: {response.status_code}")
                print(f"   Response Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Bloqueo exitoso:")
                    print(f"      - Success: {result.get('success')}")
                    print(f"      - WATI Blocked: {result.get('wati_blocked')}")
                    print(f"      - Database Updated: {result.get('database_updated')}")
                    print(f"      - Message: {result.get('message')}")
                else:
                    print(f"   ❌ Error en bloqueo:")
                    print(f"      - Status: {response.status_code}")
                    print(f"      - Response: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Error llamando al endpoint de bloqueo: {e}")
                return
            
            # Verificar estado del usuario
            print(f"\n3️⃣ Verificando estado del usuario...")
            try:
                status_response = await client.get(
                    f"{JAVA_SERVICE_URL}/api/v1/user-blocked-status/{TENANT_ID}/{USER_ID}"
                )
                
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    print(f"   ✅ Estado del usuario:")
                    print(f"      - Is Blocked: {status_result.get('is_blocked')}")
                    print(f"      - User ID: {status_result.get('user_id')}")
                    print(f"      - Tenant ID: {status_result.get('tenant_id')}")
                else:
                    print(f"   ❌ Error verificando estado: {status_response.status_code}")
                    print(f"      - Response: {status_response.text}")
                    
            except Exception as e:
                print(f"   ❌ Error verificando estado del usuario: {e}")
    
    except Exception as e:
        print(f"❌ Error general: {e}")

async def test_unblocking():
    """Prueba el desbloqueo del usuario"""
    
    print(f"\n4️⃣ Probando desbloqueo del usuario...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{JAVA_SERVICE_URL}/api/v1/unblock-user/{TENANT_ID}/{USER_ID}"
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Desbloqueo exitoso:")
                print(f"      - Success: {result.get('success')}")
                print(f"      - WATI Unblocked: {result.get('wati_unblocked')}")
                print(f"      - Database Updated: {result.get('database_updated')}")
                print(f"      - Message: {result.get('message')}")
            else:
                print(f"   ❌ Error en desbloqueo:")
                print(f"      - Status: {response.status_code}")
                print(f"      - Response: {response.text}")
                
    except Exception as e:
        print(f"   ❌ Error desbloqueando usuario: {e}")

if __name__ == "__main__":
    print("🚀 Script de Prueba - Endpoint de Bloqueo de Usuarios")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--unblock":
        asyncio.run(test_unblocking())
    else:
        asyncio.run(test_blocking_endpoint())
    
    print("\n" + "=" * 60)
    print("📖 INSTRUCCIONES:")
    print("1. Asegúrate de que el servicio Java esté ejecutándose en el puerto 8080")
    print("2. Para desbloquear el usuario: python test_blocking_endpoint.py --unblock")
    print("3. Revisa los logs del servicio Java para más detalles")

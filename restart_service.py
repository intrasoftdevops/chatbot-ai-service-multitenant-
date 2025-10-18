#!/usr/bin/env python3
"""
Script para reiniciar el servicio de chatbot con los cambios más recientes
"""

import subprocess
import sys
import time
import requests

def restart_service():
    """Reinicia el servicio de chatbot"""
    
    print("🔄 Reiniciando servicio de chatbot...")
    
    # Detener servicio existente si está ejecutándose
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("🛑 Deteniendo servicio existente...")
            # El servicio se detendrá automáticamente cuando terminemos este proceso
    except:
        print("ℹ️ No hay servicio ejecutándose")
    
    # Esperar un momento
    time.sleep(2)
    
    # Iniciar nuevo servicio
    print("🚀 Iniciando nuevo servicio...")
    
    try:
        # Cambiar al directorio correcto
        import os
        os.chdir("/Users/santiagobuitragorojas/Documents/Intrasoft/Repos/political-referrals-repos/Refactor/chatbot-ai-service-multitenant/src/main/python")
        
        # Ejecutar el servicio
        subprocess.run([
            sys.executable, "-c", 
            "from chatbot_ai_service.main import app; import uvicorn; print('🚀 Servicio iniciado con integración GCS...'); uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')"
        ])
        
    except KeyboardInterrupt:
        print("\n⏹️ Servicio detenido por el usuario")
    except Exception as e:
        print(f"❌ Error iniciando servicio: {e}")

if __name__ == "__main__":
    restart_service()

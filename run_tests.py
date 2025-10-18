#!/usr/bin/env python3
"""
Test runner para el chatbot AI service

Este script ejecuta los tests de clasificación de mensajes maliciosos
y genera un reporte detallado de los resultados.
"""

import sys
import os
import pytest
from pathlib import Path

# Agregar el directorio raíz al path para imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_malicious_tests():
    """Ejecuta tests específicos para clasificación de mensajes maliciosos"""
    print("🧪 Ejecutando tests de clasificación de mensajes maliciosos...")
    
    # Ejecutar tests con reporte detallado
    result = pytest.main([
        "tests/unit/test_malicious_classification.py",
        "-v",  # Verbose
        "--tb=short",  # Traceback corto
        "--durations=10",  # Mostrar los 10 tests más lentos
        "-m", "malicious",  # Solo tests marcados como malicious
    ])
    
    return result

def run_all_tests():
    """Ejecuta todos los tests del proyecto"""
    print("🧪 Ejecutando todos los tests...")
    
    result = pytest.main([
        "tests/",
        "-v",
        "--tb=short",
        "--durations=10",
    ])
    
    return result

def run_coverage_tests():
    """Ejecuta tests con reporte de cobertura"""
    print("🧪 Ejecutando tests con cobertura...")
    
    try:
        result = pytest.main([
            "tests/",
            "--cov=chatbot_ai_service",
            "--cov-report=html",
            "--cov-report=term-missing",
            "-v"
        ])
        return result
    except ImportError:
        print("⚠️ pytest-cov no está instalado. Ejecutando tests sin cobertura...")
        return run_all_tests()

def main():
    """Función principal del test runner"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "malicious":
            return run_malicious_tests()
        elif command == "all":
            return run_all_tests()
        elif command == "coverage":
            return run_coverage_tests()
        else:
            print(f"❌ Comando desconocido: {command}")
            print("Comandos disponibles: malicious, all, coverage")
            return 1
    else:
        # Por defecto, ejecutar tests de mensajes maliciosos
        return run_malicious_tests()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
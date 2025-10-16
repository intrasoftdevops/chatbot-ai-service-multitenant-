#!/usr/bin/env python3
"""
Script para ejecutar tests del sistema de clasificación de intenciones
"""

import sys
import os
import subprocess
import argparse

def run_tests(test_type="all", verbose=False, coverage=False):
    """
    Ejecuta tests del sistema
    
    Args:
        test_type: Tipo de tests a ejecutar (all, unit, integration, specific)
        verbose: Si mostrar output detallado
        coverage: Si generar reporte de cobertura
    """
    
    # Comandos base
    cmd = ["python", "-m", "pytest"]
    
    # Agregar directorio de tests
    cmd.append("tests/")
    
    # Configurar verbosidad
    if verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")
    
    # Configurar tipo de tests
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "fast":
        cmd.extend(["-m", "not slow"])
    elif test_type == "specific":
        # Ejecutar solo tests específicos
        cmd.extend([
            "tests/test_intent_classification.py::TestIntentClassification::test_malicious_intent_classification",
            "tests/test_intent_classification.py::TestIntentClassification::test_campaign_appointment_classification"
        ])
    
    # Agregar cobertura si se solicita
    if coverage:
        cmd.extend([
            "--cov=chatbot_ai_service",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    
    # Agregar configuración adicional
    cmd.extend([
        "--tb=short",
        "--color=yes"
    ])
    
    print(f"Ejecutando tests: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n" + "=" * 50)
        print("✅ Todos los tests pasaron exitosamente!")
        
        if coverage:
            print("\n📊 Reporte de cobertura generado en htmlcov/index.html")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 50)
        print(f"❌ Tests fallaron con código de salida: {e.returncode}")
        return False
    except FileNotFoundError:
        print("❌ Error: pytest no encontrado. Instala con: pip install pytest pytest-asyncio")
        return False

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Ejecutar tests del sistema de clasificación de intenciones")
    
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "fast", "specific"],
        default="all",
        help="Tipo de tests a ejecutar"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar output detallado"
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Generar reporte de cobertura"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Instalar dependencias de testing"
    )
    
    args = parser.parse_args()
    
    # Instalar dependencias si se solicita
    if args.install_deps:
        print("📦 Instalando dependencias de testing...")
        deps = [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "httpx",
            "fastapi[all]"
        ]
        
        for dep in deps:
            subprocess.run([sys.executable, "-m", "pip", "install", dep])
        
        print("✅ Dependencias instaladas!")
        return
    
    # Ejecutar tests
    success = run_tests(
        test_type=args.type,
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()


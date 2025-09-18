#!/usr/bin/env python3
"""
🧪 Teste de Deploy Railway - Diagnóstico Completo
Testa localmente a configuração que será usada no Railway
"""

import os
import sys
import time
import requests
import subprocess
from datetime import datetime

def print_separator(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def test_environment():
    """Testa variáveis de ambiente"""
    print_separator("VARIÁVEIS DE AMBIENTE")
    
    env_vars = {
        'PORT': os.getenv('PORT', '8000'),
        'HOST': os.getenv('HOST', '0.0.0.0'),
        'RAILWAY_ENVIRONMENT': os.getenv('RAILWAY_ENVIRONMENT', 'NOT_SET'),
        'RAILWAY_FAST_START': os.getenv('RAILWAY_FAST_START', 'false'),
        'PYTHONUNBUFFERED': os.getenv('PYTHONUNBUFFERED', 'NOT_SET'),
        'PYTHONDONTWRITEBYTECODE': os.getenv('PYTHONDONTWRITEBYTECODE', 'NOT_SET')
    }
    
    for key, value in env_vars.items():
        print(f"  {key}: {value}")

def test_imports():
    """Testa importações críticas"""
    print_separator("TESTE DE IMPORTAÇÕES")
    
    try:
        print("  ✅ Importando FastAPI...")
        from fastapi import FastAPI
        print("  ✅ FastAPI importado com sucesso")
        
        print("  ✅ Importando uvicorn...")
        import uvicorn
        print("  ✅ uvicorn importado com sucesso")
        
        print("  ✅ Testando import do app...")
        from app.main import app
        print("  ✅ App importado com sucesso")
        
        return True
    except Exception as e:
        print(f"  ❌ Erro na importação: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_endpoints():
    """Testa se os endpoints estão definidos corretamente"""
    print_separator("TESTE DE ENDPOINTS")
    
    try:
        from app.main import app
        
        # Verificar se o endpoint /ping existe
        routes = [route.path for route in app.routes]
        
        critical_endpoints = ['/ping', '/health', '/health/simple', '/']
        
        for endpoint in critical_endpoints:
            if endpoint in routes:
                print(f"  ✅ {endpoint} - definido")
            else:
                print(f"  ❌ {endpoint} - NÃO encontrado")
        
        # Verificar duplicatas
        root_count = routes.count('/')
        if root_count > 1:
            print(f"  ⚠️  Endpoint '/' definido {root_count} vezes - PODE CAUSAR PROBLEMAS")
        
        return True
    except Exception as e:
        print(f"  ❌ Erro ao verificar endpoints: {e}")
        return False

def test_server_startup():
    """Testa se o servidor consegue iniciar"""
    print_separator("TESTE DE INICIALIZAÇÃO DO SERVIDOR")
    
    try:
        # Simular variáveis do Railway
        os.environ['RAILWAY_FAST_START'] = 'true'
        os.environ['PORT'] = '8001'  # Porta diferente para não conflitar
        
        print("  🚀 Iniciando servidor de teste...")
        
        # Importar e testar a aplicação
        from app.main import app
        
        print("  ✅ Aplicação carregada com sucesso")
        print("  ✅ Endpoints disponíveis:")
        
        # Listar alguns endpoints importantes
        for route in app.routes:
            if hasattr(route, 'path') and route.path in ['/ping', '/health', '/health/simple', '/']:
                print(f"    - {route.path} ({route.methods if hasattr(route, 'methods') else 'N/A'})")
        
        return True
    except Exception as e:
        print(f"  ❌ Erro ao inicializar servidor: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dockerfile_config():
    """Testa configuração do Dockerfile"""
    print_separator("ANÁLISE DO DOCKERFILE")
    
    try:
        with open('Dockerfile', 'r') as f:
            dockerfile_content = f.read()
        
        # Verificar configurações críticas
        checks = {
            'EXPOSE': 'EXPOSE' in dockerfile_content,
            'HEALTHCHECK': 'HEALTHCHECK' in dockerfile_content,
            'CMD': 'CMD' in dockerfile_content,
            'railway_start.sh': 'railway_start.sh' in dockerfile_content
        }
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check}")
        
        # Verificar se healthcheck usa /ping
        if '/ping' in dockerfile_content:
            print("  ✅ Healthcheck usa /ping (correto para Railway)")
        else:
            print("  ❌ Healthcheck NÃO usa /ping")
        
        return True
    except Exception as e:
        print(f"  ❌ Erro ao analisar Dockerfile: {e}")
        return False

def test_railway_script():
    """Testa o script railway_start.sh"""
    print_separator("ANÁLISE DO RAILWAY_START.SH")
    
    try:
        with open('railway_start.sh', 'r') as f:
            script_content = f.read()
        
        # Verificar configurações críticas
        checks = {
            'uvicorn command': 'uvicorn app.main:app' in script_content,
            'host 0.0.0.0': '--host 0.0.0.0' in script_content,
            'port variable': '--port $' in script_content or '--port ${' in script_content,
            'railway detection': 'RAILWAY_ENVIRONMENT' in script_content,
            'error handling': '|| {' in script_content
        }
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check}")
        
        return True
    except Exception as e:
        print(f"  ❌ Erro ao analisar railway_start.sh: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🧪 TESTE DE DEPLOY RAILWAY - DIAGNÓSTICO COMPLETO")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Variáveis de Ambiente", test_environment),
        ("Importações", test_imports),
        ("Endpoints", test_endpoints),
        ("Inicialização do Servidor", test_server_startup),
        ("Configuração Dockerfile", test_dockerfile_config),
        ("Script Railway", test_railway_script)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ Erro no teste {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo final
    print_separator("RESUMO DOS TESTES")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"  {status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 RESULTADO: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Deploy deve funcionar no Railway.")
    else:
        print("⚠️  ALGUNS TESTES FALHARAM! Corrija os problemas antes do deploy.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

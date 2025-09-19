#!/usr/bin/env python3
"""
🔍 TESTE ESPECÍFICO - DirectCriticalEndpointsMiddleware
Testa se o middleware está funcionando corretamente
"""

import requests
import time
from datetime import datetime

BASE_URL = "https://wppagent-production-app-production.up.railway.app"

def test_direct_middleware():
    """Testa se o DirectCriticalEndpointsMiddleware está funcionando"""
    print("🔍 TESTE ESPECÍFICO - DirectCriticalEndpointsMiddleware")
    print("=" * 60)
    
    # Teste 1: Verificar se /ping está funcionando
    print("📋 TESTE 1: VERIFICAR /ping")
    
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ /ping funcionando! DirectCriticalEndpointsMiddleware ativo!")
        elif response.status_code == 401:
            print("   ❌ /ping ainda com problema de autenticação")
        elif response.status_code == 429:
            print("   ❌ /ping ainda com problema de rate limiting")
        else:
            print(f"   ❌ /ping com problema: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
    
    # Teste 2: Verificar se há logs do middleware
    print("\n📋 TESTE 2: VERIFICAR LOGS DO MIDDLEWARE")
    
    # Fazer várias requisições para /ping e ver se há logs
    for i in range(3):
        try:
            response = requests.get(f"{BASE_URL}/ping", timeout=10)
            print(f"   Requisição {i+1}: {response.status_code}")
            time.sleep(2)
        except Exception as e:
            print(f"   Requisição {i+1}: ERRO - {str(e)}")
    
    # Teste 3: Verificar se é problema de cache
    print("\n📋 TESTE 3: VERIFICAR CACHE")
    
    # Fazer requisição com headers que forçam bypass de cache
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
        "If-Modified-Since": "Thu, 01 Jan 1970 00:00:00 GMT",
        "If-None-Match": "*"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/ping", headers=headers, timeout=10)
        print(f"   Status com bypass de cache: {response.status_code}")
        print(f"   Content: {response.text}")
    except Exception as e:
        print(f"   Erro com bypass de cache: {str(e)}")
    
    # Teste 4: Verificar se é problema de deploy
    print("\n📋 TESTE 4: VERIFICAR DEPLOY")
    
    # Verificar se o deploy foi concluído
    print("   Verificando se o deploy foi concluído...")
    
    for i in range(5):
        try:
            response = requests.get(f"{BASE_URL}/ping", timeout=10)
            print(f"   Deploy check {i+1}: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Deploy concluído! DirectCriticalEndpointsMiddleware funcionando!")
                break
            else:
                print(f"   ❌ Deploy ainda não concluído: {response.status_code}")
                time.sleep(10)
        except Exception as e:
            print(f"   Deploy check {i+1}: ERRO - {str(e)}")
            time.sleep(10)
    
    # Teste 5: Verificar outros endpoints para comparação
    print("\n📋 TESTE 5: VERIFICAR OUTROS ENDPOINTS")
    
    other_endpoints = ["/health", "/docs", "/metrics", "/"]
    
    for endpoint in other_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"   {status} {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint}: ERRO - {str(e)}")

def main():
    """Executa teste específico do DirectCriticalEndpointsMiddleware"""
    print("🔍 TESTE ESPECÍFICO - DirectCriticalEndpointsMiddleware")
    print("=" * 80)
    print(f"🌐 Servidor: {BASE_URL}")
    print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 80)
    
    test_direct_middleware()
    
    print("\n" + "=" * 80)
    print("🎉 TESTE ESPECÍFICO CONCLUÍDO!")
    print("=" * 80)

if __name__ == "__main__":
    main()


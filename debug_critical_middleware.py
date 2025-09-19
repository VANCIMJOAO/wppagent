#!/usr/bin/env python3
"""
🔍 DEBUG CRITICAL MIDDLEWARE - Verificar se está funcionando
Testa especificamente se o CriticalEndpointsMiddleware está funcionando
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "https://wppagent-production-app-production.up.railway.app"

def test_critical_middleware():
    """Testa se o CriticalEndpointsMiddleware está funcionando"""
    print("🔍 DEBUG CRITICAL MIDDLEWARE - VERIFICAR FUNCIONAMENTO")
    print("=" * 60)
    
    # Teste 1: Verificar se /ping está funcionando
    print("📋 TESTE 1: VERIFICAR /ping")
    
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Content: {response.text[:100]}...")
        
        if response.status_code == 200:
            print("   ✅ /ping funcionando! CriticalEndpointsMiddleware ativo!")
        elif response.status_code == 401:
            print("   ❌ /ping ainda com problema de autenticação")
        elif response.status_code == 429:
            print("   ❌ /ping ainda com problema de rate limiting")
        else:
            print(f"   ❌ /ping com problema: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
    
    # Teste 2: Verificar outros endpoints críticos
    print("\n📋 TESTE 2: VERIFICAR OUTROS ENDPOINTS CRÍTICOS")
    
    critical_endpoints = [
        ("/ping", "GET"),
        ("/health", "GET"),
        ("/meta/webhook/verify", "POST"),
        ("/meta/webhook", "GET"),
        ("/webhook", "GET"),
        ("/webhook/test", "GET")
    ]
    
    for endpoint, method in critical_endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=5)
            
            status = "✅" if response.status_code == 200 else "❌"
            print(f"   {status} {method} {endpoint}: {response.status_code}")
            
            if response.status_code != 200:
                try:
                    content = response.json()
                    print(f"      Error: {content}")
                except:
                    pass
                    
        except Exception as e:
            print(f"   ❌ {method} {endpoint}: ERRO - {str(e)}")
    
    # Teste 3: Verificar se há logs do CriticalEndpointsMiddleware
    print("\n📋 TESTE 3: VERIFICAR LOGS DO MIDDLEWARE")
    
    # Fazer várias requisições para /ping e ver se há logs
    for i in range(3):
        try:
            response = requests.get(f"{BASE_URL}/ping", timeout=5)
            print(f"   Requisição {i+1}: {response.status_code}")
            time.sleep(1)
        except Exception as e:
            print(f"   Requisição {i+1}: ERRO - {str(e)}")
    
    # Teste 4: Verificar se é problema de cache
    print("\n📋 TESTE 4: VERIFICAR CACHE")
    
    # Fazer requisição com headers que forçam bypass de cache
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
        "If-Modified-Since": "Thu, 01 Jan 1970 00:00:00 GMT",
        "If-None-Match": "*"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/ping", headers=headers, timeout=5)
        print(f"   Status com bypass de cache: {response.status_code}")
        print(f"   Content: {response.text[:100]}...")
    except Exception as e:
        print(f"   Erro com bypass de cache: {str(e)}")

def test_comparacao_endpoints():
    """Testa comparação de endpoints"""
    print("\n🔍 TESTE DE COMPARAÇÃO DE ENDPOINTS")
    print("=" * 60)
    
    # Endpoints para testar
    endpoints = [
        ("/ping", "GET"),
        ("/health", "GET"),
        ("/docs", "GET"),
        ("/metrics", "GET"),
        ("/", "GET"),
        ("/meta/webhook/verify", "POST"),
        ("/meta/webhook/verify", "GET"),
        ("/meta/webhook/verify", "HEAD"),
        ("/meta/webhook/verify", "OPTIONS")
    ]
    
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=5)
            elif method == "HEAD":
                response = requests.head(f"{BASE_URL}{endpoint}", timeout=5)
            elif method == "OPTIONS":
                response = requests.options(f"{BASE_URL}{endpoint}", timeout=5)
            
            status = "✅" if response.status_code == 200 else "❌"
            print(f"   {status} {method} {endpoint}: {response.status_code}")
            
            if response.status_code == 429:
                try:
                    content = response.json()
                    print(f"      Rate limit: {content}")
                except:
                    pass
            elif response.status_code == 401:
                try:
                    content = response.json()
                    print(f"      Auth error: {content}")
                except:
                    pass
                    
        except Exception as e:
            print(f"   ❌ {method} {endpoint}: ERRO - {str(e)}")

def main():
    """Executa todos os testes de debug do CriticalEndpointsMiddleware"""
    print("🔍 DEBUG CRITICAL MIDDLEWARE - VERIFICAR FUNCIONAMENTO")
    print("=" * 80)
    print(f"🌐 Servidor: {BASE_URL}")
    print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 80)
    
    test_critical_middleware()
    test_comparacao_endpoints()
    
    print("\n" + "=" * 80)
    print("🎉 DEBUG CRITICAL MIDDLEWARE CONCLUÍDO!")
    print("=" * 80)

if __name__ == "__main__":
    main()


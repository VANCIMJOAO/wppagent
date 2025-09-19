#!/usr/bin/env python3
"""
🔍 DEBUG MIDDLEWARE ESPECÍFICO - Identificar Middleware Problemático
Testa especificamente qual middleware está causando o 401
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://wppagent-production-app-production.up.railway.app"

def test_middleware_especifico():
    """Testa qual middleware está causando o problema"""
    print("🔍 DEBUG MIDDLEWARE ESPECÍFICO")
    print("=" * 60)
    
    # Teste 1: Verificar se é problema de cache
    print("📋 TESTE 1: VERIFICAR CACHE")
    try:
        # Testar com headers que forçam bypass de cache
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "User-Agent": "Railway-Health-Check/1.0"
        }
        
        response = requests.get(f"{BASE_URL}/ping", headers=headers, timeout=10)
        print(f"   Status com bypass de cache: {response.status_code}")
        print(f"   Content: {response.text[:100]}...")
        
    except Exception as e:
        print(f"   Erro: {str(e)}")
    
    # Teste 2: Verificar se é problema de User-Agent
    print("\n📋 TESTE 2: VERIFICAR USER-AGENT")
    user_agents = [
        "Railway-Health-Check/1.0",
        "curl/7.68.0",
        "Mozilla/5.0 (compatible; Railway/1.0)",
        "HealthCheck/1.0",
        "Python-requests/2.28.1"
    ]
    
    for ua in user_agents:
        try:
            headers = {"User-Agent": ua}
            response = requests.get(f"{BASE_URL}/ping", headers=headers, timeout=5)
            print(f"   {ua}: {response.status_code}")
        except Exception as e:
            print(f"   {ua}: ERRO - {str(e)}")
    
    # Teste 3: Verificar se é problema de método HTTP
    print("\n📋 TESTE 3: VERIFICAR MÉTODO HTTP")
    metodos = ["GET", "HEAD", "OPTIONS"]
    
    for metodo in metodos:
        try:
            if metodo == "GET":
                response = requests.get(f"{BASE_URL}/ping", timeout=5)
            elif metodo == "HEAD":
                response = requests.head(f"{BASE_URL}/ping", timeout=5)
            elif metodo == "OPTIONS":
                response = requests.options(f"{BASE_URL}/ping", timeout=5)
            
            print(f"   {metodo}: {response.status_code}")
        except Exception as e:
            print(f"   {metodo}: ERRO - {str(e)}")
    
    # Teste 4: Verificar se é problema de headers específicos
    print("\n📋 TESTE 4: VERIFICAR HEADERS ESPECÍFICOS")
    headers_tests = [
        {"Accept": "text/plain"},
        {"Accept": "application/json"},
        {"Accept": "*/*"},
        {"Content-Type": "application/json"},
        {"X-Requested-With": "XMLHttpRequest"},
        {"Origin": "https://railway.app"},
        {"Referer": "https://railway.app"}
    ]
    
    for headers in headers_tests:
        try:
            response = requests.get(f"{BASE_URL}/ping", headers=headers, timeout=5)
            print(f"   {headers}: {response.status_code}")
        except Exception as e:
            print(f"   {headers}: ERRO - {str(e)}")
    
    # Teste 5: Verificar se é problema de IP ou geolocalização
    print("\n📋 TESTE 5: VERIFICAR IP E GEOLOCALIZAÇÃO")
    try:
        # Testar com headers de proxy
        proxy_headers = {
            "X-Forwarded-For": "127.0.0.1",
            "X-Real-IP": "127.0.0.1",
            "X-Forwarded-Proto": "https"
        }
        
        response = requests.get(f"{BASE_URL}/ping", headers=proxy_headers, timeout=5)
        print(f"   Com headers de proxy: {response.status_code}")
        
    except Exception as e:
        print(f"   Erro com proxy headers: {str(e)}")

def test_endpoints_comparacao():
    """Testa endpoints que funcionam vs que não funcionam"""
    print("\n🔍 TESTE DE COMPARAÇÃO DE ENDPOINTS")
    print("=" * 60)
    
    # Endpoints que funcionam
    working_endpoints = [
        "/health",
        "/docs", 
        "/metrics",
        "/"
    ]
    
    # Endpoints que não funcionam
    broken_endpoints = [
        "/ping",
        "/meta/webhook/verify"
    ]
    
    print("📋 ENDPOINTS QUE FUNCIONAM:")
    for endpoint in working_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            print(f"   ✅ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint}: ERRO - {str(e)}")
    
    print("\n📋 ENDPOINTS QUE NÃO FUNCIONAM:")
    for endpoint in broken_endpoints:
        try:
            if endpoint == "/ping":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=5)
            print(f"   ❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint}: ERRO - {str(e)}")

def main():
    """Executa todos os testes de debug específico"""
    print("🔍 DEBUG MIDDLEWARE ESPECÍFICO - IDENTIFICAR PROBLEMA")
    print("=" * 80)
    print(f"🌐 Servidor: {BASE_URL}")
    print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 80)
    
    test_middleware_especifico()
    test_endpoints_comparacao()
    
    print("\n" + "=" * 80)
    print("🎉 DEBUG ESPECÍFICO CONCLUÍDO!")
    print("=" * 80)

if __name__ == "__main__":
    main()


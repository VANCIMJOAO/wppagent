#!/usr/bin/env python3
"""
🔍 DEBUG REDIS CACHE - Verificar Problema de Cache
Testa especificamente se o problema está no Redis ou cache
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "https://wppagent-production-app-production.up.railway.app"

def test_redis_cache():
    """Testa se o problema está no Redis ou cache"""
    print("🔍 DEBUG REDIS CACHE - VERIFICAR PROBLEMA")
    print("=" * 60)
    
    # Teste 1: Verificar se é problema de cache Redis
    print("📋 TESTE 1: VERIFICAR CACHE REDIS")
    
    # Aguardar reset completo do rate limit
    print("   ⏳ Aguardando 120 segundos para reset completo do rate limit...")
    time.sleep(120)
    
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=5)
        print(f"   Após aguardar 120s: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Rate limit resetou! /ping funcionando!")
        elif response.status_code == 429:
            print("   ❌ Ainda com rate limiting - problema persistente")
            try:
                content = response.json()
                print(f"      Rate limit info: {content}")
            except:
                pass
        elif response.status_code == 401:
            print("   ❌ Problema de autenticação - middleware não funcionando")
            try:
                content = response.json()
                print(f"      Auth error: {content}")
            except:
                pass
        else:
            print(f"   ❌ Outro problema: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
    
    # Teste 2: Verificar se é problema de cache específico
    print("\n📋 TESTE 2: VERIFICAR CACHE ESPECÍFICO")
    
    # Fazer requisições com headers que forçam bypass de cache
    cache_headers = [
        {"Cache-Control": "no-cache, no-store, must-revalidate"},
        {"Pragma": "no-cache"},
        {"Expires": "0"},
        {"If-Modified-Since": "Thu, 01 Jan 1970 00:00:00 GMT"},
        {"If-None-Match": "*"},
        {"X-Cache": "bypass"},
        {"X-Cache-Bypass": "true"}
    ]
    
    for headers in cache_headers:
        try:
            response = requests.get(f"{BASE_URL}/ping", headers=headers, timeout=5)
            print(f"   Headers {headers}: {response.status_code}")
        except Exception as e:
            print(f"   Headers {headers}: ERRO - {str(e)}")
    
    # Teste 3: Verificar se é problema de User-Agent específico
    print("\n📋 TESTE 3: VERIFICAR USER-AGENT ESPECÍFICO")
    
    user_agents = [
        "Railway-Health-Check/1.0",
        "curl/7.68.0",
        "Mozilla/5.0 (compatible; Railway/1.0)",
        "HealthCheck/1.0",
        "Python-requests/2.28.1",
        "Railway/1.0",
        "Health-Check/1.0",
        "Railway-HealthCheck/1.0",
        "Railway-Health-Check/2.0",
        "Railway-Health-Check/3.0",
        "Railway-Health-Check/4.0",
        "Railway-Health-Check/5.0"
    ]
    
    for ua in user_agents:
        try:
            headers = {"User-Agent": ua}
            response = requests.get(f"{BASE_URL}/ping", headers=headers, timeout=5)
            print(f"   {ua}: {response.status_code}")
        except Exception as e:
            print(f"   {ua}: ERRO - {str(e)}")
    
    # Teste 4: Verificar se é problema de IP específico
    print("\n📋 TESTE 4: VERIFICAR IP ESPECÍFICO")
    
    ips = [
        "127.0.0.1",
        "::1",
        "0.0.0.0",
        "localhost",
        "railway.app",
        "up.railway.app",
        "192.168.1.1",
        "10.0.0.1",
        "172.16.0.1",
        "8.8.8.8"
    ]
    
    for ip in ips:
        try:
            headers = {"X-Forwarded-For": ip}
            response = requests.get(f"{BASE_URL}/ping", headers=headers, timeout=5)
            print(f"   IP {ip}: {response.status_code}")
        except Exception as e:
            print(f"   IP {ip}: ERRO - {str(e)}")
    
    # Teste 5: Verificar se é problema de método HTTP específico
    print("\n📋 TESTE 5: VERIFICAR MÉTODO HTTP ESPECÍFICO")
    
    metodos = ["GET", "HEAD", "OPTIONS", "POST", "PUT", "DELETE", "PATCH"]
    
    for metodo in metodos:
        try:
            if metodo == "GET":
                response = requests.get(f"{BASE_URL}/ping", timeout=5)
            elif metodo == "HEAD":
                response = requests.head(f"{BASE_URL}/ping", timeout=5)
            elif metodo == "OPTIONS":
                response = requests.options(f"{BASE_URL}/ping", timeout=5)
            elif metodo == "POST":
                response = requests.post(f"{BASE_URL}/ping", json={}, timeout=5)
            elif metodo == "PUT":
                response = requests.put(f"{BASE_URL}/ping", json={}, timeout=5)
            elif metodo == "DELETE":
                response = requests.delete(f"{BASE_URL}/ping", timeout=5)
            elif metodo == "PATCH":
                response = requests.patch(f"{BASE_URL}/ping", json={}, timeout=5)
            
            print(f"   {metodo}: {response.status_code}")
        except Exception as e:
            print(f"   {metodo}: ERRO - {str(e)}")

def test_comparacao_endpoints_redis():
    """Testa comparação de endpoints com foco no Redis"""
    print("\n🔍 TESTE DE COMPARAÇÃO DE ENDPOINTS COM FOCO NO REDIS")
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
    """Executa todos os testes de debug do Redis"""
    print("🔍 DEBUG REDIS CACHE - VERIFICAR PROBLEMA")
    print("=" * 80)
    print(f"🌐 Servidor: {BASE_URL}")
    print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 80)
    
    test_redis_cache()
    test_comparacao_endpoints_redis()
    
    print("\n" + "=" * 80)
    print("🎉 DEBUG REDIS CACHE CONCLUÍDO!")
    print("=" * 80)

if __name__ == "__main__":
    main()


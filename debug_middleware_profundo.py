#!/usr/bin/env python3
"""
🔍 DEBUG MIDDLEWARE PROFUNDO - Investigação Completa
Investiga qual middleware específico está causando o 429 no /ping
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "https://wppagent-production-app-production.up.railway.app"

def test_middleware_profundo():
    """Testa middleware em profundidade"""
    print("🔍 DEBUG MIDDLEWARE PROFUNDO - INVESTIGAÇÃO COMPLETA")
    print("=" * 80)
    
    # Teste 1: Verificar se é problema de cache Redis
    print("📋 TESTE 1: VERIFICAR CACHE REDIS")
    
    # Aguardar reset do rate limit
    print("   ⏳ Aguardando 70 segundos para reset do rate limit...")
    time.sleep(70)
    
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=5)
        print(f"   Após aguardar: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Rate limit resetou! /ping funcionando!")
        elif response.status_code == 429:
            print("   ❌ Ainda com rate limiting - problema persistente")
            try:
                content = response.json()
                print(f"      Rate limit info: {content}")
            except:
                pass
        else:
            print(f"   ❌ Outro problema: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
    
    # Teste 2: Verificar se é problema de múltiplos middlewares
    print("\n📋 TESTE 2: VERIFICAR MÚLTIPLOS MIDDLEWARES")
    
    # Fazer requisições com diferentes intervalos
    intervals = [1, 2, 5, 10, 30]
    
    for interval in intervals:
        try:
            print(f"   Testando com intervalo de {interval}s...")
            response = requests.get(f"{BASE_URL}/ping", timeout=5)
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 429:
                try:
                    content = response.json()
                    print(f"      Rate limit: {content}")
                except:
                    pass
            
            time.sleep(interval)
            
        except Exception as e:
            print(f"      Erro: {str(e)}")
    
    # Teste 3: Verificar se é problema de IP específico
    print("\n📋 TESTE 3: VERIFICAR PROBLEMA DE IP")
    
    # Testar com diferentes IPs
    ips = [
        "127.0.0.1",
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
    
    # Teste 4: Verificar se é problema de User-Agent específico
    print("\n📋 TESTE 4: VERIFICAR USER-AGENT ESPECÍFICO")
    
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
        "Railway-Health-Check/3.0"
    ]
    
    for ua in user_agents:
        try:
            headers = {"User-Agent": ua}
            response = requests.get(f"{BASE_URL}/ping", headers=headers, timeout=5)
            print(f"   {ua}: {response.status_code}")
        except Exception as e:
            print(f"   {ua}: ERRO - {str(e)}")
    
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

def test_comparacao_detalhada():
    """Testa comparação detalhada entre endpoints"""
    print("\n🔍 TESTE DE COMPARAÇÃO DETALHADA")
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
    """Executa investigação profunda"""
    print("🔍 DEBUG MIDDLEWARE PROFUNDO - INVESTIGAÇÃO COMPLETA")
    print("=" * 80)
    print(f"🌐 Servidor: {BASE_URL}")
    print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 80)
    
    test_middleware_profundo()
    test_comparacao_detalhada()
    
    print("\n" + "=" * 80)
    print("🎉 DEBUG MIDDLEWARE PROFUNDO CONCLUÍDO!")
    print("=" * 80)

if __name__ == "__main__":
    main()


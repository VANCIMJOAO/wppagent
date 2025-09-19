#!/usr/bin/env python3
"""
🔍 DEBUG RATE LIMITING - Identificar Conflito entre Middlewares
Testa especificamente o problema de rate limiting no /ping
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "https://wppagent-production-app-production.up.railway.app"

def test_rate_limiting_detalhado():
    """Testa rate limiting em detalhes"""
    print("🔍 DEBUG RATE LIMITING DETALHADO")
    print("=" * 60)
    
    # Teste 1: Verificar se é problema de múltiplos middlewares
    print("📋 TESTE 1: VERIFICAR MÚLTIPLOS MIDDLEWARES")
    
    # Fazer várias requisições para /ping e ver o comportamento
    for i in range(5):
        try:
            response = requests.get(f"{BASE_URL}/ping", timeout=5)
            print(f"   Requisição {i+1}: {response.status_code}")
            
            if response.status_code == 429:
                try:
                    content = response.json()
                    print(f"      Rate limit info: {content}")
                except:
                    print(f"      Content: {response.text[:100]}...")
            
            # Aguardar 1 segundo entre requisições
            time.sleep(1)
            
        except Exception as e:
            print(f"   Requisição {i+1}: ERRO - {str(e)}")
    
    # Teste 2: Verificar se é problema de IP
    print("\n📋 TESTE 2: VERIFICAR PROBLEMA DE IP")
    
    # Testar com diferentes headers de IP
    ip_headers = [
        {"X-Forwarded-For": "127.0.0.1"},
        {"X-Real-IP": "127.0.0.1"},
        {"X-Forwarded-For": "192.168.1.1"},
        {"X-Forwarded-For": "10.0.0.1"},
        {}  # Sem headers de IP
    ]
    
    for headers in ip_headers:
        try:
            response = requests.get(f"{BASE_URL}/ping", headers=headers, timeout=5)
            print(f"   Headers {headers}: {response.status_code}")
        except Exception as e:
            print(f"   Headers {headers}: ERRO - {str(e)}")
    
    # Teste 3: Verificar se é problema de User-Agent
    print("\n📋 TESTE 3: VERIFICAR PROBLEMA DE USER-AGENT")
    
    user_agents = [
        "Railway-Health-Check/1.0",
        "curl/7.68.0",
        "Mozilla/5.0 (compatible; Railway/1.0)",
        "HealthCheck/1.0",
        "Python-requests/2.28.1",
        "Railway/1.0",
        "Health-Check/1.0"
    ]
    
    for ua in user_agents:
        try:
            headers = {"User-Agent": ua}
            response = requests.get(f"{BASE_URL}/ping", headers=headers, timeout=5)
            print(f"   {ua}: {response.status_code}")
        except Exception as e:
            print(f"   {ua}: ERRO - {str(e)}")
    
    # Teste 4: Verificar se é problema de método HTTP
    print("\n📋 TESTE 4: VERIFICAR PROBLEMA DE MÉTODO HTTP")
    
    metodos = ["GET", "HEAD", "OPTIONS", "POST"]
    
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
            
            print(f"   {metodo}: {response.status_code}")
        except Exception as e:
            print(f"   {metodo}: ERRO - {str(e)}")

def test_comparacao_endpoints():
    """Testa comparação entre endpoints que funcionam e não funcionam"""
    print("\n🔍 TESTE DE COMPARAÇÃO DE ENDPOINTS")
    print("=" * 60)
    
    # Endpoints para testar
    endpoints = [
        ("/ping", "GET"),
        ("/health", "GET"),
        ("/docs", "GET"),
        ("/metrics", "GET"),
        ("/", "GET"),
        ("/meta/webhook/verify", "POST")
    ]
    
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=5)
            
            status = "✅" if response.status_code == 200 else "❌"
            print(f"   {status} {method} {endpoint}: {response.status_code}")
            
            if response.status_code == 429:
                try:
                    content = response.json()
                    print(f"      Rate limit: {content}")
                except:
                    pass
                    
        except Exception as e:
            print(f"   ❌ {method} {endpoint}: ERRO - {str(e)}")

def test_aguardar_reset_rate_limit():
    """Testa aguardar reset do rate limit"""
    print("\n🔍 TESTE DE AGUARDAR RESET DO RATE LIMIT")
    print("=" * 60)
    
    print("   Aguardando 60 segundos para reset do rate limit...")
    time.sleep(60)
    
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=5)
        print(f"   Após aguardar: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Rate limit resetou! /ping funcionando!")
        else:
            print(f"   ❌ Ainda com problema: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro após aguardar: {str(e)}")

def main():
    """Executa todos os testes de rate limiting"""
    print("🔍 DEBUG RATE LIMITING - IDENTIFICAR CONFLITO")
    print("=" * 80)
    print(f"🌐 Servidor: {BASE_URL}")
    print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 80)
    
    test_rate_limiting_detalhado()
    test_comparacao_endpoints()
    test_aguardar_reset_rate_limit()
    
    print("\n" + "=" * 80)
    print("🎉 DEBUG RATE LIMITING CONCLUÍDO!")
    print("=" * 80)

if __name__ == "__main__":
    main()


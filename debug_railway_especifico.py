#!/usr/bin/env python3
"""
🔍 DEBUG RAILWAY ESPECÍFICO - Verificar Problema no Railway
Testa especificamente se o problema está no Railway ou localmente
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "https://wppagent-production-app-production.up.railway.app"

def test_railway_especifico():
    """Testa especificamente o Railway"""
    print("🔍 DEBUG RAILWAY ESPECÍFICO - VERIFICAR PROBLEMA")
    print("=" * 60)
    
    # Teste 1: Verificar se é problema de cache do Railway
    print("📋 TESTE 1: VERIFICAR CACHE DO RAILWAY")
    
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
        print(f"   Content: {response.text[:100]}...")
        
        # Verificar headers de resposta
        print(f"   Headers de resposta:")
        for header, value in response.headers.items():
            if 'cache' in header.lower() or 'etag' in header.lower():
                print(f"      {header}: {value}")
        
    except Exception as e:
        print(f"   Erro: {str(e)}")
    
    # Teste 2: Verificar se é problema de User-Agent específico do Railway
    print("\n📋 TESTE 2: VERIFICAR USER-AGENT DO RAILWAY")
    
    railway_user_agents = [
        "Railway-Health-Check/1.0",
        "Railway-Health-Check/2.0", 
        "Railway-Health-Check/3.0",
        "Railway/1.0",
        "Railway/2.0",
        "Railway/3.0",
        "Health-Check/1.0",
        "Health-Check/2.0",
        "Health-Check/3.0"
    ]
    
    for ua in railway_user_agents:
        try:
            headers = {"User-Agent": ua}
            response = requests.get(f"{BASE_URL}/ping", headers=headers, timeout=5)
            print(f"   {ua}: {response.status_code}")
        except Exception as e:
            print(f"   {ua}: ERRO - {str(e)}")
    
    # Teste 3: Verificar se é problema de IP específico do Railway
    print("\n📋 TESTE 3: VERIFICAR IP DO RAILWAY")
    
    railway_ips = [
        "127.0.0.1",
        "::1",
        "0.0.0.0",
        "localhost",
        "railway.app",
        "up.railway.app"
    ]
    
    for ip in railway_ips:
        try:
            headers = {"X-Forwarded-For": ip}
            response = requests.get(f"{BASE_URL}/ping", headers=headers, timeout=5)
            print(f"   IP {ip}: {response.status_code}")
        except Exception as e:
            print(f"   IP {ip}: ERRO - {str(e)}")
    
    # Teste 4: Verificar se é problema de método HTTP específico do Railway
    print("\n📋 TESTE 4: VERIFICAR MÉTODO HTTP DO RAILWAY")
    
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
            
            if response.status_code == 401:
                try:
                    content = response.json()
                    print(f"      Auth error: {content}")
                except:
                    pass
                    
        except Exception as e:
            print(f"   {metodo}: ERRO - {str(e)}")
    
    # Teste 5: Verificar se é problema de timeout ou rate limiting
    print("\n📋 TESTE 5: VERIFICAR TIMEOUT E RATE LIMITING")
    
    # Fazer várias requisições com intervalos diferentes
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
            elif response.status_code == 401:
                try:
                    content = response.json()
                    print(f"      Auth error: {content}")
                except:
                    pass
            
            time.sleep(interval)
            
        except Exception as e:
            print(f"      Erro: {str(e)}")

def test_comparacao_endpoints_railway():
    """Testa comparação de endpoints no Railway"""
    print("\n🔍 TESTE DE COMPARAÇÃO DE ENDPOINTS NO RAILWAY")
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
    """Executa todos os testes de debug do Railway"""
    print("🔍 DEBUG RAILWAY ESPECÍFICO - VERIFICAR PROBLEMA")
    print("=" * 80)
    print(f"🌐 Servidor: {BASE_URL}")
    print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 80)
    
    test_railway_especifico()
    test_comparacao_endpoints_railway()
    
    print("\n" + "=" * 80)
    print("🎉 DEBUG RAILWAY ESPECÍFICO CONCLUÍDO!")
    print("=" * 80)

if __name__ == "__main__":
    main()


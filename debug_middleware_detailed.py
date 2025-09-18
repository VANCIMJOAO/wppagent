#!/usr/bin/env python3
"""
🔍 DEBUG MIDDLEWARE DETALHADO - Análise Profunda
Testa especificamente a lógica do middleware de autenticação
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://wppagent-production-app-production.up.railway.app"

def test_middleware_logic():
    """Testa a lógica específica do middleware"""
    print("🔍 TESTE DETALHADO - LÓGICA DO MIDDLEWARE")
    print("=" * 60)
    
    # Simular a lógica do middleware
    public_endpoints = {
        "/health",
        "/ping",  # Railway healthcheck endpoint
        "/docs",
        "/openapi.json",
        "/webhook",  # WhatsApp webhook - prefixo genérico
        "/webhook/test",  # WhatsApp webhook - endpoint de teste
        "/meta",  # Meta webhook específico - SEM JWT
        "/meta/webhook",  # Meta webhook específico - rota completa
        "/debug",  # Debug endpoints (TEMPORÁRIO)
        "/system",  # System info endpoints (TEMPORÁRIO)
        "/api/v1/webhooks",  # WhatsApp webhook - rota completa
        "/auth/login",
        "/admin/login",  # Admin login endpoint
        "/admin/create-initial-admin",  # TEMPORÁRIO: Criar admin inicial
        "/admin/debug-admin",  # TEMPORÁRIO: Debug admin
        "/admin/debug-jwt",  # TEMPORÁRIO: Debug JWT
        "/auth/register",
        "/metrics",
        "/metrics/system",
        "/cors/test",  # Endpoint de teste CORS
        "/cors/debug",  # Endpoint de debug CORS
        "/appointments/test",  # 🚀 PF-001: Rotas de teste sem autenticação
        "/",  # Endpoint raiz
    }
    
    def _is_public_endpoint(path: str) -> bool:
        """Simula a lógica do middleware"""
        for public_path in public_endpoints:
            if path == public_path or path.startswith(public_path + "/"):
                return True
        return False
    
    # Testar diferentes paths
    test_paths = [
        "/ping",
        "/ping/",
        "/health",
        "/docs",
        "/meta/webhook/verify",
        "/webhook",
        "/api/users",
        "/admin",
        "/"
    ]
    
    print("📋 TESTANDO LÓGICA DO MIDDLEWARE:")
    for path in test_paths:
        is_public = _is_public_endpoint(path)
        status = "✅ PÚBLICO" if is_public else "❌ PRIVADO"
        print(f"   {status} {path}")
    
    print("\n🔍 TESTANDO ENDPOINTS REAIS:")
    
    # Testar endpoints reais
    for path in test_paths:
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=5)
            is_public = _is_public_endpoint(path)
            expected_status = 200 if is_public else 401
            actual_status = response.status_code
            
            if actual_status == expected_status:
                status = "✅ CORRETO"
            else:
                status = "❌ INCORRETO"
            
            print(f"   {status} {path} - Esperado: {expected_status}, Atual: {actual_status}")
            
        except Exception as e:
            print(f"   ❌ ERRO {path} - {str(e)}")

def test_specific_issues():
    """Testa problemas específicos identificados"""
    print("\n🔍 TESTE DE PROBLEMAS ESPECÍFICOS")
    print("=" * 60)
    
    # Problema 1: /ping retornando 401
    print("📋 PROBLEMA 1: /ping retornando 401")
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Content: {response.text}")
    except Exception as e:
        print(f"   Erro: {str(e)}")
    
    # Problema 2: /meta/webhook/verify retornando 401
    print("\n📋 PROBLEMA 2: /meta/webhook/verify retornando 401")
    try:
        webhook_data = {"test": "data"}
        response = requests.post(f"{BASE_URL}/meta/webhook/verify", json=webhook_data, timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Content: {response.text}")
    except Exception as e:
        print(f"   Erro: {str(e)}")
    
    # Problema 3: Verificar se há middleware duplicado
    print("\n📋 PROBLEMA 3: Verificar middleware duplicado")
    try:
        # Testar com header específico
        headers = {"User-Agent": "Railway-Health-Check/1.0"}
        response = requests.get(f"{BASE_URL}/ping", headers=headers, timeout=5)
        print(f"   Status com User-Agent Railway: {response.status_code}")
        
        # Testar com Accept específico
        headers = {"Accept": "text/plain"}
        response = requests.get(f"{BASE_URL}/ping", headers=headers, timeout=5)
        print(f"   Status com Accept text/plain: {response.status_code}")
        
    except Exception as e:
        print(f"   Erro: {str(e)}")

def test_middleware_order():
    """Testa se há problema na ordem dos middlewares"""
    print("\n🔍 TESTE DE ORDEM DOS MIDDLEWARES")
    print("=" * 60)
    
    # Testar endpoints que funcionam
    working_endpoints = ["/health", "/docs", "/metrics", "/"]
    
    for endpoint in working_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            print(f"   ✅ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint}: {str(e)}")
    
    # Testar endpoints que não funcionam
    broken_endpoints = ["/ping", "/meta/webhook/verify"]
    
    for endpoint in broken_endpoints:
        try:
            if endpoint == "/ping":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=5)
            print(f"   ❌ {endpoint}: {response.status_code} (deveria ser 200)")
        except Exception as e:
            print(f"   ❌ {endpoint}: {str(e)}")

def main():
    """Executa todos os testes de debug"""
    print("🔍 DEBUG MIDDLEWARE DETALHADO - ANÁLISE PROFUNDA")
    print("=" * 80)
    print(f"🌐 Servidor: {BASE_URL}")
    print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 80)
    
    test_middleware_logic()
    test_specific_issues()
    test_middleware_order()
    
    print("\n" + "=" * 80)
    print("🎉 DEBUG CONCLUÍDO!")
    print("=" * 80)

if __name__ == "__main__":
    main()

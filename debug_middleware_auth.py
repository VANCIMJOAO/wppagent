#!/usr/bin/env python3
"""
🔍 DEBUG MIDDLEWARE AUTH - Diagnóstico Completo
Testa especificamente o problema de autenticação nos endpoints públicos
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://wppagent-production-app-production.up.railway.app"

def test_endpoint(endpoint: str, method: str = "GET", data: dict = None, headers: dict = None):
    """Testa um endpoint específico"""
    print(f"\n🔍 Testando {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers, timeout=10)
        elif method == "OPTIONS":
            response = requests.options(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
        
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        try:
            content = response.json()
            print(f"   Content: {json.dumps(content, indent=2)}")
        except:
            print(f"   Content: {response.text[:200]}...")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return False

def main():
    """Executa diagnóstico completo"""
    print("🔍 DIAGNÓSTICO COMPLETO - MIDDLEWARE AUTH")
    print("=" * 60)
    print(f"🌐 Servidor: {BASE_URL}")
    print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    # Teste 1: Endpoints que DEVEM ser públicos
    print("\n📋 TESTE 1: ENDPOINTS PÚBLICOS (devem retornar 200)")
    public_endpoints = [
        "/ping",
        "/",
        "/docs",
        "/openapi.json",
        "/health",
        "/metrics"
    ]
    
    for endpoint in public_endpoints:
        success = test_endpoint(endpoint)
        status = "✅ SUCESSO" if success else "❌ FALHA"
        print(f"   {status} {endpoint}")
    
    # Teste 2: Endpoints que DEVEM exigir autenticação
    print("\n📋 TESTE 2: ENDPOINTS PRIVADOS (devem retornar 401)")
    private_endpoints = [
        "/api/users",
        "/admin",
        "/auth/profile",
        "/appointments"
    ]
    
    for endpoint in private_endpoints:
        success = test_endpoint(endpoint)
        status = "✅ SUCESSO" if not success else "❌ FALHA"
        print(f"   {status} {endpoint} (deveria ser 401)")
    
    # Teste 3: Webhook endpoints
    print("\n📋 TESTE 3: WEBHOOK ENDPOINTS")
    webhook_data = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "test",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "15551234567",
                        "phone_number_id": "728348237027885"
                    },
                    "messages": [{
                        "from": "+5511999999999",
                        "id": "test_message",
                        "timestamp": "1234567890",
                        "text": {"body": "Teste"},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    webhook_endpoints = [
        "/meta/webhook/verify",
        "/webhook",
        "/api/v1/webhooks"
    ]
    
    for endpoint in webhook_endpoints:
        success = test_endpoint(endpoint, "POST", webhook_data)
        status = "✅ SUCESSO" if success else "❌ FALHA"
        print(f"   {status} {endpoint}")
    
    # Teste 4: CORS
    print("\n📋 TESTE 4: CORS")
    cors_headers = {
        "Origin": "https://example.com",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Content-Type"
    }
    
    cors_success = test_endpoint("/ping", "OPTIONS", headers=cors_headers)
    status = "✅ SUCESSO" if cors_success else "❌ FALHA"
    print(f"   {status} CORS preflight")
    
    # Teste 5: Headers específicos
    print("\n📋 TESTE 5: HEADERS ESPECÍFICOS")
    
    # Teste com User-Agent específico
    headers_ua = {"User-Agent": "Railway-Health-Check/1.0"}
    success = test_endpoint("/ping", headers=headers_ua)
    status = "✅ SUCESSO" if success else "❌ FALHA"
    print(f"   {status} /ping com User-Agent Railway")
    
    # Teste com Accept específico
    headers_accept = {"Accept": "application/json"}
    success = test_endpoint("/ping", headers=headers_accept)
    status = "✅ SUCESSO" if success else "❌ FALHA"
    print(f"   {status} /ping com Accept JSON")
    
    print("\n" + "=" * 60)
    print("🎉 DIAGNÓSTICO CONCLUÍDO!")
    print("=" * 60)

if __name__ == "__main__":
    main()

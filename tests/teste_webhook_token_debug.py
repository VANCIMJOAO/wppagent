#!/usr/bin/env python3
"""
TESTE ESPECÍFICO DE WEBHOOK VERIFICATION
========================================
Testa especificamente a verificação do webhook para debugar o token
"""

import requests

def test_webhook_verification():
    """Testa diferentes tokens para identificar o problema"""
    print("🔍 TESTE ESPECÍFICO DE WEBHOOK VERIFICATION")
    print("=" * 60)
    
    railway_url = "https://wppagent-production-app-production.up.railway.app"
    
    # Diferentes tokens para testar
    tokens_to_test = [
        "whatsapp_webhook_verify_token",
        "your_verify_token_here",
        "test_token",
        "",
        "webhook_token"
    ]
    
    for token in tokens_to_test:
        print(f"\n🧪 Testando token: '{token}'")
        
        verify_params = {
            "hub.mode": "subscribe",
            "hub.verify_token": token,
            "hub.challenge": "test_challenge_12345"
        }
        
        try:
            response = requests.get(f"{railway_url}/webhook/verify", params=verify_params, timeout=30)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:100]}")
            
            if response.status_code == 200:
                print("✅ TOKEN ENCONTRADO!")
                print(f"🎯 Token correto: '{token}'")
                return token
            else:
                print("❌ Token incorreto")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    print("\n❌ Nenhum token funcionou")
    return None

if __name__ == "__main__":
    test_webhook_verification()
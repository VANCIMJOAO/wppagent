#!/usr/bin/env python3
"""
Debug específico para Webhook
Investigando erro 500 no webhook verification
"""

import requests
import json
import traceback

def test_webhook_debug():
    """Teste específico para webhook"""
    base_url = "https://wppagent-production.up.railway.app"
    
    print("🔍 DEBUG WEBHOOK VERIFICATION")
    print("=============================")
    
    try:
        # Testar webhook verification
        params = {
            'hub.mode': 'subscribe',
            'hub.challenge': 'test123',
            'hub.verify_token': 'test_verify_token_123'
        }
        
        response = requests.get(f"{base_url}/webhook", params=params, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 500:
            print("\n❌ ERRO 500 DETECTADO NO WEBHOOK")
            print("Investigando possíveis causas...")
            
            # Testar outros endpoints do webhook
            print("\n🔍 TESTANDO OUTROS ENDPOINTS WEBHOOK:")
            
            # Testar POST webhook
            try:
                post_response = requests.post(f"{base_url}/webhook", json={}, timeout=10)
                print(f"Webhook POST Status: {post_response.status_code}")
                print(f"Webhook POST Response: {post_response.text[:200]}...")
            except Exception as e:
                print(f"Webhook POST Error: {e}")
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_webhook_debug()

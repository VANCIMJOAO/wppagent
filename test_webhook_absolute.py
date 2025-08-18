#!/usr/bin/env python3
"""
🧪 TESTE RÁPIDO DO WEBHOOK ABSOLUTO
==================================
Teste simples para verificar se o sistema de controle absoluto 
está funcionando antes do deploy.
"""

import requests
import json
import time
from datetime import datetime

def test_webhook_absolute():
    """Testa webhook com controle absoluto"""
    
    base_url = "http://localhost:8000"  # Para teste local
    
    print("🧪 TESTE DO WEBHOOK ABSOLUTO")
    print("="*50)
    
    # 1. Verificar se endpoints estão funcionando
    try:
        print("\n📊 Testando endpoint /webhook/stats...")
        response = requests.get(f"{base_url}/webhook/stats", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"Cache size: {stats.get('cache_info', {}).get('cached_messages', 0)}")
            print("✅ Endpoint stats OK")
        else:
            print("❌ Endpoint stats falhou")
    except Exception as e:
        print(f"❌ Erro no teste stats: {e}")
    
    # 2. Verificar controle
    try:
        print("\n🎛️ Testando endpoint /webhook/control...")
        response = requests.get(f"{base_url}/webhook/control", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            control = response.json()
            print(f"Response control: {control.get('response_control')}")
            print(f"Single response working: {control.get('single_response_working')}")
            print("✅ Endpoint control OK")
        else:
            print("❌ Endpoint control falhou")
    except Exception as e:
        print(f"❌ Erro no teste control: {e}")
    
    # 3. Verificar status
    try:
        print("\n📡 Testando endpoint /webhook/status...")
        response = requests.get(f"{base_url}/webhook/status", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            status = response.json()
            print(f"Status: {status.get('status')}")
            print(f"Corrections active: {status.get('corrections_active')}")
            print(f"Absolute control: {status.get('absolute_control')}")
            print("✅ Endpoint status OK")
        else:
            print("❌ Endpoint status falhou")
    except Exception as e:
        print(f"❌ Erro no teste status: {e}")
    
    # 4. Testar webhook com mensagem fake
    webhook_payload = {
        "entry": [{
            "id": "test_entry",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"phone_number_id": "123456789"},
                    "messages": [{
                        "id": f"test_msg_{int(time.time())}",
                        "from": "5511999999999",
                        "type": "text",
                        "timestamp": str(int(time.time())),
                        "text": {"body": "Oi, teste webhook absoluto!"}
                    }]
                }
            }]
        }]
    }
    
    try:
        print("\n📤 Testando webhook POST com mensagem fake...")
        response = requests.post(
            f"{base_url}/webhook",
            json=webhook_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Webhook POST OK")
            
            # Verificar stats após teste
            time.sleep(2)
            stats_response = requests.get(f"{base_url}/webhook/stats", timeout=5)
            if stats_response.status_code == 200:
                stats = stats_response.json()
                processed = stats.get('stats', {}).get('messages_processed', 0)
                responses = stats.get('stats', {}).get('responses_sent', 0)
                blocked = stats.get('stats', {}).get('messages_blocked', 0)
                
                print(f"📊 Stats após teste:")
                print(f"  Mensagens processadas: {processed}")
                print(f"  Respostas enviadas: {responses}")
                print(f"  Mensagens bloqueadas: {blocked}")
        else:
            print(f"❌ Webhook POST falhou: {response.text}")
    except Exception as e:
        print(f"❌ Erro no teste webhook: {e}")
    
    print("\n" + "="*50)
    print("🏁 TESTE CONCLUÍDO")

if __name__ == "__main__":
    test_webhook_absolute()
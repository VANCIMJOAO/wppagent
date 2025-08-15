#!/usr/bin/env python3
"""
🔧 TESTE WEBHOOK SIMULADO
========================
Simula exatamente uma mensagem do WhatsApp
para testar se a formatação está funcionando
"""

import requests
import json
import time

def test_webhook_simulation():
    print("🔧 TESTE WEBHOOK SIMULADO")
    print("=" * 40)
    
    # URL do webhook
    url = "https://wppagent-production.up.railway.app/webhook"
    
    # Simular payload do WhatsApp (verificar como é na verdade)
    current_timestamp = str(int(time.time()))
    
    # Payload simulando exatamente o que o WhatsApp envia
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "103285572647990",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "15551536026",
                        "phone_number_id": "103285572647990"
                    },
                    "messages": [{
                        "from": "15551536026",
                        "id": f"wamid.test_{current_timestamp}",
                        "timestamp": current_timestamp,
                        "text": {
                            "body": "Quais serviços vocês oferecem?"
                        },
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "WhatsApp/1.0"
    }
    
    print(f"📡 Enviando para: {url}")
    print(f"📨 Mensagem: Quais serviços vocês oferecem?")
    print(f"📱 De: 15551536026")
    print()
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📝 Resposta: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook processado com sucesso!")
            print("📲 Verifique seu WhatsApp para ver a resposta")
        else:
            print(f"❌ Erro no webhook: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

if __name__ == "__main__":
    test_webhook_simulation()

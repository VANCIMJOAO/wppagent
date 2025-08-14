#!/usr/bin/env python3
"""
📱 TESTE RÁPIDO - WhatsApp Real + Webhook
=========================================
"""

import asyncio
import aiohttp
import time
import random
import hmac
import hashlib
import json
from datetime import datetime

RAILWAY_URL = "https://wppagent-production.up.railway.app"
TEST_PHONE = "5516991022255"

async def test_whatsapp_real_and_webhook():
    """Teste rápido: webhook + WhatsApp real"""
    print("📱 TESTE WHATSAPP REAL + WEBHOOK")
    print("=" * 40)
    
    test_messages = [
        "Olá! Teste rápido do sistema",
        "Quais serviços vocês oferecem?",
        "Quanto custa uma limpeza de pele?"
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, message in enumerate(test_messages, 1):
            print(f"\n🧪 Teste {i}/3: {message}")
            
            # 1. Enviar via webhook (simulação)
            message_id = f"wamid_{int(time.time())}_{random.randint(1000, 9999)}"
            timestamp = str(int(time.time()))
            
            webhook_payload = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "test_entry",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"phone_number_id": "test_phone_id"},
                            "contacts": [{"profile": {"name": "Teste Real"}, "wa_id": TEST_PHONE}],
                            "messages": [{
                                "from": TEST_PHONE,
                                "id": message_id,
                                "timestamp": timestamp,
                                "type": "text",
                                "text": {"body": message}
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            # Criar assinatura
            payload_bytes = json.dumps(webhook_payload, separators=(',', ':')).encode()
            signature = hmac.new("meutoken123".encode(), payload_bytes, hashlib.sha256).hexdigest()
            
            try:
                print("  📤 Enviando webhook...")
                async with session.post(
                    f"{RAILWAY_URL}/webhook",
                    json=webhook_payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "WhatsApp/2.0",
                        "X-Hub-Signature-256": f"sha256={signature}"
                    },
                    timeout=10
                ) as response:
                    print(f"  ✅ Webhook: {response.status}")
                    
            except Exception as e:
                print(f"  ❌ Webhook error: {e}")
                continue
            
            # 2. Enviar via WhatsApp API real
            try:
                print("  📱 Enviando WhatsApp real...")
                
                # Usar o endpoint correto de teste
                params = {
                    "phone_number": TEST_PHONE,
                    "message": f"[TESTE REAL] {message}"
                }
                
                async with session.post(
                    f"{RAILWAY_URL}/webhook/test-send",
                    params=params,
                    timeout=15
                ) as response:
                    
                    if response.status == 200:
                        print("  ✅ WhatsApp real enviado!")
                    else:
                        error_text = await response.text()
                        print(f"  ⚠️ WhatsApp real: {response.status} - {error_text[:100]}")
                        
            except Exception as e:
                print(f"  ❌ WhatsApp real error: {e}")
            
            # Aguardar um pouco entre mensagens
            if i < len(test_messages):
                print("  ⏳ Aguardando...")
                await asyncio.sleep(3)
    
    print("\n🎯 TESTE CONCLUÍDO!")
    print("Verifique seu WhatsApp para as mensagens reais enviadas")

if __name__ == "__main__":
    asyncio.run(test_whatsapp_real_and_webhook())

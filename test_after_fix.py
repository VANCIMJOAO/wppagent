#!/usr/bin/env python3
"""
🧪 Teste Pós-Correção
"""

import asyncio
import aiohttp
import json
import hmac
import hashlib
import time
import random
from datetime import datetime

async def test_after_fix():
    """Teste após corrigir status"""
    print(f"🔧 TESTE PÓS-CORREÇÃO às {datetime.now().strftime('%H:%M:%S')}")
    print("="*50)
    
    # Enviar uma mensagem simples de teste
    message = f"Teste pós-correção {datetime.now().strftime('%H:%M:%S')} - o bot está funcionando?"
    
    webhook_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "test_fix",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"phone_number_id": "728348237027885"},
                    "contacts": [{"profile": {"name": "João Teste Fix"}, "wa_id": "5516991022255"}],
                    "messages": [{
                        "from": "5516991022255",
                        "id": f"fix_{int(time.time())}_{random.randint(1000, 9999)}",
                        "timestamp": str(int(time.time())),
                        "type": "text",
                        "text": {"body": message}
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    payload_bytes = json.dumps(webhook_payload, separators=(',', ':')).encode()
    signature = hmac.new("meutoken123".encode(), payload_bytes, hashlib.sha256).hexdigest()
    
    async with aiohttp.ClientSession() as session:
        try:
            print(f"📤 Enviando: '{message}'")
            async with session.post(
                "https://wppagent-production.up.railway.app/webhook",
                json=webhook_payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "WhatsApp/2.0",
                    "X-Hub-Signature-256": f"sha256={signature}"
                },
                timeout=10
            ) as response:
                
                status = response.status
                text = await response.text()
                
                print(f"📊 Status: {status}")
                if status == 200:
                    print("✅ Webhook processado - aguarde resposta no WhatsApp!")
                else:
                    print(f"❌ Erro: {text}")
                    
        except Exception as e:
            print(f"💥 Erro: {e}")

if __name__ == "__main__":
    asyncio.run(test_after_fix())

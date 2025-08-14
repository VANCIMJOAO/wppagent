#!/usr/bin/env python3
"""
🧪 Teste Real: Cliente → LLM → Resposta
======================================
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

async def test_real_conversation():
    """Teste real: cliente envia → sistema responde"""
    print("📱 TESTE REAL: Cliente → LLM → Resposta")
    print("=" * 45)
    print(f"🎯 Cliente: {TEST_PHONE}")
    print(f"⏰ Hora: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Mensagens que um cliente real enviaria
    client_messages = [
        "Oi! Quero fazer uma limpeza de pele",
        "Quanto custa?",
        "Vocês fazem sobrancelha também?"
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, message in enumerate(client_messages, 1):
            print(f"💬 Teste {i}/3: Cliente enviando...")
            print(f"   📝 Mensagem: '{message}'")
            
            # Simular webhook como se fosse cliente real enviando
            message_id = f"real_{int(time.time())}_{random.randint(1000, 9999)}"
            timestamp = str(int(time.time()))
            
            webhook_payload = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "real_test_entry",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"phone_number_id": "728348237027885"},
                            "contacts": [{"profile": {"name": "João Cliente Real"}, "wa_id": TEST_PHONE}],
                            "messages": [{
                                "from": TEST_PHONE,  # Cliente enviando
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
                print("   📤 Enviando webhook (simulando cliente)...")
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
                    
                    status = response.status
                    text = await response.text()
                    
                    if status == 200:
                        print(f"   ✅ Webhook processado com sucesso")
                        print(f"   🤖 Sistema deve enviar resposta LLM para seu WhatsApp agora!")
                    else:
                        print(f"   ❌ Erro no webhook: {status}")
                        print(f"   📄 Resposta: {text[:100]}")
                        
            except Exception as e:
                print(f"   💥 Erro: {e}")
                continue
            
            # Aguardar antes da próxima mensagem
            if i < len(client_messages):
                print("   ⏳ Aguardando resposta...")
                await asyncio.sleep(8)  # Tempo para LLM processar e você ver no WhatsApp
                print()
    
    print("🎯 TESTE CONCLUÍDO!")
    print("📱 Verifique seu WhatsApp - você deve ter recebido 3 respostas da LLM")
    print("💡 Se não recebeu, pode haver problema na configuração do sistema")

if __name__ == "__main__":
    asyncio.run(test_real_conversation())

#!/usr/bin/env python3
"""
🧪 TESTE RÁPIDO DE DEBUG - WhatsApp Agent
===========================================
Teste rápido para verificar se o bypass está funcionando
"""

import asyncio
import aiohttp
import json
import time
import random
import logging
import hmac
import hashlib
from datetime import datetime, timezone

# Configurações
RAILWAY_URL = "https://wppagent-production.up.railway.app"
TEST_PHONE = "5516991022255"
WEBHOOK_URL = f"{RAILWAY_URL}/webhook"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_quick_webhook():
    """Teste rápido do webhook"""
    logger.info("🚀 TESTE RÁPIDO - Verificando bypass do webhook")
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        
        # Verificar health primeiro
        try:
            async with session.get(f"{RAILWAY_URL}/health") as response:
                health_data = await response.json()
                logger.info(f"✅ Health Check: {response.status} - {health_data.get('status', 'unknown')}")
        except Exception as e:
            logger.error(f"❌ Health Check falhou: {e}")
            return
        
        # Testar webhook com 3 mensagens simples
        messages = [
            "Olá! Como está?",
            "Gostaria de saber sobre os serviços",
            "Obrigado!"
        ]
        
        for i, message in enumerate(messages, 1):
            logger.info(f"📤 [{i}/3] Enviando: {message}")
            
            # Criar payload do WhatsApp
            message_id = f"wamid.test_{int(time.time())}{random.randint(1000, 9999)}"
            timestamp = str(int(time.time()))
            
            payload = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "24386792860950513",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550987654",
                                "phone_number_id": "728348237027885"
                            },
                            "contacts": [{
                                "profile": {
                                    "name": "João Testador Sistema"
                                },
                                "wa_id": TEST_PHONE
                            }],
                            "messages": [{
                                "from": TEST_PHONE,
                                "id": message_id,
                                "timestamp": timestamp,
                                "type": "text",
                                "text": {
                                    "body": message
                                }
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            # Criar assinatura
            payload_bytes = json.dumps(payload, separators=(',', ':')).encode()
            webhook_secret = "meutoken123"
            signature = hmac.new(webhook_secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
            
            # Enviar webhook
            try:
                start_time = time.time()
                async with session.post(
                    WEBHOOK_URL,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "WhatsApp/2.0",
                        "X-Hub-Signature-256": f"sha256={signature}"
                    }
                ) as response:
                    response_time = time.time() - start_time
                    response_text = await response.text()
                    
                    status_icon = "✅" if response.status == 200 else "❌"
                    logger.info(f"{status_icon} [{i}/3] Status: {response.status} | Tempo: {response_time*1000:.1f}ms")
                    
                    if response.status != 200:
                        logger.error(f"Response body: {response_text[:200]}...")
                    
                    # Pausa entre mensagens
                    if i < len(messages):
                        await asyncio.sleep(2)
                        
            except Exception as e:
                logger.error(f"❌ [{i}/3] Erro ao enviar '{message}': {e}")
    
    logger.info("🎯 Teste rápido concluído!")

if __name__ == "__main__":
    asyncio.run(test_quick_webhook())

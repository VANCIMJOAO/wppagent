"""
Teste rápido para verificar se as correções funcionaram
"""
import asyncio
import aiohttp
import os
import json
from datetime import datetime, timezone

RAILWAY_URL = "https://wppagent-production.up.railway.app"
TEST_PHONE = "5516991022255"

async def test_webhook_fix():
    """Teste do webhook com as correções aplicadas"""
    
    # Test payload simples
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "123456789",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "15550987654",
                        "phone_number_id": "728348237027885"
                    },
                    "contacts": [{
                        "profile": {"name": "Test User"},
                        "wa_id": TEST_PHONE
                    }],
                    "messages": [{
                        "from": TEST_PHONE,
                        "id": f"test_{int(datetime.now(timezone.utc).timestamp())}",
                        "timestamp": str(int(datetime.now(timezone.utc).timestamp())),
                        "type": "text",
                        "text": {"body": "Teste do fix webhook - olá!"}
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # Testar webhook
            print("📤 Testando webhook corrigido...")
            async with session.post(
                f"{RAILWAY_URL}/webhook",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                print(f"📨 Status webhook: {response.status}")
                if response.status == 200:
                    print("✅ Webhook funcionando!")
                elif response.status == 403:
                    print("❌ Ainda com erro 403 - verificar logs")
                else:
                    print(f"⚠️ Status inesperado: {response.status}")
                
                response_text = await response.text()
                print(f"Response: {response_text[:100]}...")
            
            # Testar health
            print("🏥 Testando health check...")
            async with session.get(f"{RAILWAY_URL}/health") as response:
                print(f"📊 Status health: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"Health: {data.get('status', 'unknown')}")
                
        except Exception as e:
            print(f"❌ Erro no teste: {e}")

if __name__ == "__main__":
    print("🧪 TESTE RÁPIDO - CORREÇÕES WEBHOOK 403")
    print("======================================")
    asyncio.run(test_webhook_fix())
    print("======================================")
    print("✅ Teste concluído!")

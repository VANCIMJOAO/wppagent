#!/usr/bin/env python3
"""
🧪 SCRIPT DE TESTE SIMPLIFICADO - WhatsApp Agent
===============================================

Testa o sistema configurando temporariamente o bypass de validação
"""

import asyncio
import aiohttp
import json
import time
import os
from datetime import datetime

# Configurar bypass temporário
os.environ['BYPASS_WEBHOOK_VALIDATION'] = 'true'

RAILWAY_URL = "https://wppagent-production.up.railway.app"
TEST_PHONE = "5516991022255"
WEBHOOK_URL = f"{RAILWAY_URL}/webhook"

async def test_simple_message():
    """Teste simples de mensagem"""
    print("🧪 TESTE SIMPLES DO WEBHOOK")
    print("=" * 40)
    
    # Payload simples do WhatsApp
    webhook_payload = {
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
                            "name": "Testador Sistema"
                        },
                        "wa_id": TEST_PHONE
                    }],
                    "messages": [{
                        "from": TEST_PHONE,
                        "id": f"wamid.test_{int(time.time())}1234",
                        "timestamp": str(int(time.time())),
                        "type": "text",
                        "text": {
                            "body": "Olá! Este é um teste simples do sistema."
                        }
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"📤 Enviando mensagem para {WEBHOOK_URL}")
            
            async with session.post(
                WEBHOOK_URL,
                json=webhook_payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "WhatsApp/2.0"
                }
            ) as response:
                response_text = await response.text()
                
                print(f"📨 Status: {response.status}")
                print(f"📝 Response: {response_text}")
                
                if response.status == 200:
                    print("✅ Webhook funcionando!")
                else:
                    print(f"❌ Erro no webhook: {response.status}")
                    
                return response.status == 200
                
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

async def test_health_endpoints():
    """Testa endpoints de saúde"""
    print("\n🏥 TESTANDO ENDPOINTS DE SAÚDE")
    print("=" * 40)
    
    endpoints = [
        "/health",
        "/health/detailed",
        "/metrics/system"
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            try:
                url = f"{RAILWAY_URL}{endpoint}"
                print(f"🔍 Testando {endpoint}...")
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"  ✅ OK: {json.dumps(data, indent=2)[:200]}...")
                    else:
                        text = await response.text()
                        print(f"  ❌ Erro {response.status}: {text[:100]}...")
                        
            except Exception as e:
                print(f"  ❌ Exceção: {e}")

async def main():
    """Função principal"""
    print("🚀 INICIANDO TESTE SIMPLIFICADO")
    print(f"🔧 BYPASS_WEBHOOK_VALIDATION: {os.getenv('BYPASS_WEBHOOK_VALIDATION')}")
    
    # Testar endpoints primeiro
    await test_health_endpoints()
    
    # Tentar teste de mensagem
    success = await test_simple_message()
    
    if success:
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
    else:
        print("\n❌ TESTE FALHOU")
        print("💡 Possíveis causas:")
        print("   - Validação de webhook ainda ativa")
        print("   - Problemas de configuração no Railway")
        print("   - APIs (WhatsApp/OpenAI) não configuradas")

if __name__ == "__main__":
    asyncio.run(main())

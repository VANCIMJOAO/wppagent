#!/usr/bin/env python3
"""
🔍 DEBUG: Envio WhatsApp Detalhado
================================
"""

import asyncio
import aiohttp
import json
from datetime import datetime

RAILWAY_URL = "https://wppagent-production.up.railway.app"
TEST_PHONE = "5516991022255"

async def debug_whatsapp_send():
    """Debug detalhado do envio WhatsApp"""
    print("🔍 DEBUG ENVIO WHATSAPP")
    print("=" * 30)
    print(f"🎯 Número: {TEST_PHONE}")
    print(f"🌐 URL: {RAILWAY_URL}")
    print(f"⏰ Hora: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    async with aiohttp.ClientSession() as session:
        # Teste 1: Verificar se o endpoint existe
        print("📍 TESTE 1: Verificando endpoint...")
        try:
            test_params = {
                "phone_number": TEST_PHONE,
                "message": f"🧪 Teste debug {datetime.now().strftime('%H:%M:%S')}"
            }
            
            async with session.post(
                f"{RAILWAY_URL}/webhook/test-send",
                params=test_params,
                timeout=20
            ) as response:
                
                status = response.status
                headers = dict(response.headers)
                text = await response.text()
                
                print(f"  📊 Status: {status}")
                print(f"  📋 Headers: {json.dumps(dict(headers), indent=2)}")
                print(f"  📄 Response: {text}")
                
                if status == 200:
                    try:
                        data = json.loads(text)
                        print(f"\n  ✅ Parsed JSON:")
                        print(f"     Success: {data.get('success')}")
                        print(f"     Message: {data.get('message')}")
                        if 'api_response' in data:
                            print(f"     API Response: {data.get('api_response')}")
                        if 'api_status' in data:
                            print(f"     API Status: {data.get('api_status')}")
                    except:
                        print("  ⚠️ Resposta não é JSON válido")
                else:
                    print(f"  ❌ Erro HTTP: {status}")
                    
        except Exception as e:
            print(f"  💥 Erro na requisição: {e}")
        
        print("\n" + "="*50)
        
        # Teste 2: Verificar endpoint direto da API Meta
        print("📍 TESTE 2: Verificando status do sistema...")
        try:
            async with session.get(
                f"{RAILWAY_URL}/health",
                timeout=10
            ) as response:
                
                health_text = await response.text()
                print(f"  🏥 Health Status: {response.status}")
                print(f"  📄 Health Response: {health_text}")
                
        except Exception as e:
            print(f"  💥 Erro health check: {e}")
        
        print("\n" + "="*50)
        
        # Teste 3: Verificar configuração Meta API
        print("📍 TESTE 3: Testando configuração...")
        
        # Simular um webhook para ver se o sistema está respondendo
        try:
            webhook_payload = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "test_debug",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"phone_number_id": "debug_test"},
                            "contacts": [{"profile": {"name": "Debug Test"}, "wa_id": TEST_PHONE}],
                            "messages": [{
                                "from": TEST_PHONE,
                                "id": f"debug_{int(datetime.now().timestamp())}",
                                "timestamp": str(int(datetime.now().timestamp())),
                                "type": "text",
                                "text": {"body": "Debug: sistema está funcionando?"}
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            # Criar assinatura simples para teste
            import hmac
            import hashlib
            payload_bytes = json.dumps(webhook_payload, separators=(',', ':')).encode()
            signature = hmac.new("meutoken123".encode(), payload_bytes, hashlib.sha256).hexdigest()
            
            async with session.post(
                f"{RAILWAY_URL}/webhook",
                json=webhook_payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "WhatsApp/2.0",
                    "X-Hub-Signature-256": f"sha256={signature}"
                },
                timeout=15
            ) as response:
                
                webhook_text = await response.text()
                print(f"  📨 Webhook Status: {response.status}")
                print(f"  📄 Webhook Response: {webhook_text}")
                
        except Exception as e:
            print(f"  💥 Erro webhook test: {e}")

if __name__ == "__main__":
    asyncio.run(debug_whatsapp_send())

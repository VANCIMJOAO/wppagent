#!/usr/bin/env python3
"""
🧪 TESTE FOCADO - WhatsApp Agent usando endpoints de debug
========================================================

Usa os endpoints específicos de teste e debug disponíveis
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

RAILWAY_URL = "https://wppagent-production.up.railway.app"
TEST_PHONE = "5516991022255"

async def test_debug_endpoints():
    """Testa endpoints de debug específicos"""
    print("🔧 TESTANDO ENDPOINTS DE DEBUG")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Testar debug webhook
        print("\n1. 🔍 Testando debug/webhook-test...")
        try:
            webhook_payload = {"test": "payload"}
            async with session.post(
                f"{RAILWAY_URL}/debug/webhook-test",
                json=webhook_payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Hub-Signature-256": "test_signature"
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Resposta: {json.dumps(data, indent=2)}")
                else:
                    text = await response.text()
                    print(f"   ❌ Erro {response.status}: {text}")
        except Exception as e:
            print(f"   ❌ Exceção: {e}")
        
        # 2. Testar webhook/test-send
        print(f"\n2. 📱 Testando webhook/test-send para {TEST_PHONE}...")
        try:
            async with session.post(
                f"{RAILWAY_URL}/webhook/test-send",
                params={
                    "phone_number": TEST_PHONE,
                    "message": "Teste automatizado do sistema WhatsApp Agent"
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Resposta: {json.dumps(data, indent=2)}")
                else:
                    text = await response.text()
                    print(f"   ❌ Erro {response.status}: {text}")
        except Exception as e:
            print(f"   ❌ Exceção: {e}")
        
        # 3. Verificar configurações de webhook
        print(f"\n3. ⚙️ Testando debug/webhook-secret...")
        try:
            async with session.get(f"{RAILWAY_URL}/debug/webhook-secret") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Configurações: {json.dumps(data, indent=2)}")
                else:
                    text = await response.text()
                    print(f"   ❌ Erro {response.status}: {text}")
        except Exception as e:
            print(f"   ❌ Exceção: {e}")

async def test_conversation_flow():
    """Testa fluxo completo de conversa via API"""
    print("\n💬 TESTANDO FLUXO DE CONVERSA VIA API")
    print("=" * 50)
    
    test_messages = [
        "Olá! Como vocês estão?",
        "Quais serviços vocês oferecem?",
        "Quanto custa uma limpeza de pele?",
        "Posso agendar para amanhã?"
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, message in enumerate(test_messages, 1):
            print(f"\n{i}. 📤 Enviando: '{message}'")
            
            try:
                # Tentar usar endpoint de conversação se existir
                endpoints_to_try = [
                    "/conversation/message",
                    "/conversation/send", 
                    "/api/message",
                    "/api/conversation"
                ]
                
                success = False
                for endpoint in endpoints_to_try:
                    try:
                        payload = {
                            "phone_number": TEST_PHONE,
                            "message": message,
                            "user_name": "Testador Sistema"
                        }
                        
                        async with session.post(
                            f"{RAILWAY_URL}{endpoint}",
                            json=payload,
                            headers={"Content-Type": "application/json"}
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                print(f"   ✅ Via {endpoint}: {json.dumps(data, indent=2)[:200]}...")
                                success = True
                                break
                            elif response.status == 404:
                                continue  # Tentar próximo endpoint
                            else:
                                text = await response.text()
                                print(f"   ⚠️ {endpoint} - {response.status}: {text[:100]}...")
                    except:
                        continue
                
                if not success:
                    print(f"   ❌ Nenhum endpoint de conversa funcionou")
                    
                # Pequena pausa entre mensagens
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Erro geral: {e}")

async def test_business_data_access():
    """Testa acesso aos dados do negócio"""
    print("\n🏢 TESTANDO ACESSO AOS DADOS DO NEGÓCIO")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        endpoints_to_test = [
            "/business/info",
            "/business/services", 
            "/business/hours",
            "/services",
            "/api/business",
            "/api/services"
        ]
        
        for endpoint in endpoints_to_test:
            print(f"\n🔍 Testando {endpoint}...")
            try:
                async with session.get(f"{RAILWAY_URL}{endpoint}") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ OK: {json.dumps(data, indent=2)[:300]}...")
                    elif response.status == 404:
                        print(f"   ℹ️ Endpoint não existe")
                    else:
                        text = await response.text()
                        print(f"   ❌ Erro {response.status}: {text[:100]}...")
            except Exception as e:
                print(f"   ❌ Exceção: {e}")

async def main():
    """Função principal"""
    print("🚀 TESTE FOCADO DO WHATSAPP AGENT")
    print("🎯 Usando endpoints específicos de debug e API")
    print("=" * 60)
    
    # Executar testes em sequência
    await test_debug_endpoints()
    await test_conversation_flow()
    await test_business_data_access()
    
    print("\n" + "=" * 60)
    print("📊 TESTE CONCLUÍDO")
    print("💡 Este teste foca nos endpoints disponíveis do sistema")
    print("🔧 Para testes completos de webhook, configure as APIs no Railway")

if __name__ == "__main__":
    asyncio.run(main())

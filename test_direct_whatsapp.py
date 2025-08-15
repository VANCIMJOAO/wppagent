#!/usr/bin/env python3
"""
🔧 TESTE DIRETO - Enviar mensagem WhatsApp
=========================================
Envia uma mensagem diretamente via API Meta para testar a formatação
"""

import aiohttp
import asyncio
import time
import random

async def test_direct_whatsapp():
    """Testa envio direto via webhook"""
    
    # Configurações
    API_BASE_URL = "https://wppagent-production.up.railway.app"
    YOUR_PHONE = "5516991022255"
    WHATSAPP_PHONE_ID = "728348237027885" 
    BOT_PHONE = "15551536026"
    
    webhook_url = f"{API_BASE_URL}/webhook"
    
    # Mensagem para testar formatação de serviços
    test_message = "Quais serviços vocês oferecem?"
    
    webhook_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": WHATSAPP_PHONE_ID,
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": BOT_PHONE,
                        "phone_number_id": WHATSAPP_PHONE_ID
                    },
                    "messages": [{
                        "from": YOUR_PHONE,
                        "id": f"wamid.direct_test_{int(time.time())}{random.randint(100,999)}",
                        "timestamp": str(int(time.time())),
                        "text": {"body": test_message},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "facebookexternalua"
    }
    
    print(f"🚀 Enviando mensagem: '{test_message}'")
    print(f"📱 Para: {BOT_PHONE}")
    print(f"🔗 Webhook: {webhook_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=webhook_payload, headers=headers, timeout=30) as response:
                if response.status == 200:
                    print("✅ Mensagem enviada com sucesso!")
                    print("📲 Verifique seu WhatsApp para ver a resposta formatada")
                    return True
                else:
                    response_text = await response.text()
                    print(f"❌ Erro no envio: {response.status}")
                    print(f"📄 Resposta: {response_text}")
                    return False
                    
    except Exception as e:
        print(f"💥 Erro inesperado: {e}")
        return False

async def main():
    print("🔧 TESTE DIRETO - WhatsApp Formatação")
    print("=" * 50)
    print("📋 Este teste enviará uma mensagem direta")
    print("🎯 para verificar a formatação dos serviços")
    print("📲 Verifique seu WhatsApp após o envio")
    print("=" * 50)
    
    input("▶️ Pressione ENTER para enviar a mensagem: ")
    
    success = await test_direct_whatsapp()
    
    if success:
        print("\n✅ Teste concluído!")
        print("📱 Verifique seu WhatsApp e nos informe:")
        print("  • Se a resposta chegou")
        print("  • Se os emojis estão aparecendo (💰 ⏰)")
        print("  • Se a numeração está funcionando (1. 2. 3.)")
        print("  • Se o texto está em negrito (*texto*)")
    else:
        print("\n❌ Falha no teste")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Teste cancelado")
    except Exception as e:
        print(f"\n💥 Erro: {e}")

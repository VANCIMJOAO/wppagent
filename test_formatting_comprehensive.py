#!/usr/bin/env python3
"""
🎯 TESTE SIMPLES - Usando lógica do comprehensive_bot_test
========================================================
Teste idêntico ao comprehensive_bot_test mas focado na formatação
"""

import asyncio
import asyncpg
import aiohttp
import time
from datetime import datetime, timedelta
import random

async def test_formatting_like_comprehensive():
    """Teste exatamente como o comprehensive_bot_test.py"""
    
    # CONFIGURAÇÕES IDÊNTICAS
    DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
    API_BASE_URL = "https://wppagent-production.up.railway.app"
    
    # CREDENCIAIS
    META_ACCESS_TOKEN = "EAAI4WnfpZAe0BPCHbYZAnCAkSMl2vJ3HtGYPAOZCIykNZCFa5Mlv7O8fD5axtHuV8OQT7SA6mPOPxBH7gZBHgQ6Sqx0ZBnwtoYQPGkGdXpdrEyCzFcg1HepawsKUQlPhbu88f4gPcyp7vrbOOIXe34aLZC3uNYFXUHLlRy4hMZApyt3K3uglX1X74gYx3Rd5JbfImIHosIY713hsOMMvQg8sVdOJuThOuZAG4dCyblQmRKAt1MZBDJkv7VOTw5tQZDZD"
    WHATSAPP_PHONE_ID = "728348237027885"
    BOT_PHONE = "15551536026"
    YOUR_PHONE = "5516991022255"
    
    print("📱 Configurações:")
    print(f"   API: {API_BASE_URL}")
    print(f"   Telefone: {YOUR_PHONE} → {BOT_PHONE}")
    print(f"   Phone ID: {WHATSAPP_PHONE_ID}")
    
    # Conectar ao banco
    try:
        db = await asyncpg.connect(DATABASE_URL)
        print("✅ Conectado ao banco PostgreSQL")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False
    
    # Mensagem teste
    message = "Quais serviços vocês oferecem?"
    
    # Webhook payload IDÊNTICO ao comprehensive_bot_test.py
    webhook_url = f"{API_BASE_URL}/webhook"
    
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
                        "id": f"wamid.format_test_{int(time.time())}{random.randint(100,999)}",
                        "timestamp": str(int(time.time())),
                        "text": {"body": message},
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
    
    print(f"📨 Enviando: '{message}'")
    
    # Enviar mensagem
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=webhook_payload, headers=headers, timeout=30) as response:
                if response.status == 200:
                    print("✅ Mensagem enviada com sucesso")
                else:
                    response_text = await response.text()
                    print(f"❌ Falha no webhook: {response.status} - {response_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Erro no envio: {e}")
        return False
    
    # Monitorar resposta IGUAL ao comprehensive_bot_test.py
    print("⏳ Aguardando resposta do bot...")
    await asyncio.sleep(2)  # Esperar processamento
    
    cutoff_time = datetime.now() - timedelta(seconds=30)
    detected_responses = []
    
    for check in range(int(20 / 3)):  # 20 segundos timeout
        try:
            recent_responses = await db.fetch("""
                SELECT direction, content, created_at, message_type
                FROM messages 
                WHERE user_id = 2 
                AND direction = 'out'
                AND created_at > $1
                ORDER BY created_at DESC
            """, cutoff_time)
            
            for msg in recent_responses:
                already_detected = any(
                    resp['timestamp'] == msg['created_at'].isoformat() 
                    for resp in detected_responses
                )
                
                if not already_detected:
                    response_data = {
                        "content": msg['content'],
                        "timestamp": msg['created_at'].isoformat(),
                        "type": msg['message_type'] or 'text'
                    }
                    
                    detected_responses.append(response_data)
                    print(f"🤖 Resposta: {msg['content'][:80]}...")
            
            if detected_responses:
                break
                
            await asyncio.sleep(3)
            
        except Exception as e:
            print(f"❌ Erro no monitoramento: {e}")
            break
    
    await db.close()
    
    # Analisar resposta
    if detected_responses:
        latest_response = detected_responses[0]['content']
        
        print("\n" + "="*60)
        print("🤖 RESPOSTA COMPLETA:")
        print("="*60)
        print(latest_response)
        print("="*60)
        
        # Verificar formatação
        formatting_elements = {
            "💰": "Emoji preço",
            "⏰": "Emoji duração", 
            "📋": "Emoji lista",
            "1.": "Numeração",
            "2.": "Numeração múltipla",
            "*": "Negrito",
            "_": "Itálico",
            "•": "Marcador"
        }
        
        found = []
        missing = []
        
        for element, desc in formatting_elements.items():
            if element in latest_response:
                found.append(f"✅ {desc}")
            else:
                missing.append(f"❌ {desc}")
        
        print(f"\n📊 ANÁLISE DE FORMATAÇÃO:")
        print(f"Encontrados ({len(found)}/{len(formatting_elements)}):")
        for item in found:
            print(f"   {item}")
        
        if missing:
            print(f"\nAusentes:")
            for item in missing:
                print(f"   {item}")
        
        score = (len(found) / len(formatting_elements)) * 100
        print(f"\n🎯 Score: {score:.1f}%")
        
        if score >= 50:
            print("🎉 Formatação funcionando!")
        else:
            print("⚠️ Formatação precisa melhorar")
        
        return score >= 50
    else:
        print("❌ Nenhuma resposta recebida")
        return False

async def main():
    print("🎯 TESTE SIMPLES - Formatação")
    print("=" * 40)
    print("📋 Usando EXATAMENTE a mesma lógica")
    print("🔄 do comprehensive_bot_test.py")
    print("=" * 40)
    
    success = await test_formatting_like_comprehensive()
    
    if success:
        print("\n✅ TESTE CONCLUÍDO COM SUCESSO!")
    else:
        print("\n❌ TESTE DETECTOU PROBLEMAS")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Teste cancelado")
    except Exception as e:
        print(f"\n💥 Erro: {e}")
        import traceback
        traceback.print_exc()

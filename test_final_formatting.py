#!/usr/bin/env python3
"""
🚀 TESTE FINAL - Formatação Após Deploy
=====================================
Aguarda deploy do Railway e testa formatação melhorada
"""

import asyncio
import asyncpg
import aiohttp
import time
import random
from datetime import datetime, timedelta

async def wait_for_deploy(timeout=180):
    """Aguarda deploy do Railway estar disponível"""
    print("⏳ Aguardando deploy do Railway...")
    
    for i in range(timeout // 10):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://wppagent-production.up.railway.app/health", timeout=5) as response:
                    if response.status == 200:
                        print(f"✅ Deploy ativo após {i*10}s")
                        return True
        except:
            pass
        
        if i % 6 == 0:  # A cada minuto
            print(f"⏳ Aguardando... {i*10}s")
        
        await asyncio.sleep(10)
    
    print("⚠️ Timeout aguardando deploy")
    return False

async def test_formatted_response():
    """Testa se a formatação melhorada está funcionando"""
    
    # Configurações (mesma lógica do comprehensive_bot_test.py)
    DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
    API_BASE_URL = "https://wppagent-production.up.railway.app"
    
    # CREDENCIAIS
    META_ACCESS_TOKEN = "EAAI4WnfpZAe0BPCHbYZAnCAkSMl2vJ3HtGYPAOZCIykNZCFa5Mlv7O8fD5axtHuV8OQT7SA6mPOPxBH7gZBHgQ6Sqx0ZBnwtoYQPGkGdXpdrEyCzFcg1HepawsKUQlPhbu88f4gPcyp7vrbOOIXe34aLZC3uNYFXUHLlRy4hMZApyt3K3uglX1X74gYx3Rd5JbfImIHosIY713hsOMMvQg8sVdOJuThOuZAG4dCyblQmRKAt1MZBDJkv7VOTw5tQZDZD"
    WHATSAPP_PHONE_ID = "728348237027885"
    BOT_PHONE = "15551536026"
    YOUR_PHONE = "5516991022255"
    
    # Enviar mensagem teste (usando mesma estrutura do comprehensive_bot_test.py)
    webhook_url = f"{API_BASE_URL}/webhook"
    test_message = "Quais serviços vocês oferecem com preços?"
    
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
                        "id": f"wamid.final_test_{int(time.time())}{random.randint(100,999)}",
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
    
    print(f"📨 Enviando: '{test_message}'")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=webhook_payload, headers=headers, timeout=30) as response:
                if response.status == 200:
                    print("✅ Mensagem enviada!")
                    
                    # Aguardar resposta
                    print("⏳ Aguardando resposta...")
                    await asyncio.sleep(5)
                    
                    # Buscar resposta no banco (mesma lógica do comprehensive_bot_test.py)
                    try:
                        db = await asyncpg.connect(DATABASE_URL)
                        cutoff_time = datetime.now() - timedelta(seconds=30)
                        
                        response_data = await db.fetchrow("""
                            SELECT content, created_at
                            FROM messages 
                            WHERE user_id = 2 
                            AND direction = 'out'
                            AND created_at > $1
                            ORDER BY created_at DESC
                            LIMIT 1
                        """, cutoff_time)
                        
                        await db.close()
                        
                        if response_data:
                            content = response_data['content']
                            print("\n🤖 RESPOSTA RECEBIDA:")
                            print("=" * 60)
                            print(content)
                            print("=" * 60)
                            
                            # Verificar formatação melhorada
                            formatting_checks = {
                                "💰": "Emoji de preço",
                                "⏰": "Emoji de duração", 
                                "📋": "Emoji de lista",
                                "1.": "Numeração ordenada",
                                "*": "Texto em negrito",
                                "_": "Texto em itálico",
                                "•": "Marcadores"
                            }
                            
                            found_elements = []
                            missing_elements = []
                            
                            for element, description in formatting_checks.items():
                                if element in content:
                                    found_elements.append(f"✅ {description}")
                                else:
                                    missing_elements.append(f"❌ {description}")
                            
                            print(f"\n📊 ANÁLISE DE FORMATAÇÃO:")
                            print(f"✅ Elementos encontrados ({len(found_elements)}/{len(formatting_checks)}):")
                            for element in found_elements:
                                print(f"   {element}")
                            
                            if missing_elements:
                                print(f"\n❌ Elementos ausentes:")
                                for element in missing_elements:
                                    print(f"   {element}")
                            
                            # Calcular score
                            score = (len(found_elements) / len(formatting_checks)) * 100
                            
                            print(f"\n🎯 SCORE DE FORMATAÇÃO: {score:.1f}%")
                            
                            if score >= 80:
                                print("🎉 EXCELENTE! Formatação funcionando perfeitamente!")
                            elif score >= 60:
                                print("👍 BOM! Formatação adequada, algumas melhorias possíveis")
                            else:
                                print("⚠️ ATENÇÃO! Formatação precisa de ajustes")
                            
                            return score >= 60
                        else:
                            print("❌ Nenhuma resposta encontrada")
                            return False
                            
                    except Exception as e:
                        print(f"❌ Erro ao verificar resposta: {e}")
                        return False
                else:
                    print(f"❌ Falha no webhook: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

async def main():
    print("🚀 TESTE FINAL - Formatação Após Deploy")
    print("=" * 50)
    print("🎯 Este teste aguardará o deploy do Railway")
    print("📊 e verificará se a formatação melhorada")
    print("✨ está funcionando corretamente")
    print("=" * 50)
    
    # Aguardar deploy
    if not await wait_for_deploy():
        print("❌ Não foi possível verificar o deploy")
        return
    
    # Aguardar mais um pouco para garantir
    print("⏳ Aguardando estabilização do deploy...")
    await asyncio.sleep(30)
    
    # Executar teste
    print("\n🧪 EXECUTANDO TESTE DE FORMATAÇÃO:")
    success = await test_formatted_response()
    
    if success:
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("✅ Formatação melhorada está funcionando")
    else:
        print("\n⚠️ TESTE DETECTOU PROBLEMAS")
        print("🔧 Pode ser necessário verificar logs do Railway")
    
    print("\n📱 Verifique também seu WhatsApp para")
    print("📊 confirmar se a formatação aparece corretamente")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Teste cancelado")
    except Exception as e:
        print(f"\n💥 Erro: {e}")
        import traceback
        traceback.print_exc()

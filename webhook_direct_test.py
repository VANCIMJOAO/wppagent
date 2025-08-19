#!/usr/bin/env python3
"""
🔍 TESTE DIRETO DO WEBHOOK
========================
Testa diretamente o webhook com controle fino sobre os dados
"""

import asyncio
import asyncpg
import aiohttp
import time
import uuid
import json

async def test_webhook_direct():
    """Teste direto do webhook"""
    print("🔍 TESTE DIRETO DO WEBHOOK")
    print("=" * 40)
    
    # Conexão com database
    DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
    API_BASE_URL = "https://wppagent-production.up.railway.app"
    
    db = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Criar telefone único garantido
        timestamp = str(int(time.time()))[-8:]  # 8 dígitos únicos
        unique_id = str(uuid.uuid4())[:6]       # 6 caracteres únicos
        phone = f"5516TEST{timestamp}"[:20]     # Garantir tamanho
        
        print(f"📱 Telefone de teste: {phone}")
        
        # Verificar se telefone já existe
        existing = await db.fetchrow("SELECT id FROM users WHERE wa_id = $1 OR telefone = $1", phone)
        if existing:
            print(f"⚠️ Telefone já existe no DB - ID: {existing['id']}")
            phone = f"5516NEW{timestamp}{unique_id[:2]}"[:20]
            print(f"📱 Novo telefone: {phone}")
        
        # Payload do webhook
        webhook_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "728348237027885",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15551536026",
                            "phone_number_id": "728348237027885"
                        },
                        "messages": [{
                            "from": phone,
                            "id": f"direct_test_{timestamp}",
                            "timestamp": str(int(time.time())),
                            "text": {"body": "Oi! Teste direto do webhook"},
                            "type": "text"
                        }],
                        "contacts": [{
                            "profile": {"name": f"DirectTest{timestamp}"},
                            "wa_id": phone
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        print(f"📤 Enviando webhook...")
        print(f"📋 Payload: {json.dumps(webhook_payload, indent=2)}")
        
        # Enviar webhook
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/webhook",
                json=webhook_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            ) as response:
                status = response.status
                text = await response.text()
                print(f"📥 Webhook response: {status}")
                print(f"📝 Response body: {text}")
        
        # Aguardar e verificar múltiplas vezes
        print(f"\n🔍 Verificando criação do usuário...")
        for attempt in range(10):  # 10 tentativas
            await asyncio.sleep(2)  # Aguardar 2 segundos
            
            user_data = await db.fetchrow("""
                SELECT id, nome, telefone, wa_id, created_at 
                FROM users 
                WHERE wa_id = $1 OR telefone = $1
                ORDER BY created_at DESC 
                LIMIT 1
            """, phone)
            
            if user_data:
                print(f"✅ SUCESSO! Usuário criado na tentativa {attempt + 1}")
                print(f"   👤 ID: {user_data['id']}")
                print(f"   📛 Nome: {user_data['nome']}")
                print(f"   📱 Telefone: {user_data['telefone']}")
                print(f"   📱 WA_ID: {user_data['wa_id']}")
                print(f"   📅 Criado: {user_data['created_at']}")
                
                # Verificar mensagens
                messages = await db.fetch("""
                    SELECT direction, content, created_at 
                    FROM messages m
                    JOIN conversations c ON m.conversation_id = c.id
                    WHERE c.user_id = $1
                    ORDER BY m.created_at ASC
                """, user_data['id'])
                
                print(f"\n💬 Mensagens encontradas: {len(messages)}")
                for i, msg in enumerate(messages, 1):
                    direction_icon = "📤" if msg['direction'] == 'out' else "📥"
                    print(f"   {direction_icon} {i}: {msg['content'][:100]}...")
                
                break
            else:
                print(f"⏳ Tentativa {attempt + 1}/10 - Usuário ainda não encontrado")
        
        if not user_data:
            print("❌ FALHA: Usuário não foi criado após 10 tentativas")
            
            # Debug: verificar últimos usuários criados
            recent = await db.fetch("""
                SELECT id, nome, telefone, wa_id, created_at 
                FROM users 
                WHERE created_at > NOW() - INTERVAL '5 minutes'
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            print(f"\n🔍 DEBUG - Últimos usuários criados (5 min):")
            for user in recent:
                print(f"   👤 ID {user['id']}: {user['telefone']} | {user['nome']} | {user['created_at']}")
        
    except Exception as e:
        print(f"💥 Erro: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(test_webhook_direct())
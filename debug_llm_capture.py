#!/usr/bin/env python3
"""
🔍 DEBUG AVANÇADO - Diagnóstico completo do sistema LLM
===================================================== 
"""

import asyncio
import aiohttp
import asyncpg
import json
import time
import random
import hmac
import hashlib
from datetime import datetime, timezone

RAILWAY_URL = "https://wppagent-production.up.railway.app"
TEST_PHONE = "5516991022255"
WEBHOOK_URL = f"{RAILWAY_URL}/webhook"
DATABASE_URL = 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway'

async def debug_llm_system():
    """Debug completo do sistema LLM"""
    print("🔍 DEBUG AVANÇADO DO SISTEMA LLM")
    print("=" * 50)
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    # 1. Verificar usuário de teste
    print("\n1. 👤 Verificando usuário de teste:")
    user = await conn.fetchrow("""
        SELECT id, wa_id, nome, created_at 
        FROM users 
        WHERE wa_id = $1
    """, TEST_PHONE)
    
    if user:
        print(f"   ✅ Usuário encontrado: ID={{user['id']}}, Nome={{user['nome']}}")
    else:
        print(f"   ❌ Usuário não encontrado")
        await conn.close()
        return
    
    # 2. Verificar conversas
    print("\n2. 💬 Verificando conversas:")
    conversations = await conn.fetch("""
        SELECT id, status, created_at, updated_at, metadata
        FROM conversations 
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 3
    """, user['id'])
    
    for conv in conversations:
        print(f"   📝 Conv {{conv['id']}}: Status={{conv['status']}}, Criada={{conv['created_at'].strftime('%H:%M:%S')}}")
        if conv['metadata']:
            print(f"      Metadata: {{conv['metadata']}}")
    
    if not conversations:
        print("   ❌ Nenhuma conversa encontrada")
        await conn.close()
        return
    
    # 3. Verificar mensagens recentes (últimos 10 minutos)
    print("\n3. 📨 Mensagens recentes (últimos 10 minutos):")
    recent_messages = await conn.fetch("""
        SELECT m.id, m.direction, m.content, m.created_at, m.metadata, c.status as conv_status
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        WHERE m.user_id = $1 
        AND m.created_at > NOW() - INTERVAL '10 minutes'
        ORDER BY m.created_at DESC
        LIMIT 10
    """, user['id'])
    
    for msg in recent_messages:
        direction = "📤" if msg['direction'] == 'in' else "📥"
        content = msg['content'][:60] + "..." if len(msg['content']) > 60 else msg['content']
        status = msg['conv_status']
        metadata = msg['metadata'] or {}
        
        print(f"   {{direction}} {{msg['created_at'].strftime('%H:%M:%S')}} [Conv:{{status}}] {{content}}")
        
        # Mostrar metadata se houver informações relevantes
        if metadata:
            if 'processing_system' in metadata:
                print(f"      🔧 Sistema: {{metadata['processing_system']}}")
            if 'error' in metadata:
                print(f"      ❌ Erro: {{metadata['error']}}")
            if 'llm_confidence' in metadata:
                print(f"      🎯 Confiança: {{metadata['llm_confidence']}}")
    
    # 4. Verificar conversas em modo "human"
    print("\n4. 🙋 Verificando conversas em modo humano:")
    human_convs = await conn.fetch("""
        SELECT id, status, updated_at
        FROM conversations 
        WHERE user_id = $1 AND status = 'human'
    """, user['id'])
    
    if human_convs:
        print(f"   ⚠️ {{len(human_convs)}} conversa(s) em modo humano (bot não responde)")
        for conv in human_convs:
            print(f"      Conv {{conv['id']}}: Atualizada {{conv['updated_at'].strftime('%H:%M:%S')}}")
    else:
        print("   ✅ Nenhuma conversa em modo humano")
    
    # 5. Verificar rate limiting
    print("\n5. ⏱️ Verificando rate limiting:")
    rate_limit_check = await conn.fetchrow("""
        SELECT COUNT(*) as msg_count
        FROM messages 
        WHERE user_id = $1 
        AND direction = 'in'
        AND created_at > NOW() - INTERVAL '1 minute'
    """, user['id'])
    
    print(f"   📊 Mensagens do usuário no último minuto: {{rate_limit_check['msg_count']}}")
    
    # 6. Verificar mensagens com erro
    print("\n6. ❌ Verificando mensagens com erro:")
    error_messages = await conn.fetch("""
        SELECT m.id, m.content, m.created_at, m.metadata
        FROM messages m
        WHERE m.user_id = $1 
        AND m.metadata::text LIKE '%error%'
        ORDER BY m.created_at DESC
        LIMIT 5
    """, user['id'])
    
    if error_messages:
        print(f"   🚨 {{len(error_messages)}} mensagem(s) com erro encontrada(s):")
        for msg in error_messages:
            print(f"      {{msg['created_at'].strftime('%H:%M:%S')}}: {{msg['metadata']}}")
    else:
        print("   ✅ Nenhuma mensagem com erro")
    
    await conn.close()
    
    # 7. Testar endpoint específico
    print("\n7. 🔗 Testando endpoints específicos:")
    
    endpoints_to_test = [
        ("/health", "Status geral"),
        ("/api/health", "Health API"),
        ("/api/status", "Status detalhado")
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint, description in endpoints_to_test:
            try:
                async with session.get(f"{RAILWAY_URL}{{endpoint}}", timeout=10) as response:
                    status = response.status
                    try:
                        data = await response.json()
                        print(f"   ✅ {{description}}: {{status}} - {{data}}")
                    except:
                        text = await response.text()
                        print(f"   ✅ {{description}}: {{status}} - {{text[:100]}}...")
            except Exception as e:
                print(f"   ❌ {{description}}: Erro - {{e}}")

if __name__ == "__main__":
    asyncio.run(debug_llm_system())import asyncio
import aiohttp
import asyncpg
import json
import time
import random
import hmac
import hashlib
from datetime import datetime, timezone

RAILWAY_URL = "https://wppagent-production.up.railway.app"
TEST_PHONE = "5516991022255"
WEBHOOK_URL = f"{RAILWAY_URL}/webhook"
DATABASE_URL = 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway'

async def test_single_message():
    """Teste com uma única mensagem para debug"""
    async with aiohttp.ClientSession() as session:
        
        # 1. Enviar uma mensagem
        logger.info("📤 Enviando mensagem de teste...")
        async with session.post(
            f"{RAILWAY_URL}/webhook/test-send",
            params={
                "phone_number": TEST_PHONE,
                "message": "Olá! Teste de captura de resposta"
            }
        ) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"✅ Mensagem enviada: {data}")
                
                if data.get('success') and 'api_response' in data:
                    msg_id = data['api_response']['messages'][0]['id']
                    logger.info(f"🆔 Message ID: {msg_id}")
            else:
                logger.error(f"❌ Erro ao enviar: {response.status}")
                return
        
        # 2. Aguardar um pouco
        logger.info("⏳ Aguardando 10s para processamento...")
        await asyncio.sleep(10)
        
        # 3. Verificar endpoints de forma detalhada
        logger.info("🔍 Verificando endpoint de flow da conversa...")
        async with session.get(f"{RAILWAY_URL}/conversation/flow/{TEST_PHONE}") as response:
            logger.info(f"Flow Status: {response.status}")
            if response.status == 200:
                flow_data = await response.json()
                logger.info(f"Flow Data: {json.dumps(flow_data, indent=2, ensure_ascii=False)[:500]}")
        
        logger.info("🔍 Verificando analytics LLM...")
        async with session.get(f"{RAILWAY_URL}/llm/analytics") as response:
            logger.info(f"LLM Analytics Status: {response.status}")
            if response.status == 200:
                llm_data = await response.json()
                logger.info(f"LLM Data: {json.dumps(llm_data, indent=2, ensure_ascii=False)[:500]}")
        
        logger.info("🔍 Verificando analytics de conversas...")
        async with session.get(f"{RAILWAY_URL}/conversation/analytics") as response:
            logger.info(f"Conversation Analytics Status: {response.status}")
            if response.status == 200:
                conv_data = await response.json()
                logger.info(f"Conversation Data: {json.dumps(conv_data, indent=2, ensure_ascii=False)[:500]}")
        
        logger.info("🔍 Verificando analytics específicas do usuário...")
        async with session.get(f"{RAILWAY_URL}/llm/conversations/{TEST_PHONE}/analytics") as response:
            logger.info(f"User Analytics Status: {response.status}")
            if response.status == 200:
                user_data = await response.json()
                logger.info(f"User Data: {json.dumps(user_data, indent=2, ensure_ascii=False)[:500]}")

if __name__ == "__main__":
    asyncio.run(test_single_message())

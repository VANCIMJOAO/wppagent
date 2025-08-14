#!/usr/bin/env python3
"""
🔍 MONITOR TEMPO REAL - Monitorar resposta LLM
===========================================
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

async def send_message_and_monitor():
    """Envia mensagem e monitora resposta"""
    
    # 1. Enviar mensagem
    message = f"Teste de monitoramento {int(time.time())}"
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
                            "name": "João Monitor"
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
    
    print(f"📤 Enviando: {message}")
    
    # Conectar ao banco antes de enviar
    conn = await asyncpg.connect(DATABASE_URL)
    
    # Obter contagem inicial
    initial_count = await conn.fetchval("""
        SELECT COUNT(*) FROM messages m 
        JOIN users u ON m.user_id = u.id 
        WHERE u.wa_id = $1
    """, TEST_PHONE)
    
    print(f"📊 Mensagens iniciais: {initial_count}")
    
    # Enviar mensagem
    async with aiohttp.ClientSession() as session:
        async with session.post(
            WEBHOOK_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "WhatsApp/2.0",
                "X-Hub-Signature-256": f"sha256={signature}"
            }
        ) as response:
            status = response.status
            print(f"📨 Status: {status}")
    
    if status != 200:
        print("❌ Falha no envio")
        await conn.close()
        return
    
    # Monitorar por 60 segundos
    print("🔍 Monitorando respostas...")
    
    for i in range(60):
        await asyncio.sleep(1)
        
        # Verificar novas mensagens
        current_count = await conn.fetchval("""
            SELECT COUNT(*) FROM messages m 
            JOIN users u ON m.user_id = u.id 
            WHERE u.wa_id = $1
        """, TEST_PHONE)
        
        new_messages = current_count - initial_count
        
        if new_messages > 1:  # Mais que a mensagem enviada
            # Buscar mensagens recentes
            recent = await conn.fetch("""
                SELECT m.direction, m.content, m.created_at
                FROM messages m
                JOIN users u ON m.user_id = u.id
                WHERE u.wa_id = $1 
                ORDER BY m.created_at DESC
                LIMIT 5
            """, TEST_PHONE)
            
            print(f"\n✅ {new_messages} novas mensagens detectadas!")
            for msg in recent:
                direction = "📤" if msg['direction'] == 'in' else "📥"
                content = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
                print(f"{direction} {msg['created_at'].strftime('%H:%M:%S')} - {content}")
            break
        
        if i % 10 == 0:
            print(f"⏳ {i}s - Aguardando resposta...")
    
    else:
        print("❌ Nenhuma resposta detectada em 60 segundos")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(send_message_and_monitor())

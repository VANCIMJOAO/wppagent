#!/usr/bin/env python3
"""
🔍 ANÁLISE COMPLETA - Verificar todas as mensagens do teste
========================================================
"""

import asyncio
import asyncpg
from datetime import datetime, timezone

DATABASE_URL = 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway'
TEST_PHONE = "5516991022255"

async def analyze_test_messages():
    """Analisa todas as mensagens do teste"""
    print("🔍 ANÁLISE COMPLETA DAS MENSAGENS DO TESTE")
    print("=" * 55)
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    # 1. Buscar todas as mensagens dos últimos 30 minutos
    messages = await conn.fetch("""
        SELECT m.id, m.direction, m.content, m.created_at, c.status as conv_status
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        JOIN users u ON m.user_id = u.id
        WHERE u.wa_id = $1 
        AND m.created_at > NOW() - INTERVAL '30 minutes'
        ORDER BY m.created_at ASC
    """, TEST_PHONE)
    
    print(f"📊 Total de mensagens dos últimos 30 min: {len(messages)}")
    
    # Separar por direção
    incoming = [m for m in messages if m['direction'] == 'in']
    outgoing = [m for m in messages if m['direction'] == 'out']
    
    print(f"📤 Mensagens enviadas (in): {len(incoming)}")
    print(f"📥 Respostas LLM (out): {len(outgoing)}")
    print(f"📈 Taxa de resposta: {len(outgoing)}/{len(incoming)} = {(len(outgoing)/len(incoming)*100) if incoming else 0:.1f}%")
    
    print(f"\n🔍 ANÁLISE DETALHADA:")
    print("-" * 80)
    
    # Agrupar mensagens em pares
    current_time = None
    waiting_for_response = []
    
    for msg in messages:
        direction = "📤" if msg['direction'] == 'in' else "📥"
        time_str = msg['created_at'].strftime('%H:%M:%S')
        content = msg['content'][:60] + "..." if len(msg['content']) > 60 else msg['content']
        
        print(f"{direction} {time_str} [{msg['conv_status']}] {content}")
        
        if msg['direction'] == 'in':
            waiting_for_response.append(msg)
        elif msg['direction'] == 'out' and waiting_for_response:
            # Encontrou uma resposta
            req_msg = waiting_for_response.pop(0)
            time_diff = (msg['created_at'] - req_msg['created_at']).total_seconds()
            print(f"   ⏱️ Tempo de resposta: {time_diff:.1f}s")
    
    # Mensagens sem resposta
    if waiting_for_response:
        print(f"\n❌ MENSAGENS SEM RESPOSTA: {len(waiting_for_response)}")
        for msg in waiting_for_response:
            time_str = msg['created_at'].strftime('%H:%M:%S')
            content = msg['content'][:60] + "..." if len(msg['content']) > 60 else msg['content']
            print(f"   📤 {time_str} - {content}")
    
    # 2. Verificar status da conversa atual
    print(f"\n📝 STATUS DA CONVERSA:")
    conversation = await conn.fetchrow("""
        SELECT c.id, c.status, c.updated_at
        FROM conversations c
        JOIN users u ON c.user_id = u.id
        WHERE u.wa_id = $1
        ORDER BY c.updated_at DESC
        LIMIT 1
    """, TEST_PHONE)
    
    if conversation:
        print(f"   ID: {conversation['id']}")
        print(f"   Status: {conversation['status']}")
        print(f"   Última atualização: {conversation['updated_at'].strftime('%H:%M:%S')}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(analyze_test_messages())

#!/usr/bin/env python3
"""
🔍 DEBUG - Verificar mensagens em tempo real
===========================================
"""

import asyncio
import asyncpg
from datetime import datetime, timezone

DATABASE_URL = 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway'
TEST_PHONE = "5516991022255"

async def check_recent_messages():
    """Verifica mensagens recentes"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    # Buscar mensagens dos últimos 5 minutos
    messages = await conn.fetch("""
        SELECT m.id, m.direction, m.content, m.created_at
        FROM messages m
        JOIN users u ON m.user_id = u.id
        WHERE u.wa_id = $1 
        AND m.created_at > NOW() - INTERVAL '5 minutes'
        ORDER BY m.created_at DESC
        LIMIT 20
    """, TEST_PHONE)
    
    print(f"🔍 Mensagens dos últimos 5 minutos: {len(messages)}")
    
    for msg in messages:
        direction = "📤" if msg['direction'] == 'in' else "📥"
        content = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
        print(f"{direction} {msg['created_at'].strftime('%H:%M:%S')} - {content}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_recent_messages())

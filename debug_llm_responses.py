#!/usr/bin/env python3
"""
🔍 DEBUG - Verificação específica de respostas LLM
=================================================
"""

import asyncio
import asyncpg
from datetime import datetime, timezone

async def debug_llm_responses():
    """Verifica especificamente as respostas da LLM"""
    print("🤖 DEBUGANDO RESPOSTAS LLM ESPECÍFICAS")
    print("=" * 50)
    
    conn = await asyncpg.connect('postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway')
    
    # Buscar respostas LLM (direção 'out')
    responses = await conn.fetch("""
        SELECT m.id, m.direction, m.content, m.created_at
        FROM messages m
        JOIN users u ON m.user_id = u.id
        WHERE u.wa_id = $1 AND m.direction = 'out'
        ORDER BY m.created_at DESC
        LIMIT 20
    """, "5516991022255")
    
    print(f"🤖 Encontradas {len(responses)} respostas LLM:")
    print()
    
    for i, resp in enumerate(responses, 1):
        print(f"{i:2d}. 📥 {resp['created_at'].strftime('%H:%M:%S')}")
        print(f"    {resp['content']}")
        print()
    
    # Verificar pares entrada-saída recentes
    print("🔄 ANÁLISE DE PARES ENTRADA-SAÍDA (últimas 10):")
    print("=" * 50)
    
    all_messages = await conn.fetch("""
        SELECT m.id, m.direction, m.content, m.created_at
        FROM messages m
        JOIN users u ON m.user_id = u.id
        WHERE u.wa_id = $1
        ORDER BY m.created_at DESC
        LIMIT 20
    """, "5516991022255")
    
    for i in range(0, min(len(all_messages)-1, 10), 2):
        if i+1 < len(all_messages):
            msg1 = all_messages[i]
            msg2 = all_messages[i+1]
            
            time_diff = abs((msg1['created_at'] - msg2['created_at']).total_seconds())
            
            print(f"Par {i//2 + 1}:")
            print(f"  📤 {msg2['created_at'].strftime('%H:%M:%S')} - {msg2['content'][:50]}...")
            print(f"  📥 {msg1['created_at'].strftime('%H:%M:%S')} - {msg1['content'][:50]}...")
            print(f"  ⏱️ Diferença: {time_diff:.1f}s")
            print()
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(debug_llm_responses())

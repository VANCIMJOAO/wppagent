#!/usr/bin/env python3
"""
🔍 DEBUG - Verificação de mensagens LLM
=========================================
Script para verificar se as respostas LLM estão sendo salvas no banco
"""

import asyncio
import asyncpg
from datetime import datetime, timezone

async def debug_llm_messages():
    """Verifica mensagens no banco de dados"""
    print("🔍 DEBUGANDO CAPTURA DE RESPOSTAS LLM")
    print("=" * 50)
    
    conn = await asyncpg.connect('postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway')
    
    # Verificar se usuário existe
    user = await conn.fetchrow(
        "SELECT id, wa_id, nome FROM users WHERE wa_id = $1", 
        "5516991022255"
    )
    
    if user:
        print(f"✅ Usuário encontrado: {user['nome']} (ID: {user['id']})")
    else:
        print("❌ Usuário não encontrado!")
        await conn.close()
        return
    
    # Verificar últimas mensagens
    print("\n📋 Últimas 15 mensagens:")
    messages = await conn.fetch("""
        SELECT m.id, m.direction, m.content, m.created_at
        FROM messages m
        WHERE m.user_id = $1
        ORDER BY m.created_at DESC
        LIMIT 15
    """, user['id'])
    
    in_count = 0
    out_count = 0
    
    for i, msg in enumerate(messages, 1):
        direction_icon = "📤" if msg['direction'] == 'in' else "📥"
        direction_text = "ENTRADA" if msg['direction'] == 'in' else "SAÍDA"
        
        if msg['direction'] == 'in':
            in_count += 1
        else:
            out_count += 1
            
        print(f"{i:2d}. {direction_icon} [{direction_text}] {msg['created_at'].strftime('%H:%M:%S')}")
        print(f"    {msg['content'][:80]}...")
        print()
    
    print(f"📊 Resumo: {in_count} entradas, {out_count} saídas")
    
    # Verificar mensagens recentes (últimos 30 minutos)
    print("\n🕐 Mensagens dos últimos 30 minutos:")
    recent_messages = await conn.fetch("""
        SELECT m.id, m.direction, m.content, m.created_at
        FROM messages m
        WHERE m.user_id = $1 
        AND m.created_at > NOW() - INTERVAL '30 minutes'
        ORDER BY m.created_at DESC
    """, user['id'])
    
    if recent_messages:
        recent_in = sum(1 for msg in recent_messages if msg['direction'] == 'in')
        recent_out = sum(1 for msg in recent_messages if msg['direction'] == 'out')
        print(f"📊 Mensagens recentes: {recent_in} entradas, {recent_out} saídas")
        
        # Mostrar as últimas 5
        for msg in recent_messages[:5]:
            direction_icon = "📤" if msg['direction'] == 'in' else "📥"
            print(f"{direction_icon} {msg['created_at'].strftime('%H:%M:%S')} - {msg['content'][:60]}...")
    else:
        print("❌ Nenhuma mensagem recente encontrada")
    
    await conn.close()
    print("\n🔍 Debug concluído!")

if __name__ == "__main__":
    asyncio.run(debug_llm_messages())

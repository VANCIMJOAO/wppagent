#!/usr/bin/env python3
"""
🔧 FIX CONVERSA - Corrigir status da conversa
==========================================
"""

import asyncio
import asyncpg

DATABASE_URL = 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway'
TEST_PHONE = "5516991022255"

async def fix_conversation_status():
    """Corrige o status da conversa para active"""
    print("🔧 CORRIGINDO STATUS DA CONVERSA")
    print("=" * 40)
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    # 1. Verificar usuário
    user = await conn.fetchrow("""
        SELECT id, wa_id, nome 
        FROM users 
        WHERE wa_id = $1
    """, TEST_PHONE)
    
    if not user:
        print("❌ Usuário não encontrado")
        await conn.close()
        return
    
    print(f"✅ Usuário: {user['nome']} (ID: {user['id']})")
    
    # 2. Verificar conversas
    conversations = await conn.fetch("""
        SELECT id, status 
        FROM conversations 
        WHERE user_id = $1
    """, user['id'])
    
    print(f"📊 Conversas encontradas: {len(conversations)}")
    
    for conv in conversations:
        print(f"   Conv {conv['id']}: Status = {conv['status']}")
        
        if conv['status'] == 'human':
            print(f"   🔄 Alterando conversa {conv['id']} para 'active'...")
            
            # Atualizar status
            await conn.execute("""
                UPDATE conversations 
                SET status = 'active', updated_at = NOW() 
                WHERE id = $1
            """, conv['id'])
            
            print(f"   ✅ Conversa {conv['id']} alterada para 'active'")
    
    await conn.close()
    print("\n🎉 Status das conversas corrigido!")
    print("💡 Agora o bot voltará a responder automaticamente")

if __name__ == "__main__":
    asyncio.run(fix_conversation_status())

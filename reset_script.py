import asyncio
import asyncpg
from datetime import datetime

async def reset_conversation_mode():
    """Reset direto no PostgreSQL do Railway"""
    
    DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
    
    try:
        print("🔗 Conectando ao banco PostgreSQL...")
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Conectado com sucesso!")
        
        # 1. Verificar status atual
        print("\n📊 Verificando status atual...")
        current_status = await conn.fetchrow("""
            SELECT c.id, c.status, c.last_message_at, u.wa_id, u.nome
            FROM conversations c
            JOIN users u ON c.user_id = u.id
            WHERE u.wa_id = $1
            ORDER BY c.created_at DESC
            LIMIT 1
        """, "5516991022255")
        
        if current_status:
            print(f"📱 Usuário: {current_status['wa_id']} ({current_status['nome']})")
            print(f"🔄 Status atual: {current_status['status']}")
            print(f"⏰ Última mensagem: {current_status['last_message_at']}")
        else:
            print("❌ Conversa não encontrada!")
            return
        
        # 2. Resetar para modo bot
        print("\n🔧 Resetando conversa para modo 'active'...")
        result = await conn.execute("""
            UPDATE conversations 
            SET status = 'active', 
                updated_at = $1,
                last_message_at = $1
            WHERE user_id = (
                SELECT id FROM users WHERE wa_id = $2
            )
        """, datetime.utcnow(), "5516991022255")
        
        print(f"✅ Conversa resetada! Comando executado: {result}")
        
        # 3. Verificar se funcionou
        print("\n🔍 Verificando após reset...")
        new_status = await conn.fetchrow("""
            SELECT c.id, c.status, c.updated_at, u.wa_id
            FROM conversations c
            JOIN users u ON c.user_id = u.id
            WHERE u.wa_id = $1
            ORDER BY c.created_at DESC
            LIMIT 1
        """, "5516991022255")
        
        if new_status:
            print(f"📊 Novo status: {new_status['status']}")
            print(f"⏰ Atualizado em: {new_status['updated_at']}")
            
            if new_status['status'] == 'active':
                print("🎉 SUCESSO! Conversa agora está em modo BOT!")
            else:
                print(f"⚠️ Status ainda é: {new_status['status']}")
        
        await conn.close()
        print("\n🔌 Conexão fechada.")
        
        return new_status['status'] if new_status else None
        
    except Exception as e:
        print(f"❌ Erro ao conectar/executar: {e}")
        return None

# Executar o reset
if __name__ == "__main__":
    print("🚨 RESET DO MODO DA CONVERSA")
    print("=" * 40)
    
    result = asyncio.run(reset_conversation_mode())
    
    print("\n" + "=" * 40)
    if result == 'active':
        print("✅ PROBLEMA RESOLVIDO!")
        print("📱 Agora teste enviando 'Oi' no WhatsApp")
        print("🤖 O bot deve responder automaticamente!")
    else:
        print("❌ Algo ainda não está certo.")
        print("🔄 Tente a solução manual no Railway Dashboard")
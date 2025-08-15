#!/usr/bin/env python3
"""
👀 MONITOR - Respostas do Bot
============================
Monitora as últimas respostas do bot para verificar formatação
"""

import asyncio
import asyncpg
from datetime import datetime, timedelta

async def monitor_bot_responses():
    """Monitora últimas respostas do bot"""
    
    DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
    
    try:
        db = await asyncpg.connect(DATABASE_URL)
        print("✅ Conectado ao banco")
        
        # Buscar últimas 3 respostas do bot
        cutoff_time = datetime.now() - timedelta(minutes=10)
        
        responses = await db.fetch("""
            SELECT content, created_at, message_type
            FROM messages 
            WHERE user_id = 2 
            AND direction = 'out'
            AND created_at > $1
            ORDER BY created_at DESC
            LIMIT 3
        """, cutoff_time)
        
        print(f"\n📋 ÚLTIMAS {len(responses)} RESPOSTAS DO BOT:")
        print("=" * 60)
        
        for i, response in enumerate(responses, 1):
            print(f"\n🤖 RESPOSTA {i}:")
            print(f"⏰ {response['created_at']}")
            print(f"📄 Tipo: {response['message_type'] or 'text'}")
            print(f"📝 Conteúdo:")
            print("-" * 40)
            print(response['content'])
            print("-" * 40)
            
            # Verificar elementos de formatação
            content = response['content']
            formatting_elements = {
                "💰": "Emoji preço" if "💰" in content else None,
                "⏰": "Emoji duração" if "⏰" in content else None,
                "📋": "Emoji lista" if "📋" in content else None,
                "1.": "Numeração" if "1." in content else None,
                "*": "Negrito" if "*" in content else None,
                "_": "Itálico" if "_" in content else None,
            }
            
            found_elements = [desc for desc in formatting_elements.values() if desc]
            
            if found_elements:
                print(f"✅ Formatação encontrada: {', '.join(found_elements)}")
            else:
                print("⚠️ Nenhum elemento de formatação detectado")
        
        await db.close()
        print("\n✅ Monitoramento concluído")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

async def main():
    print("👀 MONITOR - Respostas do Bot")
    print("=" * 40)
    print("🔍 Verificando últimas respostas para")
    print("📊 validar formatação implementada")
    print("=" * 40)
    
    await monitor_bot_responses()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Monitoramento cancelado")
    except Exception as e:
        print(f"\n💥 Erro: {e}")

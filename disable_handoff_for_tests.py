#!/usr/bin/env python3
"""
🔧 Desabilitar Handoff Temporariamente para Testes
"""

import asyncio
import asyncpg
import os
from datetime import datetime

DATABASE_URL = 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway'

async def disable_handoff_for_tests():
    """Desabilita handoff para permitir testes da LLM"""
    print("🔧 DESABILITANDO HANDOFF PARA TESTES")
    print("=" * 40)
    
    try:
        # Conectar ao banco
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Conectado ao banco de dados")
        
        # 1. Corrigir todas as conversas para 'active'
        result = await conn.execute("""
            UPDATE conversations 
            SET status = 'active', updated_at = $1
            WHERE status = 'human'
        """, datetime.utcnow())
        
        affected = result.split()[-1] if result else "0"
        print(f"🔄 Conversas corrigidas: {affected}")
        
        # 2. Verificar status atual
        conversations = await conn.fetch("""
            SELECT id, user_id, status, created_at 
            FROM conversations 
            ORDER BY updated_at DESC 
            LIMIT 5
        """)
        
        print(f"\n📊 Status atual das conversas:")
        for conv in conversations:
            print(f"   Conv {conv['id']}: Status={conv['status']}")
        
        # 3. Limpar logs de handoff se existirem
        try:
            await conn.execute("DELETE FROM handoff_logs WHERE created_at > NOW() - INTERVAL '1 hour'")
            print("🧹 Logs de handoff recentes limpos")
        except:
            print("ℹ️ Tabela handoff_logs não existe (OK)")
        
        await conn.close()
        
        print("\n🎉 HANDOFF DESABILITADO TEMPORARIAMENTE")
        print("💡 Agora você pode testar sem interferência do handoff automático")
        print("⚠️ Para testes de produção, reative o handoff depois")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    asyncio.run(disable_handoff_for_tests())

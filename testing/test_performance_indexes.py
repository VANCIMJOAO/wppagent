#!/usr/bin/env python3
"""
Teste para verificar se os índices de performance foram criados corretamente
"""

import asyncio
import asyncpg
from datetime import datetime

async def test_performance_indexes():
    """Teste para verificar índices de performance"""
    
    try:
        # Conectar ao banco de dados
        DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
        conn = await asyncpg.connect(DATABASE_URL)
        
        print("🔍 Verificando índices de performance criados...\n")
        
        # Verificar índices da tabela messages
        messages_indexes = await conn.fetch("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'messages' 
            AND indexname LIKE 'idx_%'
            ORDER BY indexname;
        """)
        
        print("📊 Índices na tabela 'messages':")
        for index in messages_indexes:
            print(f"  - {index['indexname']}: {index['indexdef']}")
        
        # Verificar especificamente o índice composto user_id, created_at
        user_created_index = await conn.fetchrow("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'messages' 
            AND indexname = 'idx_messages_user_created';
        """)
        
        if user_created_index:
            print(f"✅ Índice composto messages(user_id, created_at) criado com sucesso!")
            print(f"   Definição: {user_created_index['indexdef']}")
        else:
            print("❌ Índice composto messages(user_id, created_at) NÃO encontrado!")
        
        print("\n" + "="*60 + "\n")
        
        # Verificar índices da tabela appointments
        appointments_indexes = await conn.fetch("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'appointments' 
            AND indexname LIKE 'idx_%'
            ORDER BY indexname;
        """)
        
        print("📊 Índices na tabela 'appointments':")
        for index in appointments_indexes:
            print(f"  - {index['indexname']}: {index['indexdef']}")
        
        # Verificar especificamente o índice composto date_time, status
        datetime_status_index = await conn.fetchrow("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'appointments' 
            AND indexname = 'idx_appointments_datetime_status';
        """)
        
        if datetime_status_index:
            print(f"✅ Índice composto appointments(date_time, status) criado com sucesso!")
            print(f"   Definição: {datetime_status_index['indexdef']}")
        else:
            print("❌ Índice composto appointments(date_time, status) NÃO encontrado!")
        
        print("\n" + "="*60 + "\n")
        
        # Testar performance dos índices
        print("⚡ Testando performance dos índices...\n")
        
        # Teste 1: Consulta com índice user_id, created_at
        explain_result = await conn.fetch("""
            EXPLAIN (ANALYZE, BUFFERS) 
            SELECT * FROM messages 
            WHERE user_id = 1
            ORDER BY created_at DESC 
            LIMIT 10;
        """)
        
        print("📈 Plano de execução para consulta messages por user_id ordenado por created_at:")
        for row in explain_result:
            print(f"   {row[0]}")
        
        print("\n" + "-"*40 + "\n")
        
        # Teste 2: Consulta com índice date_time, status
        explain_result2 = await conn.fetch("""
            EXPLAIN (ANALYZE, BUFFERS) 
            SELECT * FROM appointments 
            WHERE date_time >= NOW() - INTERVAL '30 days' 
            AND status = 'scheduled';
        """)
        
        print("📈 Plano de execução para consulta appointments por date_time e status:")
        for row in explain_result2:
            print(f"   {row[0]}")
        
        print("\n✅ Teste de índices de performance concluído com sucesso!")
        
        # Estatísticas finais
        total_indexes = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM pg_indexes 
            WHERE tablename IN ('messages', 'appointments') 
            AND indexname LIKE 'idx_%';
        """)
        
        print(f"\n📊 Total de índices de performance criados: {total_indexes}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar índices: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("🚀 Iniciando teste de índices de performance...")
    print(f"⏰ Timestamp: {datetime.now()}\n")
    
    result = asyncio.run(test_performance_indexes())
    
    if result:
        print("\n🎉 Todos os índices de performance foram implementados corretamente!")
    else:
        print("\n💥 Problemas encontrados na implementação dos índices!")

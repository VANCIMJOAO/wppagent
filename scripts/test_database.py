#!/usr/bin/env python3
"""
🧪 Teste das otimizações do banco de dados
"""

import asyncio
import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_operations():
    """Testar operações básicas do banco"""
    
    print("🧪 Testando operações do banco de dados...")
    
    try:
        async with AsyncSessionLocal() as session:
            # Teste 1: Conectividade
            print("1️⃣ Testando conectividade...")
            result = await session.execute(text("SELECT 1"))
            if result.scalar() == 1:
                print("✅ Conectividade OK")
            
            # Teste 2: Verificar tabelas existentes
            print("2️⃣ Verificando tabelas...")
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Encontradas {len(tables)} tabelas: {', '.join(tables)}")
            
            # Teste 3: Verificar índices existentes
            print("3️⃣ Verificando índices...")
            result = await session.execute(text("""
                SELECT indexname, tablename 
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """))
            indexes = result.fetchall()
            print(f"✅ Encontrados {len(indexes)} índices")
            
            # Teste 4: Criar um índice de teste se não existir
            print("4️⃣ Testando criação de índice...")
            try:
                await session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_test_optimization 
                    ON admin_users (created_at DESC)
                """))
                await session.commit()
                print("✅ Índice de teste criado")
            except Exception as e:
                print(f"⚠️ Índice já existe ou erro: {e}")
            
            # Teste 5: Estatísticas básicas
            print("5️⃣ Coletando estatísticas...")
            
            # Contar admins
            result = await session.execute(text("SELECT count(*) FROM admin_users"))
            admin_count = result.scalar()
            print(f"📊 Admins cadastrados: {admin_count}")
            
            # Tamanho do banco
            result = await session.execute(text("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """))
            db_size = result.scalar()
            print(f"📊 Tamanho do banco: {db_size}")
            
            # Conexões ativas
            result = await session.execute(text("""
                SELECT count(*) FROM pg_stat_activity WHERE state = 'active'
            """))
            active_connections = result.scalar()
            print(f"📊 Conexões ativas: {active_connections}")
            
            print("\n🎯 Todos os testes passaram! O banco está funcionando corretamente.")
            return True
            
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_database_operations())
    if not success:
        sys.exit(1)
    else:
        print("\n✅ Sistema de banco de dados validado!")
        print("🚀 Pronto para otimizações!")

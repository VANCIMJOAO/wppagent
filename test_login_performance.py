#!/usr/bin/env python3
"""
Teste de performance do endpoint de login
"""

import asyncio
import time
import os
import sys
import httpx

# Configurar variáveis de ambiente
os.environ["DATABASE_URL"] = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
os.environ["REDIS_URL"] = "redis://default:SvSHiMNuuQEtmIUgGIEGqPpXsdZeInDG@yamanote.proxy.rlwy.net:14106"

# Adicionar o diretório do projeto ao path
sys.path.insert(0, "/home/vancim/whats_agent")

async def test_login_performance():
    """Testar performance do endpoint de login"""
    
    # Dados de teste
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    print("🚀 Testando performance do endpoint /admin/login...")
    
    # Testar múltiplas requisições
    times = []
    async with httpx.AsyncClient() as client:
        for i in range(5):
            start_time = time.time()
            
            try:
                response = await client.post(
                    "http://localhost:8000/admin/login",
                    json=login_data,
                    timeout=10.0
                )
                
                end_time = time.time()
                duration = end_time - start_time
                times.append(duration)
                
                print(f"  Teste {i+1}: {duration:.6f}s - Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"    ✅ Login bem-sucedido")
                else:
                    print(f"    ❌ Erro: {response.text}")
                    
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                times.append(duration)
                print(f"  Teste {i+1}: {duration:.6f}s - ❌ Erro: {e}")
    
    # Calcular estatísticas
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n📊 Estatísticas de Performance:")
        print(f"  - Tempo médio: {avg_time:.6f}s")
        print(f"  - Tempo mínimo: {min_time:.6f}s")
        print(f"  - Tempo máximo: {max_time:.6f}s")
        print(f"  - Meta: <1.0s")
        
        if avg_time > 1.0:
            print(f"  ⚠️ PERFORMANCE ACIMA DO LIMITE!")
        else:
            print(f"  ✅ Performance dentro do limite")
    
    return times

async def test_database_queries():
    """Testar performance das queries de banco"""
    print("\n🔍 Testando performance das queries de banco...")
    
    from app.database import AsyncSessionLocal
    from app.models.database import AdminUser
    from sqlalchemy import select
    from app.routes.admin_auth import verify_password
    
    async with AsyncSessionLocal() as session:
        # Teste 1: Busca por username
        start_time = time.time()
        result = await session.execute(
            select(AdminUser).where(AdminUser.username == "admin")
        )
        admin_user = result.scalar_one_or_none()
        end_time = time.time()
        
        print(f"  Query 1 - Busca por username: {end_time - start_time:.6f}s")
        
        if admin_user:
            # Teste 2: Verificação de senha
            start_time = time.time()
            password_ok = verify_password("admin123", admin_user.password_hash)
            end_time = time.time()
            
            print(f"  Query 2 - Verificação de senha: {end_time - start_time:.6f}s")
            print(f"  Senha válida: {password_ok}")

if __name__ == "__main__":
    asyncio.run(test_login_performance())
    asyncio.run(test_database_queries())

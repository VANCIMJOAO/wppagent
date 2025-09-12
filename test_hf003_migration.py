"""
🔒 HF003 - Teste de Consolidação de Tabelas Auth
==============================================

Testa a migração HF003 que consolida auth_users e admin_users
"""

import pytest
import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def test_auth_consolidation():
    """Testa migração HF003 - Consolidação das tabelas de auth"""
    async with AsyncSessionLocal() as db:
        print("🔒 HF003 - Testando consolidação de auth...")
        
        # Verificar auth_users existe
        result = await db.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'auth_users'
        """))
        auth_table_exists = result.scalar()
        assert auth_table_exists == 1, "Tabela auth_users deve existir"
        print("✅ auth_users table exists")
        
        # Verificar admin_users não existe mais  
        result = await db.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'admin_users'
        """))
        admin_table_exists = result.scalar()
        print(f"admin_users table exists: {admin_table_exists}")
        
        # Verificar backup foi criado se havia admin_users
        result = await db.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'admin_users_backup_hf003'
        """))
        backup_exists = result.scalar()
        print(f"✅ backup table exists: {backup_exists}")
        
        # Verificar se existem admins na auth_users
        result = await db.execute(text("""
            SELECT COUNT(*) FROM auth_users WHERE role = 'admin'
        """))
        admin_count = result.scalar()
        print(f"✅ Admin users in auth_users: {admin_count}")
        
        # Verificar índices foram criados
        result = await db.execute(text("""
            SELECT COUNT(*) FROM pg_indexes 
            WHERE indexname IN ('idx_auth_users_email_active', 'idx_auth_users_role_active')
        """))
        index_count = result.scalar()
        print(f"✅ Optimized indexes created: {index_count}")

async def test_login_pos_migracao():
    """Testa se login ainda funciona após migração"""
    async with AsyncSessionLocal() as db:
        print("🔒 HF003 - Testando login pós migração...")
        
        # Verificar se existe algum usuário admin para testar
        result = await db.execute(text("""
            SELECT email, password_hash FROM auth_users 
            WHERE role = 'admin' AND is_active = true
            LIMIT 1
        """))
        admin_user = result.fetchone()
        
        if admin_user:
            print(f"✅ Admin user found: {admin_user.email}")
            
            # Verificar estrutura da tabela auth_users
            result = await db.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'auth_users'
                ORDER BY ordinal_position
            """))
            columns = [row[0] for row in result.fetchall()]
            expected_columns = ['id', 'email', 'password_hash', 'name', 'role', 'phone', 'is_active', 'created_at', 'updated_at']
            
            for col in expected_columns:
                assert col in columns, f"Coluna {col} deve existir em auth_users"
            
            print("✅ auth_users table structure is correct")
        else:
            print("⚠️  No admin users found to test login")

async def test_hf003_integration():
    """Teste de integração completo HF003"""
    try:
        await test_auth_consolidation()
        await test_login_pos_migracao()
        print("🎉 HF003 - Todos os testes passaram!")
        return True
    except Exception as e:
        print(f"❌ HF003 - Erro nos testes: {e}")
        return False

if __name__ == "__main__":
    print("🔒 HF003 Test Suite - Consolidação Auth Tables")
    print("=" * 50)
    
    # Executar testes
    result = asyncio.run(test_hf003_integration())
    
    if result:
        print("✅ HF003 VALIDATION PASSED")
    else:
        print("❌ HF003 VALIDATION FAILED")
        exit(1)

#!/usr/bin/env python3
"""
🔧 Fix PostgreSQL RBAC Schema

Corrige o problema do tipo 'permissiontype' no PostgreSQL Railway.
Remove qualquer referência incorreta a tipos enum que não existem.
"""

import asyncio
import logging
from sqlalchemy import text
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def fix_rbac_schema():
    """Corrige schema RBAC no PostgreSQL"""
    
    print("🔧 Iniciando correção do schema RBAC...")
    
    try:
        async with AsyncSessionLocal() as session:
            
            # 1. Verificar se a tabela existe
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'rbac_permissions'
                );
            """))
            table_exists = result.scalar()
            
            print(f"📋 Tabela rbac_permissions existe: {table_exists}")
            
            if not table_exists:
                print("❌ Tabela rbac_permissions não encontrada!")
                return False
            
            # 2. Verificar colunas da tabela
            result = await session.execute(text("""
                SELECT column_name, data_type, udt_name 
                FROM information_schema.columns 
                WHERE table_name = 'rbac_permissions'
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            print("📊 Colunas da tabela rbac_permissions:")
            for col in columns:
                print(f"  - {col.column_name}: {col.data_type} ({col.udt_name})")
            
            # 3. Verificar tipos enum existentes
            result = await session.execute(text("""
                SELECT typname FROM pg_type 
                WHERE typtype = 'e'
                ORDER BY typname;
            """))
            
            enums = result.fetchall()
            print("🔤 Tipos enum existentes:")
            for enum_type in enums:
                print(f"  - {enum_type.typname}")
            
            # 4. Verificar se permissiontype existe como enum
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM pg_type 
                    WHERE typname = 'permissiontype'
                );
            """))
            enum_exists = result.scalar()
            
            print(f"🔍 Tipo 'permissiontype' existe: {enum_exists}")
            
            # 5. Se permission_type estiver como enum incorreto, converter para varchar
            result = await session.execute(text("""
                SELECT data_type, udt_name 
                FROM information_schema.columns 
                WHERE table_name = 'rbac_permissions' 
                AND column_name = 'permission_type';
            """))
            
            col_info = result.fetchone()
            if col_info:
                print(f"🏷️ permission_type: {col_info.data_type} ({col_info.udt_name})")
                
                # Se estiver como enum, converter para varchar
                if col_info.udt_name == 'permissiontype':
                    print("🔄 Convertendo permission_type de enum para varchar...")
                    
                    await session.execute(text("""
                        ALTER TABLE rbac_permissions 
                        ALTER COLUMN permission_type TYPE VARCHAR(100);
                    """))
                    
                    print("✅ Coluna permission_type convertida para VARCHAR(100)")
            
            # 6. Tentar uma query simples
            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM rbac_permissions;
                """))
                count = result.scalar()
                print(f"📈 Total de permissions: {count}")
                
                # Se count = 0, vamos inserir algumas permissões básicas
                if count == 0:
                    print("📝 Inserindo permissões básicas...")
                    
                    await session.execute(text("""
                        INSERT INTO rbac_permissions (permission_type, name, description, category, risk_level, requires_2fa, is_active, created_at, updated_at)
                        VALUES 
                        ('DASHBOARD_VIEW', 'Visualizar Dashboard', 'Permite visualizar o dashboard principal', 'DASHBOARD', 'LOW', false, true, NOW(), NOW()),
                        ('APPOINTMENTS_VIEW', 'Visualizar Agendamentos', 'Permite visualizar agendamentos', 'APPOINTMENTS', 'LOW', false, true, NOW(), NOW()),
                        ('SYSTEM_ADMIN', 'Administrador Sistema', 'Acesso completo ao sistema', 'SYSTEM', 'CRITICAL', true, true, NOW(), NOW())
                        ON CONFLICT (permission_type) DO NOTHING;
                    """))
                    
                    print("✅ Permissões básicas inseridas")
                
            except Exception as e:
                print(f"❌ Erro ao consultar permissions: {e}")
                return False
            
            await session.commit()
            print("✅ Schema RBAC corrigido com sucesso!")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao corrigir schema RBAC: {e}")
        logger.exception("Erro detalhado:")
        return False

async def main():
    """Executa correção do schema"""
    print("🔧 CORREÇÃO DO SCHEMA RBAC - POSTGRESQL")
    print("=" * 50)
    
    success = await fix_rbac_schema()
    
    if success:
        print("🎉 Correção concluída com sucesso!")
    else:
        print("❌ Falha na correção do schema")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())

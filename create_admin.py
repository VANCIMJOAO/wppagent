#!/usr/bin/env python3
"""
🔐 SCRIPT DE INICIALIZAÇÃO DO ADMIN
==================================
Cria o usuário admin inicial se não existir
"""

import asyncio
import sys
import os
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal, init_db
from app.models.database import AdminUser

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin_if_not_exists():
    """Cria admin inicial se não existir"""
    print("🔐 Iniciando criação do usuário admin...")
    
    try:
        # Inicializar banco
        await init_db()
        print("✅ Banco de dados inicializado")
        
        # Usar sessão assíncrona
        async with AsyncSessionLocal() as session:
            # Verificar se admin existe
            result = await session.execute(
                select(AdminUser).where(AdminUser.username == "admin")
            )
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                print("ℹ️  Usuário admin já existe")
                return
            
            # Criar novo admin
            hashed_password = pwd_context.hash("admin123")
            
            new_admin = AdminUser(
                username="admin",
                password_hash=hashed_password,
                is_active=True
            )
            
            session.add(new_admin)
            await session.commit()
            
            print("✅ Usuário admin criado com sucesso!")
            print("📋 Credenciais:")
            print("   Username: admin")
            print("   Password: admin123")
            
    except Exception as e:
        print(f"❌ Erro ao criar admin: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_admin_if_not_exists())

#!/usr/bin/env python3
"""
🚀 Script rápido para criar admin para testes
"""

import asyncio
import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.database import AdminUser
from app.routes.admin_auth import get_password_hash
from sqlalchemy import select

async def create_test_admin():
    """Criar admin para testes rapidamente"""
    
    # Admin padrão para testes
    admin_data = {
        'username': 'dbadmin',
        'email': 'dbadmin@test.com',
        'full_name': 'Database Administrator',
        'password': 'dbos.getenv("ADMIN_PASSWORD", "SECURE_ADMIN_PASSWORD")',
        'is_active': True,
        'is_super_admin': True
    }
    
    try:
        async with AsyncSessionLocal() as session:
            # Verificar se já existe
            result = await session.execute(
                select(AdminUser).where(AdminUser.username == admin_data['username'])
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"✅ Admin '{admin_data['username']}' já existe")
                print(f"📧 Email: {existing.email}")
                print(f"🔒 Use a senha: {admin_data['password']}")
                return True
            
            # Criar novo admin
            admin_user = AdminUser(
                username=admin_data['username'],
                email=admin_data['email'],
                full_name=admin_data['full_name'],
                password_hash=get_password_hash(admin_data['password']),
                is_active=admin_data['is_active'],
                is_super_admin=admin_data['is_super_admin']
            )
            
            session.add(admin_user)
            await session.commit()
            
            print("✅ Admin criado com sucesso!")
            print(f"👤 Username: {admin_data['username']}")
            print(f"📧 Email: {admin_data['email']}")
            print(f"🔒 Senha: {admin_data['password']}")
            print(f"👑 Super Admin: {admin_data['is_super_admin']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(create_test_admin())
    if not success:
        sys.exit(1)

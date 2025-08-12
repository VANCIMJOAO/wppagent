#!/usr/bin/env python3
"""
👤 Script para criar usuário administrador inicial
=====================================================

Cria o primeiro usuário admin para acessar as funcionalidades
de otimização do banco de dados e outras operações administrativas.
"""

import asyncio
import sys
import os
from getpass import getpass

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal, engine
from app.models.database import AdminUser
from app.routes.admin_auth import get_password_hash
from sqlalchemy import select

async def create_admin_user():
    """Criar usuário admin inicial"""
    
    print("🔐 Criando usuário administrador inicial")
    print("=" * 50)
    
    # Solicitar dados do admin
    username = input("Username do admin: ").strip()
    if not username:
        print("❌ Username é obrigatório")
        return False
    
    email = input("Email do admin: ").strip()
    if not email:
        print("❌ Email é obrigatório")
        return False
    
    full_name = input("Nome completo (opcional): ").strip()
    if not full_name:
        full_name = username
    
    password = getpass("Senha do admin: ").strip()
    if not password:
        print("❌ Senha é obrigatória")
        return False
    
    confirm_password = getpass("Confirmar senha: ").strip()
    if password != confirm_password:
        print("❌ Senhas não coincidem")
        return False
    
    if len(password) < 8:
        print("❌ Senha deve ter pelo menos 8 caracteres")
        return False
    
    try:
        # Usar sessão async
        async with AsyncSessionLocal() as session:
            # Verificar se admin já existe
            result = await session.execute(
                select(AdminUser).where(AdminUser.username == username)
            )
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                print(f"❌ Admin '{username}' já existe")
                return False
            
            # Verificar se email já existe
            result = await session.execute(
                select(AdminUser).where(AdminUser.email == email)
            )
            existing_email = result.scalar_one_or_none()
            
            if existing_email:
                print(f"❌ Email '{email}' já está em uso")
                return False
            
            # Criar novo admin
            admin_user = AdminUser(
                username=username,
                email=email,
                full_name=full_name,
                password_hash=get_password_hash(password),
                is_active=True,
                is_super_admin=False
            )
            
            session.add(admin_user)
            await session.commit()
            
            print(f"✅ Admin '{username}' criado com sucesso!")
            print(f"📧 Email: {email}")
            print(f"👤 Nome: {full_name}")
            print("\n🚀 Agora você pode:")
            print("1. Fazer login em /admin/login")
            print("2. Acessar otimizações em /database/*")
            print("3. Criar outros admins em /admin/create")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao criar admin: {e}")
        return False

async def list_admins():
    """Listar admins existentes"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(AdminUser))
            admins = result.scalars().all()
            
            if not admins:
                print("📋 Nenhum admin cadastrado")
            else:
                print("\n📋 Admins cadastrados:")
                print("-" * 30)
                for admin in admins:
                    status = "🟢 Ativo" if admin.is_active else "🔴 Inativo"
                    print(f"• {admin.username} - {status}")
                    print(f"  Criado em: {admin.created_at}")
                    if admin.last_login:
                        print(f"  Último login: {admin.last_login}")
                    print()
                    
    except Exception as e:
        print(f"❌ Erro ao listar admins: {e}")

def main():
    """Função principal"""
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        asyncio.run(list_admins())
    else:
        success = asyncio.run(create_admin_user())
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()

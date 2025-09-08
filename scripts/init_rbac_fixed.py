#!/usr/bin/env python3
"""
Script de Inicialização do Sistema RBAC - Versão Corrigida
Cria usuário administrador padrão e testa funcionalidades básicas
"""

import asyncio
import sys
import os
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append('/home/vancim/whats_agent')

from app.database import get_db
from app.models.rbac import RBACUser, RBACRole, RBACPermission, PermissionCategory, RiskLevel, RoleType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from passlib.context import CryptContext

# Contexto para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def initialize_rbac_system():
    """Inicializar sistema RBAC com dados padrão"""
    
    print("🔧 Inicializando Sistema RBAC...")
    
    try:
        # Obter sessão async do banco
        async for db in get_db():
            print("📋 Verificando estado atual do sistema...")
            
            # Verificar se o sistema já foi inicializado
            result = await db.execute(select(func.count(RBACUser.id)))
            existing_users = result.scalar()
            
            result = await db.execute(select(func.count(RBACRole.id)))
            existing_roles = result.scalar()
            
            if existing_users > 0 and existing_roles > 0:
                print(f"✅ Sistema já inicializado!")
                print(f"   - Usuários: {existing_users}")
                print(f"   - Roles: {existing_roles}")
                return
            
            print("🚀 Inicializando sistema pela primeira vez...")
            
            # 1. Criar permissões do sistema
            print("1️⃣ Criando permissões do sistema...")
            permissions_data = [
                # Dashboard
                ("DASHBOARD_VIEW", "Visualizar Dashboard", "Acesso ao dashboard principal", PermissionCategory.DASHBOARD, RiskLevel.LOW),
                ("DASHBOARD_MANAGE", "Gerenciar Dashboard", "Configurar widgets e layouts", PermissionCategory.DASHBOARD, RiskLevel.MEDIUM),
                
                # Appointments
                ("APPOINTMENTS_VIEW", "Visualizar Agendamentos", "Ver agendamentos existentes", PermissionCategory.APPOINTMENTS, RiskLevel.LOW),
                ("APPOINTMENTS_CREATE", "Criar Agendamentos", "Criar novos agendamentos", PermissionCategory.APPOINTMENTS, RiskLevel.MEDIUM),
                ("APPOINTMENTS_UPDATE", "Atualizar Agendamentos", "Modificar agendamentos", PermissionCategory.APPOINTMENTS, RiskLevel.MEDIUM),
                ("APPOINTMENTS_DELETE", "Excluir Agendamentos", "Remover agendamentos", PermissionCategory.APPOINTMENTS, RiskLevel.HIGH),
                ("APPOINTMENTS_MANAGE", "Gerenciar Agendamentos", "Controle total sobre agendamentos", PermissionCategory.APPOINTMENTS, RiskLevel.HIGH),
                
                # Conversations  
                ("CONVERSATIONS_VIEW", "Visualizar Conversas", "Ver conversas do WhatsApp", PermissionCategory.CONVERSATIONS, RiskLevel.LOW),
                ("CONVERSATIONS_SEND", "Enviar Mensagens", "Enviar mensagens via WhatsApp", PermissionCategory.CONVERSATIONS, RiskLevel.MEDIUM),
                ("CONVERSATIONS_MANAGE", "Gerenciar Conversas", "Controle completo sobre conversas", PermissionCategory.CONVERSATIONS, RiskLevel.HIGH),
                
                # Clients
                ("CLIENTS_VIEW", "Visualizar Clientes", "Ver dados dos clientes", PermissionCategory.CLIENTS, RiskLevel.LOW),
                ("CLIENTS_CREATE", "Criar Clientes", "Adicionar novos clientes", PermissionCategory.CLIENTS, RiskLevel.MEDIUM),
                ("CLIENTS_UPDATE", "Atualizar Clientes", "Modificar dados dos clientes", PermissionCategory.CLIENTS, RiskLevel.MEDIUM),
                ("CLIENTS_DELETE", "Excluir Clientes", "Remover clientes", PermissionCategory.CLIENTS, RiskLevel.HIGH),
                ("CLIENTS_MANAGE", "Gerenciar Clientes", "Controle total sobre clientes", PermissionCategory.CLIENTS, RiskLevel.HIGH),
                
                # Reports
                ("REPORTS_VIEW", "Visualizar Relatórios", "Ver relatórios e estatísticas", PermissionCategory.REPORTS, RiskLevel.LOW),
                ("REPORTS_CREATE", "Criar Relatórios", "Gerar novos relatórios", PermissionCategory.REPORTS, RiskLevel.MEDIUM),
                ("REPORTS_EXPORT", "Exportar Relatórios", "Exportar relatórios em diversos formatos", PermissionCategory.REPORTS, RiskLevel.MEDIUM),
                ("REPORTS_MANAGE", "Gerenciar Relatórios", "Controle completo sobre relatórios", PermissionCategory.REPORTS, RiskLevel.HIGH),
                
                # System
                ("USERS_VIEW", "Visualizar Usuários", "Ver lista de usuários", PermissionCategory.SYSTEM, RiskLevel.MEDIUM),
                ("USERS_CREATE", "Criar Usuários", "Adicionar novos usuários", PermissionCategory.SYSTEM, RiskLevel.HIGH),
                ("USERS_UPDATE", "Atualizar Usuários", "Modificar dados dos usuários", PermissionCategory.SYSTEM, RiskLevel.HIGH),
                ("USERS_DELETE", "Excluir Usuários", "Remover usuários", PermissionCategory.SYSTEM, RiskLevel.CRITICAL),
                ("USERS_MANAGE", "Gerenciar Usuários", "Controle total sobre usuários", PermissionCategory.SYSTEM, RiskLevel.CRITICAL),
                ("SYSTEM_VIEW", "Visualizar Sistema", "Ver configurações e status", PermissionCategory.SYSTEM, RiskLevel.MEDIUM),
                ("SYSTEM_MANAGE", "Gerenciar Sistema", "Configurar sistema", PermissionCategory.SYSTEM, RiskLevel.CRITICAL),
                ("SYSTEM_ADMIN", "Administrador Sistema", "Acesso administrativo completo", PermissionCategory.SYSTEM, RiskLevel.CRITICAL),
                ("SYSTEM_RBAC_MANAGE", "Gerenciar RBAC", "Controle do sistema de permissões", PermissionCategory.SYSTEM, RiskLevel.CRITICAL, True)
            ]
            
            for perm_data in permissions_data:
                perm_type, name, desc, category, risk, requires_2fa = perm_data if len(perm_data) == 6 else (*perm_data, False)
                
                # Verificar se já existe
                result = await db.execute(select(RBACPermission).where(RBACPermission.permission_type == perm_type))
                existing = result.scalar_one_or_none()
                
                if not existing:
                    permission = RBACPermission(
                        permission_type=perm_type,
                        name=name,
                        description=desc,
                        category=category,
                        risk_level=risk,
                        requires_2fa=requires_2fa
                    )
                    db.add(permission)
            
            await db.commit()
            print("   ✅ Permissões criadas")
            
            # 2. Criar roles do sistema
            print("2️⃣ Criando roles do sistema...")
            roles_data = [
                ("super_admin", "Super Administrador", "Acesso completo ao sistema", RoleType.SYSTEM, True, False),
                ("admin", "Administrador", "Administrador do sistema", RoleType.SYSTEM, True, True),
                ("manager", "Gerente", "Gerente de operações", RoleType.SYSTEM, True, True),
                ("operator", "Operador", "Operador do sistema", RoleType.SYSTEM, True, True),
                ("viewer", "Visualizador", "Apenas visualização", RoleType.SYSTEM, True, True),
                ("guest", "Convidado", "Acesso limitado", RoleType.SYSTEM, True, False)
            ]
            
            for role_data in roles_data:
                name, desc, full_desc, role_type, is_system, can_delete = role_data
                
                # Verificar se já existe
                result = await db.execute(select(RBACRole).where(RBACRole.name == name))
                existing = result.scalar_one_or_none()
                
                if not existing:
                    role = RBACRole(
                        name=name,
                        description=full_desc,
                        role_type=role_type,
                        is_system_role=is_system,
                        can_be_deleted=can_delete
                    )
                    db.add(role)
            
            await db.commit()
            print("   ✅ Roles criados")
            
            # 3. Atribuir permissões aos roles
            print("3️⃣ Atribuindo permissões aos roles...")
            
            # Buscar todos os roles e permissões
            result = await db.execute(select(RBACRole))
            roles = {role.name: role for role in result.scalars().all()}
            
            result = await db.execute(select(RBACPermission))
            permissions = {perm.permission_type: perm for perm in result.scalars().all()}
            
            # Definir permissões por role
            role_permissions = {
                "super_admin": list(permissions.keys()),  # Todas as permissões
                "admin": [
                    "DASHBOARD_VIEW", "DASHBOARD_MANAGE",
                    "APPOINTMENTS_VIEW", "APPOINTMENTS_CREATE", "APPOINTMENTS_UPDATE", "APPOINTMENTS_MANAGE",
                    "CONVERSATIONS_VIEW", "CONVERSATIONS_SEND", "CONVERSATIONS_MANAGE",
                    "CLIENTS_VIEW", "CLIENTS_CREATE", "CLIENTS_UPDATE", "CLIENTS_MANAGE",
                    "REPORTS_VIEW", "REPORTS_CREATE", "REPORTS_EXPORT", "REPORTS_MANAGE",
                    "USERS_VIEW", "USERS_CREATE", "USERS_UPDATE", "USERS_MANAGE",
                    "SYSTEM_VIEW", "SYSTEM_MANAGE"
                ],
                "manager": [
                    "DASHBOARD_VIEW", "DASHBOARD_MANAGE",
                    "APPOINTMENTS_VIEW", "APPOINTMENTS_CREATE", "APPOINTMENTS_UPDATE", "APPOINTMENTS_MANAGE",
                    "CONVERSATIONS_VIEW", "CONVERSATIONS_SEND",
                    "CLIENTS_VIEW", "CLIENTS_CREATE", "CLIENTS_UPDATE",
                    "REPORTS_VIEW", "REPORTS_CREATE", "REPORTS_EXPORT",
                    "USERS_VIEW"
                ],
                "operator": [
                    "DASHBOARD_VIEW",
                    "APPOINTMENTS_VIEW", "APPOINTMENTS_CREATE", "APPOINTMENTS_UPDATE",
                    "CONVERSATIONS_VIEW", "CONVERSATIONS_SEND",
                    "CLIENTS_VIEW", "CLIENTS_CREATE", "CLIENTS_UPDATE",
                    "REPORTS_VIEW"
                ],
                "viewer": [
                    "DASHBOARD_VIEW",
                    "APPOINTMENTS_VIEW",
                    "CONVERSATIONS_VIEW",
                    "CLIENTS_VIEW",
                    "REPORTS_VIEW"
                ],
                "guest": [
                    "DASHBOARD_VIEW"
                ]
            }
            
            # Atribuir permissões
            for role_name, perm_types in role_permissions.items():
                role = roles.get(role_name)
                if role:
                    for perm_type in perm_types:
                        permission = permissions.get(perm_type)
                        if permission and permission not in role.permissions:
                            role.permissions.append(permission)
            
            await db.commit()
            print("   ✅ Permissões atribuídas aos roles")
            
            # 4. Criar usuário administrador padrão
            print("4️⃣ Criando usuário administrador padrão...")
            
            # Verificar se admin já existe
            result = await db.execute(select(RBACUser).where(RBACUser.username == "admin"))
            existing_admin = result.scalar_one_or_none()
            
            if not existing_admin:
                # Hash da senha
                password_hash = pwd_context.hash("Admin@123")
                
                admin_user = RBACUser(
                    username="admin",
                    email="admin@whatsagent.local",
                    full_name="Administrador do Sistema",
                    password_hash=password_hash,
                    is_active=True,
                    is_verified=True,
                    requires_2fa=False
                )
                db.add(admin_user)
                await db.commit()
                
                # Refresh para obter ID
                await db.refresh(admin_user)
                
                # Atribuir role super_admin
                super_admin_role = roles.get("super_admin")
                if super_admin_role:
                    admin_user.roles.append(super_admin_role)
                    await db.commit()
                
                print(f"   ✅ Usuário admin criado com ID: {admin_user.id}")
            else:
                print("   ⚠️  Usuário admin já existe")
            
            # 5. Criar usuários de exemplo
            print("5️⃣ Criando usuários de exemplo...")
            example_users = [
                ("manager", "manager@whatsagent.local", "Gerente do Sistema", "Manager@123", "manager"),
                ("operator", "operator@whatsagent.local", "Operador do Sistema", "Operator@123", "operator"),
                ("viewer", "viewer@whatsagent.local", "Visualizador do Sistema", "Viewer@123", "viewer")
            ]
            
            for username, email, full_name, password, role_name in example_users:
                # Verificar se já existe
                result = await db.execute(select(RBACUser).where(RBACUser.username == username))
                existing = result.scalar_one_or_none()
                
                if not existing:
                    password_hash = pwd_context.hash(password)
                    user = RBACUser(
                        username=username,
                        email=email,
                        full_name=full_name,
                        password_hash=password_hash,
                        is_active=True,
                        is_verified=True,
                        requires_2fa=False
                    )
                    db.add(user)
                    await db.commit()
                    await db.refresh(user)
                    
                    # Atribuir role
                    role = roles.get(role_name)
                    if role:
                        user.roles.append(role)
                        await db.commit()
                    
                    print(f"   ✅ Usuário '{username}' criado com role '{role_name}'")
                else:
                    print(f"   ⚠️  Usuário '{username}' já existe")
            
            # 6. Mostrar estatísticas finais
            print("6️⃣ Verificando inicialização...")
            
            result = await db.execute(select(func.count(RBACUser.id)))
            total_users = result.scalar()
            
            result = await db.execute(select(func.count(RBACUser.id)).where(RBACUser.is_active == True))
            active_users = result.scalar()
            
            result = await db.execute(select(func.count(RBACRole.id)))
            total_roles = result.scalar()
            
            result = await db.execute(select(func.count(RBACRole.id)).where(RBACRole.is_system_role == True))
            system_roles = result.scalar()
            
            result = await db.execute(select(func.count(RBACPermission.id)))
            total_permissions = result.scalar()
            
            print(f"""
📊 Sistema RBAC inicializado com sucesso!

Estatísticas:
├── Usuários: {total_users} total
│   └── Ativos: {active_users}
├── Roles: {total_roles} total  
│   └── Sistema: {system_roles}
└── Permissões: {total_permissions} total

🔑 Credenciais de acesso:
├── Usuário: admin
├── Senha: Admin@123
└── Permissões: Super Administrador (todas as permissões)

⚠️  IMPORTANTE:
- Altere a senha padrão no primeiro login
- Configure 2FA para usuários administrativos
- Revise as permissões conforme necessário

🌐 Acesso:
- Frontend: http://localhost:3000/login
- API: http://localhost:8000/api/rbac/
- Documentação: http://localhost:8000/docs
            """)
            
            print("\n🎉 Inicialização concluída com sucesso!")
            break  # Sair do loop async for
        
    except Exception as e:
        print(f"❌ Erro durante a inicialização: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gerenciador do Sistema RBAC")
    parser.add_argument("--init", action="store_true", help="Inicializar sistema RBAC")
    
    args = parser.parse_args()
    
    if args.init:
        asyncio.run(initialize_rbac_system())
    else:
        print("Sistema RBAC - WhatsAgent")
        print("Use --init para inicializar o sistema")

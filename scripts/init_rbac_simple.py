#!/usr/bin/env python3
"""
Script de Inicialização do Sistema RBAC - Versão Simplificada
Popula as tabelas RBAC com dados iniciais usando asyncpg diretamente
"""

import asyncio
import asyncpg
from passlib.context import CryptContext

DATABASE_URL = 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway'

# Contexto para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def initialize_rbac_system():
    """Inicializar sistema RBAC com dados padrão"""
    
    print("🔧 Inicializando Sistema RBAC...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Verificar se já foi inicializado
        users_count = await conn.fetchval("SELECT COUNT(*) FROM rbac_users")
        roles_count = await conn.fetchval("SELECT COUNT(*) FROM rbac_roles")
        
        if users_count > 0 and roles_count > 0:
            print(f"✅ Sistema já inicializado!")
            print(f"   - Usuários: {users_count}")
            print(f"   - Roles: {roles_count}")
            return
        
        print("🚀 Inicializando sistema pela primeira vez...")
        
        # 1. Criar permissões do sistema
        print("1️⃣ Criando permissões do sistema...")
        permissions_data = [
            # Dashboard
            ("DASHBOARD_VIEW", "Visualizar Dashboard", "Acesso ao dashboard principal", "DASHBOARD", "LOW", False),
            ("DASHBOARD_MANAGE", "Gerenciar Dashboard", "Configurar widgets e layouts", "DASHBOARD", "MEDIUM", False),
            
            # Appointments
            ("APPOINTMENTS_VIEW", "Visualizar Agendamentos", "Ver agendamentos existentes", "APPOINTMENTS", "LOW", False),
            ("APPOINTMENTS_CREATE", "Criar Agendamentos", "Criar novos agendamentos", "APPOINTMENTS", "MEDIUM", False),
            ("APPOINTMENTS_UPDATE", "Atualizar Agendamentos", "Modificar agendamentos", "APPOINTMENTS", "MEDIUM", False),
            ("APPOINTMENTS_DELETE", "Excluir Agendamentos", "Remover agendamentos", "APPOINTMENTS", "HIGH", False),
            ("APPOINTMENTS_MANAGE", "Gerenciar Agendamentos", "Controle total sobre agendamentos", "APPOINTMENTS", "HIGH", False),
            
            # Conversations  
            ("CONVERSATIONS_VIEW", "Visualizar Conversas", "Ver conversas do WhatsApp", "CONVERSATIONS", "LOW", False),
            ("CONVERSATIONS_SEND", "Enviar Mensagens", "Enviar mensagens via WhatsApp", "CONVERSATIONS", "MEDIUM", False),
            ("CONVERSATIONS_MANAGE", "Gerenciar Conversas", "Controle completo sobre conversas", "CONVERSATIONS", "HIGH", False),
            
            # Clients
            ("CLIENTS_VIEW", "Visualizar Clientes", "Ver dados dos clientes", "CLIENTS", "LOW", False),
            ("CLIENTS_CREATE", "Criar Clientes", "Adicionar novos clientes", "CLIENTS", "MEDIUM", False),
            ("CLIENTS_UPDATE", "Atualizar Clientes", "Modificar dados dos clientes", "CLIENTS", "MEDIUM", False),
            ("CLIENTS_DELETE", "Excluir Clientes", "Remover clientes", "CLIENTS", "HIGH", False),
            ("CLIENTS_MANAGE", "Gerenciar Clientes", "Controle total sobre clientes", "CLIENTS", "HIGH", False),
            
            # Reports
            ("REPORTS_VIEW", "Visualizar Relatórios", "Ver relatórios e estatísticas", "REPORTS", "LOW", False),
            ("REPORTS_CREATE", "Criar Relatórios", "Gerar novos relatórios", "REPORTS", "MEDIUM", False),
            ("REPORTS_EXPORT", "Exportar Relatórios", "Exportar relatórios em diversos formatos", "REPORTS", "MEDIUM", False),
            ("REPORTS_MANAGE", "Gerenciar Relatórios", "Controle completo sobre relatórios", "REPORTS", "HIGH", False),
            
            # System
            ("USERS_VIEW", "Visualizar Usuários", "Ver lista de usuários", "SYSTEM", "MEDIUM", False),
            ("USERS_CREATE", "Criar Usuários", "Adicionar novos usuários", "SYSTEM", "HIGH", False),
            ("USERS_UPDATE", "Atualizar Usuários", "Modificar dados dos usuários", "SYSTEM", "HIGH", False),
            ("USERS_DELETE", "Excluir Usuários", "Remover usuários", "SYSTEM", "CRITICAL", True),
            ("USERS_MANAGE", "Gerenciar Usuários", "Controle total sobre usuários", "SYSTEM", "CRITICAL", True),
            ("SYSTEM_VIEW", "Visualizar Sistema", "Ver configurações e status", "SYSTEM", "MEDIUM", False),
            ("SYSTEM_MANAGE", "Gerenciar Sistema", "Configurar sistema", "SYSTEM", "CRITICAL", True),
            ("SYSTEM_ADMIN", "Administrador Sistema", "Acesso administrativo completo", "SYSTEM", "CRITICAL", True),
            ("SYSTEM_RBAC_MANAGE", "Gerenciar RBAC", "Controle do sistema de permissões", "SYSTEM", "CRITICAL", True)
        ]
        
        for perm_data in permissions_data:
            perm_type, name, desc, category, risk, requires_2fa = perm_data
            
            # Verificar se já existe
            existing = await conn.fetchval(
                "SELECT id FROM rbac_permissions WHERE permission_type = $1", 
                perm_type
            )
            
            if not existing:
                await conn.execute(
                    """INSERT INTO rbac_permissions 
                       (permission_type, name, description, category, risk_level, requires_2fa) 
                       VALUES ($1, $2, $3, $4, $5, $6)""",
                    perm_type, name, desc, category, risk, requires_2fa
                )
        
        print("   ✅ Permissões criadas")
        
        # 2. Criar roles do sistema
        print("2️⃣ Criando roles do sistema...")
        roles_data = [
            ("super_admin", "Super Administrador", "SYSTEM", True, False),
            ("admin", "Administrador", "SYSTEM", True, True),
            ("manager", "Gerente", "SYSTEM", True, True),
            ("operator", "Operador", "SYSTEM", True, True),
            ("viewer", "Visualizador", "SYSTEM", True, True),
            ("guest", "Convidado", "SYSTEM", True, False)
        ]
        
        for name, desc, role_type, is_system, can_delete in roles_data:
            # Verificar se já existe
            existing = await conn.fetchval("SELECT id FROM rbac_roles WHERE name = $1", name)
            
            if not existing:
                await conn.execute(
                    """INSERT INTO rbac_roles 
                       (name, description, role_type, is_system_role, can_be_deleted) 
                       VALUES ($1, $2, $3, $4, $5)""",
                    name, desc, role_type, is_system, can_delete
                )
        
        print("   ✅ Roles criados")
        
        # 3. Atribuir permissões aos roles
        print("3️⃣ Atribuindo permissões aos roles...")
        
        # Buscar IDs dos roles e permissões
        roles = {}
        roles_result = await conn.fetch("SELECT id, name FROM rbac_roles")
        for row in roles_result:
            roles[row['name']] = row['id']
        
        permissions = {}
        perms_result = await conn.fetch("SELECT id, permission_type FROM rbac_permissions")
        for row in perms_result:
            permissions[row['permission_type']] = row['id']
        
        # Definir permissões por role
        role_permissions_map = {
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
        for role_name, perm_types in role_permissions_map.items():
            role_id = roles.get(role_name)
            if role_id:
                for perm_type in perm_types:
                    perm_id = permissions.get(perm_type)
                    if perm_id:
                        # Verificar se já existe
                        existing = await conn.fetchval(
                            "SELECT 1 FROM role_permissions WHERE role_id = $1 AND permission_id = $2",
                            role_id, perm_id
                        )
                        if not existing:
                            await conn.execute(
                                "INSERT INTO role_permissions (role_id, permission_id) VALUES ($1, $2)",
                                role_id, perm_id
                            )
        
        print("   ✅ Permissões atribuídas aos roles")
        
        # 4. Criar usuário administrador padrão
        print("4️⃣ Criando usuário administrador padrão...")
        
        # Verificar se admin já existe
        existing_admin = await conn.fetchval("SELECT id FROM rbac_users WHERE username = $1", "admin")
        
        if not existing_admin:
            # Hash da senha
            password_hash = pwd_context.hash("Admin@123")
            
            admin_id = await conn.fetchval(
                """INSERT INTO rbac_users 
                   (username, email, full_name, password_hash, is_active, is_verified, requires_2fa) 
                   VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id""",
                "admin", "admin@whatsagent.local", "Administrador do Sistema", 
                password_hash, True, True, False
            )
            
            # Atribuir role super_admin
            super_admin_id = roles.get("super_admin")
            if super_admin_id:
                await conn.execute(
                    "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2)",
                    admin_id, super_admin_id
                )
            
            print(f"   ✅ Usuário admin criado com ID: {admin_id}")
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
            existing = await conn.fetchval("SELECT id FROM rbac_users WHERE username = $1", username)
            
            if not existing:
                password_hash = pwd_context.hash(password)
                user_id = await conn.fetchval(
                    """INSERT INTO rbac_users 
                       (username, email, full_name, password_hash, is_active, is_verified, requires_2fa) 
                       VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id""",
                    username, email, full_name, password_hash, True, True, False
                )
                
                # Atribuir role
                role_id = roles.get(role_name)
                if role_id:
                    await conn.execute(
                        "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2)",
                        user_id, role_id
                    )
                
                print(f"   ✅ Usuário '{username}' criado com role '{role_name}'")
            else:
                print(f"   ⚠️  Usuário '{username}' já existe")
        
        # 6. Mostrar estatísticas finais
        print("6️⃣ Verificando inicialização...")
        
        total_users = await conn.fetchval("SELECT COUNT(*) FROM rbac_users")
        active_users = await conn.fetchval("SELECT COUNT(*) FROM rbac_users WHERE is_active = TRUE")
        total_roles = await conn.fetchval("SELECT COUNT(*) FROM rbac_roles")
        system_roles = await conn.fetchval("SELECT COUNT(*) FROM rbac_roles WHERE is_system_role = TRUE")
        total_permissions = await conn.fetchval("SELECT COUNT(*) FROM rbac_permissions")
        
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

🔑 Outros usuários de teste:
├── manager / Manager@123 (Gerente)
├── operator / Operator@123 (Operador)
└── viewer / Viewer@123 (Visualizador)

⚠️  IMPORTANTE:
- Altere as senhas padrão no primeiro login
- Configure 2FA para usuários administrativos
- Revise as permissões conforme necessário

🌐 Próximos passos:
1. Testar login: http://localhost:8000/api/auth/login
2. Verificar RBAC: http://localhost:8000/api/rbac/stats
3. Documentação: http://localhost:8000/docs#/rbac
        """)
        
        print("\n🎉 Inicialização concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a inicialização: {e}")
        import traceback
        print(traceback.format_exc())
    
    finally:
        await conn.close()


if __name__ == "__main__":
    print("🚀 Inicializador RBAC - WhatsAgent")
    asyncio.run(initialize_rbac_system())

#!/usr/bin/env python3
"""
Script de Inicialização do Sistema RBAC
Cria usuário administrador padrão e testa funcionalidades básicas
"""

import asyncio
import sys
import os
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append('/home/vancim/whats_agent')

from app.services.rbac_service import RBACService
from app.database import get_db
from app.models.rbac import RBACUser, RBACRole
from sqlalchemy.orm import Session


async def initialize_rbac_system():
    """Inicializar sistema RBAC com dados padrão"""
    
    print("🔧 Inicializando Sistema RBAC...")
    
    try:
        # Obter sessão do banco
        db = next(get_db())
        rbac_service = RBACService(db)
        
        print("📋 Verificando estado atual do sistema...")
        
        # Verificar se o sistema já foi inicializado
        existing_users = db.query(RBACUser).count()
        existing_roles = db.query(RBACRole).count()
        
        if existing_users > 0 and existing_roles > 0:
            print(f"✅ Sistema já inicializado!")
            print(f"   - Usuários: {existing_users}")
            print(f"   - Roles: {existing_roles}")
            
            # Mostrar estatísticas
            stats = rbac_service.get_system_stats()
            print(f"📊 Estatísticas atuais:")
            print(f"   - Usuários ativos: {stats['users']['active']}")
            print(f"   - Usuários inativos: {stats['users']['inactive']}")
            print(f"   - Roles de sistema: {stats['roles']['system_roles']}")
            print(f"   - Roles customizados: {stats['roles']['custom_roles']}")
            print(f"   - Total de permissões: {stats['permissions']['total']}")
            
            return
        
        print("🚀 Inicializando sistema pela primeira vez...")
        
        # Inicializar sistema RBAC
        print("1️⃣ Criando roles e permissões do sistema...")
        rbac_service.initialize_system()
        
        # Criar usuário administrador padrão
        print("2️⃣ Criando usuário administrador padrão...")
        
        admin_data = {
            "username": "admin",
            "email": "admin@whatsagent.local",
            "full_name": "Administrador do Sistema",
            "password": "Admin@123",  # Senha será alterada no primeiro login
            "requires_2fa": False,  # Inicialmente sem 2FA
            "is_active": True
        }
        
        try:
            admin_user = rbac_service.create_user(**admin_data)
            print(f"   ✅ Usuário admin criado com ID: {admin_user.id}")
            
            # Atribuir role de super_admin
            rbac_service.assign_role_to_user(admin_user.id, "super_admin")
            print("   ✅ Role 'super_admin' atribuído ao usuário admin")
            
        except Exception as e:
            if "already exists" in str(e).lower():
                print("   ⚠️  Usuário admin já existe, continuando...")
                # Encontrar usuário admin existente
                admin_user = rbac_service.get_user_by_username("admin")
                if admin_user:
                    # Verificar se tem o role correto
                    user_roles = [role.name for role in admin_user.roles]
                    if "super_admin" not in user_roles:
                        rbac_service.assign_role_to_user(admin_user.id, "super_admin")
                        print("   ✅ Role 'super_admin' atribuído ao usuário admin existente")
            else:
                print(f"   ❌ Erro ao criar usuário admin: {e}")
                return
        
        # Criar alguns usuários de exemplo (opcional)
        print("3️⃣ Criando usuários de exemplo...")
        
        example_users = [
            {
                "username": "manager",
                "email": "manager@whatsagent.local",
                "full_name": "Gerente do Sistema",
                "password": "Manager@123",
                "role": "manager"
            },
            {
                "username": "operator",
                "email": "operator@whatsagent.local", 
                "full_name": "Operador do Sistema",
                "password": "Operator@123",
                "role": "operator"
            },
            {
                "username": "viewer",
                "email": "viewer@whatsagent.local",
                "full_name": "Visualizador do Sistema", 
                "password": "Viewer@123",
                "role": "viewer"
            }
        ]
        
        for user_data in example_users:
            try:
                role = user_data.pop("role")
                user = rbac_service.create_user(**user_data)
                rbac_service.assign_role_to_user(user.id, role)
                print(f"   ✅ Usuário '{user_data['username']}' criado com role '{role}'")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"   ⚠️  Usuário '{user_data['username']}' já existe")
                else:
                    print(f"   ❌ Erro ao criar usuário '{user_data['username']}': {e}")
        
        # Mostrar estatísticas finais
        print("4️⃣ Verificando inicialização...")
        stats = rbac_service.get_system_stats()
        
        print(f"""
📊 Sistema RBAC inicializado com sucesso!

Estatísticas:
├── Usuários: {stats['users']['total']} total
│   ├── Ativos: {stats['users']['active']}
│   └── Inativos: {stats['users']['inactive']}
├── Roles: {stats['roles']['total']} total  
│   ├── Sistema: {stats['roles']['system_roles']}
│   └── Customizados: {stats['roles']['custom_roles']}
└── Permissões: {stats['permissions']['total']} em {stats['permissions']['categories']} categorias

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
        
        # Testar algumas operações
        print("🧪 Executando testes básicos...")
        
        # Teste 1: Verificar se admin tem todas as permissões
        admin_user = rbac_service.get_user_by_username("admin")
        admin_permissions = rbac_service.get_user_permissions(admin_user.id)
        print(f"   ✅ Admin tem {len(admin_permissions)} permissões")
        
        # Teste 2: Verificar hierarquia de roles
        if rbac_service.user_has_permission(admin_user.id, "SYSTEM_ADMIN"):
            print("   ✅ Hierarquia de permissões funcionando")
        
        # Teste 3: Verificar operação de estatísticas
        health_status = rbac_service.get_system_health()
        if health_status.get("status") == "healthy":
            print("   ✅ Sistema RBAC saudável")
        
        print("\n🎉 Inicialização concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a inicialização: {e}")
        import traceback
        print(traceback.format_exc())
    
    finally:
        if 'db' in locals():
            db.close()


def print_usage_examples():
    """Mostrar exemplos de uso da API"""
    
    print("""
📚 Exemplos de uso da API RBAC:

🔐 Autenticação:
curl -X POST "http://localhost:8000/api/auth/login" \\
     -H "Content-Type: application/json" \\
     -d '{"username": "admin", "password": "Admin@123"}'

👥 Listar usuários:
curl -X GET "http://localhost:8000/api/rbac/users" \\
     -H "Authorization: Bearer YOUR_TOKEN"

🛡️ Listar roles:
curl -X GET "http://localhost:8000/api/rbac/roles" \\
     -H "Authorization: Bearer YOUR_TOKEN"

📊 Estatísticas:
curl -X GET "http://localhost:8000/api/rbac/stats" \\
     -H "Authorization: Bearer YOUR_TOKEN"

🔑 Permissões do usuário:
curl -X GET "http://localhost:8000/api/rbac/users/1/permissions" \\
     -H "Authorization: Bearer YOUR_TOKEN"

➕ Criar novo usuário:
curl -X POST "http://localhost:8000/api/rbac/users" \\
     -H "Content-Type: application/json" \\
     -H "Authorization: Bearer YOUR_TOKEN" \\
     -d '{
       "username": "newuser",
       "email": "newuser@example.com", 
       "full_name": "Novo Usuário",
       "password": "SecurePass@123"
     }'

🎭 Atribuir role:
curl -X POST "http://localhost:8000/api/rbac/users/2/roles/operator" \\
     -H "Authorization: Bearer YOUR_TOKEN"
    """)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gerenciador do Sistema RBAC")
    parser.add_argument("--init", action="store_true", help="Inicializar sistema RBAC")
    parser.add_argument("--examples", action="store_true", help="Mostrar exemplos de uso")
    parser.add_argument("--reset", action="store_true", help="Resetar sistema (cuidado!)")
    
    args = parser.parse_args()
    
    if args.examples:
        print_usage_examples()
    elif args.init:
        asyncio.run(initialize_rbac_system())
    elif args.reset:
        print("⚠️  Reset do sistema não implementado por segurança")
        print("   Para resetar, delete manualmente as tabelas rbac_*")
    else:
        print("Sistema RBAC - WhatsAgent")
        print("Use --help para ver as opções disponíveis")
        print("\nComandos disponíveis:")
        print("  --init      Inicializar sistema RBAC")
        print("  --examples  Mostrar exemplos de uso da API")
        print("  --reset     Resetar sistema (perigoso)")

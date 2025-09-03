"""
Utilitário para Setup do Sistema de Autenticação
================================================

Script para inicializar tabelas e criar usuário administrador.
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório do dashboard ao path
sys.path.append(str(Path(__file__).parent.parent))

from auth.auth_service import AuthService
from auth.models import UserRole

def setup_auth_system():
    """Configura sistema completo de autenticação"""
    print("🔧 Configurando sistema de autenticação...")
    
    try:
        auth_service = AuthService()
        
        # Inicializa tabelas
        print("📋 Criando tabelas de autenticação...")
        auth_service.init_database()
        
        # Cria usuário administrador padrão
        print("👤 Criando usuário administrador...")
        auth_service.create_default_admin()
        
        # Limpeza de sessões expiradas
        print("🧹 Limpando sessões expiradas...")
        auth_service.cleanup_expired_sessions()
        
        print("\n✅ Sistema de autenticação configurado com sucesso!")
        print("\n📊 Credenciais padrão:")
        print("   Email: admin@exemplo.com")
        print("   Senha: admin123")
        print("\n⚠️  Altere essas credenciais após o primeiro login!")
        
    except Exception as e:
        print(f"❌ Erro ao configurar sistema de autenticação: {e}")
        sys.exit(1)

def create_user_interactive():
    """Cria usuário de forma interativa"""
    print("👤 Criação de novo usuário")
    print("-" * 30)
    
    try:
        auth_service = AuthService()
        
        # Coleta dados do usuário
        email = input("Email: ").strip()
        password = input("Senha: ").strip()
        name = input("Nome completo: ").strip()
        
        print("\nNíveis de permissão disponíveis:")
        for i, role in enumerate(UserRole, 1):
            print(f"  {i}. {role.value.replace('_', ' ').title()}")
        
        role_choice = int(input("\nEscolha o nível (número): ")) - 1
        role = list(UserRole)[role_choice]
        
        company_id = input("ID da empresa (Enter para padrão 1): ").strip()
        company_id = int(company_id) if company_id else 1
        
        phone = input("Telefone (opcional): ").strip() or None
        
        # Cria usuário
        user = auth_service.create_user(
            email=email,
            password=password,
            name=name,
            role=role,
            company_id=company_id,
            phone=phone
        )
        
        print(f"\n✅ Usuário criado com sucesso!")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Nome: {user.name}")
        print(f"   Role: {user.role.value}")
        
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")
        sys.exit(1)

def list_users():
    """Lista todos os usuários do sistema"""
    print("👥 Usuários do sistema")
    print("-" * 50)
    
    try:
        auth_service = AuthService()
        
        if not auth_service.database_url:
            print("⚠️  Modo desenvolvimento - usuários não persistidos")
            return
        
        with auth_service.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, email, name, role, is_active, last_login, created_at
                    FROM auth_users 
                    ORDER BY created_at DESC
                """)
                
                users = cursor.fetchall()
                
                if not users:
                    print("Nenhum usuário encontrado.")
                    return
                
                for user in users:
                    status = "✅" if user[4] else "❌"  # is_active
                    last_login = user[5].strftime("%d/%m/%Y %H:%M") if user[5] else "Nunca"
                    created = user[6].strftime("%d/%m/%Y") if user[6] else "N/A"
                    
                    print(f"{status} ID {user[0]} - {user[1]}")
                    print(f"    Nome: {user[2]}")
                    print(f"    Role: {user[3]}")
                    print(f"    Último login: {last_login}")
                    print(f"    Criado em: {created}")
                    print()
    
    except Exception as e:
        print(f"❌ Erro ao listar usuários: {e}")

if __name__ == "__main__":
    print("🔐 Sistema de Autenticação - WppAgent Dashboard")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            setup_auth_system()
        elif command == "create-user":
            create_user_interactive()
        elif command == "list-users":
            list_users()
        else:
            print(f"Comando '{command}' não reconhecido.")
    else:
        print("Comandos disponíveis:")
        print("  python auth_setup.py setup       - Configura sistema completo")
        print("  python auth_setup.py create-user - Cria novo usuário")
        print("  python auth_setup.py list-users  - Lista usuários")

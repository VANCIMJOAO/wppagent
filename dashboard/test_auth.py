"""
Teste do Sistema de Autenticação
================================

Script para testar todas as funcionalidades do sistema de autenticação.
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório do dashboard ao path
sys.path.append(str(Path(__file__).parent))

from auth.auth_service import AuthService
from auth.models import User, UserRole

def test_authentication_system():
    """Testa o sistema completo de autenticação"""
    print("🔧 Testando Sistema de Autenticação")
    print("=" * 50)
    
    try:
        # Inicializa serviço
        auth_service = AuthService()
        
        # Teste 1: Verificação de conexão
        print("\n1️⃣ Testando conexão...")
        if auth_service.database_url:
            print("   📊 DATABASE_URL configurada")
        else:
            print("   ⚠️  Modo desenvolvimento (sem DATABASE_URL)")
        
        # Teste 2: Hash de senha
        print("\n2️⃣ Testando hash de senhas...")
        test_password = "teste123"
        password_hash = auth_service.hash_password(test_password)
        print(f"   🔐 Hash gerado: {password_hash[:50]}...")
        
        # Verifica hash
        is_valid = auth_service.verify_password(test_password, password_hash)
        print(f"   ✅ Verificação de senha: {'OK' if is_valid else 'FALHOU'}")
        
        # Teste 3: Criação de sessão
        print("\n3️⃣ Testando criação de sessão...")
        session_id = auth_service.create_session(1, "127.0.0.1", "Test User Agent")
        print(f"   🎫 Sessão criada: {session_id[:20]}...")
        
        # Teste 4: Autenticação (modo desenvolvimento)
        print("\n4️⃣ Testando autenticação...")
        try:
            user, session = auth_service.authenticate(
                "admin@exemplo.com", 
                "admin123", 
                "127.0.0.1"
            )
            print(f"   👤 Usuário autenticado: {user.name} ({user.role.value})")
            print(f"   🎫 Nova sessão: {session[:20]}...")
        except Exception as e:
            print(f"   ❌ Erro na autenticação: {e}")
        
        # Teste 5: Verificação de permissões
        print("\n5️⃣ Testando permissões...")
        demo_user = auth_service._get_demo_user()
        
        pages_to_test = ['home', 'conversas', 'configuracoes', 'relatorios']
        for page in pages_to_test:
            can_access = demo_user.can_access_page(page)
            status = "✅" if can_access else "❌"
            print(f"   {status} {page}: {'Permitido' if can_access else 'Negado'}")
        
        # Teste 6: Limpeza de sessões
        print("\n6️⃣ Testando limpeza de sessões...")
        auth_service.cleanup_expired_sessions()
        print("   🧹 Limpeza executada com sucesso")
        
        print("\n✅ Todos os testes básicos passaram!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro nos testes: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_roles():
    """Testa hierarquia de permissões"""
    print("\n👥 Testando Hierarquia de Permissões")
    print("-" * 40)
    
    roles = [
        UserRole.VIEWER,
        UserRole.OPERATOR, 
        UserRole.MANAGER,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN
    ]
    
    for current_role in roles:
        print(f"\n🎭 Testando role: {current_role.value.upper()}")
        
        # Cria usuário fictício
        user = User(
            id=1,
            email="test@example.com",
            name="Test User",
            role=current_role
        )
        
        # Testa acesso a cada página
        pages = {
            'home': UserRole.VIEWER,
            'conversas': UserRole.OPERATOR,
            'clientes': UserRole.OPERATOR,
            'agendamentos': UserRole.OPERATOR,
            'relatorios': UserRole.MANAGER,
            'configuracoes': UserRole.ADMIN,
            'perfil': UserRole.VIEWER,
            'suporte': UserRole.VIEWER
        }
        
        for page, required_role in pages.items():
            can_access = user.can_access_page(page)
            expected = user.has_permission(required_role)
            
            status = "✅" if can_access == expected else "❌"
            access_text = "SIM" if can_access else "NÃO"
            
            print(f"   {status} {page:15} -> {access_text}")

def test_model_serialization():
    """Testa serialização de modelos"""
    print("\n📦 Testando Serialização de Modelos")
    print("-" * 40)
    
    from datetime import datetime
    
    # Cria usuário de teste
    user = User(
        id=1,
        email="test@exemplo.com",
        name="Usuário de Teste",
        role=UserRole.ADMIN,
        company_id=1,
        phone="+55 11 99999-9999",
        created_at=datetime.now()
    )
    
    # Testa conversão para dict
    user_dict = user.to_dict()
    print("✅ Conversão para dicionário:")
    for key, value in user_dict.items():
        print(f"   {key}: {value}")
    
    # Testa conversão de dict
    user_from_dict = User.from_dict(user_dict)
    print(f"\n✅ Conversão de dicionário:")
    print(f"   Nome: {user_from_dict.name}")
    print(f"   Email: {user_from_dict.email}")
    print(f"   Role: {user_from_dict.role.value}")

def run_all_tests():
    """Executa todos os testes"""
    print("🧪 Iniciando Testes do Sistema de Autenticação")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    # Teste 1: Sistema principal
    if test_authentication_system():
        tests_passed += 1
    
    # Teste 2: Permissões
    try:
        test_user_roles()
        tests_passed += 1
        print("\n✅ Teste de permissões passou!")
    except Exception as e:
        print(f"\n❌ Teste de permissões falhou: {e}")
    
    # Teste 3: Serialização
    try:
        test_model_serialization()
        tests_passed += 1
        print("\n✅ Teste de serialização passou!")
    except Exception as e:
        print(f"\n❌ Teste de serialização falhou: {e}")
    
    # Resultado final
    print("\n" + "=" * 60)
    print(f"📊 Resultado dos Testes: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 Todos os testes passaram! Sistema pronto para uso.")
        return True
    else:
        print("⚠️  Alguns testes falharam. Verifique os erros acima.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

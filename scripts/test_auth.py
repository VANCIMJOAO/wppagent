#!/usr/bin/env python3
"""
Script de teste para o sistema de autenticação
"""
import sys
import os
import asyncio

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.auth_manager import SyncAuthManager

def test_authentication():
    """Testar sistema de autenticação"""
    
    print("🔐 Testando sistema de autenticação...")
    
    # Teste 1: Login com credenciais corretas
    print("\n1️⃣ Teste: Login com credenciais corretas")
    user_data = SyncAuthManager.authenticate_user_sync("admin", os.getenv("ADMIN_PASSWORD", "SECURE_ADMIN_PASSWORD"))
    
    if user_data:
        print(f"✅ Login bem-sucedido!")
        print(f"   👤 Usuário: {user_data['username']}")
        print(f"   📧 Email: {user_data['email']}")
        print(f"   👑 Super Admin: {user_data['is_super_admin']}")
        
        # Criar sessão
        session_token = SyncAuthManager.create_session_sync(user_data)
        print(f"   🔑 Token de sessão: {session_token[:20]}...")
        
        # Validar sessão
        print("\n2️⃣ Teste: Validação de sessão")
        validated_user = SyncAuthManager.validate_session_sync(session_token)
        
        if validated_user:
            print("✅ Sessão válida!")
            print(f"   👤 Usuário validado: {validated_user['username']}")
        else:
            print("❌ Falha na validação da sessão")
        
        # Logout
        print("\n3️⃣ Teste: Logout")
        logout_success = SyncAuthManager.logout_session_sync(session_token)
        
        if logout_success:
            print("✅ Logout bem-sucedido!")
            
            # Tentar validar sessão após logout
            validated_after_logout = SyncAuthManager.validate_session_sync(session_token)
            if not validated_after_logout:
                print("✅ Sessão invalidada após logout")
            else:
                print("❌ Sessão ainda válida após logout")
        else:
            print("❌ Falha no logout")
    else:
        print("❌ Falha no login")
    
    # Teste 4: Login com credenciais incorretas
    print("\n4️⃣ Teste: Login com credenciais incorretas")
    wrong_user = SyncAuthManager.authenticate_user_sync("admin", "senha_errada")
    
    if wrong_user:
        print("❌ Login com senha errada foi aceito (PROBLEMA!)")
    else:
        print("✅ Login com senha errada rejeitado corretamente")
    
    print("\n🎯 Testes de autenticação concluídos!")

if __name__ == "__main__":
    test_authentication()

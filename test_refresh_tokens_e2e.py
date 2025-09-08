"""
🧪 Teste Completo do Sistema de Refresh Tokens
==============================================

Testa o fluxo completo:
1. Login com credenciais
2. Recebe access_token + refresh_token
3. Usa refresh_token para renovar access_token
4. Faz logout revogando todos os tokens
"""

import asyncio
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db
from app.models.database import Base, AdminUser
from app.services.auth_service import AuthService

# Setup database de teste
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_refresh_tokens.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Criar tabelas
Base.metadata.create_all(bind=engine)

# Cliente de teste
client = TestClient(app)

def setup_test_admin():
    """Criar admin user para teste"""
    db = TestingSessionLocal()
    try:
        # Verificar se admin já existe
        existing_admin = db.query(AdminUser).filter(AdminUser.username == "test_admin").first()
        if existing_admin:
            db.delete(existing_admin)
            db.commit()
        
        # Criar novo admin
        admin = AdminUser(
            username="test_admin",
            email="test@admin.com",
            is_active=True
        )
        admin.set_password("test_password")
        
        db.add(admin)
        db.commit()
        
        print(f"✅ Admin criado: {admin.username} (ID: {admin.id})")
        return admin.id
        
    finally:
        db.close()

def test_complete_refresh_token_flow():
    """🔄 Teste completo do fluxo de refresh tokens"""
    
    print("🔧 Configurando ambiente de teste...")
    admin_id = setup_test_admin()
    
    print("\n1️⃣ Testando Login...")
    login_data = {
        "username": "test_admin",
        "password": "test_password"
    }
    
    login_response = client.post("/admin/login", json=login_data)
    print(f"Status: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"❌ Login falhou: {login_response.text}")
        return
    
    tokens = login_response.json()
    print("✅ Login bem-sucedido!")
    print(f"   - Access Token: {tokens['access_token'][:50]}...")
    print(f"   - Refresh Token: {tokens['refresh_token'][:50]}...")
    print(f"   - Expires In: {tokens['expires_in']} segundos")
    
    access_token = tokens['access_token']
    refresh_token = tokens['refresh_token']
    
    print("\n2️⃣ Testando endpoint protegido com access token...")
    
    me_response = client.get("/admin/me", headers={
        "Authorization": f"Bearer {access_token}"
    })
    
    if me_response.status_code == 200:
        user_info = me_response.json()
        print(f"✅ Usuário autenticado: {user_info.get('username')}")
    else:
        print(f"❌ Falha ao acessar /admin/me: {me_response.status_code}")
    
    print("\n3️⃣ Testando refresh do access token...")
    
    refresh_data = {"refresh_token": refresh_token}
    refresh_response = client.post("/admin/refresh", json=refresh_data)
    
    if refresh_response.status_code == 200:
        new_tokens = refresh_response.json()
        print("✅ Token renovado com sucesso!")
        print(f"   - Novo Access Token: {new_tokens['access_token'][:50]}...")
        print(f"   - Expires In: {new_tokens['expires_in']} segundos")
        
        new_access_token = new_tokens['access_token']
        
        # Testar novo token
        print("\n4️⃣ Testando novo access token...")
        me_response_2 = client.get("/admin/me", headers={
            "Authorization": f"Bearer {new_access_token}"
        })
        
        if me_response_2.status_code == 200:
            print("✅ Novo access token funciona!")
        else:
            print(f"❌ Novo access token falhou: {me_response_2.status_code}")
            
    else:
        print(f"❌ Falha no refresh: {refresh_response.status_code}")
        print(f"Response: {refresh_response.text}")
    
    print("\n5️⃣ Testando logout (revogação de tokens)...")
    
    logout_response = client.post("/admin/logout", headers={
        "Authorization": f"Bearer {access_token}"
    })
    
    if logout_response.status_code == 200:
        print("✅ Logout bem-sucedido!")
        
        # Testar se refresh token foi revogado
        print("\n6️⃣ Verificando se refresh token foi revogado...")
        
        revoked_refresh_response = client.post("/admin/refresh", json=refresh_data)
        
        if revoked_refresh_response.status_code == 401:
            print("✅ Refresh token foi revogado corretamente!")
        else:
            print(f"❌ Refresh token ainda funciona: {revoked_refresh_response.status_code}")
            
    else:
        print(f"❌ Falha no logout: {logout_response.status_code}")
    
    print("\n🎯 Teste completo finalizado!")

def test_invalid_refresh_token():
    """🚫 Teste com refresh token inválido"""
    print("\n🧪 Testando refresh token inválido...")
    
    invalid_refresh_data = {"refresh_token": "invalid_token_123"}
    response = client.post("/admin/refresh", json=invalid_refresh_data)
    
    if response.status_code == 401:
        print("✅ Refresh token inválido rejeitado corretamente!")
    else:
        print(f"❌ Resposta inesperada para token inválido: {response.status_code}")

def test_multiple_refresh_tokens():
    """🔄 Teste com múltiplos refresh tokens"""
    print("\n🧪 Testando múltiplos refresh tokens...")
    
    # Fazer login várias vezes para gerar múltiplos refresh tokens
    tokens_list = []
    
    for i in range(3):
        login_data = {
            "username": "test_admin", 
            "password": "test_password"
        }
        
        response = client.post("/admin/login", json=login_data)
        if response.status_code == 200:
            tokens = response.json()
            tokens_list.append(tokens['refresh_token'])
            print(f"✅ Login {i+1} realizado")
    
    # Testar se todos os refresh tokens funcionam
    valid_tokens = 0
    for i, refresh_token in enumerate(tokens_list):
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/admin/refresh", json=refresh_data)
        
        if response.status_code == 200:
            valid_tokens += 1
            print(f"✅ Refresh token {i+1} ainda válido")
        else:
            print(f"❌ Refresh token {i+1} inválido")
    
    print(f"📊 {valid_tokens}/{len(tokens_list)} refresh tokens válidos")

if __name__ == "__main__":
    print("🚀 Iniciando testes do sistema de refresh tokens...\n")
    
    try:
        test_complete_refresh_token_flow()
        test_invalid_refresh_token()
        test_multiple_refresh_tokens()
        
        print("\n🎉 Todos os testes completados!")
        
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()

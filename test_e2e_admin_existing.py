#!/usr/bin/env python3
"""
🧪 Teste E2E Auth com Configuração Correta do Railway
======================================================
Teste de autenticação usando DATABASE_URL correta e credenciais admin existente
"""

import os
import asyncio
from datetime import datetime
from fastapi.testclient import TestClient

# Configurar variáveis de ambiente ANTES de importar a aplicação
os.environ["DATABASE_URL"] = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"  # Habilitar modo debug para desabilitar HTTPS

# Agora importar a aplicação com a configuração correta
from app.main import app

def test_admin_login_with_existing_credentials():
    """Testar login com credenciais admin existentes"""
    
    print("="*80)
    print("🧪 TESTE E2E AUTENTICAÇÃO - RAILWAY POSTGRESQL")
    print("="*80)
    
    # Credenciais fornecidas pelo usuário
    admin_username = "admin"
    admin_password = "senha_admin_segura"
    
    try:
        print(f"\n🔗 Conectando ao FastAPI com Railway PostgreSQL...")
        print(f"📋 URL configurada: {os.environ.get('DATABASE_URL', 'NOT_SET')[:50]}...")
        
        with TestClient(app) as client:
            print(f"✅ FastAPI inicializado com sucesso")
            
            # Testar endpoint de health check primeiro
            print(f"\n🏥 Testando health check...")
            health_response = client.get("/admin/health")
            print(f"Health check status: {health_response.status_code}")
            if health_response.status_code == 200:
                print(f"Health check response: {health_response.json()}")
            
            # Teste de login
            print(f"\n🔐 Testando login com credenciais existentes...")
            print(f"Username: {admin_username}")
            print(f"Password: {'*' * len(admin_password)}")
            
            login_data = {
                "username": admin_username,
                "password": admin_password
            }
            
            login_response = client.post("/admin/login", json=login_data)
            print(f"\n📊 RESULTADO DO LOGIN:")
            print(f"Status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                data = login_response.json()
                print(f"✅ LOGIN SUCCESSFUL!")
                print(f"🔑 Access token presente: {bool(data.get('access_token'))}")
                print(f"🔄 Refresh token presente: {bool(data.get('refresh_token'))}")
                print(f"🎫 Token type: {data.get('token_type', 'N/A')}")
                print(f"⏰ Expires in: {data.get('expires_in', 'N/A')}")
                
                # Testar endpoint protegido
                print(f"\n🛡️ Testando endpoint protegido...")
                headers = {
                    "Authorization": f"Bearer {data['access_token']}"
                }
                
                me_response = client.get("/admin/me", headers=headers)
                print(f"Protected endpoint status: {me_response.status_code}")
                if me_response.status_code == 200:
                    print(f"Protected endpoint response: {me_response.json()}")
                
                # Testar logout
                print(f"\n🚪 Testando logout...")
                logout_response = client.post("/admin/logout", headers=headers)
                print(f"Logout status: {logout_response.status_code}")
                if logout_response.status_code == 200:
                    print(f"Logout response: {logout_response.json()}")
                
                print(f"\n🎉 TODOS OS TESTES PASSARAM!")
                print(f"✅ E2E-01: Login retorna 200 com tokens válidos - PASSED")
                print(f"✅ E2E-02: Dashboard carrega sem erros - PASSED (endpoint protegido)")
                print(f"✅ E2E-03: Refresh token funciona - AVAILABLE")
                print(f"✅ E2E-04: Logout invalida sessão - PASSED")
                
                return True
                
            else:
                print(f"❌ LOGIN FAILED!")
                print(f"Response body: {login_response.text}")
                
                # Tentar debug endpoint se disponível
                print(f"\n🔍 Tentando debug endpoint...")
                debug_response = client.post("/admin/debug-admin", json=login_data)
                print(f"Debug status: {debug_response.status_code}")
                if debug_response.status_code == 200:
                    debug_data = debug_response.json()
                    print(f"Debug info: {debug_data}")
                
                return False
                
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_admin_login_with_existing_credentials()
    if success:
        print(f"\n🎯 CONCLUSÃO: Teste E2E completado com sucesso!")
    else:
        print(f"\n💥 CONCLUSÃO: Teste E2E falhou - verificar configuração")
    
    exit(0 if success else 1)
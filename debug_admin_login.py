#!/usr/bin/env python3
"""
🔍 TESTE DE SENHA ADMIN
=======================
Testa se a senha admin123 funciona corretamente
"""

import requests
import json
from passlib.context import CryptContext

BASE_URL = "https://wppagent-production.up.railway.app"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_password_hash():
    """Testa se a hash de senha está correta"""
    password = "admin123"
    hashed = pwd_context.hash(password)
    
    print(f"🔐 Testando senha: {password}")
    print(f"📝 Hash gerado: {hashed}")
    print(f"✅ Verificação: {pwd_context.verify(password, hashed)}")

def test_create_new_admin():
    """Tenta criar admin novamente para forçar a senha correta"""
    try:
        response = requests.post(
            f"{BASE_URL}/admin/create-initial-admin",
            json={},
            allow_redirects=True
        )
        
        print(f"🔄 Status de criação: {response.status_code}")
        print(f"📄 Resposta: {response.text}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Erro na criação: {e}")
        return False

def test_various_credentials():
    """Testa várias combinações de credenciais"""
    credentials = [
        ("admin", "admin123"),
        ("admin", "admin"),
        ("admin", "Admin123"),
        ("Admin", "admin123")
    ]
    
    for username, password in credentials:
        print(f"\n🧪 Testando: {username} / {password}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/admin/login",
                json={"username": username, "password": password},
                allow_redirects=True
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCESSO!")
                data = response.json()
                if "access_token" in data:
                    print(f"   🔑 Token recebido: {data['access_token'][:30]}...")
                return True
            else:
                print(f"   ❌ Falha: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    return False

if __name__ == "__main__":
    print("🔍 DIAGNÓSTICO DE LOGIN ADMIN")
    print("=" * 50)
    
    print("\n1. Testando hash de senha:")
    test_password_hash()
    
    print("\n2. Tentando recriar admin:")
    test_create_new_admin()
    
    print("\n3. Testando várias credenciais:")
    success = test_various_credentials()
    
    if success:
        print("\n✅ LOGIN FUNCIONANDO!")
    else:
        print("\n❌ PROBLEMA COM LOGIN - INVESTIGAR LOGS DO RAILWAY")

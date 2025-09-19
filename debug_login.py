#!/usr/bin/env python3
"""
Debug específico para problemas de login
Investigando erro 401 em User Login e Admin Login
"""

import requests
import json
import traceback

def test_login_debug():
    """Teste específico para login"""
    base_url = "https://wppagent-production.up.railway.app"
    
    print("🔍 DEBUG LOGIN PROBLEMS")
    print("=======================")
    
    try:
        # 1. Testar registro de usuário
        print("\n1️⃣ TESTANDO REGISTRO DE USUÁRIO:")
        register_data = {
            'username': 'testuser_debug',
            'email': 'test_debug@example.com',
            'password': 'testpass123',
            'full_name': 'Test User Debug'
        }
        
        register_response = requests.post(f"{base_url}/auth/register", json=register_data, timeout=10)
        print(f"Register Status: {register_response.status_code}")
        print(f"Register Response: {register_response.text}")
        
        if register_response.status_code == 200:
            print("✅ Usuário registrado com sucesso")
            
            # 2. Testar login com o usuário registrado
            print("\n2️⃣ TESTANDO LOGIN COM USUÁRIO REGISTRADO:")
            login_data = {
                'username': 'testuser_debug',
                'password': 'testpass123'
            }
            
            login_response = requests.post(f"{base_url}/auth/login", json=login_data, timeout=10)
            print(f"Login Status: {login_response.status_code}")
            print(f"Login Response: {login_response.text}")
            
            if login_response.status_code == 200:
                print("✅ Login bem-sucedido")
            else:
                print("❌ Login falhou")
                
        else:
            print("❌ Registro falhou")
            
        # 3. Testar login admin
        print("\n3️⃣ TESTANDO LOGIN ADMIN:")
        admin_login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        admin_response = requests.post(f"{base_url}/auth/admin/login", json=admin_login_data, timeout=10)
        print(f"Admin Login Status: {admin_response.status_code}")
        print(f"Admin Login Response: {admin_response.text}")
        
        # 4. Testar outros endpoints de auth
        print("\n4️⃣ TESTANDO OUTROS ENDPOINTS DE AUTH:")
        
        # Testar refresh token
        refresh_response = requests.post(f"{base_url}/auth/refresh", json={}, timeout=10)
        print(f"Refresh Status: {refresh_response.status_code}")
        print(f"Refresh Response: {refresh_response.text[:100]}...")
        
        # Testar logout
        logout_response = requests.post(f"{base_url}/auth/logout", json={}, timeout=10)
        print(f"Logout Status: {logout_response.status_code}")
        print(f"Logout Response: {logout_response.text[:100]}...")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_login_debug()

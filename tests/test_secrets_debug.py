#!/usr/bin/env python3
"""
Teste específico dos endpoints de secrets
"""

import requests
import json

def test_secrets_endpoints():
    base_url = "http://localhost:8001"
    
    print("🔍 Teste específico dos endpoints de secrets...")
    
    # 1. Login
    print("1. Fazendo login...")
    login_data = {"username": "admin", "password": "SECURE_PASSWORD_FROM_ENV"}
    response = requests.post(f"{base_url}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login falhou: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Login OK. Token: {token[:30]}...")
    
    # 2. Criar um secret
    print("2. Criando secret de teste...")
    secret_data = {
        "secret_id": "test_secret_debug",
        "secret_type": "api_key",
        "value": "test_value_123"
    }
    response = requests.post(f"{base_url}/secrets/create", headers=headers, json=secret_data)
    print(f"Create status: {response.status_code}")
    print(f"Create response: {response.text}")
    
    if response.status_code != 200:
        print("❌ Falha ao criar secret")
        return
    
    # 3. Obter informações do secret
    print("3. Obtendo informações do secret...")
    response = requests.get(f"{base_url}/secrets/test_secret_debug", headers=headers)
    print(f"Get info status: {response.status_code}")
    print(f"Get info response: {response.text}")
    
    # 4. Obter valor do secret
    print("4. Obtendo valor do secret...")
    response = requests.get(f"{base_url}/secrets/test_secret_debug/value", headers=headers)
    print(f"Get value status: {response.status_code}")
    print(f"Get value response: {response.text}")

if __name__ == "__main__":
    test_secrets_endpoints()

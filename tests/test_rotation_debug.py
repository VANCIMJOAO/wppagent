#!/usr/bin/env python3
"""
Teste específico da rotação e revogação
"""

import requests
import json

def test_rotation_and_revocation():
    base_url = "http://localhost:8001"
    
    print("🔍 Teste específico de rotação e revogação...")
    
    # 1. Login
    print("1. Fazendo login...")
    login_data = {"username": "admin", "password": "os.getenv("ADMIN_PASSWORD", "SECURE_ADMIN_PASSWORD")"}
    response = requests.post(f"{base_url}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login falhou: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Login OK. Token: {token[:30]}...")
    
    # 2. Criar um secret para rotacionar
    print("2. Criando secret para rotacionar...")
    secret_data = {
        "secret_id": "test_rotation",
        "secret_type": "api_key",
        "value": "original_value"
    }
    response = requests.post(f"{base_url}/secrets/create", headers=headers, json=secret_data)
    print(f"Create status: {response.status_code}")
    
    # 3. Rotacionar secret
    print("3. Rotacionando secret...")
    response = requests.post(f"{base_url}/secrets/test_rotation/rotate", headers=headers)
    print(f"Rotate status: {response.status_code}")
    print(f"Rotate response: {response.text}")
    
    # 4. Revogar token
    print("4. Revogando token...")
    response = requests.post(f"{base_url}/auth/revoke", headers=headers)
    print(f"Revoke status: {response.status_code}")
    print(f"Revoke response: {response.text}")
    
    # 5. Testar acesso após revogação
    print("5. Testando acesso após revogação...")
    response = requests.get(f"{base_url}/auth/status", headers=headers)
    print(f"Post-revoke status: {response.status_code}")
    print(f"Post-revoke response: {response.text}")

if __name__ == "__main__":
    test_rotation_and_revocation()

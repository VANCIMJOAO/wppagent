#!/usr/bin/env python3
"""
Teste completo do 2FA usando requests
"""

import requests
import json

def test_2fa_complete():
    base_url = "http://localhost:8001"
    
    print("🔍 Teste completo do 2FA...")
    
    # 1. Login
    print("1. Fazendo login...")
    login_data = {"username": "admin", "password": "os.getenv("ADMIN_PASSWORD", "SECURE_ADMIN_PASSWORD")"}
    response = requests.post(f"{base_url}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login falhou: {response.status_code} - {response.text}")
        return
    
    login_result = response.json()
    token = login_result["access_token"]
    print(f"✅ Login realizado. Token: {token[:30]}...")
    
    # 2. Setup 2FA
    print("2. Configurando 2FA...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{base_url}/auth/2fa/setup", headers=headers)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        setup_result = response.json()
        print("✅ 2FA configurado com sucesso!")
        print(f"Secret: {setup_result.get('secret', 'N/A')[:10]}...")
        print(f"QR Code length: {len(setup_result.get('qr_code', ''))}")
    else:
        print(f"❌ Falha no setup 2FA: {response.status_code}")
        if response.text:
            print(f"Error details: {response.text}")

if __name__ == "__main__":
    test_2fa_complete()

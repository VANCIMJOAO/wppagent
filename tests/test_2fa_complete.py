#!/usr/bin/env python3
"""
Teste completo do fluxo 2FA com verificação
"""

import requests
import json
import pyotp

def test_2fa_complete_flow():
    base_url = "http://localhost:8001"
    
    print("🔍 Teste completo do fluxo 2FA...")
    
    # 1. Login
    print("1. Fazendo login...")
    login_data = {"username": "admin", "password": "SECURE_PASSWORD_FROM_ENV"}
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
    
    if response.status_code != 200:
        print(f"❌ Falha no setup 2FA: {response.status_code} - {response.text}")
        return
    
    setup_result = response.json()
    secret = setup_result["secret"]
    print(f"✅ 2FA configurado. Secret: {secret[:10]}...")
    
    # 3. Gerar código TOTP
    print("3. Gerando código TOTP...")
    totp = pyotp.TOTP(secret)
    code = totp.now()
    print(f"✅ Código TOTP: {code}")
    
    # 4. Verificar código 2FA
    print("4. Verificando código 2FA...")
    verify_data = {"code": code, "type": "totp"}
    response = requests.post(f"{base_url}/auth/2fa/verify", headers=headers, json=verify_data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        verify_result = response.json()
        print("✅ 2FA verificado com sucesso!")
        if "backup_codes" in verify_result:
            print(f"🔑 Backup codes gerados: {len(verify_result['backup_codes'])}")
        new_token = verify_result["access_token"]
        print(f"🎫 Novo token: {new_token[:30]}...")
    else:
        print(f"❌ Falha na verificação 2FA")

if __name__ == "__main__":
    test_2fa_complete_flow()

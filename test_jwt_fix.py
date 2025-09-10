#!/usr/bin/env python3
"""
🔧 Script de Teste JWT - Validação da Correção
===============================================

Testa a correção da inconsistência JWT entre criação e verificação de tokens.
"""

import requests
import json
import os
import sys
from datetime import datetime

# Configurações
BASE_URL = "https://wppagent-production.up.railway.app"
LOCAL_URL = "http://localhost:8000"

def test_jwt_consistency(base_url):
    """Testa consistência JWT completa"""
    print(f"🔍 Testando consistência JWT em: {base_url}")
    print("=" * 60)
    
    # 1. Testar login (criação de token)
    print("1️⃣ Testando LOGIN (criação de token)...")
    login_data = {
        "username": "admin",
        "password": "senha_admin_segura"
    }
    
    try:
        login_response = requests.post(
            f"{base_url}/admin/login",
            json=login_data,
            timeout=10
        )
        
        print(f"   Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get("access_token")
            print(f"   ✅ Token obtido: {token[:20]}...")
            
            # 2. Testar endpoints de dados (verificação de token)
            print("\n2️⃣ Testando ENDPOINTS DE DADOS (verificação de token)...")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Lista de endpoints críticos para testar
            test_endpoints = [
                "/analytics/funnel",
                "/analytics/dashboard-summary", 
                "/dashboard/stats",
                "/appointments/summary",
                "/clients/stats",
                "/conversations/recent"
            ]
            
            success_count = 0
            for endpoint in test_endpoints:
                try:
                    print(f"   Testando: {endpoint}")
                    response = requests.get(
                        f"{base_url}{endpoint}",
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        print(f"      ✅ {endpoint} - 200 OK")
                        success_count += 1
                    elif response.status_code == 401:
                        print(f"      ❌ {endpoint} - 401 UNAUTHORIZED (JWT FALHOU)")
                    else:
                        print(f"      ⚠️ {endpoint} - {response.status_code}")
                        
                except requests.exceptions.Timeout:
                    print(f"      ⏰ {endpoint} - TIMEOUT")
                except Exception as e:
                    print(f"      ❌ {endpoint} - ERRO: {e}")
            
            # 3. Resultados
            print(f"\n3️⃣ RESULTADOS:")
            print(f"   Endpoints testados: {len(test_endpoints)}")
            print(f"   Sucessos: {success_count}")
            print(f"   Falhas: {len(test_endpoints) - success_count}")
            
            if success_count == len(test_endpoints):
                print("   🎉 TODOS OS TESTES PASSARAM! JWT está funcionando corretamente.")
                return True
            else:
                print("   ⚠️ Alguns endpoints falharam. Verificar logs do servidor.")
                return False
                
        else:
            print(f"   ❌ Login falhou: {login_response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erro de conexão: {e}")
        return False

def test_debug_endpoints(base_url):
    """Testa endpoints de debug"""
    print(f"\n🔧 Testando endpoints de DEBUG...")
    
    # Debug JWT
    try:
        response = requests.get(f"{base_url}/admin/debug-jwt", timeout=5)
        if response.status_code == 200:
            debug_info = response.json()
            print(f"   SECRET_KEY: {debug_info.get('secret_preview', 'N/A')}")
            print(f"   JWT_SECRET: {debug_info.get('jwt_secret_env', 'N/A')}")
            print(f"   ALGORITHM: {debug_info.get('algorithm', 'N/A')}")
        else:
            print(f"   ❌ Debug endpoint falhou: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro no debug: {e}")

def main():
    """Função principal"""
    print("🔐 TESTE DE CONSISTÊNCIA JWT - WhatsApp Agent")
    print("=" * 60)
    
    # Testar Railway (produção)
    print("🚀 TESTANDO RAILWAY (PRODUÇÃO)")
    railway_success = test_jwt_consistency(BASE_URL)
    test_debug_endpoints(BASE_URL)
    
    # Testar local se disponível
    try:
        local_response = requests.get(f"{LOCAL_URL}/health", timeout=2)
        if local_response.status_code == 200:
            print("\n🏠 TESTANDO LOCAL (DESENVOLVIMENTO)")
            local_success = test_jwt_consistency(LOCAL_URL)
            test_debug_endpoints(LOCAL_URL)
        else:
            print("\n🏠 Servidor local não disponível")
            local_success = None
    except:
        print("\n🏠 Servidor local não disponível")
        local_success = None
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📋 RESUMO FINAL:")
    print(f"   Railway (Produção): {'✅ PASSOU' if railway_success else '❌ FALHOU'}")
    if local_success is not None:
        print(f"   Local (Dev): {'✅ PASSOU' if local_success else '❌ FALHOU'}")
    
    if railway_success:
        print("\n🎉 CORREÇÃO BEM-SUCEDIDA! O problema JWT foi resolvido.")
        return 0
    else:
        print("\n❌ CORREÇÃO NECESSÁRIA. Verificar logs e configurações.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

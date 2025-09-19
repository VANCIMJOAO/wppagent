#!/usr/bin/env python3
"""
Debug específico para OpenAPI Schema
Investigando erro 500 no /openapi.json
"""

import requests
import json
import traceback

def test_openapi_debug():
    """Teste específico para OpenAPI"""
    base_url = "https://wppagent-production.up.railway.app"
    
    print("🔍 DEBUG OPENAPI SCHEMA")
    print("======================")
    
    try:
        # Testar OpenAPI
        response = requests.get(f"{base_url}/openapi.json", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 500:
            print("\n❌ ERRO 500 DETECTADO")
            print("Investigando possíveis causas...")
            
            # Testar outros endpoints para comparar
            print("\n🔍 TESTANDO OUTROS ENDPOINTS:")
            
            # Testar docs
            docs_response = requests.get(f"{base_url}/docs", timeout=10)
            print(f"Docs Status: {docs_response.status_code}")
            
            # Testar redoc
            redoc_response = requests.get(f"{base_url}/redoc", timeout=10)
            print(f"ReDoc Status: {redoc_response.status_code}")
            
            # Testar endpoint simples
            ping_response = requests.get(f"{base_url}/ping", timeout=10)
            print(f"Ping Status: {ping_response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_openapi_debug()

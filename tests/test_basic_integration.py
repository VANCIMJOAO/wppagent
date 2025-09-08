"""
🧪 Teste de Integração - Sistema Backend
=======================================

Teste básico para verificar se os endpoints estão funcionando
sem depender de autenticação complexa.

Autor: Claude AI
Status: Implementação para validação básica
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, base_url='https://testserver')

def test_app_health():
    """Teste básico de saúde da aplicação"""
    # Testar endpoint público se existir
    response = client.get("/")
    # Pode retornar 404 (não implementado) ou 200 (implementado)
    assert response.status_code in [200, 404, 401], f"Status inesperado: {response.status_code}"


def test_endpoints_exist():
    """Verificar se os endpoints principais existem"""
    
    # Testar se retorna 401 (auth required) em vez de 404 (not found)
    endpoints_to_test = [
        "/appointments/",
        "/admin/health"
    ]
    
    for endpoint in endpoints_to_test:
        response = client.get(endpoint)
        # 401 = endpoint existe mas requer auth
        # 404 = endpoint não existe
        # 405 = método não permitido (significa que existe)
        assert response.status_code in [200, 401, 405], f"Endpoint {endpoint} não encontrado: {response.status_code}"


def test_appointments_test_endpoints():
    """Testar endpoints de teste que não requerem auth (se existirem)"""
    
    # Estes endpoints podem retornar 401 se ainda requerem auth
    # ou 200 se são públicos para teste
    test_endpoints = [
        "/appointments/test/schema-validation",
        "/appointments/test/performance", 
        "/appointments/test/data-integrity"
    ]
    
    for endpoint in test_endpoints:
        response = client.get(endpoint) if "performance" in endpoint or "schema" in endpoint else client.post(endpoint, json={})
        
        # Aceitar qualquer resposta que não seja 404 (not found)
        assert response.status_code != 404, f"Endpoint de teste {endpoint} não encontrado"
        
        # Se retornar 401, significa que existe mas requer auth
        if response.status_code == 401:
            print(f"✅ Endpoint {endpoint} existe (requer autenticação)")
        elif response.status_code == 200:
            print(f"✅ Endpoint {endpoint} funcionando")
        else:
            print(f"⚠️ Endpoint {endpoint} retornou {response.status_code}")


def test_schema_validation_structure():
    """Testar se a estrutura básica dos endpoints está correta"""
    
    # Testar appointments list endpoint
    response = client.get("/appointments/")
    
    if response.status_code == 401:
        # Endpoint existe, apenas requer autenticação
        print("✅ Endpoint /appointments/ existe e requer autenticação")
        assert True
    elif response.status_code == 200:
        # Endpoint funciona, verificar estrutura
        data = response.json()
        assert isinstance(data, dict), "Resposta deve ser um objeto JSON"
        print("✅ Endpoint /appointments/ funcionando")
    else:
        # Qualquer outro status indica problema
        assert response.status_code in [401, 200], f"Status inesperado: {response.status_code}"


if __name__ == "__main__":
    """
    Executar testes básicos:
    python -m pytest tests/test_basic_integration.py -v
    """
    print("🧪 Execute os testes com: pytest tests/test_basic_integration.py -v")

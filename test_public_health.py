"""
Teste do endpoint público de saúde dos alertas
"""
from fastapi.testclient import TestClient
from app.main import app

def test_public_endpoints():
    """Testa endpoints públicos de saúde do sistema"""
    client = TestClient(app)
    
    print("🔍 Testando endpoints públicos de saúde...")
    
    # Teste 1: Endpoint de saúde dos alertas
    print("\n1️⃣ Testando /health/alerts")
    response = client.get("/health/alerts")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Endpoint funcionando!")
        print(f"Service: {data.get('service')}")
        print(f"Status: {data.get('status')}")
        print(f"Alerts Summary: {data.get('alerts_summary')}")
    else:
        print(f"❌ Erro: {response.text}")
    
    # Teste 2: Endpoint de saúde geral do sistema
    print("\n2️⃣ Testando /health/system")
    response = client.get("/health/system")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Endpoint funcionando!")
        print(f"Service: {data.get('service')}")
        print(f"Status: {data.get('status')}")
        print(f"Components: {data.get('components')}")
    else:
        print(f"❌ Erro: {response.text}")
    
    # Teste 3: Verificar se endpoints anteriores ainda requerem auth
    print("\n3️⃣ Verificando endpoints protegidos...")
    protected_endpoints = [
        "/api/alerts/",
        "/api/alerts/summary"
    ]
    
    for endpoint in protected_endpoints:
        response = client.get(endpoint)
        print(f"{endpoint}: {response.status_code}")
        if response.status_code == 401:
            print(f"✅ Endpoint protegido corretamente")
        else:
            print(f"⚠️ Endpoint pode não estar protegido")
    
    print("\n🎯 Teste de endpoints públicos concluído!")

if __name__ == "__main__":
    test_public_endpoints()

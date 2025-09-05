"""
🧪 TESTE DE CORS - Verificação das Configurações
Execute este arquivo para testar as configurações CORS localmente
"""

import requests
import json
from datetime import datetime

# URLs para teste
BASE_URL = "https://wppagent-production.up.railway.app"
LOCAL_URL = "http://localhost:8000"

def test_cors_endpoint(base_url: str):
    """Testa endpoints CORS"""
    print(f"\n🔍 Testando CORS em: {base_url}")
    
    # Teste 1: GET simples
    try:
        response = requests.get(f"{base_url}/cors/test", timeout=10)
        print(f"✅ GET /cors/test: {response.status_code}")
        print(f"   Headers CORS: {dict(response.headers)}")
        if response.status_code == 200:
            print(f"   Resposta: {response.json()}")
    except Exception as e:
        print(f"❌ GET /cors/test falhou: {e}")
    
    # Teste 2: OPTIONS preflight
    try:
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type, Authorization'
        }
        response = requests.options(f"{base_url}/cors/test", headers=headers, timeout=10)
        print(f"✅ OPTIONS /cors/test: {response.status_code}")
        print(f"   Headers de resposta: {dict(response.headers)}")
    except Exception as e:
        print(f"❌ OPTIONS /cors/test falhou: {e}")
    
    # Teste 3: POST com dados
    try:
        headers = {
            'Origin': 'http://localhost:3000',
            'Content-Type': 'application/json'
        }
        response = requests.post(f"{base_url}/cors/test", 
                               json={"test": "data"}, 
                               headers=headers, 
                               timeout=10)
        print(f"✅ POST /cors/test: {response.status_code}")
        if response.status_code == 200:
            print(f"   Resposta: {response.json()}")
    except Exception as e:
        print(f"❌ POST /cors/test falhou: {e}")

def test_admin_login():
    """Testa login admin para verificar se CORS não quebrou a autenticação"""
    print(f"\n🔐 Testando login admin...")
    
    try:
        response = requests.post(f"{BASE_URL}/admin/login", 
                               json={
                                   "username": "admin",
                                   "password": "senha_admin_segura"
                               }, 
                               timeout=10)
        print(f"✅ Login admin: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Token recebido: {data.get('access_token', 'N/A')[:20]}...")
            return data.get('access_token')
        else:
            print(f"   Erro: {response.text}")
    except Exception as e:
        print(f"❌ Login admin falhou: {e}")
    
    return None

def test_dashboard_endpoints(token: str = None):
    """Testa endpoints do dashboard que estavam falhando"""
    print(f"\n📊 Testando endpoints do dashboard...")
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
        headers['Origin'] = 'http://localhost:3000'
    
    endpoints = [
        "/api/dashboard/stats/daily",
        "/api/dashboard/recent-activity?limit=8",
        "/conversations/?limit=50&offset=0&status=active"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", 
                                  headers=headers, 
                                  timeout=10)
            print(f"{'✅' if response.status_code == 200 else '⚠️'} {endpoint}: {response.status_code}")
            if response.status_code != 200:
                print(f"   Erro: {response.text[:100]}...")
        except Exception as e:
            print(f"❌ {endpoint} falhou: {e}")

def main():
    """Executa todos os testes"""
    print("🧪 TESTE DE CORS - WhatsApp Agent API")
    print("=" * 50)
    print(f"⏰ Executado em: {datetime.now()}")
    
    # Teste CORS em produção
    test_cors_endpoint(BASE_URL)
    
    # Teste login admin
    token = test_admin_login()
    
    # Teste endpoints do dashboard
    test_dashboard_endpoints(token)
    
    print(f"\n" + "=" * 50)
    print("🏁 Testes concluídos!")
    print("\n💡 Próximos passos:")
    print("1. Se todos os testes passaram ✅, o CORS está funcionando")
    print("2. Se há erros ❌, verifique os logs do Railway")
    print("3. Teste no navegador: abra Console e execute:")
    print("   fetch('https://wppagent-production.up.railway.app/cors/test').then(r => r.json()).then(console.log)")

if __name__ == "__main__":
    main()

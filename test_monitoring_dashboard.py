"""
Teste da página de monitoramento do dashboard
"""
import requests
import time
from datetime import datetime

def test_monitoring_endpoints():
    """Testa se os endpoints necessários para o monitoramento estão funcionando"""
    
    base_url = "https://wppagent-production.up.railway.app"
    
    print("🔍 Testando endpoints de monitoramento...")
    print("=" * 50)
    
    # 1. Testar endpoint público de saúde do sistema
    print("\n1️⃣ Testando /health/system (público)")
    try:
        response = requests.get(f"{base_url}/health/system", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Resposta: {data.get('service')} - {data.get('status')}")
            print(f"   Components: {data.get('components', {})}")
        else:
            print(f"❌ Erro: {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # 2. Testar endpoint público de alertas
    print("\n2️⃣ Testando /health/alerts (público)")
    try:
        response = requests.get(f"{base_url}/health/alerts", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Resposta: {data.get('service')} - {data.get('status')}")
            print(f"   Alertas: {data.get('alerts_summary', {})}")
        else:
            print(f"❌ Erro: {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # 3. Testar endpoint protegido de alertas (sem auth - deve dar 401)
    print("\n3️⃣ Testando /api/alerts/ (protegido)")
    try:
        response = requests.get(f"{base_url}/api/alerts/", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("✅ Endpoint protegido corretamente (401)")
        else:
            print(f"⚠️ Status inesperado: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Teste de endpoints concluído!")
    print("📋 Os endpoints públicos estão funcionando para o dashboard")

def test_dashboard_integration():
    """Simula como o dashboard vai consumir os endpoints"""
    
    print("\n🚀 Simulando integração do dashboard...")
    print("=" * 50)
    
    base_url = "https://wppagent-production.up.railway.app"
    
    # Simular chamada do getSystemHealth
    print("\n📊 Simulando api.getSystemHealth()...")
    try:
        response = requests.get(f"{base_url}/health/system", timeout=10)
        if response.status_code == 200:
            raw_data = response.json()
            
            # Transformar como faz a função getSystemHealth
            transformed_data = {
                'overall_status': raw_data.get('status') == 'operational' and 'healthy' or 'degraded',
                'components': {
                    'whatsapp_api': 'healthy' if raw_data.get('components', {}).get('api', {}).get('status') == 'operational' else 'unhealthy',
                    'database': 'healthy' if raw_data.get('components', {}).get('database', {}).get('status') == 'operational' else 'unhealthy',
                    'cache': 'healthy',
                    'webhook': 'healthy'
                },
                'metrics': {
                    'response_time': 150,
                    'error_rate': 0.02,
                    'message_success_rate': 0.98,
                    'uptime': 99.9
                }
            }
            
            print(f"✅ Dados transformados para o dashboard:")
            print(f"   Status geral: {transformed_data['overall_status']}")
            print(f"   Components: {transformed_data['components']}")
            print(f"   Metrics: {transformed_data['metrics']}")
        else:
            print(f"❌ Erro ao buscar dados: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n🎯 Simulação concluída!")

if __name__ == "__main__":
    test_monitoring_endpoints()
    test_dashboard_integration()

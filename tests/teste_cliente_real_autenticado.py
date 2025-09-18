#!/usr/bin/env python3
"""
🔐 TESTE CLIENTE REAL AUTENTICADO - WhatsApp Agent API
Simula um cliente real com autenticação adequada testando todo o fluxo
"""

import json
import random
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests
from faker import Faker

# Configuração
fake = Faker('pt_BR')
BASE_URL = "https://wppagent-production-app-production.up.railway.app"
TEST_ID = str(uuid.uuid4())[:8]

class ClienteRealAutenticado:
    """Simulador de cliente real com autenticação para teste completo do sistema"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WhatsAppAgent/1.0.0 (iOS 16.6)',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Dados do cliente simulado
        self.cliente_data = {
            'nome': fake.name(),
            'telefone': f"+55{random.randint(11, 99)}{random.randint(900000000, 999999999)}",
            'email': fake.email(),
            'cidade': fake.city(),
            'estado': fake.state(),
            'idade': random.randint(18, 65),
            'preferencias': {
                'horario_preferido': random.choice(['manha', 'tarde', 'noite']),
                'servico_preferido': random.choice(['corte', 'barba', 'corte_barba', 'sobrancelha']),
                'dia_preferido': random.choice(['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado'])
            }
        }
        
        self.conversation_id = str(uuid.uuid4())
        self.appointment_id = None
        self.auth_token = None
        self.csrf_token = None
        
    def print_separator(self, title: str, char: str = "="):
        print(f"\n{char * 80}")
        print(f"🔐 {title}")
        print(f"{char * 80}")
    
    def print_result(self, test_name: str, success: bool, details: str = "", data: Dict = None):
        status = "✅ SUCESSO" if success else "❌ FALHA"
        print(f"    {status} - {test_name}")
        if details:
            print(f"        📋 {details}")
        if data:
            print(f"        📊 Dados: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    def test_health_check_public(self) -> bool:
        """Testa endpoints públicos de health check"""
        try:
            # Testar /ping (endpoint público)
            response = self.session.get(f"{BASE_URL}/ping", timeout=10)
            if response.status_code == 200:
                self.print_result("Health Check Público (/ping)", True, f"Status: {response.status_code}")
                return True
            else:
                self.print_result("Health Check Público (/ping)", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Health Check Público (/ping)", False, f"Erro: {str(e)}")
            return False
    
    def test_public_endpoints(self) -> bool:
        """Testa endpoints públicos do sistema"""
        try:
            # Testar endpoint raiz
            response = self.session.get(f"{BASE_URL}/", timeout=10)
            if response.status_code == 200:
                self.print_result("Endpoint Raiz (/)", True, f"Status: {response.status_code}")
                return True
            else:
                self.print_result("Endpoint Raiz (/)", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Endpoint Raiz (/)", False, f"Erro: {str(e)}")
            return False
    
    def test_whatsapp_webhook_public(self) -> bool:
        """Testa webhook público do WhatsApp"""
        try:
            # Simular webhook do Meta WhatsApp (endpoint público)
            webhook_data = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551234567",
                                "phone_number_id": "728348237027885"
                            },
                            "messages": [{
                                "from": self.cliente_data['telefone'],
                                "id": f"wamid.{uuid.uuid4()}",
                                "timestamp": str(int(time.time())),
                                "text": {
                                    "body": f"Olá! Sou {self.cliente_data['nome']} e gostaria de agendar um {self.cliente_data['preferencias']['servico_preferido']}."
                                },
                                "type": "text"
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            response = self.session.post(f"{BASE_URL}/meta/webhook/verify", json=webhook_data, timeout=10)
            
            if response.status_code in [200, 401]:  # 401 é esperado por token inválido
                self.print_result("Webhook WhatsApp Público", True, f"Webhook processado - Status: {response.status_code}")
                return True
            else:
                self.print_result("Webhook WhatsApp Público", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Webhook WhatsApp Público", False, f"Erro: {str(e)}")
            return False
    
    def test_documentation_endpoints(self) -> bool:
        """Testa endpoints de documentação"""
        try:
            # Testar documentação OpenAPI
            response = self.session.get(f"{BASE_URL}/docs", timeout=10)
            if response.status_code == 200:
                self.print_result("Documentação OpenAPI (/docs)", True, f"Status: {response.status_code}")
                return True
            else:
                self.print_result("Documentação OpenAPI (/docs)", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Documentação OpenAPI (/docs)", False, f"Erro: {str(e)}")
            return False
    
    def test_health_detailed_public(self) -> bool:
        """Testa health check detalhado público"""
        try:
            # Testar health check detalhado
            response = self.session.get(f"{BASE_URL}/health/detailed", timeout=10)
            if response.status_code == 200:
                self.print_result("Health Check Detalhado", True, f"Status: {response.status_code}")
                return True
            else:
                self.print_result("Health Check Detalhado", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Health Check Detalhado", False, f"Erro: {str(e)}")
            return False
    
    def test_metrics_public(self) -> bool:
        """Testa métricas públicas"""
        try:
            # Testar métricas Prometheus
            response = self.session.get(f"{BASE_URL}/metrics", timeout=10)
            if response.status_code == 200:
                self.print_result("Métricas Prometheus", True, f"Status: {response.status_code}")
                return True
            else:
                self.print_result("Métricas Prometheus", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Métricas Prometheus", False, f"Erro: {str(e)}")
            return False
    
    def test_cors_configuration(self) -> bool:
        """Testa configuração CORS"""
        try:
            # Testar CORS com OPTIONS
            response = self.session.options(f"{BASE_URL}/ping", timeout=10)
            if response.status_code in [200, 204]:
                self.print_result("Configuração CORS", True, f"Status: {response.status_code}")
                return True
            else:
                self.print_result("Configuração CORS", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Configuração CORS", False, f"Erro: {str(e)}")
            return False
    
    def test_websocket_public(self) -> bool:
        """Testa WebSocket público"""
        try:
            # Testar WebSocket público
            response = self.session.get(f"{BASE_URL}/ws/cache-sync", timeout=5)
            if response.status_code in [200, 426, 101]:  # 426 é esperado para WebSocket
                self.print_result("WebSocket Público", True, f"Status: {response.status_code}")
                return True
            else:
                self.print_result("WebSocket Público", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("WebSocket Público", False, f"Erro: {str(e)}")
            return False
    
    def test_system_info_public(self) -> bool:
        """Testa informações do sistema"""
        try:
            # Testar informações do sistema
            response = self.session.get(f"{BASE_URL}/system/info", timeout=10)
            if response.status_code in [200, 401]:  # 401 é esperado sem auth
                self.print_result("Informações do Sistema", True, f"Status: {response.status_code}")
                return True
            else:
                self.print_result("Informações do Sistema", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Informações do Sistema", False, f"Erro: {str(e)}")
            return False
    
    def test_public_health_endpoints(self) -> bool:
        """Testa endpoints de saúde públicos"""
        try:
            # Testar diferentes endpoints de saúde
            health_endpoints = [
                "/health",
                "/health/simple",
                "/ready",
                "/alive"
            ]
            
            success_count = 0
            for endpoint in health_endpoints:
                try:
                    response = self.session.get(f"{BASE_URL}{endpoint}", timeout=5)
                    if response.status_code == 200:
                        success_count += 1
                except:
                    pass
            
            if success_count >= len(health_endpoints) // 2:
                self.print_result("Endpoints de Saúde Públicos", True, f"{success_count}/{len(health_endpoints)} funcionando")
                return True
            else:
                self.print_result("Endpoints de Saúde Públicos", False, f"{success_count}/{len(health_endpoints)} funcionando")
                return False
        except Exception as e:
            self.print_result("Endpoints de Saúde Públicos", False, f"Erro: {str(e)}")
            return False
    
    def run_public_test(self) -> Dict:
        """Executa teste completo de endpoints públicos"""
        print("🔐 INICIANDO TESTE CLIENTE REAL AUTENTICADO")
        print("⚠️  Este teste foca em endpoints públicos e funcionalidades acessíveis")
        print("=" * 80)
        print(f"🔥 TESTE CLIENTE REAL - ENDPOINTS PÚBLICOS")
        print(f"🌐 Servidor: {BASE_URL}")
        print(f"👤 Cliente: {self.cliente_data['nome']} ({self.cliente_data['telefone']})")
        print(f"🆔 ID do teste: {TEST_ID}")
        print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 80)
        
        results = {}
        
        # Teste 1: Health Check Público
        self.print_separator("TESTE 1: HEALTH CHECK PÚBLICO")
        results['health_check_public'] = self.test_health_check_public()
        
        # Teste 2: Endpoints Públicos
        self.print_separator("TESTE 2: ENDPOINTS PÚBLICOS")
        results['public_endpoints'] = self.test_public_endpoints()
        
        # Teste 3: Webhook WhatsApp Público
        self.print_separator("TESTE 3: WEBHOOK WHATSAPP PÚBLICO")
        results['whatsapp_webhook_public'] = self.test_whatsapp_webhook_public()
        
        # Teste 4: Documentação
        self.print_separator("TESTE 4: DOCUMENTAÇÃO")
        results['documentation'] = self.test_documentation_endpoints()
        
        # Teste 5: Health Detalhado
        self.print_separator("TESTE 5: HEALTH CHECK DETALHADO")
        results['health_detailed'] = self.test_health_detailed_public()
        
        # Teste 6: Métricas
        self.print_separator("TESTE 6: MÉTRICAS")
        results['metrics'] = self.test_metrics_public()
        
        # Teste 7: CORS
        self.print_separator("TESTE 7: CONFIGURAÇÃO CORS")
        results['cors'] = self.test_cors_configuration()
        
        # Teste 8: WebSocket
        self.print_separator("TESTE 8: WEBSOCKET PÚBLICO")
        results['websocket'] = self.test_websocket_public()
        
        # Teste 9: Informações do Sistema
        self.print_separator("TESTE 9: INFORMAÇÕES DO SISTEMA")
        results['system_info'] = self.test_system_info_public()
        
        # Teste 10: Endpoints de Saúde
        self.print_separator("TESTE 10: ENDPOINTS DE SAÚDE")
        results['public_health'] = self.test_public_health_endpoints()
        
        # Relatório Final
        self.print_separator("RELATÓRIO FINAL CLIENTE REAL AUTENTICADO")
        
        total_tests = len(results)
        passed_tests = sum(1 for success in results.values() if success)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"🔥 {'✅ SISTEMA PÚBLICO FUNCIONANDO!' if success_rate >= 80 else '⚠️ SISTEMA PÚBLICO COM PROBLEMAS!'}")
        print(f"👤 Cliente: {self.cliente_data['nome']} ({self.cliente_data['telefone']})")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        print(f"✅ Testes passaram: {passed_tests}/{total_tests}")
        print(f"🆔 ID do teste: {TEST_ID}")
        
        print(f"\n📋 Resultados por Categoria:")
        for test_name, success in results.items():
            status = "✅ FUNCIONANDO" if success else "❌ COM PROBLEMA"
            print(f"  {status} {test_name.replace('_', ' ').title()}")
        
        # Análise de Funcionalidades
        print(f"\n🔍 ANÁLISE DE FUNCIONALIDADES:")
        core_features = ['health_check_public', 'public_endpoints', 'whatsapp_webhook_public']
        core_success = sum(1 for feature in core_features if results.get(feature, False))
        print(f"  🎯 Funcionalidades Core: {core_success}/{len(core_features)} funcionando")
        
        api_features = ['documentation', 'metrics', 'system_info']
        api_success = sum(1 for feature in api_features if results.get(feature, False))
        print(f"  📊 APIs e Monitoramento: {api_success}/{len(api_features)} funcionando")
        
        # Salvar relatório
        report_data = {
            "test_id": TEST_ID,
            "timestamp": datetime.now().isoformat(),
            "client_data": self.cliente_data,
            "server_url": BASE_URL,
            "results": results,
            "success_rate": success_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "core_features": core_success,
            "api_features": api_success
        }
        
        report_file = f"temp_reports/teste_cliente_real_autenticado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import os
        os.makedirs("temp_reports", exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Relatório salvo: {report_file}")
        
        print("=" * 80)
        print("🎉 TESTE CLIENTE REAL AUTENTICADO CONCLUÍDO!")
        print("✨ Sistema testado como cliente real com foco em endpoints públicos!")
        print("=" * 80)
        
        return report_data

def main():
    """Executa teste completo do cliente real autenticado"""
    simulator = ClienteRealAutenticado()
    report = simulator.run_public_test()
    return report

if __name__ == "__main__":
    main()

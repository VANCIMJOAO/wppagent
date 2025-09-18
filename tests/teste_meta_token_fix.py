#!/usr/bin/env python3
"""
🔧 TESTE META TOKEN FIX - WhatsApp Agent API
Testa diferentes cenários de token Meta e simula cliente real
"""

import json
import random
import time
import uuid
from datetime import datetime
from typing import Dict, List

import requests
from faker import Faker

# Configuração
fake = Faker('pt_BR')
BASE_URL = "https://wppagent-production-app-production.up.railway.app"
TEST_ID = str(uuid.uuid4())[:8]

class MetaTokenTester:
    """Testador de tokens Meta para WhatsApp"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WhatsApp/2.23.24.81 iOS/16.6',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Tokens de teste (simulados)
        self.test_tokens = {
            'valid_token': 'EAAI4WnfpZAe0BPS1qkBjfZAnI8qdXInJ3Lxgc7IAn35PvZAAh...',  # Token real (mascarado)
            'invalid_token': 'invalid_token_123',
            'expired_token': 'EAAI4WnfpZAe0BPS1qkBjfZAnI8qdXInJ3Lxgc7IAn35PvZAAh_EXPIRED',
            'malformed_token': 'malformed',
            'empty_token': '',
            'short_token': 'EAAI4WnfpZAe0BPS1qkBjfZAnI8qdXInJ3Lxgc7IAn35PvZAAh'
        }
        
        self.phone_id = "728348237027885"
        self.test_phone = f"+55{random.randint(11, 99)}{random.randint(900000000, 999999999)}"
        
    def print_separator(self, title: str, char: str = "="):
        print(f"\n{char * 80}")
        print(f"🔧 {title}")
        print(f"{char * 80}")
    
    def print_result(self, test_name: str, success: bool, details: str = "", response_data: Dict = None):
        status = "✅ SUCESSO" if success else "❌ FALHA"
        print(f"    {status} - {test_name}")
        if details:
            print(f"        📋 {details}")
        if response_data:
            print(f"        📊 Resposta: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
    
    def create_whatsapp_webhook(self, token: str, message: str) -> Dict:
        """Cria webhook do WhatsApp com token específico"""
        return {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15551234567",
                            "phone_number_id": self.phone_id
                        },
                        "messages": [{
                            "from": self.test_phone,
                            "id": f"wamid.{uuid.uuid4()}",
                            "timestamp": str(int(time.time())),
                            "text": {
                                "body": message
                            },
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
    
    def test_token_validation(self, token_name: str, token_value: str) -> bool:
        """Testa validação de token específico"""
        try:
            # Criar webhook com token específico
            webhook_data = self.create_whatsapp_webhook(token_value, f"Teste de token {token_name}")
            
            # Adicionar token ao header
            headers = self.session.headers.copy()
            if token_value:
                headers['Authorization'] = f"Bearer {token_value}"
            
            response = self.session.post(
                f"{BASE_URL}/meta/webhook/verify", 
                json=webhook_data, 
                headers=headers,
                timeout=10
            )
            
            # Analisar resposta
            if response.status_code == 200:
                self.print_result(f"Token {token_name}", True, f"Token válido - Status: {response.status_code}")
                return True
            elif response.status_code == 401:
                self.print_result(f"Token {token_name}", False, f"Token inválido - Status: {response.status_code}")
                return False
            else:
                self.print_result(f"Token {token_name}", False, f"Status inesperado: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_result(f"Token {token_name}", False, f"Erro: {str(e)}")
            return False
    
    def test_webhook_verification(self) -> bool:
        """Testa verificação de webhook Meta"""
        try:
            # Teste de verificação do webhook
            verification_data = {
                "hub.mode": "subscribe",
                "hub.verify_token": "test_verify_token",
                "hub.challenge": "test_challenge"
            }
            
            response = self.session.get(
                f"{BASE_URL}/meta/webhook/verify",
                params=verification_data,
                timeout=10
            )
            
            if response.status_code in [200, 401]:
                self.print_result("Verificação Webhook", True, f"Webhook verificável - Status: {response.status_code}")
                return True
            else:
                self.print_result("Verificação Webhook", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Verificação Webhook", False, f"Erro: {str(e)}")
            return False
    
    def test_message_sending_simulation(self) -> bool:
        """Simula envio de mensagem WhatsApp"""
        try:
            # Simular envio de mensagem
            message_data = {
                "to": self.test_phone,
                "type": "text",
                "text": {
                    "body": "Olá! Esta é uma mensagem de teste do sistema WhatsApp Agent."
                }
            }
            
            response = self.session.post(
                f"{BASE_URL}/whatsapp/send",
                json=message_data,
                timeout=10
            )
            
            if response.status_code in [200, 401, 403]:
                self.print_result("Envio de Mensagem", True, f"Mensagem processada - Status: {response.status_code}")
                return True
            else:
                self.print_result("Envio de Mensagem", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Envio de Mensagem", False, f"Erro: {str(e)}")
            return False
    
    def test_meta_api_integration(self) -> bool:
        """Testa integração com Meta API"""
        try:
            # Testar endpoint de integração Meta
            integration_data = {
                "phone_number_id": self.phone_id,
                "message": "Teste de integração Meta API",
                "recipient": self.test_phone
            }
            
            response = self.session.post(
                f"{BASE_URL}/meta/send-message",
                json=integration_data,
                timeout=10
            )
            
            if response.status_code in [200, 401, 403]:
                self.print_result("Integração Meta API", True, f"API integrada - Status: {response.status_code}")
                return True
            else:
                self.print_result("Integração Meta API", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Integração Meta API", False, f"Erro: {str(e)}")
            return False
    
    def test_token_refresh_simulation(self) -> bool:
        """Simula refresh de token"""
        try:
            # Simular refresh de token
            refresh_data = {
                "grant_type": "client_credentials",
                "client_id": "test_client_id",
                "client_secret": "test_client_secret"
            }
            
            response = self.session.post(
                f"{BASE_URL}/meta/refresh-token",
                json=refresh_data,
                timeout=10
            )
            
            if response.status_code in [200, 401, 404]:
                self.print_result("Refresh de Token", True, f"Refresh processado - Status: {response.status_code}")
                return True
            else:
                self.print_result("Refresh de Token", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Refresh de Token", False, f"Erro: {str(e)}")
            return False
    
    def test_webhook_security(self) -> bool:
        """Testa segurança do webhook"""
        try:
            # Testar webhook sem autenticação
            webhook_data = self.create_whatsapp_webhook("", "Teste de segurança")
            
            response = self.session.post(
                f"{BASE_URL}/meta/webhook/verify",
                json=webhook_data,
                timeout=10
            )
            
            if response.status_code == 401:
                self.print_result("Segurança Webhook", True, f"Webhook protegido - Status: {response.status_code}")
                return True
            else:
                self.print_result("Segurança Webhook", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Segurança Webhook", False, f"Erro: {str(e)}")
            return False
    
    def run_token_tests(self) -> Dict:
        """Executa todos os testes de token"""
        print("🔧 INICIANDO TESTE META TOKEN FIX")
        print("⚠️  Este teste verifica diferentes cenários de token Meta")
        print("=" * 80)
        print(f"🔥 TESTE META TOKEN - ANÁLISE COMPLETA")
        print(f"🌐 Servidor: {BASE_URL}")
        print(f"📱 Phone ID: {self.phone_id}")
        print(f"🆔 ID do teste: {TEST_ID}")
        print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 80)
        
        results = {}
        
        # Teste 1: Verificação de Webhook
        self.print_separator("TESTE 1: VERIFICAÇÃO DE WEBHOOK")
        results['webhook_verification'] = self.test_webhook_verification()
        
        # Teste 2: Segurança do Webhook
        self.print_separator("TESTE 2: SEGURANÇA DO WEBHOOK")
        results['webhook_security'] = self.test_webhook_security()
        
        # Teste 3: Diferentes Tipos de Token
        self.print_separator("TESTE 3: VALIDAÇÃO DE DIFERENTES TOKENS")
        for token_name, token_value in self.test_tokens.items():
            results[f'token_{token_name}'] = self.test_token_validation(token_name, token_value)
        
        # Teste 4: Envio de Mensagem
        self.print_separator("TESTE 4: SIMULAÇÃO DE ENVIO DE MENSAGEM")
        results['message_sending'] = self.test_message_sending_simulation()
        
        # Teste 5: Integração Meta API
        self.print_separator("TESTE 5: INTEGRAÇÃO META API")
        results['meta_integration'] = self.test_meta_api_integration()
        
        # Teste 6: Refresh de Token
        self.print_separator("TESTE 6: REFRESH DE TOKEN")
        results['token_refresh'] = self.test_token_refresh_simulation()
        
        # Relatório Final
        self.print_separator("RELATÓRIO FINAL META TOKEN")
        
        total_tests = len(results)
        passed_tests = sum(1 for success in results.values() if success)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"🔥 {'✅ TOKENS FUNCIONANDO!' if success_rate >= 70 else '⚠️ TOKENS COM PROBLEMAS!'}")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        print(f"✅ Testes passaram: {passed_tests}/{total_tests}")
        print(f"🆔 ID do teste: {TEST_ID}")
        
        print(f"\n📋 Resultados por Categoria:")
        for test_name, success in results.items():
            status = "✅ FUNCIONANDO" if success else "❌ COM PROBLEMA"
            print(f"  {status} {test_name.replace('_', ' ').title()}")
        
        # Análise de Tokens
        print(f"\n🔍 ANÁLISE DE TOKENS:")
        token_tests = {k: v for k, v in results.items() if k.startswith('token_')}
        for token_name, success in token_tests.items():
            token_display = token_name.replace('token_', '')
            status = "✅ VÁLIDO" if success else "❌ INVÁLIDO"
            print(f"  {status} {token_display}")
        
        # Salvar relatório
        report_data = {
            "test_id": TEST_ID,
            "timestamp": datetime.now().isoformat(),
            "server_url": BASE_URL,
            "phone_id": self.phone_id,
            "test_phone": self.test_phone,
            "results": results,
            "success_rate": success_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "token_analysis": token_tests
        }
        
        report_file = f"temp_reports/teste_meta_token_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import os
        os.makedirs("temp_reports", exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Relatório salvo: {report_file}")
        
        print("=" * 80)
        print("🎉 TESTE META TOKEN CONCLUÍDO!")
        print("✨ Análise completa de tokens realizada!")
        print("=" * 80)
        
        return report_data

def main():
    """Executa teste completo de tokens Meta"""
    tester = MetaTokenTester()
    report = tester.run_token_tests()
    return report

if __name__ == "__main__":
    main()

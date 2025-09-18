#!/usr/bin/env python3
"""
🔍 SUPER DEBUG META WEBHOOK
===========================
Sistema avançado de debug para identificar exatamente onde está o erro
"""

import requests
import json
from datetime import datetime
import time

# Configurações
RAILWAY_URL = "https://wppagent-production-app-production.up.railway.app"
META_ACCESS_TOKEN = "EAAI4WnfpZAe0BPS1qkBjfZAnI8qdXInJ3Lxgc7IAn35PvZAAhdeRELACQTUspzTFViQ6OfzzjqbzS9ZCutlTTTzNmz8ezkeGtCkGtyxujzcN67ZBEKzriS79jlXxbqoZBw3f0MAMTOZCVKpeq2fTbUd6f4h2tvoCAXSLb9vPf1C0EQXyvKZA3986WNYeZA4vrfanZBLJyVLppTnjVupAGZAyOfRaey3ebfWz4CeLCEK5JbfjXQCNQGhT8dx0gQZAAZDZD"
META_PHONE_NUMBER_ID = "728348237027885"
NUMERO_LIBERADO = "5516991022255"  # Número que está na whitelist

class SuperDebugMeta:
    def __init__(self):
        self.session = requests.Session()
        self.debug_steps = []
        
    def log_debug(self, step: str, status: str, details: str = "", data: any = None):
        """Log detalhado de cada passo"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        entry = {
            "timestamp": timestamp,
            "step": step,
            "status": status,
            "details": details,
            "data": data
        }
        self.debug_steps.append(entry)
        
        status_icon = "✅" if status == "SUCCESS" else "❌" if status == "ERROR" else "🔍"
        print(f"{timestamp} {status_icon} {step}")
        if details:
            print(f"          📋 {details}")
        if data and status == "SUCCESS":
            print(f"          📊 {str(data)[:150]}...")
        print()

    def test_1_endpoint_availability(self):
        """Teste 1: Verificar se endpoints estão disponíveis"""
        print("🔍 TESTE 1: DISPONIBILIDADE DOS ENDPOINTS")
        print("=" * 80)
        
        endpoints_to_test = [
            "/health",
            "/webhook/verify", 
            "/webhook/test",
            "/meta/webhook/verify",
            "/meta/webhook/receive"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                if endpoint == "/health":
                    response = self.session.get(f"{RAILWAY_URL}{endpoint}", timeout=10)
                elif "verify" in endpoint:
                    params = {
                        "hub.mode": "subscribe",
                        "hub.verify_token": "whatsapp_webhook_verify_token", 
                        "hub.challenge": "12345"
                    }
                    response = self.session.get(f"{RAILWAY_URL}{endpoint}", params=params, timeout=10)
                else:
                    response = self.session.post(f"{RAILWAY_URL}{endpoint}", 
                                               json={"test": "ping"}, timeout=10)
                
                if response.status_code in [200, 404, 405, 401, 403]:
                    self.log_debug(f"Endpoint {endpoint}", "SUCCESS", 
                                 f"Status: {response.status_code}", response.text[:100])
                else:
                    self.log_debug(f"Endpoint {endpoint}", "ERROR", 
                                 f"Status: {response.status_code}", response.text[:100])
                    
            except Exception as e:
                self.log_debug(f"Endpoint {endpoint}", "ERROR", f"Exception: {str(e)}")

    def test_2_meta_api_direct(self):
        """Teste 2: Testar Meta API diretamente"""
        print("📱 TESTE 2: META API DIRETA")
        print("=" * 80)
        
        headers = {
            'Authorization': f'Bearer {META_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Teste 2.1: Verificar número
        try:
            url = f"https://graph.facebook.com/v18.0/{META_PHONE_NUMBER_ID}"
            response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_debug("Meta API - Info do número", "SUCCESS",
                             f"Número: {data.get('display_phone_number')}, Status: {data.get('status')}")
            else:
                self.log_debug("Meta API - Info do número", "ERROR", 
                             f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_debug("Meta API - Info do número", "ERROR", f"Exception: {str(e)}")
        
        # Teste 2.2: Enviar mensagem para número liberado
        try:
            url = f"https://graph.facebook.com/v18.0/{META_PHONE_NUMBER_ID}/messages"
            message_data = {
                "messaging_product": "whatsapp",
                "to": NUMERO_LIBERADO,
                "type": "text",
                "text": {
                    "body": f"🧪 Teste Super Debug - {datetime.now().strftime('%H:%M:%S')}"
                }
            }
            
            response = self.session.post(url, json=message_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                message_id = data.get("messages", [{}])[0].get("id")
                self.log_debug("Meta API - Envio mensagem", "SUCCESS",
                             f"Message ID: {message_id}")
            else:
                self.log_debug("Meta API - Envio mensagem", "ERROR",
                             f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_debug("Meta API - Envio mensagem", "ERROR", f"Exception: {str(e)}")

    def test_3_webhook_simulation(self):
        """Teste 3: Simular webhook do Meta"""
        print("🔗 TESTE 3: SIMULAÇÃO DE WEBHOOK META")
        print("=" * 80)
        
        # Webhook data realista
        webhook_data = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "debug_business_account",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15551536026",
                            "phone_number_id": META_PHONE_NUMBER_ID
                        },
                        "contacts": [{
                            "profile": {"name": "Debug User"},
                            "wa_id": NUMERO_LIBERADO
                        }],
                        "messages": [{
                            "id": f"wamid.debug_{int(time.time())}",
                            "from": NUMERO_LIBERADO,
                            "timestamp": str(int(time.time())),
                            "text": {
                                "body": "Olá! Testando webhook debug"
                            },
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        # Testar diferentes endpoints
        webhook_endpoints = [
            "/webhook",
            "/webhook/test", 
            "/meta/webhook/receive"
        ]
        
        for endpoint in webhook_endpoints:
            try:
                self.log_debug(f"Webhook {endpoint}", "INFO", "Enviando webhook...")
                
                response = self.session.post(f"{RAILWAY_URL}{endpoint}", 
                                           json=webhook_data, timeout=15)
                
                if response.status_code == 200:
                    self.log_debug(f"Webhook {endpoint}", "SUCCESS",
                                 f"Webhook processado com sucesso")
                elif response.status_code == 401:
                    self.log_debug(f"Webhook {endpoint}", "ERROR",
                                 f"Erro 401: {response.text}")
                elif response.status_code == 404:
                    self.log_debug(f"Webhook {endpoint}", "ERROR",
                                 "Endpoint não encontrado")
                elif response.status_code == 405:
                    self.log_debug(f"Webhook {endpoint}", "ERROR",
                                 "Método não permitido")
                else:
                    self.log_debug(f"Webhook {endpoint}", "ERROR",
                                 f"Status: {response.status_code}", response.text)
                    
            except Exception as e:
                self.log_debug(f"Webhook {endpoint}", "ERROR", f"Exception: {str(e)}")

    def test_4_auth_middleware_debug(self):
        """Teste 4: Debug do middleware de autenticação"""
        print("🔒 TESTE 4: DEBUG MIDDLEWARE AUTENTICAÇÃO")
        print("=" * 80)
        
        # Testar com diferentes headers
        test_cases = [
            {"name": "Sem headers", "headers": {}},
            {"name": "Com User-Agent", "headers": {"User-Agent": "Meta-WhatsApp/1.0"}},
            {"name": "Com X-Hub-Signature", "headers": {"X-Hub-Signature-256": "sha256=test"}},
            {"name": "Simulando Meta", "headers": {
                "User-Agent": "facebookexternalua",
                "X-Hub-Signature-256": "sha256=test",
                "Content-Type": "application/json"
            }}
        ]
        
        for test_case in test_cases:
            try:
                self.log_debug(f"Auth test - {test_case['name']}", "INFO", "Testando headers...")
                
                response = self.session.post(f"{RAILWAY_URL}/webhook/test",
                                           json={"test": "auth"},
                                           headers=test_case['headers'],
                                           timeout=10)
                
                if response.status_code == 200:
                    self.log_debug(f"Auth test - {test_case['name']}", "SUCCESS", "Passou no middleware")
                else:
                    self.log_debug(f"Auth test - {test_case['name']}", "ERROR",
                                 f"Status: {response.status_code}", response.text)
                    
            except Exception as e:
                self.log_debug(f"Auth test - {test_case['name']}", "ERROR", f"Exception: {str(e)}")

    def test_5_railway_logs_analysis(self):
        """Teste 5: Análise de logs e sistema"""
        print("📊 TESTE 5: ANÁLISE DO SISTEMA")
        print("=" * 80)
        
        # Testar endpoints de sistema
        system_endpoints = [
            "/metrics",
            "/webhook/stats",
            "/webhook/health"
        ]
        
        for endpoint in system_endpoints:
            try:
                response = self.session.get(f"{RAILWAY_URL}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    self.log_debug(f"Sistema {endpoint}", "SUCCESS", "Endpoint funcionando")
                elif response.status_code == 401:
                    self.log_debug(f"Sistema {endpoint}", "INFO", "Precisa autenticação")
                else:
                    self.log_debug(f"Sistema {endpoint}", "ERROR", 
                                 f"Status: {response.status_code}")
            except Exception as e:
                self.log_debug(f"Sistema {endpoint}", "ERROR", f"Exception: {str(e)}")

    def run_super_debug(self):
        """Executar super debug completo"""
        print("🔥 SUPER DEBUG META WEBHOOK INICIADO")
        print("=" * 80)
        print(f"🌐 Railway URL: {RAILWAY_URL}")
        print(f"📱 Meta Phone ID: {META_PHONE_NUMBER_ID}")
        print(f"📞 Número Liberado: {NUMERO_LIBERADO}")
        print(f"⏰ Início: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 80)
        print()
        
        self.test_1_endpoint_availability()
        self.test_2_meta_api_direct()
        self.test_3_webhook_simulation()
        self.test_4_auth_middleware_debug()
        self.test_5_railway_logs_analysis()
        
        print("📋 RESUMO DO SUPER DEBUG")
        print("=" * 80)
        
        success_count = len([s for s in self.debug_steps if s['status'] == 'SUCCESS'])
        error_count = len([s for s in self.debug_steps if s['status'] == 'ERROR'])
        total_count = len(self.debug_steps)
        
        print(f"✅ Sucessos: {success_count}")
        print(f"❌ Erros: {error_count}")
        print(f"📊 Total: {total_count}")
        print(f"🎯 Taxa de sucesso: {(success_count/total_count)*100:.1f}%")
        
        print("\n🔍 PRINCIPAIS ERROS ENCONTRADOS:")
        for step in self.debug_steps:
            if step['status'] == 'ERROR':
                print(f"   ❌ {step['step']}: {step['details']}")
        
        print("\n💾 Debug salvo: /home/vancim/whats_agent/temp_reports/super_debug_meta.json")
        
        # Salvar debug completo
        with open("/home/vancim/whats_agent/temp_reports/super_debug_meta.json", "w") as f:
            json.dump(self.debug_steps, f, indent=2, default=str)

if __name__ == "__main__":
    debug = SuperDebugMeta()
    debug.run_super_debug()
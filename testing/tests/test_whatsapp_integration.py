#!/usr/bin/env python3
"""
🧪 Teste das Melhorias de Integração WhatsApp
============================================

Testa:
- Validação de assinatura do webhook
- Retry logic robusto para Meta API
- Handling para rate limits da Meta
- Fallback para indisponibilidade da API
"""

import asyncio
import json
import hmac
import hashlib
from datetime import datetime
from app.services.whatsapp_security import whatsapp_security, MetaAPIStatus
from app.config import settings
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppIntegrationTester:
    """Tester para funcionalidades de integração WhatsApp"""
    
    def __init__(self):
        self.test_results = {}
    
    def test_webhook_signature_validation(self):
        """Testa validação de assinatura do webhook"""
        print("🧪 Testando validação de assinatura do webhook...")
        
        # Teste com webhook secret vazio
        whatsapp_security.webhook_secret = ""
        result1 = whatsapp_security.validate_webhook_signature(b"test", "signature")
        
        # Teste com webhook secret configurado
        whatsapp_security.webhook_secret = "test_secret"
        payload = b'{"test": "data"}'
        
        # Criar assinatura válida
        valid_signature = hmac.new(
            b"test_secret",
            payload,
            hashlib.sha256
        ).hexdigest()
        
        result2 = whatsapp_security.validate_webhook_signature(payload, f"sha256={valid_signature}")
        result3 = whatsapp_security.validate_webhook_signature(payload, "invalid_signature")
        
        self.test_results["webhook_signature"] = {
            "empty_secret": result1,  # Deve ser True (desabilitado)
            "valid_signature": result2,  # Deve ser True
            "invalid_signature": result3  # Deve ser False
        }
        
        print(f"   ✅ Secret vazio: {result1}")
        print(f"   ✅ Assinatura válida: {result2}")
        print(f"   ❌ Assinatura inválida: {result3}")
        print()
    
    async def test_rate_limiting_handling(self):
        """Testa handling de rate limiting"""
        print("🧪 Testando handling de rate limiting...")
        
        # Simular rate limit
        whatsapp_security.api_status = MetaAPIStatus.RATE_LIMITED
        whatsapp_security.rate_limit_reset_time = datetime.utcnow()
        
        # Verificar se está em rate limit
        is_rate_limited = whatsapp_security._is_rate_limited()
        
        # Simular headers de rate limit
        headers = {"Retry-After": "60"}
        whatsapp_security._handle_rate_limit(headers)
        
        self.test_results["rate_limiting"] = {
            "detects_rate_limit": is_rate_limited,
            "processes_retry_after": whatsapp_security.rate_limit_reset_time is not None
        }
        
        print(f"   ✅ Detecta rate limit: {is_rate_limited}")
        print(f"   ✅ Processa Retry-After: {whatsapp_security.rate_limit_reset_time is not None}")
        print()
    
    async def test_fallback_queue(self):
        """Testa sistema de fallback"""
        print("🧪 Testando sistema de fallback...")
        
        # Limpar fila
        whatsapp_security.fallback_queue = []
        
        # Simular API indisponível
        whatsapp_security.api_status = MetaAPIStatus.UNAVAILABLE
        
        # Tentar fazer requisição (deve ir para fallback)
        result = await whatsapp_security.make_api_request(
            method="POST",
            endpoint="/test",
            data={"test": "data"}
        )
        
        # Verificar se foi adicionado à fila
        queue_size = len(whatsapp_security.fallback_queue)
        
        self.test_results["fallback_queue"] = {
            "request_returns_none": result is None,
            "added_to_queue": queue_size > 0,
            "queue_size": queue_size
        }
        
        print(f"   ✅ Requisição retorna None: {result is None}")
        print(f"   ✅ Adicionado à fila: {queue_size > 0}")
        print(f"   📊 Tamanho da fila: {queue_size}")
        print()
    
    def test_retry_delay_calculation(self):
        """Testa cálculo de delay para retry"""
        print("🧪 Testando cálculo de delay para retry...")
        
        delays = []
        for attempt in range(5):
            delay = whatsapp_security._calculate_retry_delay(attempt)
            delays.append(delay)
        
        # Verificar se delays aumentam exponencialmente
        exponential_growth = all(delays[i] >= delays[i-1] for i in range(1, len(delays)))
        
        self.test_results["retry_delays"] = {
            "delays": delays,
            "exponential_growth": exponential_growth,
            "max_delay_respected": all(d <= whatsapp_security.max_delay for d in delays)
        }
        
        print(f"   ✅ Delays: {[f'{d:.2f}s' for d in delays]}")
        print(f"   ✅ Crescimento exponencial: {exponential_growth}")
        print(f"   ✅ Respeita delay máximo: {all(d <= whatsapp_security.max_delay for d in delays)}")
        print()
    
    def test_api_status_reporting(self):
        """Testa relatório de status da API"""
        print("🧪 Testando relatório de status da API...")
        
        # Configurar estado conhecido
        whatsapp_security.api_status = MetaAPIStatus.AVAILABLE
        whatsapp_security.requests_remaining = 500
        whatsapp_security.fallback_queue = [{"test": "item"}]
        
        status = whatsapp_security.get_api_status()
        
        expected_keys = ["status", "requests_remaining", "rate_limit_reset", "fallback_queue_size"]
        has_all_keys = all(key in status for key in expected_keys)
        
        self.test_results["api_status"] = {
            "has_all_keys": has_all_keys,
            "status": status,
            "correct_values": (
                status["status"] == "available" and
                status["requests_remaining"] == 500 and
                status["fallback_queue_size"] == 1
            )
        }
        
        print(f"   ✅ Tem todas as chaves: {has_all_keys}")
        print(f"   ✅ Valores corretos: {status}")
        print()
    
    def test_user_agent_validation(self):
        """Testa validação de User-Agent"""
        print("🧪 Testando validação de User-Agent...")
        
        test_cases = [
            ("WhatsApp/2.0", True),
            ("facebookexternalua/1.0", True),
            ("Mozilla/5.0 Meta", True),
            ("facebook-crawler", True),
            ("random-bot/1.0", False),
            ("", False)
        ]
        
        results = []
        for user_agent, expected in test_cases:
            result = whatsapp_security._is_valid_whatsapp_user_agent(user_agent)
            results.append((user_agent, result, result == expected))
            print(f"   {'✅' if result == expected else '❌'} '{user_agent}': {result}")
        
        self.test_results["user_agent_validation"] = {
            "all_correct": all(correct for _, _, correct in results),
            "results": results
        }
        print()
    
    def print_summary(self):
        """Imprime resumo dos testes"""
        print("📋 RESUMO DOS TESTES")
        print("=" * 50)
        
        total_tests = 0
        passed_tests = 0
        
        for test_name, results in self.test_results.items():
            print(f"\n🧪 {test_name.upper().replace('_', ' ')}:")
            
            if isinstance(results, dict):
                for key, value in results.items():
                    if isinstance(value, bool):
                        total_tests += 1
                        if value:
                            passed_tests += 1
                        print(f"   {'✅' if value else '❌'} {key}: {value}")
                    elif key not in ["delays", "status", "results"]:
                        print(f"   📊 {key}: {value}")
        
        print(f"\n🎯 RESULTADO FINAL: {passed_tests}/{total_tests} testes passaram")
        
        if passed_tests == total_tests:
            print("🎉 TODOS OS TESTES PASSARAM! Integração WhatsApp robusta implementada.")
        else:
            print("⚠️  Alguns testes falharam. Revisar implementação.")

async def main():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTES DE INTEGRAÇÃO WHATSAPP")
    print("=" * 60)
    print()
    
    tester = WhatsAppIntegrationTester()
    
    # Executar testes
    tester.test_webhook_signature_validation()
    await tester.test_rate_limiting_handling()
    await tester.test_fallback_queue()
    tester.test_retry_delay_calculation()
    tester.test_api_status_reporting()
    tester.test_user_agent_validation()
    
    # Resumo final
    tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
🚀 TESTE REAL COMPLETO - WhatsApp Agent em Produção
==================================================

Agora com as APIs configuradas no Railway!
Teste completo de todas as funcionalidades em ambiente real.
"""

import asyncio
import aiohttp
import json
import time
import random
from datetime import datetime
from typing import List, Dict

# Configurações para o teste real
RAILWAY_URL = "https://wppagent-production.up.railway.app"
TEST_PHONE = "5516991022255"

class RealProductionTester:
    """Testador completo para ambiente de produção"""
    
    def __init__(self):
        self.session = None
        self.test_results = []
        self.start_time = datetime.now()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_system_health(self):
        """Testa saúde completa do sistema"""
        print("🏥 VERIFICAÇÃO DE SAÚDE DO SISTEMA")
        print("-" * 50)
        
        try:
            # Health check detalhado
            async with self.session.get(f"{RAILWAY_URL}/health/detailed") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"📊 Status geral: {data['overall_status']}")
                    
                    checks = data.get('checks', {})
                    for service, status in checks.items():
                        icon = "✅" if status['status'] == 'healthy' else "❌"
                        print(f"   {icon} {service}: {status['status']} - {status['message']}")
                        
                    return data['overall_status'] == 'healthy'
                else:
                    print(f"❌ Health check falhou: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Erro no health check: {e}")
            return False

    async def test_webhook_message_real(self, message: str, delay: float = 3.0):
        """Envia mensagem real via webhook"""
        try:
            webhook_payload = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "production_test_entry",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551536026",
                                "phone_number_id": "728348237027885"
                            },
                            "contacts": [{
                                "profile": {"name": "Cliente Teste Real"},
                                "wa_id": TEST_PHONE
                            }],
                            "messages": [{
                                "from": TEST_PHONE,
                                "id": f"wamid.real_test_{int(time.time())}{random.randint(1000, 9999)}",
                                "timestamp": str(int(time.time())),
                                "type": "text",
                                "text": {"body": message}
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            print(f"📤 Enviando: '{message}'")
            
            async with self.session.post(
                f"{RAILWAY_URL}/webhook",
                json=webhook_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                status = response.status
                response_text = await response.text()
                
                print(f"   📨 Status: {status}")
                if status == 200:
                    print(f"   ✅ Processado com sucesso!")
                else:
                    print(f"   ⚠️ Resposta: {response_text[:100]}...")
                
                await asyncio.sleep(delay)
                
                return {
                    "message": message,
                    "status": status,
                    "response": response_text,
                    "success": status == 200
                }
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return {
                "message": message,
                "status": 500,
                "error": str(e),
                "success": False
            }

    async def test_scenario_real_greeting(self):
        """Cenário real: Saudação inicial"""
        print("\n🎬 CENÁRIO REAL 1: Primeira Interação")
        print("-" * 40)
        
        messages = [
            "Olá! Boa tarde!",
            "Gostaria de conhecer os serviços do Studio",
            "É a primeira vez que venho aqui"
        ]
        
        results = []
        for msg in messages:
            result = await self.test_webhook_message_real(msg)
            results.append(result)
            
        return results

    async def test_scenario_real_booking(self):
        """Cenário real: Agendamento completo"""
        print("\n🎬 CENÁRIO REAL 2: Agendamento Completo")
        print("-" * 40)
        
        messages = [
            "Quero agendar uma limpeza de pele",
            "Qual o preço e duração?",
            "Perfeito! Tenho disponibilidade amanhã de manhã",
            "Às 10h seria ideal",
            "Meu nome é Maria Silva",
            "Confirmo o agendamento!"
        ]
        
        results = []
        for msg in messages:
            result = await self.test_webhook_message_real(msg, delay=4.0)
            results.append(result)
            
        return results

    async def test_scenario_real_complex(self):
        """Cenário real: Consulta complexa"""
        print("\n🎬 CENÁRIO REAL 3: Consulta Complexa")
        print("-" * 40)
        
        messages = [
            "Estou planejando um dia especial para minha filha de 18 anos",
            "É aniversário dela e queria um tratamento completo",
            "Quais pacotes vocês têm disponíveis?",
            "Ela tem pele oleosa, o que vocês recomendam?",
            "E para as unhas também?",
            "Quanto ficaria tudo isso?"
        ]
        
        results = []
        for msg in messages:
            result = await self.test_webhook_message_real(msg, delay=4.0)
            results.append(result)
            
        return results

    async def test_direct_api_calls(self):
        """Testa chamadas diretas da API"""
        print("\n🔧 TESTE DE ENDPOINTS DIRETOS")
        print("-" * 40)
        
        endpoints = [
            ("/health", "GET", "Health básico"),
            ("/metrics/system", "GET", "Métricas do sistema"),
            ("/webhook/test-send", "POST", "Teste de envio direto")
        ]
        
        for endpoint, method, description in endpoints:
            try:
                print(f"🔍 {description}...")
                
                if method == "GET":
                    async with self.session.get(f"{RAILWAY_URL}{endpoint}") as response:
                        if response.status == 200:
                            print(f"   ✅ OK")
                        else:
                            print(f"   ⚠️ Status: {response.status}")
                            
                elif method == "POST" and endpoint == "/webhook/test-send":
                    async with self.session.post(
                        f"{RAILWAY_URL}{endpoint}",
                        params={
                            "phone_number": TEST_PHONE,
                            "message": "🚀 Teste real de produção - Sistema funcionando!"
                        }
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('success'):
                                print(f"   ✅ Mensagem enviada: {data.get('message')}")
                            else:
                                print(f"   ⚠️ Fallback: {data.get('message')}")
                        else:
                            print(f"   ❌ Erro: {response.status}")
                            
            except Exception as e:
                print(f"   ❌ Exceção: {e}")

    async def generate_production_report(self, all_results):
        """Gera relatório final de produção"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL - TESTE REAL DE PRODUÇÃO")
        print("=" * 60)
        print(f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"🌐 Ambiente: {RAILWAY_URL}")
        print(f"📱 Número teste: {TEST_PHONE}")
        
        # Estatísticas gerais
        total_messages = sum(len(scenario) for scenario in all_results)
        successful_messages = sum(
            1 for scenario in all_results 
            for result in scenario 
            if result.get('success', False)
        )
        
        success_rate = (successful_messages / total_messages * 100) if total_messages > 0 else 0
        
        print(f"\n📈 ESTATÍSTICAS:")
        print(f"   • Total de mensagens: {total_messages}")
        print(f"   • Mensagens processadas: {successful_messages}")
        print(f"   • Taxa de sucesso: {success_rate:.1f}%")
        print(f"   • Duração do teste: {(datetime.now() - self.start_time).total_seconds():.1f}s")
        
        # Status por cenário
        print(f"\n🎬 RESULTADOS POR CENÁRIO:")
        scenario_names = ["Primeira Interação", "Agendamento Completo", "Consulta Complexa"]
        
        for i, (name, results) in enumerate(zip(scenario_names, all_results)):
            scenario_success = sum(1 for r in results if r.get('success', False))
            scenario_total = len(results)
            scenario_rate = (scenario_success / scenario_total * 100) if scenario_total > 0 else 0
            
            icon = "✅" if scenario_rate >= 80 else "⚠️" if scenario_rate >= 50 else "❌"
            print(f"   {icon} {name}: {scenario_success}/{scenario_total} ({scenario_rate:.1f}%)")
        
        # Conclusão
        print(f"\n🏆 CONCLUSÃO:")
        if success_rate >= 90:
            print("   🎉 EXCELENTE! Sistema funcionando perfeitamente!")
        elif success_rate >= 70:
            print("   ✅ BOM! Sistema operacional com pequenos ajustes necessários")
        elif success_rate >= 50:
            print("   ⚠️ REGULAR! Sistema precisa de ajustes")
        else:
            print("   ❌ CRÍTICO! Sistema precisa de correções urgentes")
            
        print(f"\n💡 RECOMENDAÇÕES:")
        if success_rate >= 90:
            print("   • Sistema pronto para uso em produção")
            print("   • Monitorar logs para otimizações")
        else:
            print("   • Verificar logs de erro para debugging")
            print("   • Revisar configurações das APIs")
            
        return {
            "total_messages": total_messages,
            "successful_messages": successful_messages,
            "success_rate": success_rate,
            "test_duration": (datetime.now() - self.start_time).total_seconds()
        }

    async def run_complete_production_test(self):
        """Executa teste completo de produção"""
        print("🚀 INICIANDO TESTE REAL DE PRODUÇÃO")
        print("🎯 WhatsApp Agent com APIs configuradas no Railway")
        print("=" * 60)
        
        # 1. Verificar saúde do sistema
        system_healthy = await self.test_system_health()
        
        if not system_healthy:
            print("\n❌ Sistema não está saudável. Abortando teste.")
            return False
        
        # 2. Testes diretos da API
        await self.test_direct_api_calls()
        
        # 3. Cenários reais de webhook
        results_greeting = await self.test_scenario_real_greeting()
        results_booking = await self.test_scenario_real_booking()
        results_complex = await self.test_scenario_real_complex()
        
        all_results = [results_greeting, results_booking, results_complex]
        
        # 4. Relatório final
        final_stats = await self.generate_production_report(all_results)
        
        return final_stats['success_rate'] >= 70

async def main():
    """Função principal do teste real"""
    print("🎬 TESTE REAL - WHATSAPP AGENT EM PRODUÇÃO")
    print("🔥 APIs configuradas no Railway - Ambiente real!")
    print()
    
    async with RealProductionTester() as tester:
        success = await tester.run_complete_production_test()
        
        if success:
            print("\n🏅 TESTE REAL CONCLUÍDO COM SUCESSO!")
            print("🎊 Sistema aprovado para produção!")
        else:
            print("\n⚠️ Teste apresentou problemas")
            print("🔧 Revisar configurações e logs")

if __name__ == "__main__":
    asyncio.run(main())

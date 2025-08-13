#!/usr/bin/env python3
"""
🧪 SCRIPT DE TESTE COMPLETO - WhatsApp Agent
===========================================

Testa todas as funcionalidades do sistema:
- Agendamentos
- Cancelamentos
- Reagendamentos
- Reclamações
- Consultas de serviços
- Interações complexas

Configurações:
- Número de teste: 5516991022255
- URL do sistema: wppagent-production.up.railway.app
- Geração de relatório detalhado com logs da LLM
"""

import asyncio
import aiohttp
import json
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
import os

# Configurações do teste
RAILWAY_URL = "https://wppagent-production.up.railway.app"
TEST_PHONE = "5516991022255"
WEBHOOK_URL = f"{RAILWAY_URL}/webhook"

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('whatsapp_test_report.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WhatsAppTester:
    """Classe para testar o sistema WhatsApp Agent"""
    
    def __init__(self):
        self.session = None
        self.test_results = []
        self.messages_sent = []
        self.responses_received = []
        self.start_time = datetime.now()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_webhook_message(self, message: str, message_type: str = "text", delay: float = 2.0) -> Dict:
        """Simula uma mensagem chegando via webhook do WhatsApp"""
        try:
            # Simular payload do WhatsApp
            webhook_payload = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "24386792860950513",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550987654",
                                "phone_number_id": "728348237027885"
                            },
                            "contacts": [{
                                "profile": {
                                    "name": "Testador Sistema"
                                },
                                "wa_id": TEST_PHONE
                            }],
                            "messages": [{
                                "from": TEST_PHONE,
                                "id": f"wamid.test_{int(time.time())}{random.randint(1000, 9999)}",
                                "timestamp": str(int(time.time())),
                                "type": message_type,
                                "text": {
                                    "body": message
                                } if message_type == "text" else None
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            logger.info(f"📤 Enviando mensagem: {message}")
            
            async with self.session.post(
                WEBHOOK_URL,
                json=webhook_payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "WhatsApp/2.0"
                }
            ) as response:
                response_data = await response.text()
                
                self.messages_sent.append({
                    "timestamp": datetime.now().isoformat(),
                    "message": message,
                    "type": message_type,
                    "status_code": response.status,
                    "response": response_data
                })
                
                logger.info(f"📨 Resposta HTTP: {response.status}")
                
                # Aguardar processamento
                await asyncio.sleep(delay)
                
                return {
                    "status_code": response.status,
                    "response": response_data,
                    "message_sent": message
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem '{message}': {e}")
            return {
                "status_code": 500,
                "error": str(e),
                "message_sent": message
            }
    
    async def get_system_status(self) -> Dict:
        """Verifica status do sistema"""
        try:
            async with self.session.get(f"{RAILWAY_URL}/health/detailed") as response:
                return {
                    "status_code": response.status,
                    "data": await response.json()
                }
        except Exception as e:
            logger.error(f"❌ Erro ao verificar status: {e}")
            return {"status_code": 500, "error": str(e)}
    
    async def get_metrics(self) -> Dict:
        """Obtém métricas do sistema"""
        try:
            async with self.session.get(f"{RAILWAY_URL}/metrics/system") as response:
                return {
                    "status_code": response.status,
                    "data": await response.json()
                }
        except Exception as e:
            logger.error(f"❌ Erro ao obter métricas: {e}")
            return {"status_code": 500, "error": str(e)}
    
    async def get_conversation_analytics(self) -> Dict:
        """Obtém analytics das conversas"""
        try:
            async with self.session.get(f"{RAILWAY_URL}/conversation/analytics") as response:
                return {
                    "status_code": response.status,
                    "data": await response.json()
                }
        except Exception as e:
            logger.error(f"❌ Erro ao obter analytics: {e}")
            return {"status_code": 500, "error": str(e)}
    
    async def get_llm_analytics(self) -> Dict:
        """Obtém analytics do sistema LLM"""
        try:
            async with self.session.get(f"{RAILWAY_URL}/llm/analytics") as response:
                return {
                    "status_code": response.status,
                    "data": await response.json()
                }
        except Exception as e:
            logger.error(f"❌ Erro ao obter LLM analytics: {e}")
            return {"status_code": 500, "error": str(e)}

    async def test_scenario_basic_greeting(self):
        """Cenário 1: Saudação básica e apresentação"""
        logger.info("\n🎬 CENÁRIO 1: Saudação e Apresentação")
        
        messages = [
            "Olá!",
            "Bom dia! Como você está?",
            "Gostaria de conhecer seus serviços"
        ]
        
        for msg in messages:
            result = await self.send_webhook_message(msg)
            self.test_results.append({
                "scenario": "basic_greeting",
                "message": msg,
                "result": result
            })
    
    async def test_scenario_service_inquiry(self):
        """Cenário 2: Consulta de serviços e preços"""
        logger.info("\n🎬 CENÁRIO 2: Consulta de Serviços")
        
        messages = [
            "Quais serviços vocês oferecem?",
            "Quanto custa uma limpeza de pele?",
            "Vocês fazem massagem relaxante?",
            "Qual a duração do hidrofacial?",
            "Têm desconto para pacotes?"
        ]
        
        for msg in messages:
            result = await self.send_webhook_message(msg)
            self.test_results.append({
                "scenario": "service_inquiry",
                "message": msg,
                "result": result
            })
    
    async def test_scenario_appointment_booking(self):
        """Cenário 3: Agendamento completo"""
        logger.info("\n🎬 CENÁRIO 3: Agendamento Completo")
        
        messages = [
            "Quero agendar um horário",
            "Limpeza de pele profunda",
            "Amanhã de manhã seria possível?",
            "Às 10h está bom",
            "Meu nome é João Silva",
            "Sim, confirmo o agendamento"
        ]
        
        for msg in messages:
            result = await self.send_webhook_message(msg, delay=3.0)
            self.test_results.append({
                "scenario": "appointment_booking",
                "message": msg,
                "result": result
            })
    
    async def test_scenario_appointment_changes(self):
        """Cenário 4: Cancelamento e reagendamento"""
        logger.info("\n🎬 CENÁRIO 4: Cancelamentos e Reagendamentos")
        
        messages = [
            "Preciso cancelar meu agendamento de amanhã",
            "Surgiu um imprevisto no trabalho",
            "Posso reagendar para outro dia?",
            "Que tal na sexta-feira?",
            "De tarde, por volta das 14h",
            "Perfeito, confirmo o reagendamento"
        ]
        
        for msg in messages:
            result = await self.send_webhook_message(msg, delay=2.5)
            self.test_results.append({
                "scenario": "appointment_changes",
                "message": msg,
                "result": result
            })
    
    async def test_scenario_complex_inquiry(self):
        """Cenário 5: Consulta complexa com múltiplos serviços"""
        logger.info("\n🎬 CENÁRIO 5: Consulta Complexa")
        
        messages = [
            "Estou planejando um dia de spa para minha mãe",
            "Ela tem 65 anos e pele sensível",
            "Quais tratamentos vocês recomendam?",
            "Quanto ficaria um pacote completo?",
            "Vocês têm estacionamento?",
            "E desconto para idosos?"
        ]
        
        for msg in messages:
            result = await self.send_webhook_message(msg, delay=3.0)
            self.test_results.append({
                "scenario": "complex_inquiry",
                "message": msg,
                "result": result
            })
    
    async def test_scenario_complaint_handling(self):
        """Cenário 6: Tratamento de reclamações"""
        logger.info("\n🎬 CENÁRIO 6: Tratamento de Reclamações")
        
        messages = [
            "Estou insatisfeito com o atendimento da semana passada",
            "A profissional chegou 30 minutos atrasada",
            "E o tratamento não ficou como esperado",
            "Gostaria de uma solução para isso",
            "Sim, aceito um desconto no próximo atendimento"
        ]
        
        for msg in messages:
            result = await self.send_webhook_message(msg, delay=3.0)
            self.test_results.append({
                "scenario": "complaint_handling",
                "message": msg,
                "result": result
            })
    
    async def test_scenario_business_hours(self):
        """Cenário 7: Consulta sobre funcionamento"""
        logger.info("\n🎬 CENÁRIO 7: Horários e Funcionamento")
        
        messages = [
            "Vocês funcionam aos sábados?",
            "E domingo?",
            "Qual o horário de almoço?",
            "Onde vocês ficam localizados?",
            "Como chegar de transporte público?"
        ]
        
        for msg in messages:
            result = await self.send_webhook_message(msg)
            self.test_results.append({
                "scenario": "business_hours",
                "message": msg,
                "result": result
            })
    
    async def test_scenario_multi_topic_conversation(self):
        """Cenário 8: Conversa com múltiplos tópicos (teste do fluxo não-linear)"""
        logger.info("\n🎬 CENÁRIO 8: Conversa Multi-Tópicos")
        
        messages = [
            "Oi! Queria saber sobre massagem",
            "Mas antes, vocês fazem sobrancelha?",
            "Voltando à massagem, qual o preço?",
            "E depilação, vocês fazem também?",
            "Ok, mas sobre a massagem, posso agendar para hoje?",
            "Na verdade, prefiro agendar a sobrancelha mesmo",
            "Para amanhã de manhã"
        ]
        
        for msg in messages:
            result = await self.send_webhook_message(msg, delay=2.0)
            self.test_results.append({
                "scenario": "multi_topic_conversation",
                "message": msg,
                "result": result
            })
    
    async def test_scenario_edge_cases(self):
        """Cenário 9: Casos extremos e edge cases"""
        logger.info("\n🎬 CENÁRIO 9: Casos Extremos")
        
        messages = [
            "asdfghjkl",  # Texto aleatório
            "😀😃😄😁😆😅😂🤣",  # Apenas emojis
            "QUERO AGENDAR AGORA!!!!!",  # Texto em maiúsculas
            "vocês fazem botox? e preenchimento? e harmonização facial?",  # Serviços não oferecidos
            "123456789",  # Apenas números
            "Obrigado pela atenção, até logo!"  # Despedida
        ]
        
        for msg in messages:
            result = await self.send_webhook_message(msg)
            self.test_results.append({
                "scenario": "edge_cases",
                "message": msg,
                "result": result
            })
    
    async def run_all_tests(self):
        """Executa todos os cenários de teste"""
        logger.info("🚀 INICIANDO BATERIA COMPLETA DE TESTES")
        logger.info("=" * 60)
        
        # Verificar status inicial do sistema
        status = await self.get_system_status()
        logger.info(f"Status inicial do sistema: {status['status_code']}")
        
        # Executar cenários
        test_scenarios = [
            self.test_scenario_basic_greeting,
            self.test_scenario_service_inquiry,
            self.test_scenario_appointment_booking,
            self.test_scenario_appointment_changes,
            self.test_scenario_complex_inquiry,
            self.test_scenario_complaint_handling,
            self.test_scenario_business_hours,
            self.test_scenario_multi_topic_conversation,
            self.test_scenario_edge_cases
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            try:
                await scenario()
                logger.info(f"✅ Cenário {i} concluído")
                await asyncio.sleep(2)  # Pausa entre cenários
            except Exception as e:
                logger.error(f"❌ Erro no cenário {i}: {e}")
        
        # Obter métricas finais
        await self.collect_final_metrics()
    
    async def collect_final_metrics(self):
        """Coleta métricas finais do sistema"""
        logger.info("\n📊 COLETANDO MÉTRICAS FINAIS")
        
        # Métricas do sistema
        system_metrics = await self.get_metrics()
        conversation_analytics = await self.get_conversation_analytics()
        llm_analytics = await self.get_llm_analytics()
        
        self.final_metrics = {
            "system_metrics": system_metrics,
            "conversation_analytics": conversation_analytics,
            "llm_analytics": llm_analytics,
            "test_duration": (datetime.now() - self.start_time).total_seconds(),
            "total_messages": len(self.messages_sent),
            "success_rate": len([r for r in self.test_results if r['result']['status_code'] == 200]) / len(self.test_results) * 100
        }
    
    def generate_detailed_report(self):
        """Gera relatório detalhado dos testes"""
        report_filename = f"whatsapp_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            "test_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
                "test_phone": TEST_PHONE,
                "railway_url": RAILWAY_URL
            },
            "summary": {
                "total_scenarios": len(set(r['scenario'] for r in self.test_results)),
                "total_messages": len(self.messages_sent),
                "success_count": len([r for r in self.test_results if r['result']['status_code'] == 200]),
                "error_count": len([r for r in self.test_results if r['result']['status_code'] != 200]),
                "success_rate_percent": len([r for r in self.test_results if r['result']['status_code'] == 200]) / len(self.test_results) * 100 if self.test_results else 0
            },
            "test_results": self.test_results,
            "messages_sent": self.messages_sent,
            "final_metrics": getattr(self, 'final_metrics', {}),
            "scenarios_breakdown": self._get_scenarios_breakdown()
        }
        
        # Salvar relatório JSON
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # Gerar relatório em texto legível
        self._generate_readable_report(report_data)
        
        logger.info(f"📋 Relatório salvo em: {report_filename}")
        return report_filename
    
    def _get_scenarios_breakdown(self):
        """Gera breakdown por cenário"""
        scenarios = {}
        for result in self.test_results:
            scenario = result['scenario']
            if scenario not in scenarios:
                scenarios[scenario] = {
                    "total_messages": 0,
                    "successful_messages": 0,
                    "failed_messages": 0,
                    "messages": []
                }
            
            scenarios[scenario]["total_messages"] += 1
            scenarios[scenario]["messages"].append(result)
            
            if result['result']['status_code'] == 200:
                scenarios[scenario]["successful_messages"] += 1
            else:
                scenarios[scenario]["failed_messages"] += 1
        
        return scenarios
    
    def _generate_readable_report(self, report_data):
        """Gera relatório em formato texto legível"""
        readable_filename = f"whatsapp_test_readable_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(readable_filename, 'w', encoding='utf-8') as f:
            f.write("🧪 RELATÓRIO DE TESTE - WHATSAPP AGENT\n")
            f.write("=" * 50 + "\n\n")
            
            # Informações gerais
            f.write("📊 RESUMO EXECUTIVO\n")
            f.write("-" * 20 + "\n")
            f.write(f"Duração do teste: {report_data['test_info']['duration_seconds']:.2f} segundos\n")
            f.write(f"Total de mensagens: {report_data['summary']['total_messages']}\n")
            f.write(f"Taxa de sucesso: {report_data['summary']['success_rate_percent']:.1f}%\n")
            f.write(f"Mensagens com sucesso: {report_data['summary']['success_count']}\n")
            f.write(f"Mensagens com erro: {report_data['summary']['error_count']}\n\n")
            
            # Breakdown por cenário
            f.write("🎬 RESULTADOS POR CENÁRIO\n")
            f.write("-" * 25 + "\n")
            
            scenarios = report_data['scenarios_breakdown']
            for scenario_name, scenario_data in scenarios.items():
                f.write(f"\n{scenario_name.upper()}:\n")
                f.write(f"  Total: {scenario_data['total_messages']}\n")
                f.write(f"  Sucessos: {scenario_data['successful_messages']}\n")
                f.write(f"  Falhas: {scenario_data['failed_messages']}\n")
                f.write(f"  Taxa de sucesso: {(scenario_data['successful_messages']/scenario_data['total_messages']*100):.1f}%\n")
            
            # Detalhes das mensagens
            f.write("\n\n📱 DETALHES DAS MENSAGENS\n")
            f.write("-" * 25 + "\n")
            
            for i, message_data in enumerate(report_data['messages_sent'], 1):
                f.write(f"\n{i}. [{message_data['timestamp']}]\n")
                f.write(f"   Mensagem: {message_data['message']}\n")
                f.write(f"   Status: {message_data['status_code']}\n")
                f.write(f"   Tipo: {message_data['type']}\n")
            
            # Métricas finais se disponíveis
            if 'final_metrics' in report_data and report_data['final_metrics']:
                f.write("\n\n📈 MÉTRICAS DO SISTEMA\n")
                f.write("-" * 20 + "\n")
                f.write(json.dumps(report_data['final_metrics'], indent=2, ensure_ascii=False))
        
        logger.info(f"📄 Relatório legível salvo em: {readable_filename}")

async def main():
    """Função principal para executar os testes"""
    logger.info("🔬 Iniciando teste completo do WhatsApp Agent")
    
    async with WhatsAppTester() as tester:
        try:
            await tester.run_all_tests()
            report_file = tester.generate_detailed_report()
            
            logger.info("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
            logger.info(f"📋 Relatório detalhado: {report_file}")
            logger.info(f"📱 Total de mensagens enviadas: {len(tester.messages_sent)}")
            logger.info(f"⏱️ Duração total: {(datetime.now() - tester.start_time).total_seconds():.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Erro durante execução dos testes: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(main())

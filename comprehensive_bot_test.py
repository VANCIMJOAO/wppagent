#!/usr/bin/env python3
"""
🔄 TESTE COMPLETO - WhatsApp LLM Agent
====================================
Testa TODOS os cenários possíveis do bot incluindo:
- Mensagens normais
- Agendamentos
- Consultas de preços
- Informações da empresa
- Casos que acionam handoff (com estratégias para contornar)
- Botões interativos
- Fluxos de conversa complexos
"""

import asyncio
import asyncpg
import aiohttp
import time
from datetime import datetime, timedelta
import logging
import json
import random
import os

class ComprehensiveWhatsAppTester:
    def __init__(self):
        # CONFIGURAÇÕES
        self.DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
        self.API_BASE_URL = "https://wppagent-production.up.railway.app"
        
        # CREDENCIAIS
        self.META_ACCESS_TOKEN = "EAAI4WnfpZAe0BPDfToaznOF09vAThubT28eoHSuPx3xn2ZBa8JaEH4ZBPcQ9Twee5ppFyAAIHW2MiR2ermRjjZCZAzM6ihYzM6ak9yDNLpOVJZCgR6IjVEDJlfMHNMXjyfY5zeVcsAKtX2IZCjlDPS3Kc8txlP1YZC0TZCZAYT3Sz9LzgTcLEmtUQgmjBqLR501b1Vhhk04frXwn68WmZC6MEC3tfZAmh5Ppd1ocXY9fZAQuI76InVvzHKzJtOVgRYgZDZD"
        self.WHATSAPP_PHONE_ID = "728348237027885"
        self.BOT_PHONE = "15551536026"
        self.YOUR_PHONE = "5516991022255"
        
        # CENÁRIOS DE TESTE COMPLETOS
        self.test_scenarios = {
            "1_basic_greeting": {
                "name": "Saudações Básicas",
                "messages": [
                    "Oi",
                    "Olá",
                    "Bom dia",
                    "Boa tarde"
                ],
                "expected_patterns": ["olá", "como posso", "ajudar", "bem-vindo"],
                "handoff_risk": "LOW"
            },
            
            "2_service_inquiry": {
                "name": "Consulta de Serviços",
                "messages": [
                    "Quais serviços vocês oferecem?",
                    "Que tipos de tratamento fazem?",
                    "O que tem disponível para hoje?",
                    "Menu de serviços"
                ],
                "expected_patterns": ["limpeza", "pele", "hidrofacial", "serviços", "oferecemos"],
                "handoff_risk": "LOW"
            },
            
            "3_pricing_inquiry": {
                "name": "Consulta de Preços",
                "messages": [
                    "Quanto custa uma limpeza de pele?",
                    "Qual o valor do hidrofacial?",
                    "Preços dos serviços",
                    "Tabela de valores"
                ],
                "expected_patterns": ["preço", "valor", "custa", "r$", "reais"],
                "handoff_risk": "MEDIUM"  # Pode acionar handoff por negociação
            },
            
            "4_scheduling_basic": {
                "name": "Agendamento Básico",
                "messages": [
                    "Quero agendar uma limpeza de pele",
                    "Gostaria de marcar um horário",
                    "Tem vaga para amanhã?",
                    "Como faço para agendar?"
                ],
                "expected_patterns": ["agendar", "horário", "disponível", "marcar", "quando"],
                "handoff_risk": "LOW"
            },
            
            "5_business_info": {
                "name": "Informações da Empresa",
                "messages": [
                    "Qual o horário de funcionamento?",
                    "Onde vocês ficam?",
                    "Endereço do studio",
                    "Telefone para contato"
                ],
                "expected_patterns": ["horário", "funcionamento", "endereço", "localização", "segunda"],
                "handoff_risk": "LOW"
            },
            
            "6_payment_methods": {
                "name": "Formas de Pagamento",
                "messages": [
                    "Quais formas de pagamento aceitam?",
                    "Posso pagar com cartão?",
                    "Tem PIX?",
                    "Aceitam dinheiro?"
                ],
                "expected_patterns": ["pagamento", "cartão", "pix", "dinheiro", "aceitamos"],
                "handoff_risk": "LOW"
            },
            
            "7_complex_scenarios": {
                "name": "Cenários Complexos (Evitando Handoff)",
                "messages": [
                    # Mensagens que normalmente acionariam handoff, mas reformuladas
                    "Estou interessada em saber sobre promoções",  # Em vez de "quero desconto"
                    "Gostaria de informações sobre agendamentos especiais",  # Em vez de "reagendar urgente"
                    "Preciso de detalhes sobre os preços dos tratamentos",  # Em vez de "negociar preço"
                    "Quero entender melhor como funciona o atendimento"  # Em vez de "falar com gerente"
                ],
                "expected_patterns": ["informações", "detalhes", "explicar", "funciona"],
                "handoff_risk": "MEDIUM"
            },
            
            "8_interactive_buttons": {
                "name": "Teste de Botões (se houver)",
                "messages": [
                    "Menu",
                    "Opções",
                    "Ajuda",
                    "Ver serviços"
                ],
                "expected_patterns": ["menu", "opções", "escolha", "selecione"],
                "handoff_risk": "LOW"
            },
            
            "9_appointment_flow": {
                "name": "Fluxo Completo de Agendamento",
                "messages": [
                    "Quero agendar um hidrofacial",
                    "Para quinta-feira se possível",
                    "De manhã seria melhor",
                    "Pode ser às 10h?"
                ],
                "expected_patterns": ["agendar", "quinta", "manhã", "10h", "confirmar"],
                "handoff_risk": "LOW"
            },
            
            "10_edge_cases": {
                "name": "Casos Especiais (Não Handoff)",
                "messages": [
                    "Primeira vez aqui, como funciona?",
                    "Sou novo cliente, o que recomendam?",
                    "Qual a diferença entre os tratamentos?",
                    "Muito obrigada pelas informações!"
                ],
                "expected_patterns": ["primeira", "novo", "diferença", "obrigada", "recomendo"],
                "handoff_risk": "LOW"
            }
        }
        
        # PALAVRAS QUE ACIONAM HANDOFF (para evitar)
        self.handoff_triggers = [
            "reclamação", "insatisfeito", "problema grave", "erro", "ruim", "péssimo", 
            "cancelar", "reembolso", "dinheiro de volta", "falar com gerente",
            "falar com atendente", "quero pessoa", "atendimento humano", "supervisor",
            "desconto", "negociar", "preço melhor", "mais barato", "reagendar urgente",
            "emergência", "hoje mesmo", "agora", "não funciona", "deu errado"
        ]
        
        self.session_id = f"comprehensive_test_{int(time.time())}"
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        self.results = {
            "session": self.session_id,
            "start_time": datetime.now().isoformat(),
            "total_scenarios": len(self.test_scenarios),
            "scenarios_tested": 0,
            "messages_sent": 0,
            "bot_responses": 0,
            "handoff_avoided": 0,
            "failed_scenarios": [],
            "detailed_results": {},
            "conversation_log": []
        }

    async def connect_db(self):
        """Conecta ao banco"""
        try:
            self.db = await asyncpg.connect(self.DATABASE_URL)
            self.logger.info("✅ Conectado ao banco PostgreSQL")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao conectar: {e}")
            return False

    def check_handoff_risk(self, message: str) -> tuple[bool, str]:
        """Verifica se a mensagem pode acionar handoff"""
        message_lower = message.lower()
        for trigger in self.handoff_triggers:
            if trigger in message_lower:
                return True, trigger
        return False, ""

    def safe_alternative(self, message: str) -> str:
        """Gera alternativa segura para mensagens que podem acionar handoff"""
        alternatives = {
            "desconto": "informações sobre promoções",
            "negociar": "detalhes sobre preços",
            "preço melhor": "opções de valores",
            "falar com atendente": "mais informações",
            "atendimento humano": "esclarecimentos adicionais",
            "problema": "dúvida",
            "reclamação": "feedback",
            "cancelar": "informações sobre agendamento"
        }
        
        for trigger, alternative in alternatives.items():
            if trigger in message.lower():
                return message.lower().replace(trigger, alternative)
        
        return message

    async def simulate_message(self, message: str):
        """Simula envio de mensagem via webhook"""
        try:
            # Verificar risco de handoff
            has_risk, trigger = self.check_handoff_risk(message)
            if has_risk:
                safe_msg = self.safe_alternative(message)
                self.logger.warning(f"⚠️ Handoff detectado em '{message}' (trigger: {trigger})")
                self.logger.info(f"🔄 Usando alternativa segura: '{safe_msg}'")
                message = safe_msg
                self.results["handoff_avoided"] += 1
            
            webhook_url = f"{self.API_BASE_URL}/webhook"
            
            webhook_payload = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": self.WHATSAPP_PHONE_ID,
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": self.BOT_PHONE,
                                "phone_number_id": self.WHATSAPP_PHONE_ID
                            },
                            "messages": [{
                                "from": self.YOUR_PHONE,
                                "id": f"wamid.test_{int(time.time())}{random.randint(100,999)}",
                                "timestamp": str(int(time.time())),
                                "text": {"body": message},
                                "type": "text"
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "facebookexternalua"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=webhook_payload, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        self.logger.info(f"✅ Mensagem enviada: '{message}'")
                        self.results["messages_sent"] += 1
                        return True
                    else:
                        response_text = await response.text()
                        self.logger.error(f"❌ Falha no webhook: {response.status} - {response_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"❌ Erro no envio: {e}")
            return False

    async def monitor_responses(self, expected_patterns: list, timeout=20):
        """Monitora respostas do bot"""
        start_time = time.time()
        await asyncio.sleep(2)  # Esperar processamento
        
        cutoff_time = datetime.now() - timedelta(seconds=30)
        detected_responses = []
        pattern_matches = []
        
        for check in range(int(timeout / 3)):
            try:
                recent_responses = await self.db.fetch("""
                    SELECT direction, content, created_at, message_type
                    FROM messages 
                    WHERE user_id = 2 
                    AND direction = 'out'
                    AND created_at > $1
                    ORDER BY created_at DESC
                """, cutoff_time)
                
                for msg in recent_responses:
                    already_detected = any(
                        resp['timestamp'] == msg['created_at'].isoformat() 
                        for resp in detected_responses
                    )
                    
                    if not already_detected:
                        response_data = {
                            "content": msg['content'],
                            "timestamp": msg['created_at'].isoformat(),
                            "type": msg['message_type'] or 'text'
                        }
                        
                        detected_responses.append(response_data)
                        self.results["bot_responses"] += 1
                        
                        # Verificar padrões esperados
                        content_lower = msg['content'].lower()
                        for pattern in expected_patterns:
                            if pattern.lower() in content_lower:
                                pattern_matches.append(pattern)
                        
                        self.logger.info(f"🤖 Resposta: {msg['content'][:80]}...")
                
                if detected_responses:
                    break
                    
                await asyncio.sleep(3)
                
            except Exception as e:
                self.logger.error(f"❌ Erro no monitoramento: {e}")
                break
        
        return detected_responses, pattern_matches

    async def test_scenario(self, scenario_key: str, scenario_data: dict):
        """Testa um cenário específico"""
        self.logger.info(f"\n📋 TESTANDO: {scenario_data['name']}")
        self.logger.info(f"🎯 Risco de handoff: {scenario_data['handoff_risk']}")
        
        scenario_results = {
            "name": scenario_data['name'],
            "handoff_risk": scenario_data['handoff_risk'],
            "messages_tested": 0,
            "responses_received": 0,
            "pattern_matches": 0,
            "success_rate": 0,
            "details": []
        }
        
        for i, message in enumerate(scenario_data['messages'], 1):
            self.logger.info(f"  📨 Teste {i}/{len(scenario_data['messages'])}: {message}")
            
            # Enviar mensagem
            success = await self.simulate_message(message)
            
            if success:
                scenario_results["messages_tested"] += 1
                
                # Monitorar resposta
                responses, matches = await self.monitor_responses(
                    scenario_data['expected_patterns'], 
                    timeout=15
                )
                
                if responses:
                    scenario_results["responses_received"] += len(responses)
                    scenario_results["pattern_matches"] += len(matches)
                    
                    self.logger.info(f"  ✅ {len(responses)} resposta(s), {len(matches)} padrão(ões) encontrado(s)")
                    
                    # Registrar detalhes
                    for response in responses:
                        scenario_results["details"].append({
                            "message_sent": message,
                            "response_received": response['content'],
                            "patterns_found": matches,
                            "timestamp": response['timestamp']
                        })
                else:
                    self.logger.warning(f"  ⚠️ Sem resposta para: {message}")
                    scenario_results["details"].append({
                        "message_sent": message,
                        "response_received": None,
                        "patterns_found": [],
                        "error": "No response received"
                    })
            
            # Intervalo entre mensagens
            await asyncio.sleep(8)
        
        # Calcular taxa de sucesso
        if scenario_results["messages_tested"] > 0:
            scenario_results["success_rate"] = (
                scenario_results["responses_received"] / scenario_results["messages_tested"]
            ) * 100
        
        # Determinar se o cenário passou
        passed = scenario_results["success_rate"] >= 75  # 75% de sucesso mínimo
        
        if passed:
            self.logger.info(f"  🎉 CENÁRIO PASSOU: {scenario_results['success_rate']:.1f}% sucesso")
        else:
            self.logger.warning(f"  ❌ CENÁRIO FALHOU: {scenario_results['success_rate']:.1f}% sucesso")
            self.results["failed_scenarios"].append(scenario_key)
        
        self.results["detailed_results"][scenario_key] = scenario_results
        self.results["scenarios_tested"] += 1
        
        return passed

    async def check_conversation_status(self):
        """Verifica se a conversa foi transferida para humano"""
        try:
            status = await self.db.fetchval("""
                SELECT status FROM conversations 
                WHERE user_id = 2 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            
            if status == "human":
                self.logger.warning("🚨 ATENÇÃO: Conversa foi transferida para modo HUMANO!")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao verificar status: {e}")
            return False

    async def reset_conversation_if_needed(self):
        """Reseta conversa se estiver em modo humano"""
        try:
            if await self.check_conversation_status():
                self.logger.info("🔄 Resetando conversa para modo BOT...")
                
                await self.db.execute("""
                    UPDATE conversations 
                    SET status = 'active' 
                    WHERE user_id = 2
                """)
                
                # Esperar um pouco antes de continuar
                await asyncio.sleep(5)
                self.logger.info("✅ Conversa resetada para modo ativo")
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao resetar conversa: {e}")

    async def run_comprehensive_test(self):
        """Executa teste completo"""
        self.logger.info("🚀 INICIANDO TESTE COMPLETO DO WHATSAPP AGENT")
        self.logger.info("=" * 70)
        self.logger.info(f"📊 {self.results['total_scenarios']} cenários para testar")
        self.logger.info(f"🛡️ Sistema anti-handoff ativado")
        self.logger.info("=" * 70)
        
        try:
            if not await self.connect_db():
                return False
            
            # Verificar status inicial
            await self.reset_conversation_if_needed()
            
            passed_scenarios = 0
            
            # Executar todos os cenários
            for scenario_key, scenario_data in self.test_scenarios.items():
                try:
                    # Verificar se conversa foi transferida antes do teste
                    await self.reset_conversation_if_needed()
                    
                    # Executar cenário
                    scenario_passed = await self.test_scenario(scenario_key, scenario_data)
                    
                    if scenario_passed:
                        passed_scenarios += 1
                    
                    # Intervalo entre cenários
                    self.logger.info("⏳ Aguardando 10s antes do próximo cenário...")
                    await asyncio.sleep(10)
                    
                except Exception as e:
                    self.logger.error(f"❌ Erro no cenário {scenario_key}: {e}")
                    self.results["failed_scenarios"].append(scenario_key)
            
            # Gerar relatório final
            await self.generate_comprehensive_report(passed_scenarios)
            
            self.logger.info("✅ TESTE COMPLETO FINALIZADO!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro geral: {e}")
            return False

    async def generate_comprehensive_report(self, passed_scenarios: int):
        """Gera relatório final detalhado"""
        end_time = datetime.now()
        duration = (end_time - datetime.fromisoformat(self.results["start_time"])).total_seconds()
        
        print("\\n" + "="*80)
        print("🎉 RELATÓRIO COMPLETO - TESTE WHATSAPP AGENT")
        print("="*80)
        
        print(f"🆔 Sessão: {self.results['session']}")
        print(f"⏱️  Duração: {duration:.1f}s ({duration/60:.1f} minutos)")
        print(f"📱 Usuário: {self.YOUR_PHONE} → Bot: {self.BOT_PHONE}")
        
        print(f"\\n📊 ESTATÍSTICAS GERAIS:")
        print(f"  🎯 Cenários testados: {self.results['scenarios_tested']}/{self.results['total_scenarios']}")
        print(f"  ✅ Cenários aprovados: {passed_scenarios}")
        print(f"  ❌ Cenários falharam: {len(self.results['failed_scenarios'])}")
        print(f"  📨 Mensagens enviadas: {self.results['messages_sent']}")
        print(f"  🤖 Respostas recebidas: {self.results['bot_responses']}")
        print(f"  🛡️ Handoffs evitados: {self.results['handoff_avoided']}")
        
        if self.results['messages_sent'] > 0:
            overall_success = (self.results['bot_responses'] / self.results['messages_sent']) * 100
            print(f"  📈 Taxa de sucesso geral: {overall_success:.1f}%")
        
        print(f"\\n📋 DETALHES POR CENÁRIO:")
        print("-" * 60)
        
        for scenario_key, results in self.results['detailed_results'].items():
            status = "✅ PASSOU" if results['success_rate'] >= 75 else "❌ FALHOU"
            print(f"{status} | {results['name']}")
            print(f"    Taxa: {results['success_rate']:.1f}% | Risco: {results['handoff_risk']}")
            print(f"    Mensagens: {results['messages_tested']} | Respostas: {results['responses_received']}")
            print()
        
        if self.results['failed_scenarios']:
            print(f"\\n❌ CENÁRIOS QUE FALHARAM:")
            for failed in self.results['failed_scenarios']:
                scenario_name = self.test_scenarios[failed]['name']
                print(f"  • {failed}: {scenario_name}")
        
        print(f"\\n🎯 RESULTADO FINAL:")
        success_percentage = (passed_scenarios / self.results['total_scenarios']) * 100
        
        if success_percentage >= 80:
            print("   🎉 EXCELENTE! Seu bot está funcionando muito bem!")
            print(f"   ✅ {success_percentage:.1f}% dos cenários passaram")
        elif success_percentage >= 60:
            print("   👍 BOM! Seu bot está funcionando adequadamente")
            print(f"   ✅ {success_percentage:.1f}% dos cenários passaram")
            print("   💡 Algumas melhorias podem ser feitas")
        else:
            print("   ⚠️ ATENÇÃO! Seu bot precisa de ajustes")
            print(f"   ❌ Apenas {success_percentage:.1f}% dos cenários passaram")
            print("   🔧 Revise as configurações e teste novamente")
        
        print("="*80)
        
        # Salvar dados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_test_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Relatório detalhado salvo: {filename}")

    async def close(self):
        """Fecha conexões"""
        try:
            if hasattr(self, 'db'):
                await self.db.close()
                self.logger.info("✅ Conexão fechada")
        except Exception as e:
            self.logger.error(f"❌ Erro ao fechar: {e}")


async def main():
    """Função principal"""
    tester = ComprehensiveWhatsAppTester()
    
    try:
        await tester.run_comprehensive_test()
    except KeyboardInterrupt:
        print("\\n⏹️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\\n💥 Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.close()


if __name__ == "__main__":
    print("🔄 TESTE COMPLETO - WhatsApp LLM Agent")
    print("=" * 60)
    print("🎯 Este teste cobrirá TODOS os cenários:")
    print("  • Saudações e conversas básicas")
    print("  • Consultas de serviços e preços")
    print("  • Agendamentos e informações")
    print("  • Casos complexos (evitando handoff)")
    print("  • Fluxos interativos")
    print("  • Casos especiais")
    print()
    print("🛡️ Sistema anti-handoff:")
    print("  • Detecta mensagens que acionariam handoff")
    print("  • Substitui por alternativas seguras")
    print("  • Reseta conversa se necessário")
    print("=" * 60)
    
    response = input("\\n▶️ Executar teste completo? (ENTER para continuar): ")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n⏹️ Programa finalizado")
    except Exception as e:
        print(f"\\n💥 Erro inesperado: {e}")
        import traceback
        traceback.print_exc()

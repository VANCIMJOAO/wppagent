"""
🧪 Testes Reais End-to-End - Jornadas Completas do Usuário
Testa fluxos completos reais sem mocks, do início ao fim
"""
import pytest
import asyncio
import time
from datetime import datetime, timedelta


class TestRealUserJourneys:
    """🎯 Jornadas reais completas de usuários"""
    
    @pytest.mark.real
    @pytest.mark.e2e_real
    @pytest.mark.conversation
    async def test_complete_discovery_journey(self, conversation_tester, real_test_reporter):
        """Testa jornada completa de descoberta dos serviços"""
        start_time = time.time()
        
        # Jornada real de um cliente descobrindo os serviços
        discovery_flow = [
            "Oi!",
            "Vocês fazem corte de cabelo?",
            "Que tipos de corte vocês fazem?",
            "Quanto custa?",
            "E barba? Fazem também?",
            "Qual o preço da barba?",
            "Tem algum pacote corte + barba?",
            "Que horário vocês funcionam?",
            "Trabalham no sábado?",
            "Domingo também?",
            "Onde fica a barbearia?",
            "É fácil de chegar?",
            "Tem estacionamento?",
            "Como é o pagamento? Aceitam cartão?",
            "PIX também?",
            "Perfeito! Obrigado pelas informações"
        ]
        
        print(f"\n🔍 INICIANDO JORNADA DE DESCOBERTA")
        print(f"📱 Telefone: {conversation_tester.phone}")
        print(f"💬 Mensagens a enviar: {len(discovery_flow)}")
        
        results = await conversation_tester.send_conversation_flow(
            discovery_flow,
            delay=2.0  # 2 segundos entre mensagens para simular real
        )
        
        duration = time.time() - start_time
        success_rate = conversation_tester.get_success_rate()
        
        real_test_reporter.record_test(
            "complete_discovery_journey",
            success_rate >= 85.0,
            duration,
            {
                "journey_type": "discovery",
                "total_messages": len(discovery_flow),
                "success_rate": success_rate,
                "duration": duration,
                "phone": conversation_tester.phone
            }
        )
        
        assert success_rate >= 85.0, f"Jornada de descoberta falhou: {success_rate:.1f}%"
        
        print(f"✅ JORNADA DE DESCOBERTA COMPLETA")
        print(f"⏱️ Duração: {duration:.1f}s")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        print(f"💬 Mensagens processadas: {len(results)}")
    
    @pytest.mark.real
    @pytest.mark.e2e_real
    @pytest.mark.conversation
    async def test_complete_booking_journey(self, conversation_tester, real_test_reporter):
        """Testa jornada completa de agendamento real"""
        start_time = time.time()
        
        customer_name = f"Cliente Teste {int(time.time())}"
        
        # Jornada completa de agendamento
        booking_flow = [
            "Olá, boa tarde!",
            "Gostaria de agendar um corte de cabelo",
            "Para amanhã, se possível",
            "Que horários vocês têm disponível?",
            "Manhã ou tarde?",
            "Prefiro de tarde",
            "14h está bom?",
            "15h também serve",
            "Então vamos de 15h mesmo",
            f"Meu nome é {customer_name}",
            "É João mesmo",
            "Telefone é esse mesmo que estou falando",
            "Quero só o corte masculino",
            "Quanto fica?",
            "Perfeito",
            "Confirmo o agendamento",
            "Para amanhã às 15h",
            "Muito obrigado!",
            "Até amanhã"
        ]
        
        print(f"\n📅 INICIANDO JORNADA DE AGENDAMENTO")
        print(f"📱 Telefone: {conversation_tester.phone}")
        print(f"👤 Cliente: {customer_name}")
        print(f"💬 Mensagens a enviar: {len(booking_flow)}")
        
        results = await conversation_tester.send_conversation_flow(
            booking_flow,
            delay=2.5  # 2.5 segundos entre mensagens
        )
        
        duration = time.time() - start_time
        success_rate = conversation_tester.get_success_rate()
        
        real_test_reporter.record_test(
            "complete_booking_journey",
            success_rate >= 85.0,
            duration,
            {
                "journey_type": "booking",
                "customer_name": customer_name,
                "total_messages": len(booking_flow),
                "success_rate": success_rate,
                "duration": duration,
                "phone": conversation_tester.phone
            }
        )
        
        assert success_rate >= 85.0, f"Jornada de agendamento falhou: {success_rate:.1f}%"
        
        print(f"✅ JORNADA DE AGENDAMENTO COMPLETA")
        print(f"👤 Cliente: {customer_name}")
        print(f"⏱️ Duração: {duration:.1f}s")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        print(f"💬 Mensagens processadas: {len(results)}")
    
    @pytest.mark.real
    @pytest.mark.e2e_real
    @pytest.mark.conversation
    async def test_complete_support_journey(self, conversation_tester, real_test_reporter):
        """Testa jornada completa de suporte/dúvidas"""
        start_time = time.time()
        
        # Jornada de suporte com múltiplas dúvidas
        support_flow = [
            "Oi, preciso de ajuda",
            "Marquei um horário mas esqueci quando é",
            "É para hoje?",
            "Ou é amanhã?",
            "Foi marcado em nome de João Silva",
            "Pode verificar pra mim?",
            "Ah, e onde fica a barbearia mesmo?",
            "É perto do shopping?",
            "Tem ponto de referência?",
            "Como chego de ônibus?",
            "E de carro?",
            "Que horas vocês abrem?",
            "E fecham que horas?",
            "Almoçam que horas?",
            "Preciso chegar antes do almoço",
            "Posso remarcar se precisar?",
            "Até que horas posso cancelar?",
            "Tem taxa de cancelamento?",
            "Entendi, obrigado",
            "Até logo!"
        ]
        
        print(f"\n🆘 INICIANDO JORNADA DE SUPORTE")
        print(f"📱 Telefone: {conversation_tester.phone}")
        print(f"💬 Mensagens a enviar: {len(support_flow)}")
        
        results = await conversation_tester.send_conversation_flow(
            support_flow,
            delay=1.8  # 1.8 segundos entre mensagens
        )
        
        duration = time.time() - start_time
        success_rate = conversation_tester.get_success_rate()
        
        real_test_reporter.record_test(
            "complete_support_journey",
            success_rate >= 85.0,
            duration,
            {
                "journey_type": "support",
                "total_messages": len(support_flow),
                "success_rate": success_rate,
                "duration": duration,
                "phone": conversation_tester.phone
            }
        )
        
        assert success_rate >= 85.0, f"Jornada de suporte falhou: {success_rate:.1f}%"
        
        print(f"✅ JORNADA DE SUPORTE COMPLETA")
        print(f"⏱️ Duração: {duration:.1f}s")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        print(f"💬 Mensagens processadas: {len(results)}")


class TestRealComplexScenarios:
    """🎭 Cenários reais complexos e realistas"""
    
    @pytest.mark.real
    @pytest.mark.e2e_real
    @pytest.mark.slow
    async def test_indecisive_customer_journey(self, conversation_tester, real_test_reporter):
        """Testa cliente indeciso que muda de ideia várias vezes"""
        start_time = time.time()
        
        # Cliente indeciso e realista
        indecisive_flow = [
            "Oi",
            "Quero cortar o cabelo",
            "Na verdade, não sei se quero",
            "Quanto custa mesmo?",
            "Hmmm, está caro",
            "Tem desconto?",
            "E se eu trouxer um amigo?",
            "Na verdade, quero só a barba",
            "Não, melhor só corte mesmo",
            "Ou o pacote completo",
            "Deixa eu pensar...",
            "Vocês fazem sobrancelha também?",
            "Ah, que bom",
            "Então quero corte + sobrancelha",
            "Para quando posso agendar?",
            "Amanhã é muito em cima?",
            "E depois de amanhã?",
            "Que horários têm?",
            "De manhã eu não posso",
            "Tarde também é complicado",
            "Noite vocês atendem?",
            "Ah, não atendem...",
            "Então tem que ser tarde mesmo",
            "15h30 pode ser?",
            "Ou 16h?",
            "Melhor 16h",
            "Meu nome é Carlos",
            "Carlos da Silva",
            "Pode confirmar?",
            "Espera, mudei de ideia",
            "Quero só o corte mesmo",
            "Confirma só o corte?",
            "Para 16h de depois de amanhã",
            "Isso mesmo",
            "Valeu!"
        ]
        
        print(f"\n🤔 INICIANDO JORNADA CLIENTE INDECISO")
        print(f"📱 Telefone: {conversation_tester.phone}")
        print(f"💬 Mensagens a enviar: {len(indecisive_flow)}")
        
        results = await conversation_tester.send_conversation_flow(
            indecisive_flow,
            delay=1.5  # Cliente indeciso demora entre mensagens
        )
        
        duration = time.time() - start_time
        success_rate = conversation_tester.get_success_rate()
        
        real_test_reporter.record_test(
            "indecisive_customer_journey",
            success_rate >= 80.0,  # Mais flexível para cenário complexo
            duration,
            {
                "journey_type": "indecisive_customer",
                "total_messages": len(indecisive_flow),
                "success_rate": success_rate,
                "duration": duration,
                "complexity": "high"
            }
        )
        
        assert success_rate >= 80.0, f"Cliente indeciso falhou: {success_rate:.1f}%"
        
        print(f"✅ JORNADA CLIENTE INDECISO COMPLETA")
        print(f"⏱️ Duração: {duration:.1f}s")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        print(f"🤔 Mudanças de ideia processadas: {len(results)}")
    
    @pytest.mark.real
    @pytest.mark.e2e_real
    async def test_upset_customer_recovery(self, conversation_tester, real_test_reporter):
        """Testa recuperação de cliente insatisfeito"""
        start_time = time.time()
        
        # Cliente começando insatisfeito
        upset_recovery_flow = [
            "Olha, estou muito chateado",
            "Marquei horário ontem e ninguém me atendeu",
            "Cheguei na hora certa",
            "Esperei 30 minutos",
            "E nada",
            "Isso é falta de respeito",
            "Quero uma explicação",
            "Não é a primeira vez que isso acontece",
            "Estou pensando em procurar outra barbearia",
            "Vocês podem me dar uma satisfação?",
            "Pelo menos uma desculpa?",
            "Ok, aceito a explicação",
            "Mas quero garantia que não vai acontecer de novo",
            "Posso remarcar?",
            "Para amanhã mesmo",
            "Que horas vocês garantem que vão me atender?",
            "14h está bom",
            "Meu nome é Roberto Santos",
            "Espero não ter problemas dessa vez",
            "Confirma aí pra mim",
            "E me mandem uma mensagem pra confirmar",
            "Valeu, até amanhã",
            "Confio que vai dar certo dessa vez"
        ]
        
        print(f"\n😠 INICIANDO JORNADA CLIENTE INSATISFEITO")
        print(f"📱 Telefone: {conversation_tester.phone}")
        print(f"💬 Mensagens a enviar: {len(upset_recovery_flow)}")
        
        results = await conversation_tester.send_conversation_flow(
            upset_recovery_flow,
            delay=2.2  # Cliente chateado demora mais para escrever
        )
        
        duration = time.time() - start_time
        success_rate = conversation_tester.get_success_rate()
        
        real_test_reporter.record_test(
            "upset_customer_recovery",
            success_rate >= 80.0,
            duration,
            {
                "journey_type": "upset_customer_recovery",
                "total_messages": len(upset_recovery_flow),
                "success_rate": success_rate,
                "duration": duration,
                "emotional_context": "upset_to_satisfied"
            }
        )
        
        assert success_rate >= 80.0, f"Recuperação de cliente falhou: {success_rate:.1f}%"
        
        print(f"✅ RECUPERAÇÃO DE CLIENTE COMPLETA")
        print(f"⏱️ Duração: {duration:.1f}s")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        print(f"🔄 Cliente recuperado com sucesso")


class TestRealMultiUserScenarios:
    """👥 Testes reais com múltiplos usuários simultâneos"""
    
    @pytest.mark.real
    @pytest.mark.e2e_real
    @pytest.mark.performance
    async def test_concurrent_real_conversations(self, real_api_client, real_test_reporter):
        """Testa conversas reais simultâneas"""
        start_time = time.time()
        
        # Diferentes tipos de clientes simultâneos
        customer_scenarios = [
            {
                "phone": f"5511800{int(time.time() % 100000):05d}",
                "type": "quick_booker",
                "messages": [
                    "Oi, quero agendar",
                    "Para hoje à tarde",
                    "16h pode?",
                    "João Silva",
                    "Confirma"
                ]
            },
            {
                "phone": f"5511801{int(time.time() % 100000):05d}",
                "type": "price_shopper",
                "messages": [
                    "Quanto custa corte?",
                    "E barba?",
                    "Tem desconto?",
                    "Obrigado"
                ]
            },
            {
                "phone": f"5511802{int(time.time() % 100000):05d}",
                "type": "detailed_inquirer",
                "messages": [
                    "Oi, tenho algumas dúvidas",
                    "Que tipos de corte fazem?",
                    "Trabalham com máquina ou tesoura?",
                    "Fazem degradê?",
                    "E corte social?",
                    "Quanto custa cada um?",
                    "Onde fica?",
                    "Valeu!"
                ]
            }
        ]
        
        async def execute_customer_scenario(scenario):
            """Executa cenário de um cliente"""
            results = []
            for message in scenario["messages"]:
                result = await real_api_client.send_webhook_message(
                    scenario["phone"], 
                    message
                )
                results.append(result)
                await asyncio.sleep(1.0)  # 1 segundo entre mensagens do mesmo cliente
            
            success_rate = (sum(1 for r in results if r["success"]) / len(results)) * 100
            return {
                "phone": scenario["phone"],
                "type": scenario["type"],
                "success_rate": success_rate,
                "total_messages": len(results)
            }
        
        print(f"\n👥 INICIANDO CONVERSAS SIMULTÂNEAS")
        print(f"🎭 Cenários: {len(customer_scenarios)}")
        
        # Executar todos os cenários simultaneamente
        tasks = [execute_customer_scenario(scenario) for scenario in customer_scenarios]
        scenario_results = await asyncio.gather(*tasks)
        
        duration = time.time() - start_time
        
        # Calcular métricas gerais
        total_messages = sum(r["total_messages"] for r in scenario_results)
        avg_success_rate = sum(r["success_rate"] for r in scenario_results) / len(scenario_results)
        
        real_test_reporter.record_test(
            "concurrent_real_conversations",
            avg_success_rate >= 80.0,
            duration,
            {
                "total_scenarios": len(customer_scenarios),
                "total_messages": total_messages,
                "average_success_rate": avg_success_rate,
                "scenario_results": scenario_results
            }
        )
        
        assert avg_success_rate >= 80.0, f"Conversas simultâneas falharam: {avg_success_rate:.1f}%"
        
        print(f"✅ CONVERSAS SIMULTÂNEAS COMPLETAS")
        print(f"⏱️ Duração: {duration:.1f}s")
        print(f"📊 Total de mensagens: {total_messages}")
        print(f"📈 Taxa média de sucesso: {avg_success_rate:.1f}%")
        
        for result in scenario_results:
            print(f"  📱 {result['type']}: {result['success_rate']:.1f}% ({result['total_messages']} msgs)")


class TestRealSystemLimits:
    """🔬 Testes reais dos limites do sistema"""
    
    @pytest.mark.real
    @pytest.mark.e2e_real
    @pytest.mark.slow
    async def test_very_long_conversation(self, conversation_tester, real_test_reporter):
        """Testa conversa muito longa e detalhada"""
        start_time = time.time()
        
        # Conversa extremamente longa simulando cliente muito detalhista
        very_long_conversation = [
            "Olá, boa tarde",
            "Estou procurando uma barbearia boa na região",
            "Vi que vocês têm boas avaliações",
            "Gostaria de saber mais sobre os serviços",
            "Fazem corte masculino?",
            "Que tipos de corte vocês fazem?",
            "Fazem corte social?",
            "E degradê?",
            "Corte com máquina também?",
            "Só tesoura?",
            "Como é o processo?",
            "Lavam o cabelo antes?",
            "E depois?",
            "Usam produtos especiais?",
            "Fazem barba também?",
            "Como é feita a barba?",
            "Usam navalha?",
            "Ou só máquina?",
            "Fazem bigode?",
            "E costeleta?",
            "Sobrancelha masculina fazem?",
            "Como é o procedimento?",
            "Dói muito?",
            "Quanto tempo demora cada serviço?",
            "Corte demora quanto tempo?",
            "E barba?",
            "Sobrancelha?",
            "Se eu fizer tudo junto, quanto tempo fica?",
            "E o preço de cada um?",
            "Corte custa quanto?",
            "Barba?",
            "Sobrancelha?",
            "Tem algum pacote?",
            "Desconto para tudo junto?",
            "Como funciona o agendamento?",
            "Posso escolher o horário?",
            "E o profissional?",
            "Tem preferência?",
            "Como é o local?",
            "É limpo?",
            "Esterilizam os equipamentos?",
            "Seguem protocolos de higiene?",
            "Onde fica exatamente?",
            "É fácil de achar?",
            "Tem ponto de referência?",
            "Como chego de transporte público?",
            "Tem estacionamento?",
            "É pago?",
            "Que horas abrem?",
            "E fecham?",
            "Funcionam aos sábados?",
            "E domingos?",
            "Feriados atendem?",
            "Como é o pagamento?",
            "Aceitam dinheiro?",
            "Cartão de débito?",
            "Crédito?",
            "PIX?",
            "Pode pagar na hora?",
            "Ou tem que pagar antes?",
            "Se eu quiser remarcar, posso?",
            "Até quando posso cancelar?",
            "Tem taxa de cancelamento?",
            "E se eu me atrasar?",
            "Quanto tempo esperam?",
            "Posso levar acompanhante?",
            "Tem lugar para esperar?",
            "Oferecem alguma coisa? Café, água?",
            "Ok, acho que esclareceu tudo",
            "Quero agendar então",
            "Para quando posso?",
            "Amanhã tem vaga?",
            "Que horas?",
            "De manhã prefiro",
            "9h pode ser?",
            "Ou 10h?",
            "10h está bom",
            "Quero o pacote completo",
            "Corte + barba + sobrancelha",
            "Quanto fica tudo?",
            "Perfeito",
            "Meu nome é Fernando Silva",
            "Telefone é este mesmo",
            "Endereço precisa?",
            "Moro na Vila Madalena",
            "Confirma para mim?",
            "Amanhã às 10h",
            "Pacote completo",
            "Quanto tempo vai demorar tudo?",
            "Ok, chegou 10 minutos antes",
            "Perfeito",
            "Muito obrigado",
            "Até amanhã!"
        ]
        
        print(f"\n📚 INICIANDO CONVERSA MUITO LONGA")
        print(f"📱 Telefone: {conversation_tester.phone}")
        print(f"💬 Mensagens a enviar: {len(very_long_conversation)}")
        print(f"⏱️ Tempo estimado: ~{len(very_long_conversation) * 1.5 / 60:.1f} minutos")
        
        results = await conversation_tester.send_conversation_flow(
            very_long_conversation,
            delay=1.5  # 1.5 segundos entre mensagens
        )
        
        duration = time.time() - start_time
        success_rate = conversation_tester.get_success_rate()
        
        real_test_reporter.record_test(
            "very_long_conversation",
            success_rate >= 80.0,
            duration,
            {
                "journey_type": "very_long_detailed",
                "total_messages": len(very_long_conversation),
                "success_rate": success_rate,
                "duration": duration,
                "conversation_length": "extreme"
            }
        )
        
        assert success_rate >= 80.0, f"Conversa longa falhou: {success_rate:.1f}%"
        
        print(f"✅ CONVERSA MUITO LONGA COMPLETA")
        print(f"⏱️ Duração: {duration/60:.1f} minutos")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        print(f"💬 Total de mensagens: {len(results)}")
        print(f"🏆 Sistema suportou conversa extremamente detalhada!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "real and e2e_real"])

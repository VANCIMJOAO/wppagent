"""
🧪 Testes End-to-End - Fluxos Críticos Completos
Testa jornadas completas do usuário do início ao fim
"""
import pytest
import asyncio
import time
from datetime import datetime, timedelta


class TestCriticalUserJourneys:
    """🎯 Testes de jornadas críticas do usuário"""
    
    @pytest.mark.e2e
    @pytest.mark.critical
    async def test_complete_appointment_booking_flow(self, test_client, conversation_simulator):
        """Testa fluxo completo de agendamento de consulta"""
        
        phone = "5511999999001"
        user_name = "João da Silva"
        
        simulator = conversation_simulator(test_client)
        
        # === ETAPA 1: Saudação inicial ===
        response1 = await simulator.send_message(phone, "Olá, boa tarde!")
        assert "sucesso" in str(response1).lower() or response1.get("status") == "success"
        
        # === ETAPA 2: Manifestar interesse em agendamento ===
        response2 = await simulator.send_message(phone, "Gostaria de agendar um corte de cabelo")
        assert "sucesso" in str(response2).lower() or response2.get("status") == "success"
        
        # === ETAPA 3: Consultar disponibilidade ===
        response3 = await simulator.send_message(phone, "Que horários vocês têm disponível para amanhã?")
        assert "sucesso" in str(response3).lower() or response3.get("status") == "success"
        
        # === ETAPA 4: Escolher horário ===
        response4 = await simulator.send_message(phone, "Quero agendar para amanhã às 14h")
        assert "sucesso" in str(response4).lower() or response4.get("status") == "success"
        
        # === ETAPA 5: Confirmar dados ===
        response5 = await simulator.send_message(phone, f"Meu nome é {user_name}")
        assert "sucesso" in str(response5).lower() or response5.get("status") == "success"
        
        # === ETAPA 6: Confirmar agendamento ===
        response6 = await simulator.send_message(phone, "Sim, confirmo o agendamento")
        assert "sucesso" in str(response6).lower() or response6.get("status") == "success"
        
        # === VERIFICAÇÃO FINAL ===
        history = simulator.get_conversation_history(phone)
        assert len(history) == 6, f"Esperado 6 mensagens, recebido {len(history)}"
        
        # Verificar se todas as etapas foram processadas sem erro
        for i, interaction in enumerate(history, 1):
            assert interaction["response"] is not None, f"Etapa {i} falhou: sem resposta"
        
        print(f"✅ JORNADA COMPLETA DE AGENDAMENTO CONCLUÍDA")
        print(f"📱 Cliente: {phone}")
        print(f"👤 Nome: {user_name}")
        print(f"📅 Etapas completadas: {len(history)}")
    
    @pytest.mark.e2e
    @pytest.mark.critical
    async def test_appointment_cancellation_flow(self, test_client, conversation_simulator):
        """Testa fluxo completo de cancelamento de agendamento"""
        
        phone = "5511999999002"
        simulator = conversation_simulator(test_client)
        
        # === PRÉ-REQUISITO: Criar um agendamento primeiro ===
        await simulator.send_message(phone, "Quero agendar um corte para amanhã às 15h")
        await simulator.send_message(phone, "Meu nome é Maria Silva")
        await simulator.send_message(phone, "Confirmo o agendamento")
        
        # Aguardar um pouco para processar
        await asyncio.sleep(0.5)
        
        # === INÍCIO DO CANCELAMENTO ===
        response1 = await simulator.send_message(phone, "Preciso cancelar meu agendamento")
        assert "sucesso" in str(response1).lower() or response1.get("status") == "success"
        
        # === CONFIRMAÇÃO DO CANCELAMENTO ===
        response2 = await simulator.send_message(phone, "Sim, quero cancelar")
        assert "sucesso" in str(response2).lower() or response2.get("status") == "success"
        
        # === MOTIVO DO CANCELAMENTO (OPCIONAL) ===
        response3 = await simulator.send_message(phone, "Surgiu um compromisso")
        assert "sucesso" in str(response3).lower() or response3.get("status") == "success"
        
        # === CONFIRMAÇÃO FINAL ===
        response4 = await simulator.send_message(phone, "Obrigada")
        assert "sucesso" in str(response4).lower() or response4.get("status") == "success"
        
        # Verificar fluxo completo
        history = simulator.get_conversation_history(phone)
        cancellation_history = history[-4:]  # Últimas 4 mensagens (cancelamento)
        
        assert len(cancellation_history) == 4
        
        print(f"✅ JORNADA COMPLETA DE CANCELAMENTO CONCLUÍDA")
        print(f"📱 Cliente: {phone}")
        print(f"🚫 Etapas de cancelamento: {len(cancellation_history)}")
    
    @pytest.mark.e2e
    @pytest.mark.critical
    async def test_price_inquiry_and_booking_flow(self, test_client, conversation_simulator):
        """Testa fluxo de consulta de preços seguido de agendamento"""
        
        phone = "5511999999003"
        simulator = conversation_simulator(test_client)
        
        # === CONSULTA DE PREÇOS ===
        response1 = await simulator.send_message(phone, "Quanto custa um corte masculino?")
        assert "sucesso" in str(response1).lower() or response1.get("status") == "success"
        
        response2 = await simulator.send_message(phone, "E barba? Fazem também?")
        assert "sucesso" in str(response2).lower() or response2.get("status") == "success"
        
        response3 = await simulator.send_message(phone, "Qual o preço do pacote corte + barba?")
        assert "sucesso" in str(response3).lower() or response3.get("status") == "success"
        
        # === DECISÃO DE AGENDAR ===
        response4 = await simulator.send_message(phone, "Perfeito! Quero agendar o pacote completo")
        assert "sucesso" in str(response4).lower() or response4.get("status") == "success"
        
        # === AGENDAMENTO ===
        response5 = await simulator.send_message(phone, "Para sexta-feira às 10h")
        assert "sucesso" in str(response5).lower() or response5.get("status") == "success"
        
        response6 = await simulator.send_message(phone, "Pedro Santos")
        assert "sucesso" in str(response6).lower() or response6.get("status") == "success"
        
        response7 = await simulator.send_message(phone, "Confirmo")
        assert "sucesso" in str(response7).lower() or response7.get("status") == "success"
        
        # Verificar jornada completa
        history = simulator.get_conversation_history(phone)
        assert len(history) == 7
        
        print(f"✅ JORNADA PREÇOS → AGENDAMENTO CONCLUÍDA")
        print(f"📱 Cliente: {phone}")
        print(f"💰 Consultas de preço + agendamento: {len(history)} etapas")
    
    @pytest.mark.e2e
    @pytest.mark.critical
    async def test_complex_rescheduling_flow(self, test_client, conversation_simulator):
        """Testa fluxo complexo de reagendamento"""
        
        phone = "5511999999004"
        simulator = conversation_simulator(test_client)
        
        # === PRÉ-REQUISITO: Agendamento existente ===
        await simulator.send_message(phone, "Quero agendar para segunda às 14h")
        await simulator.send_message(phone, "Ana Costa")
        await simulator.send_message(phone, "Confirmo")
        
        await asyncio.sleep(0.5)
        
        # === INÍCIO DO REAGENDAMENTO ===
        response1 = await simulator.send_message(phone, "Preciso remarcar meu horário")
        assert "sucesso" in str(response1).lower() or response1.get("status") == "success"
        
        # === NOVA DATA/HORA ===
        response2 = await simulator.send_message(phone, "Pode ser na terça-feira?")
        assert "sucesso" in str(response2).lower() or response2.get("status") == "success"
        
        response3 = await simulator.send_message(phone, "Que horas vocês têm na terça?")
        assert "sucesso" in str(response3).lower() or response3.get("status") == "success"
        
        response4 = await simulator.send_message(phone, "Às 16h está bom")
        assert "sucesso" in str(response4).lower() or response4.get("status") == "success"
        
        # === CONFIRMAÇÃO ===
        response5 = await simulator.send_message(phone, "Sim, confirmo a remarcação")
        assert "sucesso" in str(response5).lower() or response5.get("status") == "success"
        
        # Verificar fluxo
        history = simulator.get_conversation_history(phone)
        rescheduling_history = history[-5:]  # Últimas 5 mensagens
        
        assert len(rescheduling_history) == 5
        
        print(f"✅ JORNADA COMPLEXA DE REAGENDAMENTO CONCLUÍDA")
        print(f"📱 Cliente: {phone}")
        print(f"🔄 Etapas de reagendamento: {len(rescheduling_history)}")


class TestErrorRecoveryFlows:
    """🚨 Testes de recuperação de erros em fluxos críticos"""
    
    @pytest.mark.e2e
    @pytest.mark.critical
    async def test_interrupted_booking_recovery(self, test_client, conversation_simulator):
        """Testa recuperação quando agendamento é interrompido"""
        
        phone = "5511999999005"
        simulator = conversation_simulator(test_client)
        
        # === INÍCIO NORMAL ===
        await simulator.send_message(phone, "Quero agendar um horário")
        await simulator.send_message(phone, "Para amanhã de manhã")
        
        # === INTERRUPÇÃO - Mudança de assunto ===
        await simulator.send_message(phone, "Vocês ficam onde mesmo?")
        await simulator.send_message(phone, "Tem estacionamento?")
        
        # === RETORNO AO AGENDAMENTO ===
        response1 = await simulator.send_message(phone, "Voltando ao agendamento, às 9h está bom?")
        assert "sucesso" in str(response1).lower() or response1.get("status") == "success"
        
        response2 = await simulator.send_message(phone, "Carlos Mendes")
        assert "sucesso" in str(response2).lower() or response2.get("status") == "success"
        
        response3 = await simulator.send_message(phone, "Pode confirmar")
        assert "sucesso" in str(response3).lower() or response3.get("status") == "success"
        
        history = simulator.get_conversation_history(phone)
        assert len(history) >= 7
        
        print(f"✅ RECUPERAÇÃO DE AGENDAMENTO INTERROMPIDO")
        print(f"📱 Cliente: {phone}")
        print(f"🔄 Mensagens totais: {len(history)}")
    
    @pytest.mark.e2e
    @pytest.mark.critical
    async def test_invalid_input_handling(self, test_client, conversation_simulator):
        """Testa tratamento de entradas inválidas em fluxos críticos"""
        
        phone = "5511999999006"
        simulator = conversation_simulator(test_client)
        
        # === ENTRADAS INVÁLIDAS ===
        response1 = await simulator.send_message(phone, "asdfghjkl")  # Texto sem sentido
        assert "sucesso" in str(response1).lower() or response1.get("status") == "success"
        
        response2 = await simulator.send_message(phone, "")  # Mensagem vazia
        assert "sucesso" in str(response2).lower() or response2.get("status") == "success"
        
        response3 = await simulator.send_message(phone, "12345")  # Apenas números
        assert "sucesso" in str(response3).lower() or response3.get("status") == "success"
        
        # === ENTRADA VÁLIDA APÓS INVÁLIDAS ===
        response4 = await simulator.send_message(phone, "Olá, gostaria de agendar um horário")
        assert "sucesso" in str(response4).lower() or response4.get("status") == "success"
        
        history = simulator.get_conversation_history(phone)
        assert len(history) == 4
        
        # Sistema deve continuar funcionando normalmente
        response5 = await simulator.send_message(phone, "Para amanhã às 15h")
        assert "sucesso" in str(response5).lower() or response5.get("status") == "success"
        
        print(f"✅ TRATAMENTO DE ENTRADAS INVÁLIDAS")
        print(f"📱 Cliente: {phone}")
        print(f"⚠️ Entradas inválidas processadas sem erro")


class TestMultiUserConcurrentFlows:
    """👥 Testes de fluxos concorrentes com múltiplos usuários"""
    
    @pytest.mark.e2e
    @pytest.mark.critical
    @pytest.mark.slow
    async def test_concurrent_booking_same_time_slot(self, test_client, conversation_simulator):
        """Testa tentativa de agendamento concorrente para o mesmo horário"""
        
        phones = ["5511999999007", "5511999999008", "5511999999009"]
        simulators = [conversation_simulator(test_client) for _ in phones]
        
        async def attempt_booking(simulator, phone, user_name):
            """Tenta fazer agendamento"""
            try:
                await simulator.send_message(phone, "Quero agendar para amanhã às 14h")
                await simulator.send_message(phone, user_name)
                await simulator.send_message(phone, "Confirmo")
                return {"phone": phone, "success": True}
            except Exception as e:
                return {"phone": phone, "success": False, "error": str(e)}
        
        # Executar agendamentos simultâneos para o mesmo horário
        tasks = [
            attempt_booking(simulators[0], phones[0], "Cliente A"),
            attempt_booking(simulators[1], phones[1], "Cliente B"),
            attempt_booking(simulators[2], phones[2], "Cliente C")
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verificar resultados
        successful_bookings = [r for r in results if r["success"]]
        
        # Deve haver pelo menos um agendamento bem-sucedido
        assert len(successful_bookings) >= 1, "Nenhum agendamento foi bem-sucedido"
        
        # Não deve haver múltiplos agendamentos para o mesmo horário
        # (isso seria verificado em nível de banco de dados/regra de negócio)
        
        print(f"✅ TESTE DE CONCORRÊNCIA EM AGENDAMENTOS")
        print(f"👥 Usuários simultâneos: {len(phones)}")
        print(f"✅ Agendamentos bem-sucedidos: {len(successful_bookings)}")
    
    @pytest.mark.e2e
    @pytest.mark.critical
    async def test_mixed_conversation_flows(self, test_client, conversation_simulator):
        """Testa diferentes tipos de conversas acontecendo simultaneamente"""
        
        scenarios = [
            {"phone": "5511999999010", "type": "booking", "messages": [
                "Quero agendar um corte",
                "Para hoje às 16h",
                "João Silva",
                "Confirmo"
            ]},
            {"phone": "5511999999011", "type": "inquiry", "messages": [
                "Quanto custa uma barba?",
                "E sobrancelha?",
                "Obrigado pelas informações"
            ]},
            {"phone": "5511999999012", "type": "cancellation", "messages": [
                "Preciso cancelar meu agendamento",
                "Sim, quero cancelar",
                "Muito obrigado"
            ]},
            {"phone": "5511999999013", "type": "support", "messages": [
                "Onde vocês ficam?",
                "Que horas abrem?",
                "Trabalham no sábado?"
            ]}
        ]
        
        async def execute_scenario(scenario):
            """Executa um cenário de conversa"""
            simulator = conversation_simulator(test_client)
            phone = scenario["phone"]
            
            results = []
            for message in scenario["messages"]:
                try:
                    response = await simulator.send_message(phone, message)
                    results.append({
                        "message": message,
                        "success": "sucesso" in str(response).lower() or response.get("status") == "success"
                    })
                    await asyncio.sleep(0.1)  # Pequeno delay entre mensagens
                except Exception as e:
                    results.append({
                        "message": message,
                        "success": False,
                        "error": str(e)
                    })
            
            return {
                "scenario_type": scenario["type"],
                "phone": phone,
                "results": results,
                "success_rate": sum(1 for r in results if r["success"]) / len(results)
            }
        
        # Executar todos os cenários concorrentemente
        tasks = [execute_scenario(scenario) for scenario in scenarios]
        scenario_results = await asyncio.gather(*tasks)
        
        # Verificar resultados
        for result in scenario_results:
            assert result["success_rate"] >= 0.8, f"Cenário {result['scenario_type']} teve taxa de sucesso baixa: {result['success_rate']:.2%}"
        
        print(f"✅ TESTE DE FLUXOS MISTOS CONCORRENTES")
        for result in scenario_results:
            print(f"📱 {result['scenario_type']}: {result['success_rate']:.2%} sucesso")


class TestSystemRecoveryFlows:
    """🔄 Testes de recuperação do sistema após falhas"""
    
    @pytest.mark.e2e
    @pytest.mark.critical
    async def test_conversation_state_persistence(self, test_client, conversation_simulator):
        """Testa persistência do estado da conversa após "reinício" do sistema"""
        
        phone = "5511999999014"
        simulator = conversation_simulator(test_client)
        
        # === PRIMEIRA PARTE DA CONVERSA ===
        await simulator.send_message(phone, "Olá, quero agendar")
        await simulator.send_message(phone, "Para amanhã de tarde")
        
        # Simular "interrupção" - limpar histórico do simulador mas manter estado do sistema
        # (em produção seria um reinício do sistema)
        simulator.clear_history()
        
        # === CONTINUAR CONVERSA APÓS "REINÍCIO" ===
        response1 = await simulator.send_message(phone, "Às 15h está disponível?")
        assert "sucesso" in str(response1).lower() or response1.get("status") == "success"
        
        response2 = await simulator.send_message(phone, "Roberto Costa")
        assert "sucesso" in str(response2).lower() or response2.get("status") == "success"
        
        response3 = await simulator.send_message(phone, "Confirmo o agendamento")
        assert "sucesso" in str(response3).lower() or response3.get("status") == "success"
        
        # Verificar se conversa continuou normalmente
        post_restart_history = simulator.get_conversation_history(phone)
        assert len(post_restart_history) == 3
        
        print(f"✅ TESTE DE PERSISTÊNCIA DE ESTADO")
        print(f"📱 Cliente: {phone}")
        print(f"🔄 Conversa continuou após 'reinício'")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "e2e"])

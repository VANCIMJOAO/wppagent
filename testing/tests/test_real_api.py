"""
🧪 Testes Reais de API - SEM MOCKS
Testa a API real rodando, incluindo webhook e fluxos completos
"""
import pytest
import asyncio
import time
from datetime import datetime


class TestRealAPIHealth:
    """🏥 Testes de saúde da API real"""
    
    @pytest.mark.real
    @pytest.mark.api
    async def test_api_is_running(self, real_api_client):
        """Verifica se a API está rodando e respondendo"""
        health = await real_api_client.health_check()
        
        assert health["healthy"], f"API não está saudável: {health}"
        assert health["status"] == 200, f"Status inesperado: {health['status']}"
        assert health["data"] is not None, "Dados de saúde não retornados"
        
        print(f"✅ API rodando e saudável")
        print(f"📊 Dados de saúde: {health['data']}")
    
    @pytest.mark.real
    @pytest.mark.api
    async def test_api_response_time(self, real_api_client, performance_tester):
        """Testa tempo de resposta da API"""
        measurement = await performance_tester.measure_api_call(
            "health_check",
            real_api_client.health_check()
        )
        
        assert measurement["success"], f"Health check falhou: {measurement}"
        assert measurement["duration"] < 5.0, f"Resposta muito lenta: {measurement['duration']:.2f}s"
        
        print(f"⚡ Tempo de resposta: {measurement['duration']:.3f}s")


class TestRealWebhookProcessing:
    """📱 Testes reais de processamento de webhook"""
    
    @pytest.mark.real
    @pytest.mark.webhook
    async def test_simple_message_processing(self, conversation_tester, real_test_reporter):
        """Testa processamento de mensagem simples"""
        start_time = time.time()
        
        # Enviar mensagem simples
        result = await conversation_tester.send_message("Olá, como vocês estão?")
        
        duration = time.time() - start_time
        real_test_reporter.record_test(
            "simple_message_processing",
            result["success"],
            duration,
            {"message": "Olá, como vocês estão?", "response": result}
        )
        
        assert result["success"], f"Mensagem falhou: {result.get('error')}"
        assert result["status_code"] == 200, f"Status inesperado: {result['status_code']}"
        
        print(f"✅ Mensagem processada em {duration:.2f}s")
        print(f"📱 Status: {result['status_code']}")
    
    @pytest.mark.real
    @pytest.mark.webhook
    async def test_greeting_flow(self, conversation_tester, real_test_reporter):
        """Testa fluxo de saudação inicial"""
        start_time = time.time()
        
        messages = [
            "Oi!",
            "Boa tarde",
            "Como vocês estão?"
        ]
        
        results = await conversation_tester.send_conversation_flow(messages, delay=1.0)
        
        duration = time.time() - start_time
        success_rate = conversation_tester.get_success_rate()
        
        real_test_reporter.record_test(
            "greeting_flow",
            success_rate >= 80.0,
            duration,
            {
                "messages": len(messages),
                "success_rate": success_rate,
                "results": results
            }
        )
        
        assert success_rate >= 80.0, f"Taxa de sucesso baixa: {success_rate:.1f}%"
        
        for i, result in enumerate(results):
            assert result["success"], f"Mensagem {i+1} falhou: {result.get('error')}"
        
        print(f"✅ Fluxo de saudação completo em {duration:.2f}s")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
    
    @pytest.mark.real
    @pytest.mark.webhook
    async def test_concurrent_messages(self, real_api_client, real_test_reporter):
        """Testa processamento concorrente de mensagens"""
        start_time = time.time()
        
        # Criar múltiplos telefones únicos
        phones = [f"5511999{i:06d}" for i in range(1, 6)]
        messages = [
            "Olá, teste concorrente 1",
            "Olá, teste concorrente 2", 
            "Olá, teste concorrente 3",
            "Olá, teste concorrente 4",
            "Olá, teste concorrente 5"
        ]
        
        # Enviar mensagens concorrentemente
        tasks = [
            real_api_client.send_webhook_message(phone, message)
            for phone, message in zip(phones, messages)
        ]
        
        results = await asyncio.gather(*tasks)
        
        duration = time.time() - start_time
        successful = sum(1 for r in results if r["success"])
        success_rate = (successful / len(results)) * 100
        
        real_test_reporter.record_test(
            "concurrent_messages",
            success_rate >= 80.0,
            duration,
            {
                "total_messages": len(results),
                "successful": successful,
                "success_rate": success_rate
            }
        )
        
        assert success_rate >= 80.0, f"Taxa de sucesso em concorrência baixa: {success_rate:.1f}%"
        
        print(f"✅ {successful}/{len(results)} mensagens concorrentes processadas em {duration:.2f}s")
        print(f"📊 Taxa de sucesso: {success_rate:.1f}%")


class TestRealConversationFlows:
    """💬 Testes reais de fluxos de conversa"""
    
    @pytest.mark.real
    @pytest.mark.conversation
    async def test_price_inquiry_flow(self, conversation_tester, price_inquiry_scenario, real_test_reporter):
        """Testa fluxo real de consulta de preços"""
        start_time = time.time()
        
        results = await conversation_tester.send_conversation_flow(
            price_inquiry_scenario["messages"],
            delay=2.0
        )
        
        duration = time.time() - start_time
        success_rate = conversation_tester.get_success_rate()
        
        real_test_reporter.record_test(
            "price_inquiry_flow",
            success_rate >= 80.0,
            duration,
            {
                "scenario": "price_inquiry",
                "messages": len(price_inquiry_scenario["messages"]),
                "success_rate": success_rate
            }
        )
        
        assert success_rate >= 80.0, f"Fluxo de preços falhou: {success_rate:.1f}%"
        
        print(f"✅ Fluxo de consulta de preços completo em {duration:.2f}s")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        print(f"💬 Mensagens processadas: {len(results)}")
    
    @pytest.mark.real
    @pytest.mark.conversation
    async def test_booking_attempt_flow(self, conversation_tester, booking_scenario, real_test_reporter):
        """Testa tentativa real de agendamento"""
        start_time = time.time()
        
        results = await conversation_tester.send_conversation_flow(
            booking_scenario["messages"],
            delay=2.5
        )
        
        duration = time.time() - start_time
        success_rate = conversation_tester.get_success_rate()
        
        real_test_reporter.record_test(
            "booking_attempt_flow",
            success_rate >= 80.0,
            duration,
            {
                "scenario": "booking_attempt",
                "customer": booking_scenario["customer_name"],
                "service": booking_scenario["service"],
                "messages": len(booking_scenario["messages"]),
                "success_rate": success_rate
            }
        )
        
        assert success_rate >= 80.0, f"Tentativa de agendamento falhou: {success_rate:.1f}%"
        
        print(f"✅ Tentativa de agendamento completa em {duration:.2f}s")
        print(f"👤 Cliente: {booking_scenario['customer_name']}")
        print(f"🛏️ Serviço: {booking_scenario['service']}")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
    
    @pytest.mark.real
    @pytest.mark.conversation
    async def test_complex_inquiry_flow(self, conversation_tester, complex_inquiry_scenario, real_test_reporter):
        """Testa fluxo real de consultas complexas"""
        start_time = time.time()
        
        results = await conversation_tester.send_conversation_flow(
            complex_inquiry_scenario["messages"],
            delay=1.5
        )
        
        duration = time.time() - start_time
        success_rate = conversation_tester.get_success_rate()
        
        real_test_reporter.record_test(
            "complex_inquiry_flow",
            success_rate >= 80.0,
            duration,
            {
                "scenario": "complex_inquiry",
                "questions": len(complex_inquiry_scenario["messages"]),
                "success_rate": success_rate
            }
        )
        
        assert success_rate >= 80.0, f"Consultas complexas falharam: {success_rate:.1f}%"
        
        print(f"✅ Consultas complexas completas em {duration:.2f}s")
        print(f"❓ Perguntas respondidas: {len(results)}")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")


class TestRealPerformanceValidation:
    """⚡ Testes reais de performance"""
    
    @pytest.mark.real
    @pytest.mark.performance
    async def test_response_time_under_load(self, real_api_client, performance_tester, real_test_reporter):
        """Testa tempo de resposta sob carga"""
        start_time = time.time()
        
        # Enviar 20 mensagens em sequência rápida
        phones = [f"5511888{i:05d}" for i in range(20)]
        
        measurements = []
        for i, phone in enumerate(phones):
            measurement = await performance_tester.measure_api_call(
                f"load_test_message_{i}",
                real_api_client.send_webhook_message(phone, f"Mensagem de carga {i}")
            )
            measurements.append(measurement)
            
            # Pequeno delay para não sobrecarregar
            await asyncio.sleep(0.1)
        
        duration = time.time() - start_time
        avg_response_time = performance_tester.get_average_duration()
        success_rate = performance_tester.get_success_rate()
        
        real_test_reporter.record_test(
            "response_time_under_load",
            avg_response_time < 10.0 and success_rate >= 80.0,
            duration,
            {
                "total_messages": len(measurements),
                "average_response_time": avg_response_time,
                "success_rate": success_rate,
                "total_duration": duration
            }
        )
        
        assert avg_response_time < 10.0, f"Tempo médio muito alto: {avg_response_time:.2f}s"
        assert success_rate >= 80.0, f"Taxa de sucesso baixa sob carga: {success_rate:.1f}%"
        
        print(f"⚡ Teste de carga completo em {duration:.2f}s")
        print(f"📊 Tempo médio de resposta: {avg_response_time:.3f}s")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        print(f"💪 Mensagens processadas: {len(measurements)}")
    
    @pytest.mark.real
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_sustained_conversation_performance(self, conversation_tester, real_test_reporter):
        """Testa performance em conversa sustentada"""
        start_time = time.time()
        
        # Conversa longa simulando uso real
        long_conversation = [
            "Olá, boa tarde!",
            "Gostaria de informações sobre os serviços",
            "Quanto custa um corte masculino?",
            "E barba? Vocês fazem?",
            "Qual o horário de funcionamento?",
            "Trabalham no sábado?",
            "Onde fica a barbearia?",
            "Tem estacionamento?",
            "Aceitam cartão?",
            "Preciso agendar para amanhã",
            "Que horários estão disponíveis?",
            "15h está bom?",
            "Meu nome é João da Silva",
            "Confirmo o agendamento",
            "Muito obrigado!"
        ]
        
        results = await conversation_tester.send_conversation_flow(
            long_conversation,
            delay=1.0  # 1 segundo entre mensagens
        )
        
        duration = time.time() - start_time
        success_rate = conversation_tester.get_success_rate()
        
        real_test_reporter.record_test(
            "sustained_conversation_performance",
            success_rate >= 80.0,
            duration,
            {
                "conversation_length": len(long_conversation),
                "total_duration": duration,
                "success_rate": success_rate,
                "avg_time_per_message": duration / len(long_conversation)
            }
        )
        
        assert success_rate >= 80.0, f"Conversa sustentada falhou: {success_rate:.1f}%"
        assert duration < 120.0, f"Conversa muito lenta: {duration:.1f}s"
        
        print(f"💬 Conversa sustentada completa em {duration:.1f}s")
        print(f"📊 {len(long_conversation)} mensagens processadas")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        print(f"⏱️ Tempo médio por mensagem: {duration/len(long_conversation):.2f}s")


class TestRealSystemStability:
    """🛡️ Testes reais de estabilidade do sistema"""
    
    @pytest.mark.real
    @pytest.mark.api
    async def test_invalid_input_handling(self, conversation_tester, real_test_reporter):
        """Testa tratamento de entradas inválidas"""
        start_time = time.time()
        
        invalid_inputs = [
            "",  # Mensagem vazia
            "   ",  # Apenas espaços
            "a" * 1000,  # Mensagem muito longa
            "🤖🤖🤖🤖🤖",  # Apenas emojis
            "12345",  # Apenas números
            "!@#$%^&*()",  # Apenas símbolos
            "😀😃😄😁😆",  # Múltiplos emojis
        ]
        
        results = await conversation_tester.send_conversation_flow(
            invalid_inputs,
            delay=0.5
        )
        
        duration = time.time() - start_time
        success_rate = conversation_tester.get_success_rate()
        
        real_test_reporter.record_test(
            "invalid_input_handling",
            success_rate >= 80.0,  # Sistema deve lidar com inputs inválidos
            duration,
            {
                "invalid_inputs": len(invalid_inputs),
                "success_rate": success_rate,
                "handled_gracefully": all(r["status_code"] == 200 for r in results)
            }
        )
        
        # Sistema deve responder a entradas inválidas sem crash
        for i, result in enumerate(results):
            assert result["status_code"] == 200, f"Input inválido {i} causou erro: {result}"
        
        print(f"🛡️ Tratamento de entradas inválidas testado em {duration:.2f}s")
        print(f"🧪 Inputs inválidos testados: {len(invalid_inputs)}")
        print(f"📈 Taxa de processamento: {success_rate:.1f}%")
    
    @pytest.mark.real
    @pytest.mark.api
    async def test_rapid_fire_messages(self, real_api_client, real_test_reporter):
        """Testa mensagens em rajada rápida"""
        start_time = time.time()
        
        phone = f"5511777{int(time.time())}"
        
        # Enviar 10 mensagens muito rápido
        tasks = []
        for i in range(10):
            task = real_api_client.send_webhook_message(phone, f"Mensagem rápida {i}")
            tasks.append(task)
        
        # Executar todas simultaneamente
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        duration = time.time() - start_time
        
        # Contar sucessos (incluindo tratamento de exceptions)
        successful = 0
        for result in results:
            if isinstance(result, dict) and result.get("success"):
                successful += 1
            elif isinstance(result, Exception):
                # Exception é aceitável em rajada muito rápida
                pass
        
        success_rate = (successful / len(results)) * 100
        
        real_test_reporter.record_test(
            "rapid_fire_messages",
            success_rate >= 50.0,  # Padrão mais flexível para rajada
            duration,
            {
                "total_messages": len(results),
                "successful": successful,
                "success_rate": success_rate,
                "rapid_fire_duration": duration
            }
        )
        
        # Sistema deve lidar com rajada sem crash (pelo menos 50% de sucesso)
        assert success_rate >= 50.0, f"Sistema falhou sob rajada: {success_rate:.1f}%"
        
        print(f"🔥 Teste de rajada completo em {duration:.3f}s")
        print(f"📊 {successful}/{len(results)} mensagens processadas")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "real"])

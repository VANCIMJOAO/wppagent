"""
🧪 Testes Unitários - Serviços Core
Testa componentes individuais isoladamente
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

# Import existing services
from app.services.llm_advanced import LLMAdvanced
from app.services.whatsapp import WhatsAppService
from app.services.cache_service_optimized import OptimizedCacheService
from app.services.availability_service import AvailabilityService
from app.services.business_data import BusinessDataService


class TestLLMService:
    """🤖 Testes do serviço LLM"""
    
    @pytest.mark.unit
    async def test_process_message_success(self, mock_openai):
        """Testa processamento bem-sucedido de mensagem"""
        llm_service = LLMService()
        
        result = await llm_service.process_message(
            user_id="test_user",
            message="Gostaria de agendar um corte",
            context={}
        )
        
        assert result is not None
        assert result.text == "Resposta de teste do assistente"
        assert result.confidence > 0
        mock_openai.chat.completions.create.assert_called_once()
    
    @pytest.mark.unit
    async def test_process_message_with_context(self, mock_openai):
        """Testa processamento com contexto"""
        llm_service = LLMService()
        
        context = {
            "user_name": "João",
            "last_service": "Corte",
            "conversation_history": ["Olá", "Como está?"]
        }
        
        result = await llm_service.process_message(
            user_id="test_user",
            message="Quero remarcar",
            context=context
        )
        
        assert result is not None
        # Verificar se contexto foi incluído na chamada
        call_args = mock_openai.chat.completions.create.call_args
        assert "João" in str(call_args)
    
    @pytest.mark.unit
    async def test_extract_intent_appointment(self, mock_openai):
        """Testa extração de intenção de agendamento"""
        llm_service = LLMService()
        
        # Configurar resposta específica para intenção
        mock_openai.chat.completions.create.return_value.choices[0].message.content = '{"intent": "agendar", "confidence": 0.95}'
        
        intent = await llm_service.extract_intent("Quero agendar um horário para amanhã")
        
        assert intent["intent"] == "agendar"
        assert intent["confidence"] >= 0.9
    
    @pytest.mark.unit
    @pytest.mark.performance
    async def test_response_time_under_limit(self, mock_openai, performance_monitor):
        """Testa se tempo de resposta está dentro do limite"""
        llm_service = LLMService()
        
        performance_monitor.start("llm_processing")
        
        await llm_service.process_message(
            user_id="test_user",
            message="Teste de performance",
            context={}
        )
        
        duration = performance_monitor.end("llm_processing")
        
        # Deve responder em menos de 5 segundos
        performance_monitor.assert_performance("llm_processing", 5.0)
    
    @pytest.mark.unit
    async def test_error_handling_openai_failure(self):
        """Testa tratamento de erro quando OpenAI falha"""
        with patch("app.services.llm_service.openai") as mock_openai:
            mock_openai.chat.completions.create.side_effect = Exception("API Error")
            
            llm_service = LLMService()
            
            result = await llm_service.process_message(
                user_id="test_user",
                message="Teste de erro",
                context={}
            )
            
            # Deve retornar resposta de fallback
            assert result is not None
            assert "erro" in result.text.lower()


class TestWhatsAppService:
    """📱 Testes do serviço WhatsApp"""
    
    @pytest.mark.unit
    async def test_send_message_success(self, mock_meta_api):
        """Testa envio bem-sucedido de mensagem"""
        whatsapp_service = WhatsAppService()
        
        result = await whatsapp_service.send_message(
            phone="5511999999999",
            message="Mensagem de teste"
        )
        
        assert result["success"] is True
        assert "test_message_id" in result["message_id"]
        mock_meta_api.post.assert_called_once()
    
    @pytest.mark.unit
    async def test_send_interactive_message(self, mock_meta_api):
        """Testa envio de mensagem interativa"""
        whatsapp_service = WhatsAppService()
        
        buttons = [
            {"id": "btn1", "title": "Agendar"},
            {"id": "btn2", "title": "Cancelar"}
        ]
        
        result = await whatsapp_service.send_interactive_message(
            phone="5511999999999",
            text="Escolha uma opção:",
            buttons=buttons
        )
        
        assert result["success"] is True
        
        # Verificar payload da chamada
        call_args = mock_meta_api.post.call_args
        payload = call_args[1]["json"]
        assert payload["type"] == "interactive"
        assert len(payload["interactive"]["action"]["buttons"]) == 2
    
    @pytest.mark.unit
    async def test_validate_webhook_signature(self):
        """Testa validação de assinatura do webhook"""
        whatsapp_service = WhatsAppService()
        
        # Teste com assinatura válida
        valid_signature = whatsapp_service.generate_signature("test_payload")
        assert whatsapp_service.validate_signature("test_payload", valid_signature)
        
        # Teste com assinatura inválida
        assert not whatsapp_service.validate_signature("test_payload", "invalid_signature")
    
    @pytest.mark.unit
    @pytest.mark.meta_api
    async def test_rate_limiting_meta_api(self, mock_meta_api):
        """Testa rate limiting da API do Meta"""
        whatsapp_service = WhatsAppService()
        
        # Simular múltiplas chamadas
        tasks = []
        for i in range(20):
            task = whatsapp_service.send_message(
                phone=f"55119999999{i:02d}",
                message=f"Mensagem {i}"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verificar se rate limiting foi aplicado
        successful_calls = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        assert successful_calls <= 10  # Limite configurado


class TestAppointmentService:
    """📅 Testes do serviço de agendamento"""
    
    @pytest.mark.unit
    async def test_create_appointment_success(self, test_db_session, setup_test_data):
        """Testa criação bem-sucedida de agendamento"""
        appointment_service = AppointmentService(test_db_session)
        test_data = setup_test_data
        
        appointment_data = {
            "user_id": test_data["user"].id,
            "service_id": test_data["services"][0].id,
            "appointment_date": datetime.now() + timedelta(days=1),
            "notes": "Teste de agendamento"
        }
        
        appointment = await appointment_service.create_appointment(appointment_data)
        
        assert appointment is not None
        assert appointment.user_id == test_data["user"].id
        assert appointment.service_id == test_data["services"][0].id
        assert appointment.status == "scheduled"
    
    @pytest.mark.unit
    async def test_check_availability_conflict(self, test_db_session, setup_test_data):
        """Testa verificação de conflito de horário"""
        appointment_service = AppointmentService(test_db_session)
        test_data = setup_test_data
        
        # Criar primeiro agendamento
        appointment_time = datetime.now() + timedelta(days=1)
        appointment_time = appointment_time.replace(hour=14, minute=0, second=0, microsecond=0)
        
        await appointment_service.create_appointment({
            "user_id": test_data["user"].id,
            "service_id": test_data["services"][0].id,
            "appointment_date": appointment_time,
        })
        
        # Tentar agendar no mesmo horário
        availability = await appointment_service.check_availability(
            service_id=test_data["services"][0].id,
            appointment_date=appointment_time
        )
        
        assert availability is False
    
    @pytest.mark.unit
    async def test_cancel_appointment(self, test_db_session, setup_test_data):
        """Testa cancelamento de agendamento"""
        appointment_service = AppointmentService(test_db_session)
        test_data = setup_test_data
        
        # Criar agendamento
        appointment = await appointment_service.create_appointment({
            "user_id": test_data["user"].id,
            "service_id": test_data["services"][0].id,
            "appointment_date": datetime.now() + timedelta(days=1),
        })
        
        # Cancelar agendamento
        result = await appointment_service.cancel_appointment(appointment.id)
        
        assert result is True
        
        # Verificar status
        updated_appointment = await appointment_service.get_appointment(appointment.id)
        assert updated_appointment.status == "cancelled"


class TestCacheService:
    """💾 Testes do serviço de cache"""
    
    @pytest.mark.unit
    async def test_set_and_get_value(self, test_redis):
        """Testa set e get de valores no cache"""
        cache_service = CacheService(test_redis)
        
        await cache_service.set("test_key", "test_value", ttl=60)
        
        value = await cache_service.get("test_key")
        assert value == "test_value"
    
    @pytest.mark.unit
    async def test_cache_expiration(self, test_redis):
        """Testa expiração do cache"""
        cache_service = CacheService(test_redis)
        
        await cache_service.set("expire_key", "expire_value", ttl=1)
        
        # Aguardar expiração
        await asyncio.sleep(1.1)
        
        value = await cache_service.get("expire_key")
        assert value is None
    
    @pytest.mark.unit
    async def test_cache_json_serialization(self, test_redis):
        """Testa serialização JSON no cache"""
        cache_service = CacheService(test_redis)
        
        test_data = {
            "user_id": 123,
            "preferences": ["option1", "option2"],
            "settings": {"theme": "dark"}
        }
        
        await cache_service.set_json("json_key", test_data)
        
        retrieved_data = await cache_service.get_json("json_key")
        assert retrieved_data == test_data
    
    @pytest.mark.unit
    async def test_cache_bulk_operations(self, test_redis):
        """Testa operações em lote no cache"""
        cache_service = CacheService(test_redis)
        
        data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        
        await cache_service.set_multiple(data, ttl=60)
        
        values = await cache_service.get_multiple(["key1", "key2", "key3"])
        assert values == ["value1", "value2", "value3"]


class TestValidators:
    """✅ Testes dos validadores"""
    
    @pytest.mark.unit
    def test_phone_validator_valid_numbers(self):
        """Testa validação de números válidos"""
        validator = PhoneValidator()
        
        valid_phones = [
            "5511999999999",
            "+5511999999999",
            "11999999999",
            "+55 11 99999-9999"
        ]
        
        for phone in valid_phones:
            assert validator.is_valid(phone), f"Phone {phone} should be valid"
    
    @pytest.mark.unit
    def test_phone_validator_invalid_numbers(self):
        """Testa validação de números inválidos"""
        validator = PhoneValidator()
        
        invalid_phones = [
            "123",
            "abcdefghijk",
            "+5511888888888888888",  # Muito longo
            ""
        ]
        
        for phone in invalid_phones:
            assert not validator.is_valid(phone), f"Phone {phone} should be invalid"
    
    @pytest.mark.unit
    def test_message_validator_content_filtering(self):
        """Testa filtragem de conteúdo de mensagens"""
        validator = MessageValidator()
        
        # Mensagens válidas
        valid_messages = [
            "Olá, gostaria de agendar um horário",
            "Qual o preço do corte?",
            "Obrigado pelo atendimento!"
        ]
        
        for message in valid_messages:
            assert validator.is_safe(message), f"Message should be safe: {message}"
        
        # Mensagens suspeitas
        suspicious_messages = [
            "CLIQUE AQUI PARA GANHAR DINHEIRO FÁCIL!!!",
            "Você ganhou um prêmio! Informe seus dados bancários",
            "javascript:alert('xss')"
        ]
        
        for message in suspicious_messages:
            assert not validator.is_safe(message), f"Message should be flagged as unsafe: {message}"
    
    @pytest.mark.unit
    def test_message_validator_length_limits(self):
        """Testa limites de tamanho de mensagem"""
        validator = MessageValidator()
        
        # Mensagem muito longa
        long_message = "a" * 5000
        assert not validator.is_valid_length(long_message)
        
        # Mensagem vazia
        assert not validator.is_valid_length("")
        
        # Mensagem de tamanho adequado
        assert validator.is_valid_length("Mensagem de teste com tamanho adequado")


class TestErrorHandling:
    """🚨 Testes de tratamento de erros"""
    
    @pytest.mark.unit
    async def test_database_connection_failure(self):
        """Testa tratamento de falha de conexão com banco"""
        with patch("app.database.create_async_engine") as mock_engine:
            mock_engine.side_effect = Exception("Database connection failed")
            
            # Importar aqui para forçar erro na conexão
            from app.services.appointment_service import AppointmentService
            
            with pytest.raises(Exception):
                service = AppointmentService()
                await service.get_appointment(1)
    
    @pytest.mark.unit
    async def test_redis_connection_failure(self, mock_cache):
        """Testa fallback quando Redis falha"""
        # Simular falha do Redis
        mock_cache.get.side_effect = Exception("Redis connection failed")
        
        from app.services.cache_service import CacheService
        cache_service = CacheService()
        
        # Deve funcionar com fallback (memória)
        await cache_service.set("test_key", "test_value")
        value = await cache_service.get("test_key")
        
        assert value == "test_value"  # Fallback deve funcionar
    
    @pytest.mark.unit
    async def test_rate_limit_exceeded(self):
        """Testa comportamento quando rate limit é excedido"""
        from app.middleware.rate_limit import RateLimitMiddleware
        
        middleware = RateLimitMiddleware()
        
        # Simular múltiplas requisições do mesmo IP
        for _ in range(100):  # Acima do limite
            result = await middleware.check_rate_limit("192.168.1.1")
        
        # Última deve ser rejeitada
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

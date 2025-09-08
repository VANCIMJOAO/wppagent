"""
🧪 TESTES UNITÁRIOS - SISTEMA UNIFICADO DE CONTROLE DE RESPOSTA
==============================================================

Testes abrangentes para validar o novo sistema unificado que substitui
os controles sobrepostos redundantes.

CENÁRIOS TESTADOS:
- ✅ Processamento de mensagem única
- ✅ Detecção de mensagens duplicadas
- ✅ Fallback Redis -> Memory cache
- ✅ TTL automático
- ✅ Hash determinístico
- ✅ Estatísticas e métricas
- ✅ Limpeza de cache
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

from app.services.response_control import UnifiedResponseControl, ResponseControlStats


class TestUnifiedResponseControl:
    """Testes para o sistema unificado de controle de resposta"""
    
    @pytest.fixture
    async def control_instance(self):
        """Fixture para instância de controle de teste"""
        control = UnifiedResponseControl(window_seconds=2)  # TTL curto para testes
        # Limpar cache antes de cada teste
        await control.clear_cache()
        return control
    
    @pytest.fixture
    def sample_message(self):
        """Mensagem de exemplo para testes"""
        return {
            "user_id": "5511999887766",
            "content": "Olá, preciso de ajuda com meu pedido"
        }
    
    def test_message_hash_generation(self, control_instance):
        """Testa geração de hash determinístico"""
        content1 = "Olá mundo"
        content2 = "  olá mundo  "  # Com espaços
        content3 = "OLÁ MUNDO"      # Maiúsculo
        content4 = "Tchau mundo"    # Diferente
        
        hash1 = control_instance.generate_message_hash(content1)
        hash2 = control_instance.generate_message_hash(content2)
        hash3 = control_instance.generate_message_hash(content3)
        hash4 = control_instance.generate_message_hash(content4)
        
        # Conteúdo similar deve gerar mesmo hash
        assert hash1 == hash2 == hash3
        # Conteúdo diferente deve gerar hash diferente
        assert hash1 != hash4
        # Hash deve ter 12 caracteres
        assert len(hash1) == 12
        assert isinstance(hash1, str)
    
    @pytest.mark.asyncio
    async def test_first_message_allowed(self, control_instance, sample_message):
        """Testa que primeira mensagem é sempre permitida"""
        can_process, reason = await control_instance.can_process_message(
            sample_message["user_id"], 
            sample_message["content"]
        )
        
        assert can_process is True
        assert "primeira vez" in reason.lower()
        assert control_instance.stats.messages_allowed == 1
        assert control_instance.stats.messages_blocked == 0
    
    @pytest.mark.asyncio
    async def test_duplicate_message_blocked(self, control_instance, sample_message):
        """Testa que mensagem duplicada é bloqueada"""
        user_id = sample_message["user_id"]
        content = sample_message["content"]
        
        # Primeira mensagem - deve passar
        can_process1, reason1 = await control_instance.can_process_message(user_id, content)
        assert can_process1 is True
        
        # Segunda mensagem idêntica - deve ser bloqueada
        can_process2, reason2 = await control_instance.can_process_message(user_id, content)
        assert can_process2 is False
        assert "duplicada" in reason2.lower()
        
        assert control_instance.stats.messages_allowed == 1
        assert control_instance.stats.messages_blocked == 1
        assert control_instance.stats.duplicates_prevented == 1
    
    @pytest.mark.asyncio
    async def test_different_users_allowed(self, control_instance):
        """Testa que usuários diferentes podem enviar mensagens iguais"""
        content = "Mesma mensagem"
        user1 = "5511111111111"
        user2 = "5511222222222"
        
        can_process1, _ = await control_instance.can_process_message(user1, content)
        can_process2, _ = await control_instance.can_process_message(user2, content)
        
        assert can_process1 is True
        assert can_process2 is True
        assert control_instance.stats.messages_allowed == 2
        assert control_instance.stats.messages_blocked == 0
    
    @pytest.mark.asyncio
    async def test_different_messages_allowed(self, control_instance, sample_message):
        """Testa que mensagens diferentes do mesmo usuário são permitidas"""
        user_id = sample_message["user_id"]
        
        can_process1, _ = await control_instance.can_process_message(user_id, "Primeira mensagem")
        can_process2, _ = await control_instance.can_process_message(user_id, "Segunda mensagem")
        
        assert can_process1 is True
        assert can_process2 is True
        assert control_instance.stats.messages_allowed == 2
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self, control_instance, sample_message):
        """Testa que mensagem é permitida novamente após TTL expirar"""
        user_id = sample_message["user_id"]
        content = sample_message["content"]
        
        # Primeira mensagem
        can_process1, _ = await control_instance.can_process_message(user_id, content)
        assert can_process1 is True
        
        # Segunda mensagem imediata - bloqueada
        can_process2, _ = await control_instance.can_process_message(user_id, content)
        assert can_process2 is False
        
        # Aguardar TTL expirar (2 segundos no teste)
        await asyncio.sleep(2.1)
        
        # Terceira mensagem após TTL - deve ser permitida
        can_process3, _ = await control_instance.can_process_message(user_id, content)
        assert can_process3 is True
        
        assert control_instance.stats.messages_allowed == 2
        assert control_instance.stats.messages_blocked == 1
    
    @pytest.mark.asyncio
    async def test_redis_fallback_to_memory(self, control_instance, sample_message):
        """Testa fallback do Redis para cache em memória"""
        # Simular Redis indisponível
        control_instance.redis_client = None
        
        user_id = sample_message["user_id"]
        content = sample_message["content"]
        
        # Primeira mensagem - deve usar cache em memória
        can_process1, reason1 = await control_instance.can_process_message(user_id, content)
        assert can_process1 is True
        assert "memory" in reason1.lower()
        
        # Segunda mensagem - deve ser bloqueada via cache em memória
        can_process2, reason2 = await control_instance.can_process_message(user_id, content)
        assert can_process2 is False
        
        assert control_instance.stats.fallback_operations >= 2
        assert control_instance.stats.redis_operations == 0
    
    @pytest.mark.asyncio
    async def test_stats_calculation(self, control_instance, sample_message):
        """Testa cálculo correto das estatísticas"""
        user_id = sample_message["user_id"]
        
        # Processar algumas mensagens
        await control_instance.can_process_message(user_id, "Mensagem 1")  # Permitida
        await control_instance.can_process_message(user_id, "Mensagem 1")  # Bloqueada (duplicata)
        await control_instance.can_process_message(user_id, "Mensagem 2")  # Permitida
        
        stats = await control_instance.get_stats()
        
        assert stats["messages_processed"] == 3
        assert stats["messages_allowed"] == 2
        assert stats["messages_blocked"] == 1
        assert stats["duplicates_prevented"] == 1
        assert stats["allowed_percentage"] == 66.67
        assert stats["blocked_percentage"] == 33.33
        assert stats["window_seconds"] == 2
        assert "last_reset" in stats
    
    @pytest.mark.asyncio
    async def test_cache_clearing(self, control_instance, sample_message):
        """Testa limpeza do cache"""
        user_id = sample_message["user_id"]
        content = sample_message["content"]
        
        # Adicionar entrada no cache
        await control_instance.can_process_message(user_id, content)
        
        # Verificar que cache tem dados
        stats_before = await control_instance.get_stats()
        assert stats_before["memory_cache_size"] > 0 or control_instance.redis_client is not None
        
        # Limpar cache
        clear_result = await control_instance.clear_cache()
        assert clear_result["status"] == "success"
        
        # Verificar que cache foi limpo
        stats_after = await control_instance.get_stats()
        assert stats_after["memory_cache_size"] == 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, control_instance):
        """Testa tratamento de erros"""
        # Simular erro no Redis
        with patch.object(control_instance, '_can_process_redis', side_effect=Exception("Redis error")):
            can_process, reason = await control_instance.can_process_message("123", "test")
            
            # Deve permitir em caso de erro para evitar bloqueio total
            assert can_process is True
            assert "erro" in reason.lower()
            assert control_instance.stats.errors > 0
    
    def test_stats_reset(self, control_instance):
        """Testa reset automático das estatísticas"""
        # Simular estatísticas antigas
        control_instance.stats.last_reset = time.time() - 7200  # 2 horas atrás
        control_instance.stats.messages_processed = 100
        
        # Trigger reset
        control_instance.stats.reset_if_needed()
        
        # Verificar reset
        assert control_instance.stats.messages_processed == 0
        assert time.time() - control_instance.stats.last_reset < 60  # Reset recente


class TestResponseControlStats:
    """Testes para a classe de estatísticas"""
    
    def test_stats_initialization(self):
        """Testa inicialização das estatísticas"""
        stats = ResponseControlStats()
        
        assert stats.messages_processed == 0
        assert stats.messages_blocked == 0
        assert stats.messages_allowed == 0
        assert stats.duplicates_prevented == 0
        assert stats.redis_operations == 0
        assert stats.fallback_operations == 0
        assert stats.errors == 0
        assert isinstance(stats.last_reset, float)
    
    def test_stats_reset_logic(self):
        """Testa lógica de reset das estatísticas"""
        stats = ResponseControlStats()
        stats.messages_processed = 50
        stats.last_reset = time.time() - 7200  # 2 horas atrás
        
        # Deve resetar
        stats.reset_if_needed()
        assert stats.messages_processed == 0
        
        # Não deve resetar se recente
        stats.messages_processed = 10
        stats.reset_if_needed()
        assert stats.messages_processed == 10


@pytest.mark.integration
class TestUnifiedResponseControlIntegration:
    """Testes de integração com Redis real (se disponível)"""
    
    @pytest.mark.asyncio
    async def test_redis_integration(self):
        """Testa integração com Redis real"""
        control = UnifiedResponseControl(window_seconds=1)
        
        if not control.redis_client:
            pytest.skip("Redis não disponível para teste de integração")
        
        user_id = "test_integration"
        content = "Mensagem de teste de integração"
        
        try:
            # Limpar qualquer estado anterior
            await control.clear_cache()
            
            # Teste básico de processamento
            can_process1, _ = await control.can_process_message(user_id, content)
            assert can_process1 is True
            
            can_process2, _ = await control.can_process_message(user_id, content)
            assert can_process2 is False
            
            # Aguardar TTL
            await asyncio.sleep(1.1)
            
            can_process3, _ = await control.can_process_message(user_id, content)
            assert can_process3 is True
            
        finally:
            # Limpar após teste
            await control.clear_cache()


if __name__ == "__main__":
    # Executar testes básicos
    pytest.main([__file__, "-v"])

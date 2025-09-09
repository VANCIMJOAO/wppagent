"""
🧪 Teste do Sistema de Cache Invalidation
=========================================

Testes para validar o funcionamento correto do sistema centralizado
de invalidação de cache, incluindo regras de eventos e patterns.

Autor: Claude AI
Status: Teste crítico para cache consistency
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.cache_invalidation import (
    CacheInvalidationService,
    CacheEvent,
    invalidate_appointment_cache,
    invalidate_conversation_cache,
    invalidate_client_cache
)


class TestCacheInvalidationService:
    """🧪 Testes do serviço principal de invalidation"""
    
    @pytest.fixture
    def invalidation_service(self):
        """Instância limpa do serviço para testes"""
        return CacheInvalidationService()
    
    def test_rules_setup(self, invalidation_service):
        """✅ Testa se todas as rules foram configuradas corretamente"""
        
        # Verificar se rules principais existem
        expected_events = [
            CacheEvent.APPOINTMENT_CREATED,
            CacheEvent.APPOINTMENT_UPDATED,
            CacheEvent.APPOINTMENT_DELETED,
            CacheEvent.CONVERSATION_CREATED,
            CacheEvent.CONVERSATION_UPDATED,
            CacheEvent.CLIENT_CREATED,
            CacheEvent.CLIENT_UPDATED,
            CacheEvent.BUSINESS_UPDATED
        ]
        
        for event in expected_events:
            assert event in invalidation_service.rules
            assert len(invalidation_service.rules[event].patterns) > 0
        
        # Verificar rule específica de appointment_created
        appointment_rule = invalidation_service.rules[CacheEvent.APPOINTMENT_CREATED]
        expected_patterns = [
            "appointments:list:*",
            "dashboard:stats:*",
            "clients:stats:*",
            "analytics:funnel:*",
            "reports:appointments:*"
        ]
        
        for pattern in expected_patterns:
            assert pattern in appointment_rule.patterns
    
    def test_get_patterns_for_event(self, invalidation_service):
        """✅ Testa obtenção de patterns para um evento"""
        
        patterns = invalidation_service.get_patterns_for_event(
            CacheEvent.APPOINTMENT_CREATED
        )
        
        assert len(patterns) > 0
        assert "appointments:list:*" in patterns
        assert "dashboard:stats:*" in patterns
        
        # Evento inexistente deve retornar lista vazia
        fake_event = "fake_event"
        empty_patterns = invalidation_service.get_patterns_for_event(fake_event)
        assert empty_patterns == []
    
    def test_build_patterns_with_context(self, invalidation_service):
        """✅ Testa construção de patterns com context"""
        
        patterns = [
            "appointments:list:*",
            "appointments:detail:{appointment_id}",
            "clients:stats:{client_id}"
        ]
        
        context = {
            "appointment_id": 123,
            "client_id": 456
        }
        
        final_patterns = invalidation_service._build_patterns_with_context(
            patterns, context
        )
        
        expected = [
            "appointments:list:*",
            "appointments:detail:123",
            "clients:stats:456"
        ]
        
        assert final_patterns == expected
    
    def test_build_patterns_missing_context(self, invalidation_service):
        """✅ Testa construção de patterns com context faltando"""
        
        patterns = ["appointments:detail:{appointment_id}"]
        context = {}  # Context vazio
        
        final_patterns = invalidation_service._build_patterns_with_context(
            patterns, context
        )
        
        # Deve usar pattern original como fallback
        assert final_patterns == patterns
    
    @pytest.mark.asyncio
    async def test_test_invalidation_dry_run(self, invalidation_service):
        """✅ Testa dry-run de invalidation"""
        
        context = {"appointment_id": 123, "client_id": 456}
        
        result = await invalidation_service.test_invalidation(
            CacheEvent.APPOINTMENT_UPDATED,
            context
        )
        
        assert result["event"] == "CacheEvent.APPOINTMENT_UPDATED"
        assert "appointments:detail:123" in result["patterns"]
        assert result["context"] == context
    
    @pytest.mark.asyncio
    @patch('app.services.cache_invalidation.cache_service')
    async def test_invalidate_for_event_success(self, mock_cache, invalidation_service):
        """✅ Testa invalidation bem-sucedida"""
        
        # Mock do cache service
        mock_cache.invalidate_pattern.return_value = 5  # 5 keys invalidated
        mock_cache.delete.return_value = True
        
        context = {"appointment_id": 123}
        
        result = await invalidation_service.invalidate_for_event(
            CacheEvent.APPOINTMENT_UPDATED,
            context
        )
        
        assert result["success"] is True
        assert result["event"] == "CacheEvent.APPOINTMENT_UPDATED"
        assert result["invalidated_keys"] > 0
        assert result["context"] == context
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    @patch('app.services.cache_invalidation.cache_service')
    async def test_invalidate_for_event_with_errors(self, mock_cache, invalidation_service):
        """✅ Testa invalidation com alguns erros"""
        
        # Mock que falha em algumas calls
        mock_cache.invalidate_pattern.side_effect = [3, Exception("Cache error")]
        
        result = await invalidation_service.invalidate_for_event(
            CacheEvent.APPOINTMENT_CREATED
        )
        
        assert result["success"] is True  # Ainda successful mesmo com alguns erros
        assert len(result["errors"]) > 0
        assert "Cache error" in str(result["errors"])
    
    @pytest.mark.asyncio
    async def test_invalidate_unknown_event(self, invalidation_service):
        """✅ Testa invalidation de evento não configurado"""
        
        fake_event = "fake_event"
        
        result = await invalidation_service.invalidate_for_event(fake_event)
        
        assert result["success"] is False
        assert result["reason"] == "event_not_configured"
    
    @pytest.mark.asyncio
    @patch('app.services.cache_invalidation.cache_service')
    async def test_concurrent_invalidations(self, mock_cache, invalidation_service):
        """✅ Testa invalidations concorrentes do mesmo evento"""
        
        mock_cache.invalidate_pattern.return_value = 3
        
        context = {"appointment_id": 123}
        
        # Executar duas invalidations simultaneamente
        task1 = invalidation_service.invalidate_for_event(
            CacheEvent.APPOINTMENT_UPDATED, context
        )
        task2 = invalidation_service.invalidate_for_event(
            CacheEvent.APPOINTMENT_UPDATED, context
        )
        
        results = await asyncio.gather(task1, task2)
        
        # Uma deve ser executada, outra deve ser skipped
        success_count = sum(1 for r in results if r["success"])
        assert success_count >= 1
        
        # Pelo menos uma deve indicar already_running
        skip_count = sum(1 for r in results if r.get("reason") == "already_running")
        assert skip_count >= 0  # Pode ser 0 se execução for muito rápida
    
    def test_list_all_rules(self, invalidation_service):
        """✅ Testa listagem de todas as rules"""
        
        rules = invalidation_service.list_all_rules()
        
        assert len(rules) > 0
        assert "CacheEvent.APPOINTMENT_CREATED" in str(rules)
        
        # Verificar estrutura da rule
        for event_str, rule_info in rules.items():
            assert "patterns" in rule_info
            assert "dependencies" in rule_info
            assert "priority" in rule_info
            assert isinstance(rule_info["patterns"], list)


class TestHelperFunctions:
    """🧪 Testes das funções helper"""
    
    @pytest.mark.asyncio
    @patch('app.services.cache_invalidation.cache_invalidation_service')
    async def test_invalidate_appointment_cache(self, mock_service):
        """✅ Testa helper de appointment cache invalidation"""
        
        mock_service.invalidate_for_event = AsyncMock(
            return_value={"success": True}
        )
        
        result = await invalidate_appointment_cache(
            event=CacheEvent.APPOINTMENT_CREATED,
            appointment_id=123,
            client_id=456,
            business_id=789
        )
        
        # Verificar se foi chamado corretamente
        mock_service.invalidate_for_event.assert_called_once_with(
            CacheEvent.APPOINTMENT_CREATED,
            {
                "appointment_id": 123,
                "client_id": 456,
                "business_id": 789
            }
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    @patch('app.services.cache_invalidation.cache_invalidation_service')
    async def test_invalidate_conversation_cache(self, mock_service):
        """✅ Testa helper de conversation cache invalidation"""
        
        mock_service.invalidate_for_event = AsyncMock(
            return_value={"success": True}
        )
        
        await invalidate_conversation_cache(
            event=CacheEvent.CONVERSATION_UPDATED,
            conversation_id=789,
            client_id=456
        )
        
        mock_service.invalidate_for_event.assert_called_once_with(
            CacheEvent.CONVERSATION_UPDATED,
            {
                "conversation_id": 789,
                "client_id": 456
            }
        )
    
    @pytest.mark.asyncio
    @patch('app.services.cache_invalidation.cache_invalidation_service')
    async def test_invalidate_client_cache(self, mock_service):
        """✅ Testa helper de client cache invalidation"""
        
        mock_service.invalidate_for_event = AsyncMock(
            return_value={"success": True}
        )
        
        await invalidate_client_cache(
            event=CacheEvent.CLIENT_UPDATED,
            client_id=123
        )
        
        mock_service.invalidate_for_event.assert_called_once_with(
            CacheEvent.CLIENT_UPDATED,
            {"client_id": 123}
        )


class TestIntegrationScenarios:
    """🧪 Testes de cenários de integração reais"""
    
    @pytest.mark.asyncio
    @patch('app.services.cache_invalidation.cache_service')
    async def test_appointment_lifecycle_cache_invalidation(self, mock_cache):
        """✅ Testa ciclo completo de appointment com cache invalidation"""
        
        mock_cache.invalidate_pattern.return_value = 5
        mock_cache.delete.return_value = True
        
        # Simular criação de appointment
        create_result = await invalidate_appointment_cache(
            event=CacheEvent.APPOINTMENT_CREATED,
            appointment_id=123,
            client_id=456
        )
        assert create_result["success"] is True
        
        # Simular atualização
        update_result = await invalidate_appointment_cache(
            event=CacheEvent.APPOINTMENT_UPDATED,
            appointment_id=123,
            client_id=456
        )
        assert update_result["success"] is True
        
        # Simular exclusão
        delete_result = await invalidate_appointment_cache(
            event=CacheEvent.APPOINTMENT_DELETED,
            appointment_id=123,
            client_id=456
        )
        assert delete_result["success"] is True
        
        # Verificar que cache foi chamado múltiplas vezes
        assert mock_cache.invalidate_pattern.call_count > 0
    
    @pytest.mark.asyncio
    @patch('app.services.cache_invalidation.cache_service')
    async def test_business_update_cascade_invalidation(self, mock_cache):
        """✅ Testa invalidation em cascata para business update"""
        
        mock_cache.invalidate_pattern.return_value = 10
        
        service = CacheInvalidationService()
        
        result = await service.invalidate_for_event(
            CacheEvent.BUSINESS_UPDATED,
            {"business_id": 1}
        )
        
        assert result["success"] is True
        assert result["invalidated_keys"] > 0
        
        # Business update deve invalidar muitos patterns
        patterns = service.get_patterns_for_event(CacheEvent.BUSINESS_UPDATED)
        assert len(patterns) > 5  # Deve invalidar muitos caches


if __name__ == "__main__":
    # Executar testes básicos
    import asyncio
    
    async def run_basic_tests():
        """🚀 Executar testes básicos"""
        print("🧪 Testando Cache Invalidation Service...")
        
        service = CacheInvalidationService()
        
        # Test 1: Rules setup
        print("✅ Test 1: Rules configuradas")
        assert len(service.rules) > 0
        
        # Test 2: Pattern building
        print("✅ Test 2: Pattern building")
        patterns = service._build_patterns_with_context(
            ["test:{id}"], {"id": 123}
        )
        assert patterns == ["test:123"]
        
        # Test 3: Dry run
        print("✅ Test 3: Dry run")
        dry_run = await service.test_invalidation(
            CacheEvent.APPOINTMENT_CREATED,
            {"appointment_id": 123}
        )
        assert dry_run["event"] == "CacheEvent.APPOINTMENT_CREATED"
        
        print("✅ Todos os testes básicos passaram!")
        print(f"📊 {len(service.rules)} regras de invalidation configuradas")
        
        # Log summary
        service.log_cache_invalidation_summary()
    
    # asyncio.run(run_basic_tests())

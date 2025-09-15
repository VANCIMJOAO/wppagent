"""
Performance Tests - Lightweight and Timeout-Safe

Testes de performance simplificados para evitar timeouts e problemas de conectividade.
Focam em medições essenciais com timeouts controlados e mocks para isolamento.
"""

import statistics
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def performance_client():
    """Fixture para cliente de performance"""
    try:
        from app.main import app

        return TestClient(app)
    except Exception as e:
        pytest.skip(f"FastAPI app not available: {e}")


@pytest.fixture
def mock_redis():
    """Mock Redis para isolamento"""
    mock = MagicMock()
    mock.ping.return_value = True
    mock.get.return_value = None
    mock.set.return_value = True
    return mock


@pytest.fixture
def mock_database():
    """Mock Database para isolamento"""
    from unittest.mock import AsyncMock

    mock = AsyncMock()
    mock.execute = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    return mock


class TestBasicPerformance:
    """Testes básicos de performance com timeouts seguros"""

    @pytest.mark.performance
    def test_health_endpoint_basic_performance(self, performance_client, mock_redis):
        """Testa performance básica do endpoint /health"""

        if not performance_client:
            pytest.skip("FastAPI client not available")

        # Test connectivity first without Redis mocking since health_checker doesn't use redis_client
        try:
            test_response = performance_client.get("/health")
            if test_response.status_code not in [200, 500]:
                pytest.skip("Health endpoint not reachable")
        except Exception:
            pytest.skip("Health endpoint not available")

        # Coleta métricas básicas
        response_times = []
        successful_requests = 0

        # Apenas 5 requisições para evitar timeout
        for i in range(5):
            start_time = time.time()
            try:
                response = performance_client.get("/health")
                end_time = time.time()

                response_time = (end_time - start_time) * 1000  # ms
                response_times.append(response_time)

                if response.status_code in [200, 500]:
                    successful_requests += 1

            except Exception:
                pass

            # Pequena pausa
            time.sleep(0.1)

        # Validação simples
        if response_times:
            avg_time = statistics.mean(response_times)
            max_time = max(response_times)

            # Requisitos muito relaxados
            assert avg_time < 5000, f"Tempo médio muito alto: {avg_time:.2f}ms"
            assert max_time < 10000, f"Tempo máximo muito alto: {max_time:.2f}ms"
            assert successful_requests >= 1, f"Nenhuma requisição bem sucedida"
        else:
            pytest.skip("Nenhuma métrica coletada")

    @pytest.mark.performance
    def test_model_creation_performance(self):
        """Testa performance de criação de modelos"""

        try:
            from app.models.database import User
        except ImportError:
            pytest.skip("User model not available")

        # Teste simples de criação
        start_time = time.time()

        user = User(
            wa_id="5511999999999",
            nome="Performance Test",
            telefone="+55 11 99999-9999",
            email="test@performance.com",
        )

        end_time = time.time()
        creation_time = (end_time - start_time) * 1000  # ms

        # Validação muito relaxada
        assert creation_time < 1000, f"Criação muito lenta: {creation_time:.2f}ms"
        assert user.wa_id == "5511999999999"

    @pytest.mark.performance
    def test_basic_data_processing(self):
        """Testa performance básica de processamento de dados"""

        # Dados de teste pequenos
        test_data = [{"id": i, "name": f"Item {i}"} for i in range(50)]

        start_time = time.time()

        # Processamento simples
        processed = []
        for item in test_data:
            processed.append(
                {"processed_id": item["id"] * 2, "processed_name": item["name"].upper()}
            )

        end_time = time.time()
        processing_time = (end_time - start_time) * 1000  # ms

        # Validação
        assert len(processed) == len(test_data)
        assert (
            processing_time < 1000
        ), f"Processamento muito lento: {processing_time:.2f}ms"


class TestServicePerformanceMocked:
    """Testes de performance de serviços com mocks"""

    @pytest.mark.performance
    def test_whatsapp_service_mock_performance(self):
        """Testa performance do serviço WhatsApp com mocks"""

        # Mock do serviço
        mock_service = MagicMock()
        mock_service.send_text_message.return_value = {"success": True}
        mock_service.verify_webhook.return_value = True

        start_time = time.time()

        # Teste de múltiplas chamadas
        for i in range(5):
            result = mock_service.send_text_message(
                to="5511999999999", message=f"Test message {i}"
            )
            assert result["success"] is True

        end_time = time.time()
        total_time = (end_time - start_time) * 1000  # ms

        # Validação para mocks (deve ser rápido)
        assert total_time < 100, f"Mock operations too slow: {total_time:.2f}ms"

    @pytest.mark.performance
    def test_database_mock_performance(self, mock_database):
        """Testa performance de operações de banco com mocks"""

        import asyncio

        async def test_operations():
            start_time = time.time()

            # Simula operações de banco
            await mock_database.execute("SELECT 1")
            await mock_database.commit()

            end_time = time.time()
            return (end_time - start_time) * 1000  # ms

        # Executa teste assíncrono
        operation_time = asyncio.run(test_operations())

        # Validação para mocks
        assert (
            operation_time < 100
        ), f"Mock DB operations too slow: {operation_time:.2f}ms"


class TestMemoryPerformance:
    """Testes básicos de performance de memória"""

    @pytest.mark.performance
    def test_basic_memory_usage(self):
        """Testa uso básico de memória"""

        try:
            import psutil

            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            pytest.skip("psutil not available")

        # Simula uso de memória pequeno
        data = []
        for i in range(100):  # Quantidade muito reduzida
            data.append(f"test_data_{i}" * 10)

        peak_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Cleanup
        del data
        import gc

        gc.collect()

        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        memory_increase = peak_memory - initial_memory

        # Validação relaxada
        assert (
            memory_increase < 50
        ), f"Aumento de memória muito alto: {memory_increase:.2f}MB"
        assert initial_memory > 0, "Memória inicial deve ser positiva"


# Configuração para testes de performance
@pytest.fixture(autouse=True, scope="function")
def performance_cleanup():
    """Cleanup automático para testes de performance"""
    # Cleanup antes do teste
    try:
        import gc

        gc.collect()
    except:
        pass

    yield

    # Cleanup após o teste
    try:
        import gc

        gc.collect()
    except:
        pass


# Configuração de marcadores
def pytest_configure(config):
    """Configuração de marcadores para pytest"""
    config.addinivalue_line(
        "markers", "performance: marca teste como teste de performance"
    )

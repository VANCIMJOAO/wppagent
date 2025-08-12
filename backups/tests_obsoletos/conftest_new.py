#!/usr/bin/env python3
"""
🧪 Configuração global de testes para WhatsApp Agent - PRODUÇÃO
Fixtures e configurações compartilhadas entre todos os testes
Cobertura completa: Unitários, Integração, Carga e E2E
"""
import pytest
import asyncio
import asyncpg
import redis.asyncio as redis
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
import tempfile
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Generator, List
import time

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configurar ambiente de teste
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test_user:test_pass@localhost/test_whatsapp_agent"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # DB 15 para testes
os.environ["OPENAI_API_KEY"] = "test_key"
os.environ["META_ACCESS_TOKEN"] = "test_token"
os.environ["WEBHOOK_VERIFY_TOKEN"] = "test_verify_token"

from app.main import app
from app.config import settings
from app.database import Base


# 🌐 CONFIGURAÇÃO GLOBAL DO PYTEST
def pytest_configure(config):
    """Configuração inicial do pytest com markers customizados"""
    print("\n🧪 CONFIGURANDO AMBIENTE DE TESTES COMPLETO")
    print("=" * 60)
    
    # Markers customizados
    config.addinivalue_line("markers", "unit: marca testes unitários")
    config.addinivalue_line("markers", "integration: marca testes de integração")
    config.addinivalue_line("markers", "load: marca testes de carga")
    config.addinivalue_line("markers", "e2e: marca testes end-to-end")
    config.addinivalue_line("markers", "slow: marca testes lentos")
    config.addinivalue_line("markers", "external: marca testes que dependem de serviços externos")
    config.addinivalue_line("markers", "meta_api: marca testes da API do Meta")
    config.addinivalue_line("markers", "critical: marca testes de fluxos críticos")


def pytest_addoption(parser):
    """Adiciona opções customizadas ao pytest"""
    parser.addoption("--quick", action="store_true", help="Executa apenas testes rápidos")
    parser.addoption("--performance-only", action="store_true", help="Executa apenas testes de performance")
    parser.addoption("--skip-setup", action="store_true", help="Pula configuração de ambiente")
    parser.addoption("--coverage-report", action="store_true", help="Gera relatório de cobertura detalhado")
    parser.addoption("--load-test-users", type=int, default=100, help="Número de usuários para testes de carga")


def pytest_unconfigure(config):
    """Limpeza final após todos os testes"""
    print("\n🧹 FINALIZANDO SUITE DE TESTES")
    print("=" * 40)


# 🔄 FIXTURES PRINCIPAIS DE INFRAESTRUTURA
@pytest.fixture(scope="session")
def event_loop():
    """📋 Loop de eventos para testes async"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_engine():
    """🗄️ Engine de banco de dados para testes"""
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_size=5,
        max_overflow=10
    )
    
    # Criar todas as tabelas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine):
    """🔄 Sessão de banco isolada para cada teste"""
    async_session = sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Iniciar transação
        await session.begin()
        
        yield session
        
        # Rollback para manter testes isolados
        await session.rollback()


@pytest.fixture
async def test_redis():
    """🔴 Cliente Redis para testes"""
    redis_client = redis.from_url(
        "redis://localhost:6379/15",
        decode_responses=True
    )
    
    # Limpar dados de teste
    await redis_client.flushdb()
    
    yield redis_client
    
    # Cleanup
    await redis_client.flushdb()
    await redis_client.close()


@pytest.fixture
async def test_client():
    """🌐 Cliente HTTP para testes da API"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# 🎭 FIXTURES DE MOCKS
@pytest.fixture
def mock_openai():
    """🤖 Mock do cliente OpenAI"""
    with patch("app.services.llm_service.openai") as mock:
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="Resposta de teste do assistente"
                )
            )
        ]
        mock_response.usage = MagicMock(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )
        
        mock.chat.completions.create = AsyncMock(return_value=mock_response)
        yield mock


@pytest.fixture
def mock_meta_api():
    """📱 Mock da API do Meta/WhatsApp"""
    with patch("app.services.whatsapp_service.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [{"id": "test_message_id"}]
        }
        
        mock_instance = MagicMock()
        mock_instance.post = AsyncMock(return_value=mock_response)
        mock_instance.get = AsyncMock(return_value=mock_response)
        
        mock_client.return_value.__aenter__.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_cache():
    """💾 Mock do serviço de cache"""
    cache_mock = MagicMock()
    cache_mock.get = AsyncMock(return_value=None)
    cache_mock.set = AsyncMock(return_value=True)
    cache_mock.delete = AsyncMock(return_value=True)
    cache_mock.exists = AsyncMock(return_value=False)
    
    with patch("app.services.cache_service.cache_service", cache_mock):
        yield cache_mock


# 📊 FIXTURES DE DADOS DE TESTE
@pytest.fixture
def sample_webhook_payload():
    """📤 Payload de exemplo do webhook do WhatsApp"""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551234567",
                                "phone_number_id": "PHONE_NUMBER_ID"
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "João Silva"
                                    },
                                    "wa_id": "5511999999999"
                                }
                            ],
                            "messages": [
                                {
                                    "from": "5511999999999",
                                    "id": "wamid.message_id",
                                    "timestamp": str(int(time.time())),
                                    "text": {
                                        "body": "Olá! Gostaria de agendar um corte de cabelo."
                                    },
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_user_data():
    """👤 Dados de usuário para testes"""
    return {
        "phone": "5511999999999",
        "name": "João Silva",
        "email": "joao@email.com",
        "preferences": {
            "language": "pt-BR",
            "notification_time": "morning"
        }
    }


@pytest.fixture
def sample_appointment_data():
    """📅 Dados de agendamento para testes"""
    return {
        "user_phone": "5511999999999",
        "service_id": 1,
        "appointment_date": datetime.now() + timedelta(days=1),
        "notes": "Teste de agendamento"
    }


@pytest.fixture
def sample_business_data():
    """🏢 Dados de negócio para testes"""
    return {
        "name": "Barbearia Teste",
        "phone": "5511888888888",
        "address": "Rua Teste, 123",
        "working_hours": {
            "monday": {"start": "09:00", "end": "18:00"},
            "tuesday": {"start": "09:00", "end": "18:00"},
            "wednesday": {"start": "09:00", "end": "18:00"},
            "thursday": {"start": "09:00", "end": "18:00"},
            "friday": {"start": "09:00", "end": "18:00"},
            "saturday": {"start": "09:00", "end": "15:00"},
            "sunday": "closed"
        }
    }


@pytest.fixture
async def setup_test_data(test_db_session, sample_user_data, sample_business_data):
    """🗂️ Setup de dados de teste no banco"""
    from app.models.user import User
    from app.models.business import Business
    from app.models.service import Service
    
    # Criar business
    business = Business(**sample_business_data)
    test_db_session.add(business)
    await test_db_session.flush()
    
    # Criar usuário
    user = User(**sample_user_data, business_id=business.id)
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Criar serviços
    services = [
        Service(name="Corte Masculino", price=30.0, duration=30, business_id=business.id),
        Service(name="Barba", price=20.0, duration=20, business_id=business.id),
        Service(name="Corte + Barba", price=45.0, duration=45, business_id=business.id)
    ]
    
    for service in services:
        test_db_session.add(service)
    
    await test_db_session.commit()
    
    return {
        "user": user,
        "business": business,
        "services": services
    }


# 📈 FIXTURES DE PERFORMANCE E MONITORAMENTO
@pytest.fixture
def performance_monitor():
    """⏱️ Monitor de performance para testes"""
    class PerformanceMonitor:
        def __init__(self):
            self.metrics = {}
            self.start_time = None
        
        def start(self, operation_name):
            self.start_time = datetime.now()
            return self
        
        def end(self, operation_name):
            if self.start_time:
                duration = (datetime.now() - self.start_time).total_seconds()
                self.metrics[operation_name] = duration
                self.start_time = None
                return duration
            return 0
        
        def get_metrics(self):
            return self.metrics.copy()
        
        def assert_performance(self, operation_name, max_duration):
            """Assert que operação não demorou mais que o esperado"""
            duration = self.metrics.get(operation_name, 0)
            assert duration <= max_duration, f"{operation_name} demorou {duration}s, máximo esperado: {max_duration}s"
    
    return PerformanceMonitor()


@pytest.fixture
def temp_file():
    """📄 Arquivo temporário para testes"""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        yield f.name
    
    # Cleanup
    try:
        os.unlink(f.name)
    except FileNotFoundError:
        pass


# 🔍 FIXTURES DE VALIDAÇÃO E TESTE ESPECÍFICAS
@pytest.fixture
def conversation_simulator():
    """💬 Simulador de conversação para testes E2E"""
    class ConversationSimulator:
        def __init__(self, test_client):
            self.client = test_client
            self.conversation_history = []
        
        async def send_message(self, phone: str, message: str) -> dict:
            """Simula envio de mensagem via webhook"""
            payload = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "test_account",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551234567",
                                "phone_number_id": "test_phone_id"
                            },
                            "contacts": [{
                                "profile": {"name": "Test User"},
                                "wa_id": phone
                            }],
                            "messages": [{
                                "from": phone,
                                "id": f"test_msg_{int(time.time())}",
                                "timestamp": str(int(time.time())),
                                "text": {"body": message},
                                "type": "text"
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            response = await self.client.post("/webhook", json=payload)
            
            # Salvar no histórico
            self.conversation_history.append({
                "phone": phone,
                "message": message,
                "response": response.json() if response.status_code == 200 else None,
                "timestamp": datetime.now()
            })
            
            return response.json() if response.status_code == 200 else {}
        
        def get_conversation_history(self, phone: str = None) -> List[dict]:
            """Obtém histórico de conversação"""
            if phone:
                return [h for h in self.conversation_history if h["phone"] == phone]
            return self.conversation_history.copy()
        
        def clear_history(self):
            """Limpa histórico de conversação"""
            self.conversation_history.clear()
    
    return ConversationSimulator


@pytest.fixture
def load_test_data():
    """🚀 Dados para testes de carga"""
    return {
        "concurrent_users": [10, 50, 100, 200],
        "test_messages": [
            "Olá, gostaria de agendar um horário",
            "Qual o preço do corte?",
            "Vocês fazem barba também?",
            "Que horários têm disponível amanhã?",
            "Posso cancelar meu agendamento?",
            "Onde vocês ficam localizados?",
            "Trabalham aos sábados?",
            "Fazem desconto para estudante?",
            "Preciso remarcar meu horário",
            "Muito obrigado pelo atendimento!"
        ],
        "test_phones": [f"5511999{i:06d}" for i in range(1000)]
    }


# 🎯 HOOKS DO PYTEST
def pytest_runtest_setup(item):
    """Setup executado antes de cada teste"""
    print(f"\n🧪 Iniciando teste: {item.name}")


def pytest_runtest_teardown(item):
    """Teardown executado após cada teste"""
    print(f"✅ Teste concluído: {item.name}")


@pytest.fixture(autouse=True)
async def cleanup_test_environment():
    """🧹 Cleanup automático do ambiente de teste"""
    yield
    
    # Cleanup adicional se necessário
    # Por exemplo, limpar arquivos temporários, conexões, etc.
    pass


# 📋 CONFIGURAÇÕES DE COLETA DE MÉTRICAS DE TESTE
@pytest.fixture(scope="session")
def test_metrics_collector():
    """📊 Coletor de métricas de teste para relatórios"""
    class TestMetricsCollector:
        def __init__(self):
            self.metrics = {
                "tests_executed": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "average_execution_time": 0,
                "coverage_percentage": 0,
                "critical_paths_tested": [],
                "performance_benchmarks": {}
            }
        
        def record_test_result(self, test_name: str, passed: bool, execution_time: float):
            """Registra resultado de um teste"""
            self.metrics["tests_executed"] += 1
            if passed:
                self.metrics["tests_passed"] += 1
            else:
                self.metrics["tests_failed"] += 1
        
        def get_summary(self) -> dict:
            """Obtém resumo das métricas"""
            return self.metrics.copy()
    
    return TestMetricsCollector()

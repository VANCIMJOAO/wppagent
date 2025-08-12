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
def backend_setup() -> Generator[BackendTestSetup, None, None]:
    """🚀 Setup completo do backend para toda a sessão de testes"""
    print("\n🚀 Iniciando setup do backend...")
    
    setup = BackendTestSetup()
    
    # Verificar se serviços já estão rodando
    status = setup.get_service_status()
    
    if not status['backend']['health']:
        print("🔧 Backend não está rodando, iniciando...")
        assert setup.start_backend_services(), "❌ Falha ao iniciar backend"
        assert setup.wait_for_services(), "❌ Serviços não ficaram disponíveis"
    else:
        print("✅ Backend já está rodando")
    
    if not status['database']['test_data']:
        print("📊 Populando dados de teste...")
        assert setup.populate_test_data(), "❌ Falha ao popular dados de teste"
    else:
        print("✅ Dados de teste já estão disponíveis")
    
    print("🎯 Backend setup completo!")
    
    yield setup
    
    # Cleanup no final da sessão
    print("\n🧹 Cleanup do backend...")
    # Nota: Comentado para permitir reutilização entre execuções
    # setup.cleanup_services()


@pytest.fixture(scope="session")
def test_reporter() -> Generator[TestReporter, None, None]:
    """📊 Reporter para métricas dos testes"""
    reporter = TestReporter()
    reporter.start_test_session()
    
    yield reporter
    
    reporter.end_test_session()
    
    # Gerar relatório final
    report = reporter.generate_report()
    
    print(f"\n📊 RELATÓRIO FINAL DA SESSÃO")
    print("=" * 40)
    print(f"🧪 Total de testes: {report['summary']['total_tests']}")
    print(f"✅ Sucessos: {report['summary']['successful']}")
    print(f"❌ Falhas: {report['summary']['failed']}")
    print(f"📈 Taxa de sucesso: {report['summary']['success_rate']:.1f}%")
    print(f"⏱️ Tempo médio por teste: {report['summary']['average_duration']:.2f}s")
    
    if report['summary']['session_duration']:
        print(f"🕐 Duração total da sessão: {report['summary']['session_duration']:.1f}s")


@pytest.fixture
def api_client(backend_setup) -> requests.Session:
    """🌐 Cliente HTTP para chamadas da API"""
    session = requests.Session()
    session.timeout = TIMEOUTS['api_response']
    return session


@pytest.fixture
def test_database() -> Generator[Session, None, None]:
    """🗄️ Sessão do banco de dados para testes"""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_customer() -> Dict[str, Any]:
    """👤 Cliente de exemplo para testes"""
    return TEST_USERS['new_customer']


@pytest.fixture
def vip_customer() -> Dict[str, Any]:
    """👑 Cliente VIP para testes"""
    return TEST_USERS['vip_customer']


@pytest.fixture
def real_whatsapp_payload(sample_customer) -> Dict[str, Any]:
    """📱 Payload real do WhatsApp para testes"""
    return {
        "entry": [{
            "id": WHATSAPP_CONFIG['phone_number_id'],
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": TEST_BUSINESS_DATA['phone'],
                        "phone_number_id": WHATSAPP_CONFIG['phone_number_id']
                    },
                    "contacts": [{
                        "profile": {"name": sample_customer['nome']},
                        "wa_id": sample_customer['wa_id']
                    }],
                    "messages": [{
                        "from": sample_customer['wa_id'],
                        "id": f"wamid.test_{int(time.time())}",
                        "timestamp": str(int(time.time())),
                        "text": {"body": "Mensagem de teste"},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }


@pytest.fixture
def webhook_helper(backend_setup):
    """🎣 Helper para enviar webhooks facilmente"""
    class WebhookHelper:
        def __init__(self, setup: BackendTestSetup):
            self.setup = setup
        
        def send_message(self, customer: Dict, message: str) -> requests.Response:
            """Envia uma mensagem via webhook"""
            payload = self.setup.create_test_webhook_payload(customer, message)
            
            response = requests.post(
                API_ENDPOINTS['webhook'],
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=TIMEOUTS['webhook_processing']
            )
            
            return response
        
        def send_conversation(self, customer: Dict, messages: List[str]) -> List[requests.Response]:
            """Envia uma sequência de mensagens"""
            responses = []
            
            for message in messages:
                response = self.send_message(customer, message)
                responses.append(response)
                time.sleep(DELAYS['between_messages'])
            
            return responses
    
    return WebhookHelper(backend_setup)


@pytest.fixture
def performance_monitor():
    """📈 Monitor de performance para testes"""
    class PerformanceMonitor:
        def __init__(self):
            self.metrics = []
        
        def measure(self, operation_name: str):
            """Context manager para medir tempo de operação"""
            class Measurement:
                def __init__(self, name: str, metrics_list: List):
                    self.name = name
                    self.metrics = metrics_list
                    self.start_time = None
                
                def __enter__(self):
                    self.start_time = time.time()
                    return self
                
                def __exit__(self, exc_type, exc_val, exc_tb):
                    duration = time.time() - self.start_time
                    self.metrics.append({
                        'operation': self.name,
                        'duration': duration,
                        'success': exc_type is None,
                        'timestamp': time.time()
                    })
            
            return Measurement(operation_name, self.metrics)
        
        def get_metrics(self) -> List[Dict]:
            return self.metrics
        
        def get_avg_duration(self, operation_name: str = None) -> float:
            if operation_name:
                operations = [m for m in self.metrics if m['operation'] == operation_name]
            else:
                operations = self.metrics
            
            if not operations:
                return 0.0
            
            return sum(op['duration'] for op in operations) / len(operations)
    
    return PerformanceMonitor()


# 🧪 FIXTURES PARA CENÁRIOS ESPECÍFICOS
@pytest.fixture
def discovery_scenario() -> Dict[str, Any]:
    """🔍 Cenário de descoberta de serviços"""
    return TEST_SCENARIOS['discovery_flow']


@pytest.fixture
def booking_scenario() -> Dict[str, Any]:
    """📅 Cenário de agendamento"""
    return TEST_SCENARIOS['booking_flow']


@pytest.fixture
def complaint_scenario() -> Dict[str, Any]:
    """😠 Cenário de reclamação"""
    return TEST_SCENARIOS['handoff_flow']


# 🎯 HELPERS DE VALIDAÇÃO
@pytest.fixture
def response_validator():
    """✅ Validador de respostas"""
    class ResponseValidator:
        @staticmethod
        def validate_webhook_response(response: requests.Response):
            """Valida resposta do webhook"""
            assert response.status_code == 200, f"Webhook falhou: {response.status_code}"
            assert response.headers.get('content-type', '').startswith('application/json'), \
                "Response não é JSON"
        
        @staticmethod
        def validate_response_time(duration: float, threshold: float = None):
            """Valida tempo de resposta"""
            if threshold is None:
                threshold = PERFORMANCE_THRESHOLDS['api_response_time']
            
            assert duration < threshold, f"Resposta muito lenta: {duration:.2f}s > {threshold}s"
        
        @staticmethod
        def validate_database_consistency(session: Session, user_wa_id: str):
            """Valida consistência dos dados no banco"""
            user = session.query(User).filter(User.wa_id == user_wa_id).first()
            assert user is not None, f"Usuário {user_wa_id} não encontrado no banco"
            
            messages = session.query(Message).filter(Message.user_id == user.id).all()
            conversations = session.query(Conversation).filter(Conversation.user_id == user.id).all()
            
            return {
                'user': user,
                'messages_count': len(messages),
                'conversations_count': len(conversations)
            }
    
    return ResponseValidator()


# 📊 FIXTURES DE DADOS DE TESTE
@pytest.fixture
def test_services() -> List[Dict]:
    """🛠️ Lista de serviços para teste"""
    return TEST_SERVICES


@pytest.fixture
def test_business_data() -> Dict[str, Any]:
    """🏢 Dados da empresa para teste"""
    return TEST_BUSINESS_DATA


# 🔧 CONFIGURAÇÕES DE PYTEST
pytest_plugins = []

# Markers customizados
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marca testes que demoram mais para executar")
    config.addinivalue_line("markers", "integration: testes de integração end-to-end")
    config.addinivalue_line("markers", "api: testes de API REST")
    config.addinivalue_line("markers", "webhook: testes de webhook do WhatsApp")
    config.addinivalue_line("markers", "database: testes que verificam dados no banco")
    config.addinivalue_line("markers", "performance: testes de performance e carga")


# 🏃 HOOKS DO PYTEST
def pytest_runtest_setup(item):
    """Setup antes de cada teste"""
    if hasattr(item, 'function'):
        test_name = item.function.__name__
        print(f"\n🧪 Iniciando teste: {test_name}")


def pytest_runtest_teardown(item, nextitem):
    """Teardown após cada teste"""
    if hasattr(item, 'function'):
        test_name = item.function.__name__
        print(f"✅ Teste concluído: {test_name}")


def pytest_runtest_makereport(item, call):
    """Hook para gerar relatórios customizados"""
    if call.when == "call":
        test_name = item.nodeid.split("::")[-1]
        duration = call.duration
        
        if call.excinfo is None:
            print(f"✅ {test_name} passou em {duration:.2f}s")
        else:
            print(f"❌ {test_name} falhou em {duration:.2f}s")


# 📋 COMANDOS CUSTOMIZADOS
def pytest_addoption(parser):
    """Adiciona opções customizadas ao pytest"""
    parser.addoption(
        "--skip-setup",
        action="store_true",
        default=False,
        help="Pula setup do backend (assume que já está rodando)"
    )
    
    parser.addoption(
        "--performance-only",
        action="store_true", 
        default=False,
        help="Executa apenas testes de performance"
    )
    
    parser.addoption(
        "--quick",
        action="store_true",
        default=False,
        help="Executa apenas testes rápidos"
    )


def pytest_collection_modifyitems(config, items):
    """Modifica coleção de testes baseado nas opções"""
    if config.getoption("--performance-only"):
        performance_items = [item for item in items if "performance" in item.keywords]
        items[:] = performance_items
    
    if config.getoption("--quick"):
        quick_items = [item for item in items if "slow" not in item.keywords]
        items[:] = quick_items


if __name__ == "__main__":
    print("🧪 CONFIGURAÇÃO DO PYTEST PARA WHATSAPP AGENT")
    print("=" * 50)
    print("📋 Execute os testes com:")
    print("   pytest tests/ -v")
    print("   pytest tests/real_backend/ -v")
    print("   pytest tests/real_backend/test_real_api_calls.py -v")
    print("   pytest --quick  # apenas testes rápidos")
    print("   pytest --performance-only  # apenas performance")
    print("   pytest --skip-setup  # pula setup do backend")

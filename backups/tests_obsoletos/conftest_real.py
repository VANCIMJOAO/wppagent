"""
🧪 Configuração de Testes REAIS - SEM MOCKS
Testa o sistema real rodando em produção/desenvolvimento
"""
import pytest
import asyncio
import httpx
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sys
from pathlib import Path

# Configurações do ambiente real
REAL_API_BASE_URL = "http://localhost:8000"
WEBHOOK_ENDPOINT = f"{REAL_API_BASE_URL}/webhook"
HEALTH_ENDPOINT = f"{REAL_API_BASE_URL}/health"

# Timeouts para testes reais
TIMEOUTS = {
    "api_call": 30.0,          # 30s para chamadas de API
    "webhook_processing": 15.0,  # 15s para processamento de webhook
    "conversation_flow": 45.0,   # 45s para fluxo completo de conversa
    "health_check": 5.0,        # 5s para health check
}

# Dados de teste reais
REAL_TEST_PHONE = "5511999999999"  # Telefone de teste
REAL_BUSINESS_DATA = {
    "name": "Barbearia Teste",
    "phone": "11999887766", 
    "address": "Rua Teste, 123",
    "services": ["Corte", "Barba", "Sobrancelha"],
    "hours": "Seg-Sex: 9h-18h, Sáb: 9h-15h"
}


class RealAPIClient:
    """Cliente para interagir com a API real"""
    
    def __init__(self):
        self.base_url = REAL_API_BASE_URL
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        self.conversation_history = {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica se a API está rodando"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return {
                "status": response.status_code,
                "healthy": response.status_code == 200,
                "data": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            return {
                "status": 0,
                "healthy": False,
                "error": str(e)
            }
    
    async def send_webhook_message(self, phone: str, message: str, message_type: str = "text") -> Dict[str, Any]:
        """Envia mensagem real via webhook"""
        timestamp = str(int(time.time()))
        message_id = f"wamid.test_{timestamp}_{phone}"
        
        # Criar payload real do WhatsApp
        webhook_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "business_account_id",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15550000000",
                            "phone_number_id": "phone_number_id"
                        },
                        "contacts": [{
                            "profile": {"name": f"Teste User {phone}"},
                            "wa_id": phone
                        }],
                        "messages": [{
                            "from": phone,
                            "id": message_id,
                            "timestamp": timestamp,
                            "type": message_type,
                            "text": {"body": message} if message_type == "text" else None
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        try:
            response = await self.client.post(
                WEBHOOK_ENDPOINT,
                json=webhook_payload,
                headers={"Content-Type": "application/json"}
            )
            
            result = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_data": response.json() if response.status_code == 200 else None,
                "error": response.text if response.status_code != 200 else None,
                "timestamp": datetime.now().isoformat(),
                "message_id": message_id
            }
            
            # Armazenar no histórico
            if phone not in self.conversation_history:
                self.conversation_history[phone] = []
            
            self.conversation_history[phone].append({
                "message": message,
                "timestamp": timestamp,
                "message_id": message_id,
                "response": result
            })
            
            return result
            
        except Exception as e:
            return {
                "status_code": 0,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def send_conversation(self, phone: str, messages: List[str], delay_between: float = 2.0) -> List[Dict[str, Any]]:
        """Envia uma sequência de mensagens simulando conversa real"""
        results = []
        
        for i, message in enumerate(messages):
            print(f"📱 Enviando mensagem {i+1}/{len(messages)}: {message[:50]}...")
            
            result = await self.send_webhook_message(phone, message)
            results.append(result)
            
            if result["success"]:
                print(f"✅ Mensagem {i+1} processada com sucesso")
            else:
                print(f"❌ Erro na mensagem {i+1}: {result.get('error', 'Erro desconhecido')}")
            
            # Delay entre mensagens para simular conversa real
            if i < len(messages) - 1:
                await asyncio.sleep(delay_between)
        
        return results
    
    def get_conversation_history(self, phone: str) -> List[Dict[str, Any]]:
        """Retorna histórico de conversa"""
        return self.conversation_history.get(phone, [])
    
    def clear_conversation_history(self, phone: str = None):
        """Limpa histórico de conversa"""
        if phone:
            self.conversation_history.pop(phone, None)
        else:
            self.conversation_history.clear()
    
    async def close(self):
        """Fecha cliente HTTP"""
        await self.client.aclose()


class RealTestReporter:
    """Reporter para métricas de testes reais"""
    
    def __init__(self):
        self.test_results = []
        self.session_start = None
        self.session_end = None
    
    def start_session(self):
        """Inicia sessão de testes"""
        self.session_start = datetime.now()
        print(f"\n🚀 INICIANDO SESSÃO DE TESTES REAIS")
        print(f"⏰ Início: {self.session_start.isoformat()}")
        print("=" * 60)
    
    def end_session(self):
        """Finaliza sessão de testes"""
        self.session_end = datetime.now()
        duration = (self.session_end - self.session_start).total_seconds()
        
        print(f"\n🏁 FINALIZANDO SESSÃO DE TESTES REAIS")
        print(f"⏰ Fim: {self.session_end.isoformat()}")
        print(f"🕐 Duração total: {duration:.1f}s")
        print("=" * 60)
    
    def record_test(self, test_name: str, success: bool, duration: float, details: Dict = None):
        """Registra resultado de teste"""
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        })
    
    def generate_report(self) -> Dict[str, Any]:
        """Gera relatório final"""
        if not self.test_results:
            return {"error": "Nenhum teste registrado"}
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for test in self.test_results if test["success"])
        failed_tests = total_tests - successful_tests
        
        total_duration = sum(test["duration"] for test in self.test_results)
        avg_duration = total_duration / total_tests if total_tests > 0 else 0
        
        session_duration = None
        if self.session_start and self.session_end:
            session_duration = (self.session_end - self.session_start).total_seconds()
        
        return {
            "summary": {
                "total_tests": total_tests,
                "successful": successful_tests,
                "failed": failed_tests,
                "success_rate": (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
                "total_duration": total_duration,
                "average_duration": avg_duration,
                "session_duration": session_duration
            },
            "test_details": self.test_results
        }


# 🧪 FIXTURES PRINCIPAIS PARA TESTES REAIS
@pytest.fixture(scope="session")
def event_loop():
    """Loop de eventos para testes async"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def real_api_client():
    """Cliente da API real"""
    client = RealAPIClient()
    
    # Verificar se API está rodando
    health = await client.health_check()
    if not health["healthy"]:
        pytest.skip(f"API não está rodando em {REAL_API_BASE_URL}: {health.get('error', 'Status: ' + str(health['status']))}")
    
    print(f"✅ API está rodando em {REAL_API_BASE_URL}")
    
    yield client
    
    await client.close()


@pytest.fixture(scope="session")
def real_test_reporter():
    """Reporter para testes reais"""
    reporter = RealTestReporter()
    reporter.start_session()
    
    yield reporter
    
    reporter.end_session()
    report = reporter.generate_report()
    
    print(f"\n📊 RELATÓRIO FINAL DE TESTES REAIS")
    print("=" * 50)
    print(f"🧪 Total de testes: {report['summary']['total_tests']}")
    print(f"✅ Sucessos: {report['summary']['successful']}")
    print(f"❌ Falhas: {report['summary']['failed']}")
    print(f"📈 Taxa de sucesso: {report['summary']['success_rate']:.1f}%")
    print(f"⏱️ Tempo médio por teste: {report['summary']['average_duration']:.2f}s")
    
    if report['summary']['session_duration']:
        print(f"🕐 Duração total da sessão: {report['summary']['session_duration']:.1f}s")


@pytest.fixture
def test_phone():
    """Telefone para testes"""
    return f"{REAL_TEST_PHONE}_{int(time.time())}"  # Único por execução


@pytest.fixture
def conversation_tester(real_api_client, test_phone):
    """Helper para testar conversas completas"""
    class ConversationTester:
        def __init__(self, client: RealAPIClient, phone: str):
            self.client = client
            self.phone = phone
            self.messages_sent = []
        
        async def send_message(self, message: str) -> Dict[str, Any]:
            """Envia uma mensagem e retorna resultado"""
            result = await self.client.send_webhook_message(self.phone, message)
            self.messages_sent.append({"message": message, "result": result})
            return result
        
        async def send_conversation_flow(self, messages: List[str], delay: float = 1.0) -> List[Dict[str, Any]]:
            """Envia fluxo completo de conversa"""
            results = []
            for message in messages:
                result = await self.send_message(message)
                results.append(result)
                if delay > 0:
                    await asyncio.sleep(delay)
            return results
        
        def get_success_rate(self) -> float:
            """Calcula taxa de sucesso das mensagens"""
            if not self.messages_sent:
                return 0.0
            successful = sum(1 for msg in self.messages_sent if msg["result"]["success"])
            return (successful / len(self.messages_sent)) * 100
        
        def get_conversation_summary(self) -> Dict[str, Any]:
            """Retorna resumo da conversa"""
            return {
                "phone": self.phone,
                "total_messages": len(self.messages_sent),
                "success_rate": self.get_success_rate(),
                "messages": self.messages_sent
            }
    
    return ConversationTester(real_api_client, test_phone)


@pytest.fixture
def performance_tester():
    """Helper para testes de performance"""
    class PerformanceTester:
        def __init__(self):
            self.measurements = []
        
        async def measure_api_call(self, operation_name: str, coroutine):
            """Mede tempo de uma operação async"""
            start_time = time.time()
            try:
                result = await coroutine
                duration = time.time() - start_time
                success = True
            except Exception as e:
                duration = time.time() - start_time
                result = {"error": str(e)}
                success = False
            
            measurement = {
                "operation": operation_name,
                "duration": duration,
                "success": success,
                "timestamp": datetime.now().isoformat(),
                "result": result
            }
            
            self.measurements.append(measurement)
            return measurement
        
        def get_average_duration(self, operation_name: str = None) -> float:
            """Calcula duração média"""
            if operation_name:
                ops = [m for m in self.measurements if m["operation"] == operation_name]
            else:
                ops = self.measurements
            
            if not ops:
                return 0.0
            
            return sum(op["duration"] for op in ops) / len(ops)
        
        def get_success_rate(self, operation_name: str = None) -> float:
            """Calcula taxa de sucesso"""
            if operation_name:
                ops = [m for m in self.measurements if m["operation"] == operation_name]
            else:
                ops = self.measurements
            
            if not ops:
                return 0.0
            
            successful = sum(1 for op in ops if op["success"])
            return (successful / len(ops)) * 100
        
        def get_performance_summary(self) -> Dict[str, Any]:
            """Retorna resumo de performance"""
            return {
                "total_operations": len(self.measurements),
                "average_duration": self.get_average_duration(),
                "success_rate": self.get_success_rate(),
                "measurements": self.measurements
            }
    
    return PerformanceTester()


# 🎯 FIXTURES DE CENÁRIOS REAIS
@pytest.fixture
def booking_scenario():
    """Cenário real de agendamento"""
    return {
        "customer_name": "João Silva Teste",
        "service": "Corte masculino",
        "preferred_time": "amanhã às 14h",
        "phone": "11987654321",
        "messages": [
            "Olá, boa tarde!",
            "Gostaria de agendar um corte de cabelo",
            "Para amanhã de tarde, se possível",
            "Às 14h está disponível?",
            "Meu nome é João Silva",
            "Sim, confirmo o agendamento"
        ]
    }


@pytest.fixture
def price_inquiry_scenario():
    """Cenário real de consulta de preços"""
    return {
        "messages": [
            "Oi! Quanto custa um corte masculino?",
            "E barba? Vocês fazem também?",
            "Qual o preço do pacote corte + barba?",
            "Obrigado pelas informações!"
        ]
    }


@pytest.fixture
def cancellation_scenario():
    """Cenário real de cancelamento"""
    return {
        "messages": [
            "Olá, preciso cancelar meu agendamento",
            "É para hoje às 15h",
            "Sim, quero cancelar mesmo",
            "Surgiu um compromisso urgente",
            "Obrigado pela compreensão"
        ]
    }


@pytest.fixture
def complex_inquiry_scenario():
    """Cenário real de consulta complexa"""
    return {
        "messages": [
            "Oi! Vocês atendem no sábado?",
            "Que horas abrem e fecham?",
            "Onde fica a barbearia?",
            "Tem estacionamento?",
            "Aceitam cartão?",
            "Perfeito, obrigado!"
        ]
    }


# 🔧 CONFIGURAÇÕES PYTEST PARA TESTES REAIS
def pytest_configure(config):
    """Configuração do pytest para testes reais"""
    print("\n🧪 CONFIGURANDO TESTES REAIS (SEM MOCKS)")
    print("=" * 60)
    
    config.addinivalue_line("markers", "real: testes com sistema real")
    config.addinivalue_line("markers", "api: testes de API real")
    config.addinivalue_line("markers", "webhook: testes de webhook real")
    config.addinivalue_line("markers", "conversation: testes de conversa real")
    config.addinivalue_line("markers", "performance: testes de performance real")
    config.addinivalue_line("markers", "e2e_real: testes end-to-end reais")


def pytest_addoption(parser):
    """Opções para testes reais"""
    parser.addoption(
        "--api-url",
        default=REAL_API_BASE_URL,
        help="URL da API para testes reais"
    )
    parser.addoption(
        "--real-phone",
        default=REAL_TEST_PHONE,
        help="Telefone base para testes reais"
    )
    parser.addoption(
        "--quick-real",
        action="store_true",
        default=False,
        help="Executa apenas testes reais rápidos"
    )


def pytest_collection_modifyitems(config, items):
    """Filtra testes baseado nas opções"""
    if config.getoption("--quick-real"):
        # Executar apenas testes marcados como rápidos
        quick_items = [item for item in items if "slow" not in item.keywords]
        items[:] = quick_items


if __name__ == "__main__":
    print("🧪 CONFIGURAÇÃO DE TESTES REAIS")
    print("=" * 40)
    print("📋 Execute os testes reais com:")
    print("   pytest tests/test_real_*.py -v")
    print("   pytest tests/test_real_*.py -v --api-url=http://localhost:8000")
    print("   pytest tests/test_real_*.py -v --quick-real")

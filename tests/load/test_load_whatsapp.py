"""
Load Testing com Locust para TRILHA 2 FASE 2.2
===============================================

Testes de performance e carga para endpoints críticos
do WhatsApp Agent usando Locust framework.
"""

import json
import random
import time
from datetime import datetime

from locust import HttpUser, between, events, task


class WhatsAppAgentUser(HttpUser):
    """
    Simulação de usuário do WhatsApp Agent
    Testa endpoints críticos sob carga
    """

    # Tempo de espera entre requests (1-3 segundos)
    wait_time = between(1, 3)

    def on_start(self):
        """Executado quando usuário inicia - setup inicial"""
        self.auth_token = None
        self.user_id = f"test_user_{random.randint(1000, 9999)}"
        self.phone_number = f"5511{random.randint(900000000, 999999999)}"

        # Tentar fazer login/autenticação se endpoint existir
        self.authenticate()

    def authenticate(self):
        """
        Tenta autenticar usuário para testes que precisam de token
        """
        try:
            response = self.client.post(
                "/auth/login",
                json={"username": self.user_id, "password": "test_password"},
                catch_response=True,
            )

            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.auth_token = data["access_token"]
                    response.success()
                else:
                    response.failure(f"No token in response: {data}")
            else:
                # Autenticação pode não estar disponível - continuar sem token
                response.success()

        except Exception as e:
            # Se endpoint não existir, continuar sem autenticação
            pass

    @property
    def auth_headers(self):
        """Headers com autenticação se disponível"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}

    @task(3)
    def health_check(self):
        """
        Teste do endpoint de health check
        Peso 3 - executado com frequência alta
        """
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(2)
    def webhook_message(self):
        """
        Simula recebimento de mensagem via webhook
        Peso 2 - carga moderada
        """
        message_data = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "business_account_id",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": self.phone_number,
                                    "phone_number_id": "phone_id",
                                },
                                "messages": [
                                    {
                                        "from": self.phone_number,
                                        "id": f"msg_{random.randint(10000, 99999)}",
                                        "timestamp": str(int(time.time())),
                                        "text": {
                                            "body": f"Mensagem de teste {random.randint(1, 1000)}"
                                        },
                                        "type": "text",
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        with self.client.post(
            "/webhook",
            json=message_data,
            headers={"Content-Type": "application/json"},
            catch_response=True,
        ) as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"Webhook failed: {response.status_code}")

    @task(1)
    def list_conversations(self):
        """
        Lista conversas do usuário
        Peso 1 - carga baixa
        """
        with self.client.get(
            "/conversations", headers=self.auth_headers, catch_response=True
        ) as response:
            if response.status_code in [200, 401]:  # 401 é OK se não autenticado
                response.success()
            else:
                response.failure(f"Conversations failed: {response.status_code}")

    @task(1)
    def dashboard_access(self):
        """
        Acesso ao dashboard principal
        Peso 1 - carga baixa
        """
        with self.client.get(
            "/dashboard", headers=self.auth_headers, catch_response=True
        ) as response:
            if response.status_code in [200, 401, 404]:  # Diversos status OK
                response.success()
            else:
                response.failure(f"Dashboard failed: {response.status_code}")

    @task(1)
    def analytics_data(self):
        """
        Busca dados de analytics
        Peso 1 - carga baixa mas pode ser pesado
        """
        with self.client.get(
            "/analytics/summary", headers=self.auth_headers, catch_response=True
        ) as response:
            if response.status_code in [200, 401, 404]:
                response.success()
            else:
                response.failure(f"Analytics failed: {response.status_code}")


class HeavyLoadUser(HttpUser):
    """
    Usuário que simula carga pesada no sistema
    Para testes de stress
    """

    wait_time = between(0.1, 0.5)  # Requisições mais frequentes

    @task
    def spam_health_checks(self):
        """Bombardeio de health checks"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Heavy health check failed: {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Executado no início dos testes"""
    print(f"\n🚀 Iniciando Load Testing - TRILHA 2 FASE 2.2")
    print(f"Target: {environment.host}")
    print(f"Usuários: {environment.runner.target_user_count}")
    print(f"=" * 50)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Executado no final dos testes"""
    print(f"\n📊 Load Testing Concluído!")
    print(f"=" * 50)

    # Estatísticas básicas
    stats = environment.runner.stats
    print(f"Total de requests: {stats.total.num_requests}")
    print(f"Requests falharam: {stats.total.num_failures}")
    print(f"Taxa de falhas: {stats.total.fail_ratio:.2%}")
    print(f"Tempo médio de resposta: {stats.total.avg_response_time:.2f}ms")
    print(f"RPS médio: {stats.total.current_rps:.2f}")

    # Análise de performance
    if stats.total.avg_response_time > 1000:
        print(
            f"⚠️  ATENÇÃO: Tempo de resposta alto (>{stats.total.avg_response_time:.0f}ms)"
        )

    if stats.total.fail_ratio > 0.05:  # 5%
        print(f"❌ PROBLEMA: Taxa de falhas alta ({stats.total.fail_ratio:.1%})")

    if stats.total.fail_ratio == 0 and stats.total.avg_response_time < 500:
        print(f"✅ EXCELENTE: Sistema respondeu bem sob carga!")


# Configurações específicas para diferentes tipos de teste
TEST_SCENARIOS = {
    "light_load": {
        "users": 10,
        "spawn_rate": 2,
        "run_time": "2m",
        "description": "Carga leve - uso normal",
    },
    "moderate_load": {
        "users": 50,
        "spawn_rate": 5,
        "run_time": "5m",
        "description": "Carga moderada - pico normal",
    },
    "heavy_load": {
        "users": 100,
        "spawn_rate": 10,
        "run_time": "10m",
        "description": "Carga pesada - stress test",
    },
    "spike_test": {
        "users": 200,
        "spawn_rate": 50,
        "run_time": "3m",
        "description": "Teste de pico - carga súbita",
    },
}


if __name__ == "__main__":
    """
    Para executar este arquivo diretamente:

    # Teste leve
    locust -f tests/load/test_load_whatsapp.py --host=http://localhost:8000 --users=10 --spawn-rate=2 -t 2m --headless

    # Teste pesado
    locust -f tests/load/test_load_whatsapp.py --host=http://localhost:8000 --users=100 --spawn-rate=10 -t 5m --headless

    # Interface web (para análise visual)
    locust -f tests/load/test_load_whatsapp.py --host=http://localhost:8000
    """
    print(
        "Execute com locust -f tests/load/test_load_whatsapp.py --host=http://localhost:8000"
    )
    print("Scenarios disponíveis:")
    for name, config in TEST_SCENARIOS.items():
        print(f"  {name}: {config['description']}")
        print(
            f"    locust ... --users={config['users']} --spawn-rate={config['spawn_rate']} -t {config['run_time']} --headless"
        )

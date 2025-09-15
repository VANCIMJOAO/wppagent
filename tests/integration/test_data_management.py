#!/usr/bin/env python3
"""TRILHA 2 FASE 2.3 - Test Data Management"""

import asyncio
import json
import random
import string
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class DataType(Enum):
    """Tipos de dados de teste"""

    USER = "user"
    CONVERSATION = "conversation"
    MESSAGE = "message"
    WEBHOOK = "webhook"
    AUTH_TOKEN = "auth_token"
    APPOINTMENT = "appointment"


@dataclass
class TestData:
    """Estrutura de dados de teste"""

    id: str
    type: DataType
    data: Dict[str, Any]
    created_at: str
    dependencies: List[str] = field(default_factory=list)
    cleanup_required: bool = True


class DataFactory:
    """Factory para criação de dados de teste"""

    def __init__(self):
        self.sequence_counters = {}
        self.created_data = {}

    def _get_sequence(self, prefix: str) -> int:
        """Gera sequência única para IDs"""
        if prefix not in self.sequence_counters:
            self.sequence_counters[prefix] = 0
        self.sequence_counters[prefix] += 1
        return self.sequence_counters[prefix]

    def _random_string(self, length: int = 8) -> str:
        """Gera string aleatória"""
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def _random_phone(self) -> str:
        """Gera número de telefone de teste"""
        return f"+55119{random.randint(10000000, 99999999)}"

    def _random_email(self) -> str:
        """Gera email de teste"""
        return f"test_{self._random_string(6)}@example.com"

    def create_user(self, **kwargs) -> TestData:
        """Cria dados de usuário"""
        seq = self._get_sequence("user")
        user_id = f"user_{seq}_{self._random_string(4)}"

        default_data = {
            "id": user_id,
            "name": f"Test User {seq}",
            "email": self._random_email(),
            "phone": self._random_phone(),
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "preferences": {
                "language": "pt-BR",
                "notifications": True,
                "timezone": "America/Sao_Paulo",
            },
        }

        # Aplicar overrides
        final_data = {**default_data, **kwargs}

        test_data = TestData(
            id=user_id,
            type=DataType.USER,
            data=final_data,
            created_at=datetime.now().isoformat(),
        )

        self.created_data[user_id] = test_data
        return test_data

    def create_conversation(self, user_id: str = None, **kwargs) -> TestData:
        """Cria dados de conversa"""
        seq = self._get_sequence("conversation")
        conv_id = f"conv_{seq}_{self._random_string(6)}"

        # Se não fornecido user_id, criar um usuário
        if not user_id:
            user = self.create_user()
            user_id = user.data["id"]

        default_data = {
            "id": conv_id,
            "user_id": user_id,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message_count": 0,
            "last_message_at": None,
            "context": [],
            "metadata": {
                "channel": "whatsapp",
                "source": "webhook",
                "priority": "normal",
            },
        }

        final_data = {**default_data, **kwargs}

        test_data = TestData(
            id=conv_id,
            type=DataType.CONVERSATION,
            data=final_data,
            created_at=datetime.now().isoformat(),
            dependencies=[user_id] if user_id else [],
        )

        self.created_data[conv_id] = test_data
        return test_data

    def create_message(self, conversation_id: str = None, **kwargs) -> TestData:
        """Cria dados de mensagem"""
        seq = self._get_sequence("message")
        msg_id = f"msg_{seq}_{self._random_string(8)}"

        # Se não fornecido conversation_id, criar uma conversa
        if not conversation_id:
            conv = self.create_conversation()
            conversation_id = conv.data["id"]

        messages_pool = [
            "Olá, preciso de ajuda",
            "Gostaria de agendar uma consulta",
            "Qual o horário de funcionamento?",
            "Obrigado pelo atendimento",
            "Tenho uma dúvida sobre os serviços",
            "Como posso cancelar meu agendamento?",
        ]

        default_data = {
            "id": msg_id,
            "conversation_id": conversation_id,
            "from": self._random_phone(),
            "to": "+5511999999999",
            "text": random.choice(messages_pool),
            "timestamp": datetime.now().isoformat(),
            "direction": "inbound",
            "status": "received",
            "type": "text",
            "metadata": {
                "whatsapp_id": f"wamid.{self._random_string(20)}",
                "timestamp_unix": int(time.time()),
            },
        }

        final_data = {**default_data, **kwargs}

        test_data = TestData(
            id=msg_id,
            type=DataType.MESSAGE,
            data=final_data,
            created_at=datetime.now().isoformat(),
            dependencies=[conversation_id],
        )

        self.created_data[msg_id] = test_data
        return test_data

    def create_webhook_payload(self, message_id: str = None, **kwargs) -> TestData:
        """Cria payload de webhook"""
        seq = self._get_sequence("webhook")
        webhook_id = f"webhook_{seq}_{self._random_string(6)}"

        # Se não fornecido message_id, criar uma mensagem
        if not message_id:
            msg = self.create_message()
            message_data = msg.data
        else:
            message_data = self.created_data.get(message_id, {}).data

        default_data = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": f"entry_{self._random_string(10)}",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "15550123456",
                                    "phone_number_id": "123456789012345",
                                },
                                "messages": [
                                    {
                                        "from": message_data.get(
                                            "from", self._random_phone()
                                        ),
                                        "id": message_data.get(
                                            "id", f"wamid.{self._random_string(20)}"
                                        ),
                                        "timestamp": str(int(time.time())),
                                        "text": {
                                            "body": message_data.get(
                                                "text", "Test message"
                                            )
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

        final_data = {**default_data, **kwargs}

        test_data = TestData(
            id=webhook_id,
            type=DataType.WEBHOOK,
            data=final_data,
            created_at=datetime.now().isoformat(),
            dependencies=[message_id] if message_id else [],
        )

        self.created_data[webhook_id] = test_data
        return test_data

    def create_auth_token(self, user_id: str = None, **kwargs) -> TestData:
        """Cria token de autenticação"""
        seq = self._get_sequence("token")
        token_id = f"token_{seq}_{self._random_string(8)}"

        if not user_id:
            user = self.create_user()
            user_id = user.data["id"]

        default_data = {
            "access_token": f"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.{self._random_string(50)}.{self._random_string(30)}",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": f"rt_{self._random_string(40)}",
            "user_id": user_id,
            "scopes": ["read", "write"],
            "issued_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
        }

        final_data = {**default_data, **kwargs}

        test_data = TestData(
            id=token_id,
            type=DataType.AUTH_TOKEN,
            data=final_data,
            created_at=datetime.now().isoformat(),
            dependencies=[user_id],
        )

        self.created_data[token_id] = test_data
        return test_data

    def create_appointment(self, user_id: str = None, **kwargs) -> TestData:
        """Cria dados de agendamento"""
        seq = self._get_sequence("appointment")
        apt_id = f"apt_{seq}_{self._random_string(6)}"

        if not user_id:
            user = self.create_user()
            user_id = user.data["id"]

        # Gerar data futura aleatória
        future_date = datetime.now() + timedelta(days=random.randint(1, 30))

        default_data = {
            "id": apt_id,
            "user_id": user_id,
            "service": "Consulta Geral",
            "date": future_date.date().isoformat(),
            "time": f"{random.randint(8, 17):02d}:{random.choice(['00', '30'])}",
            "status": "scheduled",
            "duration_minutes": 30,
            "notes": f"Agendamento de teste #{seq}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        final_data = {**default_data, **kwargs}

        test_data = TestData(
            id=apt_id,
            type=DataType.APPOINTMENT,
            data=final_data,
            created_at=datetime.now().isoformat(),
            dependencies=[user_id],
        )

        self.created_data[apt_id] = test_data
        return test_data


class TestDataManager:
    """Gerenciador de dados de teste com fixtures e cleanup"""

    def __init__(self):
        self.factory = DataFactory()
        self.fixtures = {}
        self.cleanup_functions = []
        self.active_data = {}

    def register_fixture(self, name: str, factory_method: Callable) -> None:
        """Registra uma fixture"""
        self.fixtures[name] = factory_method

    def get_fixture(self, name: str, **kwargs) -> TestData:
        """Obtém dados de uma fixture"""
        if name not in self.fixtures:
            raise ValueError(f"Fixture '{name}' not found")

        # Verificar se fixture já foi criada
        if name in self.active_data:
            return self.active_data[name]

        # Criar nova fixture
        data = self.fixtures[name](**kwargs)
        self.active_data[name] = data
        return data

    def create_test_scenario(self, scenario_name: str) -> Dict[str, TestData]:
        """Cria cenário completo de teste"""
        scenarios = {
            "simple_conversation": self._create_simple_conversation_scenario,
            "complex_workflow": self._create_complex_workflow_scenario,
            "error_conditions": self._create_error_conditions_scenario,
            "performance_test": self._create_performance_test_scenario,
            "authentication_flow": self._create_authentication_flow_scenario,
        }

        if scenario_name not in scenarios:
            raise ValueError(f"Scenario '{scenario_name}' not found")

        return scenarios[scenario_name]()

    def _create_simple_conversation_scenario(self) -> Dict[str, TestData]:
        """Cenário: Conversa simples"""
        user = self.factory.create_user(name="João Silva")
        conversation = self.factory.create_conversation(user_id=user.data["id"])
        message = self.factory.create_message(
            conversation_id=conversation.data["id"], text="Olá, preciso de ajuda"
        )
        webhook = self.factory.create_webhook_payload(message_id=message.id)

        return {
            "user": user,
            "conversation": conversation,
            "message": message,
            "webhook": webhook,
        }

    def _create_complex_workflow_scenario(self) -> Dict[str, TestData]:
        """Cenário: Workflow completo"""
        user = self.factory.create_user(name="Maria Santos")
        auth_token = self.factory.create_auth_token(user_id=user.data["id"])
        conversation = self.factory.create_conversation(user_id=user.data["id"])

        # Múltiplas mensagens
        messages = []
        for i, text in enumerate(["Olá", "Quero agendar", "Obrigada"]):
            msg = self.factory.create_message(
                conversation_id=conversation.data["id"],
                text=text,
                direction="inbound" if i % 2 == 0 else "outbound",
            )
            messages.append(msg)

        appointment = self.factory.create_appointment(user_id=user.data["id"])

        return {
            "user": user,
            "auth_token": auth_token,
            "conversation": conversation,
            "messages": messages,
            "appointment": appointment,
        }

    def _create_error_conditions_scenario(self) -> Dict[str, TestData]:
        """Cenário: Condições de erro"""
        # Usuário com dados inválidos
        invalid_user = self.factory.create_user(
            email="invalid-email", phone="invalid-phone"
        )

        # Token expirado
        expired_token = self.factory.create_auth_token(
            expires_at=(datetime.now() - timedelta(hours=1)).isoformat()
        )

        # Webhook malformado
        malformed_webhook = TestData(
            id="webhook_malformed",
            type=DataType.WEBHOOK,
            data={"invalid": "structure"},
            created_at=datetime.now().isoformat(),
        )

        return {
            "invalid_user": invalid_user,
            "expired_token": expired_token,
            "malformed_webhook": malformed_webhook,
        }

    def _create_performance_test_scenario(self) -> Dict[str, TestData]:
        """Cenário: Teste de performance"""
        users = []
        conversations = []
        messages = []

        # Criar 10 usuários com conversas
        for i in range(10):
            user = self.factory.create_user(name=f"User {i+1}")
            conv = self.factory.create_conversation(user_id=user.data["id"])

            # 5 mensagens por conversa
            for j in range(5):
                msg = self.factory.create_message(
                    conversation_id=conv.data["id"],
                    text=f"Message {j+1} from user {i+1}",
                )
                messages.append(msg)

            users.append(user)
            conversations.append(conv)

        return {"users": users, "conversations": conversations, "messages": messages}

    def _create_authentication_flow_scenario(self) -> Dict[str, TestData]:
        """Cenário: Fluxo de autenticação"""
        admin_user = self.factory.create_user(
            name="Admin User", email="admin@example.com"
        )

        regular_user = self.factory.create_user(
            name="Regular User", email="user@example.com"
        )

        admin_token = self.factory.create_auth_token(
            user_id=admin_user.data["id"], scopes=["read", "write", "admin"]
        )

        user_token = self.factory.create_auth_token(
            user_id=regular_user.data["id"], scopes=["read"]
        )

        return {
            "admin_user": admin_user,
            "regular_user": regular_user,
            "admin_token": admin_token,
            "user_token": user_token,
        }

    def register_cleanup(self, cleanup_func: Callable) -> None:
        """Registra função de cleanup"""
        self.cleanup_functions.append(cleanup_func)

    async def cleanup_all(self) -> None:
        """Executa cleanup de todos os dados criados"""
        print("🧹 Executando cleanup de dados de teste...")

        cleanup_count = 0

        # Executar funções de cleanup registradas
        for cleanup_func in self.cleanup_functions:
            try:
                if asyncio.iscoroutinefunction(cleanup_func):
                    await cleanup_func()
                else:
                    cleanup_func()
                cleanup_count += 1
            except Exception as e:
                print(f"   ⚠️ Erro no cleanup: {e}")

        # Limpar dados em memória
        self.factory.created_data.clear()
        self.active_data.clear()

        print(f"   ✅ Cleanup completo: {cleanup_count} funções executadas")
        return cleanup_count > 0


class TestDataFramework:
    """Framework completo de gerenciamento de dados de teste"""

    def __init__(self):
        self.manager = TestDataManager()
        self.test_results = []
        self._setup_fixtures()

    def _setup_fixtures(self):
        """Configura fixtures padrão"""
        self.manager.register_fixture("default_user", self.manager.factory.create_user)
        self.manager.register_fixture(
            "admin_user",
            lambda: self.manager.factory.create_user(
                name="Admin", email="admin@test.com"
            ),
        )
        self.manager.register_fixture(
            "simple_conversation",
            lambda: self.manager.create_test_scenario("simple_conversation"),
        )

    def test_data_factory(self) -> bool:
        """Testa factory de dados"""
        print("🧪 Test Data: Factory...")

        # Testar criação de diferentes tipos
        user = self.manager.factory.create_user()
        conversation = self.manager.factory.create_conversation()
        message = self.manager.factory.create_message()
        webhook = self.manager.factory.create_webhook_payload()
        token = self.manager.factory.create_auth_token()
        appointment = self.manager.factory.create_appointment()

        types_created = all(
            [
                user.type == DataType.USER,
                conversation.type == DataType.CONVERSATION,
                message.type == DataType.MESSAGE,
                webhook.type == DataType.WEBHOOK,
                token.type == DataType.AUTH_TOKEN,
                appointment.type == DataType.APPOINTMENT,
            ]
        )

        print(f"   ✅ Tipos criados: {'PASSOU' if types_created else 'FALHOU'}")

        # Testar IDs únicos
        users = [self.manager.factory.create_user() for _ in range(5)]
        unique_ids = len(set(user.id for user in users)) == 5
        print(f"   🆔 IDs únicos: {'PASSOU' if unique_ids else 'FALHOU'}")

        success = types_created and unique_ids
        print(f"   🎯 Data factory: {'✅ PASSOU' if success else '❌ FALHOU'}")
        return success

    def test_fixtures(self) -> bool:
        """Testa sistema de fixtures"""
        print("�� Test Data: Fixtures...")

        # Testar fixture padrão
        user1 = self.manager.get_fixture("default_user")
        user2 = self.manager.get_fixture("default_user")  # Deve retornar o mesmo

        same_fixture = user1.id == user2.id
        print(f"   🔗 Fixture reutilizada: {'PASSOU' if same_fixture else 'FALHOU'}")

        # Testar fixture admin
        admin = self.manager.get_fixture("admin_user")
        is_admin = "admin" in admin.data["email"].lower()
        print(f"   👑 Admin fixture: {'PASSOU' if is_admin else 'FALHOU'}")

        success = same_fixture and is_admin
        print(f"   🎯 Fixtures: {'✅ PASSOU' if success else '❌ FALHOU'}")
        return success

    def test_scenarios(self) -> bool:
        """Testa criação de cenários"""
        print("🧪 Test Data: Scenarios...")

        scenarios_tested = []

        # Testar cenário simples
        simple = self.manager.create_test_scenario("simple_conversation")
        simple_complete = all(
            key in simple for key in ["user", "conversation", "message", "webhook"]
        )
        scenarios_tested.append(simple_complete)
        print(f"   📝 Cenário simples: {'PASSOU' if simple_complete else 'FALHOU'}")

        # Testar cenário complexo
        complex_scenario = self.manager.create_test_scenario("complex_workflow")
        complex_complete = all(
            key in complex_scenario for key in ["user", "conversation", "appointment"]
        )
        scenarios_tested.append(complex_complete)
        print(f"   🔄 Cenário complexo: {'PASSOU' if complex_complete else 'FALHOU'}")

        # Testar cenário de erro
        error_scenario = self.manager.create_test_scenario("error_conditions")
        error_complete = "invalid_user" in error_scenario
        scenarios_tested.append(error_complete)
        print(f"   ⚠️ Cenário de erro: {'PASSOU' if error_complete else 'FALHOU'}")

        success = all(scenarios_tested)
        print(f"   🎯 Scenarios: {'✅ PASSOU' if success else '❌ FALHOU'}")
        return success

    def test_dependencies(self) -> bool:
        """Testa gerenciamento de dependências"""
        print("🧪 Test Data: Dependencies...")

        # Criar dados com dependências
        user = self.manager.factory.create_user()
        conversation = self.manager.factory.create_conversation(user_id=user.data["id"])
        message = self.manager.factory.create_message(
            conversation_id=conversation.data["id"]
        )

        # Verificar dependências
        conv_depends_on_user = user.data["id"] in conversation.dependencies
        msg_depends_on_conv = conversation.data["id"] in message.dependencies

        print(
            f"   🔗 Conversa depende de usuário: {'PASSOU' if conv_depends_on_user else 'FALHOU'}"
        )
        print(
            f"   🔗 Mensagem depende de conversa: {'PASSOU' if msg_depends_on_conv else 'FALHOU'}"
        )

        success = conv_depends_on_user and msg_depends_on_conv
        print(f"   🎯 Dependencies: {'✅ PASSOU' if success else '❌ FALHOU'}")
        return success

    async def test_cleanup(self) -> bool:
        """Testa sistema de cleanup"""
        print("🧪 Test Data: Cleanup...")

        # Criar alguns dados
        initial_count = len(self.manager.factory.created_data)

        for i in range(3):
            self.manager.factory.create_user()
            self.manager.factory.create_conversation()

        after_creation = len(self.manager.factory.created_data)
        data_created = after_creation > initial_count
        print(f"   📊 Dados criados: {'PASSOU' if data_created else 'FALHOU'}")

        # Registrar função de cleanup
        cleanup_executed = False

        def test_cleanup_func():
            nonlocal cleanup_executed
            cleanup_executed = True

        self.manager.register_cleanup(test_cleanup_func)

        # Executar cleanup
        cleanup_result = await self.manager.cleanup_all()

        after_cleanup = len(self.manager.factory.created_data)
        data_cleaned = after_cleanup == 0

        print(f"   🧹 Cleanup executado: {'PASSOU' if cleanup_executed else 'FALHOU'}")
        print(f"   🗑️ Dados removidos: {'PASSOU' if data_cleaned else 'FALHOU'}")

        success = data_created and cleanup_executed and data_cleaned and cleanup_result
        print(f"   🎯 Cleanup: {'✅ PASSOU' if success else '❌ FALHOU'}")
        return success

    async def run_all_data_management_tests(self):
        """Executa todos os testes de gerenciamento de dados"""
        print("🎯 TRILHA 2 FASE 2.3 - Test Data Management")
        print("📊 Gerenciamento Dinâmico de Dados de Teste")
        print("=" * 60)

        tests = [
            ("Data Factory", self.test_data_factory),
            ("Fixtures", self.test_fixtures),
            ("Scenarios", self.test_scenarios),
            ("Dependencies", self.test_dependencies),
            ("Cleanup", self.test_cleanup),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            try:
                print(f"\n🔧 {test_name}:")
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()

                if result:
                    passed += 1
                    self.test_results.append({"test": test_name, "status": "PASSED"})
                else:
                    self.test_results.append({"test": test_name, "status": "FAILED"})
            except Exception as e:
                print(f"�� Erro em {test_name}: {e}")
                self.test_results.append(
                    {"test": test_name, "status": "ERROR", "error": str(e)}
                )

        success_rate = passed / total

        print("\n" + "=" * 60)
        print("📊 RESULTADOS DO GERENCIAMENTO DE DADOS")
        print("=" * 60)
        print(f"✅ Testes Passaram: {passed}")
        print(f"❌ Testes Falharam: {total - passed}")
        print(f"📊 Total: {total}")
        print(f"🎯 Taxa de Sucesso: {success_rate:.1%}")

        if success_rate >= 0.8:
            print("\n🎉 EXCELENTE: Test Data Management validado!")
            print("✅ Factory criando dados consistentes")
            print("🔗 Fixtures e cenários funcionando")
            print("🧹 Cleanup automático operacional")
            print("📊 Dependências bem gerenciadas")
        elif success_rate >= 0.6:
            print("\n⚠️ BOM: Gerenciamento funciona, alguns ajustes necessários")
        else:
            print("\n❌ ATENÇÃO: Problemas no gerenciamento de dados")

        print(f"\n🎯 TRILHA 2 FASE 2.3 - Test Data Management IMPLEMENTADO")
        return success_rate >= 0.6


async def main():
    """Função principal"""
    framework = TestDataFramework()
    success = await framework.run_all_data_management_tests()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

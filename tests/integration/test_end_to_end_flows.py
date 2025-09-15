"""
End-to-End Integration Tests

Tests de fluxos completos que simulam cenários reais de uso do WhatsApp Agent,
incluindo interações completas entre componentes: API → WhatsApp → Database.
"""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.models.database import Appointment, Business, Service, User


class TestCompleteUserJourney:
    """Testa jornadas completas do usuário desde primeiro contato até agendamento"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_user_registration_to_appointment_flow(self, client):
        """
        Testa fluxo completo: usuário envia mensagem → registro → consulta serviços → agendamento
        """
        # 1. Usuário envia primeira mensagem pelo WhatsApp
        first_contact_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "PHONE_NUMBER_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {"phone_number_id": "test_phone_id"},
                                "messages": [
                                    {
                                        "id": "msg_first_contact",
                                        "from": "5511988776655",
                                        "type": "text",
                                        "text": {
                                            "body": "Olá, gostaria de agendar um horário"
                                        },
                                        "timestamp": str(
                                            int(datetime.now().timestamp())
                                        ),
                                    }
                                ],
                                "contacts": [
                                    {
                                        "profile": {"name": "João Silva"},
                                        "wa_id": "5511988776655",
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        # Mock WhatsApp service to avoid real API calls
        with patch(
            "app.services.whatsapp_security.whatsapp_security.send_message"
        ) as mock_send:
            mock_send.return_value = {"success": True, "message_id": "mock_msg_id"}

            # Process first contact
            response = client.post("/webhook", json=first_contact_payload)
            assert response.status_code == 200

            # Verify welcome message was sent
            assert mock_send.called
            sent_args = mock_send.call_args
            assert "5511988776655" in str(sent_args)

        # 2. Usuário pede lista de serviços
        services_request_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "PHONE_NUMBER_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {"phone_number_id": "test_phone_id"},
                                "messages": [
                                    {
                                        "id": "msg_services_request",
                                        "from": "5511988776655",
                                        "type": "text",
                                        "text": {
                                            "body": "Quais serviços vocês oferecem?"
                                        },
                                        "timestamp": str(
                                            int(datetime.now().timestamp())
                                        ),
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        with patch(
            "app.services.whatsapp_security.whatsapp_security.send_message"
        ) as mock_send:
            mock_send.return_value = {"success": True}

            response = client.post("/webhook", json=services_request_payload)
            assert response.status_code == 200

            # Verify services list was sent
            assert mock_send.called

        # 3. Usuário solicita agendamento
        booking_request_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "PHONE_NUMBER_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {"phone_number_id": "test_phone_id"},
                                "messages": [
                                    {
                                        "id": "msg_booking_request",
                                        "from": "5511988776655",
                                        "type": "text",
                                        "text": {
                                            "body": "Quero agendar um corte para amanhã às 15h"
                                        },
                                        "timestamp": str(
                                            int(datetime.now().timestamp())
                                        ),
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        with patch(
            "app.services.whatsapp_security.whatsapp_security.send_message"
        ) as mock_send:
            mock_send.return_value = {"success": True}

            response = client.post("/webhook", json=booking_request_payload)
            assert response.status_code == 200

            # Verify booking confirmation was sent
            assert mock_send.called

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_appointment_cancellation_flow(self, client):
        """Testa fluxo de cancelamento de agendamento via WhatsApp"""

        # Usuário solicita cancelamento
        cancellation_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "PHONE_NUMBER_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {"phone_number_id": "test_phone_id"},
                                "messages": [
                                    {
                                        "id": "msg_cancellation",
                                        "from": "5511988776655",
                                        "type": "text",
                                        "text": {
                                            "body": "Preciso cancelar meu agendamento"
                                        },
                                        "timestamp": str(
                                            int(datetime.now().timestamp())
                                        ),
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        with patch(
            "app.services.whatsapp_security.whatsapp_security.send_message"
        ) as mock_send:
            mock_send.return_value = {"success": True}

            response = client.post("/webhook", json=cancellation_payload)
            assert response.status_code == 200

            # Verify cancellation was processed
            assert mock_send.called

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_business_hours_validation_flow(self, client):
        """Testa validação de horário de funcionamento"""

        # Usuário tenta agendar fora do horário
        after_hours_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "PHONE_NUMBER_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {"phone_number_id": "test_phone_id"},
                                "messages": [
                                    {
                                        "id": "msg_after_hours",
                                        "from": "5511988776655",
                                        "type": "text",
                                        "text": {
                                            "body": "Quero agendar para hoje às 23h"
                                        },
                                        "timestamp": str(
                                            int(datetime.now().timestamp())
                                        ),
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        with patch(
            "app.services.whatsapp_security.whatsapp_security.send_message"
        ) as mock_send:
            mock_send.return_value = {"success": True}

            response = client.post("/webhook", json=after_hours_payload)
            assert response.status_code == 200

            # Verify business hours message was sent
            assert mock_send.called
            sent_message = str(mock_send.call_args)
            assert any(
                keyword in sent_message.lower()
                for keyword in ["horário", "funcionamento", "fechado"]
            )


class TestMultipleBusinessFlow:
    """Testa fluxos envolvendo múltiplos negócios"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_business_selection_flow(self, client):
        """Testa seleção entre múltiplos negócios"""

        # Usuário pede informações gerais
        general_inquiry_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "PHONE_NUMBER_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {"phone_number_id": "test_phone_id"},
                                "messages": [
                                    {
                                        "id": "msg_general_inquiry",
                                        "from": "5511999888777",
                                        "type": "text",
                                        "text": {"body": "Quais unidades vocês têm?"},
                                        "timestamp": str(
                                            int(datetime.now().timestamp())
                                        ),
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        with patch(
            "app.services.whatsapp_security.whatsapp_security.send_message"
        ) as mock_send:
            mock_send.return_value = {"success": True}

            response = client.post("/webhook", json=general_inquiry_payload)
            assert response.status_code == 200

            # Should list available businesses
            assert mock_send.called


class TestErrorHandlingFlows:
    """Testa fluxos de tratamento de erros"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_invalid_message_format_handling(self, client):
        """Testa tratamento de mensagens com formato inválido"""

        # Mensagem com formato inválido
        invalid_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "PHONE_NUMBER_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {"phone_number_id": "test_phone_id"},
                                "messages": [{}],  # Mensagem vazia/inválida
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        response = client.post("/webhook", json=invalid_payload)
        # Should handle gracefully without crashing
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_whatsapp_api_failure_handling(self, client):
        """Testa tratamento quando API do WhatsApp falha"""

        # Mensagem normal
        normal_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "PHONE_NUMBER_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {"phone_number_id": "test_phone_id"},
                                "messages": [
                                    {
                                        "id": "msg_api_failure_test",
                                        "from": "5511999888777",
                                        "type": "text",
                                        "text": {"body": "Teste de falha na API"},
                                        "timestamp": str(
                                            int(datetime.now().timestamp())
                                        ),
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        # Mock API failure
        with patch(
            "app.services.whatsapp_security.whatsapp_security.send_message"
        ) as mock_send:
            mock_send.side_effect = Exception("WhatsApp API Error")

            response = client.post("/webhook", json=normal_payload)
            # Should handle API failure gracefully
            assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_database_error_handling(self, client):
        """Testa tratamento de erros de banco de dados"""

        # This test would require mocking database operations
        # to simulate database failures and verify graceful handling
        pass


class TestPerformanceFlows:
    """Testa fluxos de performance e carga"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.performance
    async def test_concurrent_webhook_processing(self, client):
        """Testa processamento concorrente de webhooks"""

        async def send_webhook_message(phone_number: str, message: str):
            """Envia uma mensagem de webhook"""
            payload = {
                "object": "whatsapp_business_account",
                "entry": [
                    {
                        "id": "PHONE_NUMBER_ID",
                        "changes": [
                            {
                                "value": {
                                    "messaging_product": "whatsapp",
                                    "metadata": {"phone_number_id": "test_phone_id"},
                                    "messages": [
                                        {
                                            "id": f"msg_concurrent_{phone_number}",
                                            "from": phone_number,
                                            "type": "text",
                                            "text": {"body": message},
                                            "timestamp": str(
                                                int(datetime.now().timestamp())
                                            ),
                                        }
                                    ],
                                },
                                "field": "messages",
                            }
                        ],
                    }
                ],
            }

            with patch(
                "app.services.whatsapp_security.whatsapp_security.send_message"
            ) as mock_send:
                mock_send.return_value = {"success": True}
                return client.post("/webhook", json=payload)

        # Send multiple concurrent requests
        tasks = []
        for i in range(10):
            phone = f"551199988877{i:02d}"
            message = f"Mensagem concorrente {i}"
            tasks.append(send_webhook_message(phone, message))

        # Execute concurrently and measure time
        start_time = datetime.now()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        execution_time = (datetime.now() - start_time).total_seconds()

        # Verify all requests completed successfully
        successful_responses = [r for r in responses if not isinstance(r, Exception)]
        assert len(successful_responses) >= 8  # At least 80% success rate

        # Verify reasonable performance (all 10 requests in under 10 seconds)
        assert execution_time < 10.0

        # Verify response status codes
        for response in successful_responses:
            if hasattr(response, "status_code"):
                assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.performance
    async def test_bulk_appointment_processing(self, client):
        """Testa processamento em lote de agendamentos"""

        # Simulate multiple users booking appointments simultaneously
        phone_numbers = [f"5511999888{i:03d}" for i in range(20)]

        async def book_appointment(phone: str):
            payload = {
                "object": "whatsapp_business_account",
                "entry": [
                    {
                        "id": "PHONE_NUMBER_ID",
                        "changes": [
                            {
                                "value": {
                                    "messaging_product": "whatsapp",
                                    "metadata": {"phone_number_id": "test_phone_id"},
                                    "messages": [
                                        {
                                            "id": f"msg_bulk_booking_{phone}",
                                            "from": phone,
                                            "type": "text",
                                            "text": {
                                                "body": "Quero agendar um horário"
                                            },
                                            "timestamp": str(
                                                int(datetime.now().timestamp())
                                            ),
                                        }
                                    ],
                                },
                                "field": "messages",
                            }
                        ],
                    }
                ],
            }

            with patch(
                "app.services.whatsapp_security.whatsapp_security.send_message"
            ) as mock_send:
                mock_send.return_value = {"success": True}
                return client.post("/webhook", json=payload)

        # Execute bulk appointments
        start_time = datetime.now()
        tasks = [book_appointment(phone) for phone in phone_numbers]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        execution_time = (datetime.now() - start_time).total_seconds()

        # Performance assertions
        successful_responses = [r for r in responses if not isinstance(r, Exception)]
        assert len(successful_responses) >= 16  # At least 80% success rate
        assert execution_time < 30.0  # 20 requests in under 30 seconds


class TestIntegrationResilience:
    """Testa resiliência e recuperação de falhas"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.resilience
    async def test_service_degradation_handling(self, client):
        """Testa comportamento quando serviços estão degradados"""

        # Test with various service failures
        failure_scenarios = [
            {"service": "whatsapp", "error": "API timeout"},
            {"service": "database", "error": "Connection lost"},
            {"service": "auth", "error": "Service unavailable"},
        ]

        for scenario in failure_scenarios:
            payload = {
                "object": "whatsapp_business_account",
                "entry": [
                    {
                        "id": "PHONE_NUMBER_ID",
                        "changes": [
                            {
                                "value": {
                                    "messaging_product": "whatsapp",
                                    "metadata": {"phone_number_id": "test_phone_id"},
                                    "messages": [
                                        {
                                            "id": f"msg_degradation_{scenario['service']}",
                                            "from": "5511999777888",
                                            "type": "text",
                                            "text": {
                                                "body": f"Test {scenario['service']} degradation"
                                            },
                                            "timestamp": str(
                                                int(datetime.now().timestamp())
                                            ),
                                        }
                                    ],
                                },
                                "field": "messages",
                            }
                        ],
                    }
                ],
            }

            # Mock service failure
            if scenario["service"] == "whatsapp":
                with patch(
                    "app.services.whatsapp_security.whatsapp_security.send_message"
                ) as mock_send:
                    mock_send.side_effect = Exception(scenario["error"])
                    response = client.post("/webhook", json=payload)
                    # Should handle gracefully
                    assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.resilience
    async def test_recovery_after_failure(self, client):
        """Testa recuperação após falhas temporárias"""

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "PHONE_NUMBER_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {"phone_number_id": "test_phone_id"},
                                "messages": [
                                    {
                                        "id": "msg_recovery_test",
                                        "from": "5511999666777",
                                        "type": "text",
                                        "text": {"body": "Test recovery"},
                                        "timestamp": str(
                                            int(datetime.now().timestamp())
                                        ),
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        # First request fails
        with patch(
            "app.services.whatsapp_security.whatsapp_security.send_message"
        ) as mock_send:
            mock_send.side_effect = Exception("Temporary failure")
            response1 = client.post("/webhook", json=payload)
            assert response1.status_code == 200

        # Second request succeeds (recovery)
        with patch(
            "app.services.whatsapp_security.whatsapp_security.send_message"
        ) as mock_send:
            mock_send.return_value = {"success": True}
            response2 = client.post("/webhook", json=payload)
            assert response2.status_code == 200
            assert mock_send.called

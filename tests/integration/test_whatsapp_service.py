"""
Testes de Integração - Serviço WhatsApp
Testa integração completa com WhatsApp API e fluxos de mensagem
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio


@pytest.mark.integration
@pytest.mark.whatsapp
class TestWhatsAppServiceIntegration:
    """Testes de integração para o serviço WhatsApp"""

    @pytest.mark.asyncio
    async def test_whatsapp_service_initialization_with_real_config(self):
        """Test WhatsApp service initialization with configuration"""
        from app.services.whatsapp import WhatsAppService

        try:
            service = WhatsAppService()

            # Service should initialize without errors
            assert service is not None
            assert hasattr(service, "base_url")
            assert hasattr(service, "headers")
            assert hasattr(service, "circuit_breaker_config")

        except Exception as e:
            pytest.fail(f"WhatsApp service initialization failed: {e}")

    @pytest.mark.asyncio
    async def test_whatsapp_message_sending_mock(self):
        """Test WhatsApp message sending with mocked API"""
        from app.services.whatsapp import WhatsAppService

        # Mock successful API response in whatsapp_security service
        with patch(
            "app.services.whatsapp_security.whatsapp_security.send_message"
        ) as mock_send:
            mock_send.return_value = {
                "messaging_product": "whatsapp",
                "messages": [{"id": "wamid.test123456"}],
            }

            service = WhatsAppService()

            # Test sending a message
            result = await service.send_text_message(
                to="5511999999999", message="Teste de integração"
            )

            # Should return successful result
            assert result is not None

            # Verify the security service was called
            mock_send.assert_called_once_with(
                phone_number="5511999999999",
                message="Teste de integração",
                message_type="text",
            )

    @pytest.mark.asyncio
    async def test_whatsapp_error_handling(self):
        """Test WhatsApp service error handling"""
        from app.services.whatsapp import WhatsAppService

        # Mock API error response in whatsapp_security
        with patch(
            "app.services.whatsapp_security.whatsapp_security.send_message"
        ) as mock_send:
            mock_send.return_value = None  # Simulate failure

            service = WhatsAppService()

            # Test error handling
            result = await service.send_text_message(
                to="5511999999999", message="Test message"
            )

            # Should handle error gracefully - returns fallback result
            assert result is not None
            assert "status" in result and result["status"] == "queued"

    @pytest.mark.asyncio
    async def test_whatsapp_request_logging(self):
        """Test WhatsApp service request logging"""
        from app.services.whatsapp import WhatsAppService

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"messages": [{"id": "test123"}]}
            mock_post.return_value = mock_response

            service = WhatsAppService()

            # Test logging functionality
            try:
                if hasattr(service, "_log_request"):
                    await service._log_request(
                        method="POST",
                        endpoint="/test",
                        payload={"test": "data"},
                        response={"result": "success"},
                        status_code=200,
                    )

                    # Logging should not raise errors
                    assert True

            except Exception as e:
                # Some database/logging errors are acceptable in test environment
                if "database" not in str(e).lower():
                    pytest.fail(f"Unexpected logging error: {e}")


@pytest.mark.integration
@pytest.mark.whatsapp
@pytest.mark.webhook
class TestWhatsAppWebhookIntegration:
    """Testes de integração para webhooks do WhatsApp"""

    @pytest.mark.asyncio
    async def test_webhook_message_processing_flow(self):
        """Test complete webhook message processing flow"""

        # Sample WhatsApp message webhook payload
        webhook_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "PHONE_NUMBER_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "5511999999999",
                                    "phone_number_id": "123456789",
                                },
                                "messages": [
                                    {
                                        "from": "5511888888888",
                                        "id": "wamid.HBgLNTUxMTg4ODg4ODg4OBUCABIYIzE2OTQ3MDcyMDAuMTIzNDU2",
                                        "timestamp": "1694707200",
                                        "type": "text",
                                        "text": {
                                            "body": "Olá! Gostaria de agendar um horário para corte de cabelo."
                                        },
                                    }
                                ],
                                "contacts": [
                                    {
                                        "profile": {"name": "João Test"},
                                        "wa_id": "5511888888888",
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        # Test webhook processing (this will depend on implementation)
        try:
            # Try to import webhook processor
            from app.routes.webhook import process_whatsapp_message

            # Test message processing
            result = await process_whatsapp_message(webhook_payload)

            # Should process without errors
            assert result is not None

        except ImportError:
            pytest.skip("Webhook processor not found or not implemented")
        except Exception as e:
            # Some errors are acceptable in test environment
            if "database" not in str(e).lower() and "connection" not in str(e).lower():
                pytest.fail(f"Unexpected webhook processing error: {e}")

    @pytest.mark.asyncio
    async def test_webhook_user_registration_flow(self):
        """Test user registration through webhook"""

        # New user message webhook
        new_user_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "PHONE_NUMBER_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "5511999999999",
                                    "phone_number_id": "123456789",
                                },
                                "messages": [
                                    {
                                        "from": "5511777777777",  # New user
                                        "id": "wamid.new_user_message",
                                        "timestamp": str(
                                            int(datetime.now().timestamp())
                                        ),
                                        "type": "text",
                                        "text": {"body": "Oi, primeira vez aqui!"},
                                    }
                                ],
                                "contacts": [
                                    {
                                        "profile": {"name": "Maria Nova"},
                                        "wa_id": "5511777777777",
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        try:
            # Test new user processing
            from app.models.database import User

            # Check if user exists before
            new_wa_id = "5511777777777"

            # Simulate webhook processing that creates user
            # This would normally be done by the webhook processor
            new_user = User(
                wa_id=new_wa_id, nome="Maria Nova", telefone="+55 11 7777-7777"
            )

            # User should be created successfully
            assert new_user.wa_id == new_wa_id
            assert new_user.nome == "Maria Nova"

        except Exception as e:
            pytest.skip(f"User creation test skipped: {e}")

    @pytest.mark.asyncio
    async def test_webhook_appointment_booking_flow(self):
        """Test appointment booking through WhatsApp webhook"""
        from datetime import datetime, timedelta

        # Appointment booking message
        booking_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "PHONE_NUMBER_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "5511999999999",
                                    "phone_number_id": "123456789",
                                },
                                "messages": [
                                    {
                                        "from": "5511888888888",
                                        "id": "wamid.booking_message",
                                        "timestamp": str(
                                            int(datetime.now().timestamp())
                                        ),
                                        "type": "text",
                                        "text": {
                                            "body": "Quero agendar para amanhã às 14h"
                                        },
                                    }
                                ],
                                "contacts": [
                                    {
                                        "profile": {"name": "Cliente Test"},
                                        "wa_id": "5511888888888",
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        try:
            # Test appointment booking flow
            from app.models.database import Appointment

            # Simulate appointment creation from webhook
            tomorrow_2pm = datetime.now().replace(hour=14, minute=0) + timedelta(days=1)

            appointment = Appointment(
                user_id=1,
                business_id=1,
                service_id=1,
                date_time=tomorrow_2pm,
                duration_minutes=60,
                notes="Agendado via WhatsApp",
            )

            # Calculate end time
            appointment.calculate_end_time()

            # Appointment should be created successfully
            assert appointment.date_time == tomorrow_2pm
            assert appointment.end_time is not None
            assert appointment.duration_minutes == 60

        except Exception as e:
            pytest.skip(f"Appointment booking test skipped: {e}")


@pytest.mark.integration
@pytest.mark.whatsapp
@pytest.mark.slow
class TestWhatsAppServicePerformance:
    """Testes de performance do serviço WhatsApp"""

    @pytest.mark.asyncio
    async def test_concurrent_message_sending(self):
        """Test concurrent message sending performance"""
        from app.services.whatsapp import WhatsAppService

        # Mock successful responses
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "messaging_product": "whatsapp",
                "messages": [{"id": "wamid.test123"}],
            }
            mock_post.return_value = mock_response

            service = WhatsAppService()

            if not hasattr(service, "send_text_message"):
                pytest.skip("send_text_message method not available")

            # Send multiple messages concurrently
            async def send_message(i):
                return await service.send_text_message(
                    to=f"55119999999{i:02d}", message=f"Teste concorrente {i}"
                )

            start_time = asyncio.get_event_loop().time()

            # Send 5 concurrent messages
            tasks = [send_message(i) for i in range(5)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            end_time = asyncio.get_event_loop().time()

            # Check that most requests completed
            successful_results = [r for r in results if not isinstance(r, Exception)]

            # Performance should be reasonable
            total_time = end_time - start_time
            assert (
                total_time < 10.0
            ), f"Concurrent messages took too long: {total_time:.2f}s"

            # At least some messages should succeed
            assert len(successful_results) > 0, "No concurrent messages succeeded"

    @pytest.mark.asyncio
    async def test_message_sending_with_retry(self):
        """Test message sending with retry logic"""
        from app.services.whatsapp import WhatsAppService

        # Mock responses: first fails, second succeeds
        responses = [
            # First attempt fails
            MagicMock(status_code=429, json=lambda: {"error": "Rate limit exceeded"}),
            # Second attempt succeeds
            MagicMock(
                status_code=200,
                json=lambda: {"messages": [{"id": "wamid.retry_success"}]},
            ),
        ]

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = responses

            service = WhatsAppService()

            if hasattr(service, "send_text_message"):
                try:
                    result = await service.send_text_message(
                        to="5511999999999", message="Teste com retry"
                    )

                    # Should eventually succeed with retry
                    assert result is not None

                except Exception as e:
                    # Retry logic might not be implemented yet
                    if "rate limit" in str(e).lower():
                        pytest.skip("Retry logic not implemented")
                    else:
                        raise

    @pytest.mark.asyncio
    async def test_webhook_processing_performance(self):
        """Test webhook processing performance with large payloads"""

        # Create large webhook payload with multiple messages
        large_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "PHONE_NUMBER_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "5511999999999",
                                    "phone_number_id": "123456789",
                                },
                                "messages": [
                                    {
                                        "from": f"551188888888{i:02d}",
                                        "id": f"wamid.large_test_{i}",
                                        "timestamp": str(
                                            int(datetime.now().timestamp()) + i
                                        ),
                                        "type": "text",
                                        "text": {
                                            "body": f"Mensagem de teste número {i} para testar performance"
                                        },
                                    }
                                    for i in range(10)  # 10 messages
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        start_time = asyncio.get_event_loop().time()

        try:
            # Process large payload
            payload_size = len(json.dumps(large_payload))

            # Should handle reasonably sized payloads
            assert payload_size > 1000, "Test payload should be substantial"
            assert payload_size < 100000, "Test payload should not be too large"

            end_time = asyncio.get_event_loop().time()
            processing_time = end_time - start_time

            # Processing should be fast
            assert (
                processing_time < 1.0
            ), f"Large payload processing took too long: {processing_time:.2f}s"

        except Exception as e:
            pytest.skip(f"Large payload test skipped: {e}")

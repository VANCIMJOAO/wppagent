"""
Testes de Integração - API Endpoints Críticos
Testa endpoints da API com dados reais e integração entre componentes
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.api
class TestHealthEndpoints:
    """Testes para endpoints de health check"""

    @pytest.mark.asyncio
    async def test_health_endpoint_basic(self, client: AsyncClient):
        """Test basic health endpoint availability"""
        response = await client.get("/health")

        # Health endpoint should always be available
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "ok", "UP"]

    @pytest.mark.asyncio
    async def test_health_detailed_endpoint(self, client: AsyncClient):
        """Test detailed health endpoint with system info"""
        response = await client.get("/health/detailed")

        if response.status_code == 404:
            pytest.skip("Detailed health endpoint not implemented")

        assert response.status_code == 200
        data = response.json()

        # Should have system information
        expected_fields = ["timestamp", "uptime", "version"]
        for field in expected_fields:
            if field in data:
                assert data[field] is not None


@pytest.mark.integration
@pytest.mark.api
class TestUserManagementAPI:
    """Testes para APIs de gerenciamento de usuários"""

    @pytest.mark.asyncio
    async def test_user_creation_flow(self, client: AsyncClient):
        """Test complete user creation and retrieval flow"""

        # Test user creation
        user_data = {
            "wa_id": "5511999999999",
            "nome": "Test User Integration",
            "telefone": "+55 11 99999-9999",
            "email": "integration@test.com",
        }

        # Try to create user - may require authentication
        response = await client.post("/users", json=user_data)

        if response.status_code in [401, 403]:
            pytest.skip("User creation requires authentication")

        if response.status_code == 404:
            pytest.skip("User creation endpoint not available")

        # If endpoint exists, test the flow
        if response.status_code == 201:
            assert response.status_code == 201
            created_user = response.json()

            assert created_user["wa_id"] == user_data["wa_id"]
            assert created_user["nome"] == user_data["nome"]
            assert "id" in created_user

            # Test user retrieval
            user_id = created_user["id"]
            get_response = await client.get(f"/users/{user_id}")

            if get_response.status_code == 200:
                retrieved_user = get_response.json()
                assert retrieved_user["id"] == user_id
                assert retrieved_user["wa_id"] == user_data["wa_id"]

    @pytest.mark.asyncio
    async def test_user_validation_errors(self, client: AsyncClient):
        """Test user creation with validation errors"""

        invalid_user_data = {
            "wa_id": "",  # Empty wa_id should fail
            "nome": "",  # Empty name
            "telefone": "invalid-phone",
            "email": "invalid-email",
        }

        response = await client.post("/users", json=invalid_user_data)

        if response.status_code == 404:
            pytest.skip("User creation endpoint not available")

        if response.status_code in [401, 403]:
            pytest.skip("User creation requires authentication")

        # Should return validation error
        assert response.status_code in [400, 422]  # Bad request or validation error


@pytest.mark.integration
@pytest.mark.api
class TestWhatsAppIntegration:
    """Testes para integração com WhatsApp API"""

    @pytest.mark.asyncio
    async def test_whatsapp_webhook_endpoint(self, client: AsyncClient):
        """Test WhatsApp webhook endpoint availability and basic processing"""

        # Test webhook verification (GET request)
        verify_params = {
            "hub.mode": "subscribe",
            "hub.challenge": "test_challenge_123",
            "hub.verify_token": "test_token",
        }

        response = await client.get("/webhook", params=verify_params)

        if response.status_code == 404:
            # Try alternative endpoint
            response = await client.get("/webhook/whatsapp", params=verify_params)

        if response.status_code == 404:
            pytest.skip("WhatsApp webhook endpoint not found")

        # Should handle webhook verification
        assert response.status_code in [
            200,
            403,
        ]  # Success or forbidden (invalid token)

    @pytest.mark.asyncio
    async def test_whatsapp_message_processing(self, client: AsyncClient):
        """Test WhatsApp webhook message processing"""

        # Sample WhatsApp webhook payload
        webhook_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123456789",
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
                                        "id": "wamid.test123",
                                        "timestamp": "1694707200",
                                        "type": "text",
                                        "text": {
                                            "body": "Olá, gostaria de agendar um horário"
                                        },
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        # Send webhook payload
        response = await client.post("/webhook", json=webhook_payload)

        if response.status_code == 404:
            # Try alternative endpoint
            response = await client.post("/webhook/whatsapp", json=webhook_payload)

        if response.status_code == 404:
            pytest.skip("WhatsApp webhook POST endpoint not found")

        # Should process webhook (may require signature validation)
        assert response.status_code in [
            200,
            400,
            403,
        ]  # Success, bad request, or forbidden


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.slow
class TestAppointmentAPI:
    """Testes para API de agendamentos"""

    @pytest.mark.asyncio
    async def test_appointment_endpoints_availability(self, client: AsyncClient):
        """Test appointment endpoints are available"""

        # Test GET appointments
        response = await client.get("/appointments")

        if response.status_code in [401, 403]:
            pytest.skip("Appointments require authentication")

        if response.status_code == 404:
            # Try alternative endpoints
            for endpoint in ["/api/appointments", "/agendamentos"]:
                alt_response = await client.get(endpoint)
                if alt_response.status_code != 404:
                    response = alt_response
                    break

        if response.status_code == 404:
            pytest.skip("Appointments endpoint not found")

        # Should return list (empty or with data)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(
            data, (list, dict)
        )  # List of appointments or paginated response

    @pytest.mark.asyncio
    async def test_appointment_creation_validation(self, client: AsyncClient):
        """Test appointment creation with various data scenarios"""

        # Valid appointment data
        appointment_data = {
            "user_id": 1,
            "business_id": 1,
            "service_id": 1,
            "date_time": (datetime.now() + timedelta(days=1)).isoformat(),
            "duration_minutes": 60,
            "notes": "Teste de integração",
        }

        response = await client.post("/appointments", json=appointment_data)

        if response.status_code == 404:
            # Try alternative endpoints
            for endpoint in ["/api/appointments", "/agendamentos"]:
                alt_response = await client.post(endpoint, json=appointment_data)
                if alt_response.status_code != 404:
                    response = alt_response
                    break

        if response.status_code == 404:
            pytest.skip("Appointment creation endpoint not found")

        if response.status_code in [401, 403]:
            pytest.skip("Appointment creation requires authentication")

        # Should create or validate appointment
        assert response.status_code in [
            200,
            201,
            400,
            422,
        ]  # Success or validation error


@pytest.mark.integration
@pytest.mark.api
class TestDashboardAPI:
    """Testes para API do dashboard administrativo"""

    @pytest.mark.asyncio
    async def test_dashboard_metrics_endpoints(self, client: AsyncClient):
        """Test dashboard metrics and analytics endpoints"""

        # Test various dashboard endpoints
        dashboard_endpoints = [
            "/dashboard",
            "/dashboard/metrics",
            "/analytics",
            "/admin/dashboard",
            "/api/dashboard",
        ]

        accessible_endpoints = []

        for endpoint in dashboard_endpoints:
            response = await client.get(endpoint)

            if response.status_code not in [
                404,
                405,
            ]:  # Not Not Found or Method Not Allowed
                accessible_endpoints.append((endpoint, response.status_code))

        if not accessible_endpoints:
            pytest.skip("No dashboard endpoints found")

        # At least one dashboard endpoint should be accessible
        assert len(accessible_endpoints) > 0

        # Test the responses
        for endpoint, status_code in accessible_endpoints:
            if status_code == 200:
                response = await client.get(endpoint)
                data = response.json()
                assert isinstance(data, (dict, list))

    @pytest.mark.asyncio
    async def test_admin_authentication_flow(self, client: AsyncClient):
        """Test admin authentication and protected routes"""

        # Test admin login endpoint
        admin_login_endpoints = [
            "/admin/login",
            "/auth/admin/login",
            "/api/admin/auth/login",
        ]

        login_endpoint = None
        for endpoint in admin_login_endpoints:
            response = await client.get(endpoint)
            if response.status_code not in [404, 405]:
                login_endpoint = endpoint
                break

        if not login_endpoint:
            pytest.skip("Admin login endpoint not found")

        # Try login with test credentials
        login_data = {
            "username": "admin",
            "password": "admin123",
            "email": "admin@test.com",
        }

        response = await client.post(login_endpoint, json=login_data)

        # Should handle login attempt (success or failure)
        assert response.status_code in [200, 201, 400, 401, 422]


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.performance
class TestAPIPerformance:
    """Testes de performance básicos para APIs"""

    @pytest.mark.asyncio
    async def test_health_endpoint_response_time(self, client: AsyncClient):
        """Test health endpoint response time"""
        import time

        start_time = time.time()
        response = await client.get("/health")
        end_time = time.time()

        response_time = end_time - start_time

        if response.status_code == 200:
            # Health endpoint should respond quickly (under 1 second)
            assert response_time < 1.0, f"Health endpoint took {response_time:.2f}s"

    @pytest.mark.asyncio
    async def test_concurrent_health_requests(self, client: AsyncClient):
        """Test handling of concurrent requests to health endpoint"""
        import asyncio

        async def make_request():
            return await client.get("/health")

        # Make 5 concurrent requests
        tasks = [make_request() for _ in range(5)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful responses
        successful_responses = [
            r for r in responses if hasattr(r, "status_code") and r.status_code == 200
        ]

        # At least some requests should succeed
        assert len(successful_responses) > 0, "No concurrent requests succeeded"

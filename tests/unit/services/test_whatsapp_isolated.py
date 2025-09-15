"""
Teste isolado do WhatsAppService - TRILHA 2 FASE 2.1
Sem dependências do conftest.py para evitar problemas de importação
Coverage Target: Services 20.33% → 60%
"""

import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../"))


def test_whatsapp_service_initialization():
    """Teste de inicialização do WhatsAppService"""
    with patch("app.services.whatsapp.settings") as mock_settings, patch(
        "app.services.whatsapp.whatsapp_security"
    ), patch("app.services.whatsapp.retry_handler"):

        # Configurar settings mock
        mock_settings.whatsapp_api_url = "https://graph.facebook.com/v18.0"
        mock_settings.whatsapp_phone_id = "123456789"
        mock_settings.meta_access_token = "test_token"

        from app.services.whatsapp import WhatsAppService

        service = WhatsAppService()

        assert service.base_url == "https://graph.facebook.com/v18.0"
        assert service.phone_number_id == "123456789"
        assert service.access_token == "test_token"
        assert service.headers["Authorization"] == "Bearer test_token"
        assert service.headers["Content-Type"] == "application/json"

        # Verificar configuração do circuit breaker
        assert service.circuit_breaker_config.failure_threshold == 3
        assert service.circuit_breaker_config.recovery_timeout == 300

        print("✅ Teste de inicialização WhatsApp Service passou!")


@pytest.mark.asyncio
async def test_whatsapp_send_text_message():
    """Teste de envio de mensagem de texto"""
    with patch("app.services.whatsapp.settings") as mock_settings, patch(
        "app.services.whatsapp.whatsapp_security"
    ) as mock_security, patch("app.services.whatsapp.retry_handler"):

        # Configurar settings mock
        mock_settings.whatsapp_api_url = "https://graph.facebook.com/v18.0"
        mock_settings.whatsapp_phone_id = "123456789"
        mock_settings.meta_access_token = "test_token"

        # Configurar whatsapp_security mock
        mock_security.send_message = AsyncMock(
            return_value={
                "messaging_product": "whatsapp",
                "messages": [{"id": "msg_123"}],
            }
        )

        from app.services.whatsapp import WhatsAppService

        service = WhatsAppService()

        # Teste envio bem-sucedido
        result = await service.send_text_message("5511999999999", "Teste de mensagem")

        assert result is not None
        assert "messages" in result
        mock_security.send_message.assert_called_once_with(
            phone_number="5511999999999",
            message="Teste de mensagem",
            message_type="text",
        )

        print("✅ Teste de envio de mensagem de texto passou!")


@pytest.mark.asyncio
async def test_whatsapp_send_text_message_failure():
    """Teste de falha no envio de mensagem"""
    with patch("app.services.whatsapp.settings") as mock_settings, patch(
        "app.services.whatsapp.whatsapp_security"
    ) as mock_security, patch("app.services.whatsapp.retry_handler"):

        # Configurar settings mock
        mock_settings.whatsapp_api_url = "https://graph.facebook.com/v18.0"
        mock_settings.whatsapp_phone_id = "123456789"
        mock_settings.meta_access_token = "test_token"

        # Configurar whatsapp_security mock para falhar
        mock_security.send_message = AsyncMock(side_effect=Exception("API Error"))

        from app.services.whatsapp import WhatsAppService

        service = WhatsAppService()

        # Teste falha no envio
        result = await service.send_text_message("5511999999999", "Teste de mensagem")

        assert "error" in result
        assert "API Error" in result["error"]

        print("✅ Teste de falha no envio de mensagem passou!")


@pytest.mark.asyncio
async def test_whatsapp_send_interactive_buttons():
    """Teste de envio de botões interativos"""
    with patch("app.services.whatsapp.settings") as mock_settings, patch(
        "app.services.whatsapp.whatsapp_security"
    ), patch("app.services.whatsapp.retry_handler") as mock_retry:

        # Configurar settings mock
        mock_settings.whatsapp_api_url = "https://graph.facebook.com/v18.0"
        mock_settings.whatsapp_phone_id = "123456789"
        mock_settings.meta_access_token = "test_token"

        # Configurar retry handler mock
        mock_retry.execute_with_retry = AsyncMock(
            return_value={
                "messaging_product": "whatsapp",
                "messages": [{"id": "msg_123"}],
            }
        )

        from app.services.whatsapp import WhatsAppService

        service = WhatsAppService()

        # Mock do método _make_api_request
        service._make_api_request = AsyncMock(
            return_value={
                "messaging_product": "whatsapp",
                "messages": [{"id": "msg_123"}],
            }
        )

        buttons = [{"id": "btn_sim", "title": "Sim"}, {"id": "btn_nao", "title": "Não"}]

        result = await service.send_interactive_buttons(
            "5511999999999", "Escolha uma opção:", buttons
        )

        assert result is not None
        assert "messages" in result

        # Verificar se retry foi chamado
        mock_retry.execute_with_retry.assert_called_once()

        print("✅ Teste de envio de botões interativos passou!")


@pytest.mark.asyncio
async def test_whatsapp_download_media():
    """Teste de download de mídia"""
    with patch("app.services.whatsapp.settings") as mock_settings, patch(
        "app.services.whatsapp.whatsapp_security"
    ), patch("app.services.whatsapp.retry_handler"), patch(
        "httpx.AsyncClient"
    ) as mock_client:

        # Configurar settings mock
        mock_settings.whatsapp_api_url = "https://graph.facebook.com/v18.0"
        mock_settings.whatsapp_phone_id = "123456789"
        mock_settings.meta_access_token = "test_token"

        # Configurar httpx mock
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Mock da primeira resposta (obter URL da mídia)
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {"url": "https://example.com/media.jpg"}

        # Mock da segunda resposta (baixar arquivo)
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.content = b"fake_image_data"

        mock_client_instance.get.side_effect = [mock_response1, mock_response2]

        from app.services.whatsapp import WhatsAppService

        service = WhatsAppService()

        result = await service.download_media("media_123")

        assert result == b"fake_image_data"
        assert mock_client_instance.get.call_count == 2

        print("✅ Teste de download de mídia passou!")


@pytest.mark.asyncio
async def test_whatsapp_download_media_failure():
    """Teste de falha no download de mídia"""
    with patch("app.services.whatsapp.settings") as mock_settings, patch(
        "app.services.whatsapp.whatsapp_security"
    ), patch("app.services.whatsapp.retry_handler"), patch(
        "httpx.AsyncClient"
    ) as mock_client:

        # Configurar settings mock
        mock_settings.whatsapp_api_url = "https://graph.facebook.com/v18.0"
        mock_settings.whatsapp_phone_id = "123456789"
        mock_settings.meta_access_token = "test_token"

        # Configurar httpx mock para falhar
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client_instance.get.return_value = mock_response

        from app.services.whatsapp import WhatsAppService

        service = WhatsAppService()

        result = await service.download_media("media_404")

        assert result is None

        print("✅ Teste de falha no download de mídia passou!")


def test_whatsapp_verify_webhook_success():
    """Teste de verificação de webhook bem-sucedida"""
    with patch("app.services.whatsapp.settings") as mock_settings, patch(
        "app.services.whatsapp.whatsapp_security"
    ), patch("app.services.whatsapp.retry_handler"), patch(
        "app.config.config_factory.get_settings"
    ) as mock_get_settings:

        # Configurar settings mock
        mock_settings.whatsapp_api_url = "https://graph.facebook.com/v18.0"
        mock_settings.whatsapp_phone_id = "123456789"
        mock_settings.meta_access_token = "test_token"
        mock_settings.webhook_verify_token = "test_verify_token"

        # Configurar get_settings mock
        mock_config = MagicMock()
        mock_config.webhook_verify_token.get_secret_value.return_value = (
            "test_verify_token"
        )
        mock_get_settings.return_value = mock_config

        from app.services.whatsapp import WhatsAppService

        service = WhatsAppService()

        result = service.verify_webhook("test_verify_token", "challenge_123")

        assert result == "challenge_123"

        print("✅ Teste de verificação de webhook bem-sucedida passou!")


def test_whatsapp_verify_webhook_failure():
    """Teste de falha na verificação de webhook"""
    with patch("app.services.whatsapp.settings") as mock_settings, patch(
        "app.services.whatsapp.whatsapp_security"
    ), patch("app.services.whatsapp.retry_handler"), patch(
        "app.config.config_factory.get_settings"
    ) as mock_get_settings:

        # Configurar settings mock
        mock_settings.whatsapp_api_url = "https://graph.facebook.com/v18.0"
        mock_settings.whatsapp_phone_id = "123456789"
        mock_settings.meta_access_token = "test_token"
        mock_settings.webhook_verify_token = "test_verify_token"

        # Configurar get_settings mock
        mock_config = MagicMock()
        mock_config.webhook_verify_token.get_secret_value.return_value = (
            "test_verify_token"
        )
        mock_get_settings.return_value = mock_config

        from app.services.whatsapp import WhatsAppService

        service = WhatsAppService()

        # Token incorreto
        result = service.verify_webhook("wrong_token", "challenge_123")

        assert result is None

        print("✅ Teste de falha na verificação de webhook passou!")


@pytest.mark.asyncio
async def test_whatsapp_make_api_request():
    """Teste do método _make_api_request"""
    with patch("app.services.whatsapp.settings") as mock_settings, patch(
        "app.services.whatsapp.whatsapp_security"
    ), patch("app.services.whatsapp.retry_handler"), patch(
        "httpx.AsyncClient"
    ) as mock_client:

        # Configurar settings mock
        mock_settings.whatsapp_api_url = "https://graph.facebook.com/v18.0"
        mock_settings.whatsapp_phone_id = "123456789"
        mock_settings.meta_access_token = "test_token"

        # Configurar httpx mock
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_client_instance.post.return_value = mock_response

        from app.services.whatsapp import WhatsAppService

        service = WhatsAppService()

        # Mock do método _log_request para evitar dependência do banco
        service._log_request = AsyncMock()

        payload = {"test": "data"}
        result = await service._make_api_request("https://api.example.com", payload)

        assert result == {"success": True}
        service._log_request.assert_called_once()

        print("✅ Teste do método _make_api_request passou!")


@pytest.mark.asyncio
async def test_whatsapp_make_api_request_errors():
    """Teste de erros no _make_api_request"""
    with patch("app.services.whatsapp.settings") as mock_settings, patch(
        "app.services.whatsapp.whatsapp_security"
    ), patch("app.services.whatsapp.retry_handler"), patch(
        "httpx.AsyncClient"
    ) as mock_client:

        # Configurar settings mock
        mock_settings.whatsapp_api_url = "https://graph.facebook.com/v18.0"
        mock_settings.whatsapp_phone_id = "123456789"
        mock_settings.meta_access_token = "test_token"

        from app.services.whatsapp import WhatsAppService

        service = WhatsAppService()
        service._log_request = AsyncMock()

        # Configurar httpx mock
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Teste erro 401 (não autorizado)
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid token"}
        mock_client_instance.post.return_value = mock_response

        with pytest.raises(Exception, match="Token inválido ou expirado"):
            await service._make_api_request("https://api.example.com", {})

        # Teste erro 429 (rate limit)
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": "Rate limit exceeded"}

        with pytest.raises(Exception, match="Rate limit excedido"):
            await service._make_api_request("https://api.example.com", {})

        # Teste erro 500 (servidor)
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}

        with pytest.raises(Exception, match="Erro na API \\(500\\)"):
            await service._make_api_request("https://api.example.com", {})

        print("✅ Teste de erros no _make_api_request passou!")


@pytest.mark.asyncio
async def test_whatsapp_log_request():
    """Teste do método _log_request"""
    with patch("app.services.whatsapp.settings") as mock_settings, patch(
        "app.services.whatsapp.whatsapp_security"
    ), patch("app.services.whatsapp.retry_handler"), patch(
        "app.services.whatsapp.AsyncSessionLocal"
    ) as mock_session:

        # Configurar settings mock
        mock_settings.whatsapp_api_url = "https://graph.facebook.com/v18.0"
        mock_settings.whatsapp_phone_id = "123456789"
        mock_settings.meta_access_token = "test_token"

        # Configurar session mock
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance

        from app.services.whatsapp import WhatsAppService

        service = WhatsAppService()

        await service._log_request(
            method="POST",
            endpoint="https://api.example.com",
            payload={"test": "data"},
            response={"success": True},
            status_code=200,
        )

        mock_session_instance.add.assert_called_once()
        mock_session_instance.commit.assert_called_once()

        print("✅ Teste do método _log_request passou!")


if __name__ == "__main__":
    print("🧪 Executando testes isolados do WhatsAppService...")

    test_whatsapp_service_initialization()

    # Executar testes assíncronos
    import asyncio

    async def run_async_tests():
        await test_whatsapp_send_text_message()
        await test_whatsapp_send_text_message_failure()
        await test_whatsapp_send_interactive_buttons()
        await test_whatsapp_download_media()
        await test_whatsapp_download_media_failure()
        await test_whatsapp_make_api_request()
        await test_whatsapp_make_api_request_errors()
        await test_whatsapp_log_request()

    asyncio.run(run_async_tests())

    test_whatsapp_verify_webhook_success()
    test_whatsapp_verify_webhook_failure()

    print(
        "\n🎉 Todos os testes do WhatsAppService passaram! Serviço WhatsApp funcionando corretamente."
    )

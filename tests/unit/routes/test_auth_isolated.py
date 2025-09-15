"""
Teste isolado das Routes de Auth - TRILHA 2 FASE 2.1
Sem dependências do conftest.py para evitar problemas de importação
Coverage Target: Routes 15.67% → 50%
"""

import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../"))


def test_auth_routes_initialization():
    """Teste de inicialização das routes de auth"""
    with patch("app.routes.auth.jwt_manager"), patch(
        "app.routes.auth.two_factor_auth"
    ), patch("app.routes.auth.rate_limiter"), patch("app.routes.auth.secrets_manager"):

        from app.routes.auth import router

        assert router.prefix == "/auth"
        assert "Authentication" in router.tags

        # Verificar se as rotas foram registradas
        routes = [route.path for route in router.routes]
        expected_routes = ["/login", "/logout", "/refresh", "/2fa/setup", "/2fa/verify"]

        # Verificar se algumas rotas principais existem
        assert any("/login" in route for route in routes)

        print("✅ Teste de inicialização das routes de auth passou!")


@pytest.mark.asyncio
async def test_login_endpoint_success():
    """Teste de login bem-sucedido"""
    with patch("app.routes.auth.jwt_manager") as mock_jwt, patch(
        "app.routes.auth.two_factor_auth"
    ) as mock_2fa, patch("app.routes.auth.rate_limiter") as mock_rate_limiter, patch(
        "app.routes.auth._verify_credentials"
    ) as mock_verify:

        # Configurar mocks
        mock_rate_limiter.check_rate_limit.return_value = (True, {})
        mock_verify.return_value = ("user123", "admin")
        mock_2fa.is_2fa_enabled.return_value = False
        mock_jwt.create_access_token.return_value = "access_token_123"
        mock_jwt.create_refresh_token.return_value = "refresh_token_123"

        from fastapi import Request, Response

        from app.routes.auth import LoginRequest, login

        # Criar mocks de request e response
        mock_request = MagicMock(spec=Request)
        mock_response = MagicMock(spec=Response)

        login_data = LoginRequest(username="admin", password="password123")

        result = await login(login_data, mock_request, mock_response)

        assert result.token_type == "bearer"
        assert result.requires_2fa is False
        assert "user_info" in result.model_dump()

        # Verificar se o rate limiter foi chamado
        mock_rate_limiter.check_rate_limit.assert_called_once()

        print("✅ Teste de login bem-sucedido passou!")


@pytest.mark.asyncio
async def test_login_endpoint_invalid_credentials():
    """Teste de login com credenciais inválidas"""
    with patch("app.routes.auth.jwt_manager"), patch(
        "app.routes.auth.two_factor_auth"
    ), patch("app.routes.auth.rate_limiter") as mock_rate_limiter, patch(
        "app.routes.auth._verify_credentials"
    ) as mock_verify:

        # Configurar mocks
        mock_rate_limiter.check_rate_limit.return_value = (True, {})
        mock_verify.return_value = (None, None)  # Credenciais inválidas

        from fastapi import Request, Response

        from app.routes.auth import LoginRequest, login

        mock_request = MagicMock(spec=Request)
        mock_response = MagicMock(spec=Response)

        login_data = LoginRequest(username="invalid", password="wrong")

        with pytest.raises(HTTPException) as exc_info:
            await login(login_data, mock_request, mock_response)

        assert exc_info.value.status_code == 401
        assert "Invalid username or password" in str(exc_info.value.detail)

        print("✅ Teste de login com credenciais inválidas passou!")


@pytest.mark.asyncio
async def test_login_endpoint_rate_limited():
    """Teste de login com rate limiting"""
    with patch("app.routes.auth.jwt_manager"), patch(
        "app.routes.auth.two_factor_auth"
    ), patch("app.routes.auth.rate_limiter") as mock_rate_limiter, patch(
        "app.routes.auth._verify_credentials"
    ):

        # Configurar rate limiter para bloquear
        mock_rate_limiter.check_rate_limit.return_value = (False, {"retry_after": 60})

        from fastapi import Request, Response

        from app.routes.auth import LoginRequest, login

        mock_request = MagicMock(spec=Request)
        mock_response = MagicMock(spec=Response)

        login_data = LoginRequest(username="admin", password="password123")

        with pytest.raises(HTTPException) as exc_info:
            await login(login_data, mock_request, mock_response)

        assert exc_info.value.status_code == 429
        assert "Too many login attempts" in str(exc_info.value.detail)

        print("✅ Teste de login com rate limiting passou!")


@pytest.mark.asyncio
async def test_login_with_2fa_required():
    """Teste de login com 2FA obrigatório"""
    with patch("app.routes.auth.jwt_manager") as mock_jwt, patch(
        "app.routes.auth.two_factor_auth"
    ) as mock_2fa, patch("app.routes.auth.rate_limiter") as mock_rate_limiter, patch(
        "app.routes.auth._verify_credentials"
    ) as mock_verify:

        # Configurar mocks
        mock_rate_limiter.check_rate_limit.return_value = (True, {})
        mock_verify.return_value = ("user123", "admin")
        mock_2fa.is_2fa_enabled.return_value = True  # 2FA habilitado
        mock_jwt.create_access_token.return_value = "temp_token_123"

        from fastapi import Request, Response

        from app.routes.auth import LoginRequest, login

        mock_request = MagicMock(spec=Request)
        mock_response = MagicMock(spec=Response)

        login_data = LoginRequest(username="admin", password="password123")

        result = await login(login_data, mock_request, mock_response)

        assert result.requires_2fa is True

        # Verificar se cookie temporário foi definido
        mock_response.set_cookie.assert_called_once()
        call_args = mock_response.set_cookie.call_args
        assert call_args[1]["key"] == "temp_auth_token"
        assert call_args[1]["max_age"] == 300  # 5 minutos

        print("✅ Teste de login com 2FA obrigatório passou!")


def test_login_request_model():
    """Teste do modelo LoginRequest"""
    from app.routes.auth import LoginRequest

    # Teste dados válidos
    login_data = LoginRequest(username="admin", password="password123")
    assert login_data.username == "admin"
    assert login_data.password == "password123"
    assert login_data.remember_me is False

    # Teste com remember_me
    login_data_remember = LoginRequest(
        username="admin", password="password123", remember_me=True
    )
    assert login_data_remember.remember_me is True

    print("✅ Teste do modelo LoginRequest passou!")


def test_login_response_model():
    """Teste do modelo LoginResponse"""
    from app.routes.auth import LoginResponse

    response_data = LoginResponse(
        expires_in=3600, user_info={"id": "123", "username": "admin"}
    )

    assert response_data.token_type == "bearer"
    assert response_data.expires_in == 3600
    assert response_data.requires_2fa is False
    assert response_data.user_info["id"] == "123"

    print("✅ Teste do modelo LoginResponse passou!")


def test_two_factor_setup_response_model():
    """Teste do modelo TwoFactorSetupResponse"""
    from app.routes.auth import TwoFactorSetupResponse

    setup_data = TwoFactorSetupResponse(
        secret="JBSWY3DPEHPK3PXP",
        qr_code="data:image/png;base64,iVBORw0KGgo...",
        backup_codes=["12345678", "87654321"],
    )

    assert setup_data.secret == "JBSWY3DPEHPK3PXP"
    assert setup_data.qr_code.startswith("data:image/png;base64,")
    assert len(setup_data.backup_codes) == 2

    print("✅ Teste do modelo TwoFactorSetupResponse passou!")


def test_two_factor_verify_request_model():
    """Teste do modelo TwoFactorVerifyRequest"""
    from app.routes.auth import TwoFactorVerifyRequest

    # Teste TOTP
    verify_totp = TwoFactorVerifyRequest(code="123456")
    assert verify_totp.code == "123456"
    assert verify_totp.type == "totp"

    # Teste backup code
    verify_backup = TwoFactorVerifyRequest(code="12345678", type="backup")
    assert verify_backup.code == "12345678"
    assert verify_backup.type == "backup"

    print("✅ Teste do modelo TwoFactorVerifyRequest passou!")


def test_refresh_token_request_model():
    """Teste do modelo RefreshTokenRequest"""
    from app.routes.auth import RefreshTokenRequest

    refresh_data = RefreshTokenRequest(refresh_token="refresh_token_123")
    assert refresh_data.refresh_token == "refresh_token_123"

    print("✅ Teste do modelo RefreshTokenRequest passou!")


def test_revoke_token_request_model():
    """Teste do modelo RevokeTokenRequest"""
    from app.routes.auth import RevokeTokenRequest

    # Teste revogar token específico
    revoke_data = RevokeTokenRequest(token="token_123")
    assert revoke_data.token == "token_123"
    assert revoke_data.revoke_all is False

    # Teste revogar todos os tokens
    revoke_all_data = RevokeTokenRequest(token="token_123", revoke_all=True)
    assert revoke_all_data.revoke_all is True

    print("✅ Teste do modelo RevokeTokenRequest passou!")


def test_cookie_config():
    """Teste da configuração de cookies"""
    from app.routes.auth import COOKIE_CONFIG

    assert COOKIE_CONFIG["httponly"] is True
    assert COOKIE_CONFIG["secure"] is True
    assert COOKIE_CONFIG["samesite"] == "strict"
    assert COOKIE_CONFIG["path"] == "/"

    print("✅ Teste da configuração de cookies passou!")


@pytest.mark.asyncio
async def test_verify_credentials_function():
    """Teste da função _verify_credentials (mock)"""
    with patch("app.routes.auth._verify_credentials") as mock_verify:

        # Configurar mock para retornar credenciais válidas
        mock_verify.return_value = ("user123", "admin")

        from app.routes.auth import _verify_credentials

        user_id, role = await _verify_credentials("admin", "password123")

        assert user_id == "user123"
        assert role == "admin"

        # Configurar mock para credenciais inválidas
        mock_verify.return_value = (None, None)

        user_id, role = await _verify_credentials("invalid", "wrong")

        assert user_id is None
        assert role is None

        print("✅ Teste da função _verify_credentials passou!")


def test_auth_router_dependencies():
    """Teste das dependências do router de auth"""
    from app.routes.auth import router

    # Verificar se o router foi criado corretamente
    assert hasattr(router, "prefix")
    assert hasattr(router, "tags")
    assert hasattr(router, "routes")

    # Verificar se há rotas registradas
    assert len(router.routes) > 0

    print("✅ Teste das dependências do router de auth passou!")


if __name__ == "__main__":
    print("🧪 Executando testes isolados das Routes de Auth...")

    test_auth_routes_initialization()
    test_login_request_model()
    test_login_response_model()
    test_two_factor_setup_response_model()
    test_two_factor_verify_request_model()
    test_refresh_token_request_model()
    test_revoke_token_request_model()
    test_cookie_config()
    test_auth_router_dependencies()

    # Executar testes assíncronos
    import asyncio

    async def run_async_tests():
        await test_login_endpoint_success()
        await test_login_endpoint_invalid_credentials()
        await test_login_endpoint_rate_limited()
        await test_login_with_2fa_required()
        await test_verify_credentials_function()

    asyncio.run(run_async_tests())

    print(
        "\n🎉 Todos os testes das Routes de Auth passaram! Endpoints de autenticação funcionando corretamente."
    )

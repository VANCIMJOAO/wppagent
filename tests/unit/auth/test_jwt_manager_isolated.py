"""
Teste isolado do JWT Manager - TRILHA 2 FASE 2.1
Sem dependências do conftest.py para evitar problemas de importação
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import jwt
import pytest
from freezegun import freeze_time

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../"))


def test_jwt_manager_basic_functionality():
    """Teste básico do JWT Manager sem dependências externas"""
    # Import direto do módulo
    from app.auth.jwt_manager import (
        SimpleJWTManager,
        get_current_user_from_token,
        jwt_manager,
    )

    # Test initialization
    manager = SimpleJWTManager()
    assert manager.algorithm == "HS256"
    assert isinstance(manager.secret_key, str)
    assert len(manager.secret_key) > 0

    # Test token creation
    user_id = "test-user-123"
    role = "admin"
    permissions = ["read", "write", "admin"]

    token = manager.create_access_token(user_id, role, permissions)
    assert isinstance(token, str)
    assert len(token) > 50

    # Test token verification
    payload = manager.verify_token(token)
    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["permissions"] == permissions
    assert payload["type"] == "access"

    # Test token info
    info = manager.get_token_info(token)
    assert info["valid"] is True
    assert info["user_id"] == user_id
    assert info["role"] == role
    assert info["permissions"] == permissions

    # Test current user
    user = manager.get_current_user_from_token(token)
    assert user is not None
    assert user["user_id"] == user_id
    assert user["role"] == role

    # Test global function - usar jwt_manager global em vez de instância separada
    global_token = jwt_manager.create_access_token(user_id, role, permissions)
    global_user = get_current_user_from_token(global_token)
    assert global_user is not None
    assert global_user["user_id"] == user_id

    print("✅ Teste básico do JWT Manager passou!")


def test_jwt_manager_refresh_token():
    """Teste do refresh token"""
    from app.auth.jwt_manager import SimpleJWTManager

    manager = SimpleJWTManager()
    user_id = "test-user-refresh"

    refresh_token = manager.create_refresh_token(user_id)
    assert isinstance(refresh_token, str)

    payload = manager.verify_token(refresh_token)
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"

    print("✅ Teste de refresh token passou!")


def test_jwt_manager_expiration():
    """Teste de expiração usando freezegun"""
    from app.auth.jwt_manager import SimpleJWTManager

    manager = SimpleJWTManager()
    user_id = "test-user-exp"

    with freeze_time("2025-09-15 10:00:00"):
        token = manager.create_access_token(user_id)

        # Token válido no mesmo momento
        payload = manager.verify_token(token)
        assert payload["sub"] == user_id

    # Token expirado após 16 minutos
    with freeze_time("2025-09-15 10:16:00"):
        try:
            manager.verify_token(token)
            assert False, "Token deveria estar expirado"
        except jwt.InvalidTokenError as e:
            assert "expirado" in str(e).lower()

    print("✅ Teste de expiração passou!")


def test_jwt_manager_invalid_tokens():
    """Teste de tokens inválidos"""
    from app.auth.jwt_manager import SimpleJWTManager

    manager = SimpleJWTManager()

    invalid_tokens = ["invalid.token.here", "not-a-jwt", "", "a.b", "a.b.c.d.e"]

    for token in invalid_tokens:
        try:
            manager.verify_token(token)
            assert False, f"Token {token} deveria ser inválido"
        except jwt.InvalidTokenError:
            pass  # Esperado

    print("✅ Teste de tokens inválidos passou!")


def test_jwt_manager_edge_cases():
    """Teste de casos extremos"""
    from app.auth.jwt_manager import SimpleJWTManager

    manager = SimpleJWTManager()

    # Token com user_id None - deve falhar na validação
    try:
        token = manager.create_access_token(None)
        manager.verify_token(token)
        assert False, "Token com subject None deveria falhar"
    except jwt.InvalidTokenError:
        pass  # Esperado

    # Token com role user
    token_user = manager.create_access_token("user123", "user")
    payload_user = manager.verify_token(token_user)
    assert payload_user["role"] == "user"
    assert payload_user["permissions"] == ["read"]

    # Token com unicode
    unicode_user = "usuário-测试-🔑"
    token_unicode = manager.create_access_token(unicode_user)
    payload_unicode = manager.verify_token(token_unicode)
    assert payload_unicode["sub"] == unicode_user

    print("✅ Teste de casos extremos passou!")


if __name__ == "__main__":
    print("🧪 Executando testes isolados do JWT Manager...")

    test_jwt_manager_basic_functionality()
    test_jwt_manager_refresh_token()
    test_jwt_manager_expiration()
    test_jwt_manager_invalid_tokens()
    test_jwt_manager_edge_cases()

    print("\n🎉 Todos os testes passaram! JWT Manager funcionando corretamente.")

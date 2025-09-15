"""
Testes expandidos para JWT Manager - TRILHA 2 FASE 2.1
Coverage Target: 38.89% → 80%

Cenários testados:
1. Token generation e validation
2. Token expiration e refresh
3. Token verification e security
4. Edge cases e security scenarios
5. User data extraction e role management
"""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import jwt
import pytest
from freezegun import freeze_time

from app.auth.jwt_manager import (SimpleJWTManager,
                                  get_current_user_from_token, jwt_manager)


class TestSimpleJWTManagerExpanded:
    """Testes expandidos para Simple JWT Manager"""

    @pytest.fixture
    def jwt_manager_instance(self):
        """Fixture do JWT Manager com configuração de teste"""
        with patch.dict(
            os.environ,
            {
                "JWT_SECRET": "test-secret-key-for-jwt-testing-expanded-coverage",
                "SECRET_KEY": "fallback-secret-key",
            },
        ):
            manager = SimpleJWTManager()
            return manager

    @pytest.fixture
    def user_data(self):
        """Dados de usuário para testes"""
        return {
            "user_id": "test-user-123",
            "role": "admin",
            "permissions": ["read", "write", "admin"],
        }

    # === TESTES BÁSICOS ===
    def test_jwt_manager_initialization(self, jwt_manager_instance):
        """Test JWT manager initialization"""
        assert jwt_manager_instance.algorithm == "HS256"
        assert (
            jwt_manager_instance.secret_key
            == "test-secret-key-for-jwt-testing-expanded-coverage"
        )
        assert (
            jwt_manager_instance.access_token_expire.total_seconds() == 15 * 60
        )  # 15 minutes
        assert jwt_manager_instance.refresh_token_expire.days == 30

    def test_jwt_manager_fallback_secret(self):
        """Test JWT manager with fallback secret"""
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {"SECRET_KEY": "fallback-test-secret"}):
                manager = SimpleJWTManager()
                assert manager.secret_key == "fallback-test-secret"

    def test_jwt_manager_default_secret(self):
        """Test JWT manager with default secret"""
        with patch.dict(os.environ, {}, clear=True):
            manager = SimpleJWTManager()
            assert manager.secret_key == "fallback-secret-key"

    def test_create_access_token_basic(self, jwt_manager_instance, user_data):
        """Test basic access token creation"""
        token = jwt_manager_instance.create_access_token(
            user_data["user_id"], user_data["role"], user_data["permissions"]
        )

        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens são longos

        # Verificar se pode ser decodificado
        decoded = jwt.decode(
            token,
            jwt_manager_instance.secret_key,
            algorithms=["HS256"],
            audience="whatsapp-agent-api",
        )
        assert decoded["sub"] == user_data["user_id"]
        assert decoded["role"] == user_data["role"]
        assert decoded["permissions"] == user_data["permissions"]
        assert decoded["type"] == "access"
        assert "jti" in decoded
        assert "iat" in decoded
        assert "exp" in decoded

    def test_create_access_token_defaults(self, jwt_manager_instance):
        """Test access token creation with defaults"""
        token = jwt_manager_instance.create_access_token("user123")

        decoded = jwt.decode(
            token,
            jwt_manager_instance.secret_key,
            algorithms=["HS256"],
            audience="whatsapp-agent-api",
        )
        assert decoded["sub"] == "user123"
        assert decoded["role"] == "admin"
        assert decoded["permissions"] == ["read", "write", "admin"]

    def test_create_access_token_user_role(self, jwt_manager_instance):
        """Test access token creation with user role"""
        token = jwt_manager_instance.create_access_token("user123", "user")

        decoded = jwt.decode(
            token,
            jwt_manager_instance.secret_key,
            algorithms=["HS256"],
            audience="whatsapp-agent-api",
        )
        assert decoded["role"] == "user"
        assert decoded["permissions"] == ["read"]

    def test_create_refresh_token(self, jwt_manager_instance, user_data):
        """Test refresh token creation"""
        token = jwt_manager_instance.create_refresh_token(user_data["user_id"])

        assert isinstance(token, str)
        assert len(token) > 50

        decoded = jwt.decode(
            token,
            jwt_manager_instance.secret_key,
            algorithms=["HS256"],
            audience="whatsapp-agent-api",
        )
        assert decoded["sub"] == user_data["user_id"]
        assert decoded["type"] == "refresh"
        assert "jti" in decoded

    # === TESTES DE VERIFICAÇÃO ===
    def test_verify_token_success(self, jwt_manager_instance, user_data):
        """Test successful token verification"""
        token = jwt_manager_instance.create_access_token(
            user_data["user_id"], user_data["role"], user_data["permissions"]
        )

        result = jwt_manager_instance.verify_token(token)

        assert result is not None
        assert result["sub"] == user_data["user_id"]
        assert result["role"] == user_data["role"]
        assert result["permissions"] == user_data["permissions"]

    def test_verify_token_expired(self, jwt_manager_instance, user_data):
        """Test verification of expired token"""
        with freeze_time("2025-09-15 10:00:00"):
            token = jwt_manager_instance.create_access_token(user_data["user_id"])

        # Avançar tempo além da expiração (15 minutos)
        with freeze_time("2025-09-15 10:20:00"):
            with pytest.raises(jwt.InvalidTokenError, match="Token expirado"):
                jwt_manager_instance.verify_token(token)

    def test_verify_token_invalid_signature(self, jwt_manager_instance, user_data):
        """Test verification of token with invalid signature"""
        token = jwt_manager_instance.create_access_token(user_data["user_id"])

        # Modificar o token (corromper assinatura)
        corrupted_token = token[:-10] + "corrupted!"

        with pytest.raises(jwt.InvalidTokenError):
            jwt_manager_instance.verify_token(corrupted_token)

    def test_verify_token_malformed(self, jwt_manager_instance):
        """Test verification of malformed tokens"""
        malformed_tokens = [
            "not.a.jwt",
            "totally-invalid",
            "",
            "a.b",  # Só 2 partes
            "a.b.c.d.e",  # Muitas partes
        ]

        for token in malformed_tokens:
            with pytest.raises(jwt.InvalidTokenError):
                jwt_manager_instance.verify_token(token)

    # === TESTES DE TOKEN INFO ===
    def test_get_token_info_valid(self, jwt_manager_instance, user_data):
        """Test getting info from valid token"""
        token = jwt_manager_instance.create_access_token(
            user_data["user_id"], user_data["role"], user_data["permissions"]
        )

        info = jwt_manager_instance.get_token_info(token)

        assert info["valid"] is True
        assert info["user_id"] == user_data["user_id"]
        assert info["role"] == user_data["role"]
        assert info["permissions"] == user_data["permissions"]
        assert info["type"] == "access"
        assert "expires_at" in info
        assert "token_id" in info

    def test_get_token_info_invalid(self, jwt_manager_instance):
        """Test getting info from invalid token"""
        info = jwt_manager_instance.get_token_info("invalid-token")

        assert info["valid"] is False
        assert "error" in info

    def test_get_token_info_expired(self, jwt_manager_instance, user_data):
        """Test getting info from expired token"""
        with freeze_time("2025-09-15 10:00:00"):
            token = jwt_manager_instance.create_access_token(user_data["user_id"])

        with freeze_time("2025-09-15 10:20:00"):
            info = jwt_manager_instance.get_token_info(token)

            assert info["valid"] is False
            assert "Token expirado" in info["error"]

    # === TESTES DE CURRENT USER ===
    def test_get_current_user_from_token_success(self, jwt_manager_instance, user_data):
        """Test getting current user from valid token"""
        token = jwt_manager_instance.create_access_token(
            user_data["user_id"], user_data["role"], user_data["permissions"]
        )

        user = jwt_manager_instance.get_current_user_from_token(token)

        assert user is not None
        assert user["id"] == user_data["user_id"]
        assert user["user_id"] == user_data["user_id"]
        assert user["role"] == user_data["role"]
        assert user["permissions"] == user_data["permissions"]

    def test_get_current_user_from_token_invalid(self, jwt_manager_instance):
        """Test getting current user from invalid token"""
        user = jwt_manager_instance.get_current_user_from_token("invalid-token")
        assert user is None

    def test_get_current_user_from_token_expired(self, jwt_manager_instance, user_data):
        """Test getting current user from expired token"""
        with freeze_time("2025-09-15 10:00:00"):
            token = jwt_manager_instance.create_access_token(user_data["user_id"])

        with freeze_time("2025-09-15 10:20:00"):
            user = jwt_manager_instance.get_current_user_from_token(token)
            assert user is None

    # === TESTES DE GLOBAL FUNCTION ===
    def test_global_get_current_user_function(self, user_data):
        """Test global get_current_user_from_token function"""
        token = jwt_manager.create_access_token(
            user_data["user_id"], user_data["role"], user_data["permissions"]
        )

        user = get_current_user_from_token(token)

        assert user is not None
        assert user["user_id"] == user_data["user_id"]

    def test_global_get_current_user_function_invalid(self):
        """Test global function with invalid token"""
        user = get_current_user_from_token("invalid-token")
        assert user is None

    # === TESTES DE EDGE CASES ===
    def test_token_with_unicode_user_id(self, jwt_manager_instance):
        """Test token with unicode characters in user_id"""
        unicode_user_id = "usuário-测试-🔑"
        token = jwt_manager_instance.create_access_token(unicode_user_id)

        result = jwt_manager_instance.verify_token(token)
        assert result["sub"] == unicode_user_id

    def test_token_with_empty_permissions(self, jwt_manager_instance):
        """Test token with empty permissions"""
        token = jwt_manager_instance.create_access_token("user123", "user", [])

        result = jwt_manager_instance.verify_token(token)
        assert result["permissions"] == []

    def test_token_with_long_user_id(self, jwt_manager_instance):
        """Test token with very long user_id"""
        long_user_id = "x" * 1000
        token = jwt_manager_instance.create_access_token(long_user_id)

        result = jwt_manager_instance.verify_token(token)
        assert result["sub"] == long_user_id

    def test_token_with_special_characters(self, jwt_manager_instance):
        """Test token with special characters in role and permissions"""
        special_role = "admin-special!@#$%"
        special_permissions = ["read:*", "write:/api/*", "admin:system.config"]

        token = jwt_manager_instance.create_access_token(
            "user123", special_role, special_permissions
        )

        result = jwt_manager_instance.verify_token(token)
        assert result["role"] == special_role
        assert result["permissions"] == special_permissions

    # === TESTES DE TIMING ===
    def test_token_near_expiration(self, jwt_manager_instance, user_data):
        """Test token validation near expiration"""
        with freeze_time("2025-09-15 10:00:00"):
            token = jwt_manager_instance.create_access_token(user_data["user_id"])

        # 14 minutos e 59 segundos depois (ainda válido)
        with freeze_time("2025-09-15 10:14:59"):
            result = jwt_manager_instance.verify_token(token)
            assert result is not None
            assert result["sub"] == user_data["user_id"]

    def test_refresh_token_expiration(self, jwt_manager_instance, user_data):
        """Test refresh token expiration"""
        with freeze_time("2025-09-15 10:00:00"):
            token = jwt_manager_instance.create_refresh_token(user_data["user_id"])

        # 31 dias depois (expirado)
        with freeze_time("2025-10-16 10:00:00"):
            with pytest.raises(jwt.InvalidTokenError, match="Token expirado"):
                jwt_manager_instance.verify_token(token)

    def test_refresh_token_valid_period(self, jwt_manager_instance, user_data):
        """Test refresh token within valid period"""
        with freeze_time("2025-09-15 10:00:00"):
            token = jwt_manager_instance.create_refresh_token(user_data["user_id"])

        # 29 dias depois (ainda válido)
        with freeze_time("2025-10-14 10:00:00"):
            result = jwt_manager_instance.verify_token(token)
            assert result is not None
            assert result["sub"] == user_data["user_id"]
            assert result["type"] == "refresh"

    # === TESTES DE CONCORRÊNCIA ===
    def test_concurrent_token_creation(self, jwt_manager_instance, user_data):
        """Test concurrent token creation"""
        import threading
        import time

        tokens = []
        errors = []

        def create_token():
            try:
                token = jwt_manager_instance.create_access_token(user_data["user_id"])
                tokens.append(token)
                time.sleep(0.01)  # Simular processamento
            except Exception as e:
                errors.append(e)

        # Executar 10 threads concorrentes
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_token)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verificar resultados
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(tokens) == 10
        assert len(set(tokens)) == 10  # Todos únicos

    def test_token_jti_uniqueness(self, jwt_manager_instance, user_data):
        """Test JTI uniqueness across tokens"""
        tokens = []
        jtis = []

        for _ in range(100):
            token = jwt_manager_instance.create_access_token(user_data["user_id"])
            tokens.append(token)

            decoded = jwt.decode(
                token,
                jwt_manager_instance.secret_key,
                algorithms=["HS256"],
                audience="whatsapp-agent-api",
            )
            jtis.append(decoded["jti"])

        # Verificar se todos JTIs são únicos
        assert len(set(jtis)) == len(jtis), "JTIs are not unique"

    # === TESTES DE PAYLOAD VALIDATION ===
    def test_token_payload_structure(self, jwt_manager_instance, user_data):
        """Test token payload structure compliance"""
        token = jwt_manager_instance.create_access_token(
            user_data["user_id"], user_data["role"], user_data["permissions"]
        )

        decoded = jwt.decode(
            token,
            jwt_manager_instance.secret_key,
            algorithms=["HS256"],
            audience="whatsapp-agent-api",
        )

        # Verificar campos obrigatórios
        required_fields = [
            "sub",
            "role",
            "permissions",
            "type",
            "iat",
            "exp",
            "jti",
            "iss",
            "aud",
        ]
        for field in required_fields:
            assert field in decoded, f"Missing required field: {field}"

        # Verificar tipos
        assert isinstance(decoded["sub"], str)
        assert isinstance(decoded["role"], str)
        assert isinstance(decoded["permissions"], list)
        assert decoded["type"] == "access"
        assert isinstance(decoded["iat"], int)
        assert isinstance(decoded["exp"], int)
        assert isinstance(decoded["jti"], str)
        assert decoded["iss"] == "whatsapp-agent"
        assert decoded["aud"] == "whatsapp-agent-api"

    def test_refresh_token_payload_structure(self, jwt_manager_instance, user_data):
        """Test refresh token payload structure"""
        token = jwt_manager_instance.create_refresh_token(user_data["user_id"])

        decoded = jwt.decode(
            token,
            jwt_manager_instance.secret_key,
            algorithms=["HS256"],
            audience="whatsapp-agent-api",
        )

        # Refresh token tem estrutura mais simples
        required_fields = ["sub", "type", "iat", "exp", "jti"]
        for field in required_fields:
            assert field in decoded, f"Missing required field: {field}"

        assert decoded["type"] == "refresh"
        assert decoded["sub"] == user_data["user_id"]

    # === TESTES DE ERROR HANDLING ===
    def test_verify_token_with_none(self, jwt_manager_instance):
        """Test verify_token with None input"""
        with pytest.raises(jwt.InvalidTokenError):
            jwt_manager_instance.verify_token(None)

    def test_verify_token_with_empty_string(self, jwt_manager_instance):
        """Test verify_token with empty string"""
        with pytest.raises(jwt.InvalidTokenError):
            jwt_manager_instance.verify_token("")

    def test_create_token_with_none_user_id(self, jwt_manager_instance):
        """Test create_access_token with None user_id"""
        # Should handle gracefully or raise appropriate error
        token = jwt_manager_instance.create_access_token(None)

        # Decode without subject validation since None is not valid
        decoded = jwt.decode(
            token,
            jwt_manager_instance.secret_key,
            algorithms=["HS256"],
            audience="whatsapp-agent-api",
            options={"verify_sub": False},  # Skip subject validation
        )
        assert decoded["sub"] is None

    def test_get_current_user_defaults(self, jwt_manager_instance):
        """Test get_current_user with default role and permissions"""
        token = jwt_manager_instance.create_access_token("user123", "user")

        user = jwt_manager_instance.get_current_user_from_token(token)

        assert user["role"] == "user"
        assert user["permissions"] == ["read"]  # Default for user role

    # === TESTES DE INTEGRAÇÃO ===
    def test_full_token_lifecycle(self, jwt_manager_instance, user_data):
        """Test complete token lifecycle"""
        # 1. Create access token
        access_token = jwt_manager_instance.create_access_token(
            user_data["user_id"], user_data["role"], user_data["permissions"]
        )

        # 2. Create refresh token
        refresh_token = jwt_manager_instance.create_refresh_token(user_data["user_id"])

        # 3. Verify access token
        access_payload = jwt_manager_instance.verify_token(access_token)
        assert access_payload["type"] == "access"

        # 4. Verify refresh token
        refresh_payload = jwt_manager_instance.verify_token(refresh_token)
        assert refresh_payload["type"] == "refresh"

        # 5. Get token info
        access_info = jwt_manager_instance.get_token_info(access_token)
        assert access_info["valid"] is True

        # 6. Get current user
        user = jwt_manager_instance.get_current_user_from_token(access_token)
        assert user is not None

        # 7. Test expiration
        with freeze_time("2025-09-15 10:00:00"):
            new_token = jwt_manager_instance.create_access_token(user_data["user_id"])

        with freeze_time("2025-09-15 10:20:00"):
            info = jwt_manager_instance.get_token_info(new_token)
            assert info["valid"] is False

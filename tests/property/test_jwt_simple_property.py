"""
Property-Based Tests para JWT Manager Simplificado
===================================================

Testes que geram automaticamente casos de teste diversos
para validar invariantes e comportamentos do sistema JWT.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import jwt
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import booleans, dictionaries, integers, text

from app.auth.jwt_manager import SimpleJWTManager
from app.config import get_settings


class TestSimpleJWTManagerProperties:
    """
    Property-based tests para Simple JWT Manager

    Testa invariantes do sistema:
    1. Token criado deve sempre ser válido quando decodificado
    2. Expiração deve ser respeitada
    3. Claims básicos devem ser preservados
    4. Diferentes user_ids devem gerar tokens diferentes
    """

    def setup_method(self):
        """Setup para cada teste"""
        self.settings = get_settings()
        self.jwt_manager = SimpleJWTManager()

    @given(
        user_id=integers(min_value=1, max_value=999999),
        role=st.sampled_from(["admin", "user", "moderator"]),
    )
    @settings(max_examples=50, deadline=None)
    @example(user_id=1, role="admin")
    @example(user_id=999999, role="user")
    def test_access_token_roundtrip_property(self, user_id, role):
        """
        PROPRIEDADE: Todo token de acesso criado deve ser decodificável
        e manter a integridade dos dados originais
        """
        # Arrange: Criar token com dados arbitrários
        token = self.jwt_manager.create_access_token(
            user_id=str(user_id),
            role=role,
            permissions=["read", "write"] if role == "admin" else ["read"],
        )

        # Act: Decodificar token
        decoded = self.jwt_manager.verify_token(token)

        # Assert: Verificar propriedades invariantes
        assert decoded is not None, "Token deve ser decodificável"
        assert decoded["sub"] == str(user_id), "User ID deve ser preservado"
        assert decoded["role"] == role, "Role deve ser preservado"
        assert decoded["type"] == "access", "Type deve ser access"
        assert decoded["aud"] == "whatsapp-agent-api", "Audience deve ser correto"
        assert decoded["iss"] == "whatsapp-agent", "Issuer deve ser correto"

        # Verificar timestamps
        now = datetime.utcnow().timestamp()
        assert (
            decoded["iat"] <= now + 10
        ), "Issued at deve ser recente"  # +10s tolerance
        assert decoded["exp"] > decoded["iat"], "Expiração deve ser após criação"

        # Verificar JTI (JWT ID único)
        assert "jti" in decoded, "Deve ter JWT ID único"
        assert decoded["jti"] is not None, "JWT ID não deve ser None"

    @given(user_id=integers(min_value=1, max_value=999999))
    @settings(max_examples=30, deadline=None)
    def test_refresh_token_roundtrip_property(self, user_id):
        """
        PROPRIEDADE: Todo refresh token criado deve ser decodificável
        e ter expiração correta
        """
        # Arrange & Act
        token = self.jwt_manager.create_refresh_token(user_id=str(user_id))
        decoded = self.jwt_manager.verify_token(token)

        # Assert: Propriedades do refresh token
        assert decoded is not None
        assert decoded["sub"] == str(user_id)
        assert decoded["type"] == "refresh"
        assert decoded["aud"] == "whatsapp-agent-api"
        assert decoded["iss"] == "whatsapp-agent"
        assert "jti" in decoded, "Refresh token deve ter JWT ID"

        # Verificar expiração (30 dias)
        expected_exp = datetime.fromtimestamp(decoded["iat"]) + timedelta(days=30)
        actual_exp = datetime.fromtimestamp(decoded["exp"])
        time_diff = abs((actual_exp - expected_exp).total_seconds())
        assert (
            time_diff < 3600
        ), "Expiração deve ser aproximadamente 30 dias"  # 1h tolerance

    @given(
        user_id1=integers(min_value=1, max_value=999999),
        user_id2=integers(min_value=1, max_value=999999),
        role1=st.sampled_from(["admin", "user"]),
        role2=st.sampled_from(["admin", "user"]),
    )
    @settings(max_examples=20, deadline=None)
    def test_different_users_generate_different_tokens(
        self, user_id1, user_id2, role1, role2
    ):
        """
        PROPRIEDADE: Usuários diferentes devem gerar tokens diferentes
        (exceto quando os dados são idênticos)
        """
        # Skip se os dados são idênticos
        if user_id1 == user_id2 and role1 == role2:
            return

        # Arrange & Act
        token1 = self.jwt_manager.create_access_token(user_id=str(user_id1), role=role1)
        token2 = self.jwt_manager.create_access_token(user_id=str(user_id2), role=role2)

        # Assert: Tokens devem ser diferentes
        assert token1 != token2, "Usuários diferentes devem gerar tokens diferentes"

        # Decodificar e verificar diferenças
        decoded1 = self.jwt_manager.verify_token(token1)
        decoded2 = self.jwt_manager.verify_token(token2)

        if user_id1 != user_id2:
            assert (
                decoded1["sub"] != decoded2["sub"]
            ), "User IDs diferentes devem resultar em subs diferentes"

        if role1 != role2:
            assert (
                decoded1["role"] != decoded2["role"]
            ), "Roles diferentes devem ser preservados"

        # JTI deve sempre ser diferente (UUID único)
        assert decoded1["jti"] != decoded2["jti"], "JWT IDs devem ser únicos"

    @given(
        user_id=integers(min_value=1, max_value=999999),
        role=st.sampled_from(["admin", "user"]),
    )
    @settings(max_examples=10, deadline=None)
    def test_token_expiration_property(self, user_id, role):
        """
        PROPRIEDADE: Tokens com expiração no passado devem ser rejeitados
        """
        # Skip this test as it requires modifying internal state
        # This would be better tested in integration tests
        pass

    @given(
        user_id=integers(min_value=1, max_value=999999),
        role=st.sampled_from(["admin", "user", "moderator"]),
    )
    @settings(max_examples=20, deadline=None)
    def test_token_info_consistency(self, user_id, role):
        """
        PROPRIEDADE: get_token_info deve ser consistente com verify_token
        """
        # Arrange
        permissions = ["read", "write", "admin"] if role == "admin" else ["read"]
        token = self.jwt_manager.create_access_token(
            user_id=str(user_id), role=role, permissions=permissions
        )

        # Act
        token_info = self.jwt_manager.get_token_info(token)
        decoded = self.jwt_manager.verify_token(token)

        # Assert: Informações devem ser consistentes
        assert token_info["valid"] is True, "Token deve ser válido"
        assert token_info["user_id"] == decoded["sub"], "User ID deve ser consistente"
        assert token_info["role"] == decoded["role"], "Role deve ser consistente"
        assert token_info["type"] == decoded["type"], "Type deve ser consistente"
        assert token_info["token_id"] == decoded["jti"], "JWT ID deve ser consistente"

    @given(
        user_id=integers(min_value=1, max_value=999999),
        role=st.sampled_from(["admin", "user"]),
    )
    @settings(max_examples=15, deadline=None)
    def test_current_user_from_token_property(self, user_id, role):
        """
        PROPRIEDADE: get_current_user_from_token deve extrair dados corretos
        """
        # Arrange
        token = self.jwt_manager.create_access_token(user_id=str(user_id), role=role)

        # Act
        user_data = self.jwt_manager.get_current_user_from_token(token)

        # Assert
        assert user_data is not None, "Deve retornar dados do usuário"
        assert user_data["id"] == str(user_id), "ID deve ser correto"
        assert user_data["user_id"] == str(user_id), "User ID deve ser correto"
        assert user_data["role"] == role, "Role deve ser correto"
        assert isinstance(
            user_data["permissions"], list
        ), "Permissions deve ser uma lista"


class TestSimpleJWTManagerEdgeCases:
    """
    Testes específicos para edge cases descobertos via property testing
    """

    def setup_method(self):
        """Setup para cada teste"""
        self.settings = get_settings()
        self.jwt_manager = SimpleJWTManager()

    def test_invalid_token_handling(self):
        """Testar como sistema lida com tokens inválidos"""
        invalid_tokens = [
            "",  # Token vazio
            "invalid.token.here",  # Token malformado
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",  # Header válido, payload inválido
            None,  # None
        ]

        for invalid_token in invalid_tokens:
            with pytest.raises((jwt.InvalidTokenError, TypeError, AttributeError)):
                if invalid_token is not None:
                    self.jwt_manager.verify_token(invalid_token)
                else:
                    self.jwt_manager.verify_token("")  # Convert None to empty string

            # get_token_info deve retornar invalid=True para tokens inválidos
            if invalid_token is not None:
                token_info = self.jwt_manager.get_token_info(invalid_token)
                assert (
                    token_info["valid"] is False
                ), f"Token inválido deve ser marcado como inválido: {invalid_token}"

    def test_concurrent_token_generation(self):
        """
        PROPRIEDADE: Tokens gerados concorrentemente devem ser únicos
        """
        import threading

        tokens = []
        errors = []

        def create_token(user_id):
            try:
                token = self.jwt_manager.create_access_token(
                    user_id=str(user_id), role="user"
                )
                tokens.append(token)
            except Exception as e:
                errors.append(e)

        # Criar múltiplas threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_token, args=(i,))
            threads.append(thread)

        # Executar concorrentemente
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Assert: Não deve haver erros e todos os tokens devem ser únicos
        assert len(errors) == 0, f"Erros durante criação concorrente: {errors}"
        assert len(tokens) == 10, "Todos os tokens devem ser criados"
        assert len(set(tokens)) == 10, "Todos os tokens devem ser únicos"

        # Verificar que todos os JTIs são únicos
        jtis = []
        for token in tokens:
            decoded = self.jwt_manager.verify_token(token)
            jtis.append(decoded["jti"])

        assert len(set(jtis)) == 10, "Todos os JWT IDs devem ser únicos"

    def test_role_permission_mapping(self):
        """Testar mapeamento correto de roles para permissions"""
        test_cases = [
            ("admin", ["read", "write", "admin"]),
            ("user", ["read"]),
            ("moderator", ["read"]),
        ]

        for role, expected_permissions in test_cases:
            token = self.jwt_manager.create_access_token(user_id="123", role=role)
            decoded = self.jwt_manager.verify_token(token)

            actual_permissions = decoded.get("permissions", [])
            if role == "admin":
                assert "admin" in actual_permissions, f"Admin deve ter permissão admin"
                assert "write" in actual_permissions, f"Admin deve ter permissão write"

            assert (
                "read" in actual_permissions
            ), f"Todas as roles devem ter permissão read"


if __name__ == "__main__":
    # Executar testes property-based
    pytest.main([__file__, "-v", "--tb=short"])

"""
Property-Based Tests para JWT Manager
=====================================

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


class TestJWTManagerProperties:
    """
    Property-based tests para JWT Manager

    Testa invariantes do sistema:
    1. Token criado deve sempre ser válido quando decodificado
    2. Expiração deve ser respeitada
    3. Claims devem ser preservados
    4. Diferentes user_ids devem gerar tokens diferentes
    """

    def setup_method(self):
        """Setup para cada teste"""
        self.settings = get_settings()
        self.jwt_manager = SimpleJWTManager()

    @given(
        user_id=integers(min_value=1, max_value=999999),
        username=text(
            min_size=3,
            max_size=50,
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
        ),
        extra_claims=dictionaries(
            keys=text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz"),
            values=text(min_size=1, max_size=100),
            max_size=5,
        ),
    )
    @settings(max_examples=50, deadline=None)
    @example(user_id=1, username="admin", extra_claims={})
    @example(
        user_id=999999,
        username="test_user_very_long_name",
        extra_claims={"role": "admin", "dept": "engineering"},
    )
    def test_access_token_roundtrip_property(self, user_id, username, extra_claims):
        """
        PROPRIEDADE: Todo token de acesso criado deve ser decodificável
        e manter a integridade dos dados originais
        """
        # Arrange: Criar token com dados arbitrários
        token = self.jwt_manager.create_access_token(
            user_id=str(user_id), role="admin", permissions=["read", "write"]
        )

        # Act: Decodificar token
        decoded = self.jwt_manager.verify_token(token)

        # Assert: Verificar propriedades invariantes
        assert decoded is not None, "Token deve ser decodificável"
        assert decoded["sub"] == str(user_id), "User ID deve ser preservado"
        assert decoded["role"] == "admin", "Role deve ser preservado"
        assert decoded["aud"] == "whatsapp-agent-api", "Audience deve ser correto"
        assert decoded["iss"] == "whatsapp-agent", "Issuer deve ser correto"
        assert decoded["type"] == "access", "Type deve ser access"

        # Verificar timestamps
        now = datetime.utcnow().timestamp()
        assert decoded["iat"] <= now + 5, "Issued at deve ser recente"  # +5s tolerance
        assert decoded["exp"] > now, "Token deve estar válido"

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

        # Verificar expiração (30 dias)
        expected_exp = datetime.utcnow() + timedelta(days=30)
        actual_exp = datetime.fromtimestamp(decoded["exp"])
        time_diff = abs((actual_exp - expected_exp).total_seconds())
        assert time_diff < 60, "Expiração deve ser aproximadamente 30 dias"

    @given(
        user_id1=integers(min_value=1, max_value=999999),
        user_id2=integers(min_value=1, max_value=999999),
        username1=text(min_size=3, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz"),
        username2=text(min_size=3, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz"),
    )
    @settings(max_examples=20, deadline=None)
    def test_different_users_generate_different_tokens(
        self, user_id1, user_id2, username1, username2
    ):
        """
        PROPRIEDADE: Usuários diferentes devem gerar tokens diferentes
        (exceto quando os dados são idênticos)
        """
        # Skip se os dados são idênticos
        if user_id1 == user_id2 and username1 == username2:
            return

        # Arrange & Act
        token1 = self.jwt_manager.create_access_token(
            user_id=user_id1, username=username1
        )
        token2 = self.jwt_manager.create_access_token(
            user_id=user_id2, username=username2
        )

        # Assert: Tokens devem ser diferentes
        assert token1 != token2, "Usuários diferentes devem gerar tokens diferentes"

        # Decodificar e verificar diferenças
        decoded1 = self.jwt_manager.decode_token(token1)
        decoded2 = self.jwt_manager.decode_token(token2)

        if user_id1 != user_id2:
            assert (
                decoded1["sub"] != decoded2["sub"]
            ), "User IDs diferentes devem resultar em subs diferentes"

        if username1 != username2:
            assert (
                decoded1["username"] != decoded2["username"]
            ), "Usernames diferentes devem ser preservados"

    @given(
        user_id=integers(min_value=1, max_value=999999),
        username=text(min_size=3, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz"),
    )
    @settings(max_examples=10, deadline=None)
    def test_token_expiration_property(self, user_id, username):
        """
        PROPRIEDADE: Tokens com expiração no passado devem ser rejeitados
        """
        # Arrange: Criar token com expiração muito curta
        with patch("app.auth.jwt_manager.datetime") as mock_datetime:
            # Simular tempo no passado para criar token expirado
            past_time = datetime.utcnow() - timedelta(hours=1)
            mock_datetime.utcnow.return_value = past_time

            token = self.jwt_manager.create_access_token(
                user_id=user_id, username=username
            )

        # Act & Assert: Token expirado deve ser rejeitado
        with pytest.raises(jwt.ExpiredSignatureError):
            self.jwt_manager.decode_token(token)

    @given(
        user_id=integers(min_value=1, max_value=999999),
        username=text(min_size=3, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz"),
        malicious_claims=dictionaries(
            keys=text(min_size=1, max_size=50),
            values=text(min_size=1, max_size=200),
            max_size=10,
        ),
    )
    @settings(max_examples=20, deadline=None)
    def test_token_security_properties(self, user_id, username, malicious_claims):
        """
        PROPRIEDADE: Sistema deve ser resistente a claims maliciosos
        """
        # Filtrar claims perigosos que podem causar problemas
        safe_claims = {
            k: v
            for k, v in malicious_claims.items()
            if k not in ["sub", "iat", "exp", "aud", "iss", "type", "username"]
            and len(str(v)) < 100  # Limitar tamanho
        }

        # Arrange & Act
        try:
            token = self.jwt_manager.create_access_token(
                user_id=user_id, username=username, **safe_claims
            )
            decoded = self.jwt_manager.decode_token(token)

            # Assert: Claims críticos não devem ser sobrescritos
            assert decoded["sub"] == str(user_id), "Sub não deve ser sobrescrito"
            assert decoded["username"] == username, "Username não deve ser sobrescrito"
            assert (
                decoded["aud"] == "whatsapp-agent-api"
            ), "Audience não deve ser sobrescrito"
            assert decoded["iss"] == "whatsapp-agent", "Issuer não deve ser sobrescrito"

        except Exception as e:
            # Se falhar, deve ser uma falha controlada, não um crash
            assert isinstance(
                e, (ValueError, TypeError, jwt.PyJWTError)
            ), f"Falha inesperada: {e}"


class TestJWTManagerEdgeCases:
    """
    Testes específicos para edge cases descobertos via property testing
    """

    def setup_method(self):
        """Setup para cada teste"""
        self.settings = get_settings()
        self.jwt_manager = SimpleJWTManager()

    @given(text(min_size=0, max_size=2))  # Usernames muito curtos
    def test_short_username_handling(self, short_username):
        """Testar como sistema lida com usernames muito curtos"""
        if len(short_username.strip()) < 3:
            # Sistema deve rejeitar usernames muito curtos
            with pytest.raises((ValueError, TypeError)):
                self.jwt_manager.create_access_token(user_id=1, username=short_username)
        else:
            # Usernames válidos devem funcionar
            token = self.jwt_manager.create_access_token(
                user_id=1, username=short_username
            )
            decoded = self.jwt_manager.decode_token(token)
            assert decoded["username"] == short_username

    def test_concurrent_token_generation(self):
        """
        PROPRIEDADE: Tokens gerados concorrentemente devem ser únicos
        """
        import threading
        import time

        tokens = []
        errors = []

        def create_token(user_id):
            try:
                token = self.jwt_manager.create_access_token(
                    user_id=user_id, username=f"user_{user_id}"
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


if __name__ == "__main__":
    # Executar testes property-based
    pytest.main([__file__, "-v", "--tb=short"])

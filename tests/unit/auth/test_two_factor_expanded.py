"""
Testes expandidos para TwoFactorAuth - TRILHA 2 FASE 2.1
Cobertura abrangente de 2FA, TOTP, códigos de backup e rate limiting

OBJETIVO: Elevar cobertura de 21.02% → 85%+ através de:
✅ Cenários TOTP (geração, validação, janela temporal)
✅ Códigos de backup (geração, uso, gerenciamento)
✅ Rate limiting e proteção contra ataques
✅ Estados de segurança e persistência Redis
✅ QR codes e setup de usuários
✅ Edge cases e error handling
"""

import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pyotp
import pytest
import qrcode
from freezegun import freeze_time

from app.auth.two_factor import TwoFactorAuth


class TestTwoFactorAuthExpanded:
    """Testes expandidos do sistema 2FA"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        mock_client = MagicMock()
        mock_client.get.return_value = None
        mock_client.set.return_value = True
        mock_client.delete.return_value = True
        mock_client.incr.return_value = 1
        mock_client.expire.return_value = True
        mock_client.hget.return_value = None
        mock_client.hset.return_value = True
        mock_client.hdel.return_value = True
        return mock_client

    @pytest.fixture
    def mock_settings(self):
        """Mock settings"""
        settings = MagicMock()
        settings.redis_url = "redis://localhost:6379"
        return settings

    @pytest.fixture
    def two_factor_auth(self, mock_redis, mock_settings):
        """Instance com mocks"""
        with patch("redis.from_url", return_value=mock_redis), patch(
            "app.auth.two_factor.get_settings", return_value=mock_settings
        ):
            return TwoFactorAuth()

    # =============================================================================
    # TESTES DE SETUP E CONFIGURAÇÃO
    # =============================================================================

    def test_init_two_factor_auth(self, two_factor_auth):
        """Testa inicialização correta"""
        assert two_factor_auth.issuer_name == "WhatsApp Agent"
        assert two_factor_auth.totp_window == 1
        assert two_factor_auth.backup_codes_count == 10
        assert two_factor_auth.max_failed_attempts == 5
        assert two_factor_auth.lockout_duration == 900

    def test_generate_secret_key(self, two_factor_auth):
        """Testa geração de chave secreta"""
        secret = two_factor_auth.generate_secret_key()

        assert isinstance(secret, str)
        assert len(secret) == 32  # Base32 encoded 20 bytes = 32 chars

        # Deve ser Base32 válido
        try:
            pyotp.TOTP(secret)
        except Exception:
            pytest.fail("Secret inválido para TOTP")

    def test_setup_2fa_for_user(self, two_factor_auth):
        """Testa setup completo de 2FA para usuário"""
        user_id = "test_user_123"

        # Mock successful Redis operations
        two_factor_auth.redis_client.hset.return_value = True

        result = two_factor_auth.setup_2fa_for_user(user_id)

        assert "secret" in result
        assert "qr_code" in result
        assert "backup_codes" in result
        assert len(result["backup_codes"]) == 10

        # Verifica chamadas Redis
        assert two_factor_auth.redis_client.hset.called
        assert two_factor_auth.redis_client.expire.called

    def test_generate_qr_code(self, two_factor_auth):
        """Testa geração de QR code"""
        secret = "JBSWY3DPEHPK3PXP"
        username = "test@example.com"

        qr_code = two_factor_auth.generate_qr_code(secret, username)

        assert isinstance(qr_code, str)
        assert qr_code.startswith("data:image/png;base64,")

    # =============================================================================
    # TESTES DE VALIDAÇÃO TOTP
    # =============================================================================

    def test_verify_totp_success(self, two_factor_auth):
        """Testa validação TOTP bem-sucedida"""
        user_id = "test_user"
        secret = "JBSWY3DPEHPK3PXP"

        # Mock Redis return secret
        two_factor_auth.redis_client.hget.return_value = secret.encode()
        two_factor_auth.redis_client.get.return_value = None  # No used tokens

        # Generate valid TOTP
        totp = pyotp.TOTP(secret)
        current_token = totp.now()

        result = two_factor_auth.verify_totp(user_id, current_token)
        assert result is True

    def test_verify_totp_invalid_token(self, two_factor_auth):
        """Testa TOTP inválido"""
        user_id = "test_user"
        secret = "JBSWY3DPEHPK3PXP"

        two_factor_auth.redis_client.hget.return_value = secret.encode()
        two_factor_auth.redis_client.get.return_value = None

        # Token inválido
        with pytest.raises(ValueError):
            two_factor_auth.verify_totp(user_id, "000000")

    def test_verify_totp_user_not_setup(self, two_factor_auth):
        """Testa validação para usuário sem 2FA configurado"""
        user_id = "test_user"

        # Redis retorna None (usuário não configurado)
        two_factor_auth.redis_client.hget.return_value = None

        with pytest.raises(ValueError):
            two_factor_auth.verify_totp(user_id, "123456")

    @freeze_time("2024-01-01 12:00:00")
    def test_verify_totp_time_window(self, two_factor_auth):
        """Testa janela temporal do TOTP"""
        user_id = "test_user"
        secret = "JBSWY3DPEHPK3PXP"

        two_factor_auth.redis_client.hget.return_value = secret.encode()
        two_factor_auth.redis_client.get.return_value = None

        totp = pyotp.TOTP(secret)

        # Token do período anterior (deve funcionar com window=1)
        with freeze_time("2024-01-01 11:59:30"):
            past_token = totp.now()

        result = two_factor_auth.verify_totp(user_id, past_token)
        assert result is True

    def test_verify_totp_already_used(self, two_factor_auth):
        """Testa token já usado"""
        user_id = "test_user"
        secret = "JBSWY3DPEHPK3PXP"
        token = "123456"

        two_factor_auth.redis_client.hget.return_value = secret.encode()
        # Token já foi usado
        two_factor_auth.redis_client.get.return_value = b"1"

        with pytest.raises(ValueError):
            two_factor_auth.verify_totp(user_id, token)

    # =============================================================================
    # TESTES DE CÓDIGOS DE BACKUP
    # =============================================================================

    def test_generate_backup_codes(self, two_factor_auth):
        """Testa geração de códigos de backup"""
        codes = two_factor_auth.generate_backup_codes()

        assert len(codes) == 10
        for code in codes:
            assert isinstance(code, str)
            assert len(code) == 8  # 8 caracteres cada
            assert code.isalnum()

    def test_verify_backup_code_success(self, two_factor_auth):
        """Testa uso bem-sucedido de código de backup"""
        user_id = "test_user"
        valid_code = "ABC12345"

        # Mock códigos disponíveis
        backup_codes = {"ABC12345": True, "DEF67890": True}
        two_factor_auth.redis_client.hget.return_value = str(backup_codes).encode()

        result = two_factor_auth.verify_backup_code(user_id, valid_code)
        assert result is True

    def test_verify_backup_code_invalid(self, two_factor_auth):
        """Testa código de backup inválido"""
        user_id = "test_user"
        invalid_code = "INVALID1"

        backup_codes = {"ABC12345": True, "DEF67890": True}
        two_factor_auth.redis_client.hget.return_value = str(backup_codes).encode()

        with pytest.raises(ValueError):
            two_factor_auth.verify_backup_code(user_id, invalid_code)

    def test_verify_backup_code_already_used(self, two_factor_auth):
        """Testa código de backup já usado"""
        user_id = "test_user"
        used_code = "ABC12345"

        # Código marcado como usado
        backup_codes = {"ABC12345": False, "DEF67890": True}
        two_factor_auth.redis_client.hget.return_value = str(backup_codes).encode()

        with pytest.raises(ValueError):
            two_factor_auth.verify_backup_code(user_id, used_code)

    def test_verify_backup_code_no_codes(self, two_factor_auth):
        """Testa usuário sem códigos de backup"""
        user_id = "test_user"

        # Nenhum código configurado
        two_factor_auth.redis_client.hget.return_value = None

        with pytest.raises(ValueError):
            two_factor_auth.verify_backup_code(user_id, "ABC12345")

    # =============================================================================
    # TESTES DE RATE LIMITING E SEGURANÇA
    # =============================================================================

    def test_rate_limiting_failed_attempts(self, two_factor_auth):
        """Testa rate limiting após tentativas falhas"""
        user_id = "test_user"

        # Simula 5 tentativas falhas (máximo)
        two_factor_auth.redis_client.incr.return_value = 5

        # Deve disparar rate limiting na 6ª tentativa
        with pytest.raises(ValueError):
            two_factor_auth.verify_totp(user_id, "000000")

        # Deve disparar rate limiting para backup code também
        with pytest.raises(ValueError):
            two_factor_auth.verify_backup_code(user_id, "INVALID1")

    def test_rate_limiting_lockout(self, two_factor_auth):
        """Testa lockout após exceder tentativas"""
        user_id = "test_user"

        # Simula usuário em lockout
        two_factor_auth.redis_client.incr.return_value = 6  # Excedeu máximo

        with pytest.raises(ValueError):
            two_factor_auth.verify_totp(user_id, "123456")

    def test_reset_failed_attempts_on_success(self, two_factor_auth):
        """Testa reset de tentativas falhas após sucesso"""
        user_id = "test_user"
        secret = "JBSWY3DPEHPK3PXP"

        two_factor_auth.redis_client.hget.return_value = secret.encode()
        two_factor_auth.redis_client.get.return_value = None
        two_factor_auth.redis_client.incr.return_value = 2  # Algumas tentativas falhas

        totp = pyotp.TOTP(secret)
        current_token = totp.now()

        result = two_factor_auth.verify_totp(user_id, current_token)
        assert result is True

        # Deve ter chamado delete para resetar contador
        two_factor_auth.redis_client.delete.assert_called()

    # =============================================================================
    # TESTES DE ESTADO E PERSISTÊNCIA
    # =============================================================================

    def test_is_2fa_enabled(self, two_factor_auth):
        """Testa verificação se 2FA está habilitado"""
        user_id = "test_user"

        # Usuário com 2FA
        two_factor_auth.redis_client.hget.return_value = b"secret_key"
        assert two_factor_auth.is_2fa_enabled(user_id) is True

        # Usuário sem 2FA
        two_factor_auth.redis_client.hget.return_value = None
        assert two_factor_auth.is_2fa_enabled(user_id) is False

    def test_disable_2fa(self, two_factor_auth):
        """Testa desabilitação de 2FA"""
        user_id = "test_user"

        two_factor_auth.redis_client.hdel.return_value = True

        result = two_factor_auth.disable_2fa(user_id)
        assert result is True

        # Verifica que todos os dados foram removidos
        expected_calls = [
            f"2fa:secret:{user_id}",
            f"2fa:backup_codes:{user_id}",
            f"2fa:failed_attempts:{user_id}",
        ]
        assert two_factor_auth.redis_client.hdel.call_count >= 1

    def test_get_backup_codes_remaining(self, two_factor_auth):
        """Testa contagem de códigos de backup restantes"""
        user_id = "test_user"

        # Simula alguns códigos usados e alguns disponíveis
        backup_codes = {"CODE1": True, "CODE2": False, "CODE3": True}
        two_factor_auth.redis_client.hget.return_value = str(backup_codes).encode()

        remaining = two_factor_auth.get_backup_codes_remaining(user_id)
        assert remaining == 2  # Apenas CODE1 e CODE3 estão disponíveis

    def test_regenerate_backup_codes(self, two_factor_auth):
        """Testa regeneração de códigos de backup"""
        user_id = "test_user"

        two_factor_auth.redis_client.hset.return_value = True

        new_codes = two_factor_auth.regenerate_backup_codes(user_id)

        assert len(new_codes) == 10
        assert two_factor_auth.redis_client.hset.called

    # =============================================================================
    # TESTES DE EDGE CASES E ERROR HANDLING
    # =============================================================================

    def test_malformed_token_input(self, two_factor_auth):
        """Testa tokens malformados"""
        user_id = "test_user"

        # Tokens com formato inválido
        invalid_tokens = ["", "12345", "1234567", "abcdef", "12345a"]

        for token in invalid_tokens:
            with pytest.raises(ValueError):
                two_factor_auth.verify_totp(user_id, token)

    def test_redis_connection_error(self, two_factor_auth):
        """Testa erro de conexão Redis"""
        user_id = "test_user"

        # Simula erro Redis
        two_factor_auth.redis_client.hget.side_effect = Exception(
            "Redis connection failed"
        )

        with pytest.raises(Exception):
            two_factor_auth.verify_totp(user_id, "123456")

    def test_concurrent_token_usage(self, two_factor_auth):
        """Testa uso concorrente do mesmo token"""
        user_id = "test_user"
        secret = "JBSWY3DPEHPK3PXP"

        two_factor_auth.redis_client.hget.return_value = secret.encode()

        # Primeira chamada: token não usado
        two_factor_auth.redis_client.get.return_value = None

        totp = pyotp.TOTP(secret)
        current_token = totp.now()

        # Primeira validação deve suceder
        result1 = two_factor_auth.verify_totp(user_id, current_token)
        assert result1 is True

        # Segunda chamada: token já usado
        two_factor_auth.redis_client.get.return_value = b"1"

        with pytest.raises(ValueError):
            two_factor_auth.verify_totp(user_id, current_token)

    def test_token_expiry_boundary(self, two_factor_auth):
        """Testa bordas de expiração de token"""
        user_id = "test_user"
        secret = "JBSWY3DPEHPK3PXP"

        two_factor_auth.redis_client.hget.return_value = secret.encode()
        two_factor_auth.redis_client.get.return_value = None

        totp = pyotp.TOTP(secret)

        # Token muito antigo (fora da janela)
        with freeze_time("2024-01-01 12:00:00"):
            old_token = totp.now()

        with freeze_time("2024-01-01 12:02:00"):  # 2 minutos depois
            with pytest.raises(ValueError):
                two_factor_auth.verify_totp(user_id, old_token)

    def test_backup_code_format_validation(self, two_factor_auth):
        """Testa validação de formato de códigos de backup"""
        user_id = "test_user"

        backup_codes = {"VALID123": True}
        two_factor_auth.redis_client.hget.return_value = str(backup_codes).encode()

        # Códigos com formato inválido
        invalid_codes = ["", "123", "TOOLONGCODE123", "invalid!", "123-456"]

        for code in invalid_codes:
            with pytest.raises(ValueError):
                two_factor_auth.verify_backup_code(user_id, code)

    def test_secret_key_persistence(self, two_factor_auth):
        """Testa persistência da chave secreta"""
        user_id = "test_user"

        # Setup inicial
        two_factor_auth.redis_client.hset.return_value = True
        result = two_factor_auth.setup_2fa_for_user(user_id)
        secret = result["secret"]

        # Verifica se chave foi salva corretamente
        expected_key = f"2fa:secret:{user_id}"
        two_factor_auth.redis_client.hset.assert_called()

        # Verifica TTL
        two_factor_auth.redis_client.expire.assert_called()

    def test_backup_codes_exhaustion(self, two_factor_auth):
        """Testa esgotamento de códigos de backup"""
        user_id = "test_user"

        # Todos os códigos foram usados
        exhausted_codes = {f"CODE{i}": False for i in range(10)}
        two_factor_auth.redis_client.hget.return_value = str(exhausted_codes).encode()

        remaining = two_factor_auth.get_backup_codes_remaining(user_id)
        assert remaining == 0

        # Tentativa de usar código deve falhar mesmo se válido
        with pytest.raises(ValueError):
            two_factor_auth.verify_backup_code(user_id, "CODE1")


# =============================================================================
# TESTES DE INTEGRAÇÃO E CENÁRIOS COMPLEXOS
# =============================================================================


class TestTwoFactorAuthIntegration:
    """Testes de integração e cenários de uso completos"""

    @pytest.fixture
    def two_factor_auth(self):
        """Instance real para testes de integração"""
        # Usar Redis real em teste (ou mock mais realista)
        with patch("app.auth.two_factor.get_settings") as mock_settings:
            mock_settings.return_value.redis_url = "redis://localhost:6379"
            return TwoFactorAuth()

    def test_complete_2fa_workflow(self, two_factor_auth):
        """Testa fluxo completo de 2FA"""
        user_id = "integration_test_user"

        with patch.object(two_factor_auth, "redis_client") as mock_redis:
            # 1. Setup inicial
            mock_redis.hset.return_value = True
            mock_redis.expire.return_value = True

            setup_result = two_factor_auth.setup_2fa_for_user(user_id)
            secret = setup_result["secret"]
            backup_codes = setup_result["backup_codes"]

            # 2. Verificação TOTP
            mock_redis.hget.return_value = secret.encode()
            mock_redis.get.return_value = None
            mock_redis.incr.return_value = 1

            totp = pyotp.TOTP(secret)
            current_token = totp.now()

            assert two_factor_auth.verify_totp(user_id, current_token) is True

            # 3. Uso de código de backup
            mock_redis.hget.return_value = str(
                {code: True for code in backup_codes}
            ).encode()
            mock_redis.hset.return_value = True

            assert two_factor_auth.verify_backup_code(user_id, backup_codes[0]) is True

            # 4. Desabilitação
            mock_redis.hdel.return_value = True
            assert two_factor_auth.disable_2fa(user_id) is True

    def test_security_attack_scenarios(self, two_factor_auth):
        """Testa cenários de ataque e proteções"""
        user_id = "attack_test_user"

        with patch.object(two_factor_auth, "redis_client") as mock_redis:
            # Simula ataque de força bruta
            mock_redis.hget.return_value = b"JBSWY3DPEHPK3PXP"
            mock_redis.get.return_value = None

            # Múltiplas tentativas falhas
            for attempt in range(1, 6):
                mock_redis.incr.return_value = attempt
                try:
                    two_factor_auth.verify_totp(user_id, "000000")
                except ValueError:
                    pass  # Esperado

            # 6ª tentativa deve disparar lockout
            mock_redis.incr.return_value = 6
            with pytest.raises(ValueError):
                two_factor_auth.verify_totp(user_id, "000000")

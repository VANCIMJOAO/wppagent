"""
Teste isolado do TwoFactorAuth - TRILHA 2 FASE 2.1
Sem dependências do conftest.py para evitar problemas de importação
Coverage Target: 21.02% → 80%
"""

import json
import os
import sys
import time
from unittest.mock import MagicMock, patch

import pyotp
import pytest
from freezegun import freeze_time

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../"))


def test_two_factor_basic_functionality():
    """Teste básico do TwoFactorAuth"""
    # Mock do Redis e settings para evitar dependências
    with patch("redis.from_url") as mock_redis_from_url, patch(
        "app.auth.two_factor.get_settings"
    ) as mock_settings:
        # Configurar mocks
        mock_redis = MagicMock()
        mock_redis_from_url.return_value = mock_redis
        mock_settings_obj = MagicMock()
        mock_settings_obj.redis_url = "redis://localhost:6379/0"
        mock_settings_obj.secret_key.get_secret_value.return_value = "test-secret-key"
        mock_settings.return_value = mock_settings_obj

        from app.auth.two_factor import TwoFactorAuth

        # Test initialization
        two_fa = TwoFactorAuth()
        assert two_fa.issuer_name == "WhatsApp Agent"
        assert two_fa.totp_window == 1
        assert two_fa.backup_codes_count == 10
        assert two_fa.max_failed_attempts == 5
        assert two_fa.lockout_duration == 900

        print("✅ Teste básico de inicialização passou!")


def test_two_factor_secret_generation():
    """Teste de geração de secret"""
    with patch("redis.from_url") as mock_redis_from_url, patch(
        "app.auth.two_factor.get_settings"
    ) as mock_settings:
        mock_redis = MagicMock()
        mock_redis_from_url.return_value = mock_redis
        mock_settings_obj = MagicMock()
        mock_settings_obj.redis_url = "redis://localhost:6379/0"
        mock_settings_obj.secret_key.get_secret_value.return_value = "test-secret-key"
        mock_settings.return_value = mock_settings_obj

        from app.auth.two_factor import TwoFactorAuth

        two_fa = TwoFactorAuth()
        user_id = "test-user-123"

        # Gerar secret
        secret = two_fa.generate_secret(user_id)

        assert isinstance(secret, str)
        assert len(secret) == 32  # Base32 secret padrão

        # Verificar se foi salvo no Redis
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == f"2fa:secret:{user_id}"
        assert call_args[0][1] == 3600  # 1 hora

        # Verificar estrutura dos dados salvos
        saved_data = json.loads(call_args[0][2])
        assert saved_data["secret"] == secret
        assert saved_data["confirmed"] is False
        assert "created_at" in saved_data

        print("✅ Teste de geração de secret passou!")


def test_two_factor_qr_code_generation():
    """Teste de geração de QR Code"""
    with patch("redis.from_url") as mock_redis_from_url, patch(
        "app.auth.two_factor.get_settings"
    ) as mock_settings:
        mock_redis = MagicMock()
        mock_redis_from_url.return_value = mock_redis
        mock_settings_obj = MagicMock()
        mock_settings_obj.redis_url = "redis://localhost:6379/0"
        mock_settings_obj.secret_key.get_secret_value.return_value = "test-secret-key"
        mock_settings.return_value = mock_settings_obj

        from app.auth.two_factor import TwoFactorAuth

        two_fa = TwoFactorAuth()

        user_id = "test-user-123"
        user_email = "test@example.com"
        secret = "JBSWY3DPEHPK3PXP"  # Secret base32 válido

        # Gerar QR Code
        qr_data = two_fa.generate_qr_code(user_id, user_email, secret)

        assert isinstance(qr_data, str)
        assert qr_data.startswith("data:image/png;base64,")
        assert len(qr_data) > 100  # QR Code base64 é grande

        print("✅ Teste de geração de QR Code passou!")


def test_two_factor_totp_verification():
    """Teste de verificação TOTP"""
    with patch("redis.from_url") as mock_redis_from_url, patch(
        "app.auth.two_factor.get_settings"
    ) as mock_settings:
        mock_redis = MagicMock()
        mock_redis_from_url.return_value = mock_redis
        mock_settings_obj = MagicMock()
        mock_settings_obj.redis_url = "redis://localhost:6379/0"
        mock_settings_obj.secret_key.get_secret_value.return_value = "test-secret-key"
        mock_settings.return_value = mock_settings_obj

        from app.auth.two_factor import TwoFactorAuth

        two_fa = TwoFactorAuth()
        user_id = "test-user-totp"
        secret = "JBSWY3DPEHPK3PXP"

        # Mock user 2FA data
        user_2fa_data = {
            "secret": secret,
            "enabled": True,
            "backup_codes": [],
            "failed_attempts": 0,
        }

        # Configurar Redis mock para retornar dados do usuário
        mock_redis.get.return_value = json.dumps(user_2fa_data).encode()
        mock_redis.exists.return_value = False  # Não está bloqueado

        # Gerar código TOTP válido
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()

        # Verificar código válido
        result = two_fa.verify_totp(user_id, valid_code)
        assert result is True

        # Verificar código inválido
        invalid_result = two_fa.verify_totp(user_id, "000000")
        assert invalid_result is False

        print("✅ Teste de verificação TOTP passou!")


def test_two_factor_backup_codes():
    """Teste de códigos de backup"""
    with patch("redis.from_url") as mock_redis_from_url, patch(
        "app.auth.two_factor.get_settings"
    ) as mock_settings:
        mock_redis = MagicMock()
        mock_redis_from_url.return_value = mock_redis
        mock_settings_obj = MagicMock()
        mock_settings_obj.redis_url = "redis://localhost:6379/0"
        mock_settings_obj.secret_key.get_secret_value.return_value = "test-secret-key"
        mock_settings.return_value = mock_settings_obj

        from app.auth.two_factor import TwoFactorAuth

        two_fa = TwoFactorAuth()
        user_id = "test-user-backup"

        # Gerar códigos de backup
        backup_codes = two_fa._generate_backup_codes()

        assert len(backup_codes) == 10
        for code in backup_codes:
            assert len(code) == 8
            assert code.isdigit()

        # Verificar que códigos são únicos
        assert len(set(backup_codes)) == len(backup_codes)

        print("✅ Teste de códigos de backup passou!")


def test_two_factor_setup_confirmation():
    """Teste de confirmação de setup 2FA"""
    with patch("redis.from_url") as mock_redis_from_url, patch(
        "app.auth.two_factor.get_settings"
    ) as mock_settings:
        mock_redis = MagicMock()
        mock_redis_from_url.return_value = mock_redis
        mock_settings_obj = MagicMock()
        mock_settings_obj.redis_url = "redis://localhost:6379/0"
        mock_settings_obj.secret_key.get_secret_value.return_value = "test-secret-key"
        mock_settings.return_value = mock_settings_obj

        from app.auth.two_factor import TwoFactorAuth

        two_fa = TwoFactorAuth()
        user_id = "test-user-setup"
        secret = "JBSWY3DPEHPK3PXP"

        # Mock secret temporário
        secret_data = {
            "secret": secret,
            "created_at": "2025-09-15T10:00:00Z",
            "confirmed": False,
        }

        mock_redis.get.return_value = json.dumps(secret_data).encode()

        # Gerar código TOTP válido
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()

        # Confirmar setup
        success, backup_codes = two_fa.confirm_2fa_setup(user_id, valid_code)

        assert success is True
        assert len(backup_codes) == 10

        # Verificar se dados permanentes foram salvos
        mock_redis.set.assert_called()
        # Verificar se secret temporário foi removido
        mock_redis.delete.assert_called_with(f"2fa:secret:{user_id}")

        print("✅ Teste de confirmação de setup passou!")


def test_two_factor_user_lockout():
    """Teste de bloqueio por tentativas falhadas"""
    with patch("redis.from_url") as mock_redis_from_url, patch(
        "app.auth.two_factor.get_settings"
    ) as mock_settings:
        mock_redis = MagicMock()
        mock_redis_from_url.return_value = mock_redis
        mock_settings_obj = MagicMock()
        mock_settings_obj.redis_url = "redis://localhost:6379/0"
        mock_settings_obj.secret_key.get_secret_value.return_value = "test-secret-key"
        mock_settings.return_value = mock_settings_obj

        from app.auth.two_factor import TwoFactorAuth

        two_fa = TwoFactorAuth()
        user_id = "test-user-lockout"

        # Verificar usuário não bloqueado inicialmente
        mock_redis.exists.return_value = False
        assert not two_fa._is_user_locked(user_id)

        # Verificar usuário bloqueado
        mock_redis.exists.return_value = True
        assert two_fa._is_user_locked(user_id)

        print("✅ Teste de bloqueio de usuário passou!")


def test_two_factor_status_check():
    """Teste de verificação de status 2FA"""
    with patch("redis.from_url") as mock_redis_from_url, patch(
        "app.auth.two_factor.get_settings"
    ) as mock_settings:
        mock_redis = MagicMock()
        mock_redis_from_url.return_value = mock_redis
        mock_settings_obj = MagicMock()
        mock_settings_obj.redis_url = "redis://localhost:6379/0"
        mock_settings_obj.secret_key.get_secret_value.return_value = "test-secret-key"
        mock_settings.return_value = mock_settings_obj

        from app.auth.two_factor import TwoFactorAuth

        two_fa = TwoFactorAuth()
        user_id = "test-user-status"

        # Teste usuário sem 2FA
        mock_redis.get.return_value = None
        status = two_fa.get_2fa_status(user_id)

        assert status["enabled"] is False
        assert status["setup_required"] is True

        # Teste usuário com 2FA habilitado
        user_2fa_data = {
            "enabled": True,
            "confirmed_at": "2025-09-15T10:00:00Z",
            "backup_codes": ["hash1", "hash2", "hash3"],
            "failed_attempts": 0,
        }

        mock_redis.get.return_value = json.dumps(user_2fa_data).encode()
        mock_redis.exists.return_value = False  # Não bloqueado

        status = two_fa.get_2fa_status(user_id)

        assert status["enabled"] is True
        assert status["setup_required"] is False
        assert status["backup_codes_count"] == 3
        assert status["failed_attempts"] == 0
        assert status["locked"] is False

        print("✅ Teste de verificação de status passou!")


def test_two_factor_edge_cases():
    """Teste de casos extremos"""
    with patch("redis.from_url") as mock_redis_from_url, patch(
        "app.auth.two_factor.get_settings"
    ) as mock_settings:
        mock_redis = MagicMock()
        mock_redis_from_url.return_value = mock_redis
        mock_settings_obj = MagicMock()
        mock_settings_obj.redis_url = "redis://localhost:6379/0"
        mock_settings_obj.secret_key.get_secret_value.return_value = "test-secret-key"
        mock_settings.return_value = mock_settings_obj

        from app.auth.two_factor import TwoFactorAuth

        two_fa = TwoFactorAuth()

        # Teste verificação TOTP sem dados de usuário
        mock_redis.get.return_value = None
        result = two_fa.verify_totp("nonexistent-user", "123456")
        assert result is False

        # Teste confirmação setup sem secret temporário
        mock_redis.get.return_value = None
        success, codes = two_fa.confirm_2fa_setup("nonexistent-user", "123456")
        assert success is False
        assert codes == []

        # Teste disable 2FA
        mock_redis.exists.return_value = True
        result = two_fa.disable_2fa("test-user")
        mock_redis.delete.assert_called_with("2fa:user:test-user")

        # Teste disable 2FA usuário inexistente
        mock_redis.exists.return_value = False
        result = two_fa.disable_2fa("nonexistent-user")
        assert result is False

        print("✅ Teste de casos extremos passou!")


def test_two_factor_backup_code_verification():
    """Teste de verificação de códigos de backup"""
    with patch("redis.from_url") as mock_redis_from_url, patch(
        "app.auth.two_factor.get_settings"
    ) as mock_settings:
        mock_redis = MagicMock()
        mock_redis_from_url.return_value = mock_redis
        mock_settings_obj = MagicMock()
        mock_settings_obj.redis_url = "redis://localhost:6379/0"
        mock_settings_obj.secret_key.get_secret_value.return_value = "test-secret-key"
        mock_settings.return_value = mock_settings_obj

        from app.auth.two_factor import TwoFactorAuth

        two_fa = TwoFactorAuth()
        user_id = "test-user-backup-verify"
        backup_code = "12345678"

        # Hash do código de backup
        hashed_code = two_fa._hash_backup_code(backup_code)

        # Mock user 2FA data com código de backup
        user_2fa_data = {
            "secret": "JBSWY3DPEHPK3PXP",
            "enabled": True,
            "backup_codes": [hashed_code, "other_hash"],
            "failed_attempts": 0,
        }

        mock_redis.get.return_value = json.dumps(user_2fa_data).encode()
        mock_redis.exists.return_value = False  # Não está bloqueado

        # Verificar código válido
        result = two_fa.verify_backup_code(user_id, backup_code)
        assert result is True

        # Verificar se código foi removido (só pode ser usado uma vez)
        mock_redis.set.assert_called()

        # Verificar código inválido
        result = two_fa.verify_backup_code(user_id, "00000000")
        assert result is False

        print("✅ Teste de verificação de códigos de backup passou!")


if __name__ == "__main__":
    print("🧪 Executando testes isolados do TwoFactorAuth...")

    test_two_factor_basic_functionality()
    test_two_factor_secret_generation()
    test_two_factor_qr_code_generation()
    test_two_factor_totp_verification()
    test_two_factor_backup_codes()
    test_two_factor_setup_confirmation()
    test_two_factor_user_lockout()
    test_two_factor_status_check()
    test_two_factor_edge_cases()
    test_two_factor_backup_code_verification()

    print(
        "\n🎉 Todos os testes do TwoFactorAuth passaram! Sistema 2FA funcionando corretamente."
    )

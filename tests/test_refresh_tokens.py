"""
🧪 Testes para Sistema de Refresh Tokens
========================================

Testa todas as funcionalidades críticas do sistema de refresh tokens:
- Criação e armazenamento de tokens
- Renovação automática de access tokens
- Revogação de tokens (logout)
- Expiração e cleanup de tokens
- Casos de erro e edge cases
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.auth_service import AuthService
from app.models.database import AdminUser, RefreshToken


@pytest.fixture
async def mock_admin_user():
    """Cria um usuário admin mock para testes"""
    user = AdminUser(
        id=1,
        username="test_admin",
        email="test@admin.com",
        password_hash="hashed_password",
        is_active=True
    )
    return user


@pytest.fixture
async def auth_service():
    """Cria instância do AuthService com session mock"""
    mock_session = AsyncMock(spec=AsyncSession)
    return AuthService(mock_session)


class TestRefreshTokens:
    """Testes para funcionalidades de refresh tokens"""
    
    async def test_access_token_expires_in_15_minutes(self, auth_service, mock_admin_user):
        """✅ Testa se access tokens expiram em 15 minutos"""
        with patch('app.services.auth_service.create_access_token') as mock_create_token:
            mock_create_token.return_value = "mock_access_token"
            
            # Mock do banco para store_refresh_token
            auth_service.db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.all.return_value = []
            auth_service.db.add = AsyncMock()
            auth_service.db.commit = AsyncMock()
            
            token_pair = await auth_service.create_token_pair(mock_admin_user)
            
            # Verificar se access token foi criado com expiração de 15 minutos
            mock_create_token.assert_called_once()
            args, kwargs = mock_create_token.call_args
            
            assert kwargs['expires_delta'] == timedelta(minutes=15)
            assert token_pair['expires_in'] == 900  # 15 minutos = 900 segundos
            assert token_pair['token_type'] == 'bearer'
    
    async def test_refresh_token_generates_new_access(self, auth_service, mock_admin_user):
        """✅ Testa se refresh token gera novo access token"""
        
        # Mock do refresh token no banco
        mock_refresh_token = RefreshToken(
            id=1,
            token_hash="hashed_refresh_token",
            admin_user_id=1,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_revoked=False
        )
        
        auth_service.db.query.return_value.filter.return_value.first.return_value = mock_refresh_token
        auth_service.db.query.return_value.filter.return_value.first.return_value = mock_admin_user
        
        with patch('app.services.auth_service.create_access_token') as mock_create_token:
            mock_create_token.return_value = "new_access_token"
            
            result = await auth_service.refresh_access_token("valid_refresh_token")
            
            # Verificar se novo access token foi criado
            assert result['access_token'] == "new_access_token"
            assert result['expires_in'] == 900
            mock_create_token.assert_called_once_with(
                user_id=1,
                expires_delta=timedelta(minutes=15)
            )
    
    async def test_revoke_tokens_logs_out_user(self, auth_service):
        """✅ Testa se revogar tokens faz logout do usuário"""
        
        # Mock da query para atualizar tokens
        mock_query = auth_service.db.query.return_value.filter.return_value.update
        mock_query.return_value = 3  # 3 tokens revogados
        auth_service.db.commit = AsyncMock()
        
        result = await auth_service.revoke_all_tokens(user_id=1)
        
        # Verificar se tokens foram marcados como revogados
        assert result is True
        mock_query.assert_called_once_with({"is_revoked": True})
        auth_service.db.commit.assert_called_once()
    
    async def test_expired_refresh_token_forces_login(self, auth_service):
        """✅ Testa se refresh token expirado força novo login"""
        
        # Mock do refresh token expirado no banco
        mock_expired_token = RefreshToken(
            id=1,
            token_hash="expired_token_hash",
            admin_user_id=1,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expirado
            is_revoked=False
        )
        
        auth_service.db.query.return_value.filter.return_value.first.return_value = mock_expired_token
        auth_service.db.commit = AsyncMock()
        
        # Deve lançar exceção para token expirado
        with pytest.raises(Exception, match="Refresh token expired"):
            await auth_service.refresh_access_token("expired_refresh_token")
        
        # Token deve ser marcado como revogado
        assert mock_expired_token.is_revoked is True
        auth_service.db.commit.assert_called_once()
    
    async def test_invalid_refresh_token_raises_error(self, auth_service):
        """✅ Testa se refresh token inválido gera erro"""
        
        # Mock de token não encontrado no banco
        auth_service.db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(Exception, match="Invalid refresh token"):
            await auth_service.refresh_access_token("invalid_token")
    
    async def test_multiple_refresh_tokens_management(self, auth_service, mock_admin_user):
        """✅ Testa gerenciamento de múltiplos refresh tokens (limite de 5)"""
        
        # Mock de 6 tokens existentes (deve manter apenas os últimos 5)
        old_tokens = [
            RefreshToken(id=i, token_hash=f"token_{i}", admin_user_id=1, is_revoked=False)
            for i in range(1, 7)
        ]
        
        auth_service.db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.all.return_value = old_tokens[-2:]  # Últimos 2 serão revogados
        auth_service.db.add = AsyncMock()
        auth_service.db.commit = AsyncMock()
        
        with patch('app.services.auth_service.create_access_token'):
            await auth_service.create_token_pair(mock_admin_user)
        
        # Verificar se tokens antigos foram revogados
        for token in old_tokens[-2:]:
            assert token.is_revoked is True
    
    async def test_cleanup_expired_tokens(self, auth_service):
        """✅ Testa limpeza de tokens expirados"""
        
        mock_delete = auth_service.db.query.return_value.filter.return_value.delete
        mock_delete.return_value = 5  # 5 tokens removidos
        auth_service.db.commit = AsyncMock()
        
        result = await auth_service.cleanup_expired_tokens()
        
        assert result == 5
        mock_delete.assert_called_once()
        auth_service.db.commit.assert_called_once()
    
    async def test_revoke_specific_refresh_token(self, auth_service):
        """✅ Testa revogação de token específico"""
        
        mock_token = RefreshToken(
            id=1,
            token_hash="specific_token_hash",
            admin_user_id=1,
            is_revoked=False
        )
        
        auth_service.db.query.return_value.filter.return_value.first.return_value = mock_token
        auth_service.db.commit = AsyncMock()
        
        result = await auth_service.revoke_refresh_token("specific_token")
        
        assert result is True
        assert mock_token.is_revoked is True
        auth_service.db.commit.assert_called_once()
    
    async def test_user_inactive_blocks_refresh(self, auth_service):
        """✅ Testa se usuário inativo bloqueia refresh"""
        
        inactive_user = AdminUser(
            id=1,
            username="inactive_user",
            is_active=False  # Usuário inativo
        )
        
        mock_refresh_token = RefreshToken(
            id=1,
            token_hash="valid_hash",
            admin_user_id=1,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_revoked=False
        )
        
        auth_service.db.query.return_value.filter.return_value.first.side_effect = [
            mock_refresh_token,  # Primeira chamada retorna o token
            inactive_user        # Segunda chamada retorna usuário inativo
        ]
        auth_service.db.commit = AsyncMock()
        
        with pytest.raises(Exception, match="User not found or inactive"):
            await auth_service.refresh_access_token("valid_token")
        
        # Token deve ser revogado
        assert mock_refresh_token.is_revoked is True


@pytest.mark.asyncio
class TestTokenSecurity:
    """Testes de segurança para tokens"""
    
    async def test_tokens_are_hashed_before_storage(self, auth_service, mock_admin_user):
        """✅ Testa se tokens são hasheados antes do armazenamento"""
        
        auth_service.db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.all.return_value = []
        auth_service.db.add = AsyncMock()
        auth_service.db.commit = AsyncMock()
        
        with patch('app.services.auth_service.create_access_token'):
            token_pair = await auth_service.create_token_pair(mock_admin_user)
        
        # Verificar se o método add foi chamado (token foi armazenado)
        auth_service.db.add.assert_called_once()
        
        # O refresh_token retornado deve ser diferente do hash armazenado
        refresh_token = token_pair['refresh_token']
        assert len(refresh_token) > 50  # Token deve ser longo
        
    async def test_token_hash_is_consistent(self, auth_service):
        """✅ Testa se hash do token é consistente"""
        
        token = "test_token_123"
        hash1 = auth_service._hash_token(token)
        hash2 = auth_service._hash_token(token)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hash length
    
    async def test_different_tokens_have_different_hashes(self, auth_service):
        """✅ Testa se tokens diferentes geram hashes diferentes"""
        
        token1 = "token_one"
        token2 = "token_two"
        
        hash1 = auth_service._hash_token(token1)
        hash2 = auth_service._hash_token(token2)
        
        assert hash1 != hash2


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v"])

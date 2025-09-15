"""
Serviço de Autenticação com Refresh Tokens
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy import and_, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_manager import SimpleJWTManager
from app.models.database import AdminUser, RefreshToken
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    """Serviço para gerenciamento de autenticação com refresh tokens"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.jwt_manager = SimpleJWTManager()

    def _hash_token(self, token: str) -> str:
        """Hash do token para armazenamento seguro"""
        return hashlib.sha256(token.encode()).hexdigest()

    def _generate_refresh_token(self) -> str:
        """Gera um refresh token seguro"""
        return secrets.token_urlsafe(64)

    async def create_token_pair(self, user: AdminUser) -> Dict[str, Any]:
        """
        Cria par de tokens (access + refresh) para o usuário

        Args:
            user: Usuário administrativo

        Returns:
            Dict com access_token, refresh_token, token_type e expires_in
        """
        try:
            # Criar access token (15 minutos)
            access_token = self.jwt_manager.create_access_token(
                user_id=str(user.id),
                role="admin",
                permissions=["read", "write", "admin"],
            )

            # Gerar refresh token (30 dias)
            refresh_token = self._generate_refresh_token()
            refresh_token_hash = self._hash_token(refresh_token)

            # Salvar refresh token no banco
            await self._store_refresh_token(refresh_token_hash, user.id)

            logger.info(f"Token pair created for user {user.id}")

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 900,  # 15 minutos em segundos
            }

        except Exception as e:
            logger.error(f"Error creating token pair for user {user.id}: {e}")
            raise

    async def _store_refresh_token(self, token_hash: str, user_id: int) -> RefreshToken:
        """Armazena refresh token no banco de dados"""
        try:
            # Invalidar tokens antigos do usuário (mantém apenas os últimos 5)
            old_tokens_query = (
                select(RefreshToken)
                .filter(
                    and_(
                        RefreshToken.admin_user_id == user_id,
                        RefreshToken.is_revoked == False,
                    )
                )
                .order_by(RefreshToken.created_at.desc())
                .offset(4)
            )

            result = await self.db.execute(old_tokens_query)
            old_tokens = result.scalars().all()

            for token in old_tokens:
                token.is_revoked = True

            # Criar novo refresh token
            expires_at = datetime.now(timezone.utc) + timedelta(days=30)

            refresh_token_obj = RefreshToken(
                token_hash=token_hash,
                admin_user_id=user_id,
                expires_at=expires_at,
                is_revoked=False,
            )

            self.db.add(refresh_token_obj)
            await self.db.commit()

            logger.info(f"Refresh token stored for user {user_id}")
            return refresh_token_obj

        except Exception as e:
            logger.error(f"Error storing refresh token for user {user_id}: {e}")
            await self.db.rollback()
            raise

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Renova access token usando refresh token

        Args:
            refresh_token: Refresh token do cliente

        Returns:
            Dict com novo access_token e expires_in

        Raises:
            Exception: Se refresh token inválido/expirado
        """
        try:
            refresh_token_hash = self._hash_token(refresh_token)

            # Buscar refresh token no banco
            token_query = select(RefreshToken).filter(
                and_(
                    RefreshToken.token_hash == refresh_token_hash,
                    RefreshToken.is_revoked == False,
                )
            )

            result = await self.db.execute(token_query)
            token_obj = result.scalar_one_or_none()

            if not token_obj:
                logger.warning("Invalid refresh token provided")
                raise Exception("Invalid refresh token")

            # Verificar se não expirou
            if token_obj.expires_at < datetime.now(timezone.utc):
                logger.warning(
                    f"Expired refresh token for user {token_obj.admin_user_id}"
                )
                token_obj.is_revoked = True
                await self.db.commit()
                raise Exception("Refresh token expired")

            # Buscar usuário
            user_query = select(AdminUser).filter(
                AdminUser.id == token_obj.admin_user_id
            )
            result = await self.db.execute(user_query)
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                logger.warning(f"User {token_obj.admin_user_id} not found or inactive")
                token_obj.is_revoked = True
                await self.db.commit()
                raise Exception("User not found or inactive")

            # Criar novo access token
            new_access_token = self.jwt_manager.create_access_token(
                user_id=str(user.id),
                role="admin",
                permissions=["read", "write", "admin"],
            )

            logger.info(f"Access token refreshed for user {user.id}")

            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": 900,  # 15 minutos
            }

        except Exception as e:
            logger.error(f"Error refreshing access token: {e}")
            raise

    async def revoke_all_tokens(self, user_id: int) -> bool:
        """
        Revoga todos os refresh tokens do usuário (logout completo)

        Args:
            user_id: ID do usuário

        Returns:
            bool: True se tokens foram revogados com sucesso
        """
        try:
            # Marcar todos os refresh tokens como revogados
            update_query = (
                update(RefreshToken)
                .where(
                    and_(
                        RefreshToken.admin_user_id == user_id,
                        RefreshToken.is_revoked == False,
                    )
                )
                .values(is_revoked=True)
            )

            result = await self.db.execute(update_query)
            updated_count = result.rowcount

            await self.db.commit()

            logger.info(f"Revoked {updated_count} refresh tokens for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error revoking tokens for user {user_id}: {e}")
            await self.db.rollback()
            return False

    async def revoke_refresh_token(self, refresh_token: str) -> bool:
        """
        Revoga um refresh token específico

        Args:
            refresh_token: Token a ser revogado

        Returns:
            bool: True se token foi revogado com sucesso
        """
        try:
            refresh_token_hash = self._hash_token(refresh_token)

            token_query = select(RefreshToken).filter(
                RefreshToken.token_hash == refresh_token_hash
            )

            result = await self.db.execute(token_query)
            token_obj = result.scalar_one_or_none()

            if token_obj:
                token_obj.is_revoked = True
                await self.db.commit()
                logger.info(f"Refresh token revoked for user {token_obj.admin_user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error revoking refresh token: {e}")
            await self.db.rollback()
            return False

    async def cleanup_expired_tokens(self) -> int:
        """
        Remove tokens expirados do banco (tarefa de limpeza)

        Returns:
            int: Número de tokens removidos
        """
        try:
            current_time = datetime.now(timezone.utc)

            # Deletar tokens expirados há mais de 1 dia
            delete_query = delete(RefreshToken).where(
                RefreshToken.expires_at < current_time - timedelta(days=1)
            )

            result = await self.db.execute(delete_query)
            deleted_count = result.rowcount

            await self.db.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired refresh tokens")

            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
            await self.db.rollback()
            return 0

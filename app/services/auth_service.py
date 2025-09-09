"""
import logging
logger = logging.getLogger(__name__)

Serviço de Autenticação com Refresh Tokens
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.database import AdminUser, RefreshToken
from app.auth.jwt_manager import SimpleJWTManager

class AuthService:
    """Serviço para gerenciamento de autenticação com refresh tokens"""
    
    def __init__(self, db: Session):
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
                permissions=["read", "write", "admin"]
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
                "expires_in": 900  # 15 minutos em segundos
            }
            
        except Exception as e:
            logger.error(f"Error creating token pair for user {user.id}: {e}")
            raise
    
    async def _store_refresh_token(self, token_hash: str, user_id: int) -> RefreshToken:
        """Armazena refresh token no banco de dados"""
        try:
            # Invalidar tokens antigos do usuário (mantém apenas os últimos 5)
            old_tokens = self.db.query(RefreshToken).filter(
                and_(
                    RefreshToken.admin_user_id == user_id,
                    RefreshToken.is_revoked == False
                )
            ).order_by(RefreshToken.created_at.desc()).offset(4).all()
            
            for token in old_tokens:
                token.is_revoked = True
            
            # Criar novo refresh token
            expires_at = datetime.now(timezone.utc) + timedelta(days=30)
            
            refresh_token_obj = RefreshToken(
                token_hash=token_hash,
                admin_user_id=user_id,
                expires_at=expires_at,
                is_revoked=False
            )
            
            self.db.add(refresh_token_obj)
            self.db.commit()
            
            logger.info(f"Refresh token stored for user {user_id}")
            return refresh_token_obj
            
        except Exception as e:
            logger.error(f"Error storing refresh token for user {user_id}: {e}")
            self.db.rollback()
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
            token_obj = self.db.query(RefreshToken).filter(
                and_(
                    RefreshToken.token_hash == refresh_token_hash,
                    RefreshToken.is_revoked == False
                )
            ).first()
            
            if not token_obj:
                logger.warning("Invalid refresh token provided")
                raise Exception("Invalid refresh token")
            
            # Verificar se não expirou
            if token_obj.expires_at < datetime.now(timezone.utc):
                logger.warning(f"Expired refresh token for user {token_obj.admin_user_id}")
                token_obj.is_revoked = True
                self.db.commit()
                raise Exception("Refresh token expired")
            
            # Buscar usuário
            user = self.db.query(AdminUser).filter(AdminUser.id == token_obj.admin_user_id).first()
            if not user or not user.is_active:
                logger.warning(f"User {token_obj.admin_user_id} not found or inactive")
                token_obj.is_revoked = True
                self.db.commit()
                raise Exception("User not found or inactive")
            
            # Criar novo access token
            new_access_token = self.jwt_manager.create_access_token(
                user_id=str(user.id),
                role="admin",
                permissions=["read", "write", "admin"]
            )
            
            logger.info(f"Access token refreshed for user {user.id}")
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": 900  # 15 minutos
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
            updated_count = self.db.query(RefreshToken).filter(
                and_(
                    RefreshToken.admin_user_id == user_id,
                    RefreshToken.is_revoked == False
                )
            ).update({"is_revoked": True})
            
            self.db.commit()
            
            logger.info(f"Revoked {updated_count} refresh tokens for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking tokens for user {user_id}: {e}")
            self.db.rollback()
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
            
            token_obj = self.db.query(RefreshToken).filter(
                RefreshToken.token_hash == refresh_token_hash
            ).first()
            
            if token_obj:
                token_obj.is_revoked = True
                self.db.commit()
                logger.info(f"Refresh token revoked for user {token_obj.admin_user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error revoking refresh token: {e}")
            self.db.rollback()
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
            deleted_count = self.db.query(RefreshToken).filter(
                RefreshToken.expires_at < current_time - timedelta(days=1)
            ).delete()
            
            self.db.commit()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired refresh tokens")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
            self.db.rollback()
            return 0

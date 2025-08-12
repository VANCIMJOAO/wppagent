"""
Módulo de autenticação para o dashboard
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal, SessionLocal
from app.utils.logger import get_logger
from app.models.database import AdminUser, LoginSession
logger = get_logger(__name__)


class AuthManager:
    """Gerenciador de autenticação"""
    
    @staticmethod
    def generate_session_token() -> str:
        """Gerar token de sessão único"""
        return secrets.token_urlsafe(64)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash do token para armazenamento seguro"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    async def authenticate_user(username: str, password: str) -> Optional[AdminUser]:
        """Autenticar usuário com username e senha"""
        async with AsyncSessionLocal() as session:
            # Buscar usuário
            result = await session.execute(
                select(AdminUser).where(
                    (AdminUser.username == username) | (AdminUser.email == username)
                )
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.is_active:
                return None
            
            # Verificar senha
            if not user.check_password(password):
                return None
            
            # Atualizar último login
            await session.execute(
                update(AdminUser)
                .where(AdminUser.id == user.id)
                .values(last_login=datetime.utcnow())
            )
            await session.commit()
            
            return user
    
    @staticmethod
    async def create_session(user: AdminUser, ip_address: str = None, user_agent: str = None) -> str:
        """Criar nova sessão de login"""
        async with AsyncSessionLocal() as session:
            # Gerar token
            token = AuthManager.generate_session_token()
            
            # Criar sessão
            login_session = LoginSession(
                session_token=token,
                admin_user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=datetime.utcnow() + timedelta(hours=24)  # 24 horas
            )
            
            session.add(login_session)
            await session.commit()
            
            return token
    
    @staticmethod
    async def validate_session(token: str) -> Optional[AdminUser]:
        """Validar token de sessão"""
        async with AsyncSessionLocal() as session:
            # Buscar sessão
            result = await session.execute(
                select(LoginSession)
                .join(AdminUser)
                .where(
                    LoginSession.session_token == token,
                    LoginSession.is_active == True,
                    LoginSession.expires_at > datetime.utcnow()
                )
            )
            session_obj = result.scalar_one_or_none()
            
            if not session_obj:
                return None
            
            # Buscar usuário
            result = await session.execute(
                select(AdminUser).where(AdminUser.id == session_obj.admin_user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.is_active:
                return None
            
            return user
    
    @staticmethod
    async def logout_session(token: str) -> bool:
        """Fazer logout da sessão"""
        async with AsyncSessionLocal() as session:
            # Desativar sessão
            result = await session.execute(
                update(LoginSession)
                .where(LoginSession.session_token == token)
                .values(is_active=False)
            )
            await session.commit()
            
            return result.rowcount > 0
    
    @staticmethod
    async def cleanup_expired_sessions():
        """Limpar sessões expiradas"""
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(LoginSession)
                .where(LoginSession.expires_at < datetime.utcnow())
                .values(is_active=False)
            )
            await session.commit()


class SyncAuthManager:
    """Versão síncrona do gerenciador de autenticação para o dashboard"""
    
    @staticmethod
    def authenticate_user_sync(username: str, password: str) -> Optional[Dict[str, Any]]:
        """Autenticar usuário (versão síncrona)"""
        with SessionLocal() as session:
            # Buscar usuário
            result = session.execute(
                select(AdminUser).where(
                    (AdminUser.username == username) | (AdminUser.email == username)
                )
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.is_active:
                return None
            
            # Verificar senha
            if not user.check_password(password):
                return None
            
            # Atualizar último login
            session.execute(
                update(AdminUser)
                .where(AdminUser.id == user.id)
                .values(last_login=datetime.utcnow())
            )
            session.commit()
            
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'is_super_admin': user.is_super_admin,
                'last_login': user.last_login
            }
    
    @staticmethod
    def create_session_sync(user_data: Dict[str, Any], ip_address: str = None, user_agent: str = None) -> str:
        """Criar nova sessão (versão síncrona)"""
        with SessionLocal() as session:
            # Gerar token
            token = AuthManager.generate_session_token()
            
            # Criar sessão
            login_session = LoginSession(
                session_token=token,
                admin_user_id=user_data['id'],
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            
            session.add(login_session)
            session.commit()
            
            return token
    
    @staticmethod
    def validate_session_sync(token: str) -> Optional[Dict[str, Any]]:
        """Validar token de sessão (versão síncrona)"""
        with SessionLocal() as session:
            # Buscar sessão
            result = session.execute(
                select(LoginSession)
                .join(AdminUser)
                .where(
                    LoginSession.session_token == token,
                    LoginSession.is_active == True,
                    LoginSession.expires_at > datetime.utcnow()
                )
            )
            session_obj = result.scalar_one_or_none()
            
            if not session_obj:
                return None
            
            # Buscar usuário
            result = session.execute(
                select(AdminUser).where(AdminUser.id == session_obj.admin_user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.is_active:
                return None
            
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'is_super_admin': user.is_super_admin,
                'last_login': user.last_login
            }
    
    @staticmethod
    def logout_session_sync(token: str) -> bool:
        """Fazer logout da sessão (versão síncrona)"""
        with SessionLocal() as session:
            # Desativar sessão
            result = session.execute(
                update(LoginSession)
                .where(LoginSession.session_token == token)
                .values(is_active=False)
            )
            session.commit()
            
            return result.rowcount > 0

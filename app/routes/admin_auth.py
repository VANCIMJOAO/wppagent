"""
🔐 Sistema de Autenticação para Administradores
==============================================

Fornece autenticação JWT para operações administrativas sensíveis
como otimização de banco de dados, monitoramento avançado, etc.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_manager import jwt_manager
from app.database import get_db
from app.models.database import AdminUser, LoginSession
from app.utils.logger import get_logger

logger = get_logger(__name__)
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Configuração de segurança
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Configurações JWT - usando JWT Manager
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 🔧 CONSTANTES PARA COMPATIBILIDADE COM MIDDLEWARE
# Estas são usadas pelo middleware.py como fallback
SECRET_KEY = jwt_manager.secret_key
ALGORITHM = jwt_manager.algorithm


class TokenData(BaseModel):
    username: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class AdminLogin(BaseModel):
    username: str
    password: str


class AdminCredentials(BaseModel):
    username: str
    password: str
    is_active: bool = True


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha está correta"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Gera hash da senha"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Cria token JWT compatível com middleware usando jwt_manager"""
    # Usar jwt_manager para garantir compatibilidade
    from app.auth.jwt_manager import jwt_manager

    user_id = data.get("sub", "admin")
    role = "admin"  # Admin auth sempre cria tokens admin
    permissions = ["read", "write", "admin", "user_management"]

    return jwt_manager.create_access_token(user_id, role, permissions)


async def get_admin_user(username: str, session: AsyncSession) -> Optional[AdminUser]:
    """Busca usuário admin pelo username"""
    try:
        result = await session.execute(
            select(AdminUser).where(AdminUser.username == username)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"❌ Erro ao buscar admin user: {e}")
        return None


async def authenticate_admin(
    username: str, password: str, session: AsyncSession
) -> Optional[AdminUser]:
    """Autentica admin user"""
    try:
        admin_user = await get_admin_user(username, session)
        if not admin_user:
            logger.warning(f"⚠️ Admin user não encontrado: {username}")
            return None

        if not admin_user.is_active:
            logger.warning(f"⚠️ Admin user inativo: {username}")
            return None

        if not verify_password(password, admin_user.password_hash):
            logger.warning(f"⚠️ Senha incorreta para admin: {username}")
            return None

        logger.info(f"✅ Admin autenticado: {username}")
        return admin_user

    except Exception as e:
        logger.error(f"❌ Erro na autenticação: {e}")
        return None


async def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> AdminUser:
    """Obtém o usuário admin atual via token JWT"""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        # Usar nosso JWT Manager em vez de jose.jwt
        payload = jwt_manager.verify_token(token)

        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # Verificar se é token de acesso
        if payload.get("type") != "access":
            raise credentials_exception

    except Exception as e:
        logger.error(f"❌ Erro ao verificar token: {e}")
        raise credentials_exception

    # Buscar admin por ID em vez de username
    try:
        result = await session.execute(
            select(AdminUser).where(AdminUser.id == int(user_id))
        )
        admin_user = result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"❌ Erro ao buscar admin por ID {user_id}: {e}")
        admin_user = None

    if admin_user is None:
        raise credentials_exception

    if not admin_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo"
        )

    return admin_user


async def create_login_session(
    admin_user: AdminUser, token: str, session: AsyncSession
):
    """Cria sessão de login"""
    try:
        login_session = LoginSession(
            admin_user_id=admin_user.id,
            session_token=get_password_hash(token),
            expires_at=datetime.utcnow()
            + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        session.add(login_session)
        await session.commit()
        logger.info(f"✅ Sessão criada para admin: {admin_user.username}")
    except Exception as e:
        logger.error(f"❌ Erro ao criar sessão: {e}")


# Router para autenticação
auth_router = APIRouter(prefix="/admin", tags=["Admin Authentication"])


@auth_router.post("/login", response_model=TokenPair)
async def admin_login(credentials: AdminLogin, session: AsyncSession = Depends(get_db)):
    """
    🔐 Login de administrador

    Autentica admin user e retorna par de tokens (access + refresh)
    """
    try:
        admin_user = await authenticate_admin(
            credentials.username, credentials.password, session
        )

        if not admin_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username ou senha incorretos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Usar AuthService para criar par de tokens
        from app.services.auth_service import AuthService

        auth_service = AuthService(session)

        token_pair = await auth_service.create_token_pair(admin_user)

        # Criar sessão (compatibilidade com sistema existente)
        await create_login_session(admin_user, token_pair["access_token"], session)

        logger.info(f"✅ Login bem-sucedido com refresh token: {admin_user.username}")

        return token_pair

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor",
        )


@auth_router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest, session: AsyncSession = Depends(get_db)
):
    """
    🔄 Renovar access token usando refresh token

    Permite renovar access token expirado sem fazer novo login
    """
    try:
        from app.services.auth_service import AuthService

        auth_service = AuthService(session)

        new_tokens = await auth_service.refresh_access_token(
            refresh_request.refresh_token
        )

        logger.info("✅ Access token renovado com sucesso")

        return new_tokens

    except Exception as e:
        logger.error(f"❌ Erro ao renovar token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


@auth_router.get("/debug-jwt")
async def debug_jwt():
    """🔧 Debug JWT secret (TEMPORÁRIO)"""
    import os

    from app.auth.jwt_manager import jwt_manager

    return {
        "secret_preview": (
            jwt_manager.secret_key[:10] + "..." if jwt_manager.secret_key else "None"
        ),
        "jwt_secret_env": (
            os.getenv("JWT_SECRET", "not-set")[:10] + "..."
            if os.getenv("JWT_SECRET")
            else "not-set"
        ),
        "secret_key_env": (
            os.getenv("SECRET_KEY", "not-set")[:10] + "..."
            if os.getenv("SECRET_KEY")
            else "not-set"
        ),
        "algorithm": jwt_manager.algorithm,
    }


@auth_router.post("/revoke")
async def revoke_tokens(
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
):
    """
    🚫 Revogar todos os tokens do usuário (logout completo)

    Invalida todos os refresh tokens do usuário atual
    """
    try:
        from app.services.auth_service import AuthService

        auth_service = AuthService(session)

        success = await auth_service.revoke_all_tokens(current_admin.id)

        if success:
            logger.info(
                f"✅ Todos os tokens revogados para user {current_admin.username}"
            )
            return {"message": "Todos os tokens foram revogados com sucesso"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao revogar tokens",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao revogar tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor",
        )


@auth_router.post("/create")
async def create_admin_user(
    credentials: AdminCredentials,
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
):
    """
    👤 Criar novo usuário admin

    Apenas admins existentes podem criar novos admins
    """
    try:
        # Verificar se username já existe
        existing_user = await get_admin_user(credentials.username, session)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username já existe"
            )

        # Criar novo admin
        new_admin = AdminUser(
            username=credentials.username,
            password_hash=get_password_hash(credentials.password),
            is_active=credentials.is_active,
            created_by=current_admin.id,
        )

        session.add(new_admin)
        await session.commit()

        logger.info(
            f"✅ Admin criado: {credentials.username} por {current_admin.username}"
        )

        return {
            "success": True,
            "message": f"Admin '{credentials.username}' criado com sucesso",
            "created_by": current_admin.username,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao criar admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar usuário admin",
        )


@auth_router.get("/me")
async def get_current_admin_info():
    """
    👤 Informações do admin atual - TESTE SIMPLIFICADO
    """
    try:
        return {"status": "ok", "test": True}
    except Exception as e:
        logger.error(f"❌ Erro em get_current_admin_info: {e}")
        return {"error": str(e), "status": "error"}


@auth_router.post("/logout")
async def admin_logout(
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
):
    """
    🚪 Logout de administrador

    Invalida todas as sessões do admin e revoga todos os refresh tokens
    """
    try:
        # Usar AuthService para revogar todos os refresh tokens
        from app.services.auth_service import AuthService

        auth_service = AuthService(session)

        # Revogar todos os refresh tokens
        await auth_service.revoke_all_tokens(current_admin.id)

        # Invalidar sessões existentes (compatibilidade com sistema existente)
        from sqlalchemy import update

        await session.execute(
            update(LoginSession)
            .where(LoginSession.admin_user_id == current_admin.id)
            .values(expires_at=datetime.utcnow())
        )

        await session.commit()

        logger.info(
            f"✅ Logout completo realizado (tokens + sessões): {current_admin.username}"
        )

        return {"success": True, "message": "Logout realizado com sucesso"}

    except Exception as e:
        logger.error(f"❌ Erro no logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro no logout"
        )


@auth_router.get("/health")
async def auth_health_check():
    """
    🏥 Health check do sistema de autenticação
    """
    return {
        "status": "healthy",
        "auth_system": "active",
        "jwt_algorithm": "HS256",
        "token_expire_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
    }


# Endpoint temporário para criar admin inicial - PÚBLICO
@auth_router.post("/create-initial-admin", include_in_schema=False, dependencies=[])
async def create_initial_admin(session: AsyncSession = Depends(get_db)):
    """
    🚨 ENDPOINT TEMPORÁRIO - Criar admin inicial
    Este endpoint deve ser removido após uso em produção
    """
    try:
        # Verificar se já existe admin
        result = await session.execute(
            select(AdminUser).where(AdminUser.username == "admin")
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            return {"message": "Admin já existe", "status": "exists"}

        # Criar novo admin usando credenciais das variáveis de ambiente
        admin_username = settings.admin_username or "admin"
        admin_password = (
            settings.admin_password.get_secret_value()
            if settings.admin_password
            else None
        )

        if not admin_password:
            raise HTTPException(
                status_code=500,
                detail="ADMIN_PASSWORD não configurada nas variáveis de ambiente",
            )

        hashed_password = pwd_context.hash(admin_password)

        new_admin = AdminUser(
            username=admin_username, password_hash=hashed_password, is_active=True
        )

        session.add(new_admin)
        await session.commit()

        logger.info("✅ Admin inicial criado via endpoint temporário")

        return {
            "message": "Admin criado com sucesso",
            "username": "admin",
            "status": "created",
        }

    except Exception as e:
        logger.error(f"❌ Erro ao criar admin inicial: {e}")
        await session.rollback()
        raise HTTPException(500, f"Erro interno: {str(e)}")


# Endpoint temporário para debug de login
@auth_router.post("/debug-admin", include_in_schema=False, dependencies=[])
async def debug_admin(credentials: AdminLogin, session: AsyncSession = Depends(get_db)):
    """
    🚨 ENDPOINT TEMPORÁRIO - Debug do admin
    """
    try:
        # Buscar admin
        result = await session.execute(
            select(AdminUser).where(AdminUser.username == credentials.username)
        )
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            return {
                "status": "user_not_found",
                "username": credentials.username,
                "admin_exists": False,
            }

        # Verificar senha
        password_ok = verify_password(credentials.password, admin_user.password_hash)

        return {
            "status": "debug_complete",
            "username": credentials.username,
            "admin_exists": True,
            "is_active": admin_user.is_active,
            "password_hash_exists": bool(admin_user.password_hash),
            "password_verified": password_ok,
            "hash_preview": admin_user.password_hash[:20] + "...",
        }

    except Exception as e:
        logger.error(f"❌ Erro no debug admin: {e}")
        return {"status": "error", "error": str(e)}

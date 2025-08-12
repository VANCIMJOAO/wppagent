"""
🔐 Sistema de Autenticação para Administradores
==============================================

Fornece autenticação JWT para operações administrativas sensíveis
como otimização de banco de dados, monitoramento avançado, etc.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.utils.logger import get_logger
from app.models.database import AdminUser, LoginSession
logger = get_logger(__name__)
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Configuração de segurança
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Configurações JWT
SECRET_KEY = getattr(settings, 'admin_jwt_secret', 'your-super-secret-admin-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha está correta"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Gera hash da senha"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Cria token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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

async def authenticate_admin(username: str, password: str, session: AsyncSession) -> Optional[AdminUser]:
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
    session: AsyncSession = Depends(get_db)
) -> AdminUser:
    """Obtém o usuário admin atual via token JWT"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    admin_user = await get_admin_user(username=token_data.username, session=session)
    if admin_user is None:
        raise credentials_exception
    
    if not admin_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo"
        )
    
    return admin_user

async def create_login_session(admin_user: AdminUser, token: str, session: AsyncSession):
    """Cria sessão de login"""
    try:
        login_session = LoginSession(
            admin_user_id=admin_user.id,
            token_hash=get_password_hash(token),
            expires_at=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        session.add(login_session)
        await session.commit()
        logger.info(f"✅ Sessão criada para admin: {admin_user.username}")
    except Exception as e:
        logger.error(f"❌ Erro ao criar sessão: {e}")

# Router para autenticação
auth_router = APIRouter(prefix="/admin", tags=["Admin Authentication"])

@auth_router.post("/login", response_model=Token)
async def admin_login(
    credentials: AdminLogin,
    session: AsyncSession = Depends(get_db)
):
    """
    🔐 Login de administrador
    
    Autentica admin user e retorna token JWT
    """
    try:
        admin_user = await authenticate_admin(
            credentials.username, 
            credentials.password, 
            session
        )
        
        if not admin_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username ou senha incorretos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": admin_user.username}, 
            expires_delta=access_token_expires
        )
        
        # Criar sessão
        await create_login_session(admin_user, access_token, session)
        
        logger.info(f"✅ Login bem-sucedido: {admin_user.username}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@auth_router.post("/create")
async def create_admin_user(
    credentials: AdminCredentials,
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username já existe"
            )
        
        # Criar novo admin
        new_admin = AdminUser(
            username=credentials.username,
            password_hash=get_password_hash(credentials.password),
            is_active=credentials.is_active,
            created_by=current_admin.id
        )
        
        session.add(new_admin)
        await session.commit()
        
        logger.info(f"✅ Admin criado: {credentials.username} por {current_admin.username}")
        
        return {
            "success": True,
            "message": f"Admin '{credentials.username}' criado com sucesso",
            "created_by": current_admin.username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao criar admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar usuário admin"
        )

@auth_router.get("/me")
async def get_current_admin_info(
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    👤 Informações do admin atual
    """
    return {
        "username": current_admin.username,
        "is_active": current_admin.is_active,
        "created_at": current_admin.created_at,
        "last_login": current_admin.last_login
    }

@auth_router.post("/logout")
async def admin_logout(
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    🚪 Logout de administrador
    
    Invalida todas as sessões do admin
    """
    try:
        # Invalidar todas as sessões do admin
        await session.execute(
            select(LoginSession).where(
                LoginSession.admin_user_id == current_admin.id,
                LoginSession.expires_at > datetime.utcnow()
            )
        )
        
        # Atualizar para expirar imediatamente
        from sqlalchemy import update
        await session.execute(
            update(LoginSession)
            .where(LoginSession.admin_user_id == current_admin.id)
            .values(expires_at=datetime.utcnow())
        )
        
        await session.commit()
        
        logger.info(f"✅ Logout realizado: {current_admin.username}")
        
        return {
            "success": True,
            "message": "Logout realizado com sucesso"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro no logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro no logout"
        )

@auth_router.get("/health")
async def auth_health_check():
    """
    🏥 Health check do sistema de autenticação
    """
    return {
        "status": "healthy",
        "auth_system": "active",
        "jwt_algorithm": ALGORITHM,
        "token_expire_minutes": ACCESS_TOKEN_EXPIRE_MINUTES
    }

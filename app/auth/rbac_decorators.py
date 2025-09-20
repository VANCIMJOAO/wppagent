"""
Decoradores e Middleware RBAC
Sistema de verificação de permissões para FastAPI
"""

import functools
import time
from typing import Callable, List, Optional, Union

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.models.rbac import PermissionType, RoleType
from app.services.rbac_service import rbac_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Bearer token security
security = HTTPBearer()


class RBACException(HTTPException):
    """Exceção específica para RBAC"""

    def __init__(self, detail: str = "Acesso negado", status_code: int = 403):
        super().__init__(status_code=status_code, detail=detail)


class InsufficientPermissionsException(RBACException):
    """Exceção para permissões insuficientes"""

    def __init__(
        self, required_permission: Union[PermissionType, List[PermissionType]]
    ):
        if isinstance(required_permission, list):
            perms_str = ", ".join([p.value for p in required_permission])
            detail = f"Permissões necessárias: {perms_str}"
        else:
            detail = f"Permissão necessária: {required_permission.value}"

        super().__init__(detail=detail)


class RoleRequiredException(RBACException):
    """Exceção para role necessário"""

    def __init__(self, required_role: Union[RoleType, List[RoleType]]):
        if isinstance(required_role, list):
            roles_str = ", ".join([r.value for r in required_role])
            detail = f"Roles necessários: {roles_str}"
        else:
            detail = f"Role necessário: {required_role.value}"

        super().__init__(detail=detail)


# ========================================
# DEPENDENCY PROVIDERS
# ========================================


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    """Extrair ID do usuário do token JWT"""
    try:
        from app.auth.jwt_manager import jwt_manager
        
        # Decodificar token JWT usando o jwt_manager existente
        token = credentials.credentials
        payload = jwt_manager.verify_token(token)
        
        # Extrair user_id do payload
        user_id = payload.get("sub")
        
        if not user_id:
            raise RBACException("Token inválido - user_id não encontrado", 401)

        # Converter para int se necessário
        try:
            return int(user_id)
        except (ValueError, TypeError):
            raise RBACException("Token inválido - user_id inválido", 401)

    except jwt.InvalidTokenError:
        raise RBACException("Token inválido", 401)
    except Exception as e:
        logger.error(f"Erro ao validar token: {e}")
        raise RBACException("Erro de autenticação", 401)


async def get_current_user(user_id: int = Depends(get_current_user_id)):
    """Obter usuário atual completo"""
    user = await rbac_service.get_user_by_id(user_id)

    if not user:
        raise RBACException("Usuário não encontrado", 404)

    if not user.is_active:
        raise RBACException("Usuário desativado", 403)

    return user


# ========================================
# DECORADORES DE PERMISSÃO
# ========================================


def require_permission(permission: PermissionType, require_2fa: bool = False):
    """
    Decorador que exige permissão específica

    Args:
        permission: Permissão necessária
        require_2fa: Se deve exigir 2FA
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Buscar user_id dos kwargs (injetado pelo Depends)
            user = None
            for key, value in kwargs.items():
                if hasattr(value, "id") and hasattr(value, "username"):
                    user = value
                    break

            if not user:
                raise RBACException("Usuário não encontrado no contexto")

            # Verificar permissão
            if not user.has_permission(permission):
                raise InsufficientPermissionsException(permission)

            # Verificar 2FA se necessário
            if require_2fa and user.requires_2fa:
                # Aqui você implementaria a verificação de 2FA
                # Por agora, apenas log
                logger.info(
                    f"2FA required for user {user.id} for permission {permission.value}"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_any_permission(
    permissions: List[PermissionType], require_2fa: bool = False
):
    """
    Decorador que exige pelo menos uma das permissões

    Args:
        permissions: Lista de permissões (qualquer uma serve)
        require_2fa: Se deve exigir 2FA
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            user = None
            for key, value in kwargs.items():
                if hasattr(value, "id") and hasattr(value, "username"):
                    user = value
                    break

            if not user:
                raise RBACException("Usuário não encontrado no contexto")

            if not user.has_any_permission(permissions):
                raise InsufficientPermissionsException(permissions)

            if require_2fa and user.requires_2fa:
                logger.info(
                    f"2FA required for user {user.id} for permissions {[p.value for p in permissions]}"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_all_permissions(
    permissions: List[PermissionType], require_2fa: bool = False
):
    """
    Decorador que exige todas as permissões

    Args:
        permissions: Lista de permissões (todas necessárias)
        require_2fa: Se deve exigir 2FA
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            user = None
            for key, value in kwargs.items():
                if hasattr(value, "id") and hasattr(value, "username"):
                    user = value
                    break

            if not user:
                raise RBACException("Usuário não encontrado no contexto")

            if not user.has_all_permissions(permissions):
                raise InsufficientPermissionsException(permissions)

            if require_2fa and user.requires_2fa:
                logger.info(
                    f"2FA required for user {user.id} for all permissions {[p.value for p in permissions]}"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(role: Union[RoleType, List[RoleType]]):
    """
    Decorador que exige role específico

    Args:
        role: Role ou lista de roles necessários
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            user = None
            for key, value in kwargs.items():
                if hasattr(value, "id") and hasattr(value, "username"):
                    user = value
                    break

            if not user:
                raise RBACException("Usuário não encontrado no contexto")

            required_roles = role if isinstance(role, list) else [role]
            user_role_types = {r.role_type for r in user.roles if r.role_type}

            if not any(req_role in user_role_types for req_role in required_roles):
                raise RoleRequiredException(role)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_super_admin():
    """Decorador que exige super admin"""

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            user = None
            for key, value in kwargs.items():
                if hasattr(value, "id") and hasattr(value, "username"):
                    user = value
                    break

            if not user:
                raise RBACException("Usuário não encontrado no contexto")

            if not user.is_super_admin():
                raise RoleRequiredException(RoleType.SUPER_ADMIN)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# ========================================
# DEPENDENCY FACTORIES PARA FASTAPI
# ========================================


def RequirePermission(permission: PermissionType):
    """Factory para criar dependency que exige permissão"""

    async def check_permission(user=Depends(get_current_user)):
        if not user.has_permission(permission):
            raise InsufficientPermissionsException(permission)
        return user

    return check_permission


def RequireAnyPermission(permissions: List[PermissionType]):
    """Factory para criar dependency que exige qualquer permissão"""

    async def check_permissions(user=Depends(get_current_user)):
        if not user.has_any_permission(permissions):
            raise InsufficientPermissionsException(permissions)
        return user

    return check_permissions


def RequireAllPermissions(permissions: List[PermissionType]):
    """Factory para criar dependency que exige todas as permissões"""

    async def check_permissions(user=Depends(get_current_user)):
        if not user.has_all_permissions(permissions):
            raise InsufficientPermissionsException(permissions)
        return user

    return check_permissions


def RequireRole(role: Union[RoleType, List[RoleType]]):
    """Factory para criar dependency que exige role"""

    async def check_role(user=Depends(get_current_user)):
        required_roles = role if isinstance(role, list) else [role]
        user_role_types = {r.role_type for r in user.roles if r.role_type}

        if not any(req_role in user_role_types for req_role in required_roles):
            raise RoleRequiredException(role)
        return user

    return check_role


def RequireSuperAdmin():
    """Factory para criar dependency que exige super admin"""

    async def check_super_admin(user=Depends(get_current_user)):
        if not user.is_super_admin():
            raise RoleRequiredException(RoleType.SUPER_ADMIN)
        return user

    return check_super_admin


# ========================================
# MIDDLEWARE
# ========================================


class RBACMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de acesso RBAC"""

    def __init__(self, app, excluded_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics",
            "/favicon.ico",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Pular paths excluídos
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        start_time = time.time()

        # Tentar extrair informações do usuário
        user_info = "anonymous"
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header:
                # Aqui você pode extrair informações básicas do token
                user_info = "authenticated"
        except:
            pass

        # Processar request
        response = await call_next(request)

        # Log da requisição
        process_time = time.time() - start_time
        logger.info(
            f"RBAC Access: {request.method} {request.url.path} "
            f"by {user_info} - {response.status_code} "
            f"({process_time:.3f}s)"
        )

        return response


# ========================================
# FUNÇÕES UTILITÁRIAS
# ========================================


async def check_permission_async(user_id: int, permission: PermissionType) -> bool:
    """Verificar permissão de forma assíncrona"""
    return await rbac_service.check_user_permission(user_id, permission)


async def get_user_permissions_async(user_id: int) -> set:
    """Obter permissões do usuário de forma assíncrona"""
    return await rbac_service.get_user_permissions(user_id)


def permission_required(permission: PermissionType):
    """
    Decorador simples para funções que precisam de permissão
    Uso: @permission_required(PermissionType.APPOINTMENTS_VIEW)
    """

    def decorator(func):
        # Adicionar metadado para identificação
        func._required_permission = permission
        return func

    return decorator

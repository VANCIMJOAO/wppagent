"""
Admin RBAC Routes
Endpoints administrativos para gerenciamento RBAC
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr

from app.auth.rbac_decorators import (
    RequirePermission,
    RequireRole,
    RequireSuperAdmin,
    get_current_user,
)
from app.models.rbac import (
    PERMISSION_DEFINITIONS,
    ROLE_CONFIGURATIONS,
    PermissionResponse,
    PermissionType,
    RoleResponse,
    RoleType,
    UserResponse,
)
from app.services.rbac_service import rbac_service

router = APIRouter(prefix="/admin/rbac", tags=["Admin RBAC Management"])

# ========================================
# MODELOS PYDANTIC PARA REQUESTS
# ========================================


class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role_types: List[RoleType]
    requires_2fa: bool = False


class UpdateUserRolesRequest(BaseModel):
    role_types: List[RoleType]


class CreateRoleRequest(BaseModel):
    name: str
    description: str
    role_type: RoleType


class BulkPermissionCheckRequest(BaseModel):
    permissions: List[PermissionType]
    check_type: str = "any"  # "any" ou "all"


# ========================================
# USUÁRIOS
# ========================================


@router.post("/users", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    current_user=Depends(RequirePermission(PermissionType.USER_MANAGEMENT)),
):
    """Criar novo usuário"""
    user = await rbac_service.create_user(
        username=request.username,
        email=request.email,
        full_name=request.full_name,
        role_types=request.role_types,
        requires_2fa=request.requires_2fa,
    )

    if not user:
        raise HTTPException(status_code=500, detail="Erro ao criar usuário")

    return rbac_service._user_to_response(user)


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    current_user=Depends(RequirePermission(PermissionType.USER_MANAGEMENT)),
):
    """Listar usuários"""
    users = await rbac_service.list_users(skip=skip, limit=limit, is_active=is_active)
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user=Depends(RequirePermission(PermissionType.USER_MANAGEMENT)),
):
    """Obter usuário por ID"""
    user = await rbac_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return rbac_service._user_to_response(user)


@router.put("/users/{user_id}/roles")
async def update_user_roles(
    user_id: int,
    request: UpdateUserRolesRequest,
    current_user=Depends(RequirePermission(PermissionType.USER_MANAGEMENT)),
):
    """Atualizar roles do usuário"""
    success = await rbac_service.update_user_roles(user_id, request.role_types)

    if not success:
        raise HTTPException(status_code=500, detail="Erro ao atualizar roles")

    return {"message": "Roles atualizados com sucesso"}


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: int,
    current_user=Depends(RequirePermission(PermissionType.USER_MANAGEMENT)),
):
    """Obter permissões do usuário"""
    permissions = await rbac_service.get_user_permissions(user_id)

    return {
        "user_id": user_id,
        "permissions": permissions,
        "permissions_count": len(permissions),
    }


# ========================================
# ROLES
# ========================================


@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    current_user=Depends(RequirePermission(PermissionType.ROLE_MANAGEMENT)),
):
    """Listar todos os roles"""
    roles = await rbac_service.list_roles()
    return roles


@router.post("/roles", response_model=RoleResponse)
async def create_custom_role(
    request: CreateRoleRequest,
    current_user=Depends(RequirePermission(PermissionType.ROLE_MANAGEMENT)),
):
    """Criar role customizado"""
    role = await rbac_service.create_custom_role(
        name=request.name,
        description=request.description,
        role_type=request.role_type,
    )

    if not role:
        raise HTTPException(status_code=500, detail="Erro ao criar role")

    return rbac_service._role_to_response(role)


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    current_user=Depends(RequirePermission(PermissionType.ROLE_MANAGEMENT)),
):
    """Obter role por ID"""
    role = await rbac_service.get_role_by_id(role_id)

    if not role:
        raise HTTPException(status_code=404, detail="Role não encontrado")

    return rbac_service._role_to_response(role)


# ========================================
# PERMISSÕES
# ========================================


@router.get("/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    current_user=Depends(RequirePermission(PermissionType.ROLE_MANAGEMENT)),
):
    """Listar todas as permissões"""
    permissions = await rbac_service.list_permissions()
    return permissions


@router.get("/permissions/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: int,
    current_user=Depends(RequirePermission(PermissionType.ROLE_MANAGEMENT)),
):
    """Obter permissão por ID"""
    permission = await rbac_service.get_permission_by_id(permission_id)

    if not permission:
        raise HTTPException(status_code=404, detail="Permissão não encontrada")

    return rbac_service._permission_to_response(permission)


# ========================================
# ATRIBUIÇÕES
# ========================================


@router.post("/assign")
async def assign_role_to_user(
    user_id: int = Body(...),
    role_id: int = Body(...),
    current_user=Depends(RequirePermission(PermissionType.USER_MANAGEMENT)),
):
    """Atribuir role a usuário"""
    success = await rbac_service.assign_role_to_user(user_id, role_id)

    if not success:
        raise HTTPException(status_code=500, detail="Erro ao atribuir role")

    return {"message": "Role atribuído com sucesso"}


@router.delete("/assign")
async def remove_role_from_user(
    user_id: int = Body(...),
    role_id: int = Body(...),
    current_user=Depends(RequirePermission(PermissionType.USER_MANAGEMENT)),
):
    """Remover role de usuário"""
    success = await rbac_service.remove_role_from_user(user_id, role_id)

    if not success:
        raise HTTPException(status_code=500, detail="Erro ao remover role")

    return {"message": "Role removido com sucesso"}


@router.post("/users/bulk-assign-role")
async def bulk_assign_role(
    user_ids: List[int] = Body(...),
    role_type: RoleType = Body(...),
    current_user=Depends(RequirePermission(PermissionType.USER_MANAGEMENT)),
):
    """Atribuir role em lote"""
    results = []

    for user_id in user_ids:
        try:
            success = await rbac_service.assign_role_by_type(user_id, role_type)
            results.append({"user_id": user_id, "success": success})
        except Exception as e:
            results.append({"user_id": user_id, "success": False, "error": str(e)})

    return {
        "message": "Atribuição em lote concluída",
        "results": results,
        "total": len(user_ids),
        "successful": sum(1 for r in results if r["success"]),
    }


# ========================================
# INICIALIZAÇÃO E MANUTENÇÃO
# ========================================


@router.post("/initialize-system")
async def initialize_rbac_system(current_user=Depends(RequireSuperAdmin())):
    """Inicializar sistema RBAC (apenas super admin)"""
    success = await rbac_service.initialize_system()

    if not success:
        raise HTTPException(status_code=500, detail="Erro ao inicializar sistema RBAC")

    return {
        "message": "Sistema RBAC inicializado com sucesso",
        "initialized_at": datetime.utcnow().isoformat(),
    }


@router.get("/health")
async def rbac_health_check():
    """Verificar saúde do sistema RBAC (sem autenticação)"""
    try:
        # Verificar se o serviço está funcionando
        permissions_count = await rbac_service.count_permissions()
        roles_count = await rbac_service.count_roles()
        users_count = await rbac_service.count_users()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "permissions_count": permissions_count,
            "roles_count": roles_count,
            "users_count": users_count,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }


@router.get("/test")
async def rbac_test():
    """Endpoint de teste simples para RBAC"""
    try:
        return {
            "status": "ok",
            "message": "RBAC service is working",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"RBAC service error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.get("/test-roles")
async def rbac_test_roles():
    """Endpoint de teste para list_roles"""
    try:
        roles = await rbac_service.list_roles()
        return {
            "status": "ok",
            "message": "list_roles funcionando",
            "roles_count": len(roles),
            "roles": roles,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"list_roles error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.get("/test-permissions")
async def rbac_test_permissions():
    """Endpoint de teste para list_permissions"""
    try:
        permissions = await rbac_service.list_permissions()
        return {
            "status": "ok",
            "message": "list_permissions funcionando",
            "permissions_count": len(permissions),
            "permissions": permissions,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"list_permissions error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.get("/test-auth")
async def rbac_test_auth(current_user=Depends(RequirePermission(PermissionType.USER_MANAGEMENT))):
    """Endpoint de teste com autenticação RBAC"""
    try:
        return {
            "status": "ok",
            "message": "RBAC auth is working",
            "user_id": current_user.id,
            "username": current_user.username,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"RBAC auth error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.get("/debug-user")
async def debug_user(user_id: int = Depends(get_current_user_id)):
    """Endpoint de debug para verificar usuário RBAC"""
    try:
        from app.services.rbac_service import rbac_service
        
        # Buscar usuário
        user = await rbac_service.get_user_by_id(user_id)
        
        if not user:
            return {
                "status": "error",
                "message": "User not found",
                "user_id": user_id
            }
        
        # Verificar roles e permissões
        roles_info = []
        for role in user.roles:
            roles_info.append({
                "id": role.id,
                "name": role.name,
                "role_type": role.role_type.value if role.role_type else None,
                "permissions": [perm.permission_type for perm in role.permissions]
            })
        
        return {
            "status": "ok",
            "user_id": user.id,
            "username": user.username,
            "is_active": user.is_active,
            "roles": roles_info,
            "all_permissions": [perm.value for perm in user.get_all_permissions()],
            "has_user_management": user.has_permission(PermissionType.USER_MANAGEMENT),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Debug error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }

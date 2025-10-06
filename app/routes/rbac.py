"""
API Routes para Sistema RBAC
Gerenciamento de usuários, roles e permissões
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
from app.auth.jwt_manager import get_current_user_from_token
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

router = APIRouter(prefix="/api/rbac", tags=["RBAC Management"])

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
    permission_types: List[PermissionType]


class PermissionCheckRequest(BaseModel):
    user_id: int
    permission: PermissionType


class BulkPermissionCheckRequest(BaseModel):
    user_id: int
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
        raise HTTPException(status_code=400, detail="Erro ao criar usuário")

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
    """Obter usuário específico"""
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
    """Atualizar roles de um usuário"""
    success = await rbac_service.update_user_roles(user_id, request.role_types)

    if not success:
        raise HTTPException(status_code=400, detail="Erro ao atualizar roles")

    return {"message": "Roles atualizados com sucesso"}


@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: int,
    current_user=Depends(RequirePermission(PermissionType.USER_MANAGEMENT)),
):
    """Desativar usuário"""
    success = await rbac_service.deactivate_user(user_id)

    if not success:
        raise HTTPException(status_code=400, detail="Erro ao desativar usuário")

    return {"message": "Usuário desativado com sucesso"}


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: int,
    current_user=Depends(RequirePermission(PermissionType.USER_MANAGEMENT)),
):
    """Obter todas as permissões de um usuário"""
    permissions = await rbac_service.get_user_permissions(user_id)

    return {
        "user_id": user_id,
        "permissions": list(permissions),
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
        permission_types=request.permission_types,
    )

    if not role:
        raise HTTPException(status_code=400, detail="Erro ao criar role")

    return rbac_service._role_to_response(role)


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: int,
    current_user=Depends(RequirePermission(PermissionType.ROLE_MANAGEMENT)),
):
    """Deletar role (apenas customizados)"""
    success = await rbac_service.delete_role(role_id)

    if not success:
        raise HTTPException(
            status_code=400, detail="Erro ao deletar role ou role não pode ser deletado"
        )

    return {"message": "Role deletado com sucesso"}


# ========================================
# PERMISSÕES
# ========================================


@router.get("/permissions")
async def list_permissions(
    category: Optional[str] = None,
    risk_level: Optional[str] = None,
    current_user=Depends(RequirePermission(PermissionType.PERMISSIONS_MANAGEMENT)),
):
    """Listar todas as permissões disponíveis"""
    permissions = []

    for perm_type, definition in PERMISSION_DEFINITIONS.items():
        # Filtros
        if category and definition.category != category:
            continue
        if risk_level and definition.risk_level != risk_level:
            continue

        permissions.append(
            {
                "permission_type": perm_type.value,
                "name": definition.description,
                "description": definition.description,
                "category": definition.category,
                "risk_level": definition.risk_level,
                "requires_2fa": definition.requires_2fa,
            }
        )

    return {
        "permissions": permissions,
        "total": len(permissions),
        "categories": list(
            set(def_.category for def_ in PERMISSION_DEFINITIONS.values())
        ),
        "risk_levels": list(
            set(def_.risk_level for def_ in PERMISSION_DEFINITIONS.values())
        ),
    }


@router.get("/permissions/categories")
async def get_permission_categories(
    current_user=Depends(RequirePermission(PermissionType.PERMISSIONS_MANAGEMENT)),
):
    """Obter categorias de permissões"""
    categories = {}

    for perm_type, definition in PERMISSION_DEFINITIONS.items():
        category = definition.category
        if category not in categories:
            categories[category] = []

        categories[category].append(
            {
                "permission_type": perm_type.value,
                "name": definition.description,
                "risk_level": definition.risk_level,
                "requires_2fa": definition.requires_2fa,
            }
        )

    return categories


# ========================================
# VERIFICAÇÃO DE PERMISSÕES
# ========================================


@router.post("/check-permission")
async def check_permission(
    request: PermissionCheckRequest,
    current_user=Depends(RequirePermission(PermissionType.USER_MANAGEMENT)),
):
    """Verificar se usuário tem permissão específica"""
    has_permission = await rbac_service.check_user_permission(
        request.user_id, request.permission
    )

    return {
        "user_id": request.user_id,
        "permission": request.permission.value,
        "has_permission": has_permission,
    }


@router.post("/check-permissions")
async def check_multiple_permissions(
    request: BulkPermissionCheckRequest,
    current_user=Depends(RequirePermission(PermissionType.USER_MANAGEMENT)),
):
    """Verificar múltiplas permissões"""
    if request.check_type == "any":
        has_permissions = await rbac_service.check_user_any_permission(
            request.user_id, request.permissions
        )
    else:  # "all"
        user = await rbac_service.get_user_by_id(request.user_id)
        has_permissions = (
            user.has_all_permissions(request.permissions) if user else False
        )

    return {
        "user_id": request.user_id,
        "permissions": [p.value for p in request.permissions],
        "check_type": request.check_type,
        "has_permissions": has_permissions,
    }


# ========================================
# ESTATÍSTICAS E AUDITORIA
# ========================================


@router.get("/stats")
async def get_system_stats(
    current_user=Depends(RequirePermission(PermissionType.SYSTEM_ADMIN)),
):
    """Obter estatísticas do sistema RBAC"""
    stats = await rbac_service.get_system_stats()
    return stats


@router.get("/permission-matrix")
async def get_permission_matrix(
    current_user=Depends(RequirePermission(PermissionType.SYSTEM_ADMIN)),
):
    """Obter matriz completa de permissões"""
    matrix = await rbac_service.get_permission_matrix()
    return {"matrix": matrix, "generated_at": datetime.utcnow().isoformat()}


@router.get("/system-roles")
async def get_system_roles_info(
    current_user=Depends(RequirePermission(PermissionType.ROLE_MANAGEMENT)),
):
    """Obter informações sobre roles do sistema"""
    roles_info = {}

    for role_type, config in ROLE_CONFIGURATIONS.items():
        roles_info[role_type.value] = {
            "name": config["name"],
            "description": config["description"],
            "permissions_count": len(config["permissions"]),
            "is_system_role": config["is_system_role"],
            "can_be_deleted": config["can_be_deleted"],
            "permissions": [p.value for p in config["permissions"]],
        }

    return {"system_roles": roles_info, "total_system_roles": len(ROLE_CONFIGURATIONS)}


# ========================================
# OPERAÇÕES EM LOTE
# ========================================


@router.post("/users/bulk-assign-role")
async def bulk_assign_role(
    user_ids: List[int] = Body(...),
    role_type: RoleType = Body(...),
    current_user=Depends(RequirePermission(PermissionType.USER_MANAGEMENT)),
):
    """Atribuir role a múltiplos usuários"""
    results = []

    for user_id in user_ids:
        # Obter roles atuais do usuário
        user = await rbac_service.get_user_by_id(user_id)
        if user:
            current_roles = [role.role_type for role in user.roles if role.role_type]
            if role_type not in current_roles:
                current_roles.append(role_type)
                success = await rbac_service.update_user_roles(user_id, current_roles)
                results.append({"user_id": user_id, "success": success})
            else:
                results.append(
                    {"user_id": user_id, "success": True, "already_has": True}
                )
        else:
            results.append(
                {"user_id": user_id, "success": False, "error": "User not found"}
            )

    return {
        "results": results,
        "total_processed": len(user_ids),
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
        # Verificar se as tabelas estão acessíveis
        stats = await rbac_service.get_system_stats()

        return {
            "status": "healthy",
            "rbac_stats": stats,
            "permissions_defined": len(PERMISSION_DEFINITIONS),
            "system_roles_defined": len(ROLE_CONFIGURATIONS),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.get("/my-permissions")
async def get_my_permissions(current_user=Depends(get_current_user_from_token)):
    """Obter permissões do usuário atual (sem necessidade de permissões especiais)"""
    permissions = current_user.get_all_permissions()

    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "permissions": list(permissions),
        "permissions_count": len(permissions),
        "roles": [role.name for role in current_user.roles],
        "is_super_admin": current_user.is_super_admin(),
    }

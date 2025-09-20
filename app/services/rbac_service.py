"""
Serviço RBAC (Role-Based Access Control)
Sistema completo de controle de acesso baseado em funções
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models.rbac import (
    PERMISSION_DEFINITIONS,
    ROLE_CONFIGURATIONS,
    PermissionResponse,
    PermissionType,
    RBACPermission,
    RBACRole,
    RBACUser,
    RoleResponse,
    RoleType,
    UserResponse,
)

logger = logging.getLogger(__name__)


class RBACService:
    """Serviço principal para gerenciamento RBAC"""

    def __init__(self):
        self.logger = logger

    # ========================================
    # INICIALIZAÇÃO DO SISTEMA
    # ========================================

    async def initialize_system(self) -> bool:
        """Inicializar sistema RBAC com dados padrão"""
        try:
            async with AsyncSessionLocal() as session:
                # 1. Criar todas as permissões
                await self._create_default_permissions(session)

                # 2. Criar roles padrão
                await self._create_default_roles(session)

                # 3. Associar permissões aos roles
                await self._assign_role_permissions(session)

                await session.commit()

            self.logger.info("✅ Sistema RBAC inicializado com sucesso")
            return True

        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar sistema RBAC: {e}")
            return False

    async def _create_default_permissions(self, session: AsyncSession):
        """Criar permissões padrão"""
        for perm_type, definition in PERMISSION_DEFINITIONS.items():
            # Verificar se já existe
            existing = await session.execute(
                select(RBACPermission).where(
                    RBACPermission.permission_type == perm_type
                )
            )

            if not existing.scalar():
                permission = RBACPermission(
                    permission_type=perm_type,
                    name=definition.description,
                    description=definition.description,
                    category=definition.category,
                    risk_level=definition.risk_level,
                    requires_2fa=definition.requires_2fa,
                )
                session.add(permission)

        self.logger.info(
            f"✅ {len(PERMISSION_DEFINITIONS)} permissões criadas/verificadas"
        )

    async def _create_default_roles(self, session: AsyncSession):
        """Criar roles padrão"""
        for role_type, config in ROLE_CONFIGURATIONS.items():
            # Verificar se já existe
            existing = await session.execute(
                select(RBACRole).where(RBACRole.role_type == role_type)
            )

            if not existing.scalar():
                role = RBACRole(
                    name=config["name"],
                    description=config["description"],
                    role_type=role_type,
                    is_system_role=config["is_system_role"],
                    can_be_deleted=config["can_be_deleted"],
                )
                session.add(role)

        self.logger.info(f"✅ {len(ROLE_CONFIGURATIONS)} roles criados/verificados")

    async def _assign_role_permissions(self, session: AsyncSession):
        """Associar permissões aos roles"""
        for role_type, config in ROLE_CONFIGURATIONS.items():
            # Buscar o role
            role_result = await session.execute(
                select(RBACRole)
                .options(selectinload(RBACRole.permissions))
                .where(RBACRole.role_type == role_type)
            )
            role = role_result.scalar()

            if role:
                # Buscar permissões necessárias
                permissions_result = await session.execute(
                    select(RBACPermission).where(
                        RBACPermission.permission_type.in_(config["permissions"])
                    )
                )
                permissions = permissions_result.scalars().all()

                # Limpar permissões existentes e adicionar novas
                role.permissions.clear()
                role.permissions.extend(permissions)

        self.logger.info("✅ Permissões associadas aos roles")

    # ========================================
    # GERENCIAMENTO DE USUÁRIOS
    # ========================================

    async def create_user(
        self,
        username: str,
        email: str,
        full_name: str,
        role_types: List[RoleType],
        requires_2fa: bool = False,
    ) -> Optional[RBACUser]:
        """Criar novo usuário"""
        try:
            async with AsyncSessionLocal() as session:
                # Verificar se já existe
                existing = await session.execute(
                    select(RBACUser).where(
                        or_(RBACUser.username == username, RBACUser.email == email)
                    )
                )

                if existing.scalar():
                    raise ValueError("Usuário ou email já existe")

                # Criar usuário
                user = RBACUser(
                    username=username,
                    email=email,
                    full_name=full_name,
                    requires_2fa=requires_2fa,
                )

                # Buscar e associar roles
                roles_result = await session.execute(
                    select(RBACRole).where(RBACRole.role_type.in_(role_types))
                )
                roles = roles_result.scalars().all()
                user.roles.extend(roles)

                session.add(user)
                await session.commit()
                await session.refresh(user)

                self.logger.info(f"✅ Usuário {username} criado com {len(roles)} roles")
                return user

        except Exception as e:
            self.logger.error(f"❌ Erro ao criar usuário: {e}")
            return None

    async def get_user_by_id(self, user_id: int) -> Optional[RBACUser]:
        """Buscar usuário por ID"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(RBACUser)
                .options(
                    selectinload(RBACUser.roles).selectinload(RBACRole.permissions)
                )
                .where(RBACUser.id == user_id)
            )
            return result.scalar()

    async def get_user_by_username(self, username: str) -> Optional[RBACUser]:
        """Buscar usuário por username"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(RBACUser)
                .options(
                    selectinload(RBACUser.roles).selectinload(RBACRole.permissions)
                )
                .where(RBACUser.username == username)
            )
            return result.scalar()

    async def list_users(
        self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> List[UserResponse]:
        """Listar usuários"""
        async with AsyncSessionLocal() as session:
            query = select(RBACUser).options(
                selectinload(RBACUser.roles).selectinload(RBACRole.permissions)
            )

            if is_active is not None:
                query = query.where(RBACUser.is_active == is_active)

            query = query.offset(skip).limit(limit)
            result = await session.execute(query)
            users = result.scalars().all()

            return [self._user_to_response(user) for user in users]

    async def update_user_roles(self, user_id: int, role_types: List[RoleType]) -> bool:
        """Atualizar roles de um usuário"""
        try:
            async with AsyncSessionLocal() as session:
                # Buscar usuário
                user_result = await session.execute(
                    select(RBACUser)
                    .options(selectinload(RBACUser.roles))
                    .where(RBACUser.id == user_id)
                )
                user = user_result.scalar()

                if not user:
                    return False

                # Buscar novos roles
                roles_result = await session.execute(
                    select(RBACRole).where(RBACRole.role_type.in_(role_types))
                )
                new_roles = roles_result.scalars().all()

                # Atualizar roles
                user.roles.clear()
                user.roles.extend(new_roles)
                user.updated_at = datetime.utcnow()

                await session.commit()

                self.logger.info(f"✅ Roles do usuário {user_id} atualizados")
                return True

        except Exception as e:
            self.logger.error(f"❌ Erro ao atualizar roles: {e}")
            return False

    async def deactivate_user(self, user_id: int) -> bool:
        """Desativar usuário"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(RBACUser).where(RBACUser.id == user_id)
                )
                user = result.scalar()

                if user:
                    user.is_active = False
                    user.updated_at = datetime.utcnow()
                    await session.commit()

                    self.logger.info(f"✅ Usuário {user_id} desativado")
                    return True

                return False

        except Exception as e:
            self.logger.error(f"❌ Erro ao desativar usuário: {e}")
            return False

    # ========================================
    # GERENCIAMENTO DE ROLES
    # ========================================

    async def create_custom_role(
        self, name: str, description: str, permission_types: List[PermissionType]
    ) -> Optional[RBACRole]:
        """Criar role customizado"""
        try:
            async with AsyncSessionLocal() as session:
                # Verificar se já existe
                existing = await session.execute(
                    select(RBACRole).where(RBACRole.name == name)
                )

                if existing.scalar():
                    raise ValueError("Role já existe")

                # Criar role
                role = RBACRole(
                    name=name,
                    description=description,
                    is_system_role=False,
                    can_be_deleted=True,
                )

                # Buscar e associar permissões
                permissions_result = await session.execute(
                    select(RBACPermission).where(
                        RBACPermission.permission_type.in_(permission_types)
                    )
                )
                permissions = permissions_result.scalars().all()
                role.permissions.extend(permissions)

                session.add(role)
                await session.commit()
                await session.refresh(role)

                self.logger.info(f"✅ Role customizado {name} criado")
                return role

        except Exception as e:
            self.logger.error(f"❌ Erro ao criar role: {e}")
            return None

    async def list_roles(self) -> List[RoleResponse]:
        """Listar todos os roles"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(RBACRole).options(
                    selectinload(RBACRole.permissions), selectinload(RBACRole.users)
                )
            )
            roles = result.scalars().all()

            return [self._role_to_response(role) for role in roles]

    async def delete_role(self, role_id: int) -> bool:
        """Deletar role (apenas se permitido)"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(RBACRole).where(RBACRole.id == role_id)
                )
                role = result.scalar()

                if not role:
                    return False

                if not role.can_be_deleted:
                    raise ValueError("Role do sistema não pode ser deletado")

                await session.delete(role)
                await session.commit()

                self.logger.info(f"✅ Role {role_id} deletado")
                return True

        except Exception as e:
            self.logger.error(f"❌ Erro ao deletar role: {e}")
            return False

    # ========================================
    # VERIFICAÇÃO DE PERMISSÕES
    # ========================================

    async def check_user_permission(
        self, user_id: int, permission: PermissionType
    ) -> bool:
        """Verificar se usuário tem permissão específica"""
        user = await self.get_user_by_id(user_id)
        if not user or not user.is_active:
            return False

        return user.has_permission(permission)

    async def check_user_any_permission(
        self, user_id: int, permissions: List[PermissionType]
    ) -> bool:
        """Verificar se usuário tem pelo menos uma das permissões"""
        user = await self.get_user_by_id(user_id)
        if not user or not user.is_active:
            return False

        return user.has_any_permission(permissions)

    async def get_user_permissions(self, user_id: int) -> Set[PermissionType]:
        """Obter todas as permissões de um usuário"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return set()

        return user.get_all_permissions()

    # ========================================
    # AUDITORIA E RELATÓRIOS
    # ========================================

    async def count_users(self) -> int:
        """Contar total de usuários"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(func.count(RBACUser.id)))
            return result.scalar() or 0

    async def count_roles(self) -> int:
        """Contar total de roles"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(func.count(RBACRole.id)))
            return result.scalar() or 0

    async def count_permissions(self) -> int:
        """Contar total de permissões"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(func.count(RBACPermission.id)))
            return result.scalar() or 0

    async def get_system_stats(self) -> Dict:
        """Obter estatísticas do sistema RBAC"""
        async with AsyncSessionLocal() as session:
            # Contar usuários
            users_count = await session.execute(select(func.count(RBACUser.id)))
            total_users = users_count.scalar()

            active_users = await session.execute(
                select(func.count(RBACUser.id)).where(RBACUser.is_active == True)
            )
            active_count = active_users.scalar()

            # Contar roles
            roles_count = await session.execute(select(func.count(RBACRole.id)))
            total_roles = roles_count.scalar()

            # Contar permissões
            permissions_count = await session.execute(
                select(func.count(RBACPermission.id))
            )
            total_permissions = permissions_count.scalar()

            return {
                "users": {
                    "total": total_users,
                    "active": active_count,
                    "inactive": total_users - active_count,
                },
                "roles": {
                    "total": total_roles,
                    "system_roles": len(ROLE_CONFIGURATIONS),
                    "custom_roles": total_roles - len(ROLE_CONFIGURATIONS),
                },
                "permissions": {
                    "total": total_permissions,
                    "categories": len(
                        set(def_.category for def_ in PERMISSION_DEFINITIONS.values())
                    ),
                },
            }

    async def get_permission_matrix(self) -> Dict:
        """Obter matriz de permissões (roles x permissions)"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(RBACRole).options(selectinload(RBACRole.permissions))
            )
            roles = result.scalars().all()

            matrix = {}
            for role in roles:
                matrix[role.name] = {
                    "role_type": role.role_type.value if role.role_type else "custom",
                    "permissions": [
                        perm.permission_type.value for perm in role.permissions
                    ],
                }

            return matrix

    # ========================================
    # MÉTODOS AUXILIARES
    # ========================================

    def _user_to_response(self, user: RBACUser) -> UserResponse:
        """Converter usuário para resposta da API"""
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            requires_2fa=user.requires_2fa,
            last_login=user.last_login,
            roles=[role.name for role in user.roles],
            permissions=list(user.get_all_permissions()),
            created_at=user.created_at,
        )

    def _role_to_response(self, role: RBACRole) -> RoleResponse:
        """Converter role para resposta da API"""
        return RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            role_type=role.role_type.value if role.role_type else None,
            is_active=role.is_active,
            is_system_role=role.is_system_role,
            can_be_deleted=role.can_be_deleted,
            permissions_count=len(role.permissions),
            users_count=len(role.users),
            permissions=[perm.permission_type.value for perm in role.permissions],
            created_at=role.created_at,
        )


# Instância singleton do serviço
rbac_service = RBACService()

"""
Migração RBAC - Sistema de Controle de Acesso Completo

Revision ID: rbac_system_2025
Revises: d08ef6b15ecb
Create Date: 2025-09-08 14:03:00.000000

✅ MIGRAÇÃO REORGANIZADA: Padrão de nomenclatura corrigido
Arquivo renomeado de 'rbac_system_2025.py' para seguir padrão YYYY_MM_DD_HHMM-revision_id-description.py
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers
revision = "rbac_system_2025"
down_revision = "d08ef6b15ecb"
branch_labels = None
depends_on = None


def upgrade():
    """Criar estrutura RBAC"""

    # Enum para tipos de permissões
    permission_type_enum = postgresql.ENUM(
        "dashboard:view",
        "dashboard:admin",
        "appointments:view",
        "appointments:create",
        "appointments:update",
        "appointments:delete",
        "appointments:admin",
        "conversations:view",
        "conversations:respond",
        "conversations:delete",
        "conversations:admin",
        "clients:view",
        "clients:create",
        "clients:update",
        "clients:delete",
        "clients:admin",
        "reports:view",
        "reports:export",
        "reports:admin",
        "system:admin",
        "users:manage",
        "roles:manage",
        "permissions:manage",
        "monitoring:view",
        "monitoring:admin",
        "backup:create",
        "backup:restore",
        "backup:admin",
        name="permissiontype",
    )
    permission_type_enum.create(op.get_bind())

    # Enum para tipos de roles
    role_type_enum = postgresql.ENUM(
        "super_admin",
        "admin",
        "manager",
        "operator",
        "viewer",
        "guest",
        name="roletype",
    )
    role_type_enum.create(op.get_bind())

    # Tabela de usuários RBAC
    op.create_table(
        "rbac_users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("username", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("email", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_verified", sa.Boolean(), default=False),
        sa.Column("requires_2fa", sa.Boolean(), default=False),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
        sa.Column(
            "updated_at", sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()
        ),
    )

    # Tabela de roles
    op.create_table(
        "rbac_roles",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("role_type", role_type_enum, nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_system_role", sa.Boolean(), default=False),
        sa.Column("can_be_deleted", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
        sa.Column(
            "updated_at", sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()
        ),
    )

    # Tabela de permissões
    op.create_table(
        "rbac_permissions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("permission_type", permission_type_enum, unique=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("risk_level", sa.String(), nullable=False),
        sa.Column("requires_2fa", sa.Boolean(), default=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
    )

    # Tabela de associação usuário-role (many-to-many)
    op.create_table(
        "user_roles",
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("rbac_users.id"), nullable=False
        ),
        sa.Column(
            "role_id", sa.Integer(), sa.ForeignKey("rbac_roles.id"), nullable=False
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    # Tabela de associação role-permission (many-to-many)
    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id", sa.Integer(), sa.ForeignKey("rbac_roles.id"), nullable=False
        ),
        sa.Column(
            "permission_id",
            sa.Integer(),
            sa.ForeignKey("rbac_permissions.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    # Índices para performance
    op.create_index("idx_rbac_users_username", "rbac_users", ["username"])
    op.create_index("idx_rbac_users_email", "rbac_users", ["email"])
    op.create_index("idx_rbac_users_active", "rbac_users", ["is_active"])
    op.create_index("idx_rbac_roles_name", "rbac_roles", ["name"])
    op.create_index("idx_rbac_roles_type", "rbac_roles", ["role_type"])
    op.create_index(
        "idx_rbac_permissions_type", "rbac_permissions", ["permission_type"]
    )
    op.create_index("idx_rbac_permissions_category", "rbac_permissions", ["category"])


def downgrade():
    """Remover estrutura RBAC"""

    # Dropar tabelas em ordem reversa das dependências
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("rbac_permissions")
    op.drop_table("rbac_roles")
    op.drop_table("rbac_users")

    # Dropar ENUMs
    op.execute("DROP TYPE IF EXISTS roletype")
    op.execute("DROP TYPE IF EXISTS permissiontype")
